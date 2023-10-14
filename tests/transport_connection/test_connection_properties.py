import logging
from uuid import uuid4
import asyncio

import pytest

from nuropb.rmq_api import RMQAPI
from nuropb.rmq_lib import rmq_api_url_from_amqp_url
from nuropb.rmq_transport import RMQTransport
from nuropb.testing.stubs import ServiceStub

logger = logging.getLogger(__name__)


def test_ampq_url_to_api_url():
    api_url = rmq_api_url_from_amqp_url(
        "amqp://guest:guest@localhost:5672/nuropb-example"
    )
    assert api_url == "http://guest:guest@localhost:15672/api"

    api_url = rmq_api_url_from_amqp_url("amqp://guest@localhost:5672/nuropb-example")
    assert api_url == "http://guest@localhost:15672/api"

    api_url = rmq_api_url_from_amqp_url("amqp:///nuropb-example")
    assert api_url == "http://localhost:15672/api"

    api_url = rmq_api_url_from_amqp_url(
        "amqps://guest:guest@localhost:5672/nuropb-example"
    )
    assert api_url == "https://guest:guest@localhost:15672/api"

    api_url = rmq_api_url_from_amqp_url("amqps://guest:guest@localhost/nuropb-example")
    assert api_url == "https://guest:guest@localhost:15671/api"


@pytest.mark.asyncio
async def test_setting_connection_properties(rmq_settings, test_settings):
    """The client connection properties can be set by the user. The user can set the connection
    properties by passing a dictionary to the connection_properties argument of the RMQAPI
    constructor. The connection properties are used to set the properties of the AMQP connection
    that is established by the client.
    """
    amqp_url = rmq_settings.copy()
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
    )

    def message_callback(*args, **kwargs):
        pass

    transport1 = RMQTransport(
        service_name="test-service",
        instance_id=uuid4().hex,
        amqp_url=amqp_url,
        message_callback=message_callback,
        **transport_settings,
    )

    await transport1.start()
    assert transport1.connected is True

    service = ServiceStub(
        service_name="test-service",
        instance_id=uuid4().hex,
    )
    api = RMQAPI(
        service_name=service.service_name,
        instance_id=service.instance_id,
        service_instance=service,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )
    await api.connect()
    assert api.connected is True

    await transport1.stop()
    assert transport1.connected is False
    await api.disconnect()
    assert api.connected is False


@pytest.mark.asyncio
async def test_single_instance_connection(rmq_settings, test_settings):
    """Test Single instance connections"""
    amqp_url = rmq_settings.copy()
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
    )

    def message_callback(*args, **kwargs):
        pass

    transport1 = RMQTransport(
        service_name="test-service",
        instance_id="Single_instance_id",
        amqp_url=amqp_url,
        message_callback=message_callback,
        **transport_settings,
    )

    await transport1.start()
    assert transport1.connected is True

    transport_settings["vhost"] = "bad"
    service = ServiceStub(
        service_name="test-service",
        instance_id="Single_instance_id",
    )
    api = RMQAPI(
        service_name=service.service_name,
        instance_id=service.instance_id,
        service_instance=service,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )
    await api.connect()
    logger.info("Connected : %s", api.connected)
    await asyncio.sleep(3)
    assert api.connected is False
    await transport1.stop()
    assert transport1.connected is False
    await api.disconnect()


@pytest.mark.asyncio
async def test_bad_credentials(rmq_settings, test_settings):
    amqp_url = rmq_settings.copy()
    amqp_url["username"] = "bad-username"
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
    )

    service = ServiceStub(
        service_name="test-service",
        instance_id="Single_instance_id",
    )
    api = RMQAPI(
        service_name=service.service_name,
        instance_id=service.instance_id,
        service_instance=service,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )
    await api.connect()
    logger.info("Connected : %s", api.connected)
    assert api.connected is False


@pytest.mark.asyncio
async def test_bad_vhost(rmq_settings, test_settings):
    amqp_url = rmq_settings.copy()
    amqp_url["vhost"] = "bad-vhost"
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
    )

    service = ServiceStub(
        service_name="test-service",
        instance_id="Single_instance_id",
    )
    api = RMQAPI(
        service_name=service.service_name,
        instance_id=service.instance_id,
        service_instance=service,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )
    await api.connect()
    logger.info("Connected : %s", api.connected)
    assert api.connected is False
