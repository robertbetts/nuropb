import datetime
import logging
import asyncio
from uuid import uuid4

from nuropb.rmq_api import RMQAPI

logger = logging.getLogger()


async def make_request(api: RMQAPI):
    service = "sandbox_service"
    method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60*30*1000
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


async def main(ioloop: asyncio.AbstractEventLoop):
    amqp_url = "amqp://guest:guest@127.0.0.1:5672/sandbox"
    service_name = "sandbox_client"
    instance_id = uuid4().hex

    transport_settings = dict(
        rpc_bindings=[],
        event_bindings=[],
        prefetch_count=10,
        default_ttl=60*30*1000,  # 30 minutes
    )
    api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
        client_only=True,
    )
    await api.connect()
    total_seconds = 0
    total_sample_count = 0

    batch_size = 10000
    number_of_batches = 1

    for _ in range(number_of_batches):
        start_time = datetime.datetime.utcnow()
        logging.info(f"Starting: {batch_size} at {start_time}")

        tasks = [ioloop.create_task(make_request(api)) for _ in range(batch_size)]

        logging.info("Waiting for tasks to complete")
        await asyncio.wait(tasks)

        end_time = datetime.datetime.utcnow()
        time_taken = end_time - start_time
        logging.info(f"Completed: {batch_size} at {end_time} in {time_taken}")
        total_seconds += time_taken.total_seconds()
        total_sample_count += batch_size

    logging.info("Client Done: %s in %s -> %s", total_sample_count, total_seconds,  total_sample_count/total_seconds)
    fut = asyncio.Future()
    await fut


if __name__ == '__main__':
    log_format = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
                  '-35s %(lineno) -5d: %(message)s')
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger('pika').setLevel(logging.WARNING)

    loop = asyncio.get_event_loop()
    loop.create_task(main(loop))
    loop.run_forever()

