from typing import Dict, Optional, Any, Union, Iterable, Tuple, List, Awaitable, Set
from uuid import uuid4
import logging
import json
from datetime import datetime
from asyncio import Future

import pika.spec
from pika.spec import BasicProperties

from nuropb.interface import (
    NuropbInterface,
    NuropbMessageError,
    MessageCallbackType,
    ConnectionCallbackType,
    PayloadDict,
    ResponsePayloadDict,
    RequestPayloadDict,
    EventPayloadDict,
    CommandPayloadDict,
    UnknownPayloadDict,
    PayloadSerializeType,
    NuropbMessageType
)
from nuropb.rmq_transport import RMQTransport, encode_payload

logger = logging.getLogger()


class RMQAPI(NuropbInterface):
    _response_futures: Dict[str, Any]
    _transport: RMQTransport
    _rpc_exchange: str
    _events_exchange: str
    _default_ttl: int

    def __init__(
        self,
        service_name: str,
        instance_id: str,
        amqp_url: str,
        rpc_exchange: Optional[str] = None,
        events_exchange: Optional[str] = None,
        dl_exchange: Optional[str] = None,
        dl_queue: Optional[str] = None,
        request_queue: Optional[str] = None,
        response_queue: Optional[str] = None,
        rpc_bindings: Optional[List[str] | Set[str]] = None,
        event_bindings: Optional[List[str] | Set[str]] = None,
        prefetch_count: Optional[int] = None,
        default_ttl: Optional[int] = None,
    ):
        self._response_futures = {}
        self._default_ttl = 60 * 60 * 1000 if default_ttl is None else default_ttl

        transport_settings: Dict[str, Any] = dict(
            service_name=service_name,
            instance_id=instance_id,
            amqp_url=amqp_url,
            message_callback=self.receive_transport_message,
            rpc_exchange=rpc_exchange,
            events_exchange=events_exchange,
            dl_exchange=dl_exchange,
            dl_queue=dl_queue,
            request_queue=request_queue,
            response_queue=response_queue,
            rpc_bindings=rpc_bindings,
            event_bindings=event_bindings,
            prefetch_count=prefetch_count,
            default_ttl=self._default_ttl,
        )
        self._transport = RMQTransport(**transport_settings)

        self._rpc_exchange = self._transport.rpc_exchange
        self._events_exchange = self._transport.events_exchange

    @property
    def connected(self) -> bool:
        """connected: returns the connection status of the underlying transport
        :return: bool
        """
        return self._transport.connected

    async def connect(self) -> None:
        """connect: connects to the underlying transport
        :return: None
        """
        await self._transport.start()

    async def disconnect(self) -> None:
        """disconnect: disconnects from the underlying transport
        :return: None
        """
        await self._transport.stop()

    def receive_transport_message(self, message: PayloadDict) -> None:
        """_received_message_over_transport: handles a messages received from the transport and routes it to the
            appropriate handler
        :return: None
        """
        if message["tag"] == "request":
            logger.debug(
                "Received request: %s.%s", message["service"], message["method"]
            )

            """ Echo sample response
            """
            response_message: ResponsePayloadDict = {
                "tag": "response",
                "correlation_id": message["correlation_id"],
                "context": message["context"],
                "trace_id": message["trace_id"],
                "result": f"response from {message['service']}.{message['method']}",
                "error": None,
            }
            body = encode_payload(response_message, "json")
            routing_key = message["reply_to"]
            properties = {
                "content_type": "application/json",
                "correlation_id": message["correlation_id"],
                "headers": {
                    "nuropb_type": "response",
                    "trace_id": message["trace_id"],
                },
            }
            self._transport.send_message(
                "", routing_key, body, properties=properties, mandatory=True
            )

        elif message["tag"] == "response":
            logger.debug("Received response: %s", message["correlation_id"])
            if message["correlation_id"] not in self._response_futures:
                logger.warning(
                    "Received an unpaired response, ignoring %s", message["correlation_id"]
                )
                return
            response_future = self._response_futures.pop(message["correlation_id"])
            response_future.set_result(message)

        elif message["tag"] == "event":
            logger.debug("Received event: %s", message["topic"])

        elif message["tag"] == "command":
            logger.debug("Received command: %s.%s", message["service"], message["method"])

    async def request(
        self,
        service: str,
        method: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
        rpc_response: bool = True,
    ) -> Union[ResponsePayloadDict, Any]:
        """Make a request for a method on service and wait until the response is received. The
            request message uses the 'message expiry' configured on the underlying transport.

            expiry is the time in milliseconds that the message will be kept on the queue before being moved
            to the dead letter queue. If None, then the message expiry configured on the transport is used.


            #TODO: Look into returning a dead letter exception for timeout or other errors that result
                in the message being returned to dead letter queue.

        Parameters:
        ----------
        service: str
            The routing key on the rpc exchange to direct the request to the desired service request queue.

        method: str
            The name of the api call / method on the service

        params: dict
            The method input parameters

        context: dict
            The context of the request. This is used to pass information to the service manager
            and is not used by the transport.
                - user_id: str  # a unique user identifier or token of the user that made the request
                - correlation_id: str  # a unique identifier of the request used to correlate the response to the request
                                       # or trace the request over the network (e.g. a uuid4 hex string)
                - service: str
                - method: str

        ttl: int optional
            expiry is the time in milliseconds that the message will be kept on the queue before being moved
            to the dead letter queue. If None, then the message expiry configured on the transport is used.

        trace_id: str optional
            an identifier to trace the request over the network (e.g. a uuid4 hex string)

        rpc_response: bool optional
            If True, then the remote rpc response is returned, else a ResponsePayloadDict is returned

        Returns:
        --------
            ResponsePayloadDict | Any: representing the response from the requested service with any exceptions raised
        """

        correlation_id = uuid4().hex
        ttl = self._default_ttl if ttl is None else ttl
        properties = dict(
            content_type="application/json",
            correlation_id=correlation_id,
            reply_to=self._transport.response_queue,
            headers={
                "nuropb_type": "request",
                "trace_id": trace_id,
            },
            expiration=f"{ttl}",
        )
        context["rmq_correlation_id"] = correlation_id
        message: RequestPayloadDict = {
            "tag": "request",
            "service": service,
            "method": method,
            "params": params,
            "correlation_id": correlation_id,
            "context": context,
            "trace_id": trace_id,
            "reply_to": self._transport.response_queue,
        }
        body = encode_payload(message, "json")
        routing_key = service

        response_future: Awaitable[PayloadDict] = Future()
        self._response_futures[correlation_id] = response_future

        # mandatory means that if it doesn't get routed to a queue then it will be returned vi self._on_message_returned
        logger.debug(
            f"Sending request message:\n"
            f"correlation_id: {correlation_id}\n"
            f"trace_id: {trace_id}\n"
            f"exchange: {self._transport.rpc_exchange}\n"
            f"routing_key: {routing_key}\n"
        )
        self._transport.send_message(
            exchange=self._transport._rpc_exchange,
            routing_key=routing_key,
            body=body,
            properties=properties,
            mandatory=True,
        )


        try:
            response: PayloadDict = await response_future
        except Exception as err:
            error_message = (
                f"Error while waiting for response to complete."
                f"correlation_id: {correlation_id}, trace_id: {trace_id}, error:{err}"
            )
            logger.exception(error_message)
            raise NuropbMessageError(error_message, response)

        if response["tag"] != "response":
            """This logic condition is prevented in the transport layer"""
            raise NuropbMessageError(
                f"Unexpected response message type: {response['tag']}", response
            )

        if not rpc_response:
            return response
        elif response["error"]:
            raise NuropbMessageError(f"RPC service error: {response['error']}", response)
        else:
            return response["result"]

    async def publish_event(
        self,
        topic: str,
        event: Dict[str, Any],
        context: Dict[str, Any],
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """Broadcasts an event with the given 'topic'.

        Parameters:
        ----------
        topic: str
            The routing key on the events exchange

        event: json-encodable Python Dict.

        context: dict
            The context around gent generation, example content includes:
                - user_id: str  # a unique user identifier or token of the user that made the request
                - correlation_id: str  # a unique identifier of the request used to correlate the response to the request
                                       # or trace the request over the network (e.g. a uuid4 hex string)
                - service: str
                - method: str

        ttl: int optional
            expiry is the time in milliseconds that the message will be kept on the queue before being moved
            to the dead letter queue. If None, then the message expiry configured on the transport is used.
            defaulted to 0 (no expiry) for events

        trace_id: str optional
            an identifier to trace the request over the network (e.g. a uuid4 hex string)

        """
        correlation_id = uuid4().hex
        ttl = 0 if ttl is None else ttl
        properties = dict(
            content_type="application/json",
            correlation_id=correlation_id,
            headers={
                "nuropb_type": "event",
                "trace_id": trace_id,
            },
            expiration=f"{ttl}",
        )
        context["rmq_correlation_id"] = correlation_id
        message: EventPayloadDict = {
            "tag": "event",
            "topic": topic,
            "event": event,
            "context": context,
            "trace_id": trace_id,
            "correlation_id": correlation_id,
        }
        body = encode_payload(message,"json")
        routing_key = topic
        logger.debug(
            "Sending event message: (%s - %s) (%s - %s)",
            correlation_id,
            self._transport.rpc_exchange,
            routing_key,
        )
        self._transport.send_message(
            exchange=self._transport.events_exchange,
            routing_key=routing_key,
            body=body,
            properties=properties,
            mandatory=True,
        )

