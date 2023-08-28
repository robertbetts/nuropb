import json
import logging
import functools
import re
from typing import List, Set, Optional, Any, Dict, Awaitable
import asyncio

import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from pika.exceptions import ChannelClosedByBroker
import pika.spec

from nuropb.interface import (
    MessageCallbackType,
    PayloadDict,
    ResponsePayloadDict, NuropbTransportError,
)

logger = logging.getLogger()
# The length of time to wait when shutting down for consumers to close.
CONSUMER_CLOSED_WAIT_TIMEOUT = 10


def obfuscate_secret(input_string: str) -> str:
    pattern = r"(:.*?@)"
    result = re.sub(
        pattern, lambda match: ":" + "x" * (len(match.group(0)) - 2) + "@", input_string
    )
    return result


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


def decode_payload(payload: bytes, payload_type: str = "json") -> Dict[str, Any]:
    """
    :param payload:
    :param payload_type:
        Currently only support json
    :return: convert bytes to a Python Dict
    """
    if payload_type != "json":
        raise ValueError(f"payload_type {payload_type} is not supported")

    decoded_payload = json.loads(payload)
    if not isinstance(decoded_payload, dict):
        raise ValueError(f"payload is not a dict: {decoded_payload}")
    return decoded_payload


def decode_rmq_message(
    _method: pika.spec.Basic.Deliver, properties: pika.spec.BasicProperties, body: bytes
) -> PayloadDict:
    """Map incoming RabbitMQ message to a nuropb message types"""
    message_type = properties.headers.get("nuropb_type")
    trace_id = properties.headers.get("trace_id")
    payload: Dict[str, Any] = decode_payload(body, "json")

    if trace_id != payload.get("trace_id"):
        logger.warning(
            f"trace_id {trace_id} does not match payload trace_id {payload.get('trace_id')}"
        )

    message_inputs: PayloadDict
    if message_type == "request":
        message_inputs = {
            "tag": "request",
            "correlation_id": properties.correlation_id,
            "context": payload.get("context", {}),
            "trace_id": trace_id,
            "service": payload["service"],
            "method": payload["method"],
            "params": payload["params"],
            "reply_to": properties.reply_to,
        }
    elif message_type == "response":
        message_inputs = {
            "tag": "response",
            "correlation_id": properties.correlation_id,
            "context": payload.get("context", {}),
            "trace_id": trace_id,
            "result": payload["result"],
            "error": payload["error"],
            "warning": payload["warning"],
        }
    elif message_type == "event":
        message_inputs = {
            "tag": "event",
            "correlation_id": properties.correlation_id,
            "context": payload.get("context", {}),
            "trace_id": trace_id,
            "topic": payload["topic"],
            "event": payload["event"],
        }
    elif message_type == "command":
        message_inputs = {
            "tag": "command",
            "correlation_id": properties.correlation_id,
            "context": payload.get("context", {}),
            "trace_id": trace_id,
            "service": payload["service"],
            "method": payload["method"],
            "params": payload["params"],
        }
    else:
        message_inputs = {
            "tag": "unknown",
            "correlation_id": properties.correlation_id,
            "context": payload.get("context", {}),
            "trace_id": trace_id,
            "payload": payload,
        }
    return message_inputs


