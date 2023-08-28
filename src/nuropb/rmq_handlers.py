import asyncio
from typing import Any, Awaitable, Dict, Union, Type
import time
import logging

from tornado.concurrent import is_future

from nuropb.interface import (
    RequestPayloadDict,
    CommandPayloadDict,
    ResponsePayloadDict,
    NuropbHandlingError,
    NuropbDeprecatedError,
    NuropbAuthenticationError,
    NuropbAuthorizationError,
    NuropbValidationError,
    PayloadDict,
    NuropbException,
)

logger = logging.getLogger()


def transformed_async_future(
    result_future, start_time, payload: Union[RequestPayloadDict, CommandPayloadDict]
) -> Awaitable[ResponsePayloadDict]:
    """Handle the result of the future in order to return a NuropbResponse. Provides support for
    asyncio Coroutines return by awaiting an async def function. result_future is converted to a Task
    to provide compatibility with the Tornado IOLoop

    PLEASE NOTE: At first glance awaitable nature of the result_future is not obvious from the code. Make
    sure you familiarise yourself with the asynchronous code flow and understand how the result_future is
    handled before making any changes.

    FYI - the calling code for execute_request() and which deals with the result_future is in rmq_transport.py

    :return: asyncio.Future()
    """
    transformed_future = asyncio.Future()

    def _handle_future_result(completed_future) -> None:
        """This function will only be called when result_future is done"""
        elapsed_time = time.time() - start_time
        logger.debug(f"Asynchronous service call completed in {elapsed_time}s\n")
        exception = completed_future.exception()
        result: Any = None
        error: Dict[str, Any] | None = None
        if not exception:
            result = completed_future.result()
        else:
            error = {"error": type(exception).__name__, "details": str(exception)}
        context = payload["context"]
        context.update(
            {
                "service": payload["service"],
                "method": payload["method"],
                "elapsed_time": elapsed_time,
            }
        )
        response = ResponsePayloadDict(
            tag="response",
            result=result,
            error=error,
            correlation_id=payload["correlation_id"],
            trace_id=payload["trace_id"],
            context=context,
            warning=None,
        )

        transformed_future.set_result(response)

    """ Provides support for asyncio Coroutines return by awaiting an async def function. 
    This is converted to a Task to provide compatibility with the Tornado IOLoop 
    """
    if asyncio.iscoroutine(result_future):
        result_future = asyncio.create_task(result_future)

    result_future.add_done_callback(_handle_future_result)

    return transformed_future


def execute_request(
    service_instance: object, payload: RequestPayloadDict
) -> Union[None, ResponsePayloadDict, Awaitable[ResponsePayloadDict]]:
    """Executes request and returns the handled response

    PLEASE NOTE: At first glance awaitable nature of the result_future is not obvious from the code. read the
    comments in transformed_async_future() to understand how the result_future is handled before making any changes.

    FYI -  the calling code for execute_request() and which deals with the result_future is in rmq_transport.py

    :param service_instance:
    :param payload:
    :return: None | ResponsePayloadDict | Awaitable[ResponsePayloadDict]
    """
    start_time = time.time()
    method_name = payload["method"]
    params = payload["params"]
    context = payload["context"]
    correlation_id = payload["correlation_id"]
    trace_id = payload["trace_id"]
    req_slug = f"method: {method_name} ( trace_id: {trace_id} correlation_id: {correlation_id} )"
    logger.debug("handling %s" % req_slug)

    if (
        method_name.startswith("_")
        or not hasattr(service_instance, method_name)
        or not callable(getattr(service_instance, method_name))
    ):
        raise NuropbHandlingError(
            message="Unknown method {}".format(method_name),
            lifecycle="service-handle",
            payload=payload,
            exception=None,
        )

    result: Any = None
    try:
        # TODO: check if method is deprecated
        # TODO: check user authentication and authorisation
        # TODO: method validation (params, context)
        # TODO: wrap within a context manager
        result = getattr(service_instance, method_name)(**params)
    except NuropbException as nuropb_error:
        logging.exception(nuropb_error)
        raise nuropb_error

    # Check if response is a tornado.concurrent.Future or asyncio.Coroutine
    if is_future(result) or asyncio.iscoroutine(result):
        return transformed_async_future(result, start_time, payload)
    else:
        elapsed_time = time.time() - start_time
        logger.debug("Request finished {} in {}s".format(req_slug, elapsed_time))
        response = ResponsePayloadDict(
            tag="response",
            result=result,
            error=None,
            correlation_id=correlation_id,
            trace_id=trace_id,
            context=context,
            warning=None,
        )
        return response
