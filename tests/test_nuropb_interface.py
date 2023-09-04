import asyncio
from typing import Dict, Any, Optional, Callable
from uuid import uuid4
import pytest  # type: ignore

from nuropb.interface import (
    NuropbInterface,
    ResponsePayloadDict,
    PayloadDict,
    AcknowledgeAction,
    RequestPayloadDict,
)


class TestTransport:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.started = False

    async def start(self):
        self.started = True

    async def stop(self):
        self.started = False

    @property
    def connected(self):
        return self.started


class TestInterface(NuropbInterface):
    _leader: bool
    _transport: object

    _test_request_future: asyncio.Future[ResponsePayloadDict] | None

    def __init__(
        self,
        service_name: str,
        instance_id: str,
        transport_class: Any,
        transport_settings: Dict[str, Any],
    ):
        self._service_name = service_name
        self._instance_id = instance_id or uuid4().hex
        self._leader = True
        self._test_request_future = None

        transport_settings.update(
            {
                "service_name": self.service_name,
                "instance_id": self.instance_id,
            }
        )
        self._transport = transport_class(**transport_settings)

    @property
    def connected(self) -> bool:
        """connected: returns the connection status of the underlying transport
        :return: bool
        """
        return self._transport.connected

    async def connect(self) -> None:
        """connect: waits for the underlying transport to connect, an exception is raised if the connection fails
        to be established
        :return: None
        """
        await self._transport.start()

    async def disconnect(self) -> None:
        """disconnect: disconnects from the underlying transport
        :return: None
        """
        await self._transport.stop()

    def receive_transport_message(
        self,
        message: PayloadDict,
        acknowledge_function: Optional[Callable[[AcknowledgeAction], None]],
    ) -> None:
        """
        TODO: update function to reflect the interface definition:
            service_message: TransportServicePayload,
            message_complete_callback: MessageCompleteFunction,
            metadata: Dict[str, Any],
        """
        if message["tag"] == "request":
            result = f"expected request response from {message['service']}.{message['method']}"
        elif message["tag"] == "command":
            result = f"expected command response from {message['service']}.{message['method']}"
        elif message["tag"] == "event":
            result = None
        else:
            raise ValueError(f"unexpected message type: {message['tag']}")

        if acknowledge_function:
            acknowledge_function("ack")
        response = ResponsePayloadDict(
            tag="response",
            result=result,
            error=None,
            correlation_id=message["correlation_id"],
            trace_id=message["trace_id"],
            context=message["context"],
        )
        if self._test_request_future:
            self._test_request_future.set_result(response)

    async def request(
        self,
        service: str,
        method: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
        rpc_response: bool = True,
    ) -> ResponsePayloadDict:
        """request: sends a request to the underlying transport and waits for the response
        :param service: the service to send the request to
        :param method: the method to invoke
        :param params: the parameters to send
        :param context: additional arguments that represent the context attached to the request.
        :param ttl: the time to live of the request
        :param trace_id: the trace id
        :param rpc_response: if True, the response is an expected RPC response, otherwise it is expected to be an
        event
        :return: ResponsePayloadDict
        """
        request = RequestPayloadDict(
            tag="request",
            service=service,
            method=method,
            params=params,
            correlation_id=uuid4().hex,
            trace_id=trace_id,
            context=context,
            reply_to="",
        )

        def acknowledge_function(action: AcknowledgeAction) -> None:
            _ = action

        self._test_request_future = asyncio.Future()
        self.receive_transport_message(request, acknowledge_function)
        response = await self._test_request_future
        return response


@pytest.mark.asyncio
async def test_basic_interface():
    service_name = "service_name"
    instance_id = uuid4().hex
    interface = TestInterface(
        service_name=service_name,
        instance_id=instance_id,
        transport_class=TestTransport,
        transport_settings={},
    )
    assert interface.service_name == service_name
    assert interface.instance_id == instance_id

    await interface.connect()
    assert interface.connected is True
    await interface.disconnect()
    assert interface.connected is False


@pytest.mark.asyncio
async def test_interface_send_request():
    service_name = "service_name"
    instance_id = uuid4().hex
    interface = TestInterface(
        service_name=service_name,
        instance_id=instance_id,
        transport_class=TestTransport,
        transport_settings={},
    )
    await interface.connect()

    service = "service"
    method = "method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 10
    trace_id = uuid4().hex
    response = await interface.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
    )
    assert response["result"] == f"expected request response from {service}.{method}"
    assert response["error"] is None
    assert response["correlation_id"] is not None
    assert response["trace_id"] == trace_id
