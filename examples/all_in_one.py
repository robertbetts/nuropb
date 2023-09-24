import logging
from typing import Any, Dict
from uuid import uuid4
import asyncio

from nuropb.contexts.context_manager import NuropbContextManager
from nuropb.contexts.context_manager_decorator import nuropb_context
from nuropb.contexts.describe import publish_to_mesh
from nuropb.rmq_api import RMQAPI

logger = logging.getLogger("nuropb-server-basic")


def get_claims_from_token(bearer_token: str) -> Dict[str, Any] | None:
    """ This is a stub for the required implentation of validating and decoding the bearer token
    """
    _ = bearer_token
    return {
        "sub": "test_user",
        "user_id": "test_user",
        "scope": "openid, profile",
        "roles": "user, admin",
    }


class QuickExampleService:
    _service_name = "quick-example"
    _instance_id = uuid4().hex

    @nuropb_context
    @publish_to_mesh(authorise_func=get_claims_from_token)
    def test_requires_user_claims(self, ctx, **kwargs: Any) -> str:
        logger.info("test_requires_user_claims called")
        assert isinstance(ctx, NuropbContextManager)
        return f"hello {ctx.user_claims['user_id']}"

    def test_method(self, param1, param2: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("test_method called")
        _ = self
        return {
            "param1": param1,
            "param2": param2,
            "reply": "response from test_method",
        }


async def main():
    logging.info("All in one example done")
    amqp_url = "amqp://guest:guest@localhost:5672/nuropb-example"
    service_instance = QuickExampleService()
    transport_settings = {
        "rpc_bindings": [service_instance._service_name],
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

    client_api = RMQAPI(
        amqp_url=amqp_url,
    )
    await client_api.connect()
    logger.info("Client connected")

    context = {
        "Authorization": "Bearer 1234567890",
    }
    response = await client_api.request(
        service="quick-example",
        method="test_requires_user_claims",
        params={},
        context=context,
    )
    logger.info(f"Response: {response}")

    response = await client_api.request(
        service="quick-example",
        method="test_method",
        params={
            "param1": "value1",
            "param2": {
                "param2a": "value2a",
            }
        },
        context={},
    )
    logger.info(f"Response: {response}")

    await client_api.disconnect()
    await service_api.disconnect()

    logging.info("All in one example done")


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
