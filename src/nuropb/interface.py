import asyncio
import logging
from abc import ABC
from typing import (
    Dict,
    Any,
    Callable,
    Optional,
    TypedDict,
    Literal,
    Type,
    Union,
    List,
)

logger = logging.getLogger(__name__)

NUROPB_VERSION = "0.1.0"
NUROPB_PROTOCOL_VERSION = "0.1.0"
NUROPB_PROTOCOL_VERSIONS_SUPPORTED = ("0.1.0",)
NUROPB_MESSAGE_TYPES = (
    "request",
    "response",
    "event",
    "command",
)

NuropbSerializeType = Literal["json"]
NuropbMessageType = Literal["request", "response", "event", "command"]

NuropbLifecycleState = Literal[
    "client-start",
    "client-encode",
    "client-send",
    "service-receive",
    "service-decode",
    "service-handle",
    "service-encode",
    "service-reply",
    "service-ack",
    "client-receive",
    "client-decode",
    "client-handle",
    "client-ack",
    "client-end",
]


class ErrorDescriptionType(TypedDict):
    error: str
    description: Optional[str]
    context: Optional[Dict[str, Any]]


class EventType(TypedDict):
    """For compatibility with better futureproof serialisation support, Any payload type is
    supported.It is encouraged to use a json compatible key/value Type e.g. Dict[str, Any]

    :target: is currently provided here as an aid for the implementation, there are use cases
    where events are targeted to a specified audience or list or targets. In the NuroPb paradigm,
    targets could be individual users or other services. A service would represent the service
    as a whole, NOT any individual instance of that service.

    It is also advised not to use NuroPb for communication between instances of a service.

    Reference the notes on EventPayloadDict
    """

    topic: str
    payload: Any
    target: Optional[List[Any]]


class RequestPayloadDict(TypedDict):
    """Type[RequestPayloadDict]: represents a request that is sent to a service:
    A request has a response, it is acknowledged by the transport layer after the destination
    service has handled the request.

    REMINDER FOR FUTURE: It is very tempting to support the Tuple[...,Any] for the
    param key. There is much broader downstream compatibility in keeping this as a
    dictionary / key-value mapping.
    """

    tag: Literal["request"]
    correlation_id: str
    context: Dict[str, Any]
    trace_id: Optional[str]
    service: str
    method: str
    params: Dict[str, Any]
    reply_to: str


class CommandPayloadDict(TypedDict):
    """Type[CommandPayloadDict]: represents a command that is sent to a service:
    A command has no response, it is acked immediately by the transport layer. The
    originator of the command has now knowledge of the execution of the command. If
    a response is required, a request should be used.

    A command is useful when used as a type of directed event.

    REMINDER FOR FUTURE: It is very tempting to support the Tuple[...,Any] for the
    param key. There is much broader downstream compatibility in keeping this as a
    dictionary / key-value mapping.
    """

    tag: Literal["command"]
    correlation_id: str
    context: Dict[str, Any]
    trace_id: Optional[str]
    service: str
    method: str
    params: Dict[str, Any]


class EventPayloadDict(TypedDict):
    """Type[EventPayloadDict]: represents an event that is published to a topic:

    :target: is currently provided here as an aid for the implementation, there are use cases
    where events are targeted to a specified audience or list or targets. In the NuroPb paradigm,
    targets could be individual users or other services. A service would represent the service
    as a whole, NOT any individual instance of that service.

    Reference the notes on EventType
    """

    tag: Literal["event"]
    correlation_id: str
    context: Dict[str, Any]
    trace_id: Optional[str]
    topic: str
    event: Any
    target: Optional[List[Any]]


class ResponsePayloadDict(TypedDict):
    """Type[ResponsePayloadDict]: represents a response to a request:"""

    tag: Literal["response"]
    correlation_id: str
    context: Dict[str, Any]
    trace_id: Optional[str]
    result: Any
    error: Optional[Dict[str, Any]]
    warning: Optional[str]


PayloadDict = Union[
    ResponsePayloadDict, RequestPayloadDict, CommandPayloadDict, EventPayloadDict
]

