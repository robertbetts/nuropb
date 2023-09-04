import logging
import datetime
import secrets
from uuid import uuid4

import pytest

from nuropb.rmq_lib import (
    build_amqp_url,
    build_rmq_api_url,
    create_virtual_host,
    delete_virtual_host,
    configure_nuropb_rmq,
)
from nuropb.rmq_transport import RMQTransport
from nuropb.testing.stubs import ServiceExample

logging.getLogger("pika").setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def test_settings():
    start_time = datetime.datetime.utcnow()
    yield {
        "api_scheme": "http",
        "api_port": 15672,
        "port": 5672,
        "host": "127.0.0.1",
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
    }
    end_time = datetime.datetime.utcnow()
    logging.info(
        f"Test summary:\n"
        f"start_time: {start_time}\n"
        f"end_time: {end_time}\n"
        f"duration: {end_time - start_time}"
    )


@pytest.fixture(scope="session")
def test_rmq_url(test_settings):
    logging.debug("Setting up RabbitMQ test instance")
    vhost = f"pytest-{secrets.token_hex(8)}"
    rmq_url = build_amqp_url(
        host=test_settings["host"],
        port=test_settings["port"],
        username=test_settings["username"],
        password=test_settings["password"],
        vhost=vhost,
    )
    api_url = build_rmq_api_url(
        scheme=test_settings["api_scheme"],
        host=test_settings["host"],
        port=test_settings["api_port"],
        username=test_settings["username"],
        password=test_settings["password"],
    )

    create_virtual_host(api_url, rmq_url)

    def message_callback(*args, **kwargs):
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
        service_name=transport.service_name,
        rmq_url=rmq_url,
        events_exchange=transport.events_exchange,
        rpc_exchange=transport.rpc_exchange,
        dl_exchange=transport._dl_exchange,
        dl_queue=transport._dl_queue,
        service_queue=transport._service_queue,
        rpc_bindings=list(transport._rpc_bindings),
        event_bindings=list(transport._event_bindings),
    )
    yield rmq_url
    logging.debug("Shutting down RabbitMQ test instance")
    delete_virtual_host(api_url, rmq_url)


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
    )
    api_url = build_rmq_api_url(
        scheme=test_settings["api_scheme"],
        host=test_settings["host"],
        port=test_settings["api_port"],
        username=test_settings["username"],
        password=test_settings["password"],
    )

    create_virtual_host(api_url, rmq_url)

    def message_callback(*args, **kwargs):
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
        service_name=transport.service_name,
        rmq_url=rmq_url,
        events_exchange=transport.events_exchange,
        rpc_exchange=transport.rpc_exchange,
        dl_exchange=transport._dl_exchange,
        dl_queue=transport._dl_queue,
        service_queue=transport._service_queue,
        rpc_bindings=list(transport._rpc_bindings),
        event_bindings=list(transport._event_bindings),
    )
    yield rmq_url
    # logging.debug("Shutting down RabbitMQ test instance")
    # delete_virtual_host(api_url, rmq_url)


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
