import logging
from typing import Any, Dict

from nuropb.interface import NuropbCallAgain, NuropbSuccess

logger = logging.getLogger(__name__)


class ServiceExample:
    _service_name: str
    _instance_id: str
    _method_call_count: int

    def __init__(self, service_name: str, instance_id: str):
        self._service_name = service_name
        self._instance_id = instance_id
        self._method_call_count = 0
        self.raise_call_again_error = True

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

    def test_call_again_error(self, **kwargs: Any) -> Dict[str, Any]:
        self._method_call_count += 1
        logger.debug(f"test_call_again_error: {kwargs}")
        success_result = f"response from {self._service_name}.test_call_again_error"
        if self.raise_call_again_error:
            """this is preventing the test from getting into an infinite loop"""
            self.raise_call_again_error = False
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
