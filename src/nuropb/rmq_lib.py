""" RabbitMQ Utility library for NuroPb
"""
import logging
from typing import Dict, Any, List
from urllib.parse import urlparse
from contextlib import contextmanager

import requests
import pika
from pika.channel import Channel

from nuropb.interface import PayloadDict, NuropbTransportError

logger = logging.getLogger()


def amqp_url(
    host: str, port: str | int, username: str, password: str, vhost: str
) -> str:
    """Create an AMQP URL for connecting to RabbitMQ"""
    return f"amqp://{username}:{password}@{host}:{port}/{vhost}"


def rmq_api_url(
    scheme: str, host: str, port: str | int, username: str, password: str
) -> str:
    """Create an API URL for connecting to RabbitMQ"""
    return f"{scheme}://{username}:{password}@{host}:{port}/api"


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
    request_queue: str,
    rpc_bindings: List[str],
    event_bindings: List[str],
) -> bool:
    """Configure the RabbitMQ broker for this transport.

    Calls to this function are idempotent, except for previously named exchanges, queues,
    and declared bindings all of which will not be removed. These will have to be manually
    removed from the broker.

    The response queue is not durable, and is auto-deleted when the connection is closed.
    This is because the response queue is only used for RPC responses, and we don't want
    to keep stale responses around.

    :param str service_name: The name of the service, being configured for
    :param str rmq_url: The URL of the RabbitMQ broker
    :param str events_exchange: The name of the events exchange
    :param str rpc_exchange: The name of the RPC exchange
    :param str dl_exchange: The name of the dead letter exchange
    :param str dl_queue: The name of the dead letter queue
    :param str request_queue: The name of the requests queue
    :param List[str] rpc_bindings: The list of RPC bindings
    :param List[str] event_bindings: The list of events bindings
    :return: True if the RabbitMQ broker was configured successfully
    """
    if len(rpc_bindings) == 0 or service_name not in rpc_bindings:
        rpc_bindings.append(service_name)

    with blocking_rabbitmq_channel(rmq_url) as channel:
        channel.exchange_declare(
            exchange=events_exchange,
            exchange_type="topic",
            durable=True,
        )

        channel.exchange_declare(
            exchange=rpc_exchange,
            exchange_type="direct",
            durable=True,
        )

        """ Setting up dead letter handling - all requests are automatically sent to a dead letter queue."""
        channel.exchange_declare(
            exchange=dl_exchange,
            exchange_type="fanout",
            durable=True,
        )

        channel.queue_declare(queue=dl_queue)
        channel.queue_bind(dl_queue, dl_exchange)

        # Declare the request queue for this transport
        requests_queue_config = {
            "durable": True,
            "auto_delete": False,
            "arguments": {"x-dead-letter-exchange": dl_exchange},
        }
        channel.queue_declare(queue=request_queue, **requests_queue_config)

        """ This NOTE is here for reference, response queue is not durable by default
        and are the responsibility of the client to declare on startup. 
        The response queue is not durable, and is auto-deleted when the connection is 
        closed.This is because the response queue is only used for RPC responses, and we 
        don't want to keep stale responses around.
        responses_queue_config = {"durable": False, "auto_delete": True}
        """

        """ Any new bindings will be registered here, however, previous bindings will not be removed.
            PLEASE TAKE NOTE, especially in the context of event bindings, this could lead to a lot of
            unnecessary traffic and debugging support issues.
        """
        for routing_key in rpc_bindings:
            logger.info("binding to {}".format(routing_key))
            channel.queue_bind(request_queue, rpc_exchange, routing_key)

        for routing_key in event_bindings:
            logger.info("binding to {}".format(routing_key))
            channel.queue_bind(request_queue, events_exchange, routing_key)

        rabbitmq_configured = True

    return rabbitmq_configured


def nack_message(
    channel: Channel,
    delivery_tag: int,
    properties: pika.spec.BasicProperties,
    mesg: PayloadDict | None,
    error: Exception | None = None,
) -> None:
    """nack the message and requeue it, there was a problem with this instance processing the message"""
    if channel is None or not channel.is_open:
        raise NuropbTransportError(
            message="Unable to nack and requeue message, RMQ channel closed",
            lifecycle="service-handle",
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
) -> None:
    """If the message is not a request, then reject the message and move on"""
    if channel is None or not channel.is_open:
        raise NuropbTransportError(
            message="unable to reject message, RMQ channel closed",
            lifecycle="service-handle",
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
) -> None:
    """ack the message"""
    if channel is None or not channel.is_open:
        raise NuropbTransportError(
            message="Unable to ack message, RMQ channel closed",
            lifecycle="service-ack",
            payload=mesg,
            exception=error,
        )
    logger.warning(
        f"Acking message, delivery_tag: {delivery_tag}, correlation_id: {properties.correlation_id}"
    )
    channel.basic_ack(delivery_tag=delivery_tag)


def get_virtual_hosts(api_url: str, vhost_url: str) -> Any | None:
    """Creates a virtual host on the RabbitMQ server using the REST API
    :param api_url: the url to the RabbitMQ API
    :param vhost_url: the virtual host to create

    :return: None
    """
    url_parts = urlparse(vhost_url)
    vhost = url_parts.path[1:] if url_parts.path.startswith("/") else url_parts.path
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
