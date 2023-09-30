# {py:mod}`examples.all_in_one`

```{py:module} examples.all_in_one
```

```{autodoc2-docstring} examples.all_in_one
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`QuickExampleService <examples.all_in_one.QuickExampleService>`
  - ```{autodoc2-docstring} examples.all_in_one.QuickExampleService
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_claims_from_token <examples.all_in_one.get_claims_from_token>`
  - ```{autodoc2-docstring} examples.all_in_one.get_claims_from_token
    :summary:
    ```
* - {py:obj}`main <examples.all_in_one.main>`
  - ```{autodoc2-docstring} examples.all_in_one.main
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <examples.all_in_one.logger>`
  - ```{autodoc2-docstring} examples.all_in_one.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: examples.all_in_one.logger
:value: >
   None

```{autodoc2-docstring} examples.all_in_one.logger
```

````

````{py:function} get_claims_from_token(bearer_token: str) -> typing.Dict[str, typing.Any] | None
:canonical: examples.all_in_one.get_claims_from_token

```{autodoc2-docstring} examples.all_in_one.get_claims_from_token
```
````

`````{py:class} QuickExampleService
:canonical: examples.all_in_one.QuickExampleService

```{autodoc2-docstring} examples.all_in_one.QuickExampleService
```

````{py:attribute} _service_name
:canonical: examples.all_in_one.QuickExampleService._service_name
:value: >
   'quick-example'

```{autodoc2-docstring} examples.all_in_one.QuickExampleService._service_name
```

````

````{py:attribute} _instance_id
:canonical: examples.all_in_one.QuickExampleService._instance_id
:value: >
   None

```{autodoc2-docstring} examples.all_in_one.QuickExampleService._instance_id
```

````

````{py:method} test_requires_user_claims(ctx, **kwargs: typing.Any) -> str
:canonical: examples.all_in_one.QuickExampleService.test_requires_user_claims

```{autodoc2-docstring} examples.all_in_one.QuickExampleService.test_requires_user_claims
```

````

````{py:method} test_method(param1, param2: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]
:canonical: examples.all_in_one.QuickExampleService.test_method

```{autodoc2-docstring} examples.all_in_one.QuickExampleService.test_method
```

````

`````

````{py:function} main()
:canonical: examples.all_in_one.main
:async:

```{autodoc2-docstring} examples.all_in_one.main
```
````
