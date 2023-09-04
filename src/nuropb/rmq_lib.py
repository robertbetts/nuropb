""" RabbitMQ Utility library for NuroPb
"""
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from contextlib import contextmanager

import requests
import pika
from pika.channel import Channel

from nuropb.interface import PayloadDict, NuropbTransportError, NuropbLifecycleState

logger = logging.getLogger(__name__)


def build_amqp_url(
    host: str, port: str | int, username: str, password: str, vhost: str
) -> str:
    """Creates an AMQP URL for connecting to RabbitMQ"""
    return f"amqp://{username}:{password}@{host}:{port}/{vhost}"


def build_rmq_api_url(
    scheme: str, host: str, port: str | int, username: str | None, password: str | None
) -> str:
    """Creates an HTTP URL for connecting to RabbitMQ management API"""
    if username is None or password is None:
        return f"{scheme}://{host}:{port}/api"
    return f"{scheme}://{username}:{password}@{host}:{port}/api"


def rmq_api_url_from_amqp_url(
    amqp_url: str, scheme: Optional[str] = None, port: Optional[int | str] = None
) -> str:
    """Creates an HTTP URL for connecting to RabbitMQ management API from an AMQP URL
    :param amqp_url: the AMQP URL to use
    :param scheme: the scheme to use, defaults to http
    :param port: the port to use, defaults to 15672
    :return: the RabbitMQ management API URL
    """
    url_parts = urlparse(amqp_url)
    username = url_parts.username
    password = url_parts.password
    host = url_parts.hostname if url_parts.hostname else "localhost"
    port = 15672 if port is None else port
    scheme = "http" if scheme is None else scheme
    return build_rmq_api_url(scheme, host, port, username, password)


def management_api_session_info(
    scheme: str,
    host: str,
    port: str | int,
    username: Optional[str] = None,
    password: Optional[str] = None,
    bearer_token: Optional[str] = None,
    verify: bool = False,
    **headers: Any,
) -> Dict[str, Any]:
    """Creates a requests session for connecting to RabbitMQ management API
    :param scheme: http or https
    :param host: the host name or ip address of the RabbitMQ server
    :param port: the port number of the RabbitMQ server
    :param username: the username to use for authentication
    :param password: the password to use for authentication
    :param bearer_token: the bearer token to use for authentication
    :param verify: whether to verify the SSL certificate
    :return: a requests session
    """
    api_url = build_rmq_api_url(scheme, host, port, username, password)
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    headers["Content-Type"] = "application/json"
    session = requests.Session()
    session.headers = headers
    session.verify = verify
    return {
        "api_url": api_url,
        "headers": headers,
    }


@contextmanager
def blocking_rabbitmq_channel(rmq_url: str) -> pika.channel.Channel:
    """Useful for initialisation of queues / exchanges."""
    connection = None
    try:
        parameters = pika.URLParameters(rmq_url)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        yield channel
    except Exception as e:
        logger.error(
            "Error opening blocking connection to open rabbitmq channel: %s", e
        )
        raise
    finally:
        if connection is not None:
            connection.close()


