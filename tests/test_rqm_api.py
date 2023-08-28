import pytest
from uuid import uuid4
import secrets
import logging
from nuropb.rmq_api import RMQAPI
from nuropb.rmq_lib import create_virtual_host, delete_virtual_host
from nuropb.rmq_transport import ServiceNotConfigured

logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger()


def test_rmq_preparation(test_settings, test_rmq_url, test_api_url):
    """ Test that the RMQ instance is and can be correctly configured
    - create virtual host should be idempotent
    - delete virtual host should be idempotent
    """
    tmp_url = f"{test_rmq_url}-{secrets.token_hex(8)}"
    create_virtual_host(test_api_url, tmp_url)
    create_virtual_host(test_api_url, tmp_url)
    delete_virtual_host(test_api_url, tmp_url)
    delete_virtual_host(test_api_url, tmp_url)


@pytest.mark.asyncio
async def test_rmq_api_client_mode(test_settings, test_rmq_url):
    """ Test client mode. this is a client only instance of RMQAPI and only established a connection
    to the RMQ server. It registers a response queue that is automatically associated with the default
    exchange, requires that RMQ is sufficiently setup.
    """
    service_name = "test_client"
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=[],
        event_bindings=[],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    rmq_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=test_rmq_url,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
        client_only=True,
    )
    await rmq_api.connect()
    assert rmq_api.connected is True
    await rmq_api.disconnect()
    assert rmq_api.connected is False


@pytest.mark.asyncio
async def test_rmq_api_client_mode_unconfigured_rmq(test_settings, unconfigured_rmq_url):
    """ Test client mode. Test the client behaviour when the RMQ server is not configured.

        Expected behaviour:
            - RMQAPI.connect() should not raise an exception and behave as if it was connected
            - RMQAPI.disconnect() should not raise an exception and behave as if it was disconnected
            - RMQAPI.request() should raise an exception
            - RMQAPI.command() should raise an exception
            - RMQAPI.publish_event() should raise an exception
    """
    logger.info("testing against RMQ server: %s", unconfigured_rmq_url)
    service_name = "test_client"
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=[],
        event_bindings=[],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    rmq_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=unconfigured_rmq_url,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
        client_only=True,
    )

    with pytest.raises(ServiceNotConfigured):
        await rmq_api.connect()
        assert rmq_api.connected is False

    await rmq_api.disconnect()
    assert rmq_api.connected is False


@pytest.mark.asyncio
async def test_rmq_api_service_mode(test_settings, test_rmq_url):
    service_name = test_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    rmq_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=test_rmq_url,
        rpc_exchange=test_settings["rpc_exchange"],
        events_exchange=test_settings["events_exchange"],
        transport_settings=transport_settings,
        client_only=True,
    )
    await rmq_api.connect()
    assert rmq_api.connected is True
    await rmq_api.disconnect()
    assert rmq_api.connected is False


@pytest.mark.asyncio
async def test_request_response(test_settings, test_rmq_url):
    service_name = test_settings["service_name"]
    instance_id = uuid4().hex
    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=test_settings["rpc_bindings"],
        event_bindings=test_settings["event_bindings"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    service_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=test_rmq_url,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=transport_settings,
    )
    assert service_api.connected is False
    await service_api.connect()
    assert service_api.connected is True

    service_name = "test_client"
    instance_id = uuid4().hex
    client_transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        rpc_bindings=[],
        event_bindings=[],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    client_api = RMQAPI(
        service_name=service_name,
        instance_id=instance_id,
        amqp_url=test_rmq_url,
        rpc_exchange="test_rpc_exchange",
        events_exchange="test_events_exchange",
        transport_settings=client_transport_settings,
        client_only=True,
    )
    await client_api.connect()
    assert client_api.connected is True
    service = "test_service"
    method = "test_method"
    params = {"param1": "value1"}
    context = {"context1": "value1"}
    ttl = 60 * 30 * 1000
    trace_id = uuid4().hex
    logging.info(f"Requesting {service}.{method}")
    response = await client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
    )
    logging.info(f"response: {response}")
    assert response == f"response from {service}.{method}"
    rpc_response = await client_api.request(
        service=service,
        method=method,
        params=params,
        context=context,
        ttl=ttl,
        trace_id=trace_id,
        rpc_response=False,
    )
    logging.info(f"response: {rpc_response}")
    assert rpc_response["result"] == f"response from {service}.{method}"
    await client_api.disconnect()
    assert client_api.connected is False
