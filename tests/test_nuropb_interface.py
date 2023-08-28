from typing import Dict, Any, Optional
from uuid import uuid4
import pytest  # type: ignore

from nuropb.interface import NuropbInterface, ResponsePayloadDict


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

    async def request(
        self,
        service: str,
        method: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> ResponsePayloadDict:
        """request: sends a request to the underlying transport and waits for the response
        :param service: the service to send the request to
        :param method: the method to invoke
        :param params: the parameters to send
        :param context: additional arguments that represent the context attached to the request.
        :param ttl: the time to live of the request
        :param trace_id: the trace id
        :return: ResponsePayloadDict
        """
        result = f"expected response from {service}.{method}"
        correlation_id = uuid4().hex
        response = ResponsePayloadDict(
            result=result,
            error=None,
            correlation_id=correlation_id,
            trace_id=trace_id,
            context=context,
        )
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
    assert response["result"] == f"expected response from {service}.{method}"
    assert response["error"] is None
    assert response["correlation_id"] is not None
    assert response["trace_id"] == trace_id
