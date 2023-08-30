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
)

logger = logging.getLogger()

NuropbInterfaceVersion = Literal["0.1.0"]
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


class BasePayloadDict(TypedDict):
    correlation_id: str
    context: Dict[str, Any]
    trace_id: Optional[str]


class RequestPayloadDict(BasePayloadDict):
    tag: Literal["request"]
    service: str
    method: str
    params: Dict[str, Any]
    reply_to: str


class ResponsePayloadDict(BasePayloadDict):
    tag: Literal["response"]
    result: Any
    error: Optional[Dict[str, Any]]
    warning: Optional[str]


class CommandPayloadDict(BasePayloadDict):
    tag: Literal["command"]
    service: str
    method: str
    params: Dict[str, Any]
    reply_to: str


class EventPayloadDict(BasePayloadDict):
    tag: Literal["event"]
    topic: str
    event: Dict[str, Any]


class UnknownPayloadDict(BasePayloadDict):
    tag: Literal["unknown"]
    payload: Dict[str, Any]


PayloadDict = Union[
    ResponsePayloadDict,
    RequestPayloadDict,
    CommandPayloadDict,
    EventPayloadDict,
    UnknownPayloadDict,
]


AcknowledgeActions = Literal["ack", "nack", "reject"]


MessageCallbackType = Callable[
    [PayloadDict, Optional[Callable[[AcknowledgeActions], None]]], None
]
""" Type[BasePayloadDict]: represents a callable with a single argument of type NuropbMessageDict :
"""


ConnectionCallbackType = Callable[[Type["NuropbInterface"], str, str], None]
""" ConnectionCallbackType: represents a callable with the inputs:
    - instance: NuropbInterface
    - status: str  # the status of the connection (connected, disconnected)
    - reason: str  # the reason for the connection status change
"""


class NuropbException(Exception):
    """NuropbException: represents a base exception for all exceptions raised by the nuropb API
    although the input parameters are optional, it is recommended that the message is set to a
    meaningful value and the nuropb_lifecycle and nuropb_message are set to the values that were
    present when the exception was raised.
    """

    lifecycle: NuropbLifecycleState | None
    payload: PayloadDict | None
    exception: Exception | None

    def __init__(
        self,
        message: Optional[str] = None,
        lifecycle: Optional[NuropbLifecycleState] = None,
        payload: Optional[PayloadDict] = None,
        exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.lifecycle = lifecycle
        self.payload = payload
        self.exception = exception


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


class NuropbValidationError(NuropbException):
    """NuropbValidationError: represents an error that occurred during the validation of a
    request or command. An error response is returned to the requester.

    An error response is returned to the requester ONLY for requests and commands.
    Events will be rejected with a NACK with requeue=False.
    """


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


class NuropbCallAgain(NuropbException):
    """NuropbCallAgain: when this exception is raised, the transport layer will NACK the message
    and schedule it to be redelivered after a delay. The delay is determined by the transport layer.
    """

    pass


class NuropbSuccess(NuropbException):
    """NuropbSuccessError: when this exception is raised, the transport layer will ACK the message
    and return a success response to the requester. This is useful when the request is a command
    or event and is executed asynchronously.

    There are some use cases where the service may want to return a success response irrespective
    to the handling of the request.
    """

    pass


class NuropbInterface(ABC):
    """NuropbInterface: represents the interface that must be implemented by a nuropb API implementation"""

    _service_name: str
    _instance_id: str

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
        raise NotImplementedError()

    async def disconnect(self) -> None:
        """disconnect: disconnects from the underlying transport
        :return: None
        """
        raise NotImplementedError()

    @property
    def connected(self) -> bool:
        """connected: returns the connection status of the underlying transport
        :return: bool
        """
        raise NotImplementedError()

    @property
    def is_leader(self) -> bool:
        """is_leader: returns the leader status of the service instance
        :return: bool
        """
        raise NotImplementedError()

    def handle_message(self, request: PayloadDict) -> None:
        """handle_message: does the processing of a decoded message received from the transport layer.

        Both response, request, command and event messages are handled by this method in the transport
        layer.

        If there is a failure while a service handles a request or command, a response that includes
        the details of the error is returned to the requester or originator.

        There are Exceptions that can be raised by the service instance that will influence the
        further lifecycle flow of the message. These are:
        - NuropbTimeoutError
        - NuropbHandlingError
        - NuropbAuthenticationError
        - NuropbCallAgain
        - NuropbSuccess

        :param request: the request
        :return: None
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def command(
        self,
        command: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
        wait_for_ack: bool = False,
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """command: sends a command to the target service. It is up to the implementation to manage message
        idempotency and message delivery guarantees.

        :param command: the service name
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
        raise NotImplementedError()

    def publish_event(
        self,
        topic: str,
        event: Any,
        context: Dict[str, Any],
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """publish_event: publishes an event to the transport layer. the event sender should not have
        any open transaction that is waiting for a response from this message. It is up to the
        implementation to manage message idempotency and message delivery guarantees.

        :param topic: the topic to publish to
        :param event: the message to publish, must be easily serializable to JSON
        :param context: additional information that represent the context in which the event is executed.
                        The must be easily serializable to JSON.
        :param ttl: expiry is the time in milliseconds that the message will be kept on the queue before being moved
                    to the dead letter queue. If None, then the message expiry configured on the transport is used.
                    defaulted to 0 (no expiry) for events
        :param trace_id: an identifier to trace the request over the network (e.g. uuid4 hex string)
        :return: None
        """
        raise NotImplementedError()
