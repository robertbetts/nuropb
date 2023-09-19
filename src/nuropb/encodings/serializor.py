from cryptography.hazmat.primitives.asymmetric import rsa

from nuropb.encodings.json_serialisation import JsonSerializor
from nuropb.interface import PayloadDict


SerializorTypes = JsonSerializor


def get_serializor(payload_type: str = "json") -> SerializorTypes:
    """Returns a serializor object for the specified encoded payload type
    :param payload_type: "json"
    :return: a serializor object
    """
    if payload_type != "json":
        raise ValueError(f"payload_type {payload_type} is not supported")

    return JsonSerializor()


def encode_payload(
    payload: PayloadDict,
    payload_type: str = "json",
    public_key: rsa.RSAPublicKey = None,
) -> bytes:
    """
    :param public_key:
    :param payload:
    :param payload_type: "json"
    :param public_key: rsa.PublicKey
    :return: a json bytes string imputed encoded payload
    """
    if payload_type != "json":
        raise ValueError(f"payload_type {payload_type} is not supported")

    return (
        get_serializor(
            payload_type=payload_type,
        )
        .encode(payload)  # to json
        .encode()  # to bytes
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
