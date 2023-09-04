"""

# TODO: Consider if the checks below should be done here or in the service implementation,
#       in addition if the service implementation, inherits from a NuroPb service base class
#       then these checks and more could be done in the base class.
# - TODO: check if the method is deprecated
# - TODO: check user authentication and authorisation
# - TODO: method validation (params, context)
# - TODO: wrap execution within a context manager
# - TODO: pass context to the service method

"""
import asyncio
import logging
from typing import Any, Tuple, List, Awaitable

from tornado.concurrent import is_future
import pika.spec

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
verbose = False


def error_dict_from_exception(exception: Exception | BaseException) -> dict[str, str]:
    """Creates an error dict from an exception
    :param exception:
    :return:
    """
    if hasattr(exception, "to_dict"):
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
    context = {}
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

    :param service_message:
    :param result:
    :param message_complete_callback:
    :return:
    """
    error = None
    acknowledgement: AcknowledgeAction = "ack"
    if asyncio.isfuture(result):
        error = result.exception()
        if error is None:
            result = result.result()
            acknowledgement = "ack"
        else:
            result = error
            acknowledgement = "reject"

    responses = []
    if service_message["nuropb_type"] == "event":
        """No requirement to handle the instance._event_handler result, only to positively acknowledge the event"""
        acknowledgement = "ack"
    else:
        if isinstance(result, (Exception, BaseException)):
            """Create NuroPb response from an exception, and update acknowledgement response

            Do not send a response for commands
            """
            (
                acknowledgement,
                transport_response,
            ) = create_transport_responses_from_exceptions(
                service_message=service_message, exception=result
            )
            """ Do not send a response for commands
            """
            if service_message["nuropb_type"] == "request":
                responses.extend(transport_response)

        elif service_message["nuropb_type"] == "request":
            """Create NuroPb response from the service call result

            Do not send a response for commands
            """
            payload = ResponsePayloadDict(
                tag="response",
                result=result,
                error=error,
                correlation_id=service_message["correlation_id"],
                trace_id=service_message["trace_id"],
                context=service_message["nuropb_payload"]["context"],
                warning=None,
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
    """Executes a transport request and calls the message_complete_callback with the result

    PLEASE NOTE: At first glance awaitable nature of the result_future is not obvious from the code. read the
    comments in transformed_async_future() to understand how the result_future is handled before making any changes.

    :param service_instance: object
    :param service_message: TransportServicePayload
    :param message_complete_callback: MessageCompleteFunction
    :return: None
    """
    result = None
    try:
        if service_message["nuropb_type"] not in ("request", "command", "event"):
            raise NuropbHandlingError(
                description=f"Service execution not support for message type {service_message['nuropb_type']}",
                lifecycle="service-handle",
                payload=service_message["nuropb_payload"],
                exception=None,
            )

        """
        correlation_id = service_message["correlation_id"]
        trace_id = service_message["trace_id"]
        """
        payload = service_message["nuropb_payload"]

        if service_message["nuropb_type"] == "event":
            topic = payload["topic"]
            event = payload["event"]
            target = payload["target"]
            context = payload["context"]
            if hasattr(service_instance, "_handle_event_"):
                event_handler = getattr(service_instance, "_handle_event_")
                if callable(event_handler):
                    result = event_handler(topic, event, target, context)
                else:
                    raise NuropbHandlingError(
                        description=f"error calling instance._event_handler for topic: {topic}",
                        lifecycle="service-handle",
                        payload=payload,
                        exception=None,
                    )

        elif service_message["nuropb_type"] in ("request", "command"):
            service_name = payload["service"]
            method_name = payload["method"]
            params = payload["params"]

            """ TODO: think about how to pass the context to the service executing the method
            # context = payload["context"]
            """

            if (
                method_name.startswith("_")
                or not hasattr(service_instance, method_name)
                or not callable(getattr(service_instance, method_name))
            ):
                raise NuropbHandlingError(
                    description="Unknown method {}".format(method_name),
                    lifecycle="service-handle",
                    payload=payload,
                    exception=None,
                )

            try:
                result = getattr(service_instance, method_name)(**params)
            except NuropbException as err:
                if verbose:
                    logger.exception(err)
                raise
            except Exception as err:
                if verbose:
                    logger.exception(err)
                raise NuropbException(
                    description=f"Runtime exception calling {service_name}.{method_name}:{err}",
                    lifecycle="service-handle",
                    payload=payload,
                    exception=err,
                )

        if asyncio.isfuture(result) or asyncio.iscoroutine(result):
            # Asynchronous responses

            if is_future(result):
                raise ValueError(
                    "Tornado Future detected, please use asyncio.Future instead"
                )

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
            # Synchronous responses
            handle_execution_result(service_message, result, message_complete_callback)
    except Exception as err:
        if verbose:
            logger.exception(err)
        handle_execution_result(service_message, err, message_complete_callback)
