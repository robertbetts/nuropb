# {py:mod}`nuropb.contexts.describe`

```{py:module} nuropb.contexts.describe
```

```{autodoc2-docstring} nuropb.contexts.describe
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`method_visible_on_mesh <nuropb.contexts.describe.method_visible_on_mesh>`
  - ```{autodoc2-docstring} nuropb.contexts.describe.method_visible_on_mesh
    :summary:
    ```
* - {py:obj}`publish_to_mesh <nuropb.contexts.describe.publish_to_mesh>`
  - ```{autodoc2-docstring} nuropb.contexts.describe.publish_to_mesh
    :summary:
    ```
* - {py:obj}`describe_service <nuropb.contexts.describe.describe_service>`
  - ```{autodoc2-docstring} nuropb.contexts.describe.describe_service
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <nuropb.contexts.describe.logger>`
  - ```{autodoc2-docstring} nuropb.contexts.describe.logger
    :summary:
    ```
* - {py:obj}`AuthorizeFunc <nuropb.contexts.describe.AuthorizeFunc>`
  - ```{autodoc2-docstring} nuropb.contexts.describe.AuthorizeFunc
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: nuropb.contexts.describe.logger
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.describe.logger
```

````

````{py:data} AuthorizeFunc
:canonical: nuropb.contexts.describe.AuthorizeFunc
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.describe.AuthorizeFunc
```

````

````{py:function} method_visible_on_mesh(method: typing.Callable[..., typing.Any]) -> bool
:canonical: nuropb.contexts.describe.method_visible_on_mesh

```{autodoc2-docstring} nuropb.contexts.describe.method_visible_on_mesh
```
````

````{py:function} publish_to_mesh(original_method: typing.Optional[typing.Callable[..., typing.Any]] = None, *, hide_method: typing.Optional[bool] = False, authorize_func: typing.Optional[nuropb.contexts.describe.AuthorizeFunc] = None, context_token_key: typing.Optional[str] = 'Authorization', requires_encryption: typing.Optional[bool] = False, description: typing.Optional[str] = None) -> typing.Any
:canonical: nuropb.contexts.describe.publish_to_mesh

```{autodoc2-docstring} nuropb.contexts.describe.publish_to_mesh
```
````

````{py:function} describe_service(class_instance: object) -> typing.Dict[str, typing.Any] | None
:canonical: nuropb.contexts.describe.describe_service

```{autodoc2-docstring} nuropb.contexts.describe.describe_service
```
````
