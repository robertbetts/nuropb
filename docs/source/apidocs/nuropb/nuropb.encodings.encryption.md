# {py:mod}`nuropb.encodings.encryption`

```{py:module} nuropb.encodings.encryption
```

```{autodoc2-docstring} nuropb.encodings.encryption
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Encryptor <nuropb.encodings.encryption.Encryptor>`
  - ```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`encrypt_payload <nuropb.encodings.encryption.encrypt_payload>`
  - ```{autodoc2-docstring} nuropb.encodings.encryption.encrypt_payload
    :summary:
    ```
* - {py:obj}`decrypt_payload <nuropb.encodings.encryption.decrypt_payload>`
  - ```{autodoc2-docstring} nuropb.encodings.encryption.decrypt_payload
    :summary:
    ```
* - {py:obj}`encrypt_key <nuropb.encodings.encryption.encrypt_key>`
  - ```{autodoc2-docstring} nuropb.encodings.encryption.encrypt_key
    :summary:
    ```
* - {py:obj}`decrypt_key <nuropb.encodings.encryption.decrypt_key>`
  - ```{autodoc2-docstring} nuropb.encodings.encryption.decrypt_key
    :summary:
    ```
````

### API

````{py:function} encrypt_payload(payload: str | bytes, key: str | bytes) -> bytes
:canonical: nuropb.encodings.encryption.encrypt_payload

```{autodoc2-docstring} nuropb.encodings.encryption.encrypt_payload
```
````

````{py:function} decrypt_payload(encrypted_payload: str | bytes, key: str | bytes) -> bytes
:canonical: nuropb.encodings.encryption.decrypt_payload

```{autodoc2-docstring} nuropb.encodings.encryption.decrypt_payload
```
````

````{py:function} encrypt_key(symmetric_key: bytes, public_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey) -> bytes
:canonical: nuropb.encodings.encryption.encrypt_key

```{autodoc2-docstring} nuropb.encodings.encryption.encrypt_key
```
````

````{py:function} decrypt_key(encrypted_symmetric_key: bytes, private_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey) -> bytes
:canonical: nuropb.encodings.encryption.decrypt_key

```{autodoc2-docstring} nuropb.encodings.encryption.decrypt_key
```
````

`````{py:class} Encryptor(service_name: typing.Optional[str] = None, private_key: typing.Optional[cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey] = None)
:canonical: nuropb.encodings.encryption.Encryptor

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor.__init__
```

````{py:attribute} _service_name
:canonical: nuropb.encodings.encryption.Encryptor._service_name
:type: str | None
:value: >
   None

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor._service_name
```

````

````{py:attribute} _private_key
:canonical: nuropb.encodings.encryption.Encryptor._private_key
:type: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey | None
:value: >
   None

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor._private_key
```

````

````{py:attribute} _service_public_keys
:canonical: nuropb.encodings.encryption.Encryptor._service_public_keys
:type: typing.Dict[str, cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey]
:value: >
   None

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor._service_public_keys
```

````

````{py:attribute} _correlation_id_symmetric_keys
:canonical: nuropb.encodings.encryption.Encryptor._correlation_id_symmetric_keys
:type: typing.Dict[str, bytes]
:value: >
   None

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor._correlation_id_symmetric_keys
```

````

````{py:method} new_symmetric_key() -> bytes
:canonical: nuropb.encodings.encryption.Encryptor.new_symmetric_key
:classmethod:

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor.new_symmetric_key
```

````

````{py:method} add_public_key(service_name: str, public_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey) -> None
:canonical: nuropb.encodings.encryption.Encryptor.add_public_key

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor.add_public_key
```

````

````{py:method} get_public_key(service_name: str) -> cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey | None
:canonical: nuropb.encodings.encryption.Encryptor.get_public_key

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor.get_public_key
```

````

````{py:method} has_public_key(service_name: str) -> bool
:canonical: nuropb.encodings.encryption.Encryptor.has_public_key

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor.has_public_key
```

````

````{py:method} encrypt_payload(payload: bytes, correlation_id: str, service_name: typing.Optional[str | None] = None) -> bytes
:canonical: nuropb.encodings.encryption.Encryptor.encrypt_payload

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor.encrypt_payload
```

````

````{py:method} decrypt_payload(payload: bytes, correlation_id: str) -> bytes
:canonical: nuropb.encodings.encryption.Encryptor.decrypt_payload

```{autodoc2-docstring} nuropb.encodings.encryption.Encryptor.decrypt_payload
```

````

`````
