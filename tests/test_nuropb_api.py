import os

from nuropb.nuropb_api import create_service, create_client, configure_mesh

import pytest


IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
if IN_GITHUB_ACTIONS:
    pytest.skip("Skipping model tests when run in Github Actions", allow_module_level=True)


@pytest.mark.asyncio
async def test_client_and_service_api_quick_setup(test_settings, rmq_settings):

    transport_settings = dict(
        dl_exchange=test_settings["dl_exchange"],
        prefetch_count=test_settings["prefetch_count"],
        default_ttl=test_settings["default_ttl"],
    )
    connection_properties = rmq_settings

    configure_mesh(
        mesh_name=connection_properties["vhost"],
        connection_properties=connection_properties,
        transport_settings=transport_settings,
    )

    service_api = create_service(
        name="test_service",
        connection_properties=connection_properties,
        transport_settings=transport_settings,
    )
    await service_api.connect()
    client_api = create_client(
        connection_properties={
            "vhost": connection_properties["vhost"],
            "port": rmq_settings["port"],
            "host": rmq_settings["host"],
        }
    )
    await client_api.connect()

    await client_api.disconnect()
    assert client_api.connected is False
    await service_api.disconnect()
    assert service_api.connected is False


@pytest.mark.asyncio
async def test_client_and_service_api_quick_setup_raw_defaults(rmq_settings):

    configure_mesh(
        connection_properties={
            "port": rmq_settings["port"],
            "host": rmq_settings["host"],
        }
    )
    service_api = create_service(
        name="test_service",
        connection_properties={
            "port": rmq_settings["port"],
            "host": rmq_settings["host"],
        }
    )
    await service_api.connect()
    client_api = create_client(connection_properties={
        "port": rmq_settings["port"],
        "host": rmq_settings["host"],
    })
    await client_api.connect()

    await client_api.disconnect()
    assert client_api.connected is False
    await service_api.disconnect()
    assert service_api.connected is False
