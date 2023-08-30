""" This is an example of when using asyncio of how to call an async function from a sync function

It is easy to get yourself in a mess when you mix sync and async functions. This example shows how to
call an async function from a sync function. The key is to use asyncio.get_event_loop() to get the
event loop and then use loop.create_task() to create a task from the async function. The task can then
be added to the event loop.

"""
import logging
import secrets
import asyncio
import time
import functools

logger = logging.getLogger(__name__)


async def async_function(instance_id: str):
    logger.info(f"Starting async_function {instance_id}")
    time.sleep(1)
    logger.info(f"Ending async_function {instance_id}")
    return instance_id


def async_function_done(instance_id: str, future):
    result = future.result()
    logger.info(f'task for async_function done: {result} {future.result()}')
    assert result == instance_id


def sync_function(instance_id: str):
    logger.info(f"Starting sync_function {instance_id}")
    ioloop = asyncio.get_event_loop()
    async_function_id = secrets.token_hex(8)
    done_callback = functools.partial(async_function_done, async_function_id)
    task = ioloop.create_task(async_function(async_function_id))
    task.add_done_callback(done_callback)
    time.sleep(5)
    logger.info(f"Ending sync_function {instance_id}")
    return instance_id


async def main(instance_id: str):
    logger.info(f"Starting main {instance_id}")
    sync_function_id = secrets.token_hex(8)
    result = sync_function(sync_function_id)
    assert result == sync_function_id
    await asyncio.sleep(1)
    logger.info(f"Ending main {instance_id}")
    return instance_id


def main_done(future):
    logger.info(f'task done: {future.done()} {future.result()}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d: %(message)s")
    my_id = secrets.token_hex(8)
    ioloop = asyncio.get_event_loop()
    task = ioloop.create_task(main(my_id))
    task.add_done_callback(main_done)
    ioloop.run_forever()
