import asyncio
import logging
from uuid import uuid4

import pytest

from nuropb.rmq_api import RMQAPI
from nuropb.service_runner import ServiceContainer

logger = logging.getLogger()


@pytest.mark.asyncio
async def test_rmq_api_client_mode(
    test_settings, rmq_settings, test_api_url, etcd_config
):
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
        amqp_url=rmq_settings,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
    )

    # FYI, Challenges with etcd features when tests run under Github Actions
    container = ServiceContainer(
        rmq_api_url=test_api_url,
        instance=rmq_api,
        etcd_config=etcd_config,
    )
    await container.start()
    await container.stop()


@pytest.mark.asyncio
async def test_rmq_api_service_mode(
    test_settings, rmq_settings, test_api_url, service_instance, etcd_config
):
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    rmq_api = RMQAPI(
        service_name=test_settings["service_name"],
        service_instance=service_instance,
        instance_id=instance_id,
        amqp_url=rmq_settings,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
    )

    # FYI, Challenges with etcd features when tests run under Github Actions
    container = ServiceContainer(
        rmq_api_url=test_api_url,
        instance=rmq_api,
        etcd_config=etcd_config,
    )
    await container.start()
    await container.stop()


@pytest.mark.asyncio
async def test_rmq_api_service_mode_no_etcd(test_settings, rmq_settings, test_api_url):
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
        amqp_url=rmq_settings,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
    )
    container = ServiceContainer(
        rmq_api_url=test_api_url,
        instance=rmq_api,
    )
    await container.start()
    await container.stop()
