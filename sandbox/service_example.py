import logging

from nuropb.interface import NuropbException

logger = logging.getLogger()


class ServiceExample:
    _service_name: str
    _instance_id: str
    _method_call_count: int

    def __init__(self, service_name: str, instance_id: str):
        self._service_name = service_name
        self._instance_id = instance_id
        self._method_call_count = 0

    def test_method(self, **kwargs) -> str:
        self._method_call_count += 1
        return f"response from {self._service_name}.test_method"

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




