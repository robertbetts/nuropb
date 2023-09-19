import logging
from pprint import pformat

import pytest

from nuropb import rmq_transport

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_requires_user_token(test_mesh_client, test_mesh_service):

    await test_mesh_service.connect()
    assert test_mesh_service.connected is True
    logger.info("SERVICE API CONNECTED")

    await test_mesh_client.connect()
    assert test_mesh_client.connected is True
    logger.info("CLIENT CONNECTED")

    service = test_mesh_service.service_name
    method = "test_requires_user_claims"
    params = {"param1": "value1"}
    context = {"Authorization": "my_jwt_token"}
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await test_mesh_service.request(
        service=service,
        method=method,
        params=params,
        context=context,
        rpc_response=False,
    )
    logger.info(f"response: {pformat(rpc_response)}")

    await test_mesh_client.disconnect()
    await test_mesh_service.disconnect()

    assert rpc_response["error"] is None
    assert rpc_response["result"]["user_id"] == "test_user"
    assert rpc_response["result"]["scope"] == "openid, profile"
    assert rpc_response["result"]["roles"] == "user, admin"
    assert rpc_response["result"]["sub"] == "test_user"


@pytest.mark.asyncio
async def test_mesh_service_describe(test_mesh_client, test_mesh_service):
    """ Call the describe function for a service on the mesh. This should return a dictionary
    describing the service and its methods.
    """

    await test_mesh_service.connect()
    assert test_mesh_service.connected is True
    logger.info("SERVICE API CONNECTED")

    await test_mesh_client.connect()
    assert test_mesh_client.connected is True
    logger.info("CLIENT CONNECTED")

    service = test_mesh_service.service_name
    method = "nuropb_describe"
    params = {}
    context = {}
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await test_mesh_service.request(
        service=service,
        method=method,
        params=params,
        context=context,
        rpc_response=False,
    )
    logger.info(f"response: {pformat(rpc_response)}")


@pytest.mark.asyncio
async def test_mesh_service_describe(test_mesh_client, test_mesh_service):
    """ user the service mesh api helper function to call the describe function for a service on the mesh.
    Test that service metta information is cached in the mesh client.
    """

    await test_mesh_service.connect()
    assert test_mesh_service.connected is True
    logger.info("SERVICE API CONNECTED")

    await test_mesh_client.connect()
    assert test_mesh_client.connected is True
    logger.info("CLIENT CONNECTED")

    service_name = test_mesh_service.service_name
    logger.info(f"test_mesh_service.describe_service('{service_name}')")
    service_info = await test_mesh_client.describe_service(
        service_name=service_name,
    )
    logger.info(f"response: {pformat(service_info)}")
    assert isinstance(service_info, dict)

    service = test_mesh_service.service_name
    method = "test_requires_encryption"
    public_key = await test_mesh_client.requires_encryption(
        service_name=service,
        method_name=method
    )
    params = {}
    context = {}
    logger.info(f"Requesting {service}.{method}")
    rpc_response = await test_mesh_service.request(
        service=service,
        method=method,
        params=params,
        context=context,
        rpc_response=False,
    )
    logger.info(f"response: {pformat(rpc_response)}")


@pytest.mark.asyncio
async def test_mesh_service_encrypt(test_mesh_client, test_mesh_service):
    """ user the service mesh api helper function to call the describe function for a service on the mesh.
    Test that service metta information is cached in the mesh client.
    """

    await test_mesh_service.connect()
    await test_mesh_client.connect()
    rmq_transport.verbose = True

    service = "test_service"
    method = "test_requires_encryption"
    logger.info(f"Requesting encrypted transport for request {service}.{method}")

    encrypted = await test_mesh_client.requires_encryption(service, method)
    params = {}
    context = {
        "Authorization": "Bearer: user_token"
    }
    rpc_response = await test_mesh_service.request(
        service=service,
        method=method,
        params=params,
        context=context,
        rpc_response=False,
        encrypted=encrypted,
    )
    logger.info(f"response: {pformat(rpc_response)}")

