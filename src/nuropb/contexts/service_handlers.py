""" This module provides features that handle the execution of nuropb service messages: Requests, Commands and Events.

Attempt is made to make the code agnostic to the underlying transport.

ROADMAP Features and Considerations (in no particular order):
- method parameter validation
- post ack commit or rollback configured by the implementation

"""
import asyncio
import logging
from typing import Any, Tuple, List, Awaitable, Dict

from tornado.concurrent import is_future
import pika.spec

from nuropb.contexts.context_manager_decorator import method_requires_nuropb_context
from nuropb.contexts.describe import describe_service
from nuropb.interface import (
    ResponsePayloadDict,
    NuropbHandlingError,
    NuropbException,
    TransportServicePayload,
    MessageCompleteFunction,
    TransportRespondPayload,
    NUROPB_PROTOCOL_VERSION,
    AcknowledgeAction,
    EventPayloadDict,
    NuropbMessageType,
    NuropbCallAgain,
    NuropbSuccess,
)

logger = logging.getLogger(__name__)

_verbose = False


@property
def verbose() -> bool:
    return _verbose


@verbose.setter
def verbose(value: bool) -> None:
    global _verbose
    _verbose = value


""" Set to True to enable module verbose logging
"""


def error_dict_from_exception(exception: Exception | BaseException) -> Dict[str, str]:
    """Creates an error dict from an exception
    :param exception:
    :return:
    """
    if isinstance(exception, NuropbException):
        return exception.to_dict()

    if hasattr(exception, "description"):
        description = (
            exception.description
            if isinstance(exception, NuropbException)
            else str(exception)
        )
        description = description if description else str(exception)
    else:
        description = str(exception)
    return {
        "error": type(exception).__name__,
        "description": description,
    }


def create_transport_response_from_rmq_decode_exception(
    exception: Exception | BaseException,
    basic_deliver: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
) -> Tuple[AcknowledgeAction, list[TransportRespondPayload]]:
    """Creates a NuroPb response from an unsupported message received over RabbitMQ"""
    _ = basic_deliver

    acknowledgement: AcknowledgeAction = "reject"
    transport_responses: List[TransportRespondPayload] = []
    context: Dict[str, Any] = {}
    correlation_id = properties.correlation_id
    trace_id = properties.headers.get("trace_id", "unknown")

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


