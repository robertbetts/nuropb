import logging
import datetime
import secrets
from uuid import uuid4
import os

import pytest
import pytest_asyncio

from nuropb.rmq_api import RMQAPI
from nuropb.rmq_lib import (
    build_amqp_url,
    build_rmq_api_url,
    create_virtual_host,
    delete_virtual_host,
    configure_nuropb_rmq,
)
from nuropb.rmq_transport import RMQTransport
from nuropb.testing.stubs import IN_GITHUB_ACTIONS, ServiceExample

logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def etcd_config():
    if IN_GITHUB_ACTIONS:
        return None
    else:
        dict(
            host="localhost",
            port=2379,
        )


@pytest.fixture(scope="session")
def test_settings():
    start_time = datetime.datetime.utcnow()

    """
        Parameters in github actions
        RMQ_AMQP_PORT: ${{ job.services.rabbitmq.ports['5672'] }}
        RMQ_API_PORT: ${{ job.services.rabbitmq.ports['15672'] }}
    """
    logger.info(os.environ)
    api_port = os.environ.get("RMQ_API_PORT", "15672")
    amqp_port = os.environ.get("RMQ_AMQP_PORT", "5672")

    yield {
        "api_scheme": "http",
        "api_port": api_port,
        "scheme": "amqp",
        "port": amqp_port,
        "host": "localhost",
        "username": "guest",
        "password": "guest",
        "service_name": "test_service",
        "rpc_exchange": "test_rpc_exchange",
        "events_exchange": "test_events_exchange",
        "dl_exchange": "test_dl_exchange",
        "rpc_bindings": ["test_service"],
        "event_bindings": [],
        "prefetch_count": 1,
        "default_ttl": 60 * 30 * 1000,  # 30 minutes
        "verify": False,
        "ssl": False,
    }
    end_time = datetime.datetime.utcnow()
    logging.info(
        f"TEST SESSION SUMMARY:\n"
        f"start_time: {start_time}\n"
        f"end_time: {end_time}\n"
        f"duration: {end_time - start_time}"
    )


@pytest.fixture(scope="session")
def rmq_settings(test_settings):
    logging.debug("Setting up RabbitMQ test instance")
    vhost = f"pytest-{secrets.token_hex(8)}"

    settings = dict(
        host=test_settings["host"],
        port=test_settings["port"],
        username=test_settings["username"],
        password=test_settings["password"],
        vhost=vhost,
        verify=test_settings["verify"],
        ssl=test_settings["ssl"],
    )

    api_url = build_rmq_api_url(
        scheme=test_settings["api_scheme"],
        host=test_settings["host"],
        port=test_settings["api_port"],
        username=test_settings["username"],
        password=test_settings["password"],
    )

    create_virtual_host(api_url, settings)

    def message_callback(*args, **kwargs):  # pragma: no cover
        pass

    transport_settings = dict(
        service_name=test_settings["service_name"],
        instance_id=uuid4().hex,
        amqp_url=settings,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=[test_settings["service_name"]],
        event_bindings=[],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
        message_callback=message_callback,
    )
    transport = RMQTransport(**transport_settings)

    configure_nuropb_rmq(
        rmq_url=settings,
        events_exchange=transport.events_exchange,
        rpc_exchange=transport.rpc_exchange,
        dl_exchange=transport._dl_exchange,
        dl_queue=transport._dl_queue,
    )
    yield settings
    logging.debug("Shutting down RabbitMQ test instance")
    delete_virtual_host(api_url, settings)


@pytest.fixture(scope="session")
def test_rmq_url_static(test_settings):
    logging.debug("Setting up RabbitMQ test instance")
    vhost = f"pytest-vhost"
    rmq_url = build_amqp_url(
        host=test_settings["host"],
        port=test_settings["port"],
        username=test_settings["username"],
        password=test_settings["password"],
        vhost=vhost,
        scheme=test_settings["scheme"],
    )
    api_url = build_rmq_api_url(
        scheme=test_settings["api_scheme"],
        host=test_settings["host"],
        port=test_settings["api_port"],
        username=test_settings["username"],
        password=test_settings["password"],
    )

    create_virtual_host(api_url, rmq_url)

    def message_callback(*args, **kwargs):  # pragma: no cover
        pass

    transport_settings = dict(
        service_name=test_settings["service_name"],
        instance_id=uuid4().hex,
        amqp_url=rmq_url,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=[test_settings["service_name"]],
        event_bindings=[],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
        message_callback=message_callback,
    )
    transport = RMQTransport(**transport_settings)

    configure_nuropb_rmq(
        rmq_url=rmq_url,
        events_exchange=transport.events_exchange,
        rpc_exchange=transport.rpc_exchange,
        dl_exchange=transport._dl_exchange,
        dl_queue=transport._dl_queue,
    )
    yield rmq_url
    logging.debug("Shutting down RabbitMQ test instance")
    delete_virtual_host(api_url, rmq_url)


@pytest.fixture(scope="session")
def test_api_url(test_settings):
    rmq_url = build_rmq_api_url(
        scheme=test_settings["api_scheme"],
        host=test_settings["host"],
        port=test_settings["api_port"],
        username=test_settings["username"],
        password=test_settings["password"],
    )
    return rmq_url


@pytest.fixture(scope="session")
def service_instance():
    return ServiceExample(
        service_name="test_service",
        instance_id=uuid4().hex,
    )


@pytest_asyncio.fixture(scope="function")
async def mesh_service(test_settings, rmq_settings, service_instance):
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
    yield service_api

    await service_api.disconnect()


@pytest_asyncio.fixture(scope="function")
async def mesh_client(rmq_settings, test_settings, mesh_service):
    instance_id = uuid4().hex
    settings = mesh_service.transport.rmq_configuration
    client_transport_settings = dict(
        dl_exchange=settings["dl_exchange"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    client_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=rmq_settings,
        rpc_exchange=settings["rpc_exchange"],
        events_exchange=settings["events_exchange"],
        transport_settings=client_transport_settings,
    )
    yield client_api

    await client_api.disconnect()
