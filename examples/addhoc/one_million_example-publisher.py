import logging
import asyncio
import time

from nuropb.rmq_api import RMQAPI

logger = logging.getLogger("one_million_example")


async def main():
    logger.info("one million example starting")
    amqp_url = "amqp://guest:guest@localhost:5672/nuropb-example"
    client_api = RMQAPI(
        amqp_url=amqp_url,
    )
    await client_api.connect()
    logger.info("Client connected")

    async def make_command(client_api: RMQAPI):
        client_api.command(
            service="one-million-example",
            method="test_method",
            params={
                "param1": "value1",
                "param2": {
                    "param2a": "value2a",
                }
            },
            context={},
        )

    total_request_time = 0
    batch_size = 100000
    number_of_batches = 10
    for i in range(number_of_batches):
        rr_start_time = time.time()
        tasks = [asyncio.create_task(make_command(client_api)) for _ in range(batch_size)]
        _ = await asyncio.wait(tasks)
        rr_taken = time.time() - rr_start_time
        total_request_time += rr_taken
        logger.info("batch %s of %s calls took %s seconds and %s calls/s", i, batch_size, rr_taken, batch_size / rr_taken)

    total_rr_count = batch_size * number_of_batches
    logger.info(
        "Request only performance: %s total calls in %s seconds @ %s calls/s",
        total_rr_count, total_request_time, total_rr_count / total_request_time
    )
    await client_api.disconnect()
    await asyncio.sleep(1)
    logger.info("All in one example done")


if __name__ == "__main__":
    log_format = (
        "%(levelname).1s %(asctime)s %(name) -25s %(funcName) "
        "-35s %(lineno) -5d: %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("nuropb").setLevel(logging.WARNING)
    asyncio.run(main())
