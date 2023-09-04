import logging
from uuid import uuid4

import pytest

from nuropb.rmq_api import RMQAPI
from nuropb.service_runner import ServiceContainer

logger = logging.getLogger()

# @pytest.mark.skip
@pytest.mark.asyncio
async def test_rmq_api_service_mode(test_settings, test_rmq_url, test_api_url):
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    rmq_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=test_rmq_url,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
    )
    container = ServiceContainer(
        rmq_api_url=test_api_url,
        instance=rmq_api,
        etcd_config=dict(
            host="localhost",
            port=2379,
        ),
    )
    # await container.start()


@pytest.mark.asyncio
async def test_rmq_api_service_mode_no_etcd(test_settings, test_rmq_url, test_api_url):
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    rmq_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=test_rmq_url,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
    )
    container = ServiceContainer(
        rmq_api_url=test_api_url,
        instance=rmq_api,
    )
    await container.start()