ServicePayloadTypes = Union[ResponsePayloadDict, CommandPayloadDict, EventPayloadDict]
ResponsePayloadTypes = Union[ResponsePayloadDict, EventPayloadDict]


class TransportServicePayload(TypedDict):
    """Type[TransportServicePayload]: represents valid service instruction payload.
    Depending on the transport implementation, there wire encoding and serialization may
    be different, and some of the fields may be in the body or header of the message.
    """

    nuropb_protocol: str  # nuropb defined and validated
    correlation_id: str  # nuropb defined
    trace_id: Optional[str]  # implementation defined
    ttl: Optional[int]  # time to live in milliseconds
    nuropb_type: NuropbMessageType
    nuropb_payload: Dict[str, Any]  # ServicePayloadTypes


class TransportRespondPayload(TypedDict):
    """Type[TransportRespondPayload]: represents valid service response message,
    valid nuropb payload types are ResponsePayloadDict, and EventPayloadDict
    """

    nuropb_protocol: str  # nuropb defined and validated
    correlation_id: str  # nuropb defined
    trace_id: Optional[str]  # implementation defined
    ttl: Optional[int]
    nuropb_type: NuropbMessageType
    nuropb_payload: ResponsePayloadTypes


ResultFutureResponsePayload = asyncio.Future[ResponsePayloadDict]
ResultFutureAny = asyncio.Future[Any]


AcknowledgeAction = Literal["ack", "nack", "reject"]
AcknowledgeCallbackFunction = Callable[[AcknowledgeAction], None]
""" AcknowledgeCallbackFunction: represents a callable with the inputs:
    - action: AcknowledgeAction  # one of "ack", "nack", "reject"
"""

MessageCompleteFunction = Callable[
    [List[TransportRespondPayload], AcknowledgeAction], None
]
""" MessageCompleteFunction: represents a callable with the inputs:
    - response_messages: List[TransportRespondPayload]  # the responses to be sent
    - acknowledge_action: AcknowledgeAction  # one of "ack", "nack", "reject"
"""

MessageCallbackFunction = Callable[
    [TransportServicePayload, MessageCompleteFunction, Dict[str, Any]], None
]
""" MessageCallbackFunction: represents a callable with the inputs:
    - message: TransportServicePayload  # the decoded message
    - message_complete: Optional[AcknowledgeCallbackFunction]  # a function that is called to acknowledge the message
    - metadata: Dict[str: Any]  # the context of the message
"""

ConnectionCallbackFunction = Callable[[Type["NuropbInterface"], str, str], None]
""" ConnectionCallbackFunction: represents a callable with the inputs:
    - instance: type of NuropbInterface
    - status: str  # the status of the connection (connected, disconnected)
    - reason: str  # the reason for the connection status change
"""


class NuropbException(Exception):
    """NuropbException: represents a base exception for all exceptions raised by the nuropb API
    although the input parameters are optional, it is recommended that the message is set to a
    meaningful value and the nuropb_lifecycle and nuropb_message are set to the values that were
    present when the exception was raised.
    """

    description: str
    lifecycle: NuropbLifecycleState | None
    payload: PayloadDict | TransportServicePayload | TransportRespondPayload | None
    exception: Exception | BaseException | None

    def __init__(
        self,
        description: Optional[str] = None,
        lifecycle: Optional[NuropbLifecycleState] = None,
        payload: Optional[PayloadDict] = None,
        exception: Optional[Exception] = None,
    ):
        if description is None:
            description = (
                f" {exception}"
                if exception is not None
                else f"{self.__class__.__name__}"
            )
        super().__init__(description)
        self.description = description
        self.lifecycle = lifecycle
        self.payload = payload
        self.exception = exception

    def to_dict(self):
        underlying_exception = str(self.exception) if self.exception else str(self)
        description = self.description if self.description else underlying_exception
        return {
            "error": self.__class__.__name__,
            "description": description,
        }


class NuropbTimeoutError(NuropbException):
    """NuropbTimeoutError: represents an error that occurred when a timeout was reached.

    The handling of this error will depend on the message type, context and where in the lifecycle
    of the message the timeout occurred.
    """

    pass


