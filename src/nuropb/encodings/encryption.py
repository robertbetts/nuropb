from typing import Dict, Optional
from base64 import b64encode, b64decode

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding


def encrypt_payload(payload: str | bytes, key: str | bytes) -> bytes:
    """Encrypt encoded payload with a key
    :param payload: str | bytes
    :param key: str
    :return: bytes
    """
    f = Fernet(key=key, backend=default_backend())
    if isinstance(payload, str):
        payload = payload.encode()
    enc_payload = f.encrypt(payload)
    return b64encode(enc_payload)


def decrypt_payload(encrypted_payload: str | bytes, key: str | bytes) -> bytes:
    """Decrypt encoded payload with a key
    :param encrypted_payload: str | bytes
    :param key: str
    :return: bytes
    """
    f = Fernet(key=key, backend=default_backend())
    payload_to_decrypt = b64decode(encrypted_payload)
    payload = f.decrypt(payload_to_decrypt)
    return payload


def encrypt_key(symmetric_key: bytes, public_key: rsa.RSAPublicKey) -> bytes:
    """Encrypt a symmetric key with an RSA public key
    :param symmetric_key: bytes
    :param public_key: rsa.RSAPublicKey
    :return: bytes, encrypted symmetric key
    """
    encrypted_symmetric_key = public_key.encrypt(
        symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return b64encode(encrypted_symmetric_key)


def decrypt_key(
    encrypted_symmetric_key: bytes, private_key: rsa.RSAPrivateKey
) -> bytes:
    """Decrypt a symmetric key encrypted with an RSA private key
    :param encrypted_symmetric_key: bytes
    :param private_key: rsa.RSAPrivateKey
    :return: bytes, decrypted symmetric key
    """
    symmetric_key = private_key.decrypt(
        b64decode(encrypted_symmetric_key),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return symmetric_key


class Encryptor:
    _service_name: str | None
    _private_key: rsa.RSAPrivateKey | None
    _service_public_keys: Dict[str, rsa.RSAPublicKey]
    _correlation_id_symmetric_keys: Dict[str, bytes]

    def __init__(
        self,
        service_name: Optional[str] = None,
        private_key: Optional[rsa.RSAPrivateKey] = None,
    ):
        self._service_name = service_name
        self._private_key = private_key
        self._service_public_keys = {}
        self._correlation_id_symmetric_keys = {}

    @classmethod
    def new_symmetric_key(cls) -> bytes:
        """Generate a new symmetric key
        :return: bytes
        """
        return Fernet.generate_key()

    def add_service_public_key(
        self, service_name: str, public_key: rsa.RSAPublicKey
    ) -> None:
        """Add a public key for a service
        :param service_name: str
        :param public_key: rsa.RSAPublicKey
        """
        self._service_public_keys[service_name] = public_key

    def get_service_public_key(self, service_name: str) -> rsa.RSAPublicKey:
        """Get a public key for a service
        :param service_name: str
        :return: rsa.RSAPublicKey
        """
        return self._service_public_keys.get[service_name]

    def encrypt_payload(
        self,
        payload: bytes,
        correlation_id: str,
        service_name: Optional[str | None] = None,
    ) -> bytes:
        """Encrypt a payload with a symmetric key

        Modes:
        1. Sending a payload to a service (Encrypt)
        4. Sending a response payload from a service (Encrypt)

        :param payload:
        :param correlation_id:
        :param service_name:
        :return: bytes
        """

        """ When service name is provided, it indicates mode 1, else mode 4 
        """
        if service_name is not None and service_name not in self._service_public_keys:
            raise ValueError(
                f"Service public key not found for service: {service_name}"
            )  # pragma: no cover

        if service_name is None:
            # Mode 4, get public key from the private key
            public_key = self._private_key.public_key()
        else:
            # Mode 1, get public key from the destination service's public key
            public_key = self._service_public_keys[service_name]

        if correlation_id not in self._correlation_id_symmetric_keys:
            # Mode 1, generate a new symmetric key and store it for this correlation_id
            key = self.new_symmetric_key()
            self._correlation_id_symmetric_keys[correlation_id] = key
        else:
            # Mode 4, use the original received symmetric key to encrypt key
            # pop it from the dict as it is not required again
            key = self._correlation_id_symmetric_keys.pop(correlation_id)

        encrypted_key = encrypt_key(key, public_key)
        encrypted_payload = encrypt_payload(payload=payload, key=key)

        return b".".join([encrypted_key, encrypted_payload])

    def decrypt_payload(self, payload: bytes, correlation_id: str) -> bytes:
        """Encrypt a payload with a symmetric key

        Modes:
        2. Receiving a response payload from a service (Decrypt)
        3. Receiving a rpc payload (Decrypt)

        :param payload:
        :param correlation_id:
        :return:
        """
        encrypted_key, encrypted_payload = payload.split(b".", 1)
        if correlation_id not in self._correlation_id_symmetric_keys:
            """Mode 3, use public key from the private key to decrypt key"""
            key = decrypt_key(encrypted_key, self._private_key)
            #  remember the key for this correlation_id to encrypt the response
            self._correlation_id_symmetric_keys[correlation_id] = key
        else:
            """Mode 2, use the original symmetric key to decrypt key
            * pop it from the dict as it is not used again
            """
            key = self._correlation_id_symmetric_keys.pop(correlation_id)

        decrypted_payload = decrypt_payload(encrypted_payload, key)

        return decrypted_payload
