import pytest
from uuid import uuid4
import secrets
import logging
from typing import Dict, Any

from redis import asyncio as aioredis

from nuropb.redis_api import RedisAPI
from nuropb.redis_lib import build_redis_url

logger = logging.getLogger()



@pytest.mark.asyncio
async def test_redis_connect(redis_settings: Dict[str, Any]):
    url = build_redis_url(
        host=redis_settings["host"],
        port=redis_settings["port"],
        username=redis_settings["username"],
        password=redis_settings["password"],
        scheme=redis_settings["scheme"],
        database=redis_settings["database"],
    )
    connection = await aioredis.from_url(url)
    await connection.close()


@pytest.mark.asyncio
async def test_redis_connect_from_settings(redis_settings: Dict[str, Any]):
    url = build_redis_url()
    connection = await aioredis.from_url(url)
    await connection.close()

    url = build_redis_url(
        host=redis_settings["host"],
        port=redis_settings["port"],
        username=redis_settings["username"],
        password=redis_settings["password"],
        scheme=redis_settings["scheme"],
        database=redis_settings["database"],
    )
    connection = await aioredis.from_url(url)
    await connection.close()


@pytest.mark.asyncio
async def test_instantiate_api(redis_settings):
    """Test that the RedisAPI instance can be instantiated"""
    if isinstance(redis_settings, str):
        with pytest.raises(ValueError):
            test_url = "/".join(redis_settings.split("/")[:-1])
            redis_api = RedisAPI(
                url=test_url,
            )
    else:
        with pytest.raises(AttributeError):
            test_url = "/".join(redis_settings.split("/")[:-1]) # type: ignore
            redis_api = RedisAPI(
                url=test_url,
            )

    redis_api = RedisAPI(
        url=redis_settings,
    )
    await redis_api.connect()
    await redis_api.connect()
    assert redis_api.connected is True
    
    await redis_api.disconnect()
    assert redis_api.is_leader is True


@pytest.mark.asyncio
async def test_redis_api_client_mode(test_redis_settings: Dict[str, Any], redis_settings: Dict[str, Any]):
    """Test client mode. this is a client only instance of RedisAPI and only established a connection
    to the Redis server. It registers a response queue that is automatically associated with the default
    exchange, requires that Redis is sufficiently setup.
    """
    instance_id = uuid4().hex
    transport_settings = dict(
        prefetch_count=test_redis_settings["prefetch_count"],
    )
    redis_api = RedisAPI(
        instance_id=instance_id,
        url=redis_settings,
        transport_settings=transport_settings,
    )
    await redis_api.connect()
    assert redis_api.connected is True
    await redis_api.disconnect()
    assert redis_api.connected is False


# @pytest.mark.skip
@pytest.mark.asyncio
async def test_redis_api_service_mode(test_redis_settings: Dict[str, Any], redis_settings, service_instance):
    service_name = test_redis_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        prefetch_count=test_redis_settings["prefetch_count"],
    )
    redis_api = RedisAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        url=redis_settings,
        transport_settings=transport_settings,
    )
    await redis_api.connect()
    assert redis_api.connected is True
    await redis_api.disconnect()
    assert redis_api.connected is False
