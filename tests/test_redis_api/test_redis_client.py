import asyncio
import pytest
from uuid import uuid4
import logging
from typing import Dict, Any

from redis import asyncio as aioredis   

from nuropb.interface import NuropbMessageError, NuropbCallAgainReject
from nuropb.redis_api import RedisAPI

logger = logging.getLogger()


@pytest.mark.asyncio()
async def test_request_response_pass(test_redis_settings: Dict[str, Any], redis_settings, redis_url):
    instance_id = uuid4().hex
    client_transport_settings = dict(
        prefetch_count=test_redis_settings["prefetch_count"],
        default_ttl=test_redis_settings["default_ttl"],
    )
    client_api = RedisAPI(
        instance_id=instance_id,
        url=redis_settings,
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

    redis = client_api.transport._connection
        
    service_queue_name = f"nuropb-{service}-sq"
    # service_queue_name = service
    
    if await redis.exists(service_queue_name):
        logger.info(f"Service queue {service_queue_name} found")
        logger.info(f"Removing service queue {service_queue_name}")
        await redis.delete(service_queue_name)
    
    queue_size = await redis.llen(service_queue_name)
        
    assert queue_size == 0
    logger.info("Queue size before send: %s", queue_size)
    
    # with pytest.raises(NuropbMessageError):
    task = asyncio.create_task(client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
    ))
    logger.info("Request task created")
    await asyncio.sleep(1)
    await client_api.disconnect()
    assert client_api.connected is False

    redis = aioredis.from_url(redis_url)
    queue_size_after_send = await redis.llen(service_queue_name)
    await redis.aclose()
    logger.info("Queue size after send: %s", queue_size_after_send)
    assert queue_size_after_send == queue_size + 1
