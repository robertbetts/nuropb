import logging
from typing import Dict, Optional, Any, Union, cast
from uuid import uuid4
import asyncio
from asyncio import Future

from nuropb.interface import (
    NuropbInterface,
    NuropbMessageError,
    PayloadDict,
    ResponsePayloadDict,
    RequestPayloadDict,
    EventPayloadDict,
    NuropbHandlingError,
    ResultFutureResponsePayload,
    TransportServicePayload,
    MessageCompleteFunction,
    NUROPB_PROTOCOL_VERSION,
    CommandPayloadDict,
)
from nuropb.rmq_transport import RMQTransport, encode_payload
from nuropb.service_handlers import execute_request, handle_execution_result

logger = logging.getLogger(__name__)
verbose = False


class RMQAPI(NuropbInterface):
    """RMQAPI: A NuropbInterface implementation that uses RabbitMQ as the underlying transport."""

    _mesh_name: str
    _connection_name: str
    _response_futures: Dict[str, ResultFutureResponsePayload]
    _transport: RMQTransport
    _rpc_exchange: str
    _events_exchange: str
    _service_instance: object | None
    _default_ttl: int
    _client_only: bool

    def __init__(
        self,
        amqp_url: str,
        service_name: str | None = None,
        instance_id: str | None = None,
        service_instance: object | None = None,
        rpc_exchange: Optional[str] = None,
        events_exchange: Optional[str] = None,
        transport_settings: Optional[Dict[str, Any]] = None,
    ):
        """RMQAPI: A NuropbInterface implementation that uses RabbitMQ as the underlying transport."""
        parts = amqp_url.split("/")
        vhost = amqp_url.split("/")[-1]
        if len(parts) < 4:
            raise ValueError("Invalid amqp_url, missing vhost")
        self._mesh_name = vhost

        """ If a service_name is not provided, then the service is a client only and will not be able 
        to register for messages on service exchanges: rpc and events.
        """
        self._instance_id = instance_id if instance_id is not None else uuid4().hex

        if service_name is None:
            self._client_only = True
            self._connection_name = f"{vhost}-client-{instance_id}"
            service_name = f"{vhost}-client"
        else:
            self._client_only = False
            self._connection_name = f"{vhost}-{service_name}-{instance_id}"

        self._service_name = service_name

        if not self._client_only and service_instance is None:
            raise ValueError(
                "A service instance must be provided when starting in service mode"
            )  # pragma: no cover
        self._service_instance = service_instance

        transport_settings = {} if transport_settings is None else transport_settings
        if self._client_only:
            transport_settings["client_only"] = True

        default_ttl = transport_settings.get("default_ttl", None)

        self._response_futures = {}
        self._default_ttl = 60 * 60 * 1000 if default_ttl is None else default_ttl

        self._api_connected = False

        if not self._client_only and self._service_instance is None:
            logger.warning(
                "No service instance provided, service will not be able to handle requests"
            )  # pragma: no cover

        transport_settings.update(
            {
                "service_name": service_name,
                "instance_id": instance_id,
                "amqp_url": amqp_url,
                "message_callback": self.receive_transport_message,
                "rpc_exchange": rpc_exchange,
                "events_exchange": events_exchange,
            }
        )
        self._transport = RMQTransport(**transport_settings)
        self._rpc_exchange = self._transport.rpc_exchange
        self._events_exchange = self._transport.events_exchange

    @property
    def service_name(self) -> str:
        """service_name: returns the service_name of the underlying transport"""
        return self._transport.service_name

    @property
    def is_leader(self) -> bool:
        return self._transport.is_leader

    @property
    def client_only(self) -> bool:
        """client_only: returns the client_only status of the underlying transport"""
        return self._client_only

    @property
    def connected(self) -> bool:
        """connected: returns the connection status of the underlying transport
        :return: bool
        """
        return self._transport.connected

    @property
    def transport(self) -> RMQTransport:
        """transport: returns the underlying transport
        :return: RMQTransport
        """
        return self._transport

    async def connect(self) -> None:
        """connect: connects to the underlying transport
        :return: None
        """
        if not self.connected:
            await self._transport.start()
            # task = asyncio.create_task(self.keep_loop_active())
            # task.add_done_callback(lambda _: None)
        else:
            logger.warning("Already connected")

    async def disconnect(self) -> None:
        """disconnect: disconnects from the underlying transport
        :return: None
        """
        await self._transport.stop()

    async def keep_loop_active(self) -> None:  # pragma: no cover
        """keep_loop_active: keeps the asyncio loop active while the transport is connected

        The factor for introducing this method is that during pytest, the asyncio loop
        is not always running when expected. there is an 1 cost with this delay, that will
        impact the performance of the service.
        TODO: investigate this further and only activate this method when required.

        :return:
        """
        logger.info("keeping_loop_active() is starting")
        while self.connected:
            await asyncio.sleep(0.001)
        logger.debug("keeping_loop_active() is stopping")

    def receive_transport_message(
        self,
        service_message: TransportServicePayload,
        message_complete_callback: MessageCompleteFunction,
        metadata: Dict[str, Any],
    ) -> None:
        """receive_transport_message: handles a messages received from the transport layer
            for processing by the service instance. Both incoming service messages and response
            messages pass through this method.

        :return: None
        """
        if service_message["nuropb_type"] == "response":
            response_payload: ResponsePayloadDict = cast(
                ResponsePayloadDict, service_message["nuropb_payload"]
            )
            logger.debug(
                f"Received response.  "
                f"trace_id: {service_message['trace_id']} "
                f"correlation_id: {service_message['correlation_id']}"
            )
            if service_message["correlation_id"] not in self._response_futures:
                logger.warning(
                    f"Received an unpaired response, ignoring "
                    f"correlation_id: {service_message['correlation_id']}"
                )
                return

            # Setting the result on this future will complete "await api.request(...)"
            try:
                response_future = self._response_futures.pop(
                    service_message["correlation_id"]
                )
                response_future.set_result(response_payload)
            except Exception as error:
                logger.exception(
                    f"Error completing response future for trace_id: {service_message['trace_id']} "
                    f"correlation_id: {service_message['correlation_id']} "
                    f"error: {error}"
                )

            return

        """ The logic below is only relevant for incoming service messages
        """
        if self._service_instance is None:
            error_description = f"No service instance configured to handle the {service_message['nuropb_type']} instruction"
            logger.warning(error_description)
            response = NuropbHandlingError(
                description=error_description,
                lifecycle="service-handle",
                payload=service_message["nuropb_payload"],
            )
            handle_execution_result(service_message, response, MessageCompleteFunction)
            return

        if service_message["nuropb_type"] in ("request", "command", "event"):
            logger.debug(f"Received {service_message['nuropb_type']}")
            execute_request(
                self._service_instance, service_message, message_complete_callback
            )

        else:
            logger.warning(
                "Received an unsupported message type: %s",
                service_message["nuropb_type"],
            )

    async def request(
        self,
        service: str,
        method: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
        rpc_response: bool = True,
    ) -> Union[ResponsePayloadDict, Any]:
        """Make a request for a method on service and wait until the response is received. The
            request message uses the 'message expiry' configured on the underlying transport.

            expiry is the time in milliseconds that the message will be kept on the queue before being moved
            to the dead letter queue. If None, then the message expiry configured on the transport is used.

            # TODO: Look into returning a dead letter exception for timeout or other errors that result
                in the message being returned to dead letter queue.

        Parameters:
        ----------
        service: str
            The routing key on the rpc exchange to direct the request to the desired service request queue.

        method: str
            The name of the api call / method on the service

        params: dict
            The method input parameters

        context: dict
            The context of the request. This is used to pass information to the service manager
            and is not used by the transport. Example content includes:
                - user_id: str  # a unique user identifier or token of the user that made the request
                - correlation_id: str  # a unique identifier of the request used to correlate the response to the
                                       # request or trace the request over the network (e.g. a uuid4 hex string)
                - service: str
                - method: str

        ttl: int optional
            expiry is the time in milliseconds that the message will be kept on the queue before being moved
            to the dead letter queue. If None, then the message expiry configured on the transport is used.

        trace_id: str optional
            an identifier to trace the request over the network (e.g. a uuid4 hex string)

        rpc_response: bool optional
            if True (default), the actual response of the RPC call is returned and where there was an error
            during the lifecycle, this is raised as an exception.
            Where rpc_response is a ResponsePayloadDict, is returned.

        Returns:
        --------
            ResponsePayloadDict | Any: representing the response from the requested service with any exceptions raised
        """

        correlation_id = uuid4().hex
        ttl = self._default_ttl if ttl is None else ttl
        properties = dict(
            content_type="application/json",
            correlation_id=correlation_id,
            reply_to=self._transport.response_queue,
            headers={
                "nuropb_protocol": NUROPB_PROTOCOL_VERSION,
                "nuropb_type": "request",
                "trace_id": trace_id,
            },
            expiration=f"{ttl}",
        )
        context["rmq_correlation_id"] = correlation_id
        message: RequestPayloadDict = {
            "tag": "request",
            "service": service,
            "method": method,
            "params": params,
            "correlation_id": correlation_id,
            "context": context,
            "trace_id": trace_id,
            "reply_to": self._transport.response_queue,
        }
        body = encode_payload(message, "json")
        routing_key = service

        response_future: ResultFutureResponsePayload = Future()
        self._response_futures[correlation_id] = response_future

        # mandatory means that if it doesn't get routed to a queue then it will be returned vi self._on_message_returned
        logger.debug(
            f"Sending request message:\n"
            f"correlation_id: {correlation_id}\n"
            f"trace_id: {trace_id}\n"
            f"exchange: {self._transport.rpc_exchange}\n"
            f"routing_key: {routing_key}\n"
            f"service: {service}\n"
            f"method: {method}\n"
        )
        self._transport.send_message(
            exchange=self._transport.rpc_exchange,
            routing_key=routing_key,
            body=body,
            properties=properties,
            mandatory=True,
        )
        response: PayloadDict | None = None
        try:
            response = await response_future
        except Exception as err:
            error_message = (
                f"Error while waiting for response to complete."
                f"correlation_id: {correlation_id}, trace_id: {trace_id}, error:{err}"
            )
            logger.exception(error_message)
            raise NuropbMessageError(
                description=error_message,
                lifecycle="client-handle",
                payload=response,
                exception=err,
            )

        if response["tag"] != "response":
            """This logic condition is prevented in the transport layer"""
            raise NuropbMessageError(
                description=f"Unexpected response message type: {response['tag']}",
                lifecycle="client-handle",
                payload=response,
                exception=None,
            )

        if not rpc_response:
            return response
        elif response["error"]:
            raise NuropbMessageError(
                description=f"RPC service error: {response['error']}",
                lifecycle="client-handle",
                payload=response,
                exception=None,
            )
        else:
            return response["result"]

    def command(
        self,
        service: str,
        method: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
        wait_for_ack: bool = False,
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """command: sends a command to the target service. It is up to the implementation to manage message
        idempotency and message delivery guarantees.

        any response from the target service is ignored.

        :param service: the service name
        :param method: the method name
        :param params: the method arguments, these must be easily serializable to JSON
        :param context: additional information that represent the context in which the request is executed.
                        The must be easily serializable to JSON.
        :param wait_for_ack: if True, the command will wait for an acknowledgement from the transport layer that the
        target has received the command. If False, the request will return immediately after the request is
        delivered to the transport layer.
        :param ttl: the time to live of the request in milliseconds. After this time and dependent on the
                    underlying transport, it will not be consumed by the target
                    or
                    assumed by the requester to have failed with an undetermined state.
        :param trace_id: an identifier to trace the request over the network (e.g. uuid4 hex string)

        :return: None
        """
        correlation_id = uuid4().hex
        ttl = self._default_ttl if ttl is None else ttl
        properties = dict(
            content_type="application/json",
            correlation_id=correlation_id,
            headers={
                "nuropb_protocol": NUROPB_PROTOCOL_VERSION,
                "nuropb_type": "command",
                "trace_id": trace_id,
            },
            expiration=f"{ttl}",
        )
        context["rmq_correlation_id"] = correlation_id
        message: CommandPayloadDict = {
            "tag": "command",
            "service": service,
            "method": method,
            "params": params,
            "correlation_id": correlation_id,
            "context": context,
            "trace_id": trace_id,
        }
        body = encode_payload(message, "json")
        routing_key = service

        # mandatory means that if it doesn't get routed to a queue then it will be returned vi self._on_message_returned
        logger.debug(
            f"Sending command message:\n"
            f"correlation_id: {correlation_id}\n"
            f"trace_id: {trace_id}\n"
            f"exchange: {self._transport.rpc_exchange}\n"
            f"routing_key: {routing_key}\n"
            f"service: {service}\n"
            f"method: {method}\n"
        )
        self._transport.send_message(
            exchange=self._transport.rpc_exchange,
            routing_key=routing_key,
            body=body,
            properties=properties,
            mandatory=True,
        )

    def publish_event(
        self,
        topic: str,
        event: Dict[str, Any],
        context: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> None:
        """Broadcasts an event with the given 'topic'.

        Parameters:
        ----------
        topic: str
            The routing key on the events exchange

        event: json-encodable Python Dict.

        context: dict
            The context around gent generation, example content includes:
                - user_id: str  # a unique user identifier or token of the user that made the request
                - correlation_id: str  # a unique identifier of the request used to correlate the response
                                       # to the request
                                       # or trace the request over the network (e.g. an uuid4 hex string)
                - service: str
                - method: str

        ttl: int optional
            expiry is the time in milliseconds that the message will be kept on the queue before being moved
            to the dead letter queue. If None, then the message expiry configured on the transport is used.
            defaulted to 0 (no expiry) for events

        trace_id: str optional
            an identifier to trace the request over the network (e.g. an uuid4 hex string)

        """
        correlation_id = uuid4().hex
        properties = dict(
            content_type="application/json",
            correlation_id=correlation_id,
            headers={
                "nuropb_protocol": NUROPB_PROTOCOL_VERSION,
                "nuropb_type": "event",
                "trace_id": trace_id,
            },
        )
        context["rmq_correlation_id"] = correlation_id
        message: EventPayloadDict = {
            "tag": "event",
            "topic": topic,
            "event": event,
            "context": context,
            "trace_id": trace_id,
            "correlation_id": correlation_id,
            "target": None,
        }
        body = encode_payload(message, "json")
        routing_key = topic
        logger.debug(
            "Sending event message: (%s - %s) (%s - %s)",
            correlation_id,
            trace_id,
            self._transport.events_exchange,
            routing_key,
        )
        self._transport.send_message(
            exchange=self._transport.events_exchange,
            routing_key=routing_key,
            body=body,
            properties=properties,
            mandatory=False,
        )
