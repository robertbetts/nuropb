import logging
from typing import Any, List

from nuropb.interface import NuropbCallAgain, NuropbSuccess, EventType

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
        self._method_call_count += 1
        return f"response from {self._service_name}.test_method"

    async def test_async_method(self, **kwargs: Any) -> str:
        self._method_call_count += 1
        return f"response from {self._service_name}.test_async_method"

    def test_success_error(self, **kwargs: Any) -> str:
        self._method_call_count += 1
        success_result = f"response from {self._service_name}.test_success_error"
        raise NuropbSuccess(
            result=success_result,
        )

    def test_call_again_error(self, **kwargs: Any) -> str:
        self._method_call_count += 1
        success_result = f"response from {self._service_name}.test_call_again_error"
        if self.raise_call_again_error:
            """this is preventing the test from getting into an infinite loop"""
            self.raise_call_again_error = False
            raise NuropbCallAgain("Test Call Again")

    def test_varied_exception(self, **kwargs: Any) -> str:
        self._method_call_count += 1

        success_result = f"response from {self._service_name}.test_method"
        if self._method_call_count % 3 == 0:
            raise NuropbSuccess(
                result=success_result,
            )

        if self._method_call_count % 4 == 0:
            events: List[EventType] = [
                {
                    "topic": "test-event",
                    "payload": {
                        "event_key": "event_value",
                    },
                    "target": [],
                }
            ]
            raise NuropbSuccess(
                result=success_result,
                events=events,
            )

        if self._method_call_count % 2 == 0:
            raise NuropbCallAgain("Test Call Again")

        return success_result
