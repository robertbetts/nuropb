import pytest
from uuid import uuid4
import logging

from nuropb.interface import NuropbMessageError, NuropbCallAgainReject
from nuropb.rmq_api import RMQAPI

logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger()


@pytest.mark.asyncio
async def test_request_response_pass(test_settings, test_rmq_url, service_instance):
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
    service = "missing_service"
    method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 5 * 1000
    trace_id = uuid4().hex
    logging.info(f"Requesting {service}.{method}")
    with pytest.raises(NuropbMessageError):
        await client_api.request(
            service=service,
            method=method,
            params=params,
            context=context,
            ttl=ttl,
            trace_id=trace_id,
            rpc_response=False,
        )
    await client_api.disconnect()
    assert client_api.connected is False
