import json
import logging
import functools
from typing import List, Set, Optional, Any, Dict, Awaitable, cast, Literal, TypedDict
import asyncio
import time

import pika
from pika import connection
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from pika.exceptions import ChannelClosedByBroker, ProbableAccessDeniedError
import pika.spec
from pika.frame import Method

from nuropb.interface import (
    PayloadDict,
    NuropbTransportError,
    NuropbLifecycleState,
    TransportServicePayload,
    NUROPB_PROTOCOL_VERSIONS_SUPPORTED,
    NUROPB_MESSAGE_TYPES,
    TransportRespondPayload,
    MessageCallbackFunction,
    AcknowledgeAction,
    NUROPB_PROTOCOL_VERSION,
    NUROPB_VERSION,
    NuropbNotDeliveredError,
    NuropbCallAgainReject,
)
from nuropb.rmq_lib import (
    rmq_api_url_from_amqp_url,
    create_virtual_host,
    configure_nuropb_rmq,
)
from nuropb.service_handlers import (
    create_transport_response_from_rmq_decode_exception,
    error_dict_from_exception,
)
from nuropb.utils import obfuscate_credentials


class RabbitMQConfiguration(TypedDict):
    rpc_exchange: str
    events_exchange: str
    dl_exchange: str
    dl_queue: str
    service_queue: str
    response_queue: str
    rpc_bindings: List[str]
    event_bindings: List[str]
    default_ttl: int
    client_only: bool


logger = logging.getLogger(__name__)

connection.PRODUCT = "NuroPb Distributed RPC-Event Library"
""" TODO: configure the RMQ client connection attributes in the pika client properties.
See related TODO below in this module
"""

CONSUMER_CLOSED_WAIT_TIMEOUT = 10
""" The wait when shutting down consumers before closing the connection
"""

verbose = False
""" Set to True to enable module verbose logging
"""


def encode_payload(payload: PayloadDict, payload_type: str = "json") -> bytes:
    """
    :param payload:
    :param payload_type:
        Currently only support json
    :return: a byte string encoded json from imputed message dict
    """
    if payload_type != "json":
        raise ValueError(f"payload_type {payload_type} is not supported")

    return json.dumps(payload).encode()


