# Discovery and Context Management

## NuroPb Context Manager and Decorator
When a service instance method is decorated with @nuropb_context, a NuropbContextManager instance will
be injected into the method, and usually into an argument named ctx. This context manager is callable
via the `with` statement. Once the context manager has exited, it is considered done and 
immutable.

### @nuropb_context
```python
def nuropb_context(
    original_method=None,
    *,
    context_parameter: Optional[str] = "ctx",
    suppress_exceptions: Optional[bool] = False,
    authorise_key: Optional[str] = None,
    authorise_func: Optional[callable] = None,
) -> Any:
    """
    :param context_parameter: str, (ctx) alternative context argument name
    :param suppress_exceptions: bool, (True), if False then exceptions will be raised during `with ctx:`      
    """
```
This decorator function injects a NuropbContext instance into a method that has ctx:NuropbContext
as an argument. The ctx parameter of the decorated method is hidden from the method's signature 
visible on the service mesh.

**NOTE:** This decorator is intended only for class methods, using it with functions will have
unexpected results and is likely to result in either and compile time or runtime exception.

This decorator if used in conjunction with the @publish_to_mesh decorator, must be applied after.
```python
    @nuropb_context
    @publish_to_mesh(authorise_func=get_claims_from_token, requires_encryption=True)
    def test_requires_encryption(self, ctx: NuropbContextManager, **kwargs: Any) -> Any:
        ...
```
The name of the ctx parameter can be changed by entering and alternative name using the 
context_parameter argument.
```python
    @nuropb_context
    @publish_to_mesh(authorise_func=get_claims_from_token, requires_encryption=True, context_parameter="myctx")
    def test_requires_encryption(self, myctx: NuropbContextManager, **kwargs: Any) -> Any:
        ...
```

Any caller of class_instance.method(ctx=ctx) can either pass a NuropbContext instance or a dict. 
If a dict is passed, a NuropbContext instance will be created from the dict and injected into
the method.


## Service Mesh Configuration Decorator

When wrapping a class with the nuropb service mesh api, all public methods are made available to all participants 
connected to the service mesh.  Any participant can request a service specification from any service, and will 
receive a json object describing the service and its methods.

### @nuropb_context
```python
def publish_to_mesh(
        original_method: Optional[Callable[..., Any]] = None,
        *,
        hide_method: Optional[bool] = False,
        authorize_func: Optional[AuthorizeFunc] = None,
        context_token_key: Optional[str] = "Authorization",
        requires_encryption: Optional[bool] = False,
        description: Optional[str] = None,
) -> Any:
    """
    :param hide_method: bool, (False) if True then the method will not be published to the service mesh
    :param authorize_func: callable(token: str) -> dict
    :param context_token_key: str, ("Authorization"), incoming request context key containing the bearer token
    :param requires_encryption: bool, (False) if True then the service mesh expect and encrypted payload
    :param description: str, if present then override the methods doc string
    """
```

Example Mesh Service Describe Information:
```python
{
    "service_name": "order_management_service",
    "service_version": "0.1.0",
    "description": "A service the manages orders",
    "warnings": [],
    "encrypted_methods": [],
    "public_key": None,
    "methods": [
        {
            "name": "create_order",
            "description": (
                "Create an order for a given security, quantity, side and order_type. Order price input is dependant "
                "on order_type and if a date is not given the current date is used, dates prior to today will be "
                "rejected by the API."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "account": {
                        "type": "string",
                        "description": "The account into which the executed trade will be booked",
                    },
                    "security": {
                        "type": "string",
                        "description": "the security to be traded",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["Open", "Filled", "Cancelled"],
                        "description": "The status of the order.",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "the quantity to be traded",
                    },
                    "side": {
                        "type": "string",
                        "enum": ["Buy", "Sell"],
                        "description": "The side of the order",
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["Market", "Limit", "Stop"],
                        "description": "The order type",
                    },
                    "price": {
                        "type": "number",
                        "description": "The price of the order",
                    },
                    "time_in_force": {
                        "type": "string",
                        "enum": ["Day", "GTC", "FOK", "IOC"],
                        "description": "The time in force of the order",
                    },
                    "stop_price": {
                        "type": "number",
                        "description": "The stop price of the order",
                    },
                    "order_date": {
                        "type": "string",
                        "format": "date",
                        "description": "The date of the order",
                    },
                },
                "required": ["account", "security", "quantity", "side"]
            }
        }
    ]
}

```

