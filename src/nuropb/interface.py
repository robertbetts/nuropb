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

logger = logging.getLogger()


PayloadSerializeType = Literal["json"]
NuropbMessageType = Literal["request", "response", "event", "command"]


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


class CommandPayloadDict(BasePayloadDict):
    tag: Literal["command"]
    service: str
    method: str
    params: Dict[str, Any]


class EventPayloadDict(BasePayloadDict):
    tag: Literal["event"]
    topic: str
    event: Dict[str, Any]


class UnknownPayloadDict(BasePayloadDict):
    tag: Literal["unknown"]
    payload: Dict[str, Any]


PayloadDict = Union[
    ResponsePayloadDict, RequestPayloadDict,
    CommandPayloadDict, EventPayloadDict,
    UnknownPayloadDict
]


MessageCallbackType = Callable[[PayloadDict], None]
""" Type[BasePayloadDict]: represents a callable with a single argument of type NuropbMessageDict :
"""


ConnectionCallbackType = Callable[[Type["NuropbInterface"], str, str], None]
""" ConnectionCallbackType: represents a callable with the inputs:
    - instance: NuropbInterface
    - status: str  # the status of the connection (connected, disconnected)
    - reason: str  # the reason for the connection status change
"""


class NuropbMessageError(Exception):
    nuropb_message: PayloadDict

    def __init__(
        self,
        message: str,
        nuropb_message: PayloadDict,
    ):
        super().__init__(message)
        self.nuropb_message = nuropb_message


class NuropbInterface(ABC):
    """NuropbInterface: represents the interface that must be implemented by a nuropb implementation"""

    service_name: str
    instance_id: str

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

    async def request(
        self,
        service: str,
        method: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> Union[ResponsePayloadDict, Any]:
        """request: sends a request to the target service and waits for a response. It is up to the
        implementation to manage message idempotency and message delivery guarantees.

        :param service: the service name
        :param method: the method name
        :param params: the method arguments, these must be easily serializable to JSON
        :param context: additional information that represent the context in which the request is executed.
                        The must be easily serializable to JSON.
        :param ttl: the time to live of the request in milliseconds. After this time and dependent on the
                    underlying transport, it will not be consumed by the target
                    or
                    assumed by the requester to have failed with an undetermined state.
        :param trace_id: an identifier to trace the request over the network (e.g. a uuid4 hex string)

        :return: ResponsePayloadDict
        """
        raise NotImplementedError()

    async def command(
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
        :param trace_id: an identifier to trace the request over the network (e.g. a uuid4 hex string)

        :return: None
        """
        raise NotImplementedError()

    def handle_event(
        self,
        topic: str,
        event: Any,
        context: Dict[str, Any],
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """handle_event: handles an event received from the transport layer. The originator of the event
        should not have an uncommitted transaction that is waiting for this event to be handled. It is up to the
        implementation to manage message idempotency and message delivery guarantees.

        :param topic: the topic
        :param event: the event, must be easily serializable to JSON
        :param context: additional information that represent the context in which the event is executed.
                        The must be easily serializable to JSON.
        :param ttl: expiry is the time in milliseconds that the message will be kept on the queue before being moved
                    to the dead letter queue. If None, then the message expiry configured on the transport is used.
                    defaulted to 0 (no expiry) for events
        :param trace_id: an identifier to trace the request over the network (e.g. a uuid4 hex string)
        :return: None
        """
        raise NotImplementedError()

    async def publish_event(
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
        :param trace_id: an identifier to trace the request over the network (e.g. a uuid4 hex string)
        :return: None
        """
        raise NotImplementedError()
