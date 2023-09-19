import logging
from types import TracebackType
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)

_test_token_cache: Dict[str, Any] = {}
_test_user_id_cache: Dict[str, Any] = {}


class NuropbContextManager:
    """This class is a context manager that can be used to manage the context transaction relating
    to an incoming nuropb service message. when a class instance method is decorated with the
    nuropb_context decorator, the context manager is instantiated and injected into the method
    as a ctx parameter.

    The nuropb context manager is both a sync and async context manager, it also provides access
    to a decorated method to the nuropb service mesh api. Events can be added to the context
    manager and will be sent to the service mesh when the context manager exits. If an exception
    is raised while the context manager is running, the exception is recorded and the context
    transaction is considered to have failed. If any events were added to the context manager,
    they are discarded.
    """

    _suppress_exceptions: bool
    _nuropb_payload: Dict[str, Any] | None
    _context: Dict[str, Any]
    _user_claims: Dict[str, Any] | None
    _events: List[Dict[str, Any]]
    _exc_type: Type[BaseException] | None
    _exec_value: BaseException | None
    _exc_tb: TracebackType | None
    _started: bool
    _done: bool

    def __init__(
        self, context: Dict[str, Any], suppress_exceptions: Optional[bool] = True
    ):
        if context is None:
            raise TypeError("context cannot be None")
        self._suppress_exceptions = (
            True if suppress_exceptions is None else suppress_exceptions
        )
        self._nuropb_payload = None
        self._context = context
        self._user_claims = None
        self._events = []

        self._exc_type = None
        self._exec_value = None
        self._exc_tb = None
        self._started = False
        self._done = False

    @property
    def context(self) -> Dict[str, Any]:
        return self._context

    @property
    def user_claims(self) -> Dict[str, Any] | None:
        return self._user_claims

    @user_claims.setter
    def user_claims(self, claims: Dict[str, Any] | None) -> None:
        if self._user_claims is not None:
            raise ValueError("user_claims can only be set once")
        self._user_claims = claims

    @property
    def events(self) -> List[Dict[str, Any]]:
        return self._events

    @property
    def error(self) -> Dict[str, Any] | None:
        if self._exc_type is None:
            return None
        return {
            "error": self._exc_type.__name__,
            "description": str(self._exec_value),
        }

    def add_event(self, event: Dict[str, Any]) -> None:
        """Add an event to the context manager. The event will be sent to the service mesh when
        the context manager exits successfully.

        Event format:
        {
            "topic": "test_topic",
            "event": "test_event_payload",
            "context": {}
        }

        :param event:
        :return:
        """
        self._events.append(event)

    def _handle_context_exit(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """This method is for customising the behaviour when a context manager exits. It has the
        same signature as __exit__ or __aexit__.

        If an exception was raised while the context manager was running, the exception information
        is recorded and content transaction is considered to have failed. If any events were added
        to the context manager, they are discarded.
        """
        if self._done:
            raise RuntimeError("Context manager has already exited")
        self._done = True
        self._exc_type = exc_type
        self._exec_value = exc_value
        self._exc_tb = exc_tb

        if exc_type is not None:
            self._events = []

        return self._suppress_exceptions

    """ 
        **** Context Manager sync and async methods ****
    """

    def __enter__(self) -> Any:
        """This method is called when entering a context manager with a with statement"""
        if self._done:
            raise RuntimeError("Context manager has already exited")
        if self._started:
            raise RuntimeError("Context manager has already entered")
        self._started = True

        return self

    async def __aenter__(self) -> Any:
        return self.__enter__()

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self._handle_context_exit(exc_type, exc_value, exc_tb)

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self.__exit__(exc_type, exc_value, exc_tb)
