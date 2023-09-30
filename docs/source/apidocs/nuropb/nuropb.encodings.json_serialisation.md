# {py:mod}`nuropb.encodings.json_serialisation`

```{py:module} nuropb.encodings.json_serialisation
```

```{autodoc2-docstring} nuropb.encodings.json_serialisation
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`NuropbEncoder <nuropb.encodings.json_serialisation.NuropbEncoder>`
  - ```{autodoc2-docstring} nuropb.encodings.json_serialisation.NuropbEncoder
    :summary:
    ```
* - {py:obj}`JsonSerializor <nuropb.encodings.json_serialisation.JsonSerializor>`
  - ```{autodoc2-docstring} nuropb.encodings.json_serialisation.JsonSerializor
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`to_json_compatible <nuropb.encodings.json_serialisation.to_json_compatible>`
  - ```{autodoc2-docstring} nuropb.encodings.json_serialisation.to_json_compatible
    :summary:
    ```
* - {py:obj}`to_json <nuropb.encodings.json_serialisation.to_json>`
  - ```{autodoc2-docstring} nuropb.encodings.json_serialisation.to_json
    :summary:
    ```
````

### API

````{py:function} to_json_compatible(obj: typing.Any, recursive: bool = True, max_depth: int = 4) -> typing.Any
:canonical: nuropb.encodings.json_serialisation.to_json_compatible

```{autodoc2-docstring} nuropb.encodings.json_serialisation.to_json_compatible
```
````

`````{py:class} NuropbEncoder(*, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, sort_keys=False, indent=None, separators=None, default=None)
:canonical: nuropb.encodings.json_serialisation.NuropbEncoder

Bases: {py:obj}`json.JSONEncoder`

```{autodoc2-docstring} nuropb.encodings.json_serialisation.NuropbEncoder
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.encodings.json_serialisation.NuropbEncoder.__init__
```

````{py:method} default(obj: typing.Any) -> typing.Any
:canonical: nuropb.encodings.json_serialisation.NuropbEncoder.default

````

`````

````{py:function} to_json(obj: typing.Any) -> str
:canonical: nuropb.encodings.json_serialisation.to_json

```{autodoc2-docstring} nuropb.encodings.json_serialisation.to_json
```
````

`````{py:class} JsonSerializor()
:canonical: nuropb.encodings.json_serialisation.JsonSerializor

Bases: {py:obj}`object`

```{autodoc2-docstring} nuropb.encodings.json_serialisation.JsonSerializor
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.encodings.json_serialisation.JsonSerializor.__init__
```

````{py:attribute} _encryption_keys
:canonical: nuropb.encodings.json_serialisation.JsonSerializor._encryption_keys
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.encodings.json_serialisation.JsonSerializor._encryption_keys
```

````

````{py:method} encode(payload: typing.Any) -> str
:canonical: nuropb.encodings.json_serialisation.JsonSerializor.encode

```{autodoc2-docstring} nuropb.encodings.json_serialisation.JsonSerializor.encode
```

````

````{py:method} decode(json_payload: str) -> typing.Any
:canonical: nuropb.encodings.json_serialisation.JsonSerializor.decode

```{autodoc2-docstring} nuropb.encodings.json_serialisation.JsonSerializor.decode
```

````

`````
