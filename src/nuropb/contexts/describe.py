import logging
import inspect
from typing import Optional, Any, get_origin, get_args, Callable, Dict, Tuple
from functools import wraps
from cryptography.hazmat.primitives import serialization


logger = logging.getLogger(__name__)

AuthoriseFunc = Callable[[str], Dict[str, Any]]


def method_visible_on_mesh(method: Callable[..., Any]) -> bool:
    """This function checks if a method has been decorated with @publish_to_mesh
    :param method: callable
    :return: bool
    """
    return getattr(method, "__nuropb_mesh_visible__", False)


def publish_to_mesh(
    original_method: Optional[Callable[..., Any]] = None,
    *,
    hide_method: Optional[bool] = False,
    authorise_func: Optional[AuthoriseFunc] = None,
    context_token_key: Optional[str] = "Authorization",
    requires_encryption: Optional[bool] = False,
    description: Optional[str] = None,
) -> Any:
    """Decorator to expose class methods to the service mesh

    When a service instance is connected to a service mesh via the service mesh client, all
    the standard public methods of the service instance is available to the service mesh. Methods
    that start with underscore will always remain hidden. methods that are explicitly marked as
    hidden by publish_to_mesh will also not be published.

    When and authorise_func is specified, this function will be called with the contents of
    context[context_token_key]. if the token validation is unsuccessful, then a failed authorisation
    exception is raised. If successful then ctx.user_claims is populated with claims attached to the
    token.

    When requires_encryption is True, the service mesh will encrypt the payload of the service message
    request and response. It is the responsibility of the process making the request to ensure that
    it has the target service's public key.

    As illustrated by the example below, @nuropb_context must always be on top of @publish_to_mesh when
    both decorators are used.

        @nuropb_context
        @publish_to_mesh(context_token_key="Authorization", authorise_func=authorise_token)
        def hello_requires_auth(...)


    :param original_method:
    :param hide_method:
    :param authorise_func:
    :param context_token_key:
    :param requires_encryption:
    :param description: str, if present then override the methods doc string
    :return:
    """
    hide_method = False if hide_method is None else hide_method
    context_token_key = (
        "Authorization" if context_token_key is None else context_token_key
    )
    if authorise_func is not None and not callable(authorise_func):
        raise TypeError("Authorise function must be callable")
    requires_encryption = False if requires_encryption is None else requires_encryption

    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return method(*args, **kwargs)

        setattr(wrapper, "__nuropb_mesh_hidden__", hide_method)
        setattr(wrapper, "__nuropb_context_token_key__", context_token_key)
        setattr(wrapper, "__nuropb_authorise_func__", authorise_func)
        setattr(wrapper, "__nuropb_requires_encryption__", requires_encryption)
        if description:
            setattr(wrapper, "__nuropb_description__", description)
        return wrapper

    if original_method:
        return decorator(original_method)
    else:
        return decorator


def describe_service(class_instance: object) -> Dict[str, Any] | None:
    """Returns a description of the class methods that will be exposed to the service mesh"""
    if class_instance is None:
        logger.warning("No service class base has been input")
        return None
    else:
        service_name = getattr(class_instance, "_service_name", None)
        service_description = getattr(class_instance, "__doc__", None)
        service_description = (
            service_description.strip() if service_description else service_description
        )
        service_version = getattr(class_instance, "_version", None)
        methods = []
        service_has_encrypted_methods = False

        for name, method in inspect.getmembers(class_instance):
            """all private methods are excluded, regardless if one has been decorated with @publish_to_mesh"""
            if name[0] == "_" or not callable(method):
                continue

            if getattr(method, "__nuropb_mesh_hidden__", False):
                continue

            requires_encryption = getattr(
                method, "__nuropb_requires_encryption__", False
            )
            if requires_encryption:
                service_has_encrypted_methods = True

            ctx_arg_name = getattr(method, "__nuropb_context_arg__", "ctx")
            method_signature = inspect.signature(method)
            required = []

            def map_annotation(arg_props: Any) -> str:
                annotation = arg_props.annotation
                label = ""
                if annotation != inspect._empty:
                    origin = get_origin(annotation)
                    if origin is not None:
                        args = [
                            a
                            for a in get_args(annotation)
                            if a.__name__ not in ("NoneType",)
                        ]
                        if len(args) == 1:
                            label = args[0].__name__

                    else:
                        label = annotation.__name__
                return label

            def map_default(arg_props: Any) -> Any:
                default = arg_props.default
                if default == inspect._empty:
                    required.append(arg_props.name)
                    return ""
                else:
                    return default

            def map_argument(arg_props: Any) -> Tuple[str, Dict[str, Any]]:
                return (
                    arg_props.name,
                    {
                        "type": map_annotation(arg_props),
                        "description": "",
                        "default": map_default(arg_props),
                    },
                )

            properties = [
                map_argument(p)
                for n, p in method_signature.parameters.items()
                if n not in ("self", "cls", ctx_arg_name)
            ]

            method_spec = {
                "description": getattr(
                    method, "__nuropb_description__", inspect.getdoc(method)
                ),
                "requires_encryption": requires_encryption,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            }
            methods.append((name, method_spec))

        service_info = {
            "service_name": service_name,
            "service_version": service_version,
            "description": service_description,
            "encrypted_methods": service_has_encrypted_methods,
            "methods": dict(methods),
        }

        if service_has_encrypted_methods:
            private_key = service_name = getattr(class_instance, "_private_key", None)
            if private_key is None:
                raise ValueError(
                    f"Service {service_name} has encrypted methods but no private key has been set"
                )

            service_info["public_key"] = (
                private_key.public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                .decode("ascii")
            )

        return service_info
