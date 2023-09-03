import logging
from uuid import uuid4
import asyncio

import pytest

from nuropb.interface import ResponsePayloadDict, RequestPayloadDict, NUROPB_PROTOCOL_VERSION, TransportServicePayload
from nuropb.service_handlers import execute_request

logger = logging.getLogger()

@pytest.mark.asyncio
def test_sync_handler_call(service_instance, event_loop):
    correlation_id = uuid4().hex
    trace_id = uuid4().hex
    request_payload: RequestPayloadDict = {
        "tag": "request",
        "context": {},
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "service": "test_service",
        "method": "test_method",
        "params": {"param1": "value1"},
        "reply_to": None,
    }
    transport_request = TransportServicePayload(
        nuropb_protocol=NUROPB_PROTOCOL_VERSION,
        nuropb_type="request",
        nuropb_payload=request_payload,
        correlation_id=correlation_id,
        trace_id=trace_id,
        ttl=None,
    )

    def future_done(responses, acknowledge):
        logger.info(f"response_result: {responses}")
        # assert response["result"] == f"response from {request_payload['service']}.{request_payload['method']}"
        # assert isinstance(response["result"], str)

    execute_request(
        service_instance,
        transport_request,
        future_done)


@pytest.mark.asyncio
async def test_async_handler_call_step_one(service_instance, event_loop):
    correlation_id = uuid4().hex
    trace_id = uuid4().hex
    request_payload: RequestPayloadDict = {
        "tag": "request",
        "context": {},
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "service": "test_service",
        "method": "test_async_method",
        "params": {"param1": "value1"},
        "reply_to": "",
    }
    transport_request = TransportServicePayload(
        nuropb_protocol=NUROPB_PROTOCOL_VERSION,
        nuropb_type="request",
        nuropb_payload=request_payload,
        correlation_id=correlation_id,
        trace_id=trace_id,
        ttl=None,
    )

    def future_done(responses, acknowledge):
        logger.info(f"response_result: {responses}")
        # assert response_result == f"response from {request_payload['service']}.{request_payload['method']}"
        wait_for_test.set_result(responses)

    wait_for_test = asyncio.Future()
    execute_request(
        service_instance,
        transport_request,
        future_done
    )
    test_result = await wait_for_test
    # assert test_result == f"response from {request_payload['service']}.{request_payload['method']}"