def configure_nuropb_rmq(
    service_name: str,
    rmq_url: str,
    events_exchange: str,
    rpc_exchange: str,
    dl_exchange: str,
    dl_queue: str,
    service_queue: str,
    rpc_bindings: List[str],
    event_bindings: List[str],
    **kwargs: Any,
) -> bool:
    """Configure the RabbitMQ broker for this transport.

    Calls to this function are IDEMPOTENT. However, previously named exchanges, queues,
    and declared bindings are not be removed. These will have to be done manually as part
    of broker housekeeping. This is to prevent accidental removal of queues and exchanges.
    It is safe to call this function multiple times and while other services are running,
    as it will not re-declare exchanges, queues, or bindings that already exist.

    PRODUCTION AUTHORISATION NOTE: The RabbitMQ user used to connect to the broker must
    have the following permissions:
    - configure: .*
    - write: .*
    - read: .*
    - access to the vhost
    Client only applications and services should not have configuration permissions. For
    completeness, there may be specific implementation need to for a client only services
    to register service queue bindings, for example a client only service that is also a
    gateway or proxy service. In this case, the treating it as a service is the correct
    approach.

    Settings for Exchange and default dead letter configuration apply to all services that
    use the same RabbitMQ broker. The rpc and event bindings are exclusive to the service,
    and are not shared with other services.

    The response queues are not durable, and are auto-deleted when the connections close.
    This approach is taken as response queues are only used for RPC responses, and there
    is no need to keep and have to handle stale responses.

    There is experimental work underway using etcd to manage the runtime configuration of
    a service leader and service followers. This will allow for persistent response queues
    and other configuration settings to be shared across multiple instances of the same
    service. This is not yet ready for production use.
    Experimentation scope:
    - service leader election
    - named instances of a service each with their own persistent response queue
    - Notification and handling of dead letter messages relating to a service

    :param str service_name: The name of the service, being configured for
    :param str rmq_url: The URL of the RabbitMQ broker
    :param str events_exchange: The name of the events exchange
    :param str rpc_exchange: The name of the RPC exchange
    :param str dl_exchange: The name of the dead letter exchange
    :param str dl_queue: The name of the dead letter queue
    :param str service_queue: The name of the requests queue
    :param List[str] rpc_bindings: The list of RPC bindings
    :param List[str] event_bindings: The list of events bindings
    :param kwargs: Additional keyword argument overflow from the transport settings.
        - client_only: bool - True if this is a client only service, False otherwise
    :return: True if the RabbitMQ broker was configured successfully
    """
    if kwargs.get("client_only", False):
        logger.info("Client only service, not configuring RMQ")
        return True

    if len(rpc_bindings) == 0 or service_name not in rpc_bindings:
        rpc_bindings.append(service_name)

    with blocking_rabbitmq_channel(rmq_url) as channel:
        logger.info(f"Declaring the dead letter exchange: {dl_exchange}")
        """ Setting up dead letter handling - all requests are automatically sent to a dead letter queue.
        for all services. This is to ensure that no messages are lost, and can be inspected for debugging
        purposes. The dead letter queue is durable, and will survive a broker restart.
        """
        channel.exchange_declare(
            exchange=dl_exchange,
            exchange_type="fanout",
            durable=True,
        )
        logger.info(f"Declaring the dead letter queue: {dl_queue}")
        channel.queue_declare(queue=dl_queue)
        logger.info(
            f"Binding the dead letter queue: {dl_queue} to the dead letter exchange: {dl_exchange}"
        )
        channel.queue_bind(dl_queue, dl_exchange)

        logger.info(f"Declaring the events exchange: {events_exchange}")
        channel.exchange_declare(
            exchange=events_exchange,
            exchange_type="topic",
            durable=True,
        )
        logger.info(f"Declaring the rpc exchange: {rpc_exchange}")
        channel.exchange_declare(
            exchange=rpc_exchange,
            exchange_type="direct",
            durable=True,
        )
        logger.info(
            f"Declaring the request queue: {service_queue} to the rpc exchange: {rpc_exchange}"
        )
        requests_queue_config = {
            "durable": True,
            "auto_delete": False,
            "arguments": {"x-dead-letter-exchange": dl_exchange},
        }
        channel.queue_declare(queue=service_queue, **requests_queue_config)

        """ This NOTE is here for reference only. A response queue is not durable by default
        and is the responsibility of the client/service follower to declare on startup. 
        As the response queue is not durable, it is auto-deleted when the connection is closed. 
        This is because the response queue is only used for RPC responses, and we don't want to 
        keep stale responses around. See the notes above about etcd leader/follower configuration
        for more information.
        
        responses_queue_config = {"durable": False, "auto_delete": True}
        """

        """ Any new bindings will be registered here, however, previous bindings will not be removed.
            PLEASE TAKE NOTE, especially in the context of event bindings, this could lead to a lot of
            unnecessary traffic and debugging support issues.
        """
        for routing_key in rpc_bindings:
            logger.info("binding to {}".format(routing_key))
            channel.queue_bind(service_queue, rpc_exchange, routing_key)

        for routing_key in event_bindings:
            logger.info("binding to {}".format(routing_key))
            channel.queue_bind(service_queue, events_exchange, routing_key)

        rabbitmq_configured = True

    return rabbitmq_configured


def nack_message(
    channel: Channel,
    delivery_tag: int,
    properties: pika.spec.BasicProperties,
    mesg: PayloadDict | None,
    error: Exception | None = None,
    lifecycle: NuropbLifecycleState | None = None,
) -> None:
    """nack_message: nack the message and requeue it, there was likely a recoverable problem with this instance
    while processing the message
    """
    if channel is None or not channel.is_open:
        lifecycle = "service-handle" if lifecycle is None else lifecycle
        raise NuropbTransportError(
            description="Unable to nack and requeue message, RMQ channel closed",
            lifecycle=lifecycle,
            payload=mesg,
            exception=error,
        )
    logger.warning(
        f"Nacking message, delivery_tag: {delivery_tag}, correlation_id: {properties.correlation_id}"
    )
    channel.basic_nack(delivery_tag=delivery_tag, requeue=True)


