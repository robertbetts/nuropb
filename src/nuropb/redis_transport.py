import functools
import json
import logging
from typing import Any, Dict, Literal, Optional, TypedDict, List
import time
import asyncio

from redis import asyncio as aioredis
import redis

from nuropb.encodings.serializor import decode_payload, encode_payload
from nuropb.interface import (
    NUROPB_MESSAGE_TYPES,
    NUROPB_PROTOCOL_VERSION,
    NUROPB_PROTOCOL_VERSIONS_SUPPORTED,
    NUROPB_VERSION,
    AcknowledgeAction,
    MessageCallbackFunction,
    NuropbCallAgainReject,
    NuropbTransportError,
    TransportRespondPayload,
    TransportServicePayload
)
from nuropb.encodings.encryption import Encryptor
from nuropb.redis_lib import (
    build_redis_url,
    configure_nuropb_redis,
    create_transport_response_from_redis_decode_exception
)
from nuropb.contexts import service_handlers
from nuropb.utils import obfuscate_credentials

class RedisConfiguration(TypedDict):
    dl_queue: str
    service_queue: str
    response_queue: str
    client_only: bool
    
    
logger = logging.getLogger(__name__)

_verbose = False

@property
def verbose() -> bool:
    return _verbose

@verbose.setter
def verbose(value: bool) -> None:
    global _verbose
    _verbose = value
    service_handlers.verbose = value

""" Set to True to enable module verbose logging
"""

def decode_redis_body(body: bytes) -> TransportServicePayload:
    """Map the incoming Redis message to python  dictionary as
    defined by ServicePayloadDict
    """
    json_message = json.loads(body)
    service_message: TransportServicePayload = {
        "nuropb_protocol": json_message["headers"].get("nuropb_protocol"),
        "nuropb_version": json_message["headers"].get("nuropb_version"),
        "nuropb_type": json_message["headers"].get("nuropb_type"),
        "nuropb_payload": {},
        "correlation_id": json_message["headers"].get("correlation_id"),
        "trace_id": json_message["headers"].get("trace_id"),
        "encrypted": json_message["headers"].get("encrypted"),
        "reply_to": json_message["headers"].get("reply_to"),
    }
    if service_message["nuropb_protocol"] not in NUROPB_PROTOCOL_VERSIONS_SUPPORTED:
        raise ValueError(
            f"nuropb_protocol '{service_message['nuropb_protocol']}' is not supported"
        )
    if service_message["nuropb_type"] not in NUROPB_MESSAGE_TYPES:
        raise ValueError(
            f"message_type '{service_message['nuropb_type']}' is not supported"
        )
    service_message["nuropb_payload"] = decode_payload(json_message["payload"], "json")
    
    return service_message
    
