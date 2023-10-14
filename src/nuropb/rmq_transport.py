import logging
import functools
from typing import List, Set, Optional, Any, Dict, Awaitable, Literal, TypedDict, cast
import asyncio
import time

import pika
from pika import connection
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from pika.exceptions import (
    ChannelClosedByBroker,
    ProbableAccessDeniedError,
    ChannelClosedByClient,
)
import pika.spec
from pika.frame import Method

from nuropb.encodings.encryption import Encryptor
from nuropb.encodings.serializor import encode_payload, decode_payload
from nuropb.interface import (
    NuropbTransportError,
    TransportServicePayload,
    NUROPB_PROTOCOL_VERSIONS_SUPPORTED,
    NUROPB_MESSAGE_TYPES,
    TransportRespondPayload,
    MessageCallbackFunction,
    AcknowledgeAction,
    NUROPB_PROTOCOL_VERSION,
    NUROPB_VERSION,
    NuropbCallAgainReject,
    RequestPayloadDict,
    ResponsePayloadDict,
)
from nuropb.rmq_lib import (
    create_virtual_host,
    configure_nuropb_rmq,
    get_connection_parameters,
)
from nuropb.contexts import service_handlers
from nuropb.contexts.service_handlers import (
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

connection.PRODUCT = "NuroPb Distributed RPC-Event Service Mesh Library"
""" TODO: configure the RMQ client connection attributes in the pika client properties.
See related TODO below in this module
"""

CONSUMER_CLOSED_WAIT_TIMEOUT = 10
""" The wait when shutting down consumers before closing the connection
"""

_verbose = False


@property
def verbose() -> bool:
    return _verbose


@verbose.setter
def verbose(value: bool) -> None:
    global _verbose
    _verbose = value
    service_handlers.verbose = value


""" Set to True to enable module verbose logging
"""


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
    """RMQTransport is the base class for the RabbitMQ transport. It wraps the
    NuroPb service mesh patterns and rules over the AMQP protocol.

    When RabbitMQ closes the connection, this class will stop and alert that
    reconnection is necessary, in some cases re-connection takes place automatically.
    Disconnections should be continuously monitored, there are various reasons why a
    connection or channel may be closed after being successfully opened, and usually
    related to authentication, permissions, protocol violation or networking.

    TODO: Configure the Pika client connection attributes in the pika client properties.
    """

    _service_name: str
    _instance_id: str
    _amqp_url: str | Dict[str, Any]
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
    _encryptor: Encryptor | None

    _connected_future: Any
    _disconnected_future: Any

    _is_leader: bool
    _is_rabbitmq_configured: bool

    _connection: AsyncioConnection | None
    _channel: Channel | None
    _consumer_tags: Set[Any]
    _consuming: bool
    _connecting: bool
    _closing: bool
    _connected: bool
    _was_consuming: bool

    def __init__(
        self,
        service_name: str,
        instance_id: str,
        amqp_url: str | Dict[str, Any],
        message_callback: MessageCallbackFunction,
        default_ttl: Optional[int] = None,
        client_only: Optional[bool] = None,
        encryptor: Optional[Encryptor] = None,
        **kwargs: Any,
    ):
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.

        :param str service_name: The name of the service
        :param str instance_id: The instance id of the service
        :param str amqp_url: The AMQP url to connect string or TLS connection details
            - cafile: str | None
            - certfile: str | None
            - keyfile: str | None
            - verify: bool (default True)
            - hostname: str
            - port: int
            - username: str
            - password: str
        :param MessageCallbackFunction message_callback: The callback to call when a message is received
        :param int default_ttl: The default time to live for messages in milliseconds, defaults to 12 hours.
        :param bool client_only:
        :param Encryptor encryptor: The encryptor to use for encrypting and decrypting messages
        :param kwargs: Mostly transport configuration options
            - str rpc_exchange: The name of the RPC exchange
            - str events_exchange: The name of the events exchange
            - str dl_exchange: The name of the dead letter exchange
            - str dl_queue: The name of the dead letter queue
            - str service_queue: The name of the requests queue
            - str response_queue: The name of the responses queue
            - List[str] rpc_bindings: The list of RPC bindings
            - List[str] event_bindings: The list of events bindings
            - int prefetch_count: The number of messages to prefetch defaults to 1, unlimited is 0.
                    Experiment with larger values for higher throughput in your user case.

            When an existing transport is initialised and connected, and a subsequent transport
            instance is connected with the same service_name and instance_id as the first, the broker
            will shut down the channel of subsequent instances when they attempt to configure their
            response queue. This is because the response queue is opened in exclusive mode. The
            exclusive mode is used to ensure that only one consumer (nuropb api connection) is
            consuming from the response queue.

            Deliberately specifying a fixed instance_id, is a valid mechanism to ensure that a service
            can only run in single instance mode. This is useful for services that are not designed to
            be run in a distributed manner or where there is specific service configuration required.
        """
        self._connected = False
        self._closing = False
        self._connecting = False
        self._was_consuming = False
        self._consuming = False

        self._connection = None
        self._channel = None
        self._consumer_tags = set()

        self._client_only = False if client_only is None else client_only
        """ If client_only is True, then the transport will not configure a service queue with
        the handling of requests, commands and events disabled. 
        """
        rpc_bindings = set(kwargs.get("rpc_bindings", []) or [])
        event_bindings = set(kwargs.get("event_bindings", []) or [])
        if self._client_only:
            logger.info("Client only transport")
            rpc_bindings = set()
            event_bindings = set()

        self._encryptor = encryptor

        # Experiment with larger values for higher throughput.
        self._service_name = service_name
        self._instance_id = instance_id
        self._amqp_url = amqp_url
        self._rpc_exchange = kwargs.get("rpc_exchange", None) or "nuropb-rpc-exchange"
        self._events_exchange = (
            kwargs.get("events_exchange", None) or "nuropb-events-exchange"
        )
        self._dl_exchange = kwargs.get("dl_exchange", None) or "nuropb-dl-exchange"
        self._dl_queue = (
            kwargs.get("dl_queue", None) or f"nuropb-{self._service_name}-dl"
        )
        self._service_queue = (
            kwargs.get("service_queue", None) or f"nuropb-{self._service_name}-sq"
        )
        self._response_queue = (
            kwargs.get("response_queue", None)
            or f"nuropb-{self._service_name}-{self._instance_id}-rq"
        )
        self._rpc_bindings = rpc_bindings
        self._event_bindings = event_bindings
        self._prefetch_count = (
            1
            if kwargs.get("prefetch_count", None) is None
            else kwargs.get("prefetch_count", 1)
        )
        self._default_ttl = default_ttl or 60 * 60 * 1000 * 12  # 12 hours
        self._message_callback = message_callback
        self._rpc_bindings.add(self._service_name)

        self._is_leader = True
        self._is_rabbitmq_configured = False

        self._connected_future = None
        self._disconnected_future = None

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def amqp_url(self) -> str | Dict[str, Any]:
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
        amqp_url: Optional[str | Dict[str, Any]] = None,
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
        # rmq_api_url = rmq_api_url or rmq_api_url_from_amqp_url(amqp_url)
        if rmq_api_url is None:
            raise ValueError("rmq_api_url is not provided")
        try:
            create_virtual_host(rmq_api_url, amqp_url)
            configure_nuropb_rmq(
                rmq_url=amqp_url,
                events_exchange=rmq_configuration["events_exchange"],
                rpc_exchange=rmq_configuration["rpc_exchange"],
                dl_exchange=rmq_configuration["dl_exchange"],
                dl_queue=rmq_configuration["dl_queue"],
            )
            self._is_rabbitmq_configured = True
            time.sleep(5)
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
            if self._connected_future.done():
                err = self._connected_future.exception()
                if isinstance(err, NuropbTransportError) and err.close_connection:
                    await self.stop()
                elif err is not None:
                    raise err
        except ProbableAccessDeniedError as err:
            if isinstance(self._amqp_url, dict):
                vhost = self._amqp_url.get("vhost", "")
            else:
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
        except NuropbTransportError as err:
            """Logging already captured, handle the error, likely a channel closed by broker"""
            if not self._connected_future.done():
                self._connected_future.set_exception(err)
                if err.close_connection:
                    await self.stop()

        except Exception as err:
            logger.exception(
                "General failure connecting to RabbitMQ. %s: %s",
                type(err).__name__,
                err,
            )
            if not self._connected_future.done():
                self._connected_future.set_exception(err)

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
        if not self._closing:
            logger.info("Stopping")
            try:
                if self._consuming:
                    await self.stop_consuming()
            except Exception as err:
                logger.exception(f"Error stopping consuming: {err}")
            self._disconnected_future = self.disconnect()
            await self._disconnected_future

    def connect(self) -> asyncio.Future[bool]:
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

        connection_parameters = get_connection_parameters(
            amqp_url=self._amqp_url,
            name=self._service_name,
            instance_id=self._instance_id,
            client_only=self._client_only,
        )
        conn = AsyncioConnection(
            parameters=connection_parameters,
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed,
        )
        self._connection = conn
        self._connecting = True
        return self._connected_future

    def disconnect(self) -> Awaitable[bool]:
        """This method closes the connection to RabbitMQ. the pika library events will drive
        the closing and reconnection process.
        :return: asyncio.Future
        """
        if self._connection is None:
            logger.info("RMQ transport is not connected")
        elif self._connection.is_closing or self._connection.is_closed:
            logger.info("RMQ transport is already closing or closed")

        if self._connection is None or not self._connected:
            disconnected_future: asyncio.Future[bool] = asyncio.Future()
            disconnected_future.set_result(True)
            return disconnected_future

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
        self, conn: AsyncioConnection, reason: Exception
    ) -> None:
        """This method is called by pika if the connection to RabbitMQ can't be established.

        :param pika.adapters.asyncio_connection.AsyncioConnection conn:
        :param Exception reason: The error
        """
        logger.error("Connection open Error. %s: %s", type(reason).__name__, reason)
        if self._connected_future is not None and not self._connected_future.done():
            if isinstance(reason, ProbableAccessDeniedError):
                close_connection = True
            else:
                close_connection = False
            self._connected_future.set_exception(
                NuropbTransportError(
                    description=f"Connection open Error. {type(reason).__name__}: {reason}",
                    exception=reason,
                    close_connection=close_connection,
                )
            )
        if self._connecting:
            self._connecting = False

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
        logger.warning("Connection closed. reason: %s", reason)
        if (
            self._disconnected_future is not None
            and not self._disconnected_future.done()
        ):
            self._disconnected_future.set_result(True)

        self._connected = False
        self._channel = None

        if self._closing:
            self._closing = False
        else:
            self._connecting = False
            # self.connect()
            asyncio.create_task(self.start())

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
        """Invoked by pika when the channel is closed. Channels are at times close by the
        broker for various reasons, the most common being protocol violations e.g. acknowledging
        messages using an invalid message_tag. In most cases when the channel is closed by
        the broker, nuropb will automatically open a new channel and re-declare the service queue.

        In the following cases the channel is not automatically re-opened:
            * When the connection is closed by this transport API
            * When the connection is close by the broker 403 (ACCESS_REFUSED):
                Typically these examples are seen:
                - "Provided JWT token has expired at timestamp". In this case the transport will
                    require a fresh JWT token before attempting to reconnect.
                - queue 'XXXXXXX' in vhost 'YYYYY' in exclusive use. In this case there is another
                    response queue setup with the same name. Having a fixed response queue name is
                    a valid mechanism to enforce a single instance of a service.
            * When the connection is close by the broker 403 (NOT_FOUND):
                Typically where there is an exchange configuration issue.

        Always investigate the reasons why a channel is closed and introduce logic to handle
        that scenario accordingly. It is important to continuously monitor for this condition.

        TODO: When there is message processing in flight, and particularly with a prefetch
            count > 1, then those messages are now not able to be acknowledged. By doing so will
            result in a forced channel closure by the broker and potentially a poison pill type
            scenario.

        :param pika.channel.Channel channel: The closed channel
        :param Exception reason: why the channel was closed
        """
        if isinstance(reason, ChannelClosedByBroker):
            if reason.reply_code == 403 and self._response_queue in reason.reply_text:
                reason_description = (
                    f"RabbitMQ channel closed by the broker ({reason.reply_code})."
                    " There is already a response queue setup with the same name and instance_id,"
                    " and hence this service is considered single instance only"
                )
            elif (
                reason.reply_code == 403
                and "Provided JWT token has expired" in reason.reply_text
            ):
                reason_description = (
                    f"RabbitMQ channel closed by the broker ({reason.reply_code})."
                    f" AuthenticationExpired: {reason.reply_text}"
                )
            else:
                reason_description = (
                    f"RabbitMQ channel closed by the broker "
                    f"({reason.reply_code}): {reason.reply_text}"
                )

            logger.critical(reason_description)
            if self._connected_future and not self._connected_future.done():
                """the Connection is still in press and when the channel was closed by the broker
                so treat as a serious error and close the connection
                """
                self._connected_future.set_exception(
                    NuropbTransportError(
                        description=reason_description,
                        exception=reason,
                        close_connection=True,
                    )
                )

            elif self._connected_future and self._connected_future.done():
                """The channel was close after the connection was established"""
                if reason.reply_code in (403, 404):
                    """There is no point in auto reconnecting when access is refused, so
                    shut the connection down.
                    """
                    asyncio.create_task(self.stop())
                else:
                    """It's ok to try and re-open the channel"""
                    logging.info("Re-opening channel")
                    self.open_channel()

        elif not isinstance(reason, ChannelClosedByClient):
            """Log the reason for the channel close and allow the re-open process to continue"""
            reason_description = (
                f"RabbitMQ channel closed ({reason.reply_code})."
                f"{type(reason).__name__}: {reason}"
            )
            logger.warning(reason_description)

    def declare_service_queue(self, frame: pika.frame.Method) -> None:
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
            # Check that passing None in here is OK
            self.on_bindok(frame, userdata=self._response_queue)

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
        self.declare_service_queue(frame)

    def on_bindok(self, _frame: pika.frame.Method, userdata: str) -> None:
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will set the prefetch count for the channel.

        :param pika.frame.Method _frame: The Queue.BindOk response frame
        :param str|unicode userdata: Extra user data (queue name)
        """
        logger.info("Response queue bound ok: %s", userdata)
        if self._channel is None:
            raise RuntimeError("RMQ transport channel is not open")

        self._channel.basic_qos(
            prefetch_count=self._prefetch_count, callback=self.on_basic_qos_ok
        )

    def on_basic_qos_ok(self, _frame: pika.frame.Method) -> None:
        """Invoked by pika when the Basic.QoS method has completed. At this
        point we will start consuming messages.

        A callback is added that will be invoked if RabbitMQ cancels the consumer for some reason.
        If RabbitMQ does cancel the consumer, on_consumer_cancelled will be invoked by pika.

        :param pika.frame.Method _frame: The Basic.QosOk response frame

        """
        logger.info("QOS set to: %d", self._prefetch_count)
        logger.info("Configure message consumption")

        if self._channel is None:
            raise RuntimeError("RMQ transport channel is not open")

        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

        # Start consuming the response queue, message from this queue require their own flow, hence
        # a dedicated handler is set up. The ack type is automatic.
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

        # Start consuming the requests queue and handle the service message flow. ack type is manual.
        if not self._client_only:
            logger.info("Ready to consume requests, events and commands")
            self._consumer_tags.add(
                self._channel.basic_consume(
                    on_message_callback=functools.partial(
                        self.on_service_message, self._service_queue
                    ),
                    queue=self._service_queue,
                    exclusive=False,
                )
            )

        self._was_consuming = True
        self._consuming = True

        if self._connected_future:
            self._connected_future.set_result(True)
            self._connecting = False
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
        encrypted = properties.headers.get("encrypted", "") == "yes"

        logger.warning(
            f"Could not route {nuropb_type} message to service {method.routing_key} "
            f"correlation_id: {correlation_id} "
            f"trace_id: {trace_id} "
            f": {method.reply_code}, {method.reply_text}"
        )
        """ End the awaiting request future with a NuropbNotDeliveredError
        """
        if nuropb_type == "request":
            if encrypted and self._encryptor:
                body = self._encryptor.decrypt_payload(
                    payload=body,
                    correlation_id=correlation_id,
                )
            request_payload = cast(RequestPayloadDict, decode_payload(body, "json"))
            request_method = request_payload["method"]
            nuropb_payload = ResponsePayloadDict(
                tag="response",
                correlation_id=correlation_id,
                context=request_payload["context"],
                trace_id=trace_id,
                result=None,
                error={
                    "error": "NuropbNotDeliveredError",
                    "description": f"Service {method.routing_key} not available. unable to call method {request_method}",
                },
                warning=None,
                reply_to="",
            )
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

    def send_message(
        self,
        payload: Dict[str, Any],
        expiry: Optional[int] = None,
        priority: Optional[int] = None,
        encoding: str = "json",
        encrypted: bool = False,
    ) -> None:
        """Send a message to over the RabbitMQ Transport

            TODO: Consider alternative handling when the channel is closed.
                also refer to the notes in the on_channel_closed method.
                - Wait and retry on a new channel?
                - setup a retry queue?
                - should there be a high water mark for the number of retries?
                - should new messages not be consumed until the channel is re-established and retry queue drained?

        :param Dict[str, Any] payload: The message contents
        :param expiry: The message expiry in milliseconds
        :param priority: The message priority
        :param encoding: The encoding of the message
        :param encrypted: True if the message is to be encrypted
        """
        mandatory = False
        exchange = ""
        reply_to = ""

        if payload["tag"] == "event":
            exchange = self._events_exchange
            routing_key = payload["topic"]
        elif payload["tag"] in ("request", "command"):
            mandatory = True
            exchange = self._rpc_exchange
            routing_key = payload["service"]
            reply_to = self._response_queue
        elif payload["tag"] == "response":
            routing_key = payload["reply_to"]
        else:
            raise ValueError(f"Unknown payload type {payload['tag']}")

        if encoding == "json":
            body = encode_payload(
                payload=payload,
                payload_type="json",
            )
        else:
            raise ValueError(f"unsupported encoding {encoding}")

        """ now encrypt the payload if public_key is not None, update RMQ header
        to indicate encrypted payload.
        """
        if (
            encrypted
            and self._encryptor
            and payload["tag"] in ("request", "command", "response")
        ):
            encrypted = "yes"
            to_service = None if payload["tag"] == "response" else payload["service"]
            """ only outgoing response and command messages require the target service name
            """
            wire_body = self._encryptor.encrypt_payload(
                payload=body,
                correlation_id=payload["correlation_id"],
                service_name=to_service,
            )
        else:
            wire_body = body

        properties = dict(
            content_type="application/json",
            correlation_id=payload["correlation_id"],
            reply_to=reply_to,
            headers={
                "nuropb_protocol": NUROPB_PROTOCOL_VERSION,
                "nuropb_version": NUROPB_VERSION,
                "nuropb_type": payload["tag"],
                "trace_id": payload["trace_id"],
                "encrypted": "yes" if encrypted else "",
            },
        )
        if expiry:
            properties["expiration"] = str(expiry)
        if priority:
            properties["priority"] = priority

        if not (self._channel is None or self._channel.is_closed):
            """Check that the channel is in a valid state before sending the response
            # TODO: Consider blocking any new messages until the channel is re-established
            and the message is sent? Especially when it is a response message.
            """
            basic_properties = pika.BasicProperties(**properties)
            self._channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=wire_body,
                properties=basic_properties,
                mandatory=mandatory,
            )

        else:
            raise NuropbTransportError(
                description="RMQ channel closed",
                payload=payload,
                exception=None,
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
        metadata["end_time"] = time.time()
        metadata["duration"] = metadata["end_time"] - metadata["start_time"]
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
        trace_id = properties.headers.get("trace_id", "unknown")
        correlation_id = properties.correlation_id
        encrypted = properties.headers.get("encrypted", "") == "yes"

        if redelivered is True and acknowledgement == "nack":
            if verbose:
                logger.debug(
                    "Redelivered is True, action is overridden from nack to rejected"
                )
            acknowledgement = "reject"
            if properties.headers.get("nuropb_type", "") == "request":
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

        """ **NOTE** if this call fails, due to a reconnect or a new channel created between the time
        the message was received and now when the message is acknowledged. the message will be 
        received again. This is a feature of RabbitMQ and is not a bug.
        """
        self.acknowledge_service_message(
            channel, delivery_tag, acknowledgement, redelivered
        )

        for respond_message in response_messages:
            respond_payload = respond_message["nuropb_payload"]
            if respond_payload["tag"] == "response":
                respond_payload["reply_to"] = reply_to
            respond_payload["correlation_id"] = correlation_id
            respond_payload["trace_id"] = trace_id

            self.send_message(
                payload=respond_payload,
                priority=None,
                encoding="json",
                encrypted=encrypted,
            )

        """ NOTE - METADATA: keep this dictionary in sync with across all these methods:
            - on_service_message, on_service_message_complete
            - on_response_message, on_response_message_complete
            - metadata_metrics
        """
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
        encrypted = properties.headers.get("encrypted", "") == "yes"
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
encrypted: {encrypted}
"""
            )
        """ Handle for the unknown message type and reply to the originator if possible
        """
        nuropb_version = properties.headers.get("nuropb_version", "")
        correlation_id = properties.correlation_id
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
            "correlation_id": correlation_id,
            "trace_id": properties.headers.get("trace_id", "unknown"),
            "encrypted": encrypted,
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
            if encrypted and self._encryptor:
                body = self._encryptor.decrypt_payload(
                    payload=body,
                    correlation_id=correlation_id,
                )
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
        correlation_id = properties.correlation_id
        nuropb_type = properties.headers.get("nuropb_type", "")
        nuropb_version = properties.headers.get("nuropb_version", "")
        encrypted = properties.headers.get("encrypted", "") == "yes"

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
                    f"correlation_id: {correlation_id}\n"
                    f"trace_id: {properties.headers.get('trace_id', '')}\n"
                    f"content_type: {properties.content_type}\n"
                    f"nuropb_type: {nuropb_type}\n"
                    f"nuropb_version: {nuropb_version}\n"
                    f"encrypted: {encrypted}\n"
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
                "encrypted": encrypted,
            }
            message_complete_callback = functools.partial(
                self.on_service_message_complete,
                channel,
                basic_deliver.delivery_tag,
                properties.reply_to,
                metadata,
            )
            if encrypted and self._encryptor:
                body = self._encryptor.decrypt_payload(
                    payload=body,
                    correlation_id=correlation_id,
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
        if self._channel is None or self._channel.is_closed:
            return
        else:
            logger.info(
                "Stopping consumers and sending a Basic.Cancel command to RabbitMQ"
            )
            all_consumers_closed: Awaitable[bool] = asyncio.Future()

            def _on_cancel_ok(frame: pika.frame.Method) -> None:
                logger.info("Consumer %s closed ok", frame.method.consumer_tag)
                self._consumer_tags.remove(frame.method.consumer_tag)
                if len(self._consumer_tags) == 0:
                    all_consumers_closed.set_result(True)  # type: ignore[attr-defined]

            for consumer_tag in self._consumer_tags:
                if self._channel and self._channel.is_open:
                    self._channel.basic_cancel(consumer_tag, _on_cancel_ok)

            try:
                logger.info(
                    "Waiting for %ss for consumers to close",
                    CONSUMER_CLOSED_WAIT_TIMEOUT,
                )
                await asyncio.wait_for(
                    all_consumers_closed, timeout=CONSUMER_CLOSED_WAIT_TIMEOUT
                )
                logger.info("Consumers to gracefully closed")
            except asyncio.TimeoutError:
                logger.error(
                    "Timed out while waiting for all consumers to gracefully close"
                )
            except Exception as err:
                logger.exception(
                    "Error while waiting for all consumers to gracefully close: %s", err
                )

            if len(self._consumer_tags) != 0:
                logger.error(
                    "Timed out while waiting for all consumers to gracefully close"
                )

            self._consuming = False
            self.close_channel()

    def close_channel(self) -> None:
        """Call to close the channel with RabbitMQ cleanly by issuing the Channel.Close RPC command."""
        logger.info("Closing the channel")
        if self._channel is None or self._channel.is_closed:
            logger.info("Channel is already closed")
        else:
            self._channel.close()
