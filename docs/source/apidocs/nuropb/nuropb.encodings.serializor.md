# {py:mod}`nuropb.encodings.serializor`

```{py:module} nuropb.encodings.serializor
```

```{autodoc2-docstring} nuropb.encodings.serializor
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_serializor <nuropb.encodings.serializor.get_serializor>`
  - ```{autodoc2-docstring} nuropb.encodings.serializor.get_serializor
    :summary:
    ```
* - {py:obj}`encode_payload <nuropb.encodings.serializor.encode_payload>`
  - ```{autodoc2-docstring} nuropb.encodings.serializor.encode_payload
    :summary:
    ```
* - {py:obj}`decode_payload <nuropb.encodings.serializor.decode_payload>`
  - ```{autodoc2-docstring} nuropb.encodings.serializor.decode_payload
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SerializorTypes <nuropb.encodings.serializor.SerializorTypes>`
  - ```{autodoc2-docstring} nuropb.encodings.serializor.SerializorTypes
    :summary:
    ```
````

### API

````{py:data} SerializorTypes
:canonical: nuropb.encodings.serializor.SerializorTypes
:value: >
   None

```{autodoc2-docstring} nuropb.encodings.serializor.SerializorTypes
```

````

````{py:function} get_serializor(payload_type: str = 'json') -> nuropb.encodings.serializor.SerializorTypes
:canonical: nuropb.encodings.serializor.get_serializor

```{autodoc2-docstring} nuropb.encodings.serializor.get_serializor
```
````

````{py:function} encode_payload(payload: nuropb.interface.PayloadDict, payload_type: str = 'json', public_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey = None) -> bytes
:canonical: nuropb.encodings.serializor.encode_payload

```{autodoc2-docstring} nuropb.encodings.serializor.encode_payload
```
````

````{py:function} decode_payload(encoded_payload: bytes, payload_type: str = 'json') -> nuropb.interface.PayloadDict
:canonical: nuropb.encodings.serializor.decode_payload

```{autodoc2-docstring} nuropb.encodings.serializor.decode_payload
```
````
