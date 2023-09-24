import logging
from typing import Any, Dict
from uuid import uuid4
import asyncio

from nuropb.rmq_api import RMQAPI

logger = logging.getLogger("one_million_example")


class QuickExampleService:
    _service_name = "one-million-example"
    _instance_id = uuid4().hex

    def test_method(self, param1, param2: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("test_method called")
        _ = self
        return {
            "reply_field": "response from test_method",
        }

async def main():
    logger.info("one million example starting")
    amqp_url = "amqp://guest:guest@localhost:5672/nuropb-example"

    service_instance = QuickExampleService()
    transport_settings = {
        "rpc_bindings": [service_instance._service_name],
        "prefetch_count": 1,
    }
    service_api = RMQAPI(
        service_instance=service_instance,
        service_name=service_instance._service_name,
        instance_id=service_instance._instance_id,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )
    await service_api.connect()
    logger.info("Service Ready")
    await asyncio.Event().wait()
    await service_api.disconnect()
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
