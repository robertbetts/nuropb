import datetime
import json
from decimal import Decimal
from dataclasses import dataclass
from uuid import uuid4
from typing import Optional

import pytest

from nuropb.encodings.json_serialisation import to_json_compatible
from nuropb.encodings.serializor import encode_payload, decode_payload


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


@pytest.fixture(scope="function")
def generic_payload():
    return {
        "int": 1,
        "float": 1.0,
        "decimal": Decimal("1.00000000000001"),
        "str": "string",
        "bool": True,
        "list": [1, 2, 3],
        "dict": {"a": 1, "b": 2},
        "none": None,
        "date": datetime.date(2020, 1, 1),
        "datetime": datetime.datetime(2020, 1, 1, 0, 0, 0),
        "utc_datetime": datetime.datetime(
            2020, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
        "utc_datetime_no_tz": datetime.datetime.utcnow(),
        "time": datetime.time(0, 0, 0),
        "timedelta": datetime.timedelta(days=1),
        "mixt_list": [1, "string", True, None, datetime.date(2020, 1, 1)],
        "mixed_dict": {
            "int": 1,
            "float": 1.0,
            "decimal": Decimal("1.00000000000001"),
            "str": "string",
            "bool": True,
            "list": [1, 2, 3],
            "dict": {"a": 1, "b": 2},
            "none": None,
            "date": datetime.date(2020, 1, 1),
            "datetime": datetime.datetime(2020, 1, 1, 0, 0, 0),
            "set": {1, 2, Decimal(3)},
        },
        "dataclass": Order(account="ABC1234",
                           security="SSE.L",
                           quantity=1000,
                           side="sell")
    }


def test_to_json_compatible(generic_payload):
    safe_obj = to_json_compatible(generic_payload)
    result = json.dumps(safe_obj)
    obj = json.loads(result)
    assert len(obj) == len(generic_payload)


def test_json_encode_decode_python_types(generic_payload):
    """Test encoding and decoding of python types."""
    encoded_payload = encode_payload(generic_payload)
    decoded_payload = decode_payload(encoded_payload)

    # assert decoded_payload == generic_payload
