import logging
from pprint import pformat

import pytest

from nuropb import rmq_transport

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_requires_user_token(mesh_client, mesh_service):
    await mesh_service.connect()
    assert mesh_service.connected is True
    logger.info("SERVICE API CONNECTED")

    await mesh_client.connect()
    assert mesh_client.connected is True
    logger.info("CLIENT CONNECTED")

    service = mesh_service.service_name
    method = "test_requires_user_claims"
    params = {"param1": "value1"}
    context = {"Authorization": "my_jwt_token"}
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await mesh_service.request(
        service=service,
        method=method,
        params=params,
        context=context,
        rpc_response=False,
    )
    logger.info(f"response: {pformat(rpc_response)}")

    await mesh_client.disconnect()
    await mesh_service.disconnect()

    assert rpc_response["error"] is None
    assert rpc_response["result"]["user_id"] == "test_user"
    assert rpc_response["result"]["scope"] == "openid, profile"
    assert rpc_response["result"]["roles"] == "user, admin"
    assert rpc_response["result"]["sub"] == "test_user"


@pytest.mark.asyncio
async def mesh_service_describe(mesh_client, mesh_service):
    """Call the describe function for a service on the mesh. This should return a dictionary
    describing the service and its methods.
    """

    await mesh_service.connect()
    assert mesh_service.connected is True
    logger.info("SERVICE API CONNECTED")

    await mesh_client.connect()
    assert mesh_client.connected is True
    logger.info("CLIENT CONNECTED")

    service = mesh_service.service_name
    method = "nuropb_describe"
    params = {}
    context = {}
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await mesh_service.request(
        service=service,
        method=method,
        params=params,
        context=context,
        rpc_response=False,
    )
    logger.info(f"response: {pformat(rpc_response)}")


@pytest.mark.asyncio
async def mesh_service_describe(mesh_client, mesh_service):
    """user the service mesh api helper function to call the describe function for a service on the mesh.
    Test that service metta information is cached in the mesh client.
    """

    await mesh_service.connect()
    assert mesh_service.connected is True
    logger.info("SERVICE API CONNECTED")

    await mesh_client.connect()
    assert mesh_client.connected is True
    logger.info("CLIENT CONNECTED")

    service_name = mesh_service.service_name
    logger.info(f"mesh_service.describe_service('{service_name}')")
    service_info = await mesh_client.describe_service(
        service_name=service_name,
    )
    logger.info(f"response: {pformat(service_info)}")
    assert isinstance(service_info, dict)

    service = mesh_service.service_name
    method = "test_requires_encryption"
    public_key = await mesh_client.requires_encryption(
        service_name=service, method_name=method
    )
    params = {}
    context = {}
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await mesh_service.request(
        service=service,
        method=method,
        params=params,
        context=context,
        rpc_response=False,
    )
    logger.info(f"response: {pformat(rpc_response)}")


@pytest.mark.asyncio(async_timeout=10)
async def mesh_service_encrypt(mesh_client, mesh_service):
    """user the service mesh api helper function to call the describe function for a service on the mesh.
    Test that service metta information is cached in the mesh client.
    """

    await mesh_service.connect()
    await mesh_client.connect()
    rmq_transport.verbose = True

    service = "test_service"
    method = "test_requires_encryption"
    logger.info(f"Requesting encrypted transport for request {service}.{method}")

    encrypted = await mesh_client.requires_encryption(service, method)
    assert encrypted is True
    params = {}
    context = {"Authorization": "Bearer: user_token"}
    rpc_response = await mesh_service.request(
        service=service,
        method=method,
        params=params,
        context=context,
        rpc_response=False,
        encrypted=encrypted,
    )
    logger.info(f"response: {pformat(rpc_response)}")
