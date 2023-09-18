import logging
import pytest
from typing import Dict, Any

from nuropb.contexts.context_manager import NuropbContextManager
from nuropb.contexts.context_manager_decorator import nuropb_context

logger = logging.getLogger(__name__)


class TestServiceClass:
    _service_name: str

    def hello_no_context(self, param1: str) -> str:  # pragma: no cover
        _ = self
        return f"hello {param1}"

    def hello_with_context(self, ctx: Dict[str, Any], param1: str) -> str:
        _ = self
        return f"from {ctx['user_id']}, hello {param1}"

    @nuropb_context
    def hello_with_context_decorator(
        self, ctx: NuropbContextManager, param1: str
    ) -> str:
        _ = self
        return f"from {ctx.context['user_id']}, hello {param1}"


@pytest.fixture(scope="function")
def context():
    return {
        "user_id": "test_user_id",
        "session_id": "test_session_id",
        "Authorisation": "Bearer: authorisation_token",
    }


@pytest.fixture(scope="function")
def instance():
    return TestServiceClass()


def test_declaring_decorator_on_class_method():
    """Using the decorator on a class method with no ctx parameter should raise a TypeError"""
    with pytest.raises(TypeError):

        class ServiceClass:
            _service_name: str

            @nuropb_context
            def hello_with_context(self, param1: str) -> str:
                _ = self, param1  # pragma: no cover

    """ the same test when specifying an alternate the ctx parameter name must also raise a TypeError
    """
    with pytest.raises(TypeError):

        class ServiceClass:
            _service_name: str

            @nuropb_context(context_parameter="context")
            def hello_with_context(self, ctx, param1: str) -> str:  # pragma: no cover
                _ = self, ctx, param1


def test_nuropb_with_context_and_decorator_no_injection(context, instance):
    params = {
        "param1": "world",
    }
    with pytest.raises(TypeError):
        result = instance.hello_with_context_decorator(**params)


def test_nuropb_context(context, instance):
    params = {
        "param1": "world",
    }
    ctx = NuropbContextManager(context=context)
    with pytest.raises(TypeError):
        result = instance.hello_no_context(ctx, **params)

    """ NOTE: the caller of instance.method() is responsible for passing the context
    which can either be a dictionary or a NuropbContextManager instance. if a dictionary
    is passed, a NuropbContextManager instance will be created from the dictionary and
    passed to the method.
    """

    """ Test with NuropbContextManager context injection and method has no decorator
    """
    with pytest.raises(TypeError):
        result = instance.hello_with_context(ctx, **params)

    """ Test with dictionary context injection and method has no decorator and params contains
    a ctx parameter as would be expected.
    """
    params = {
        "param1": "world",
        "ctx": {"key": "value"},
    }
    ctx = context
    with pytest.raises(TypeError):
        result = instance.hello_with_context(ctx, **params)


def test_nuropb_context_decorator(context, instance):
    params = {
        "param1": "world",
    }
    ctx = context
    result = instance.hello_with_context_decorator(ctx, **params)
    assert result == "from test_user_id, hello world"

    ctx = NuropbContextManager(context=context)
    result = instance.hello_with_context_decorator(ctx, **params)
    assert result == "from test_user_id, hello world"