class RedisTransport:
    """RedisTransport is the base class for the Redis API. It wraps the
    NuroPb service mesh patterns and rules.

    When Redis closes the connection, this class will stop.
    Disconnections should be continuously monitored, there are various reasons why a
    connection may be closed after being successfully opened, and usually
    related to authentication, permissions, protocol violation or networking.
    
    https://redis-py.readthedocs.io/en/stable/connections.html
        redis://[[username]:[password]]@localhost:6379/0
        rediss://[[username]:[password]]@localhost:6379/0
        unix://[username@]/path/to/socket.sock?db=0[&password=password]    
    """
    def __init__(
        self,
        service_name: str,
        instance_id: str,
        url: str | Dict[str, Any],
        message_callback: MessageCallbackFunction,
        client_only: Optional[bool] = None,
        encryptor: Optional[Encryptor] = None,
        **kwargs: Any,
    ):
        self._connected = False
        self._connection = None
        self._client_only = False if client_only is None else client_only
        """ If client_only is True, then the transport will not service
        the handling of requests, commands and events disabled. 
        """
        
        self._encryptor = encryptor
        self._service_name = service_name
        self._instance_id = instance_id
        if isinstance(url, dict):
            url = build_redis_url(
                scheme=url.get("scheme"),
                host=url["host"],
                port=url["port"],
                username=url.get("username"),
                password=url.get("password"),
                database=url.get("database"),
            )
        self._url = url            
        self._dl_queue = (
            kwargs.get("dl_queue", None) or f"nuropb-{self._service_name}-dl"
        )
        self._service_queue = (
            kwargs.get("service_queue", None) or f"nuropb-{self._service_name}-sq"
        )
        self._response_queue = (
            kwargs.get("response_queue", None)
            or f"nuropb-{self._service_name}-{self._instance_id}-rq"
        )
        self._message_callback = message_callback

        self._is_leader = True

        self._listenting_task = None

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def url(self) -> str | Dict[str, Any]:
        return self._url

    @property
    def is_leader(self) -> bool:
        return self._is_leader

    @is_leader.setter
    def is_leader(self, value: bool) -> None:
        """is_leader: set the transport's leader status"""
        self._is_leader = value
        
    @property
    def connected(self) -> bool:
        """connected: returns the connection status of the underlying transport
        :return: bool
        """
        return self._connected

    @property
    def service_queue(self) -> str:
        """response_queue: returns the name of the sevice queue
        :return: str
        """
        return self._service_queue       

    @property
    def response_queue(self) -> str:
        """response_queue: returns the name of the response queue
        :return: str
        """
        return self._response_queue        
    
    @property
    def configuration(self) -> RedisConfiguration:
        """configuration: returns the Redis configuration
        :return: Dict[str, Any]
        """
        return {
            "dl_queue": self._dl_queue,
            "service_queue": self._service_queue,
            "response_queue": self._response_queue,
            "client_only": self._client_only,
        }
        
    async def start(self) -> None:
        """Start the transport by connecting to Redis"""
        try:
            self._connection = await aioredis.from_url(self._url)
            self._connected = True
            asyncio.create_task(self.listen_to_queues())
        except Exception as err:
            logger.exception(
                "General failure while connecting to Redis. %s: %s",
                type(err).__name__,
                err,
            )
            
    async def stop(self) -> None:
        """Stop the transport by disconnecting from Redis"""
        if self._connected:
            self._connected = False
            await self._connection.aclose()

    async def send_message(
        self,
        payload: Dict[str, Any],
        encoding: str | None = None,
        encrypted: bool = False,
    ) -> None:
        """Send a message to over Redis

        :param Dict[str, Any] payload: The message contents
        :param encoding: The encoding of the message
        :param encrypted: True if the message is to be encrypted
        """
        logger.debug(f"{self._service_name} sending message: {type(payload)} {payload}")
        if payload["tag"] not in ("event", "request", "command", "response"):
            raise ValueError(f"Unknown message type {payload['tag']}")
        
        reply_to = None
        if payload["tag"] == "event":
            routing_key = payload["topic"]
        elif payload["tag"] in ("request", "command"):
            # NOTE: With Rabit the routing key is the service name and exchange name. the service queue routing happens internal to the broker
            # with Redis the service's routing_key must be explict following the convention: f"nuropb-{payload['service']}-sq" 
            routing_key = f"nuropb-{payload['service']}-sq"
            reply_to = self._response_queue
        elif payload["tag"] == "response":
            routing_key = payload["reply_to"]

        encoding = "json" if encoding is None else encoding
        body = encode_payload(
            payload=payload,
            payload_type=encoding,
        )

        """ Next encrypt the payload if public_key is not None, update the header
        to indicate encrypted payload.
        """
        if (
            encrypted
            and self._encryptor
            and payload["tag"] in ("request", "command", "response")
        ):
            to_service = None if payload["tag"] == "response" else payload["service"]
            """ only outgoing response and command messages require the target service name
            """
            wire_body = self._encryptor.encrypt_payload(
                payload=body,
                correlation_id=payload["correlation_id"],
                service_name=to_service,
            )
        else:
            wire_body = body

        message = dict(
            headers = {
                "nuropb_protocol": NUROPB_PROTOCOL_VERSION,
                "nuropb_version": NUROPB_VERSION,
                "nuropb_type": payload["tag"],
                "correlation_id": payload["correlation_id"],
                "trace_id": payload["trace_id"],
                "reply_to": reply_to,
                "encrypted": encrypted,
            },
            payload = wire_body.decode()
        )
        
        try:
            await self._connection.lpush(routing_key, json.dumps(message))
        except Exception as err:
            logger.error("dict: {message}")
            logger.exception(f"Error decoding message to json: {err}")
            
            return
        logger.debug(f"{self._service_name} sent message sent {routing_key}")

    @classmethod
    def acknowledge_service_message(
        cls,
        metadata: Dict[str, Any],
        action: Literal["ack", "nack", "reject"],
        redelivered: bool,
    ) -> None:
        """Acknowledgement of a message

        # TODO: Implement the acknowledgement of a message and replaying of messages for Redis

        In NuroPb, acknowledgements of message is due to three possible outcomes:
        - ack: Successfully processed, acknowledged and removed from the queue
        - nack: A recoverable error occurs, the message is not acknowledged and requeued
        - reject: An unrecoverable error occurs, the message is not acknowledged and dropped

        To prevent accidental use of the redelivered parameter and to ensure system
        predictability on the Call Again feature, messages are only allowed to be redelivered
        once and only once. To this end all messages that have redelivered == True will be
        rejected. if redelivered is overridden with None, it is assumed True.

        :param str action: The action to take, one of ack, nack or reject
        :param bool redelivered: True if the message is being requeued / replayed.
        """
        _ = metadata
        redelivered = True if redelivered is None else redelivered
        nuropb_type = metadata["nuropb_type"]
        correlation_id = metadata["correlation_id"]
        
        if action == "ack":
            logger.debug("Acknowledging message")
        elif action == "nack":
            if redelivered:
                logger.debug(
                    "Redelivered is True, action is overridden from {action} to rejected"
                )
            else:
                logger.debug(
                    "Redelivered is False, first time nack and requeue is allowed"
                )
        elif action == "reject":
            logger.debug(f"Rejecting message {nuropb_type}, {correlation_id}")
        else:
            raise ValueError(f"Invalid action {action}")

    @classmethod
    def metadata_metrics(cls, metadata: Dict[str, Any]) -> None:
        """Invoked by the transport after a service message has been processed.

        NOTE - METADATA: keep this metadata in sync with across all these methods:
            - on_service_message, on_service_message_complete
            - on_response_message, on_response_message_complete
            - metadata_metrics

        :param metadata: information to drive message processing metrics
        :return: None
        """
        metadata["end_time"] = time.time()
        metadata["duration"] = metadata["end_time"] - metadata["start_time"]
        # FIXME: uncomment the line below
        # logger.debug(f"metadata log: {metadata}")
        

    def on_service_message_complete(
        self,
        metadata: Dict[str, Any],
        response_messages: List[TransportRespondPayload],
        acknowledgement: AcknowledgeAction,
    ) -> None:
        """Invoked by the implementation after a service message has been processed.

        This is provided to the implementation as a helper function to complete the message flow.
        The message flow state parameters: channel, delivery_tag, reply_to and private_metadata
        are hidden from the implementation through the use of functools.partial. The interface
        of this function as it appears to the implementation is:
            response_messages:  List[TransportRespondPayload]
            acknowledgement: Literal["ack", "nack", "reject"]

        NOTE: The acknowledgement references the incoming service message that resulted in
              these responses

        :param metadata: information to drive message processing metrics
        :param response_messages: List[TransportRespondPayload]
        :param acknowledgement:
        :return:
        """
        redelivered = metadata.get("redelivered")
        reply_to = metadata["reply_to"]
        trace_id = metadata.get("trace_id", "unknown")
        correlation_id = metadata["correlation_id"]
        encrypted = metadata.get("encrypted")
        redelivered = metadata.get("redelivered")

        if redelivered is True and acknowledgement == "nack":
            if verbose:
                logger.debug(
                    "Redelivered is True, action is overridden from nack to rejected"
                )
            acknowledgement = "reject"
            if metadata["nuropb_type"] == "request":
                exception = NuropbCallAgainReject(
                    description=(
                        f"Rejecting second call again request for trace_id: {trace_id}"
                        f", correlation_id: {correlation_id}"
                    )
                )
                response_messages[0]["nuropb_payload"][
                    "error"
                ] = service_handlers.error_dict_from_exception(exception=exception)
            else:
                response_messages = []
        elif acknowledgement == "nack":
            response_messages = []

        self.acknowledge_service_message(metadata, acknowledgement, redelivered)

        async def async_send_():
            for respond_message in response_messages:
                respond_payload = respond_message["nuropb_payload"]
                if respond_payload["tag"] == "response":
                    respond_payload["reply_to"] = reply_to
                    logger.debug(f"Sending {acknowledgement} response to {reply_to}")
                respond_payload["correlation_id"] = correlation_id
                respond_payload["trace_id"] = trace_id
                try:
                    await self.send_message(
                        payload=respond_payload,
                        encoding="json",
                        encrypted=encrypted,
                    )
                except Exception as err:
                    logger.exception(
                        (
                            f"Error sending response message: {err}\n"
                            f"correlation_id: {correlation_id}\n"
                            f"trace_id: {trace_id}\n"
                        )
                    )

            """ NOTE - METADATA: keep this dictionary in sync with across all these methods:
                - on_message, on_message_complete
                - metadata_metrics
            """
            metadata["acknowledgement"] = acknowledgement
            metadata["message_count"] = len(response_messages)
            metadata["flow_complete"] = True
            self.metadata_metrics(metadata=metadata)
        
        asyncio.create_task(async_send_())
    
    async def on_service_message(self, body: bytes) -> None:
        """on_message: callback function to handle incoming messages
        :param message: Dict[str, Any]
        :return: None
        """
        logger.debug("Message received on service queue: %s", body)
        
        """NOTE - METADATA: keep this dictionary in sync with across all these methods:
        - on_service_message, on_message_complete
        - metadata_metrics
        """
        nuropb_message = json.loads(body)
        metadata = {
            "start_time": time.time(),
            "service_name": self._service_name,
            "instance_id": self._instance_id,
            "is_leader": self._is_leader,
            "client_only": self._client_only,
            "nuropb_type": nuropb_message["headers"]["nuropb_type"],
            "nuropb_version": nuropb_message["headers"]["nuropb_version"],
            "correlation_id": nuropb_message["headers"]["correlation_id"],
            "trace_id": nuropb_message["headers"].get("trace_id"),
            "encrypted": nuropb_message["headers"].get("encrypted"),
            "reply_to": nuropb_message["headers"].get("reply_to"),
            "redelivered": nuropb_message["headers"].get("redelivered"),
        }
        message_complete_callback = functools.partial(
            self.on_service_message_complete,
            metadata,
        )
        encrypted = metadata["encrypted"]
        correlation_id = metadata["correlation_id"]
        redelivered = metadata["redelivered"]
        
        """ Decode service message
        """
        try:
            if encrypted and self._encryptor:
                body = self._encryptor.decrypt_payload(
                    payload=nuropb_message["payload"],
                    correlation_id=correlation_id,
                )
            
            service_message: TransportServicePayload = decode_redis_body(body)
        except Exception as error:
            """Exceptions caught here are treated as permanent failures, ack the message and send
            error response is possible
            """
            logger.exception(f"Service message decode error: {error}")
            self.acknowledge_service_message(
                metadata,  "reject", redelivered
            )

            try:
                (
                    acknowledgement,
                    responses,
                ) = create_transport_response_from_redis_decode_exception(
                    exception=error, metadata=metadata
                )
                message_complete_callback(responses, acknowledgement)
            except Exception as err:
                logger.debug(
                    f"Failed to send service message decode error response: {err}"
                )

            return


        """ NEXT: handle the service message
        
            Any errors caught here are treated as permanent failures, rejected and dropped.        
        """            
        try:
            """Assume for now that we can't use key word arguments in self.message_callback"""
            self._message_callback(service_message, message_complete_callback, metadata)

        except asyncio.CancelledError:
            logger.debug("on_message task was cancelled for correlation_id: %s", nuropb_message["correlation_id"])

        except Exception as error:
            """Exceptions caught here are treated as permanent failures, ack the message and send error response"""
            logger.exception(f"service message handling error: {error}")
            try:
                (
                    acknowledgement,
                    responses,
                ) = create_transport_response_from_redis_decode_exception(
                    exception=error,
                    metadata=metadata
                )
                await message_complete_callback(responses, acknowledgement)
            except Exception as err:
                logger.debug(f"Failed to send service handling error response: {err}")
        

    def on_response_message_complete(
        self,
        metadata: Dict[str, Any],
        response_messages: List[TransportRespondPayload],
        acknowledgement: AcknowledgeAction,
    ) -> None:
        """Invoked by the implementation after a service message has been processed.

        This is provided to the implementation as a helper function to complete the message flow.
        The message flow state parameters: channel, delivery_tag, reply_to and private_metadata
        are hidden from the implementation through the use of functools.partial. The interface
        of this function as it appears to the implementation is:
            response_messages:  List[TransportRespondPayload]
            acknowledgement: Literal["ack", "nack", "reject"]

        NOTE: The acknowledgement references the incoming service message that resulted in
              these responses

        :param metadata: information to drive message processing metrics
        :param response_messages: List[TransportRespondPayload]
        :param acknowledgement:
        :return:
        """
        if acknowledgement != "ack":
            logger.warning(
                f"Response messages are auto-acknowledged, ignoring {acknowledgement}"
            )
            acknowledgement = "ack"

        """ Response messages are received from the response queue which is configured for 
        auto-acknowledgement. Code below is for reference only in the event that auto-acknowledgement 
        is disabled or a durable queue is used with explicit acknowledgement.
        
        self.acknowledge_service_message(channel, delivery_tag, acknowledgement, redelivered)
        """

        if len(response_messages) > 0:
            logger.warning(
                "Response messages are not themselves allowed to have response replies, ignoring"
            )

        """ NOTE - METADATA: keep this dictionary in sync with across all these methods:
        - on_service_message, on_service_message_complete
        - on_response_message, on_response_message_complete
        - metadata_metrics
        """
        metadata["acknowledgement"] = acknowledgement
        metadata["message_count"] = 0
        metadata["flow_complete"] = True
        self.metadata_metrics(metadata=metadata)
    
    async def on_response_message(
        self,
        body: bytes,
    ) -> None:
        """Invoked when a message is delivered to the response_queue. 
        :param bytes body: The message body
        """
        
        logger.debug("Message received on response queue: %s", body)
        nuropb_message = json.loads(body)
                
        """NOTE - METADATA: keep this dictionary in sync with across all these methods:
        - on_service_message, on_message_complete
        - metadata_metrics
        """
        metadata = {
            "start_time": time.time(),
            "service_name": self._service_name,
            "instance_id": self._instance_id,
            "is_leader": self._is_leader,
            "client_only": self._client_only,
            "nuropb_type": nuropb_message["headers"]["nuropb_type"],
            "nuropb_version": nuropb_message["headers"]["nuropb_version"],
            "correlation_id": nuropb_message["headers"]["correlation_id"],
            "trace_id": nuropb_message["headers"].get("trace_id"),
            "encrypted": nuropb_message["headers"].get("encrypted"),
            "reply_to": nuropb_message["headers"].get("reply_to"),
            "redelivered": nuropb_message["headers"].get("redelivered"),
        }        
        
        correlation_id = metadata["correlation_id"]
        nuropb_type = metadata["nuropb_type"],
        nuropb_version = metadata["nuropb_version"]
        encrypted = metadata["encrypted"]

        if not verbose:
            logger.debug(f"response message received: '{nuropb_type}'")
        else:
            logger.debug(
                (
                    f"MESSAGE FROM RESPONSE QUEUE:\n"
                    f"service_name: {self._service_name}\n"
                    f"instance_id: {self._instance_id}\n"
                    f"correlation_id: {correlation_id}\n"
                    f"trace_id: {metadata['trace_id']}\n"
                    f"nuropb_type: {nuropb_type}\n"
                    f"nuropb_version: {nuropb_version}\n"
                    f"encrypted: {encrypted}\n"
                )
            )
        try:
            """NOTE - METADATA: keep this dictionary in sync with across all these methods:
            - on_service_message, on_service_message_complete
            - on_response_message, on_response_message_complete
            - metadata_metrics
            """
            message_complete_callback = functools.partial(
                self.on_service_message_complete,
                metadata,
            )
            
            if encrypted and self._encryptor:
                body = self._encryptor.decrypt_payload(
                    payload=nuropb_message["payload"],
                    correlation_id=correlation_id,
                )

            message = decode_redis_body(body)
            self._message_callback(message, message_complete_callback, metadata)
            
        except Exception as err:
            logger.exception(
                (
                    f"Error processing response message: {err}\n"
                    f"correlation_id: {correlation_id}\n"
                    f"trace_id: {metadata['trace_id']}\n"
                )
            )

    async def listen_to_queues(self) -> None:

        if self._client_only:
            queues = [self._response_queue]
        else:
            queues = [self._service_queue, self._response_queue]
        logger.debug(f"{self._service_name} Listening to queues: %s", ", ".join(queues))
                        
        while self._connected:
            """ https://aioredis.readthedocs.io/en/latest/examples/#blocking-commands
            """
            try:
                queue_recieved, raw_message = await self._connection.blpop(queues, timeout=0)
                queue_name = queue_recieved.decode()
                
                logger.debug(f"{self._service_name} received redis message from list: {queue_name}")
                
                if queue_name == self._service_queue:
                    await self.on_service_message(raw_message)
                elif queue_name == self._response_queue:
                    await self.on_response_message(raw_message)
                else:
                    logger.error(f"Unknown queue: {queue_name}")
                    continue
                
            except redis.exceptions.ConnectionError as err:
                logger.info(f"ConnectionError : {err}")
                self._connected = False
                break
            except asyncio.CancelledError:
                logger.info("listen_to_queues task was cancelled")
                break
            except Exception as err:
                logger.exception(f"Runtime error listening for messages: {err}\n")
                break
