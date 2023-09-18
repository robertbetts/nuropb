import logging
from typing import List
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from nuropb.contexts.describe import publish_to_mesh
from nuropb.interface import NuropbException, NuropbSuccess, NuropbCallAgain, EventType


logger = logging.getLogger()


class ServiceExample:
    _service_name: str
    _private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    _instance_id: str
    _method_call_count: int

    def __init__(self, service_name: str, instance_id: str):
        self._service_name = service_name
        self._instance_id = instance_id
        self._method_call_count = 0

    @classmethod
    def _handle_event_(
        cls,
        topic: str,
        event: dict,
        target: list[str] | None = None,
        context: dict | None = None,
        trace_id: str | None = None,
    ) -> None:
        _ = target, context, trace_id
        logger.debug(f"Received event {topic}:{event}")

    @publish_to_mesh(requires_encryption=True)
    def test_method(self, **kwargs) -> str:
        self._method_call_count += 1

        success_result = f"response from {self._service_name}.test_method"

        if self._method_call_count % 400 == 0:
            events: List[EventType] = [
                {
                    "topic": "test-event",
                    "encoded_payload": {
                        "event_key": "event_value",
                    },
                    "target": [],
                }
            ]
            raise NuropbSuccess(
                result=success_result,
                events=events,
            )

        if self._method_call_count % 200 == 0:
            raise NuropbSuccess(
                result=success_result,
            )

        if self._method_call_count % 100 == 0:
            raise NuropbCallAgain("Test Call Again")

        return success_result

    async def test_async_method(self, **kwargs) -> str:
        self._method_call_count += 1
        return f"response from {self._service_name}.test_async_method"

    async def async_method(self, **kwargs) -> int:
        self._method_call_count += 1
        return self._method_call_count

    def sync_method(self, **kwargs) -> int:
        self._method_call_count += 1
        return self._method_call_count

    def method_with_exception(self, **kwargs) -> None:
        raise Exception("Test sync exception")

    def async_method_with_exception(self, **kwargs) -> None:
        raise Exception("Test async method exception")

    def method_with_nuropb_exception(self, **kwargs) -> None:
        raise NuropbException("Test Nuropb Exception")