class NuropbTransportError(NuropbException):
    """NuropbTransportError: represents an error that inside the plumbing.

    The handling of this error will depend on the message type, context and where in the lifecycle
    of the message the timeout occurred.
    """

    pass


class NuropbMessageError(NuropbException):
    """NuropbMessageError: represents an error that occurred during the encoding or decoding of a
    message.

    The handling of this error will depend on the message type, context and where in the lifecycle
    of the message the timeout occurred.
    """

    pass


class NuropbHandlingError(NuropbException):
    """NuropbHandlingError: represents an error that occurred during the execution or fulfilment
    of a request or command. An error response is returned to the requester.

    The handling of this error will depend on the message type, context and where in the lifecycle
    of the message the timeout occurred.
    """

    pass


class NuropbDeprecatedError(NuropbHandlingError):
    """NuropbDeprecatedError: represents an error that occurred during the execution or fulfilment
    of a request, command or event topic that has been marked deprecated.

    An error response is returned to the requester ONLY for requests and commands.
    Events will be rejected with a NACK with requeue=False.
    """

    pass


class NuropbValidationError(NuropbException):
    """NuropbValidationError: represents an error that occurred during the validation of a
    request or command. An error response is returned to the requester.

    An error response is returned to the requester ONLY for requests and commands.
    Events will be rejected with a NACK with requeue=False.
    """

    pass


class NuropbAuthenticationError(NuropbException):
    """NuropbAuthenticationError: when this exception is raised, the transport layer will ACK the
    message and return an authentication error response to the requester.

    This exception occurs whe the identity of the requester can not be validated. for example
    an unknown, invalid or expired user identifier or auth token.

    The handling of this error will depend on the message type, context and where in the lifecycle
    of the message the timeout occurred.

    In most cases, the requester will not be able to recover from this error and will need provide
    valid credentials and retry the request. The approach to this retry outside the scope of the
    nuropb API.
    """

    pass


class NuropbAuthorizationError(NuropbException):
    """NuropbAuthorizationError: when this exception is raised, the transport layer will ACK the
    message and return an authorization error response to the requester.

    This exception occurs whe the requester does not have the required privileges to perform the
    requested action of either a request or command.

    The handling of this error will depend on the message type, context and where in the lifecycle
    of the message the timeout occurred.

    In most cases, the requester will not be able to recover from this error and will need provide
    valid credentials and retry the request. The approach to this retry outside the scope of the
    nuropb API.
    """


class NuropbNotDeliveredError(NuropbException):
    """NuropbNotDeliveredError: when this exception is raised, the transport layer will ACK the
    message and return an error response to the requester.
    """


class NuropbCallAgainReject(NuropbException):
    """NuropbCallAgainReject: when this exception is raised, the transport layer will REJECT
    the message

    To prevent accidental use of the redelivered parameter and to ensure system predictability
    on the Call Again feature, messages are only allowed to be redelivered once and only once.
    To this end all messages that have redelivered == True will be rejected.
    """


class NuropbCallAgain(NuropbException):
    """NuropbCallAgain: when this exception is raised, the transport layer will NACK the message
    and schedule it to be redelivered. The delay is determined by the transport layer or message
    broker. A call again will result in a forced repeated call of the original message, with the
    same correlation_id and trace_id.

    The call again "feature" is ignored for event service messages and response messages, as
    these are acked in all cases. The call again feature by implication is only supported for
    request and command messages.

    WARNING: with request messages, if a response has been returned, then this pattern
             SHOULD NOT be used. The requester will receive the same response again, which will be
             ignored as an unpaired response. if the underlying service method has no idempotence
             guarantees, the service could end up in an inconsistent state.
    """


class NuropbSuccess(NuropbException):
    """NuropbSuccessError: when this exception is raised, the transport layer will ACK the message
    and return a success response if service payload is a 'request'. This is useful when the request
    is a command or event and is executed asynchronously.

    There are some use cases where the service may want to return a success response irrespective
    to the handling of the request.

    A useful example is to short circuit processing when an outcome can be predetermined from the
    inputs alone. For end to end request-response consistency, this class must be instantiated with
    ResponsePayloadDict that contains a result consistent with the method and inputs provided.

    Another use case is for the transmission of events raised during the execution of an event,
    command or request. Events will only be sent to the transports layer after the successful
    processing of a service message.
    """

    result: Any
    payload: ResponsePayloadDict | None
    events: List[EventType] = []

    def __init__(
        self,
        result: Any,
        description: Optional[str] = None,
        payload: ResponsePayloadDict = None,
        lifecycle: Optional[NuropbLifecycleState] = None,
        events: Optional[List[EventType]] = None,
    ):
        super().__init__(
            description=description,
            lifecycle=lifecycle,
            payload=payload,
            exception=None,
        )
        self.result = result
        self.payload = payload
        self.events = [] if events is None else events


