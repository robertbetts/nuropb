from typing import Optional

from nuropb.encodings.json_serialisation import JsonSerializor
from nuropb.interface import PayloadDict


SerializorTypes = JsonSerializor


def get_serializor(payload_type: str = "json") -> SerializorTypes:
    """Returns a serializor object for the specified encoded_payload type
    :param payload_type: "json"
    :return: a serializor object
    """
    if payload_type != "json":
        raise ValueError(f"payload_type {payload_type} is not supported")

    return JsonSerializor()


def encode_payload(
    payload: PayloadDict,
    payload_type: str = "json",
) -> bytes:
    """
    :param payload:
    :param payload_type: "json"
    :return: a json bytes string imputed encoded_payload
    """
    if payload_type != "json":
        raise ValueError(f"payload_type {payload_type} is not supported")

    return (
        get_serializor(
            payload_type=payload_type,
        )
        .encode(payload)
        .encode()
    )


def decode_payload(
    encoded_payload: bytes,
    payload_type: str = "json",
) -> PayloadDict:
    """
    :param encoded_payload:
    :param payload_type: "json"
    :return: PayloadDict
    """
    if payload_type != "json":
        raise ValueError(f"payload_type {payload_type} is not supported")

    payload = get_serializor(
        payload_type=payload_type,
    ).decode(encoded_payload.decode())
    if not isinstance(payload, dict):
        raise ValueError(
            f"Decoded payload is not a dictionary: {type(payload).__name__}"
        )
    return payload
