# {py:mod}`nuropb.contexts.context_manager`

```{py:module} nuropb.contexts.context_manager
```

```{autodoc2-docstring} nuropb.contexts.context_manager
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`NuropbContextManager <nuropb.contexts.context_manager.NuropbContextManager>`
  - ```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <nuropb.contexts.context_manager.logger>`
  - ```{autodoc2-docstring} nuropb.contexts.context_manager.logger
    :summary:
    ```
* - {py:obj}`_test_token_cache <nuropb.contexts.context_manager._test_token_cache>`
  - ```{autodoc2-docstring} nuropb.contexts.context_manager._test_token_cache
    :summary:
    ```
* - {py:obj}`_test_user_id_cache <nuropb.contexts.context_manager._test_user_id_cache>`
  - ```{autodoc2-docstring} nuropb.contexts.context_manager._test_user_id_cache
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: nuropb.contexts.context_manager.logger
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.logger
```

````

````{py:data} _test_token_cache
:canonical: nuropb.contexts.context_manager._test_token_cache
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager._test_token_cache
```

````

````{py:data} _test_user_id_cache
:canonical: nuropb.contexts.context_manager._test_user_id_cache
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager._test_user_id_cache
```

````

`````{py:class} NuropbContextManager(context: typing.Dict[str, typing.Any], suppress_exceptions: typing.Optional[bool] = True)
:canonical: nuropb.contexts.context_manager.NuropbContextManager

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.__init__
```

````{py:attribute} _suppress_exceptions
:canonical: nuropb.contexts.context_manager.NuropbContextManager._suppress_exceptions
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._suppress_exceptions
```

````

````{py:attribute} _nuropb_payload
:canonical: nuropb.contexts.context_manager.NuropbContextManager._nuropb_payload
:type: typing.Dict[str, typing.Any] | None
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._nuropb_payload
```

````

````{py:attribute} _context
:canonical: nuropb.contexts.context_manager.NuropbContextManager._context
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._context
```

````

````{py:attribute} _user_claims
:canonical: nuropb.contexts.context_manager.NuropbContextManager._user_claims
:type: typing.Dict[str, typing.Any] | None
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._user_claims
```

````

````{py:attribute} _events
:canonical: nuropb.contexts.context_manager.NuropbContextManager._events
:type: typing.List[typing.Dict[str, typing.Any]]
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._events
```

````

````{py:attribute} _exc_type
:canonical: nuropb.contexts.context_manager.NuropbContextManager._exc_type
:type: typing.Type[BaseException] | None
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._exc_type
```

````

````{py:attribute} _exec_value
:canonical: nuropb.contexts.context_manager.NuropbContextManager._exec_value
:type: BaseException | None
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._exec_value
```

````

````{py:attribute} _exc_tb
:canonical: nuropb.contexts.context_manager.NuropbContextManager._exc_tb
:type: types.TracebackType | None
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._exc_tb
```

````

````{py:attribute} _started
:canonical: nuropb.contexts.context_manager.NuropbContextManager._started
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._started
```

````

````{py:attribute} _done
:canonical: nuropb.contexts.context_manager.NuropbContextManager._done
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._done
```

````

````{py:property} context
:canonical: nuropb.contexts.context_manager.NuropbContextManager.context
:type: typing.Dict[str, typing.Any]

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.context
```

````

````{py:property} user_claims
:canonical: nuropb.contexts.context_manager.NuropbContextManager.user_claims
:type: typing.Dict[str, typing.Any] | None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.user_claims
```

````

````{py:property} events
:canonical: nuropb.contexts.context_manager.NuropbContextManager.events
:type: typing.List[typing.Dict[str, typing.Any]]

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.events
```

````

````{py:property} error
:canonical: nuropb.contexts.context_manager.NuropbContextManager.error
:type: typing.Dict[str, typing.Any] | None

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.error
```

````

````{py:method} add_event(event: typing.Dict[str, typing.Any]) -> None
:canonical: nuropb.contexts.context_manager.NuropbContextManager.add_event

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.add_event
```

````

````{py:method} _handle_context_exit(exc_type: typing.Type[BaseException] | None, exc_value: BaseException | None, exc_tb: types.TracebackType | None) -> bool
:canonical: nuropb.contexts.context_manager.NuropbContextManager._handle_context_exit

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager._handle_context_exit
```

````

````{py:method} __enter__() -> typing.Any
:canonical: nuropb.contexts.context_manager.NuropbContextManager.__enter__

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.__enter__
```

````

````{py:method} __aenter__() -> typing.Any
:canonical: nuropb.contexts.context_manager.NuropbContextManager.__aenter__
:async:

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.__aenter__
```

````

````{py:method} __exit__(exc_type: typing.Type[BaseException] | None, exc_value: BaseException | None, exc_tb: types.TracebackType | None) -> bool | None
:canonical: nuropb.contexts.context_manager.NuropbContextManager.__exit__

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.__exit__
```

````

````{py:method} __aexit__(exc_type: typing.Type[BaseException] | None, exc_value: BaseException | None, exc_tb: types.TracebackType | None) -> bool | None
:canonical: nuropb.contexts.context_manager.NuropbContextManager.__aexit__
:async:

```{autodoc2-docstring} nuropb.contexts.context_manager.NuropbContextManager.__aexit__
```

````

`````
