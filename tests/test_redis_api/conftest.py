import logging
import datetime
from uuid import uuid4
import os
from typing import Dict, Any

import pytest

from nuropb.redis_transport import RedisTransport
from nuropb.redis_lib import (
    build_redis_url,
    configure_nuropb_redis
)
from nuropb.testing.stubs import IN_GITHUB_ACTIONS, ServiceExample

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_redis_settings():
    start_time = datetime.datetime.utcnow()

    """
        Parameters in github actions
        REDIS_PORT: ${{ job.services.redis.ports['6379'] }}
    """
    # logger.info(os.environ)
    redis_port = os.environ.get("REDIS_PORT", "6379")

    yield {
        "scheme": "redis",
        "host": "127.0.0.1",
        "port": redis_port,
        "username": None,
        "password": None,
        "database": 0,
        "service_name": "test_service",
        "rpc_exchange": "test_rpc_exchange",
        "events_exchange": "test_events_exchange",
        "dl_exchange": "test_dl_exchange",
        "rpc_bindings": ["test_service"],
        "event_bindings": [],
        "prefetch_count": 1,
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
def redis_settings(test_redis_settings: Dict[str, Any]):
    logging.debug("Setting up Redis test instance")
    database = None

    settings = dict(
        scheme=test_redis_settings["scheme"],
        host=test_redis_settings["host"],
        port=test_redis_settings["port"],
        username=test_redis_settings["username"],
        password=test_redis_settings["password"],
        database=database,
        verify=test_redis_settings["verify"],
        ssl=test_redis_settings["ssl"],
    )

    def message_callback(*args, **kwargs):  # pragma: no cover
        pass

    transport_settings = dict(
        service_name=test_redis_settings["service_name"],
        instance_id=uuid4().hex,
        url=settings,
        database=database,
        prefetch_count=test_redis_settings["prefetch_count"],
        message_callback=message_callback,
    )
    transport = RedisTransport(**transport_settings)

    yield settings


@pytest.fixture(scope="session")
def redis_url(test_redis_settings: Dict[str, Any]):
    url = build_redis_url(
            host=test_redis_settings["host"],
            port=test_redis_settings["port"],
            username=test_redis_settings["username"],
            password=test_redis_settings["password"],
            scheme=test_redis_settings["scheme"],
            database=test_redis_settings["database"],
        )
    yield url

@pytest.fixture(scope="session")
def test_redis_url_static(test_redis_settings: Dict[str, Any]):
    logging.debug("Setting up Redis test instance")
    database = 0
    url = build_redis_url(
        scheme=test_redis_settings["scheme"],
        host=test_redis_settings["host"],
        port=test_redis_settings["port"],
        username=test_redis_settings["username"],
        password=test_redis_settings["password"],
        database=database,
    )


    def message_callback(*args, **kwargs):  # pragma: no cover
        pass

    transport_settings = dict(
        service_name=test_redis_settings["service_name"],
        instance_id=uuid4().hex,
        url=url,
        rpc_exchange=test_redis_settings["rpc_exchange"],
        events_exchange=test_redis_settings["events_exchange"],
        dl_exchange=test_redis_settings["dl_exchange"],
        rpc_bindings=[test_redis_settings["service_name"]],
        event_bindings=[],
        prefetch_count=test_redis_settings["prefetch_count"],
        message_callback=message_callback,
    )
    transport = RedisTransport(**transport_settings)

    configure_nuropb_redis(
        url=url,
        events_exchange=transport.events_exchange,
        rpc_exchange=transport.rpc_exchange,
        dl_exchange=transport._dl_exchange,
        dl_queue=transport._dl_queue,
    )
    yield url

