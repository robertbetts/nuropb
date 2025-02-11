import logging
import json
import asyncio
from redis import asyncio as aioredis
import redis

logger = logging.getLogger(__name__)


async def subscribe_to_redis_pubsub(redis_url, queue_name):
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
            # Initialize the queue with an empty JSON array
            r.set(queue_name, "[]")
            logger.info(f"Queue '{queue_name}' created successfully with JSON format.")
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



async def write_json_messages(r, queue_name, n):
    import json
    import random
    import string
    logger.info(f"Writing {n} messages to queue '{queue_name}'")
    try:
        for _ in range(n):
            message = {
                "id": ''.join(random.choices(string.ascii_letters + string.digits, k=8)),
                "value": random.randint(1, 100),
                "status": random.choice(["new", "processing", "completed"])
            }
            message_json = json.dumps(message)
            await r.lpush(queue_name, message_json)
            logger.info(f"Message {message['id']} added to queue '{queue_name}'")
    except Exception as e:
        logger.error(f"Failed to write messages to queue '{queue_name}': {str(e)}")

async def read_json_messages(r, queue, n):
    read_count = 0
    try:
        while True:
            message_received = await r.lpop(queue)
            if message_received:
                read_count += 1
                message = json.loads(message_received.decode())
                logger.info(f"Message {message['id']} read from queue '{queue}'")
                if read_count >= n:
                    break
                    
    except Exception as e:
        logger.exception(f"Error reading messages from queues: {str(e)}")
        
    return read_count

async def read_json_messages_2(r, queues, n):
    read_count = 0
    try:
        while True:
            queue_received, message_received = await r.blpop(queues, timeout=0)
            if message_received:
                read_count += 1
                message = json.loads(message_received.decode())
                logger.info(f"Message {message['id']} read from queue '{queue_received}'")
                if read_count >= n:
                    break
                    
    except Exception as e:
        logger.exception(f"Error reading messages from queues: {str(e)}")
        
    return read_count


async def queue_example():
    redis_url = "redis://127.0.0.1:6379/0"
    redis_url = "redis://127.0.0.1:6379/"
    
    queues = ["example_queue_1", "example_queue_2"]
    
    conn = aioredis.from_url(redis_url)
    
    for queue in queues:
        if await conn.exists(queue):
            await conn.delete(queue)
            logger.info(f"Queue '{queue}' removed successfully.")
    
    # tasks = [asyncio.create_task(read_json_messages(conn, queue, 5)) for queue in queues]
    tasks = [asyncio.create_task(read_json_messages_2(conn, queues, 5))]
    for queue_name in queues:
        await write_json_messages(conn, queue_name, 5)

    try:
        result = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        result = None
        logger.exception(f"Error reading messages from queues: {str(e)}")
        
    logger.info(f"Read messages {result} from queues")
    await conn.aclose()
    
def main():
    asyncio.run(queue_example())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
