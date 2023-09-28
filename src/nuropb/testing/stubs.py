import logging
from typing import Any, Dict, Optional
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from uuid import uuid4
import os

from nuropb.contexts.context_manager import NuropbContextManager
from nuropb.contexts.context_manager_decorator import nuropb_context
from nuropb.contexts.describe import publish_to_mesh
from nuropb.interface import NuropbCallAgain, NuropbSuccess

logger = logging.getLogger(__name__)


IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


def get_claims_from_token(bearer_token: str) -> Dict[str, Any] | None:
    """This is a stub for the authorise_func that is used in the tests"""
    _ = bearer_token
    return {
        "sub": "test_user",
        "user_id": "test_user",
        "scope": "openid, profile",
        "roles": "user, admin",
    }


class ServiceStub:
    _service_name: str
    _instance_id: str
    _private_key: rsa.RSAPrivateKey

    def __init__(
            self,
            service_name: str,
            instance_id: Optional[str] = None,
            private_key: Optional[rsa.RSAPrivateKey] = None,
    ):
        self._service_name = service_name
        self._instance_id = instance_id or uuid4().hex
        self._private_key = private_key or rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def private_key(self) -> rsa.RSAPrivateKey:
        return self._private_key


class ServiceExample(ServiceStub):
    _method_call_count: int
    _raise_call_again_error: bool

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._method_call_count = 0
        self._raise_call_again_error = True

    def test_method(self, **kwargs: Any) -> str:
        _ = kwargs
        self._method_call_count += 1
        return f"response from {self._service_name}.test_method"

    async def test_async_method(self, **kwargs: Any) -> str:
        _ = kwargs
        self._method_call_count += 1
        return f"response from {self._service_name}.test_async_method"

    def test_success_error(self, **kwargs: Any) -> None:
        self._method_call_count += 1
        logger.debug(f"test_success_error: {kwargs}")
        success_result = f"response from {self._service_name}.test_success_error"
        raise NuropbSuccess(
            result=success_result,
        )

    @nuropb_context
    @publish_to_mesh(authorise_func=get_claims_from_token)
    def test_requires_user_claims(self, ctx: NuropbContextManager, **kwargs: Any) -> Any:
        assert isinstance(self, ServiceExample)
        assert isinstance(ctx, NuropbContextManager)
        self._method_call_count += 1
        logger.debug(f"test_requires_user_claims: {kwargs}")
        return ctx.user_claims

    @nuropb_context
    @publish_to_mesh(authorise_func=get_claims_from_token, requires_encryption=True)
    def test_requires_encryption(self, ctx: NuropbContextManager, **kwargs: Any) -> Any:
        assert isinstance(self, ServiceExample)
        assert isinstance(ctx, NuropbContextManager)
        self._method_call_count += 1
        logger.debug(f"test_requires_encryption: {kwargs}")
        return "Result that's to be encrypted in transit"

    def test_call_again_error(self, **kwargs: Any) -> Dict[str, Any]:
        self._method_call_count += 1
        logger.debug(f"test_call_again_error: {kwargs}")
        success_result = f"response from {self._service_name}.test_call_again_error"
        if self._raise_call_again_error:
            """this is preventing the test from getting into an infinite loop"""
            self._raise_call_again_error = False
            raise NuropbCallAgain("Test Call Again")
        result = kwargs.copy()
        result.update(
            {
                "success": success_result,
                "count": self._method_call_count,
            }
        )
        return result

    def test_call_again_loop(self, **kwargs: Any) -> None:
        self._method_call_count += 1
        logger.debug(f"test_call_again_error very time: {kwargs}")
        raise NuropbCallAgain("Test Call Again")
