from typing import Optional

from uuid import uuid4

from nuropb.interface import RequestPayloadDict, ResponsePayloadDict


def execute_request(service_instance: object, request: RequestPayloadDict) -> Optional[ResponsePayloadDict]:
    """ execute request and return response
    :param service_instance:
    :param request: RequestPayloadDict
    :return: ResponsePayloadDict
    """
    result = f"expected response from {request['service']}.{request['method']}"
    correlation_id = uuid4().hex
    response = ResponsePayloadDict(
        result=result,
        error=None,
        correlation_id=correlation_id,
        trace_id=request["trace_id"],
        context=request["context"],
    )
    return response


    start_time = time.time()
    nuro_type = message["tag"]
    method_name = message["method"]
    params = message["params"]
    context = message["context"]
    trace_id = message["trace_id"]
    req_slug = "method: {} ( trace_id: {} correlation_id: {} )".format(
        method_name,
        trace_id,
        message.correlation_id
    )
    logger.debug('handling %s' % req_slug)

    try:
        if method_name.startswith("_") or \
                not hasattr(self.service, method_name) or \
                not callable(getattr(self.service, method_name)):
            raise SailProcessError("Unable to call method {}".format(method_name), message)

        if self.service.validate_auth_key(auth_key, method_name):
            result = getattr(self.service, method_name)(**params)
        else:
            raise SailAuthenticationError("Authentication failed calling method {}".format(method_name))

        # Check if response is a tornado.concurrent.Future or asyncio.Coroutine
        if is_future(result) or asyncio.iscoroutine(result):
            return transformed_async_future(
                result,
                start_time,
                req_slug
            )
        else:
            elapsed_time = time.time() - start_time
            logger.debug('Request finished {} in {}s'.format(req_slug, elapsed_time))
            return SailResponse(result, None)

    except Exception as e:
        logger.warning("Error handling service request %s: %s", req_slug, e)
        logger.exception(e)
    return SailResponse(None, str(e))