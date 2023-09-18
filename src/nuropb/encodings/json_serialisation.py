from typing import Any, Dict, Optional
import json
import datetime
from decimal import Decimal
import dataclasses


def to_json_compatible(obj: Any, recursive: bool = True, max_depth: int = 4) -> Any:
    """Returns a json compatible value for obj, if obj is not a native json type, then
    return a string representation.

    datetime.datetime: isoformat() + "Z". if there's timezone info, the datetime is
        converted to utc. if there is no timezone info, the datetime is assumed to be utc.

    :param obj: Any
    :param recursive: bool, whether to recursively convert obj to json compatible types
    :param max_depth: int, the maximum depth to recurse
    :return: str, or other json compatible type
    """
    if max_depth < 0:
        return obj  # pragma: no cover

    if isinstance(obj, datetime.datetime):
        if obj.tzinfo is None:
            obj = obj.replace(tzinfo=datetime.timezone.utc)  # assume and set to UTC
        elif obj.tzinfo != datetime.timezone.utc:
            obj = obj.astimezone(datetime.timezone.utc)  # convert to UTC
        json_string = f"{obj.isoformat()}Z"
        return json_string

    if isinstance(obj, (datetime.date, datetime.time)):
        json_string = obj.isoformat()
        return json_string

    if isinstance(obj, datetime.timedelta):
        json_string = str(obj)
        return json_string

    if isinstance(obj, Decimal):
        return "{0:f}".format(obj)

    if dataclasses.is_dataclass(obj):
        dataclass_dict = dataclasses.asdict(obj)
        return dataclass_dict

    if isinstance(obj, dict) and recursive:
        return {
            k: to_json_compatible(v, recursive=recursive, max_depth=max_depth - 1)
            for k, v in obj.items()
        }

    if isinstance(obj, (list, tuple)) and recursive:
        return [
            to_json_compatible(v, recursive=recursive, max_depth=max_depth - 1)
            for v in obj
        ]

    if isinstance(obj, set) and recursive:
        return [
            to_json_compatible(v, recursive=recursive, max_depth=max_depth - 1)
            for v in obj
        ]

    return obj


class NuropbEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            json_string = f"{obj.isoformat()}Z"
            return json_string

        if isinstance(obj, (datetime.date, datetime.time)):
            json_string = f"{obj.isoformat()}Z"
            return json_string

        if isinstance(obj, datetime.timedelta):
            json_string = str(obj)
            return json_string

        if isinstance(obj, Decimal):
            return "{0:f}".format(obj)

        if dataclasses.is_dataclass(obj):
            dataclass_dict = dataclasses.asdict(obj)
            return dataclass_dict

        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


def to_json(obj: Any) -> str:
    """Returns a json string representation of the input object, if not a native json type"""
    return json.dumps(obj, cls=NuropbEncoder)


class JsonSerializor(object):
    """Serializes and deserializes nuropb payloads to and from JSON format."""

    _encryption_keys: Dict[str, Any]
    """ encryption keys related to a given correlation_id
    """

    def __init__(self):
        """Initializes a new JsonSerializor instance."""
        self._encryption_keys = {}

    def encode(self, payload: Any) -> str:
        """Encodes a nuropb encoded_payload to JSON.

        :param payload: Any, The encoded_payload to encode.
        :return: str, The JSON-encoded encoded_payload.
        """
        _ = self
        json_payload = to_json(payload)
        return json_payload

    def decode(self, json_payload: str) -> Any:
        """Decodes a JSON-encoded nuropb encoded_payload.

        :param json_payload: str, The JSON-encoded encoded_payload to decode.
        :return: Any, The decoded encoded_payload.
        """
        _ = self
        payload = json.loads(json_payload)
        return payload
