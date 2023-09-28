import asyncio
import logging
from uuid import uuid4

import pytest

from nuropb.rmq_api import RMQAPI

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_call_self(test_settings, rmq_settings, service_instance):
    """ Currently this test passes, as there is no check for the service name in the request method.
    Restricting the service name to be different from the service name of the service instance is
    under consideration for a future release.
    """
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    service_api = RMQAPI(
        service_name=service_instance.service_name,
        instance_id=service_instance.instance_id,
        service_instance=service_instance,
        amqp_url=rmq_settings,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True
    logger.info("SERVICE API CONNECTED")

    service = "test_service"
    method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 5 * 1000
    trace_id = uuid4().hex
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await service_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
        rpc_response=False,
    )
    logger.info(f"response: {rpc_response}")
    assert rpc_response["result"] == f"response from {service}.{method}"

    await service_api.disconnect()
    assert service_api.connected is False


@pytest.mark.asyncio
async def test_subscribe_to_events_from_self(test_settings, rmq_settings, service_instance):
    """ Currently this test passes, as there is no check to restrict binding to the service queue
    for events that originate from the service.
    This restriction is under consideration for a future release.
    """
    test_topic = f"{service_instance.service_name}.test-event"
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=[test_topic],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    test_future = asyncio.Future()

    def handle_event(topic, event, target, context):
        logger.info(f"Received event {topic} {target} {event} {context}")
        assert topic == test_topic
        test_future.set_result(True)

    setattr(service_instance, "_handle_event_", handle_event)

    service_api = RMQAPI(
        service_name=service_instance.service_name,
        instance_id=service_instance.instance_id,
        service_instance=service_instance,
        amqp_url=rmq_settings,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
    )
    await service_api.connect()
    assert service_api.connected is True
    logger.info("SERVICE API CONNECTED")

    service_api.publish_event(test_topic, {"test": "event"}, {})

    await test_future

    await service_api.disconnect()
    assert service_api.connected is False
