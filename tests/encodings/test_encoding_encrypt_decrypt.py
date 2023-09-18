from uuid import uuid4
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from nuropb.encodings.encryption import (
    encrypt_payload,
    decrypt_payload,
    encrypt_key,
    decrypt_key,
    Encryptor,
)
from nuropb.encodings.serializor import encode_payload, decode_payload
from nuropb.interface import RequestPayloadDict, ResponsePayloadDict


def test_symmetric_encryption():
    """Test symmetric encryption and decryption"""
    key = Fernet.generate_key()
    payload = "Hello World"
    encrypted_payload = encrypt_payload(payload, key)
    print(encrypted_payload)
    decrypted_payload = decrypt_payload(encrypted_payload, key)
    assert payload == decrypted_payload.decode()


def test_asymmetric_encryption():
    """Test asymmetric encryption and decryption"""
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    public_key = private_key.public_key()
    key = Fernet.generate_key()
    encrypted_key = encrypt_key(key, public_key)
    decrypted_key = decrypt_key(encrypted_key, private_key)
    print(encrypted_key)
    assert key == decrypted_key


def test_encrypted_payload_exchange():
    correlation_id = uuid4().hex
    trace_id = uuid4().hex
    request_payload: RequestPayloadDict = {
        "tag": "request",
        "context": {},
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "service": "test_service",
        "method": "test_async_method",
        "params": {"param1": "value1"},
    }
    service_name = "test_service"
    service_private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    service_encryptor = Encryptor(service_name, service_private_key)
    client_encryptor = Encryptor()
    client_encryptor.add_service_public_key(
        service_name=service_name, public_key=service_private_key.public_key()
    )
    request_payload_body = encode_payload(request_payload, "json")
    encrypted_request_payload = client_encryptor.encrypt_payload(
        payload=request_payload_body,
        correlation_id=correlation_id,
        service_name=service_name,
    )
    print(encrypted_request_payload)

    decrypted_request_payload = service_encryptor.decrypt_payload(
        payload=encrypted_request_payload, correlation_id=correlation_id
    )
    print(decrypted_request_payload)
    payload = decode_payload(decrypted_request_payload, "json")
    print(payload)
    assert payload["service"] == "test_service"
    assert payload["method"] == "test_async_method"
    assert payload["params"]["param1"] == "value1"

    response_payload: ResponsePayloadDict = {
        "tag": "response",
        "context": {},
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "result": "Hello World",
        "error": None,
        "warning": None,
    }
    response_payload_body = encode_payload(response_payload, "json")
    encrypted_response_payload = service_encryptor.encrypt_payload(
        payload=response_payload_body,
        correlation_id=correlation_id,
    )
    print(encrypted_response_payload)

    decrypted_response_payload = client_encryptor.decrypt_payload(
        payload=encrypted_response_payload,
        correlation_id=correlation_id,
    )
    print(decrypted_response_payload)
    payload = decode_payload(decrypted_response_payload, "json")
    print(payload)
    assert payload["result"] == "Hello World"
