import pytest
from uuid import uuid4
import logging

from nuropb.interface import NuropbException, NuropbMessageError, NuropbCallAgainReject
from nuropb.rmq_api import RMQAPI

logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger()


@pytest.mark.asyncio
async def test_request_response_fail(test_settings, rmq_settings, service_instance):
    service_name = test_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    service_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=transport_settings,
    )
    assert service_api.connected is False
    await service_api.connect()
    assert service_api.connected is True

    service_name = "test_client"
    instance_id = uuid4().hex
    client_transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    client_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=client_transport_settings,
    )
    await client_api.connect()
    assert client_api.connected is True
    service = "test_service"
    method = "test_method_DOES_NOT_EXIST"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 30 * 1000
    trace_id = uuid4().hex
    logger.info(f"Requesting {service}.{method}")
    with pytest.raises(NuropbMessageError) as error:
        result = await client_api.request(
            service=service,
            method=method,
            params=params,
            context=context,
            ttl=ttl,
            trace_id=trace_id,
        )
    assert error.value.description == "Unknown method test_method_DOES_NOT_EXIST"

    method = "test_method"
    rpc_response = await client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
        rpc_response=False,
    )
    logger.info(f"response: {rpc_response}")
    assert rpc_response["result"] == f"response from {service}.{method}"
    await client_api.disconnect()
    assert client_api.connected is False
    await service_api.disconnect()
    assert service_api.connected is False


@pytest.mark.asyncio
async def test_request_response_pass(test_settings, rmq_settings, service_instance):
    service_name = test_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    service_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True
    logger.info("SERVICE API CONNECTED")

    instance_id = uuid4().hex
    client_transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    client_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=client_transport_settings,
    )
    await client_api.connect()
    assert client_api.connected is True
    logger.info("CLIENT CONNECTED")
    service = "test_service"
    method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 5 * 1000
    trace_id = uuid4().hex
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
        rpc_response=False,
    )
    logger.info(f"response: {rpc_response}")
    assert rpc_response["result"] == f"response from {service}.{method}"
    await client_api.disconnect()
    assert client_api.connected is False
    await service_api.disconnect()
    assert service_api.connected is False


@pytest.mark.asyncio
async def test_request_response_success(test_settings, rmq_settings, service_instance):
    service_name = test_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    service_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True
    logger.info("SERVICE API CONNECTED")

    instance_id = uuid4().hex
    client_transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    client_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=client_transport_settings,
    )
    await client_api.connect()
    assert client_api.connected is True
    logger.info("CLIENT CONNECTED")
    service = "test_service"
    method = "test_success_error"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 5 * 1000
    trace_id = uuid4().hex
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
        rpc_response=False,
    )
    logger.info(f"response: {rpc_response}")
    assert rpc_response["result"] == f"response from {service}.{method}"
    await client_api.disconnect()
    assert client_api.connected is False
    await service_api.disconnect()
    assert service_api.connected is False


@pytest.mark.asyncio
async def test_request_response_call_again(
    test_settings, rmq_settings, service_instance
):
    service_name = test_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    service_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True
    logger.info("SERVICE API CONNECTED")

    instance_id = uuid4().hex
    client_transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    client_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=client_transport_settings,
    )
    await client_api.connect()
    assert client_api.connected is True
    logger.info("CLIENT CONNECTED")
    trace_id = uuid4().hex
    service = "test_service"
    method = "test_call_again_error"
    params = {"trace_id": trace_id}
    context = {"context1": "value1"}
    ttl = 60 * 5 * 1000
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
    )
    logger.info(f"response: {rpc_response}")
    assert rpc_response["success"] == f"response from {service}.{method}"
    assert rpc_response["trace_id"] == trace_id
    await client_api.disconnect()
    assert client_api.connected is False
    await service_api.disconnect()
    assert service_api.connected is False


@pytest.mark.asyncio
async def test_request_response_call_again_loop_fail(
    test_settings, rmq_settings, service_instance
):
    service_name = test_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    service_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True
    logger.info("SERVICE API CONNECTED")

    instance_id = uuid4().hex
    client_transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    client_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=rmq_settings,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=client_transport_settings,
    )
    await client_api.connect()
    assert client_api.connected is True
    logger.info("CLIENT CONNECTED")
    trace_id = uuid4().hex
    service = "test_service"
    method = "test_call_again_loop"
    params = {"trace_id": trace_id}
    context = {"context1": "value1"}
    ttl = 60 * 5 * 1000
    logger.info(f"Requesting {service}.{method}")
    with pytest.raises(NuropbMessageError):
        await client_api.request(
            service=service,
            method=method,
            params=params,
            context=context,
            ttl=ttl,
            trace_id=trace_id,
        )

    result = await client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
        rpc_response=False,
    )
    assert result["error"]["error"] == "NuropbCallAgainReject"
    await client_api.disconnect()
    assert client_api.connected is False
    await service_api.disconnect()
    assert service_api.connected is False
