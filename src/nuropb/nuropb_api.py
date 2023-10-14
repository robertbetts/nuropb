"""
Factory functions for instantiating nuropb api's.
"""
import logging
from typing import Optional, Dict, Any, Callable
from uuid import uuid4

from nuropb.rmq_api import RMQAPI
from nuropb.rmq_lib import (
    configure_nuropb_rmq,
    create_virtual_host,
    build_amqp_url,
    build_rmq_api_url,
    rmq_api_url_from_amqp_url,
)

logger = logging.getLogger(__name__)


def default_connection_properties(
    connection_properties: Dict[str, Any]
) -> Dict[str, Any]:
    if "host" not in connection_properties:
        connection_properties["host"] = "localhost"
    if "username" not in connection_properties:
        connection_properties["username"] = "guest"
    if "password" not in connection_properties:
        connection_properties["password"] = "guest"
    if "vhost" not in connection_properties:
        connection_properties["vhost"] = "nuropb"
    if "verify" not in connection_properties:
        connection_properties["verify"] = False
    if "ssl" not in connection_properties:
        connection_properties["ssl"] = False
    if "port" not in connection_properties and connection_properties["ssl"]:
        connection_properties["port"] = 5671
    elif "port" not in connection_properties:
        connection_properties["port"] = 5672

    return connection_properties


def create_client(
    name: Optional[str] = None,
    instance_id: Optional[str] = None,
    connection_properties: Optional[Dict[str, Any]] = None,
    transport_settings: Optional[str | Dict[str, Any]] = None,
    transport: Optional[RMQAPI] = RMQAPI,
) -> RMQAPI:
    """Create a client api instance for the nuropb service mesh. This caller of this function
    will have to implement the asyncio call to connect to the service mesh:
        await client_api.connect()

    :param name: used to identify the api connection to the service mesh
    :param instance_id: used to create the service mesh response queue for this api connection
    :param connection_properties: str or dict with values as required for the chosen transport api client
    :param transport_settings: dict with values as required for the underlying transport api
    :param transport: the class of the transport api client to use
    :return:
    """

    if connection_properties is None:
        connection_properties = default_connection_properties(
            {
                "vhost": "nuropb",
                "ssl": False,
                "verify": False,
            }
        )
    elif isinstance(connection_properties, dict):
        connection_properties = default_connection_properties(connection_properties)

    if transport is None:
        transport = RMQAPI
    if transport_settings is None:
        transport_settings = {}

    client_api: RMQAPI = transport(
        amqp_url=connection_properties,
        service_name=name,
        instance_id=instance_id,
        transport_settings=transport_settings,
    )
    return client_api


async def connect(instance_id: Optional[str] = None):
    client_api = create_client(
        instance_id=instance_id,
    )
    await client_api.connect()
    return client_api


def configure_mesh(
    mesh_name: Optional[str] = None,
    connection_properties: Optional[Dict[str, Any]] = None,
    transport_settings: Optional[str | Dict[str, Any]] = None,
):
    if mesh_name is None:
        mesh_name = "nuropb"

    if connection_properties is None:
        connection_properties = default_connection_properties(
            {
                "vhost": mesh_name,
                "ssl": False,
                "verify": False,
            }
        )

    if isinstance(connection_properties, str):
        amqp_url = connection_properties

    elif isinstance(connection_properties, dict):
        connection_properties = default_connection_properties(connection_properties)

        if connection_properties["ssl"]:
            rmq_scheme = "amqps"
        else:
            rmq_scheme = "amqp"

        host = connection_properties["host"]
        port = connection_properties["port"]
        username = connection_properties["username"]
        password = connection_properties["password"]
        vhost = connection_properties["vhost"]

        amqp_url = build_amqp_url(host, port, username, password, vhost, rmq_scheme)
    else:
        raise ValueError("connection_properties must be a str or dict")

    rmq_api_url = rmq_api_url_from_amqp_url(amqp_url)
    create_virtual_host(
        api_url=rmq_api_url,
        vhost_url=amqp_url,
    )

    if transport_settings is None:
        transport_settings = {}
    if "rpc_exchange" not in transport_settings:
        transport_settings["rpc_exchange"] = "nuropb-rpc-exchange"
    if "events_exchange" not in transport_settings:
        transport_settings["events_exchange"] = "nuropb-events-exchange"
    if "dl_exchange" not in transport_settings:
        transport_settings["dl_exchange"] = "nuropb-dl-exchange"
    if "dl_queue" not in transport_settings:
        transport_settings["dl_queue"] = "nuropb-dl-queue"

    configure_nuropb_rmq(
        rmq_url=connection_properties,
        events_exchange=transport_settings["events_exchange"],
        rpc_exchange=transport_settings["rpc_exchange"],
        dl_exchange=transport_settings["dl_exchange"],
        dl_queue=transport_settings["dl_queue"],
    )


