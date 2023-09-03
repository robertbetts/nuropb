import pytest
from uuid import uuid4
import logging

from nuropb.rmq_api import RMQAPI

logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger()


@pytest.mark.asyncio
async def test_event_publish(test_settings, test_rmq_url_static, service_instance):
    test_rmq_url = test_rmq_url_static

    service_name = test_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=["test-event"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    service_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        service_instance=service_instance,
        amqp_url=test_rmq_url,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True
    logging.info(f"SERVICE API CONNECTED - {service_api.instance_id}")

    instance_id = uuid4().hex
    client_transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=[],
        event_bindings=[],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    client_api = RMQAPI(
        instance_id=instance_id,
        amqp_url=test_rmq_url,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=client_transport_settings,
    )
    await client_api.connect()
    assert client_api.connected is True
    logging.info(f"CLIENT CONNECTED - {client_api.instance_id}")
    topic = "test-event"
    event = {"event_key": "event_value"}
    context = {"context1": "value1"}
    trace_id = uuid4().hex
    logging.info(f"Publishing {topic}")
    client_api.publish_event(
        topic=topic,
        event=event,
        context=context,
        trace_id=trace_id,
    )
    await client_api.disconnect()
    assert client_api.connected is False
    await service_api.disconnect()
    assert service_api.connected is False
