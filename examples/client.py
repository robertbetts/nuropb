import datetime
import logging
import asyncio
from uuid import uuid4

from nuropb.rmq_api import RMQAPI


logger = logging.getLogger("nuropb-client")


async def perform_request(api: RMQAPI, encryption_test: bool = False):
    service = "test_service"
    if encryption_test:
        method = "test_encrypt_method"
    else:
        method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 30 * 1000
    trace_id = uuid4().hex

    """ Some service methods can be declared as requiring encryption always. When a service provides 
    a public key with its service description, then all methods are have optional encryption. The 
    example here, does a check whether the method requires encryption or not.
    """
    encrypted = await api.requires_encryption(service, method)

    response = await api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
        encrypted=encrypted,
    )
    return response == f"response from {service}.{method}"


async def perform_command(api: RMQAPI):
    service = "test_service"
    method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 30 * 1000
    trace_id = uuid4().hex
    encrypted = await api.requires_encryption(service, method)
    api.command(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
        encrypted=encrypted,
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
    amqp_url = "amqp://guest:guest@localhost:5672/nuropb-example"
    api = RMQAPI(
        amqp_url=amqp_url,
    )
    await api.connect()

    """ This first service mesh call, is to describe the service api and to determine whether
    the service has encrypted methods.
    """
    service = "test_service"
    describe_info = await api.describe_service(service)
    encrypted_methods = describe_info["encrypted_methods"]
    has_public_key = await api.has_public_key(service)
    logger.info(f"service {service} has encrypted methods requiring encryption: {encrypted_methods}")
    logger.info(f"service {service} supports general encryption: {has_public_key}")

    encryption_test = False
    logger.info(f"performing encrypted requests: {encryption_test}")

    """ Perform a number of service mesh calls, commands and events
    Each of the three blocks below in each iteration of the loop, the individual tasks are 
    performed asynchronously
    """
    total_seconds = 0
    total_sample_count = 0
    total_request_time = 0

    batch_size = 5000
    number_of_batches = 5
    ioloop = asyncio.get_event_loop()

    for _ in range(number_of_batches):
        start_time = datetime.datetime.utcnow()
        logger.info(f"Starting: {batch_size} at {start_time}")

        loop_batch_size = 0
        logger.info("Waiting for %s requests to complete", batch_size)
        rr_start_time = datetime.datetime.utcnow()
        tasks = [ioloop.create_task(perform_request(api, encryption_test)) for _ in range(batch_size)]
        result = await asyncio.wait(tasks)
        rr_taken = (datetime.datetime.utcnow() - rr_start_time).total_seconds()
        total_request_time += rr_taken
        logger.info("the request batch of %s calls took %s seconds and %s calls/s", batch_size, rr_taken, batch_size / rr_taken)
        # logger.info(f"Request complete: {result[0]}")
        loop_batch_size += batch_size

        logger.info("Waiting for %s commands to execute", batch_size)
        tasks = [ioloop.create_task(perform_command(api)) for _ in range(batch_size)]
        await asyncio.wait(tasks)
        loop_batch_size += batch_size

        logger.info("Waiting for %s events to publish")
        tasks = [ioloop.create_task(publish_event(api)) for _ in range(batch_size)]
        await asyncio.wait(tasks)
        loop_batch_size += batch_size

        end_time = datetime.datetime.utcnow()
        time_taken = end_time - start_time
        logger.info(f"Completed {batch_size * 3} calls to the service mesh in {time_taken}")
        total_seconds += time_taken.total_seconds()
        total_sample_count += loop_batch_size

    logger.info(
        "Client mixed performance: %s total calls in %s seconds @ %s calls/s",
        total_sample_count,
        total_seconds,
        total_sample_count / total_seconds,
    )
    total_rr_count = batch_size * number_of_batches
    logger.info(
        "Request only performance: %s total calls in %s seconds @ %s calls/s",
        total_rr_count, total_request_time, total_rr_count / total_request_time
    )
    logging.info("Client Done")


if __name__ == "__main__":
    log_format = (
        "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
        "-35s %(lineno) -5d: %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger("pika").setLevel(logging.CRITICAL)
    logging.getLogger("nuropb").setLevel(logging.WARNING)
    asyncio.run(main())
