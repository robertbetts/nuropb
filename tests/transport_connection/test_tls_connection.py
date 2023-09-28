import os
from uuid import uuid4

import pytest

from nuropb.rmq_api import RMQAPI
from nuropb.rmq_transport import RMQTransport
from nuropb.testing.stubs import ServiceStub

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
if IN_GITHUB_ACTIONS:
    pytest.skip("Skipping model tests when run in Github Actions", allow_module_level=True)


@pytest.mark.asyncio
async def test_tls_connect(rmq_settings, test_settings):

    def message_callback(message):
        print(message)

    cacertfile = os.path.join(os.path.dirname(__file__), "ca_cert.pem")
    certfile = os.path.join(os.path.dirname(__file__), "cert-2.pem")
    keyfile = os.path.join(os.path.dirname(__file__), "key-2.pem")

    amqp_url = {
        "cafile": cacertfile,
        "host": "localhost",
        "username": "guest",
        "password": "guest",
        "port": 5671,
        "vhost": rmq_settings["vhost"],
        "verify": False,
        "certfile": certfile,
        "keyfile": keyfile,
    }
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
    )
    transport1 = RMQTransport(
        service_name="test-service",
        instance_id=uuid4().hex,
        amqp_url=amqp_url,
        message_callback=message_callback,
        **transport_settings,
    )
    await transport1.start()
    assert transport1.connected is True

    service = ServiceStub(
        service_name="test-service",
        instance_id=uuid4().hex,
    )
    api = RMQAPI(
        service_name=service.service_name,
        instance_id=service.instance_id,
        service_instance=service,
        amqp_url=amqp_url,
        transport_settings=transport_settings
    )
    await api.connect()
    assert api.connected is True

    await transport1.stop()
    assert transport1.connected is False
    await api.disconnect()
    assert api.connected is False