class ServiceNotConfigured(Exception):
    """Raised when a service is not propery configured on the RabbitMQ broker.
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
    _request_queue: str
    _response_queue: str
    _rpc_bindings: Set[str]
    _event_bindings: Set[str]
    _prefetch_count: int
    _default_ttl: int
    _client_only: bool
    _message_callback: MessageCallbackType

    _response_futures: Dict[str, Awaitable[PayloadDict]]
    _connected_future: Any
    _disconnected_future: Any

    _is_leader: bool
    _is_rabbitmq_configured: bool

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
        message_callback: MessageCallbackType,
        rpc_exchange: Optional[str] = None,
        events_exchange: Optional[str] = None,
        dl_exchange: Optional[str] = None,
        dl_queue: Optional[str] = None,
        request_queue: Optional[str] = None,
        response_queue: Optional[str] = None,
        rpc_bindings: Optional[List[str] | Set[str]] = None,
        event_bindings: Optional[List[str] | Set[str]] = None,
        prefetch_count: Optional[int] = None,
        default_ttl: Optional[int] = None,
        client_only: Optional[bool] = None,
    ):  # NOSONAR
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.

        :param str service_name: The name of the service
        :param str instance_id: The instance id of the service
        :param str amqp_url: The AMQP url to connect with
        :param MessageCallbackType message_callback: The callback to call when a message is received
        :param str rpc_exchange: The name of the RPC exchange
        :param str events_exchange: The name of the events exchange
        :param str dl_exchange: The name of the dead letter exchange
        :param str dl_queue: The name of the dead letter queue
        :param str request_queue: The name of the requests queue
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

        self._connection = None
        self._channel = None
        self._consumer_tags = set()

        self._client_only = False if client_only is None else client_only
        """ If client_only is True, then the transport will not attempt to configure a response queue. Handling
        requests, commands are disabled. This is useful for testing and for clients that do not need to respond
        """

        # Experiment with larger values for higher throughput.
        self._service_name = service_name
        self._instance_id = instance_id
        self._amqp_url = amqp_url
        self._rpc_exchange = rpc_exchange or "nuropb-rpc-exchange"
        self._events_exchange = events_exchange or "nuropb-events-exchange"
        self._dl_exchange = dl_exchange or "nuropb-dl-exchange"
        self._dl_queue = dl_queue or f"nuropb-{self._service_name}-dl-q"
        self._request_queue = request_queue or f"nuropb-{self._service_name}-req-q"
        self._response_queue = (
            response_queue or f"nuropb-{self._service_name}-{self._instance_id}-resp-q"
        )
        self._rpc_bindings = set(rpc_bindings or [])
        self._event_bindings = set(event_bindings or [])
        self._prefetch_count = 1 if prefetch_count is None else prefetch_count
        self._default_ttl = default_ttl or 60 * 60 * 1000 * 12  # 12 hours
        self._message_callback = message_callback
        self._rpc_bindings.add(self._service_name)

        self._is_leader = True
        self._is_rabbitmq_configured = False

        self._response_futures = {}
        self._connected_future = None
        self._disconnected_future = None

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def is_leader(self) -> bool:
        return self._is_leader

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

    async def start(self) -> None:
        """Start the transport by connecting to RabbitMQ"""
        self._connected_future = self.connect()
        await self._connected_future

    async def stop(self) -> None:
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

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

        logger.info("Connecting to %s", obfuscate_secret(self._amqp_url))

        self._connected_future = asyncio.Future()
        connection = AsyncioConnection(
            parameters=pika.URLParameters(self._amqp_url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed,
        )
        self._connection = connection

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

        :param pika.adapters.asyncio_connection.AsyncioConnection _unused_connection:
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

        :param pika.connection.Connection _unused_connection: The closed connection obj
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
         in so we can make use of it.

        :param pika.channel.Channel channel: The channel object
        """
        logger.info("Channel opened")
        self._channel = channel
        self._channel.add_on_close_callback(self.on_channel_closed)
        self.declare_response_queue()

    def on_channel_closed(self, channel: Channel, reason: Exception) -> None:
        """Invoked by pika when RabbitMQ unexpectedly closes the channel. Channels are usually closed
        if you attempt to do something that violates the protocol, such as re-declare an exchange or
        queue with different parameters. In this case, we'll close the connection to shutdown the object.

        :param pika.channel.Channel channel: The closed channel
        :param Exception reason: why the channel was closed
        """
        if isinstance(reason, ChannelClosedByBroker):
            logger.critical("Channel %i was closed by broker: %s", channel, reason)
            if reason.reply_code == 404:
                logging.error(
                    f"""\n\n
RabbitMQ channel closed by broker with reply_code: {reason.reply_code} and reply_text: {reason.reply_text}
This is usually caused by a misconfiguration of the RabbitMQ broker.
Please check the RabbitMQ broker configuration and restart the service:

RabbitMQ url: {obfuscate_secret(self._amqp_url)}

Check that the following exchanges, queues and bindings exist:
    Exchange: {self._rpc_exchange}
    Exchange: {self._events_exchange}
    Exchange: {self._dl_exchange}
    Queue: {self._dl_queue}
    Queue: {self._request_queue}
    Queue: {self._response_queue}
    Bindings: {self._rpc_bindings}
    Bindings: {self._event_bindings}
\n\n"""
                )
                if self._connected_future and not self._connected_future.done():
                    self._connected_future.set_exception(
                        ServiceNotConfigured(
                            f"RabbitMQ not preperly configured: {reason}"
                        )
                    )

    def declare_response_queue(self) -> None:
        """Setup the response queue on RabbitMQ by invoking the Queue.Declare RPC command. When it
        is complete, the on_response_queue_declareok method will be invoked by pika.
        """
        logger.info("Declaring response queue %s", self._response_queue)
        if self._channel is None:
            raise RuntimeError("RMQ transport channel is not open")

        cb = functools.partial(
            self.on_response_queue_declareok, userdata=self._response_queue
        )
        response_queue_config = {"durable": False, "auto_delete": True}
        self._channel.queue_declare(
            queue=self._response_queue, callback=cb, **response_queue_config
        )

    def on_response_queue_declareok(
        self, frame: pika.frame.Method, userdata: str
    ) -> None:
        """Method invoked by pika when the Queue.Declare RPC call made in setup_response_queue has
        completed. In this method we will bind request queue and the response queues. When this
        command is complete, the on_bindok method will be invoked by pika.

        :param pika.frame.Method _unused_frame: The Queue.DeclareOk frame
        :param str|unicode userdata: Extra user data (queue name)
        """

        if not self._client_only:
            if self._channel is None:
                raise RuntimeError("RMQ transport channel is not open")

            logger.info(
                "Refreshing the service request queue and bindings: %s",
                self._request_queue,
            )
            request_queue_config = {
                "durable": True,
                "auto_delete": False,
                "arguments": {"x-dead-letter-exchange": self._dl_exchange},
            }
            self._channel.queue_declare(
                queue=self._request_queue, **request_queue_config
            )

            for routing_key in self._rpc_bindings:
                logger.info(
                    "Binding %s to %s with %s",
                    self._request_queue,
                    self._rpc_exchange,
                    routing_key,
                )
                self._channel.queue_bind(
                    self._request_queue, self._rpc_exchange, routing_key=routing_key
                )

            for routing_key in self._event_bindings:
                logger.info(
                    "Binding %s to %s with %s",
                    self._request_queue,
                    self._events_exchange,
                    routing_key,
                )
                self._channel.queue_bind(
                    self._response_queue, self._events_exchange, routing_key=routing_key
                )

        self.on_bindok(frame, userdata=self._response_queue)

    def on_bindok(self, _frame: pika.frame.Method, userdata: str) -> None:
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will set the prefetch count for the channel.

        :param pika.frame.Method _unused_frame: The Queue.BindOk response frame
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

        :param pika.frame.Method _unused_frame: The Basic.QosOk response frame

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

        # Start consuming the response queue
        logger.info(
            "Consuming Responses, these need their own handler as the ack type is automatic"
        )
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
                        self.on_service_message, self._request_queue
                    ),
                    queue=self._request_queue,
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
        logger.info("Consumer was cancelled remotely, shutting down: %r", method_frame)
        if self._channel:
            self._channel.close()

    def send_message(
        self,
        exchange: str,
        routing_key: str,
        body: bytes,
        properties: Dict[str, Any],
        mandatory: bool,
    ) -> None:
        """Send a message to RabbitMQ"""
        if self._channel is None:
            raise RuntimeError("RMQ transport channel is not open")

        basic_properties = pika.BasicProperties(**properties)
        self._channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=body,
            properties=basic_properties,
            mandatory=mandatory,
        )

    def on_service_message(
        self,
        _queue_name: str,
        _channel: Channel,
        basic_deliver: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Invoked when a message is delivered to the request_queue. The channel is passed for your convenience.
        The basic_deliver object that is passed in carries the exchange, routing key, delivery tag and a
        redelivered flag for the message. The properties passed in is an instance of BasicProperties with the
        message properties and the body is the message that was sent.

        the error handling here can seem a little complicated, essentially if an error receiving and handling a
        can be returned to the sender, then we do it. If the message is not a request, then we can just reject
        the message and move on. If the message is a request, then we need to send a response the message ack must
        only take place after _message_callback has been successfully compelted.

        if the processing of a request message fails, then we nack the message and requeue it, there was a problem
        with this instance processing the message.

        # TODO we need to think about eccesive errors and decide on a strategy for for shutting down the service
        # instance

        :param str _queue_name: The name of the queue that the message was received on
        :param pika.channel.Channel _channel: The channel object
        :param pika.spec.Basic.Deliver basic_deliver: basic_deliver method
        :param pika.spec.BasicProperties properties: properties
        :param bytes body: The message body
        """
        logger.debug(
            f"Received message from the service queue # {basic_deliver.delivery_tag}\n"
            f"exchange: {basic_deliver.exchange}\n"
            f"routing_key: {basic_deliver.routing_key}\n"
            f"correlation_id: {properties.correlation_id}\n"
            f"trace_id: {properties.headers.get('trace_id', '')}\n"
            f"content_type: {properties.content_type}\n"
            f"body: {body!r}\n"
        )
        message: PayloadDict | None = None
        try:
            message = decode_rmq_message(basic_deliver, properties, body)
        except Exception as err:
            logger.exception(
                (
                    f"Error decoding service message # {basic_deliver.delivery_tag}: {err}\n"
                    f"Error: {err}\n"
                    f"message type: {properties.headers.get('nuropb_type', '')}\n"
                    f"correlation_id: {properties.correlation_id}\n"
                    f"trace_id: {properties.headers.get('trace_id', '')}\n"
                )
            )
            if not (
                properties.headers.get("nuropb_type", "") == "request"
                and properties.reply_to
            ):
                """If the message is not a request or replay-able, then we can just reject the message and move on"""
                logger.warning("Rejecting message")
                if self._channel is None:
                    raise NuropbTransportError(
                        message="unable to reject message due to handling error, RMQ channel closed",
                        lifecycle="service-decode",
                        payload=message,
                        exception=err,
                    )
                self._channel.basic_reject(
                    delivery_tag=basic_deliver.delivery_tag, requeue=False
                )
                return
            else:
                """Send an error response to the requestor, with information on the decoding error"""
                error_response: ResponsePayloadDict = {
                    "tag": "response",
                    "correlation_id": properties.correlation_id,
                    "context": {
                        "rmq_context": properties.correlation_id,
                    },
                    "trace_id": properties.headers.get("trace_id", ""),
                    "result": None,
                    "error": {
                        "error": type(err).__name__,
                        "description": f"Error decoding message: {err}",
                    },
                    "warning": None,
                }

                if self._channel is None:
                    raise NuropbTransportError(
                        message="unable to return handling error to requestor, RMQ channel closed",
                        lifecycle="service-decode",
                        payload=error_response,
                        exception=err,
                    )
                body = encode_payload(error_response, "json")
                self.send_message(
                    exchange="",
                    routing_key=properties.reply_to,
                    body=body,
                    properties={
                        "correlation_id": properties.correlation_id,
                        "headers": {
                            "nuropb_type": "response",
                            "trace_id": properties.headers.get("trace_id", ""),
                        },
                        "content_type": properties.content_type,
                    },
                    mandatory=True,
                )
                self._channel.basic_ack(basic_deliver.delivery_tag)
                return

        try:
            """If the message is a request, then we need to send a response the message ack must only
            take place after _message_callback has been successfully compelted
            """
            self._message_callback(message)
        except Exception as err:
            logger.error(
                (
                    f"lifecycle: service-handle\n"
                    f"Error processing service message # {basic_deliver.delivery_tag}: {err}\n"
                    f"correlation_id: {properties.correlation_id}\n"
                    f"trace_id: {properties.headers.get('trace_id', '')}\n"
                )
            )
            logger.exception("")
            if message["tag"] == "request":
                """nack the message and requeue it, there was a problem with this instance processing the message"""
                if self._channel is None or not self._channel.is_open:
                    raise NuropbTransportError(
                        message="unable to nack and requeue message due to handling error, RMQ channel closed",
                        lifecycle="service-handle",
                        payload=message,
                        exception=err,
                    )
                logger.warning("Nacking message")
                self._channel.basic_nack(
                    delivery_tag=basic_deliver.delivery_tag, requeue=True
                )
                return
            else:
                """If the message is not a request, then we can just reject the message and move on"""
                if self._channel is None or not self._channel.is_open:
                    raise NuropbTransportError(
                        message="unable to reject message due to handling error, RMQ channel closed",
                        lifecycle="service-handle",
                        payload=message,
                        exception=err,
                    )
                logger.warning("Rejecting message")
                self._channel.basic_reject(
                    delivery_tag=basic_deliver.delivery_tag, requeue=False
                )
                return

        logger.debug(
            "Acknowledging service message receipt %s", basic_deliver.delivery_tag
        )
        if self._channel is None:
            # TODO: Handle the case for this logic cleanly, is there a retry mechanism possilbe
            #  after re-establishing a new channel?
            #  things to think about:
            # - what happens to the result if the channel is closed?
            # - What happens id the request is resent, can we leverage the existing result
            # - what happens if the request is resent to another service worker?
            # - what happens to the request sender waiting for a response?
            raise NuropbTransportError(
                message=f"unable to ack {message['tag']} message, RMQ channel closed",
                lifecycle="service-ack",
                payload=message,
                exception=None,
            )

        self._channel.basic_ack(basic_deliver.delivery_tag)

    def on_response_message(
        self,
        queue_name: str,
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

        :param str queue_name: The name of the queue that the message was received on
        :param pika.channel.Channel _unused_channel: The channel object
        :param pika.spec.Basic.Deliver basic_deliver: basic_deliver method
        :param pika.spec.BasicProperties properties: properties
        :param bytes body: The message body
        """
        logger.debug(
            (
                f"Received message from the response queue # {basic_deliver.delivery_tag}\n"
                f"exchange: {basic_deliver.exchange}\n"
                f"routing_key: {basic_deliver.routing_key}\n"
                f"correlation_id: {properties.correlation_id}\n"
                f"trace_id: {properties.headers.get('trace_id', '')}\n"
                f"content_type: {properties.content_type}\n"
                f"body: {body!r}\n"
            )
        )

        try:
            message = decode_rmq_message(basic_deliver, properties, body)
            self._message_callback(message)
        except Exception as err:
            logger.error(
                (
                    f"Error processing response message # {basic_deliver.delivery_tag}: {err}\n"
                    f"correlation_id: {properties.correlation_id}\n"
                    f"trace_id: {properties.headers.get('trace_id', '')}\n"
                )
            )
            logger.exception("")
            return

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
                logging.error(
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