def decode_payload(
    payload: bytes,
    payload_type: str = "json",
    updates: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    :param payload:
    :param payload_type:
        Currently only support json
    :param updates:
        Optional dict to update the decoded payload with
    :return: convert bytes to a Python Dict
    """
    if payload_type != "json":
        raise ValueError(f"payload_type {payload_type} is not supported")

    decoded_payload: Any = json.loads(payload)
    if not isinstance(decoded_payload, dict):
        raise ValueError(f"payload is not a dict: {decoded_payload}")
    if updates is not None:
        decoded_payload.update(updates)

    return decoded_payload


def decode_rmq_body(
    method: pika.spec.Basic.Deliver, properties: pika.spec.BasicProperties, body: bytes
) -> TransportServicePayload:
    """Map the incoming RabbitMQ message to python compatible dictionary as
    defined by ServicePayloadDict
    """
    _ = method  # Future placeholder
    service_message: TransportServicePayload = {
        "nuropb_protocol": properties.headers.get("nuropb_protocol"),
        "nuropb_type": properties.headers.get("nuropb_type"),
        "nuropb_payload": {},
        "correlation_id": properties.correlation_id,
        "trace_id": properties.headers.get("trace_id"),
        "ttl": properties.expiration,
    }
    if service_message["nuropb_protocol"] not in NUROPB_PROTOCOL_VERSIONS_SUPPORTED:
        raise ValueError(
            f"nuropb_protocol '{service_message['nuropb_protocol']}' is not supported"
        )
    if service_message["nuropb_type"] not in NUROPB_MESSAGE_TYPES:
        raise ValueError(
            f"message_type '{service_message['nuropb_type']}' is not supported"
        )
    service_message["nuropb_payload"] = decode_payload(body, "json")
    return service_message


class ServiceNotConfigured(Exception):
    """Raised when a service is not properly configured on the RabbitMQ broker.
    the leader will be expected to configure the Exchange and service queues
    """

    pass


class RMQTransport:
    """

    If RabbitMQ closes the connection, this class will stop and indicate
    that reconnection is necessary. You should look at the output, as
    there are limited reasons why the connection may be closed, which
    usually are tied to permission related issues or socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """

    _service_name: str
    _instance_id: str
    _amqp_url: str
    _rpc_exchange: str
    _events_exchange: str
    _dl_exchange: str
    _dl_queue: str
    _service_queue: str
    _response_queue: str
    _rpc_bindings: Set[str]
    _event_bindings: Set[str]
    _prefetch_count: int
    _default_ttl: int
    _client_only: bool
    _message_callback: MessageCallbackFunction

    _connected_future: Any
    _disconnected_future: Any

    _is_leader: bool
    _is_rabbitmq_configured: bool

    _ioloop: asyncio.AbstractEventLoop | None
    _connection: AsyncioConnection | None
    _channel: Channel | None
    _consumer_tags: Set[Any]
    _consuming: bool
    _closing: bool
    _connected: bool
    _reconnect: bool
    _was_consuming: bool

    def __init__(
        self,
        service_name: str,
        instance_id: str,
        amqp_url: str,
        message_callback: MessageCallbackFunction,
        rpc_exchange: Optional[str] = None,
        events_exchange: Optional[str] = None,
        dl_exchange: Optional[str] = None,
        dl_queue: Optional[str] = None,
        service_queue: Optional[str] = None,
        response_queue: Optional[str] = None,
        rpc_bindings: Optional[List[str] | Set[str]] = None,
        event_bindings: Optional[List[str] | Set[str]] = None,
        prefetch_count: Optional[int] = None,
        default_ttl: Optional[int] = None,
        client_only: Optional[bool] = None,
        ioloop: Optional[asyncio.AbstractEventLoop] = None,
    ):  # NOSONAR
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.

        :param str service_name: The name of the service
        :param str instance_id: The instance id of the service
        :param str amqp_url: The AMQP url to connect with
        :param MessageCallbackFunction message_callback: The callback to call when a message is received
        :param str rpc_exchange: The name of the RPC exchange
        :param str events_exchange: The name of the events exchange
        :param str dl_exchange: The name of the dead letter exchange
        :param str dl_queue: The name of the dead letter queue
        :param str service_queue: The name of the requests queue
        :param str response_queue: The name of the responses queue
        :param List[str] rpc_bindings: The list of RPC bindings
        :param List[str] event_bindings: The list of events bindings
        :param int prefetch_count: The number of messages to prefetch defaults to 1, unlimited is 0.
                Experiment with larger values for higher throughput in your user case.
        :param int default_ttl: The default time to live for messages in milliseconds, defaults to 12 hours.
        """
        self._reconnect = True
        self._connected = False
        self._closing = False
        self._was_consuming = False
        self._consuming = False

        self._ioloop = ioloop
        self._connection = None
        self._channel = None
        self._consumer_tags = set()

        self._client_only = False if client_only is None else client_only
        """ If client_only is True, then the transport will not configure a service queue with
        the handling of requests, commands and events disabled. 
        """
        if self._client_only:
            logger.info("Client only transport")
            rpc_bindings = []
            event_bindings = []

        # Experiment with larger values for higher throughput.
        self._service_name = service_name
        self._instance_id = instance_id
        self._amqp_url = amqp_url
        self._rpc_exchange = rpc_exchange or "nuropb-rpc-exchange"
        self._events_exchange = events_exchange or "nuropb-events-exchange"
        self._dl_exchange = dl_exchange or "nuropb-dl-exchange"
        self._dl_queue = dl_queue or f"nuropb-{self._service_name}-dl"
        self._service_queue = service_queue or f"nuropb-{self._service_name}-service"
        self._response_queue = (
            response_queue
            or f"nuropb-{self._service_name}-{self._instance_id}-response"
        )
        self._rpc_bindings = set(rpc_bindings or [])
        self._event_bindings = set(event_bindings or [])
        self._prefetch_count = 1 if prefetch_count is None else prefetch_count
        self._default_ttl = default_ttl or 60 * 60 * 1000 * 12  # 12 hours
        self._message_callback = message_callback
        self._rpc_bindings.add(self._service_name)

        self._is_leader = True
        self._is_rabbitmq_configured = False

        self._connected_future = None
        self._disconnected_future = None

    @property
    def ioloop(self) -> asyncio.AbstractEventLoop:
        """ioloop: returns the asyncio event loop"""
        if self._ioloop is None:
            self._ioloop = asyncio.get_event_loop()
        return self._ioloop

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def amqp_url(self) -> str:
        return self._amqp_url

    @property
    def is_leader(self) -> bool:
        return self._is_leader

    @is_leader.setter
    def is_leader(self, value: bool) -> None:
        """is_leader: set the transport's leader status"""
        self._is_leader = value

    @property
    def connected(self) -> bool:
        """connected: returns the connection status of the underlying transport
        :return: bool
        """
        return self._connected

    @property
    def rpc_exchange(self) -> str:
        """rpc_exchange: returns the name of the RPC exchange
        :return: str
        """
        return self._rpc_exchange

    @property
    def events_exchange(self) -> str:
        """events_exchange: returns the name of the events exchange
        :return: str
        """
        return self._events_exchange

    @property
    def response_queue(self) -> str:
        """response_queue: returns the name of the response queue
        :return: str
        """
        return self._response_queue

    @property
    def rmq_configuration(self) -> RabbitMQConfiguration:
        """rmq_configuration: returns the RabbitMQ configuration
        :return: Dict[str, Any]
        """
        return {
            "rpc_exchange": self._rpc_exchange,
            "events_exchange": self._events_exchange,
            "dl_exchange": self._dl_exchange,
            "dl_queue": self._dl_queue,
            "service_queue": self._service_queue,
            "response_queue": self._response_queue,
            "rpc_bindings": list(self._rpc_bindings),
            "event_bindings": list(self._event_bindings),
            "default_ttl": self._default_ttl,
            "client_only": self._client_only,
        }

    def configure_rabbitmq(
        self,
        rmq_configuration: Optional[RabbitMQConfiguration] = None,
        amqp_url: Optional[str] = None,
        rmq_api_url: Optional[str] = None,
    ) -> None:
        """configure_rabbitmq: configure the RabbitMQ transport with the provided configuration

        if rmq_configuration is None, then the transport will be configured with the configuration
        provided during the transport's __init__().

        if the virtual host in the build_amqp_url is not configured, then it will be created.

        :param rmq_configuration: RabbitMQConfiguration
        :param amqp_url: Optional[str] if not provided then self._amqp_url is used
        :param rmq_api_url: Optional[str] if not provided then it is created amqp_url
        :return: None
        """
        if rmq_configuration is None:
            rmq_configuration = self.rmq_configuration
        amqp_url = amqp_url or self._amqp_url
        if amqp_url is None:
            raise ValueError("amqp_url is not provided")
        rmq_api_url = rmq_api_url or rmq_api_url_from_amqp_url(amqp_url)
        if rmq_api_url is None:
            raise ValueError("rmq_api_url is not provided")
        try:
            create_virtual_host(rmq_api_url, amqp_url)
            configure_nuropb_rmq(
                service_name=self._service_name,
                rmq_url=amqp_url,
                events_exchange=rmq_configuration["events_exchange"],
                rpc_exchange=rmq_configuration["rpc_exchange"],
                dl_exchange=rmq_configuration["dl_exchange"],
                dl_queue=rmq_configuration["dl_queue"],
                service_queue=rmq_configuration["service_queue"],
                rpc_bindings=rmq_configuration["rpc_bindings"],
                event_bindings=rmq_configuration["event_bindings"],
            )
            self._is_rabbitmq_configured = True
        except Exception as err:
            logger.exception(
                f"Failed to configure RabbitMQ with the provided configuration:\n"
                f"Error: {err}\n"
                f" - amqp url: {obfuscate_credentials(amqp_url)}\n"
                f" - api url: {obfuscate_credentials(rmq_api_url)}\n"
                f" - RabbitMQ configuration: {rmq_configuration}\n"
            )
            raise err

    async def start(self) -> None:
        """Start the transport by connecting to RabbitMQ"""
        self._connected_future = self.connect()
        try:
            await self._connected_future
        except ProbableAccessDeniedError as err:
            vhost = self._amqp_url.split("/")[-1]
            if "ConnectionClosedByBroker: (530) 'NOT_ALLOWED - vhost" in str(err):
                raise ServiceNotConfigured(
                    f"The NuroPb configuration is missing from RabbitMQ for the virtual host: {vhost}"
                )
            else:
                logger.error(
                    f"Access denied to RabbitMQ for the virtual host {vhost}: {err}"
                )
                raise err
        except Exception as err:
            logger.error(f"Failed to connect to RabbitMQ: {err}")
            raise err

    async def stop(self) -> None:
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All commands issued prior to starting the
        IOLoop will be buffered but not processed.

        """
        self._reconnect = False
        if not self._closing:
            logger.info("Stopping")
            if self._consuming:
                await self.stop_consuming()
            self._disconnected_future = self.disconnect()
            await self._disconnected_future

    def connect(self) -> Awaitable[bool]:
        """This method initiates a connection to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.

        When the connection and channel is successfully opened, the incoming messages will
        automatically be handled by _handle_message()

        :rtype: asyncio.Future

        """
        if self._connected and not self._closing and self._connection is not None:
            raise RuntimeError("Already connected to RabbitMQ")
        if self._closing:
            raise RuntimeError("Can't open a RabbitMQ connection while it is closing")
        if self._connected_future is not None and not self._connected_future.done():
            raise RuntimeError("Already connecting to RabbitMQ")

        logger.info("Connecting to %s", obfuscate_credentials(self._amqp_url))

        self._connected_future = asyncio.Future()
        client_properties = {
            "service_name": self._service_name,
            "instance_id": self._instance_id,
            "client_only": self._client_only,
            "nuropb_protocol": NUROPB_PROTOCOL_VERSION,
            "nuropb_version": NUROPB_VERSION,
        }

        conn = AsyncioConnection(
            parameters=pika.URLParameters(self._amqp_url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed,
            custom_ioloop=self.ioloop,
        )
        # TODO: overwrite the pika client properties with our own, see top of module too
        conn._client_properties.update(
            {
                "product": "NuroPb Distributed RPC-Event Library",
            }
        )
        self._connection = conn

        return self._connected_future

    def disconnect(self) -> Awaitable[bool]:
        """This method closes the connection to RabbitMQ. the pika library events will drive
        the closing and reconnection process.
        :return: asyncio.Future
        """
        if self._connection is None:
            raise RuntimeError("RMQ transport is not connected")

        if self._connection.is_closing or self._connection.is_closed:
            raise RuntimeError("RMQ transport is already closing or closed")

        if (
            self._disconnected_future is not None
            and not self._disconnected_future.done()
        ):
            raise RuntimeError("Already closing to RabbitMQ")

        logger.info("Closing RMQ transport connection")
        self._disconnected_future = asyncio.Future()
        self._closing = True
        self._connection.close()
        return self._disconnected_future

    def on_connection_open(self, _connection: AsyncioConnection) -> None:
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :param pika.adapters.asyncio_connection.AsyncioConnection _connection:
           The connection
        """
        logger.info("Connection opened - now opening channel")
        self.open_channel()

    def on_connection_open_error(
        self, _connection: AsyncioConnection, err: Exception
    ) -> None:
        """This method is called by pika if the connection to RabbitMQ
        can't be established.

        :param pika.adapters.asyncio_connection.AsyncioConnection _connection:
           The connection
        :param Exception err: The error
        """
        logger.error("Connection open failed: %s", err)
        if self._connected_future is not None and not self._connected_future.done():
            self._connected_future.set_exception(err)

    def on_connection_closed(
        self, _connection: AsyncioConnection, reason: Exception
    ) -> None:
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection _connection: The closed connection obj
        :param Exception reason: exception representing reason for loss of
            connection.

        """
        logger.warning("connection closed for reason %s", reason)
        self._channel = None
        if not self._closing:
            logger.warning("Possible reconnect necessary")

        if self._connected_future is not None and not self._connected_future.done():
            self._connected_future.set_exception(
                RuntimeError(f"Connection closed for reason: {reason}")
            )

        if (
            self._disconnected_future is not None
            and not self._disconnected_future.done()
        ):
            self._disconnected_future.set_result(True)

        self._connected = False

    def open_channel(self) -> None:
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC command. When RabbitMQ
        responds that the channel is open, the on_channel_open callback will be invoked by pika.
        """
        logger.info("Creating a new channel")
        if self._connection is None:
            raise RuntimeError("RMQ transport is not connected")
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel: Channel) -> None:
        """This method is invoked by pika when the channel has been opened. The channel object is passed
         in so that we can make use of it.

        :param pika.channel.Channel channel: The channel object
        """
        logger.info("Channel opened")
        self._channel = channel
        self._channel.add_on_close_callback(self.on_channel_closed)
        self._channel.add_on_return_callback(self.on_message_returned)
        self.declare_response_queue()

    def on_channel_closed(self, channel: Channel, reason: Exception) -> None:
        """Invoked by pika when RabbitMQ unexpectedly closes the channel. Channels are usually closed
        if you attempt to do something that violates the protocol, such as re-declare an exchange or
        queue with different parameters. In this case, we'll close the connection to shut down the object.

        :param pika.channel.Channel channel: The closed channel
        :param Exception reason: why the channel was closed
        """
        if isinstance(reason, ChannelClosedByBroker):
            logger.critical("Channel %i was closed by broker: %s", channel, reason)
            if reason.reply_code == 404:
                logger.error(
                    f"""\n\n
RabbitMQ channel closed by broker with reply_code: {reason.reply_code} and reply_text: {reason.reply_text}
This is usually caused by a misconfiguration of the RabbitMQ broker.
Please check the RabbitMQ broker configuration and restart the service:

RabbitMQ url: {obfuscate_credentials(self._amqp_url)}

Check that the following exchanges, queues and bindings exist:
    Exchange: {self._rpc_exchange}
    Exchange: {self._events_exchange}
    Exchange: {self._dl_exchange}
    Queue: {self._dl_queue}
    Queue: {self._service_queue}
    Queue: {self._response_queue}
    Bindings: {self._rpc_bindings}
    Bindings: {self._event_bindings}
\n\n"""
                )
                if self._connected_future and not self._connected_future.done():
                    self._connected_future.set_exception(
                        ServiceNotConfigured(
                            f"RabbitMQ not properly configured: {reason}"
                        )
                    )

    def declare_service_queue(self) -> None:
        """Refresh the request queue on RabbitMQ by invoking the Queue.Declare RPC command. When it
        is complete, the on_service_queue_declareok method will be invoked by pika.

        This call is idempotent and will not fail if the queue already exists.
        """
        if not self._client_only:
            logger.info("Declaring request queue %s", self._service_queue)
            if self._channel is None:
                raise RuntimeError("RMQ transport channel is not open")

            cb = functools.partial(
                self.on_service_queue_declareok, _userdata=self._service_queue
            )
            service_queue_config = {
                "durable": True,
                "auto_delete": False,
                "arguments": {"x-dead-letter-exchange": self._dl_exchange},
            }
            self._channel.queue_declare(
                queue=self._service_queue, callback=cb, **service_queue_config
            )
        else:
            logger.info("Client only, not declaring request queue")
            # TODO: FIXME: Check that passing None in here is OK
            self.on_bindok(None, userdata=self._response_queue)

    def on_service_queue_declareok(
        self, frame: pika.frame.Method, _userdata: str
    ) -> None:
        logger.info(f"Refreshing rpc bindings for service queue: {self._service_queue}")
        if self._channel is None:
            raise RuntimeError("RMQ transport channel is not open")

        for routing_key in self._rpc_bindings:
            logger.info(
                f"Binding to"
                f" rpc exchange {self._rpc_exchange}"
                f" on routing key {routing_key}"
            )
            self._channel.queue_bind(
                self._service_queue, self._rpc_exchange, routing_key=routing_key
            )
        logger.info(
            f"Refreshing event bindings for service queue: {self._service_queue}"
        )
        for routing_key in self._event_bindings:
            logger.info(
                f"Binding to"
                f" events exchange {self._events_exchange}"
                f" on topic {routing_key}"
            )
            self._channel.queue_bind(
                self._service_queue, self._events_exchange, routing_key=routing_key
            )
        self.on_bindok(frame, userdata=self._response_queue)

    def declare_response_queue(self) -> None:
        """Set up the response queue on RabbitMQ by invoking the Queue.Declare RPC command. When it
        is complete, the on_response_queue_declareok method will be invoked by pika.
        """
        logger.info("Declaring response queue %s", self._response_queue)
        if self._channel is None:
            raise RuntimeError("RMQ transport channel is not open")

        cb = functools.partial(
            self.on_response_queue_declareok, _userdata=self._response_queue
        )
        response_queue_config = {"durable": False, "auto_delete": True}
        self._channel.queue_declare(
            queue=self._response_queue, callback=cb, **response_queue_config
        )

    def on_response_queue_declareok(
        self, frame: pika.frame.Method, _userdata: str
    ) -> None:
        """Method invoked by pika when the Queue.Declare RPC call made in setup_response_queue has
        completed. In this method we will bind request queue and the response queues. When this
        command is complete, the on_bindok method will be invoked by pika.

        No explicit binds required for the response queue as it relies on the default exchange and
        routing key to the name of the queue.

        :param pika.frame.Method frame: The Queue.DeclareOk frame
        :param str|unicode _userdata: Extra user data (queue name)
        """
        _ = frame
        logger.info("Response queue declared ok: %s", _userdata)
        self.declare_service_queue()

    def on_bindok(self, _frame: pika.frame.Method, userdata: str) -> None:
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will set the prefetch count for the channel.

        :param pika.frame.Method _frame: The Queue.BindOk response frame
        :param str|unicode userdata: Extra user data (queue name)
        """
        logger.info("Response queue bound ok: %s", userdata)
        """This method sets up the consumer prefetch to only be delivered
        one message at a time. The consumer must acknowledge this message
        before RabbitMQ will deliver another one. You should experiment
        with different prefetch values to achieve desired performance.
        """
        if self._channel is None:
            raise RuntimeError("RMQ transport channel is not open")

        self._channel.basic_qos(
            prefetch_count=self._prefetch_count, callback=self.on_basic_qos_ok
        )

    def on_basic_qos_ok(self, _frame: pika.frame.Method) -> None:
        """Invoked by pika when the Basic.QoS method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        :param pika.frame.Method _frame: The Basic.QosOk response frame

        This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_service_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        logger.info("QOS set to: %d", self._prefetch_count)
        logger.info("Configure message consumption")

        """Add a callback that will be invoked if RabbitMQ cancels the consumer for some reason. 
        If RabbitMQ does cancel the consumer, on_consumer_cancelled will be invoked by pika.
        """
        if self._channel is None:
            raise RuntimeError("RMQ transport channel is not open")

        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

        # Start consuming the response queue these need their own handler as the ack type is automatic
        self._consumer_tags.add(
            self._channel.basic_consume(
                on_message_callback=functools.partial(
                    self.on_response_message, self._response_queue
                ),
                auto_ack=True,
                queue=self._response_queue,
                exclusive=True,
            )
        )

        # Start consuming the requests queue
        if not self._client_only:
            logger.info("Consuming Requests, Events and Commands")
            self._consumer_tags.add(
                self._channel.basic_consume(
                    on_message_callback=functools.partial(
                        self.on_service_message, self._service_queue
                    ),
                    queue=self._service_queue,
                )
            )

        self._was_consuming = True
        self._consuming = True

        if self._connected_future:
            self._connected_future.set_result(True)
        self._connected = True

    def on_consumer_cancelled(self, method_frame: pika.frame.Method) -> None:
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame
        """
        logger.info(
            f"Consumer was cancelled remotely, closing the current channel. Reason: {method_frame}"
        )
        if self._channel:
            self._channel.close()

    def on_message_returned(
        self,
        channel: pika.channel.Channel,  # noqa
        method: pika.spec.Basic.Return,
        properties: pika.spec.BasicProperties,
        body: bytes,  # noqa
    ) -> None:
        """Called when message has been rejected by the server.

        callable callback: The function to call, having the signature callback(channel, method, properties, body)

        :param channel: pika.Channel
        :param method: pika.spec.Basic.Deliver
        :param properties: pika.spec.BasicProperties
        :param body: bytes
        """
        _ = channel, body
        correlation_id = properties.correlation_id
        trace_id = properties.headers.get("trace_id", "unknown")
        nuropb_type = properties.headers.get("nuropb_type", "unknown")
        nuropb_version = properties.headers.get("nuropb_version", "unknown")
        logger.warning(
            f"Could not route {nuropb_type} message ro service {method.routing_key} "
            f"correlation_id: {correlation_id} "
            f"trace_id: {trace_id} "
            f": {method.reply_code}, {method.reply_text}"
        )
        """ End the awaiting request future with a NuropbNotDeliveredError
        """
        if nuropb_type == "request":
            nuropb_payload = decode_payload(body, "json")
            request_method = nuropb_payload["method"]
            nuropb_payload["tag"] = nuropb_type
            nuropb_payload["error"] = {
                "error": "NuropbNotDeliveredError",
                "description": f"Service {method.routing_key} not available. unable to call method {request_method}",
            }
            nuropb_payload["result"] = None
            nuropb_payload.pop("service", None)
            nuropb_payload.pop("method", None)
            nuropb_payload.pop("params", None)
            nuropb_payload.pop("reply_to", None)
            message = TransportRespondPayload(
                nuropb_protocol=NUROPB_PROTOCOL_VERSION,
                correlation_id=correlation_id,
                trace_id=trace_id,
                ttl=None,
                nuropb_type="response",
                nuropb_payload=nuropb_payload,
            )
            metadata = {
                "start_time": time.time(),
                "service_name": self._service_name,
                "instance_id": self._instance_id,
                "is_leader": self._is_leader,
                "client_only": self._client_only,
                "nuropb_type": nuropb_type,
                "nuropb_version": nuropb_version,
                "correlation_id": properties.correlation_id,
                "trace_id": properties.headers.get("trace_id", "unknown"),
            }

            message_complete_callback = functools.partial(
                self.on_service_message_complete,
                channel,
                "",
                "",
                metadata,
            )
            self._message_callback(message, message_complete_callback, metadata)

        if verbose:
            raise NuropbNotDeliveredError(
                (
                    f"Could not route message {nuropb_type} with "
                    f"correlation_id: {correlation_id} "
                    f"trace_id: {trace_id} "
                    f": {method.reply_code}, {method.reply_text}"
                )
            )

    def send_message(
        self,
        exchange: str,
        routing_key: str,
        body: bytes,
        properties: Dict[str, Any],
        mandatory: Optional[bool] = None,
    ) -> None:
        """Send a message to over the RabbitMQ Transport

            TODO: Consider the handling if the channel that's closed. Wait and retry on a new channel?
            - setup a retry queue?
            - should there be a high water mark for the number of retries?
            - should new messages not be consumed until the channel is re-established and retry queue drained?

        :param str exchange: The exchange to publish to
        :param str routing_key: The routing key to publish with
        :param bytes body: The message body
        :param Dict[str, Any] properties: The message properties
        :param bool mandatory: The mandatory flag, defaults to True
        """
        mandatory = True if mandatory is None else mandatory
        headers = properties.setdefault("headers", {})
        headers.update(
            {
                "nuropb_protocol": NUROPB_PROTOCOL_VERSION,
            }
        )
        properties["headers"] = headers
        if self._channel is None or self._channel.is_closed:
            lifecycle: NuropbLifecycleState = "client-send"
            if properties.get("headers", {}).get("nuropb_type", "") == "response":
                lifecycle = "service-reply"

            payload: PayloadDict | None = None
            if properties.get("content_type", "") == "application/json":
                payload = cast(PayloadDict, decode_payload(body, "json"))

            raise NuropbTransportError(
                description="RMQ channel closed, send message",
                lifecycle=lifecycle,
                payload=payload,
                exception=None,
            )

        else:
            basic_properties = pika.BasicProperties(**properties)
            self._channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
                properties=basic_properties,
                mandatory=mandatory,
            )

    @classmethod
    def acknowledge_service_message(
        cls,
        channel: Channel,
        delivery_tag: int,
        action: Literal["ack", "nack", "reject"],
        redelivered: bool,
    ) -> None:
        """Acknowledgement of a service message

        In NuroPb, acknowledgements of service message requests have three possible outcomes:
        - ack: Successfully processed, acknowledged and removed from the queue
        - nack: A recoverable error occurs, the message is not acknowledged and requeued
        - reject: An unrecoverable error occurs, the message is not acknowledged and dropped

        To prevent accidental use of the redelivered parameter and to ensure system
        predictability on the Call Again feature, messages are only allowed to be redelivered
        once and only once. To this end all messages that have redelivered == True will be
        rejected. if redelivered is overridden with None, it is assumed True.

        :param pika.channel.Channel channel: The channel object
        :param int delivery_tag: The delivery tag
        :param str action: The action to take, one of ack, nack or reject
        :param bool redelivered: True if the message is being requeued / replayed.
        """
        redelivered = True if redelivered is None else redelivered
        if action == "ack":
            channel.basic_ack(delivery_tag=delivery_tag)
        elif action == "nack":
            if redelivered:
                logger.debug(
                    "Redelivered is True, action is overridden from {action} to rejected"
                )
                channel.basic_reject(delivery_tag=delivery_tag, requeue=False)
                raise NuropbCallAgainReject("Redelivered message is rejecting")
            else:
                if verbose:
                    logger.debug(
                        "Redelivered is False, first time nack and requeue is allowed"
                    )
                channel.basic_nack(delivery_tag=delivery_tag, requeue=True)
        elif action == "reject":
            channel.basic_reject(delivery_tag=delivery_tag, requeue=False)
        else:
            raise ValueError(f"Invalid action {action}")

    def send_response_messages(
        self, reply_to: str, message: TransportRespondPayload
    ) -> None:
        """Send response to request messages and also event messages. These messages can be over
        new connections and channels. Any exceptions need to be contained and handled within the
        scope of this method.
        """
        correlation_id = "unknown"
        trace_id = "unknown"
        try:
            nuropb_type = message["nuropb_type"]
            correlation_id = message["correlation_id"] or "unknown"
            trace_id = message["trace_id"] or "unknown"
            if nuropb_type == "response":
                routing_key = reply_to
                exchange = ""
                ttl = ""
            else:
                routing_key = ""
                exchange = self._events_exchange
                ttl = str(message.get("ttl") or self._default_ttl)

            body = encode_payload(message["nuropb_payload"], "json")
            properties = {
                "content_type": "application/json",
                "correlation_id": message["correlation_id"],
                "headers": {
                    "nuropb_type": nuropb_type,
                    "nuropb_protocol": NUROPB_PROTOCOL_VERSION,
                    "trace_id": trace_id,
                },
            }
            if ttl:
                properties["expiration"] = ttl

            self.send_message(
                exchange, routing_key, body, properties=properties, mandatory=True
            )
        except Exception as error:
            logger.critical(
                f"Error sending message in response to request correlation_id: {correlation_id}, trace_id: {trace_id}"
            )
            logger.exception(f"Failed to send response message: Error: {error}")

    @classmethod
    def metadata_metrics(cls, metadata: Dict[str, Any]) -> None:
        """Invoked by the transport after a service message has been processed.

        NOTE - METADATA: keep this metadata in sync with across all these methods:
            - on_service_message, on_service_message_complete
            - on_response_message, on_response_message_complete
            - metadata_metrics

        :param metadata: information to drive message processing metrics
        :return: None
        """
        logger.debug(f"metadata log: {metadata}")

    def on_service_message_complete(
        self,
        channel: Channel,
        basic_deliver: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        private_metadata: Dict[str, Any],
        response_messages: List[TransportRespondPayload],
        acknowledgement: AcknowledgeAction,
    ) -> None:
        """Invoked by the implementation after a service message has been processed.

        This is provided to the implementation as a helper function to complete the message flow.
        The message flow state parameters: channel, delivery_tag, reply_to and private_metadata
        are hidden from the implementation through the use of functools.partial. The interface
        of this function as it appears to the implementation is:
            response_messages:  List[TransportRespondPayload]
            acknowledgement: Literal["ack", "nack", "reject"]

        NOTE: The acknowledgement references the incoming service message that resulted in
              these responses

        :param channel:
        :param pika.spec.Basic.Deliver basic_deliver: basic_deliver method
        :param pika.spec.BasicProperties properties: properties
        :param private_metadata: information to drive message processing metrics
        :param response_messages: List[TransportRespondPayload]
        :param acknowledgement:
        :return:
        """
        delivery_tag = basic_deliver.delivery_tag
        redelivered = basic_deliver.redelivered
        reply_to = properties.reply_to

        if redelivered is True and acknowledgement == "nack":
            if verbose:
                logger.debug(
                    "Redelivered is True, action is overridden from nack to rejected"
                )
            acknowledgement = "reject"
            if properties.headers.get("nuropb_type", "") == "request":
                trace_id = properties.headers.get("trace_id", "unknown")
                correlation_id = properties.correlation_id
                exception = NuropbCallAgainReject(
                    description=(
                        f"Rejecting second call again request for trace_id: {trace_id}"
                        f", correlation_id: {correlation_id}"
                    )
                )
                response_messages[0]["nuropb_payload"][
                    "error"
                ] = error_dict_from_exception(exception=exception)
            else:
                response_messages = []
        elif acknowledgement == "nack":
            response_messages = []

        self.acknowledge_service_message(
            channel, delivery_tag, acknowledgement, redelivered
        )

        for respond_message in response_messages:
            reply_to = reply_to or ""
            self.send_response_messages(reply_to, respond_message)

        """ NOTE - METADATA: keep this dictionary in sync with across all these methods:
            - on_service_message, on_service_message_complete
            - on_response_message, on_response_message_complete
            - metadata_metrics
        """
        private_metadata["end_time"] = time.time()
        private_metadata["duration"] = (
            private_metadata["end_time"] - private_metadata["start_time"]
        )
        private_metadata["acknowledgement"] = acknowledgement
        private_metadata["message_count"] = len(response_messages)
        private_metadata["flow_complete"] = True
        self.metadata_metrics(metadata=private_metadata)

    def on_service_message(
        self,
        queue_name: str,
        channel: Channel,
        basic_deliver: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Invoked when a message is delivered to the service_queue.

        DESIGN PARAMETERS:
            - Incoming service messages handling (this) require a deliberate acknowledgement.
                * Acknowledgements must be sent on the same channel and with the same delivery tag
            - Incoming response messages (on_response_message) are automatically acknowledged
            - Not all service messages require a response, e.g. events and commands
            - Transport must remain agnostic to the handling of the service message

        OTHER DESIGN CONSIDERATIONS:
            - Connections to the RabbitMQ broker should be authenticated, and encrypted using TLS
            - Payload data not used for NuroPb message handling should be separately encrypted,
              and specially when containing sensitive data e.g. PI or PII .

        FLOW DESIGN:
        1. Python json->dict compatible message is received from the service request (rpc) queue
        2. message is decoded into a python typed dictionary: TransportServicePayload
        3. this message is passed to the message_callback which has no return value, but may raise any
            type of exception.
            - message_callback is provided by the implementation and supplied on transport instantiation
            - message_callback is responsible for handling all exceptions, acknowledgements and
              appropriate responses
            - a helper function is provided that will handle message acknowledgement and any responses.
                the function has all the required state to do so. See note 4 below.
        4. State required to be preserved until the message is acknowledged:
            - channel + delivery_tag
            - reply_to
            - correlation_id
            - trace_id
            - incoming decoded message
        5. This state can only exist in-memory as it's not all "picklable" and bound to the current open channel
        6. If an exception is raised, then the message is immediately rejected and dropped.

        (transport) -> on_service_message
            -> (transport) message_callback(TransportServicePayload, MessageCompleteFunction, Dict[str, Any])
                -> (api) message_complete_callback(List[TransportRespondPayload], AcknowledgeAction)
                    -> (transport) acknowledge_service_message(channel, delivery_tag, action)
                    -> (transport) send_response_messages(reply_to, response_messages)
                    -> (transport) metadata_metrics(metadata)

        # TODO: Needing to think about excessive errors and decide on a strategy for for shutting down
        #       the service instance. Should this take place in the transport layer or the API ?
        # - what happens to the result if the channel is closed?
        # - What happens if the request is resent, can we leverage the existing result
        # - what happens if the request is resent to another service worker?
        # - what happens to the request sender waiting for a response?

        NOTES:
        * Call Again:
        When a message is nack'd and requeued, there is no current way to track how many
        times this may have occurred for the same message. To ensure stability, behaviour
        predictability and to limit the abuse of patterns, the use of NuropbCallAgain is
        limited to once and only once. This is enforced at the transport layer. For RabbitMQ
        if the incoming message is a requeued message, the basic_deliver.redelivered is
        True. Call again for all redelivered messages will be rejected.

        :param str queue_name: The name of the queue that the message was received on
        :param pika.channel.Channel channel: The channel object
        :param pika.spec.Basic.Deliver basic_deliver: basic_deliver method
        :param pika.spec.BasicProperties properties: properties
        :param bytes body: The message body
        """
        nuropb_type = properties.headers.get("nuropb_type", "")
        nuropb_version = properties.headers.get("nuropb_version", "")
        if not verbose:
            logger.debug(f"service message received: '{nuropb_type}'")
        else:
            logger.debug(
                f"""MESSAGE FROM SERVICE QUEUE:
delivery_tag: {basic_deliver.delivery_tag}
from_exchange: {basic_deliver.exchange}
from_queue: {queue_name}
routing_key: {basic_deliver.routing_key}
correlation_id: {properties.correlation_id}
trace_id: {properties.headers.get('trace_id', '')}
content_type: {properties.content_type}
nuropb_type: {nuropb_type}
nuropb_version: {nuropb_version}
"""
            )
        """ Handle for the unknown message type and reply to the originator if possible
        """
        nuropb_version = properties.headers.get("nuropb_version", "")

        """ NOTE - METADATA: keep this dictionary in sync with across all these methods:
            - on_service_message, on_service_message_complete
            - on_response_message, on_response_message_complete
            - metadata_metrics
        """
        metadata = {
            "start_time": time.time(),
            "service_name": self._service_name,
            "instance_id": self._instance_id,
            "is_leader": self._is_leader,
            "client_only": self._client_only,
            "nuropb_type": nuropb_type,
            "nuropb_version": nuropb_version,
            "correlation_id": properties.correlation_id,
            "trace_id": properties.headers.get("trace_id", "unknown"),
        }

        message_complete_callback = functools.partial(
            self.on_service_message_complete,
            channel,
            basic_deliver,
            properties,
            metadata,
        )

        """ Decode service message
        """
        try:
            service_message = decode_rmq_body(basic_deliver, properties, body)
        except Exception as error:
            """Exceptions caught here are treated as permanent failures, ack the message and send
            error response is possible
            """
            logger.exception(f"Service message decode error: {error}")
            self.acknowledge_service_message(
                channel, basic_deliver.delivery_tag, "reject", basic_deliver.redelivered
            )

            try:
                (
                    acknowledgement,
                    responses,
                ) = create_transport_response_from_rmq_decode_exception(
                    exception=error, basic_deliver=basic_deliver, properties=properties
                )
                message_complete_callback(responses, acknowledgement)
            except Exception as err:
                logger.debug(
                    f"Failed to send service message decode error response: {err}"
                )

            return

        """ NEXT: handle the service message
        
            Acknowledgement of the message can only take place on this channel and using
            the delivery tag of this message. if the channel is closed before the message is
            acknowledged, then the message will be requeued and redelivered to a new channel
            and potentially a new service worker.

            Any errors caught here are treated as permanent failures, rejected and dropped.        
        """
        try:
            """Assume for now that we can't use key word arguments in self.message_callback"""
            self._message_callback(service_message, message_complete_callback, metadata)

        except Exception as error:
            """Exceptions caught here are treated as permanent failures, ack the message and send error response"""
            logger.exception(f"service message handling error: {error}")
            try:
                (
                    acknowledgement,
                    responses,
                ) = create_transport_response_from_rmq_decode_exception(
                    exception=error, basic_deliver=basic_deliver, properties=properties
                )
                message_complete_callback(responses, acknowledgement)
            except Exception as err:
                logger.debug(f"Failed to send service handling error response: {err}")
            return

    def on_response_message_complete(
        self,
        channel: Channel,
        basic_deliver: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        private_metadata: Dict[str, Any],
        response_messages: List[TransportRespondPayload],
        acknowledgement: AcknowledgeAction,
    ) -> None:
        """Invoked by the implementation after a service message has been processed.

        This is provided to the implementation as a helper function to complete the message flow.
        The message flow state parameters: channel, delivery_tag, reply_to and private_metadata
        are hidden from the implementation through the use of functools.partial. The interface
        of this function as it appears to the implementation is:
            response_messages:  List[TransportRespondPayload]
            acknowledgement: Literal["ack", "nack", "reject"]

        NOTE: The acknowledgement references the incoming service message that resulted in
              these responses

        :param channel:
        :param pika.spec.Basic.Deliver basic_deliver: basic_deliver method
        :param pika.spec.BasicProperties properties: properties
        :param private_metadata: information to drive message processing metrics
        :param response_messages: List[TransportRespondPayload]
        :param acknowledgement:
        :return:
        """
        _ = channel, basic_deliver, properties

        if acknowledgement != "ack":
            logger.warning(
                f"Response messages are auto-acknowledged, ignoring {acknowledgement}"
            )
            acknowledgement = "ack"

        """ Response messages are received from the response queue which is configured for 
        auto-acknowledgement. Code below is for reference only in the event that auto-acknowledgement 
        is disabled or a durable queue is used with explicit acknowledgement.
        
        self.acknowledge_service_message(channel, delivery_tag, acknowledgement, redelivered)
        """

        if len(response_messages) > 0:
            logger.warning(
                "Response messages are not themselves allowed to have response replies, ignoring"
            )

        """ NOTE - METADATA: keep this dictionary in sync with across all these methods:
        - on_service_message, on_service_message_complete
        - on_response_message, on_response_message_complete
        - metadata_metrics
        """
        private_metadata["end_time"] = time.time()
        private_metadata["duration"] = (
            private_metadata["end_time"] - private_metadata["start_time"]
        )
        private_metadata["acknowledgement"] = acknowledgement
        private_metadata["message_count"] = 0
        private_metadata["flow_complete"] = True
        self.metadata_metrics(metadata=private_metadata)

    def on_response_message(
        self,
        _queue_name: str,
        channel: pika.channel.Channel,  # noqa
        basic_deliver: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Invoked when a message is delivered to the response_queue. The channel is passed for
        your convenience. The basic_deliver object that is passed in carries the exchange,
        routing key, delivery tag and a redelivered flag for the message. The properties passed
        in is an instance of BasicProperties with the message properties and the body is the
        message that was sent.

        :param str _queue_name: The name of the queue that the message was received on
        :param pika.channel.Channel channel: The channel object
        :param pika.spec.Basic.Deliver basic_deliver: basic_deliver
        :param pika.spec.BasicProperties properties: properties
        :param bytes body: The message body
        """
        nuropb_type = properties.headers.get("nuropb_type", "")
        nuropb_version = properties.headers.get("nuropb_version", "")
        if not verbose:
            logger.debug(f"response message received: '{nuropb_type}'")
        else:
            logger.debug(
                (
                    f"MESSAGE FROM RESPONSE QUEUE:\n"
                    f"delivery_tag: {basic_deliver.delivery_tag}\n"
                    f"service_name: {self._service_name}\n"
                    f"instance_id: {self._instance_id}\n"
                    f"exchange: {basic_deliver.exchange}\n"
                    f"routing_key: {basic_deliver.routing_key}\n"
                    f"correlation_id: {properties.correlation_id}\n"
                    f"trace_id: {properties.headers.get('trace_id', '')}\n"
                    f"content_type: {properties.content_type}\n"
                    f"nuropb_type: {nuropb_type}\n"
                    f"nuropb_version: {nuropb_version}\n"
                )
            )
        try:
            """NOTE - METADATA: keep this dictionary in sync with across all these methods:
            - on_service_message, on_service_message_complete
            - on_response_message, on_response_message_complete
            - metadata_metrics
            """
            metadata = {
                "start_time": time.time(),
                "service_name": self._service_name,
                "instance_id": self._instance_id,
                "is_leader": self._is_leader,
                "client_only": self._client_only,
                "nuropb_type": nuropb_type,
                "nuropb_version": nuropb_version,
                "correlation_id": properties.correlation_id,
                "trace_id": properties.headers.get("trace_id", "unknown"),
            }
            message_complete_callback = functools.partial(
                self.on_service_message_complete,
                channel,
                basic_deliver.delivery_tag,
                properties.reply_to,
                metadata,
            )
            message = decode_rmq_body(basic_deliver, properties, body)
            self._message_callback(message, message_complete_callback, metadata)
        except Exception as err:
            logger.exception(
                (
                    f"Error processing response message # {basic_deliver.delivery_tag}: {err}\n"
                    f"correlation_id: {properties.correlation_id}\n"
                    f"trace_id: {properties.headers.get('trace_id', '')}\n"
                )
            )

    async def stop_consuming(self) -> None:
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.
        """
        if self._channel:
            logger.info("Sending a Basic.Cancel RPC command to RabbitMQ")
            logger.info("Closing consumers %s", self._consumer_tags)

            all_consumers_closed: Awaitable[bool] = asyncio.Future()

            def _on_cancel_ok(frame: pika.frame.Method) -> None:
                logger.info("Consumer %s closed ok", frame.method.consumer_tag)
                self._consumer_tags.remove(frame.method.consumer_tag)
                if len(self._consumer_tags) == 0:
                    all_consumers_closed.set_result(True)  # type: ignore[attr-defined]

            for consumer_tag in self._consumer_tags:
                if self._channel:
                    self._channel.basic_cancel(consumer_tag, _on_cancel_ok)
            logger.info(
                "Waiting for %ss for consumers to close", CONSUMER_CLOSED_WAIT_TIMEOUT
            )
            try:
                await asyncio.wait_for(
                    all_consumers_closed, timeout=CONSUMER_CLOSED_WAIT_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.error(
                    "Timed out while waiting for all consumers to gracefully close"
                )

            if len(self._consumer_tags) != 0:
                logger.error(
                    "Timed out while waiting for all consumers to gracefully close"
                )

            self._consuming = False
            logger.info("RabbitMQ acknowledged the cancellation of the consumer")
            self.close_channel()

    def close_channel(self) -> None:
        """Call to close the channel with RabbitMQ cleanly by issuing the Channel.Close RPC command."""
        logger.info("Closing the channel")
        if self._channel is None or self._channel.is_closed:
            logger.info("Channel is already closed")
        else:
            self._channel.close()
