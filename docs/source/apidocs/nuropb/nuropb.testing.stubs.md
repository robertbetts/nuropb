# {py:mod}`nuropb.testing.stubs`

```{py:module} nuropb.testing.stubs
```

```{autodoc2-docstring} nuropb.testing.stubs
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ServiceStub <nuropb.testing.stubs.ServiceStub>`
  - ```{autodoc2-docstring} nuropb.testing.stubs.ServiceStub
    :summary:
    ```
* - {py:obj}`ServiceExample <nuropb.testing.stubs.ServiceExample>`
  - ```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_claims_from_token <nuropb.testing.stubs.get_claims_from_token>`
  - ```{autodoc2-docstring} nuropb.testing.stubs.get_claims_from_token
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <nuropb.testing.stubs.logger>`
  - ```{autodoc2-docstring} nuropb.testing.stubs.logger
    :summary:
    ```
* - {py:obj}`IN_GITHUB_ACTIONS <nuropb.testing.stubs.IN_GITHUB_ACTIONS>`
  - ```{autodoc2-docstring} nuropb.testing.stubs.IN_GITHUB_ACTIONS
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: nuropb.testing.stubs.logger
:value: >
   None

```{autodoc2-docstring} nuropb.testing.stubs.logger
```

````

````{py:data} IN_GITHUB_ACTIONS
:canonical: nuropb.testing.stubs.IN_GITHUB_ACTIONS
:value: >
   None

```{autodoc2-docstring} nuropb.testing.stubs.IN_GITHUB_ACTIONS
```

````

````{py:function} get_claims_from_token(bearer_token: str) -> typing.Dict[str, typing.Any] | None
:canonical: nuropb.testing.stubs.get_claims_from_token

```{autodoc2-docstring} nuropb.testing.stubs.get_claims_from_token
```
````

`````{py:class} ServiceStub(service_name: str, instance_id: typing.Optional[str] = None, private_key: typing.Optional[cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey] = None)
:canonical: nuropb.testing.stubs.ServiceStub

```{autodoc2-docstring} nuropb.testing.stubs.ServiceStub
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.testing.stubs.ServiceStub.__init__
```

````{py:attribute} _service_name
:canonical: nuropb.testing.stubs.ServiceStub._service_name
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.testing.stubs.ServiceStub._service_name
```

````

````{py:attribute} _instance_id
:canonical: nuropb.testing.stubs.ServiceStub._instance_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.testing.stubs.ServiceStub._instance_id
```

````

````{py:attribute} _private_key
:canonical: nuropb.testing.stubs.ServiceStub._private_key
:type: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey
:value: >
   None

```{autodoc2-docstring} nuropb.testing.stubs.ServiceStub._private_key
```

````

````{py:property} service_name
:canonical: nuropb.testing.stubs.ServiceStub.service_name
:type: str

```{autodoc2-docstring} nuropb.testing.stubs.ServiceStub.service_name
```

````

````{py:property} instance_id
:canonical: nuropb.testing.stubs.ServiceStub.instance_id
:type: str

```{autodoc2-docstring} nuropb.testing.stubs.ServiceStub.instance_id
```

````

````{py:property} private_key
:canonical: nuropb.testing.stubs.ServiceStub.private_key
:type: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey

```{autodoc2-docstring} nuropb.testing.stubs.ServiceStub.private_key
```

````

`````

`````{py:class} ServiceExample(*args: typing.Any, **kwargs: typing.Any)
:canonical: nuropb.testing.stubs.ServiceExample

Bases: {py:obj}`nuropb.testing.stubs.ServiceStub`

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample.__init__
```

````{py:attribute} _method_call_count
:canonical: nuropb.testing.stubs.ServiceExample._method_call_count
:type: int
:value: >
   None

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample._method_call_count
```

````

````{py:attribute} _raise_call_again_error
:canonical: nuropb.testing.stubs.ServiceExample._raise_call_again_error
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample._raise_call_again_error
```

````

````{py:method} test_method(**kwargs: typing.Any) -> str
:canonical: nuropb.testing.stubs.ServiceExample.test_method

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample.test_method
```

````

````{py:method} do_async_task(**kwargs: typing.Any) -> str
:canonical: nuropb.testing.stubs.ServiceExample.do_async_task
:async:

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample.do_async_task
```

````

````{py:method} test_async_method(**kwargs: typing.Any) -> str
:canonical: nuropb.testing.stubs.ServiceExample.test_async_method
:async:

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample.test_async_method
```

````

````{py:method} test_success_error(**kwargs: typing.Any) -> None
:canonical: nuropb.testing.stubs.ServiceExample.test_success_error

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample.test_success_error
```

````

````{py:method} test_requires_user_claims(ctx: nuropb.contexts.context_manager.NuropbContextManager, **kwargs: typing.Any) -> typing.Any
:canonical: nuropb.testing.stubs.ServiceExample.test_requires_user_claims

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample.test_requires_user_claims
```

````

````{py:method} test_requires_encryption(ctx: nuropb.contexts.context_manager.NuropbContextManager, **kwargs: typing.Any) -> typing.Any
:canonical: nuropb.testing.stubs.ServiceExample.test_requires_encryption

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample.test_requires_encryption
```

````

````{py:method} test_call_again_error(**kwargs: typing.Any) -> typing.Dict[str, typing.Any]
:canonical: nuropb.testing.stubs.ServiceExample.test_call_again_error

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample.test_call_again_error
```

````

````{py:method} test_call_again_loop(**kwargs: typing.Any) -> None
:canonical: nuropb.testing.stubs.ServiceExample.test_call_again_loop

```{autodoc2-docstring} nuropb.testing.stubs.ServiceExample.test_call_again_loop
```

````

`````