class NuropbInterface(ABC):
    """NuropbInterface: represents the interface that must be implemented by a nuropb API implementation"""

    _service_name: str
    _instance_id: str
    _service_instance: object

    @property
    def service_name(self) -> str:
        """service_name: returns the service name"""
        return self._service_name

    @property
    def instance_id(self) -> str:
        """instance_id: returns the instance id"""
        return self._instance_id

    async def connect(self) -> None:
        """connect: waits for the underlying transport to connect, an exception is raised if the connection fails
        to be established
        :return: None
        """
        raise NotImplementedError()  # pragma: no cover

    async def disconnect(self) -> None:
        """disconnect: disconnects from the underlying transport
        :return: None
        """
        raise NotImplementedError()  # pragma: no cover

    @property
    def connected(self) -> bool:
        """connected: returns the connection status of the underlying transport
        :return: bool
        """
        raise NotImplementedError()  # pragma: no cover

    @property
    def is_leader(self) -> bool:
        """is_leader: returns the leader status of the service instance
        :return: bool
        """
        raise NotImplementedError()  # pragma: no cover

    def receive_transport_message(
        self,
        service_message: TransportServicePayload,
        message_complete_callback: MessageCompleteFunction,
        metadata: Dict[str, Any],
    ) -> None:
        """handle_message: does the processing of a NuroPb message received from the transport
        layer.

        All response, request, command and event messages received from the transport layer are
        handled here.

        For failures service messages are handled, other than for events, a response including
        details of the error is returned to the flow originator.

        The Exception type raised during the message handling influences the lifecycle flow:
        Some of these could be:
        - NuropbTimeoutError
        - NuropbHandlingError
        - NuropbAuthenticationError
        - NuropbCallAgain
        - NuropbSuccess

        :param service_message: TransportServicePayload
        :param message_complete_callback: MessageCompleteFunction
        :param metadata: Dict[str, Any] - metric gathering information
        :return: None
        """
        raise NotImplementedError()  # pragma: no cover

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
        """request: sends a request to the target service and waits for a response. It is up to the
        implementation to manage message idempotency and message delivery guarantees.

        :param service: the service name
        :param method: the method name
        :param params: the method arguments, these must be easily serializable to JSON
        :param context: additional information that represent the context in which the request is executed.
            The must be easily serializable to JSON.
        :param ttl: the time to live of the request in milliseconds. After this time and dependent on the
            lifecycle state and underlying transport, it will not be consumed by the target service and
            should be assumed by the requester to have failed with an undetermined state.
        :param trace_id: an identifier to trace the request over the network (e.g. uuid4 hex string)
        :param rpc_response: if True (default), the actual response of the RPC call is returned and where
            there was an error during the lifecycle, this is raised as an exception.
            Where rpc_response is a ResponsePayloadDict, is returned.

        :return: ResponsePayloadDict
        """
        raise NotImplementedError()  # pragma: no cover

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
        raise NotImplementedError()  # pragma: no cover

    def publish_event(
        self,
        topic: str,
        event: Any,
        context: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> None:
        """publish_event: publishes an event to the transport layer. the event sender should not have
        any open transaction that is waiting for a response from this message. It is up to the
        implementation to manage message idempotency and message delivery guarantees.

        :param topic: the topic to publish to
        :param event: the message to publish, must be easily serializable to JSON
        :param context: additional information that represent the context in which the event is executed.
                        The must be easily serializable to JSON.
        :param trace_id: an identifier to trace the request over the network (e.g. uuid4 hex string)
        :return: None
        """
        raise NotImplementedError()  # pragma: no cover