class MeshService:
    """A generic service class that can be used to create a connection only service instance for the
    nuropb service mesh. This class could also be used as a template or to define a subclass for
    creating a service instance.
    """

    _service_name: str
    _instance_id: str
    _event_bindings: list[str]
    _event_callback: Optional[Callable]

    def __init__(
        self,
        service_name: str,
        instance_id: Optional[str] = None,
        event_bindings: Optional[list[str]] = None,
        event_callback: Optional[Callable] = None,
    ):
        self._service_name = service_name
        self._instance_id = instance_id or uuid4().hex
        self._event_bindings = event_bindings or []
        self._event_callback = event_callback

    async def _handle_event_(
        self,
        topic: str,
        event: dict,
        target: list[str] | None = None,
        context: dict | None = None,
        trace_id: str | None = None,
    ):
        _ = self
        if self._event_callback is not None:
            await self._event_callback(topic, event, target, context, trace_id)


def create_service(
    name: str,
    instance_id: Optional[str] = None,
    service_instance: Optional[object] = None,
    connection_properties: Optional[Dict[str, Any]] = None,
    transport_settings: Optional[str | Dict[str, Any]] = None,
    transport: Optional[RMQAPI] = RMQAPI,
    event_bindings: Optional[list[str]] = None,
    event_callback: Optional[Callable] = None,
) -> RMQAPI:
    """Create a client api instance for the nuropb service mesh. This caller of this function
    will have to implement the asyncio call to connect to the service mesh:
        await client_api.connect()

    :param name: used to identify this service to the service mesh
    :param instance_id: used to create the service mesh response queue for this individual api
        connection
    :param service_instance: the instance of the service class that is intended to be exposed
        to the service mesh
    :param connection_properties: str or dict with values as required for the chosen transport
        api client
    :param transport_settings: dict with values as required for the underlying transport api
    :param transport: the class of the transport api client to use
    :param event_bindings: when service_instance is None, a list of event topics that this
        service will subscribe to.
        when service_instance is not None, the list will override the event_bindings of the
        transport_settings if any are defined.
    :param event_callback: when service_instance is None, a callback function that will be
        called when an event is received
    :return:
    """

    if connection_properties is None:
        connection_properties = default_connection_properties(
            {
                "vhost": "nuropb",
                "ssl": False,
                "verify": False,
            }
        )
    elif isinstance(connection_properties, dict):
        connection_properties = default_connection_properties(connection_properties)

    if transport is None:
        transport = RMQAPI
    if transport_settings is None:
        transport_settings = {}

    if service_instance is None:
        service_instance = MeshService(
            service_name=name,
            instance_id=instance_id,
            event_bindings=event_bindings,
            event_callback=event_callback,
        )
    elif event_bindings is not None:
        transport_settings["event_bindings"] = event_bindings

    service_api: RMQAPI = transport(
        amqp_url=connection_properties,
        service_name=name,
        service_instance=service_instance,
        instance_id=instance_id,
        transport_settings=transport_settings,
    )
    return service_api
