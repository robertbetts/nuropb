import pytest
from uuid import uuid4
import logging

from nuropb.rmq_api import RMQAPI

logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger()


# @pytest.mark.skip
@pytest.mark.asyncio
async def test_async_service_methods(test_settings, test_rmq_url, service_instance):
    """
    FIXME: There is a race condition in the test that causes the test to hang, the suspicion is that
           is the handling of async methods on a service instance.
    """
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
        amqp_url=test_rmq_url,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True

    logging.info("SERVICE API CONNECTED")

    instance_id = uuid4().hex
    client_transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    client_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=test_rmq_url,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=client_transport_settings,
    )
    await client_api.connect()
    assert client_api.connected is True
    logging.info("CLIENT CONNECTED")
    service = "test_service"
    method = "test_async_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 5 * 1000
    trace_id = uuid4().hex
    logging.info(f"Requesting {service}.{method}")
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
    await service_api.disconnect()
    assert service_api.connected is False
