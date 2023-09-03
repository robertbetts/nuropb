import datetime
import logging
import asyncio
from uuid import uuid4

from nuropb.rmq_api import RMQAPI


logger = logging.getLogger("client")


async def make_request(api: RMQAPI):
    service = "sandbox_service"
    method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 30 * 1000
    trace_id = uuid4().hex
    response = await api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
    )
    return response == f"response from {service}.{method}"


async def make_command(api: RMQAPI):
    service = "sandbox_service"
    method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 30 * 1000
    trace_id = uuid4().hex
    api.command(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
    )


async def publish_event(api: RMQAPI):
    topic = "test-event"
    event = {"event_key": "event_value"}
    context = {"context1": "value1"}
    trace_id = uuid4().hex
    api.publish_event(
        topic=topic,
        event=event,
        context=context,
        trace_id=trace_id,
    )


async def main():
    amqp_url = "amqp://guest:guest@127.0.0.1:5672/sandbox"
    instance_id = uuid4().hex

    transport_settings = dict(
        prefetch_count=10,
        default_ttl=60 * 30 * 1000,  # 30 minutes
    )
    api = RMQAPI(
        instance_id=instance_id,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )
    await api.connect()

    total_seconds = 0
    total_sample_count = 0

    batch_size = 5000
    number_of_batches = 1
    ioloop = asyncio.get_event_loop()

    for _ in range(number_of_batches):
        start_time = datetime.datetime.utcnow()
        logger.info(f"Starting: {batch_size} at {start_time}")

        loop_batch_size = 0
        tasks = [ioloop.create_task(make_request(api)) for _ in range(batch_size)]
        logger.info("Waiting for request tasks to complete")
        result = await asyncio.wait(tasks)
        loop_batch_size += batch_size
        # logger.info(f"Request complete: {result[0]}")

        tasks = [ioloop.create_task(make_command(api)) for _ in range(batch_size)]
        logger.info("Waiting for command tasks to complete")
        await asyncio.wait(tasks)
        loop_batch_size += batch_size

        tasks = [ioloop.create_task(publish_event(api)) for _ in range(batch_size)]
        logger.info("Waiting for publish tasks to complete")
        await asyncio.wait(tasks)
        loop_batch_size += batch_size

        end_time = datetime.datetime.utcnow()
        time_taken = end_time - start_time
        logger.info(f"Completed: {batch_size} at {end_time} in {time_taken}")
        total_seconds += time_taken.total_seconds()
        total_sample_count += loop_batch_size

    logger.info(
        "Client Done: %s in %s -> %s",
        total_sample_count,
        total_seconds,
        total_sample_count / total_seconds,
    )
    fut = asyncio.Future()
    await fut


if __name__ == "__main__":
    log_format = (
        "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
        "-35s %(lineno) -5d: %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger("pika").setLevel(logging.WARNING)
    asyncio.run(main())
