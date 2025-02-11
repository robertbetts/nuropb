""" Redis Utility library for NuroPb
"""
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from contextlib import contextmanager
from typing import Any, Tuple, List, Awaitable, Dict

from nuropb.contexts.service_handlers import error_dict_from_exception
from nuropb.interface import (
    AcknowledgeAction,
    PayloadDict,
    NuropbTransportError,
    NUROPB_VERSION,
    NUROPB_PROTOCOL_VERSION,
    ResponsePayloadDict,
    TransportRespondPayload,
)

logger = logging.getLogger(__name__)


def build_redis_url(
    scheme: str | None = None,
    host: str | None = None,
    port: str | None = None,
    username: str = None,
    password: str = None,
    database: int | None = None,
    
) -> str:
    """Creates an AMQP URL for connecting to RabbitMQ
    
    https://redis-py.readthedocs.io/en/stable/connections.html
        redis://[[username]:[password]]@localhost:6379/0
        rediss://[[username]:[password]]@localhost:6379/0
        unix://[username@]/path/to/socket.sock?db=0[&password=password]    
    """
    scheme = f"{scheme}" if scheme else "redis"
    host = f"{host}" if host else "127.0.0.1"
    port = f"{port}" if port else "6379"
    database = f"{database}" if database else ""
    if username:
        password = f":{password}" if password.strip() else ""
        return f"{scheme}://{username}{password}@{host}:{port}/{database}"
    else:
        return f"{scheme}://{host}:{port}/{database}"
    

def configure_nuropb_redis(
    url: str | Dict[str, Any],
    events_exchange: str,
    rpc_exchange: str,
    dl_exchange: str,
    dl_queue: str,
    **kwargs: Any,
) -> bool:
    """Configure the Reddis as a message broker for this transport.

    Calls to this function are IDEMPOTENT. However, previously named exchanges, queues,
    and declared bindings are not be removed. These will have to be done manually as part
    of broker housekeeping. This is to prevent accidental removal of queues and exchanges.
    It is safe to call this function multiple times and while other services are running,
    as it will not re-declare exchanges, queues, or bindings that already exist.

    :param str url: The URL for Redis
    :param str events_exchange: The name of the events exchange
    :param str rpc_exchange: The name of the RPC exchange
    :param str dl_exchange: The name of the dead letter exchange
    :param str dl_queue: The name of the dead letter queue
    :param kwargs: Additional keyword argument overflow from the transport settings.
        - client_only: bool - True if this is a client only service, False otherwise
    :return: True if Redis was configured successfully
    """
    if kwargs.get("client_only", False):
        logger.info("Client only service, not configuring Redis")
        return True

    redis_configured = True

    return redis_configured


def create_transport_response_from_redis_decode_exception(
    exception: Exception | BaseException,
    metadata: Dict[str, Any],
) -> Tuple[AcknowledgeAction, list[TransportRespondPayload]]:
    """Creates a NuroPb response from an unsupported message received from Redis"""

    acknowledgement: AcknowledgeAction = "reject"
    transport_responses: List[TransportRespondPayload] = []
    context: Dict[str, Any] = {}
    correlation_id = metadata["correlation_id"]
    trace_id = metadata.get("trace_id", "unknown")

    response = ResponsePayloadDict(
        tag="response",
        correlation_id=correlation_id,
        context=context,
        trace_id=trace_id,
        result=None,
        error=error_dict_from_exception(exception=exception),
        warning=None,
        reply_to="",
    )
    transport_responses.append(
        TransportRespondPayload(
            nuropb_protocol=NUROPB_PROTOCOL_VERSION,
            correlation_id=correlation_id,
            trace_id=trace_id,
            ttl=None,
            nuropb_type="response",
            nuropb_payload=response,
        )
    )
    return acknowledgement, transport_responses
