import logging
import asyncio
from uuid import uuid4
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from nuropb.rmq_api import RMQAPI
from nuropb.service_runner import ServiceContainer
from service_example import ServiceExample

logger = logging.getLogger("server")


async def main():
    amqp_url = "amqp://guest:guest@127.0.0.1:5672/sandbox"
    api_url = "http://guest:guest@localhost:15672/api"
    service_name = "sandbox"
    instance_id = uuid4().hex

    """ load private_key and create one if it done not exist
    """
    primary_key_filename = "key.pem"
    private_key = None
    if os.path.exists(primary_key_filename):
        with open(primary_key_filename, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                data=key_file.read(),
                backend=default_backend(),
                password=None,
            )
    if private_key is None:
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        primary_key_data: bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        with open(primary_key_filename, "wt") as f:
            f.write(primary_key_data.decode("utf-8"))


    transport_settings = dict(
        rpc_bindings=[service_name],
        event_bindings=[],
        prefetch_count=1,
    )

    service_example = ServiceExample(
        service_name=service_name,
        instance_id=instance_id,
        private_key=private_key,
    )

    api = RMQAPI(
        service_instance=service_example,
        service_name=service_name,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )

    container = ServiceContainer(
        rmq_api_url=api_url,
        instance=api,
        # etcd_config=dict(
        #     host="localhost",
        #     port=2379,
        # ),
    )
    started = await container.start()
    if started:
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
