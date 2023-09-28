import logging
from typing import Any, Dict
from uuid import uuid4
import asyncio

from nuropb.rmq_api import RMQAPI

logger = logging.getLogger("nuropb-server-basic")


class BasicExampleService:
    _service_name = "basic-example"
    _instance_id = uuid4().hex

    async def test_async_method(self, **params: Any) -> str:
        logger.info("test_async_method called")
        _ = self
        asyncio.sleep(0.1)
        return "response from test_method"

    def test_method(self, param1, param2: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("test_method called")
        _ = self
        return {
            "param1": param1,
            "param2": param2,
            "reply": "response from test_method",
        }


async def main():
    amqp_url = "amqp://guest:guest@localhost:5672/nuropb-example"
    service_instance = BasicExampleService()
    transport_settings = {
        "rpc_bindings": [service_instance._service_name],
    }
    mesh_api = RMQAPI(
        service_instance=service_instance,
        service_name=service_instance._service_name,
        instance_id=service_instance._instance_id,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )
    await mesh_api.connect()
    try:
        logging.info("Service %s ready", service_instance._service_name)
        await asyncio.Event().wait()
        logging.info("Shutting down signal received")
        await mesh_api.disconnect()
    except BaseException as err:
        logging.info("Shutting down. %s: %s", type(err).__name__, err)
        await mesh_api.disconnect()
    finally:
        logging.info("Service %s done", service_instance._service_name)

    logging.info("Service %s done", service_instance._service_name)


if __name__ == "__main__":
    log_format = (
        "%(levelname).1s %(asctime)s %(name) -25s %(funcName) "
        "-35s %(lineno) -5d: %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("etcd3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
