import logging
import asyncio
from uuid import uuid4

from nuropb.rmq_api import RMQAPI
from nuropb.rmq_lib import configure_nuropb_rmq, create_virtual_host

logger = logging.getLogger(__name__)

"""
This script is used to setup the RabbitMQ exchanges, queues, and bindings for the 
NuroPb examples. A running RabbitMQ instance with the management plugin is required.

The default login credentials are assumed. If you have changed the default login credentials
for RabbitMQ, you will need to update the amqp_url and rmq_api_url variables below.
"""
amqp_url = "amqp://guest:guest@localhost:5672/nuropb-example"
rmq_api_url = "http://guest:guest@localhost:15672/api"


class MeshServiceInstance:
    """ Helper service instance class used purely for the virtual host and exchanges configured in RabbitMQ.
    The service queue and dead letter created for this instance during the setup can be deleted.
    """
    _service_name = "mesh-setup"
    _instance_id = uuid4().hex


async def main():
    service_instance = MeshServiceInstance()
    api = RMQAPI(
        amqp_url=amqp_url,
        service_name=service_instance._service_name,  # pragma: no cover
        instance_id=service_instance._instance_id,  # pragma: no cover
        service_instance=service_instance,
    )
    create_virtual_host(rmq_api_url, amqp_url)
    transport_settings = api.transport.rmq_configuration
    configure_nuropb_rmq(
        service_name=service_instance._service_name,  # pragma: no cover
        rmq_url=amqp_url,
        events_exchange=transport_settings["events_exchange"],
        rpc_exchange=transport_settings["rpc_exchange"],
        dl_exchange=transport_settings["dl_exchange"],
        dl_queue=transport_settings["dl_queue"],
        service_queue=transport_settings["service_queue"],
        rpc_bindings=transport_settings["rpc_bindings"],
        event_bindings=transport_settings["event_bindings"],
    )


if __name__ == "__main__":
    log_format = (
        "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
        "-35s %(lineno) -5d: %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("nuropb").setLevel(logging.INFO)
    asyncio.run(main())
