import logging
from typing import Dict, Optional, Any, Union, cast
from uuid import uuid4
from asyncio import Future
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from nuropb.encodings.encryption import Encryptor
from nuropb.interface import (
    NuropbInterface,
    NuropbMessageError,
    ResponsePayloadDict,
    RequestPayloadDict,
    EventPayloadDict,
    NuropbHandlingError,
    ResultFutureResponsePayload,
    TransportServicePayload,
    MessageCompleteFunction,
    CommandPayloadDict,
    NuropbException,
)
from nuropb.rmq_transport import RMQTransport
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
    _encryptor: Encryptor
    _service_discovery: Dict[str, Any]
    _service_public_keys: Dict[str, Any]

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
            """Configure for client only mode"""
            self._client_only = True
            self._connection_name = f"{vhost}-client-{instance_id}"
            service_name = f"{vhost}-client"
            self._encryptor = Encryptor()
        else:
            """Configure for service mode"""
            self._client_only = False
            self._connection_name = f"{vhost}-{service_name}-{instance_id}"
            self._encryptor = Encryptor(
                service_name=service_name,
                private_key=getattr(service_instance, "_private_key", None),
            )

        self._service_name = service_name
        """ Is also a label for the api whether in client or service mode.
        """

        self._service_discovery = {}
        """ A dictionary of service_name: service mesh discovered service_info
        """
        self._service_public_keys = {}
        """ A dictionary of service_name: public_key for when encryption is required
        """

        if not self._client_only and service_instance is None:
            raise ValueError(
                "A service instance must be provided when starting in service mode"
            )  # pragma: no cover
        self._service_instance = service_instance
        """ the class instance that will be shared on the service mesh
        """

        transport_settings = {} if transport_settings is None else transport_settings
        if self._client_only:
            transport_settings["client_only"] = True

        self._response_futures = {}

        default_ttl = transport_settings.get("default_ttl", None)
        self._default_ttl = 60 * 60 * 1000 if default_ttl is None else default_ttl
        """ default time to live or timeout service mesh interaction
        """

        self._api_connected = False

        if not self._client_only and self._service_instance is None:
            logger.warning(
                "No service instance provided, service will not be able to handle requests"
            )  # pragma: no cover

        transport_settings.update(
            {
                "service_name": self._service_name,
                "instance_id": self._instance_id,
                "amqp_url": amqp_url,
                "message_callback": self.receive_transport_message,
                "rpc_exchange": rpc_exchange,
                "events_exchange": events_exchange,
                "encryptor": self._encryptor,
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
        else:
            logger.warning("Already connected")

    async def disconnect(self) -> None:
        """disconnect: disconnects from the underlying transport
        :return: None
        """
        await self._transport.stop()

    def receive_transport_message(
        self,
        service_message: TransportServicePayload,
        message_complete_callback: MessageCompleteFunction,
        metadata: Dict[str, Any],
    ) -> None:
        """receive_transport_message: handles a messages received from the transport layer. Both
         incoming service messages and response messages pass through this method.

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
        encrypted: bool = False,
    ) -> Union[ResponsePayloadDict, Any]:
        """Makes a rpc request for a method on a service mesh service and waits until the response is
        received.

        :param service: str, The routing key on the rpc exchange to direct the request to the desired
            service request queue.
        :param method: str, the name of the api call / method on the service
        :param params: dict, The method input parameters
        :param context: dict
            The context of the request. This is used to pass information to the service manager
            and is not used by the transport. Example content includes:
                - user_id: str  # a unique user identifier or token of the user that made the request
                - correlation_id: str  # a unique identifier of the request used to correlate the response to the
                                       # request or trace the request over the network (e.g. uuid4 hex string)
                - service: str
                - method: str
        :param ttl: int optional
            expiry is the time in milliseconds that the message will be kept on the queue before being moved
            to the dead letter queue. If None, then the message expiry configured on the transport is used.
        :param trace_id: str optional
            an identifier to trace the request over the network (e.g. uuid4 hex string)
        :param rpc_response: bool optional
            if True (default), the actual response of the RPC call is returned and where there was an error,
            that is raised as an exception.
            Where rpc_response is a ResponsePayloadDict, is returned.
        :param encrypted: bool
            if True then the message will be encrypted in transit
        :return ResponsePayloadDict | Any: representing the response from the requested service with any
            exceptions raised
        """
        correlation_id = uuid4().hex
        ttl = self._default_ttl if ttl is None else ttl
        message: RequestPayloadDict = {
            "tag": "request",
            "service": service,
            "method": method,
            "params": params,
            "correlation_id": correlation_id,
            "context": context,
            "trace_id": trace_id,
        }
        response_future: ResultFutureResponsePayload = Future()
        self._response_futures[correlation_id] = response_future

        # mandatory means that if it doesn't get routed to a queue then it will be returned vi self._on_message_returned
        logger.debug(
            f"Sending request message:\n"
            f"correlation_id: {correlation_id}\n"
            f"trace_id: {trace_id}\n"
            f"service: {service}\n"
            f"method: {method}\n"
        )
        try:
            self._transport.send_message(
                payload=message,
                expiry=ttl,
                priority=None,
                encoding="json",
                encrypted=encrypted,
            )
        except Exception as err:
            if rpc_response is False:
                return {
                    "tag": "response",
                    "context": context,
                    "correlation_id": correlation_id,
                    "trace_id": trace_id,
                    "result": None,
                    "error": {
                        "error": f"{type(err).__name__}",
                        "description": f"Error sending request message: {err}",
                    },
                }
            else:
                raise err

        try:
            response = await response_future
            if rpc_response is True and response["error"] is not None:
                raise NuropbMessageError(
                    description=response["error"]["description"],
                    payload=response,
                )
            elif rpc_response is True:
                return response["result"]
            else:
                return response
        except BaseException as err:
            if rpc_response is True:
                raise err
            else:
                if not isinstance(err, NuropbException):
                    error = {
                        "error": f"{type(err).__name__}",
                        "description": f"Error waiting for response: {err}",
                    }
                else:
                    error = err.to_dict()
                return {
                    "tag": "response",
                    "context": context,
                    "correlation_id": correlation_id,
                    "trace_id": trace_id,
                    "result": None,
                    "error": error,
                }

    def command(
        self,
        service: str,
        method: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
        encrypted: bool = False,
    ) -> None:
        """command: sends a command to the target service. I.e. a targeted event. response is not expected
        and ignored.

        :param service: the service name
        :param method: the method name
        :param params: the method arguments, these must be easily serializable to JSON
        :param context: additional information that represent the context in which the request is executed.
                        The must be easily serializable to JSON.
        :param ttl: the time to live of the request in milliseconds. After this time and dependent on the
                    underlying transport, it will not be consumed by the target
                    or
                    assumed by the requester to have failed with an undetermined state.
        :param trace_id: an identifier to trace the request over the network (e.g. uuid4 hex string)
        :param encrypted: bool, if True then the message will be encrypted in transit
        :return: None
        """
        correlation_id = uuid4().hex
        ttl = self._default_ttl if ttl is None else ttl
        message: CommandPayloadDict = {
            "tag": "command",
            "service": service,
            "method": method,
            "params": params,
            "correlation_id": correlation_id,
            "context": context,
            "trace_id": trace_id,
        }

        # mandatory means that if it doesn't get routed to a queue then it will be returned vi self._on_message_returned
        logger.debug(
            f"Sending command message:\n"
            f"correlation_id: {correlation_id}\n"
            f"trace_id: {trace_id}\n"
            f"service: {service}\n"
            f"method: {method}\n"
        )
        self._transport.send_message(
            payload=message,
            expiry=ttl,
            priority=None,
            encoding="json",
            encrypted=encrypted,
        )

    def publish_event(
        self,
        topic: str,
        event: Dict[str, Any],
        context: Dict[str, Any],
        trace_id: Optional[str] = None,
        encrypted: bool = False,
    ) -> None:
        """Broadcasts an event with the given topic.

        :param topic: str, The routing key on the events exchange
        :param event: json-encodable Python Dict.
        :param context: dict, The context around gent generation, example content includes:
                - user_id: str  # a unique user identifier or token of the user that made the request
                - correlation_id: str  # a unique identifier of the request used to correlate the response
                                       # to the request
                                       # or trace the request over the network (e.g. an uuid4 hex string)
                - service: str
                - method: str
        :param trace_id: str optional
            an identifier to trace the request over the network (e.g. an uuid4 hex string)
        :param encrypted: bool, if True then the message will be encrypted in transit
        """
        correlation_id = uuid4().hex
        message: EventPayloadDict = {
            "tag": "event",
            "topic": topic,
            "event": event,
            "context": context,
            "trace_id": trace_id,
            "correlation_id": correlation_id,
            "target": None,
        }
        logger.debug(
            "Sending event message: (%s - %s)",
            correlation_id,
            trace_id,
        )
        self._transport.send_message(
            payload=message,
            priority=None,
            encoding="json",
            encrypted=encrypted,
        )

    async def describe_service(
        self, service_name: str, refresh: bool = False
    ) -> Dict[str, Any] | None:
        """describe_service: returns the service information for the given service_name,
        if it is not already cached or refresh is try then the service discovery is queried directly.

        :param service_name: str
        :param refresh: bool
        :return: dict
        """
        if service_name in self._service_discovery or refresh:
            return self._service_discovery[service_name]

        service_info = await self.request(
            service=service_name,
            method="nuropb_describe",
            params={},
            context={},
            ttl=60 * 1000,  # 1 minute
            trace_id=uuid4().hex,
        )
        if not isinstance(service_info, dict):
            raise ValueError(
                f"Invalid service_info returned for service {service_name}"
            )
        else:
            self._service_discovery[service_name] = service_info
            try:
                text_public_key = service_info.get("public_key", None)
                if text_public_key:
                    public_key = serialization.load_pem_public_key(
                        data=text_public_key.encode("ascii"),
                        backend=default_backend(),
                    )
                    self._encryptor.add_service_public_key(
                        service_name=service_name, public_key=public_key
                    )
            except Exception as err:
                logger.error(f"error loading the public key for {service_name}: {err}")
            finally:
                return service_info

    async def requires_encryption(self, service_name: str, method_name: str) -> bool:
        """requires_encryption: Queries the service discovery information for the service_name
        and returns True if encryption is required else False.
        none of encryption is not required.

        :param service_name: str
        :param method_name: str
        :return: bool
        """
        service_info = await self.describe_service(service_name)
        method_info = service_info["methods"].get(method_name, None)
        if method_info is None:
            raise ValueError(
                f"Method {method_name} not found on service {service_name}"
            )
        return method_info.get("requires_encryption", False)
