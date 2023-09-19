import datetime
from typing import List, Optional
from uuid import uuid4
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from nuropb.contexts.context_manager import NuropbContextManager
from nuropb.contexts.context_manager_decorator import nuropb_context
from nuropb.contexts.describe import describe_service, publish_to_mesh

service_describe = service_api_spec = {
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


@dataclass
class Order:
    account: str
    security: str
    quantity: int
    side: str

    order_id: str = uuid4().hex
    order_date: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    status: str = "Open"
    order_type: str = "Market"
    time_in_force: str = "Day"

    executed_time: Optional[datetime] = None
    account_id: Optional[str] = None
    security_id: Optional[str] = None
    price: Optional[float] = None
    stop_price: Optional[float] = None


class OrderManagementService:
    """
    Some useful documentation to describe the characteristic of the service and its purpose
    """
    _service_name = "oms_v2"
    _version = "2.0.1"
    _private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    @nuropb_context
    @publish_to_mesh(requires_encryption=True)
    async def get_orders(
            self,
            ctx: NuropbContextManager,
            order_date: datetime.datetime,
            account: Optional[str] = None,
            status: Optional[str] = "",
            security: Optional[str] = None,
            side: Optional[str] = None
    ) -> List[Order]:
        _ = order_date, account, status, security, side
        assert isinstance(self, OrderManagementService)
        assert isinstance(ctx, NuropbContextManager)
        return []

    @nuropb_context
    @publish_to_mesh
    async def create_order(self, ctx: NuropbContextManager) -> Order:
        assert isinstance(self, OrderManagementService)
        assert isinstance(ctx, NuropbContextManager)
        new_order = Order(account="ABC1234",
                          security="SSE.L",
                          quantity=1000,
                          side="sell")
        return new_order

    @nuropb_context
    @publish_to_mesh(hide_method=True)
    async def internal_method(self, ctx: NuropbContextManager) -> str:
        assert isinstance(self, OrderManagementService)
        assert isinstance(ctx, NuropbContextManager)
        return "OK"

    async def undecorated_method(self) -> str:
        assert isinstance(self, OrderManagementService)
        return "OK"


class Service:
    """ Some useful documentation to describe the characteristic of the service and its purpose
    """
    service_name = "describe_service"

    def hello(self, _param1: str, param2: str = "value2") -> str:
        _ = self, _param1, param2
        return "hello world"

    @nuropb_context
    async def do_some_transaction(
            self,
            ctx: NuropbContextManager,
            order_no: str,
            order_date: datetime.datetime,
            order_amount: float
    ) -> str:
        """ Some useful documentation for this method

        :param ctx:
        :param order_no:
        :param order_date:
        :param order_amount:
        :return:
        """
        _ = self, ctx, order_no, order_date, order_amount
        return "transaction successful"

    def _private_method(self, param1, param2):
        _ = self, param1, param2
        return "private method"


def test_instance_describe():
    service_instance = OrderManagementService()
    result = describe_service(service_instance)
    assert result["description"] == service_instance.__doc__.strip()
    assert len(result["methods"]) == 3
    assert len(result["methods"]["create_order"]) == 3
    assert result["methods"]["get_orders"]["requires_encryption"] is True

