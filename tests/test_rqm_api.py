import pytest
from uuid import uuid4
import secrets
import logging

from nuropb.rmq_api import RMQAPI
from nuropb.rmq_lib import create_virtual_host, delete_virtual_host

logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger()


def test_rmq_preparation(test_settings, test_rmq_url, test_api_url):
    """Test that the RMQ instance is and can be correctly configured
    - create virtual host must be idempotent
    - delete virtual host must be idempotent
    """
    if isinstance(test_rmq_url, str):
        tmp_url = f"{test_rmq_url}-{secrets.token_hex(8)}"
    else:
        tmp_url = test_rmq_url.copy()
        tmp_url["vhost"] = f"{test_rmq_url['vhost']}-{secrets.token_hex(8)}"
    create_virtual_host(test_api_url, tmp_url)
    create_virtual_host(test_api_url, tmp_url)
    delete_virtual_host(test_api_url, tmp_url)
    delete_virtual_host(test_api_url, tmp_url)


@pytest.mark.asyncio
async def test_instantiate_api(test_settings, test_rmq_url):
    """Test that the RMQAPI instance can be instantiated"""
    if isinstance(test_rmq_url, str):
        with pytest.raises(ValueError):
            test_url = "/".join(test_rmq_url.split("/")[:-1])
            rmq_api = RMQAPI(
                amqp_url=test_url,
            )
    else:
        with pytest.raises(AttributeError):
            test_url = "/".join(test_rmq_url.split("/")[:-1])
            rmq_api = RMQAPI(
                amqp_url=test_url,
            )


    rmq_api = RMQAPI(
        amqp_url=test_rmq_url,
    )
    await rmq_api.connect()
    await rmq_api.connect()
    await rmq_api.disconnect()

    assert rmq_api.is_leader is True


@pytest.mark.asyncio
async def test_rmq_api_client_mode(test_settings, test_rmq_url):
    """Test client mode. this is a client only instance of RMQAPI and only established a connection
    to the RMQ server. It registers a response queue that is automatically associated with the default
    exchange, requires that RMQ is sufficiently setup.
    """
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=[],
        event_bindings=[],
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
    await rmq_api.connect()
    assert rmq_api.connected is True
    await rmq_api.disconnect()
    assert rmq_api.connected is False


# @pytest.mark.skip


@pytest.mark.asyncio
async def test_rmq_api_service_mode(test_settings, test_rmq_url, service_instance):
    service_name = test_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    rmq_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        amqp_url=test_rmq_url,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
    )
    await rmq_api.connect()
    assert rmq_api.connected is True
    await rmq_api.disconnect()
    assert rmq_api.connected is False
