import logging

import redis

logger = logging.getLogger(__name__)


def connect_basic():
    r = redis.Redis()
    r.ping()    

import asyncio

async def listen_to_redis_queue(redis_url, queue_name):
    r = redis.Redis.from_url(redis_url)
    pubsub = r.pubsub()

    try:
        pubsub.subscribe(queue_name)
        logger.info(f"Subscribed to {queue_name}")

        while True:
            message = pubsub.get_message()
            if message:
                logger.info(f"Received message: {message['data']}")
            await asyncio.sleep(0.01)  # Sleep briefly to avoid busy-waiting

    except redis.exceptions.ResponseError as e:
        if "no such key" in str(e).lower():
            raise Exception(f"The queue '{queue_name}' does not exist.") from e
        else:
            raise

    finally:
        pubsub.close()

async def read_from_redis_queue(redis_url, queue_name):
    r = redis.Redis.from_url(redis_url)
    pubsub = r.pubsub()

    try:
        pubsub.subscribe(queue_name)
        logger.info(f"Subscribed to {queue_name}")

        while True:
            message = pubsub.get_message()
            if message:
                logger.info(f"Received message: {message['data']}")
            await asyncio.sleep(0.01)  # Sleep briefly to avoid busy-waiting

    except redis.exceptions.ResponseError as e:
        if "no such key" in str(e).lower():
            raise Exception(f"The queue '{queue_name}' does not exist.") from e
        else:
            raise

    finally:
        pubsub.close()


async def create_redis_queue(redis_url, queue_name):
    r = redis.Redis.from_url(redis_url)
    try:
        # Attempt to create a new queue by setting a key
        if r.exists(queue_name):
            raise Exception(f"The queue '{queue_name}' already exists.")
        else:
            r.set(queue_name, "")
            logger.info(f"Queue '{queue_name}' created successfully.")
    except redis.exceptions.RedisError as e:
        logger.error(f"Failed to create queue '{queue_name}': {str(e)}")
        raise


async def remove_redis_queue(redis_url, queue_name):
    r = redis.Redis.from_url(redis_url)
    try:
        # Attempt to remove the queue by deleting the key
        if r.exists(queue_name):
            r.delete(queue_name)
            logger.info(f"Queue '{queue_name}' removed successfully.")
        else:
            raise Exception(f"The queue '{queue_name}' does not exist.")
    except redis.exceptions.RedisError as e:
        logger.error(f"Failed to remove queue '{queue_name}': {str(e)}")
        raise

async def purge_redis_queue(redis_url, queue_name):
    r = redis.Redis.from_url(redis_url)
    try:
        # Attempt to purge the queue by deleting all elements
        if r.exists(queue_name):
            r.set(queue_name, "")
            logger.info(f"Queue '{queue_name}' purged successfully.")
        else:
            raise Exception(f"The queue '{queue_name}' does not exist.")
    except redis.exceptions.RedisError as e:
        logger.error(f"Failed to purge queue '{queue_name}': {str(e)}")
        raise







if __name__ == "__main__":
    connect_basic()
