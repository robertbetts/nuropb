import os

import pytest
from nuropb.rmq_transport import RMQTransport


@pytest.mark.asyncio
async def test_tls_connect():

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
        "vhost": "nuropb",
        "verify": False,
        "certfile": certfile,
        "keyfile": keyfile,
    }
    transport = RMQTransport(
        service_name="test-service",
        instance_id="test-service-instance",
        amqp_url=amqp_url,
        message_callback=message_callback,
    )
    await transport.start()
    assert transport.connected is True
    # await asyncio.Event().wait()
    await transport.stop()
    assert transport.connected is False




