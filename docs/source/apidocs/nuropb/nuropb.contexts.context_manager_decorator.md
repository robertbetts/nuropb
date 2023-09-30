# {py:mod}`nuropb.contexts.context_manager_decorator`

```{py:module} nuropb.contexts.context_manager_decorator
```

```{autodoc2-docstring} nuropb.contexts.context_manager_decorator
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`method_requires_nuropb_context <nuropb.contexts.context_manager_decorator.method_requires_nuropb_context>`
  - ```{autodoc2-docstring} nuropb.contexts.context_manager_decorator.method_requires_nuropb_context
    :summary:
    ```
* - {py:obj}`nuropb_context <nuropb.contexts.context_manager_decorator.nuropb_context>`
  - ```{autodoc2-docstring} nuropb.contexts.context_manager_decorator.nuropb_context
    :summary:
    ```
````

### API

````{py:function} method_requires_nuropb_context(method: typing.Callable[..., typing.Any]) -> bool
:canonical: nuropb.contexts.context_manager_decorator.method_requires_nuropb_context

```{autodoc2-docstring} nuropb.contexts.context_manager_decorator.method_requires_nuropb_context
```
````

````{py:function} nuropb_context(original_method: typing.Optional[typing.Callable[..., typing.Any]] = None, *, context_parameter: str = 'ctx', suppress_exceptions: bool = False) -> typing.Any
:canonical: nuropb.contexts.context_manager_decorator.nuropb_context

```{autodoc2-docstring} nuropb.contexts.context_manager_decorator.nuropb_context
```
````
