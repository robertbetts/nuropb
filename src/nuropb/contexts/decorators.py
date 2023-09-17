import inspect
from typing import Optional, Any
from functools import wraps

from nuropb.contexts.context_manager import NuropbContextManager


def nuropb_context(
        original_method=None,
        *,
        context_parameter: Optional[str] = "ctx",
        suppress_exceptions: Optional[bool] = False,
        authorise_key: Optional[str] = None,
        authorise_func: Optional[callable] = None,
) -> Any:
    """ This decorator function injects a NuropbContext instance into a method that has ctx:NuropbContext
    as an argument. The ctx parameter of the decorated method is hidden from the method's signature visible
    on the service mesh.

    The name of the ctx parameter can be changed by passing a string to the context_parameter argument.

    The caller of class_instance.method(ctx=ctx) can either pass a NuropbContext instance or a dict. If a dict
    is passed, a NuropbContext instance will be created from the dict.

    *NOTE* This decorator is only for with class methods, using with functions will have unexpected
    results and is likely to raise a TypeException

    :param original_method: the method to be decorated
    :param context_parameter: str
    :param suppress_exceptions: bool
    :param authorise_key: str
    :param authorise_func: callable(token: str) -> dict
    :return: a decorated method
    """
    context_parameter = "ctx" if context_parameter is None else context_parameter
    suppress_exceptions = False if suppress_exceptions is None else suppress_exceptions

    def decorator(method):
        if context_parameter not in inspect.signature(method).parameters:
            raise TypeError(
                f"method {method.__name__} does not have {context_parameter} as an argument"
            )

        @wraps(method)
        def wrapper(*args, **kwargs):
            """ validate calling arguments
            """
            if len(args) < 2 or not isinstance(args[1], (NuropbContextManager, dict)):
                raise TypeError(
                    f"The @nuropb_context, expects a {context_parameter}: NuropbContextManager "
                    f"or dict, as the first argument in calling instance.method"
                )
            context = args[1]
            if isinstance(context, NuropbContextManager):
                ctx = context
            else:
                ctx = NuropbContextManager(
                    context=context,
                    suppress_exceptions=suppress_exceptions,
                )
            if authorise_key is not None and authorise_func is not None:
                ctx.user_claims = authorise_func(ctx.context[authorise_key])
            kwargs[context_parameter] = ctx
            return method(*args[1:], **kwargs)

        return wrapper

    if original_method:
        return decorator(original_method)
    else:
        return decorator

