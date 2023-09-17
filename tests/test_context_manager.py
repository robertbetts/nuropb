import logging
import pytest
from typing import Any, Dict
import asyncio

from nuropb.contexts.context_manager import NuropbContextManager


logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def context():
    return {
        "user_id": "test_user_id",
        "session_id": "test_session_id",
    }


@pytest.fixture(scope="function")
def ctx(context):
    return NuropbContextManager(context=context)


def test_initialise_context_manager(context):
    """ Test that we can initialise a context manager with a context dict
    """
    ctx = NuropbContextManager(context=context)
    assert ctx.context == context
    assert ctx.events == []

    with pytest.raises(TypeError):
        ctx = NuropbContextManager(context=None)


def test_cm_add_events(context):
    ctx = NuropbContextManager(context=context)
    ctx.add_event({
        "topic": "test_topic",
        "event": "test_event_payload",
        "context": context
    })
    compare_event = {
        "topic": "test_topic",
        "event": "test_event_payload",
        "context": context
    }
    assert ctx.events == [compare_event]


def test_cm_with_happy_path(ctx):
    with ctx as context:
        context.add_event({
            "topic": "test_topic",
            "event": "test_event_payload",
            "context": context
        })
    assert len(ctx.events) == 1
    assert ctx.error is None


def test_cm_with_happy_error(ctx):
    with ctx as context:
        1 / 0

    assert len(ctx.events) == 0


def test_cm_with_suppress_exception_false(context):
    ctx = NuropbContextManager(context=context, suppress_exceptions=False)
    with pytest.raises(ZeroDivisionError):
        with ctx as context:
            1 / 0


@pytest.mark.asyncio
async def test_cm_with_suppress_exception_false_async():
    ctx = NuropbContextManager(context={}, suppress_exceptions=False)
    with pytest.raises(ZeroDivisionError):
        async with ctx as context:
            1 / 0
    assert ctx.error["error"] == "ZeroDivisionError"
    assert ctx.error["description"] == "division by zero"