def reject_message(
    channel: Channel,
    delivery_tag: int,
    properties: pika.spec.BasicProperties,
    mesg: PayloadDict | None,
    error: Exception | None = None,
    lifecycle: NuropbLifecycleState | None = None,
) -> None:
    """reject_message: If the message is not a request, then reject the message and move on"""
    if channel is None or not channel.is_open:
        lifecycle = "service-handle" if lifecycle is None else lifecycle
        raise NuropbTransportError(
            description="unable to reject message, RMQ channel closed",
            lifecycle=lifecycle,
            payload=mesg,
            exception=error,
        )
    logger.warning(
        f"Rejecting message, delivery_tag: {delivery_tag}, correlation_id: {properties.correlation_id}"
    )
    channel.basic_reject(delivery_tag=delivery_tag, requeue=False)


def ack_message(
    channel: Channel,
    delivery_tag: int,
    properties: pika.spec.BasicProperties,
    mesg: PayloadDict | None,
    error: Exception | None = None,
    lifecycle: NuropbLifecycleState | None = None,
) -> None:
    """ack_message: ack the message"""
    if channel is None or not channel.is_open:
        lifecycle = "service-handle" if lifecycle is None else lifecycle
        raise NuropbTransportError(
            description="Unable to ack message, RMQ channel closed",
            lifecycle=lifecycle,
            payload=mesg,
            exception=error,
        )
    logger.warning(
        f"Acking message, delivery_tag: {delivery_tag}, correlation_id: {properties.correlation_id}"
    )
    channel.basic_ack(delivery_tag=delivery_tag)


def get_virtual_host_queues(api_url: str, vhost_url: str) -> Any | None:
    """Creates a virtual host on the RabbitMQ server using the REST API
    :param api_url: the url to the RabbitMQ API
    :param vhost_url: the virtual host to create

    :return: None
    """
    url_parts = urlparse(vhost_url)
    vhost = url_parts.path[1:] if url_parts.path.startswith("/") else url_parts.path
    api_url += f"/queues/{vhost}"
    headers: Dict[str, Any] = {}
    response = requests.get(
        url=api_url,
        headers=headers,
        verify=False,
    )
    if response.status_code == 404:
        return None
    else:
        response.raise_for_status()
        return response.json()


def get_virtual_hosts(api_url: str, vhost_url: str) -> Any | None:
    """Creates a virtual host on the RabbitMQ server using the REST API
    :param api_url: the url to the RabbitMQ API
    :param vhost_url: the virtual host to create

    :return: None
    """
    _ = vhost_url
    api_url += "/vhosts"
    headers: Dict[str, Any] = {}
    response = requests.get(
        url=api_url,
        headers=headers,
        verify=False,
    )
    if response.status_code == 404:
        return None
    else:
        response.raise_for_status()
        return response.json()


def create_virtual_host(api_url: str, vhost_url: str) -> None:
    """Creates a virtual host on the RabbitMQ server using the REST API
    :param api_url: the url to the RabbitMQ API
    :param vhost_url: the virtual host to create

    :return: None
    """
    url_parts = urlparse(vhost_url)
    vhost = url_parts.path[1:] if url_parts.path.startswith("/") else url_parts.path

    vhost_data = get_virtual_hosts(api_url, vhost_url)
    vhost_exists = False
    if vhost_data:
        vhost_exists = any([item["name"] == vhost for item in vhost_data])

    if vhost_exists:
        logger.info(f"vhost exists: {vhost}")
        return

    api_url += f"/vhosts/{vhost}"
    headers = {"content-type": "application/json"}
    data = {"configure": ".*", "write": ".*", "read": ".*"}

    response = requests.put(
        url=api_url,
        json=data,
        headers=headers,
        verify=False,
    )
    logger.info(f"vhost created: {vhost}")
    response.raise_for_status()


def delete_virtual_host(api_url: str, vhost_url: str) -> None:
    """Deletes a virtual host on the RabbitMQ server using the REST API
    :param api_url: the url to the RabbitMQ API
    :param vhost_url: the virtual host to delete

    :return: None
    """
    url_parts = urlparse(vhost_url)
    vhost = url_parts.path[1:] if url_parts.path.startswith("/") else url_parts.path

    vhost_data = get_virtual_hosts(api_url, vhost_url)
    vhost_exists = False
    if vhost_data:
        vhost_exists = any([item["name"] == vhost for item in vhost_data])

    if not vhost_exists:
        logger.info(f"vhost does not exist: {vhost}")
        return

    api_url += f"/vhosts/{vhost}"
    headers = {"content-type": "application/json"}
    response = requests.delete(
        url=api_url,
        headers=headers,
        verify=False,
    )
    logger.info(f"vhost deleted: {vhost}")
    response.raise_for_status()
