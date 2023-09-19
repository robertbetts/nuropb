# Service Context Management and Mesh Publication Features

## Context Manager and Decorator
When a service instance method is decorated with @nuropb_context, a NuropbContextManager instance will
be injected into the method, and usually into an argument named ctx. This context manager is callable
with the context `with` statement. Once the context manager has exited, it is considered done and 
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
```
This decorator function injects a NuropbContext instance into a method that has ctx:NuropbContext
as an argument. The ctx parameter of the decorated method is hidden from the method's signature 
visible on the service mesh.

The name of the ctx parameter can be changed by entering and alternative name using the 
context_parameter argument.

Any caller of class_instance.method(ctx=ctx) can either pass a NuropbContext instance or a dict. 
If a dict is passed, a NuropbContext instance will be created from the dict.

*NOTE* This decorator is intended only for class methods, using it with functions will have 
unexpected results and is likely to result in either and compile or runtime exception.

:param original_method: reserved for the @decorator logic 
:param context_parameter: str, (ctx) alternative context argument name
:param suppress_exceptions: bool, (True), if False then exceptions will be raised during with ctx as ...:  
:param authorise_func: callable(token: str) -> dict
:param authorise_key: str,
:return: a decorated method

## Describe
The published methods of a service are made available to all participants on a service mesh. The 
specification follows this example:
```python
service_api_spec = {
    "name": "order_management_service",
    "service_name": "order_management_service",
    "published_events": [],
    "service_model": [],
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

