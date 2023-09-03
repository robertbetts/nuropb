import logging
import asyncio
from uuid import uuid4

from nuropb.rmq_api import RMQAPI
from nuropb.service_runner import ServiceContainer
from service_example import ServiceExample

logger = logging.getLogger("server")


async def main():
    amqp_url = "amqp://guest:guest@127.0.0.1:5672/sandbox"
    api_url = "http://guest:guest@localhost:15672/api"
    service_name = "sandbox_service"
    instance_id = uuid4().hex

    transport_settings = dict(
        rpc_bindings=[service_name],
        event_bindings=["test-event"],
        prefetch_count=10,
        default_ttl=60 * 30 * 1000,  # 30 minutes
    )

    service_example = ServiceExample(
        service_name=service_name,
        instance_id=instance_id,
    )

    api = RMQAPI(
        service_instance=service_example,
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )

    container = ServiceContainer(
        rmq_api_url=api_url,
        instance=api,
        etcd_config=dict(
            host="localhost",
            port=2379,
        ),
    )
    await container.start()

    fut = asyncio.Future()
    await fut
    logging.info("Server Done")


if __name__ == "__main__":
    log_format = (
        "%(levelname).1s %(asctime)s %(name) -25s %(funcName) "
        "-35s %(lineno) -5d: %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("etcd3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    asyncio.run(main())