def create_transport_responses_from_exceptions(
    service_message: TransportServicePayload, exception: Exception | BaseException
) -> Tuple[AcknowledgeAction, list[TransportRespondPayload]]:
    """Creates a NuroPb response from an exceptions and also accommodates special cases like
    NuropbCallAgain and NuropbSuccess

    :param service_message:
    :param exception:
    :return:
    """
    acknowledgement: AcknowledgeAction = "reject"
    transport_responses: List[TransportRespondPayload] = []
    service_context = service_message["nuropb_payload"]["context"]
    service_type: NuropbMessageType = service_message["nuropb_type"]
    correlation_id = service_message["correlation_id"]
    trace_id = service_message["trace_id"]

    response_template = ResponsePayloadDict(
        tag="response",
        correlation_id=correlation_id,
        context=service_context,
        trace_id=trace_id,
        result=None,
        error=None,
        warning=None,
        reply_to="",
    )
    event_template = EventPayloadDict(
        tag="event",
        correlation_id=correlation_id,
        context=service_context,
        trace_id=trace_id,
        topic="",
        event=None,
        target=None,
    )
    if isinstance(exception, NuropbCallAgain):
        """Acknowledge with a "nack" to requeue the message and send no TransportRespondPayload
        This case will hold true for requests, commands and events

        When a message is nack'd and requeued, there is no current way to track how many
        times this may have occurred for the same message. To ensure stability, behaviour
        predictability and to limit the abuse of patterns, the use of NuropbCallAgain is
        limited to once and only once. This is enforced at the transport layer. For RabbitMQ
        if the incoming message is a requeued message, the basic_deliver.redelivered is
        True. Call again for all redelivered messages will be rejected.

        a nuropb_ca_count header is added
        or incremented to the message. This is used to limit the number of times a message is
        requeued before it is dead-lettered.
        """
        acknowledgement = "nack"
        if service_type == "request":
            response = response_template.copy()
            response["result"] = None
            response["error"] = error_dict_from_exception(exception=exception)
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

    elif isinstance(exception, NuropbSuccess):
        """this is only applicable to requests as they have a response, for commands and events
        the acknowledgement will be "ack" and no TransportRespondPayload will be sent

        only send responses for requests
        """
        acknowledgement = "ack"
        if service_type == "request":
            response = response_template.copy()
            response.update({"result": exception.result})
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
            """ Check the  NuropbSuccess if there are and events to be sent as well
            """
            if exception.events:
                for event in exception.events:
                    event_payload = event_template.copy()
                    event_payload.update(
                        {
                            "topic": event["topic"],
                            "event": event["payload"],
                            "target": event["target"],
                        }
                    )
                    transport_responses.append(
                        TransportRespondPayload(
                            nuropb_protocol=NUROPB_PROTOCOL_VERSION,
                            correlation_id=correlation_id,
                            trace_id=trace_id,
                            ttl=None,
                            nuropb_type="event",
                            nuropb_payload=event_payload,
                        )
                    )

    elif isinstance(exception, (Exception, NuropbException)):
        """Process all other exceptions with a reject acknowledgement and create NuroPb response
        for request messages only.
        """
        acknowledgement = "reject"
        if service_type == "request":
            response = response_template.copy()
            response.update(
                {
                    "error": error_dict_from_exception(exception=exception),
                }
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


def handle_execution_result(
    service_message: TransportServicePayload,
    result: Any,
    message_complete_callback: MessageCompleteFunction,
) -> None:
    """This function is called from the execute_request() to handle both synchronous and asynchronous results

    With standard implementation message_complete_callback is defined in the transport layer.
    * For service messages transport.on_service_message_complete() is used
    * For response messages transport.on_response_message_complete() is used.

    #FUTURE: There is consideration of how to pass a context through this flow to until the transport
    acknowledgement has completed. This is to allow for the possibility of a post ack commit or rollback.
    It also allows to more flexible handling for events raised during requests, commands and incoming events

    :param service_message:
    :param result:
    :param message_complete_callback:
    :return:
    """
    error: BaseException | Dict[str, Any] | None = None
    acknowledgement: AcknowledgeAction = "ack"
    responses = []

    # If this a Future, should it be checked that it's done, or probably has it already?
    if asyncio.isfuture(result):
        error = result.exception()
        if error is None:
            result = result.result()
            acknowledgement = "ack"
        else:
            result = error
            acknowledgement = "reject"

    if isinstance(result, BaseException):
        """Create NuroPb response from an exception, and update acknowledgement type.
        NOTE: Some exceptions are special cases and not necessarily errors. For example,
        NuropbCallAgain and NuropbSuccess are not errors.
        """
        (
            acknowledgement,
            transport_response,
        ) = create_transport_responses_from_exceptions(
            service_message=service_message, exception=result
        )
        if service_message["nuropb_type"] == "request":
            responses.extend(transport_response)
        if verbose:
            logger.exception(result)

    if service_message["nuropb_type"] in ("event", "command"):
        """There is no requirement to handle the response of instance._event_handler result, only to
        positively acknowledge the event. There is also no requirements to handle the response of
        a command, only to positively acknowledge the command.
        """
        pass  # Do nothing

    if service_message["nuropb_type"] == "request":
        """Create NuroPb response from the service call result"""
        if isinstance(error, BaseException):
            pyload_error = error_dict_from_exception(error)
            if verbose:
                logger.exception(result)
        else:
            pyload_error = error

        payload = ResponsePayloadDict(
            tag="response",
            result=result,
            error=pyload_error,
            correlation_id=service_message["correlation_id"],
            trace_id=service_message["trace_id"],
            context=service_message["nuropb_payload"]["context"],
            warning=None,
            reply_to="",
        )
        responses.append(
            TransportRespondPayload(
                nuropb_protocol=NUROPB_PROTOCOL_VERSION,
                correlation_id=service_message["correlation_id"],
                trace_id=service_message["trace_id"],
                ttl=None,
                nuropb_type="response",
                nuropb_payload=payload,
            )
        )

    message_complete_callback(responses, acknowledgement)


def execute_request(
    service_instance: object,
    service_message: TransportServicePayload,
    message_complete_callback: MessageCompleteFunction,
) -> None:
    """Executes a transport request and call the message_complete_callback with the result

    PLEASE NOTE: At first glance awaitable nature of the result_future is not obvious from the code. read the
    comments in transformed_async_future() to understand how the result_future is handled before making any changes.

    :param service_instance: object
    :param service_message: TransportServicePayload
    :param message_complete_callback: MessageCompleteFunction
    :return: None
    """

    if service_message["nuropb_type"] not in ("request", "command", "event"):
        description = f"Service execution not support for message type {service_message['nuropb_type']}"
        err = NuropbHandlingError(
            description=description,
            payload=service_message["nuropb_payload"],
            exception=None,
        )
        handle_execution_result(service_message, err, message_complete_callback)
        return

    result = None
    try:
        payload = service_message["nuropb_payload"]

        if service_message["nuropb_type"] == "event":
            payload = service_message["nuropb_payload"]
            topic = payload["topic"]
            event = payload["event"]
            target = payload["target"]
            context = payload["context"]
            event_handler = getattr(service_instance, "_handle_event_", None)
            if event_handler and callable(event_handler):
                result = event_handler(topic, event, target, context)
            else:
                result = NuropbHandlingError(
                    description=f"error calling instance._event_handler for topic: {topic}",
                    payload=payload,
                    exception=None,
                )
            handle_execution_result(service_message, result, message_complete_callback)
            return

        # By inference service_message["nuropb_type"] in ("request", "command")

        payload = service_message["nuropb_payload"]
        service_name = payload["service"]
        method_name = payload["method"]
        params = payload["params"]

        if method_name != "nuropb_describe" and (
            method_name.startswith("_")
            or not hasattr(service_instance, method_name)
            or not callable(getattr(service_instance, method_name))
        ):
            exception_result = NuropbHandlingError(
                description="Unknown method {}".format(method_name),
                payload=payload,
                exception=None,
            )
            handle_execution_result(
                service_message, exception_result, message_complete_callback
            )
            return

        try:
            if method_name == "nuropb_describe":
                result = describe_service(service_instance)
            else:
                service_instance_method = getattr(service_instance, method_name)
                if method_requires_nuropb_context(service_instance_method):
                    result = service_instance_method(
                        service_message["nuropb_payload"]["context"], **params
                    )
                else:
                    result = getattr(service_instance, method_name)(**params)

        except BaseException as err:
            if not isinstance(err, NuropbException):
                description = (
                    f"Runtime exception calling {service_name}.{method_name}:"
                    f"{type(err).__name__}: {err}"
                )
                exception_result = NuropbException(
                    description=description,
                    payload=payload,
                    exception=err,
                )
            else:
                exception_result = err

            handle_execution_result(
                service_message, exception_result, message_complete_callback
            )
            return

        if asyncio.isfuture(result) or asyncio.iscoroutine(result):
            if is_future(result):
                exception_result = ValueError(
                    "Tornado Future detected, please use asyncio.Future instead"
                )
                handle_execution_result(
                    service_message, exception_result, message_complete_callback
                )
                return

            def future_done_callback(future: Awaitable[Any]) -> None:
                handle_execution_result(
                    service_message, future, message_complete_callback
                )

            task = asyncio.ensure_future(result)
            """This check is important as there's a likelihood that the task is already done"""
            if task.done():
                future_done_callback(task)
            else:
                task.add_done_callback(future_done_callback)

        else:
            handle_execution_result(service_message, result, message_complete_callback)

    except Exception as err:
        # For any potential uncaught exceptions
        handle_execution_result(service_message, err, message_complete_callback)
