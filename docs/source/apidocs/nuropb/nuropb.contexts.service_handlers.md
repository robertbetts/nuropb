# {py:mod}`nuropb.contexts.service_handlers`

```{py:module} nuropb.contexts.service_handlers
```

```{autodoc2-docstring} nuropb.contexts.service_handlers
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`verbose <nuropb.contexts.service_handlers.verbose>`
  - ```{autodoc2-docstring} nuropb.contexts.service_handlers.verbose
    :summary:
    ```
* - {py:obj}`error_dict_from_exception <nuropb.contexts.service_handlers.error_dict_from_exception>`
  - ```{autodoc2-docstring} nuropb.contexts.service_handlers.error_dict_from_exception
    :summary:
    ```
* - {py:obj}`create_transport_response_from_rmq_decode_exception <nuropb.contexts.service_handlers.create_transport_response_from_rmq_decode_exception>`
  - ```{autodoc2-docstring} nuropb.contexts.service_handlers.create_transport_response_from_rmq_decode_exception
    :summary:
    ```
* - {py:obj}`create_transport_responses_from_exceptions <nuropb.contexts.service_handlers.create_transport_responses_from_exceptions>`
  - ```{autodoc2-docstring} nuropb.contexts.service_handlers.create_transport_responses_from_exceptions
    :summary:
    ```
* - {py:obj}`handle_execution_result <nuropb.contexts.service_handlers.handle_execution_result>`
  - ```{autodoc2-docstring} nuropb.contexts.service_handlers.handle_execution_result
    :summary:
    ```
* - {py:obj}`execute_request <nuropb.contexts.service_handlers.execute_request>`
  - ```{autodoc2-docstring} nuropb.contexts.service_handlers.execute_request
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <nuropb.contexts.service_handlers.logger>`
  - ```{autodoc2-docstring} nuropb.contexts.service_handlers.logger
    :summary:
    ```
* - {py:obj}`_verbose <nuropb.contexts.service_handlers._verbose>`
  - ```{autodoc2-docstring} nuropb.contexts.service_handlers._verbose
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: nuropb.contexts.service_handlers.logger
:value: >
   None

```{autodoc2-docstring} nuropb.contexts.service_handlers.logger
```

````

````{py:data} _verbose
:canonical: nuropb.contexts.service_handlers._verbose
:value: >
   False

```{autodoc2-docstring} nuropb.contexts.service_handlers._verbose
```

````

````{py:function} verbose() -> bool
:canonical: nuropb.contexts.service_handlers.verbose

```{autodoc2-docstring} nuropb.contexts.service_handlers.verbose
```
````

````{py:function} error_dict_from_exception(exception: Exception | BaseException) -> typing.Dict[str, str]
:canonical: nuropb.contexts.service_handlers.error_dict_from_exception

```{autodoc2-docstring} nuropb.contexts.service_handlers.error_dict_from_exception
```
````

````{py:function} create_transport_response_from_rmq_decode_exception(exception: Exception | BaseException, basic_deliver: pika.spec.Basic.Deliver, properties: pika.spec.BasicProperties) -> typing.Tuple[nuropb.interface.AcknowledgeAction, list[nuropb.interface.TransportRespondPayload]]
:canonical: nuropb.contexts.service_handlers.create_transport_response_from_rmq_decode_exception

```{autodoc2-docstring} nuropb.contexts.service_handlers.create_transport_response_from_rmq_decode_exception
```
````

````{py:function} create_transport_responses_from_exceptions(service_message: nuropb.interface.TransportServicePayload, exception: Exception | BaseException) -> typing.Tuple[nuropb.interface.AcknowledgeAction, list[nuropb.interface.TransportRespondPayload]]
:canonical: nuropb.contexts.service_handlers.create_transport_responses_from_exceptions

```{autodoc2-docstring} nuropb.contexts.service_handlers.create_transport_responses_from_exceptions
```
````

````{py:function} handle_execution_result(service_message: nuropb.interface.TransportServicePayload, result: typing.Any, message_complete_callback: nuropb.interface.MessageCompleteFunction) -> None
:canonical: nuropb.contexts.service_handlers.handle_execution_result

```{autodoc2-docstring} nuropb.contexts.service_handlers.handle_execution_result
```
````

````{py:function} execute_request(service_instance: object, service_message: nuropb.interface.TransportServicePayload, message_complete_callback: nuropb.interface.MessageCompleteFunction) -> None
:canonical: nuropb.contexts.service_handlers.execute_request

```{autodoc2-docstring} nuropb.contexts.service_handlers.execute_request
```
````
