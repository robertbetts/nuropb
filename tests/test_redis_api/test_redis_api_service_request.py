import pytest
from uuid import uuid4
import logging
from typing import Dict, Any

from nuropb.interface import NuropbException, NuropbMessageError, NuropbCallAgainReject
from nuropb.redis_api import RedisAPI

logger = logging.getLogger()


@pytest.mark.asyncio
async def test_request_response_pass(test_redis_settings: Dict[str, Any], redis_settings, service_instance):
    service_name = test_redis_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        prefetch_count=test_redis_settings["prefetch_count"],
        default_ttl=test_redis_settings["default_ttl"],
    )
    service_api = RedisAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        url=redis_settings,
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True
    logger.info("SERVICE API CONNECTED")

    instance_id = uuid4().hex
    client_transport_settings = dict(
        prefetch_count=test_redis_settings["prefetch_count"],
        default_ttl=test_redis_settings["default_ttl"],
    )
    client_api = RedisAPI(
        instance_id=instance_id,
        url=redis_settings,
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
async def test_request_response_fail(test_redis_settings: Dict[str, Any], redis_settings, service_instance):
    service_name = test_redis_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        prefetch_count=test_redis_settings["prefetch_count"],
        default_ttl=test_redis_settings["default_ttl"],
    )
    service_api = RedisAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        url=redis_settings,
        transport_settings=transport_settings,
    )
    assert service_api.connected is False
    await service_api.connect()
    assert service_api.connected is True

    service_name = "test_client"
    instance_id = uuid4().hex
    client_transport_settings = dict(
        prefetch_count=test_redis_settings["prefetch_count"],
        default_ttl=test_redis_settings["default_ttl"],
    )
    client_api = RedisAPI(
        instance_id=instance_id,
        url=redis_settings,
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
async def test_request_response_success(test_redis_settings: Dict[str, Any], redis_settings, service_instance):
    service_name = test_redis_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        rpc_bindings=test_redis_settings["rpc_bindings"],
        event_bindings=test_redis_settings["event_bindings"],
        prefetch_count=test_redis_settings["prefetch_count"],
        default_ttl=test_redis_settings["default_ttl"],
    )
    service_api = RedisAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        url=redis_settings,
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True
    logger.info("SERVICE API CONNECTED")

    instance_id = uuid4().hex
    client_transport_settings = dict(
        prefetch_count=test_redis_settings["prefetch_count"],
        default_ttl=test_redis_settings["default_ttl"],
    )
    client_api = RedisAPI(
        instance_id=instance_id,
        url=redis_settings,
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

