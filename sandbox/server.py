import logging
import asyncio
from uuid import uuid4

from nuropb.rmq_api import RMQAPI
from nuropb.rmq_transport import configure_rmq

logger = logging.getLogger()


async def main(ioloop: asyncio.AbstractEventLoop):
    amqp_url = "amqp://guest:guest@127.0.0.1:5672/sandbox"
    service_name = "sandbox_service"
    instance_id = uuid4().hex

    api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=amqp_url,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        dl_exchange="test_dl_exchange",
        rpc_bindings=[service_name],
        event_bindings=[],
        prefetch_count=10,
        default_ttl=60*30*1000,  # 30 minutes
    )
    configured = configure_rmq(
        rmq_url=amqp_url,
        rpc_exchange=api._transport.rpc_exchange,
        events_exchange=api._transport.events_exchange,
        dl_exchange=api._transport._dl_exchange,
        dl_queue=api._transport._dl_queue,
        request_queue=api._transport._request_queue,
        response_queue=api._transport.response_queue,
        rpc_bindings=[service_name],
        event_bindings=[],
    )
    await api.connect()
    fut = asyncio.Future()
    await fut
    logging.info("Server Done")


if __name__ == '__main__':
    log_format = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
                  '-35s %(lineno) -5d: %(message)s')
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger('pika').setLevel(logging.INFO)

    loop = asyncio.get_event_loop()
    loop.create_task(main(loop))
    loop.run_forever()

