import logging
import pytest
from typing import Dict, Any
import datetime

from nuropb.contexts.context_manager import NuropbContextManager
from nuropb.contexts.context_manager_decorator import nuropb_context
from nuropb.contexts.describe import publish_to_mesh

logger = logging.getLogger(__name__)


def authorise_token(token: str) -> Dict[str, Any]:
    _ = token
    return {
        "user_id": "test_user_id",
        "expiry": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=1),
        "scope": "openid profile",
        "roles": ["test_role1", "test_role2"],
    }


class AuthoriseServiceClass:
    _service_name: str

    @nuropb_context
    @publish_to_mesh(context_token_key="Authorization", authorise_func=authorise_token)
    def hello_requires_auth(
        self, ctx: NuropbContextManager, param1: str
    ) -> Dict[str, Any]:
        _ = self
        claims = ctx.user_claims
        return {
            "context": ctx.context["user_id"],
            "claims": claims,
        }


@pytest.fixture(scope="function")
def context():
    return {
        "user_id": "test_user_id",
        "session_id": "test_session_id",
        "Authorization": "Bearer: authorisation_token",
    }


@pytest.fixture(scope="function")
def instance():
    return AuthoriseServiceClass()


def test_declaring_decorator_on_class_method(instance, context):
    """Using the decorator on a class method with no ctx parameter should raise a TypeError"""
    ctx = NuropbContextManager(context=context, suppress_exceptions=False)

    result = instance.hello_requires_auth(ctx, param1="test_param1")
    assert isinstance(result["claims"], dict)
    assert result["claims"]["user_id"] == "test_user_id"
    assert result["claims"]["scope"] == "openid profile"
    assert result["claims"]["roles"] == ["test_role1", "test_role2"]
