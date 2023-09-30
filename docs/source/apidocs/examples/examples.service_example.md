# {py:mod}`examples.service_example`

```{py:module} examples.service_example
```

```{autodoc2-docstring} examples.service_example
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ServiceExample <examples.service_example.ServiceExample>`
  - ```{autodoc2-docstring} examples.service_example.ServiceExample
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <examples.service_example.logger>`
  - ```{autodoc2-docstring} examples.service_example.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: examples.service_example.logger
:value: >
   None

```{autodoc2-docstring} examples.service_example.logger
```

````

`````{py:class} ServiceExample(service_name: str, instance_id: str, private_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey)
:canonical: examples.service_example.ServiceExample

```{autodoc2-docstring} examples.service_example.ServiceExample
```

```{rubric} Initialization
```

```{autodoc2-docstring} examples.service_example.ServiceExample.__init__
```

````{py:attribute} _service_name
:canonical: examples.service_example.ServiceExample._service_name
:type: str
:value: >
   None

```{autodoc2-docstring} examples.service_example.ServiceExample._service_name
```

````

````{py:attribute} _instance_id
:canonical: examples.service_example.ServiceExample._instance_id
:type: str
:value: >
   None

```{autodoc2-docstring} examples.service_example.ServiceExample._instance_id
```

````

````{py:attribute} _private_key
:canonical: examples.service_example.ServiceExample._private_key
:type: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey
:value: >
   None

```{autodoc2-docstring} examples.service_example.ServiceExample._private_key
```

````

````{py:attribute} _method_call_count
:canonical: examples.service_example.ServiceExample._method_call_count
:type: int
:value: >
   None

```{autodoc2-docstring} examples.service_example.ServiceExample._method_call_count
```

````

````{py:method} _handle_event_(topic: str, event: dict, target: list[str] | None = None, context: dict | None = None, trace_id: str | None = None) -> None
:canonical: examples.service_example.ServiceExample._handle_event_
:classmethod:

```{autodoc2-docstring} examples.service_example.ServiceExample._handle_event_
```

````

````{py:method} test_method(**kwargs) -> str
:canonical: examples.service_example.ServiceExample.test_method

```{autodoc2-docstring} examples.service_example.ServiceExample.test_method
```

````

````{py:method} test_encrypt_method(**kwargs) -> str
:canonical: examples.service_example.ServiceExample.test_encrypt_method

```{autodoc2-docstring} examples.service_example.ServiceExample.test_encrypt_method
```

````

````{py:method} test_exception_method(**kwargs) -> str
:canonical: examples.service_example.ServiceExample.test_exception_method

```{autodoc2-docstring} examples.service_example.ServiceExample.test_exception_method
```

````

````{py:method} test_async_method(**kwargs) -> str
:canonical: examples.service_example.ServiceExample.test_async_method
:async:

```{autodoc2-docstring} examples.service_example.ServiceExample.test_async_method
```

````

````{py:method} async_method(**kwargs) -> int
:canonical: examples.service_example.ServiceExample.async_method
:async:

```{autodoc2-docstring} examples.service_example.ServiceExample.async_method
```

````

````{py:method} sync_method(**kwargs) -> int
:canonical: examples.service_example.ServiceExample.sync_method

```{autodoc2-docstring} examples.service_example.ServiceExample.sync_method
```

````

````{py:method} method_with_exception(**kwargs) -> None
:canonical: examples.service_example.ServiceExample.method_with_exception

```{autodoc2-docstring} examples.service_example.ServiceExample.method_with_exception
```

````

````{py:method} async_method_with_exception(**kwargs) -> None
:canonical: examples.service_example.ServiceExample.async_method_with_exception

```{autodoc2-docstring} examples.service_example.ServiceExample.async_method_with_exception
```

````

````{py:method} method_with_nuropb_exception(**kwargs) -> None
:canonical: examples.service_example.ServiceExample.method_with_nuropb_exception

```{autodoc2-docstring} examples.service_example.ServiceExample.method_with_nuropb_exception
```

````

`````
