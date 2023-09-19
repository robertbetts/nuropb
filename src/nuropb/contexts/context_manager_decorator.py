import inspect
from typing import Optional, Any, Callable
from functools import wraps

from nuropb.contexts.context_manager import NuropbContextManager


def method_requires_nuropb_context(method: Callable[..., Any]) -> bool:
    """This function checks if a method has been decorated with @nuropb_context
    :param method: Callable
    :return: bool
    """
    return getattr(method, "__nuropb_context__", False)


def nuropb_context(
    original_method: Optional[Callable[..., Any]] = None,
    *,
    context_parameter: str = "ctx",
    suppress_exceptions: bool = False,
) -> Any:
    """This decorator function injects a NuropbContext instance into a method that has ctx:NuropbContext
    as an argument. The ctx parameter of the decorated method is hidden from the method's signature visible
    on the service mesh.

    The name of the ctx parameter can be changed by passing a string to the context_parameter argument.

    The caller of class_instance.method(ctx=ctx) can either pass a NuropbContext instance or a dict. If a dict
    is passed, a NuropbContext instance will be created from the dict.

    *NOTE* This decorator is only for with class methods, using with functions will have unexpected
    results and is likely to raise a TypeException

    As illustrated by the example below, @nuropb_context must always be on top of @publish_to_mesh when
    both decorators are used.

        @nuropb_context
        @publish_to_mesh(context_token_key="Authorization", authorise_func=authorise_token)
        def hello_requires_auth(...)


    :param original_method: the method to be decorated
    :param context_parameter: str
    :param suppress_exceptions: bool
    :return: a decorated method
    """
    context_parameter = context_parameter or "ctx"
    suppress_exceptions = False if suppress_exceptions is None else suppress_exceptions

    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        if context_parameter not in inspect.signature(method).parameters:
            raise TypeError(
                f"method {method.__name__} does not have {context_parameter} as an argument"
            )

        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """validate calling arguments"""
            if len(args) < 2 or not isinstance(args[1], (NuropbContextManager, dict)):
                raise TypeError(
                    f"The @nuropb_context, expects a {context_parameter}: NuropbContextManager "
                    f"or dict, as the first argument in calling instance.method"
                )
            method_args = list(args)
            ctx = method_args[1]
            if not isinstance(ctx, NuropbContextManager):
                """Replace dictionary context with NuropbContextManager instance"""
                ctx = NuropbContextManager(
                    context=method_args[1],
                    suppress_exceptions=suppress_exceptions,
                )
                method_args[1] = ctx

            authorise_func = getattr(wrapper, "__nuropb_authorise_func__", None)
            if authorise_func is not None:
                context_token_key = getattr(wrapper, "__nuropb_context_token_key__")
                ctx.user_claims = authorise_func(ctx.context[context_token_key])

            # kwargs[context_parameter] = ctx
            # return method(*args[1:], **kwargs)
            return method(*method_args, **kwargs)

        setattr(wrapper, "__nuropb_context__", True)
        setattr(wrapper, "__nuropb_context_arg__", context_parameter)
        return wrapper

    if original_method:
        return decorator(original_method)
    else:
        return decorator
