import pytest
from uuid import uuid4
import logging
from nuropb.rmq_api import RMQAPI
from nuropb.rmq_transport import ServiceNotConfigured, configure_rmq

logging.getLogger("pika").setLevel(logging.WARNING)


@pytest.mark.asyncio
async def test_rmq_api():
    service_name = "un_configured_service"
    instance_id = uuid4().hex
    rmq_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url="amqp://guest:guest@localhost:5672/test",
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        dl_exchange="test_dl_exchange",
        rpc_bindings=[service_name],
        event_bindings=[],
        prefetch_count=1,
        default_ttl=60 * 30,  # 30 minutes
    )

    # assert rmq_api.connected is False
    # with pytest.raises(ServiceNotConfigured):
    #     await rmq_api.connect()
    #     assert rmq_api.connected is False

    rmq_api._transport._client_only = True
    await rmq_api.connect()
    assert rmq_api.connected is True
    await rmq_api.disconnect()
    assert rmq_api.connected is False


@pytest.mark.asyncio
async def test_configure_and_run_api():
    service_name = "test_service"
    instance_id = uuid4().hex
    amqp_url = "amqp://guest:guest@localhost:5672/test"

    rmq_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=amqp_url,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        dl_exchange="test_dl_exchange",
        rpc_bindings=[service_name],
        event_bindings=[],
        prefetch_count=1,
        default_ttl=60 * 30,  # 30 minutes
    )

    configured = configure_rmq(
        rmq_url=amqp_url,
        rpc_exchange=rmq_api._transport._rpc_exchange,
        events_exchange=rmq_api._transport._events_exchange,
        dl_exchange=rmq_api._transport._dl_exchange,
        dl_queue=rmq_api._transport._dl_queue,
        request_queue=rmq_api._transport._request_queue,
        response_queue=rmq_api._transport._response_queue,
        rpc_bindings=[service_name],
        event_bindings=[],
    )
    assert configured is True

    assert rmq_api.connected is False
    await rmq_api.connect()
    assert rmq_api.connected is True


@pytest.mark.asyncio
async def test_request_response():
    service_name = "test_service"
    instance_id = uuid4().hex
    amqp_url = "amqp://guest:guest@localhost:5672/test"
    service_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=amqp_url,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        dl_exchange="test_dl_exchange",
        rpc_bindings=[service_name],
        event_bindings=[],
        prefetch_count=1,
        default_ttl=60 * 30,  # 30 minutes
    )
    configured = configure_rmq(
        rmq_url=amqp_url,
        rpc_exchange=service_api._transport._rpc_exchange,
        events_exchange=service_api._transport._events_exchange,
        dl_exchange=service_api._transport._dl_exchange,
        dl_queue=service_api._transport._dl_queue,
        request_queue=service_api._transport._request_queue,
        response_queue=service_api._transport._response_queue,
        rpc_bindings=[service_name],
        event_bindings=[],
    )
    assert configured is True
    assert service_api.connected is False
    await service_api.connect()
    assert service_api.connected is True

    service_name = "test_client"
    instance_id = uuid4().hex
    client_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url="amqp://guest:guest@localhost:5672/test",
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        prefetch_count=1,
        default_ttl=60 * 30 * 1000,  # 30 minutes
    )
    client_api._transport._client_only = True
    await client_api.connect()
    assert client_api.connected is True
    service = "test_service"
    method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 30 * 1000
    trace_id = uuid4().hex
    logging.info(f"Requesting {service}.{method}")
    response = await client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
    )
    logging.info(f"response: {response}")
    assert response == f"response from {service}.{method}"
    rpc_response = await client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
        rpc_response=False,
    )
    logging.info(f"response: {rpc_response}")
    assert rpc_response["result"] == f"response from {service}.{method}"
    await client_api.disconnect()
    assert client_api.connected is False
