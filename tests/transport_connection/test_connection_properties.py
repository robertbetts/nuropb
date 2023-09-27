import logging
from uuid import uuid4
import asyncio

import pytest

from nuropb.rmq_api import RMQAPI
from nuropb.rmq_transport import RMQTransport
from nuropb.testing.stubs import ServiceStub

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_setting_connection_properties(test_rmq_url, test_settings):
    """The client connection properties can be set by the user. The user can set the connection
    properties by passing a dictionary to the connection_properties argument of the RMQAPI
    constructor. The connection properties are used to set the properties of the AMQP connection
    that is established by the client.
    """
    amqp_url = {
        "host": "localhost",
        "username": "guest",
        "password": "guest",
        "port": test_rmq_url["port"],
        "vhost": test_rmq_url["vhost"],
        "verify": False,
    }
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
async def test_single_instance_connection(test_rmq_url, test_settings):
    """Test Single instance connections
    """
    amqp_url = {
        "host": "localhost",
        "username": "guest",
        "password": "guest",
        "port": test_rmq_url["port"],
        "vhost": test_rmq_url["vhost"],
    }
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
async def test_bad_credentials(test_rmq_url, test_settings):

    amqp_url = {
        "host": test_rmq_url["host"],
        "username": test_rmq_url["username"],
        "password": "bad_guest",
        "port": test_rmq_url["port"],
        "vhost": test_rmq_url["vhost"],
    }
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
async def test_bad_vhost(test_rmq_url, test_settings):

    amqp_url = {
        "host": test_rmq_url["host"],
        "username": test_rmq_url["username"],
        "password": test_rmq_url["password"],
        "port": test_rmq_url["port"],
        "vhost": "bad_vhost",
    }
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