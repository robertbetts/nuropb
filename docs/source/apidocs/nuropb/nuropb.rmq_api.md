# {py:mod}`nuropb.rmq_api`

```{py:module} nuropb.rmq_api
```

```{autodoc2-docstring} nuropb.rmq_api
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`RMQAPI <nuropb.rmq_api.RMQAPI>`
  - ```{autodoc2-docstring} nuropb.rmq_api.RMQAPI
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <nuropb.rmq_api.logger>`
  - ```{autodoc2-docstring} nuropb.rmq_api.logger
    :summary:
    ```
* - {py:obj}`verbose <nuropb.rmq_api.verbose>`
  - ```{autodoc2-docstring} nuropb.rmq_api.verbose
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: nuropb.rmq_api.logger
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.logger
```

````

````{py:data} verbose
:canonical: nuropb.rmq_api.verbose
:value: >
   False

```{autodoc2-docstring} nuropb.rmq_api.verbose
```

````

`````{py:class} RMQAPI(amqp_url: str | typing.Dict[str, typing.Any], service_name: str | None = None, instance_id: str | None = None, service_instance: object | None = None, rpc_exchange: typing.Optional[str] = None, events_exchange: typing.Optional[str] = None, transport_settings: typing.Optional[typing.Dict[str, typing.Any]] = None)
:canonical: nuropb.rmq_api.RMQAPI

Bases: {py:obj}`nuropb.interface.NuropbInterface`

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.__init__
```

````{py:attribute} _mesh_name
:canonical: nuropb.rmq_api.RMQAPI._mesh_name
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._mesh_name
```

````

````{py:attribute} _connection_name
:canonical: nuropb.rmq_api.RMQAPI._connection_name
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._connection_name
```

````

````{py:attribute} _response_futures
:canonical: nuropb.rmq_api.RMQAPI._response_futures
:type: typing.Dict[str, nuropb.interface.ResultFutureResponsePayload]
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._response_futures
```

````

````{py:attribute} _transport
:canonical: nuropb.rmq_api.RMQAPI._transport
:type: nuropb.rmq_transport.RMQTransport
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._transport
```

````

````{py:attribute} _rpc_exchange
:canonical: nuropb.rmq_api.RMQAPI._rpc_exchange
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._rpc_exchange
```

````

````{py:attribute} _events_exchange
:canonical: nuropb.rmq_api.RMQAPI._events_exchange
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._events_exchange
```

````

````{py:attribute} _service_instance
:canonical: nuropb.rmq_api.RMQAPI._service_instance
:type: object | None
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._service_instance
```

````

````{py:attribute} _default_ttl
:canonical: nuropb.rmq_api.RMQAPI._default_ttl
:type: int
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._default_ttl
```

````

````{py:attribute} _client_only
:canonical: nuropb.rmq_api.RMQAPI._client_only
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._client_only
```

````

````{py:attribute} _encryptor
:canonical: nuropb.rmq_api.RMQAPI._encryptor
:type: nuropb.encodings.encryption.Encryptor
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._encryptor
```

````

````{py:attribute} _service_discovery
:canonical: nuropb.rmq_api.RMQAPI._service_discovery
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._service_discovery
```

````

````{py:attribute} _service_public_keys
:canonical: nuropb.rmq_api.RMQAPI._service_public_keys
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._service_public_keys
```

````

````{py:method} _get_vhost(amqp_url: str | typing.Dict[str, typing.Any]) -> str
:canonical: nuropb.rmq_api.RMQAPI._get_vhost
:classmethod:

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._get_vhost
```

````

````{py:attribute} _service_name
:canonical: nuropb.rmq_api.RMQAPI._service_name
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._service_name
```

````

````{py:property} service_name
:canonical: nuropb.rmq_api.RMQAPI.service_name
:type: str

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.service_name
```

````

````{py:property} is_leader
:canonical: nuropb.rmq_api.RMQAPI.is_leader
:type: bool

````

````{py:property} client_only
:canonical: nuropb.rmq_api.RMQAPI.client_only
:type: bool

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.client_only
```

````

````{py:property} connected
:canonical: nuropb.rmq_api.RMQAPI.connected
:type: bool

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.connected
```

````

````{py:property} transport
:canonical: nuropb.rmq_api.RMQAPI.transport
:type: nuropb.rmq_transport.RMQTransport

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.transport
```

````

````{py:method} connect() -> None
:canonical: nuropb.rmq_api.RMQAPI.connect
:async:

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.connect
```

````

````{py:method} disconnect() -> None
:canonical: nuropb.rmq_api.RMQAPI.disconnect
:async:

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.disconnect
```

````

````{py:method} receive_transport_message(service_message: nuropb.interface.TransportServicePayload, message_complete_callback: nuropb.interface.MessageCompleteFunction, metadata: typing.Dict[str, typing.Any]) -> None
:canonical: nuropb.rmq_api.RMQAPI.receive_transport_message

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.receive_transport_message
```

````

````{py:method} _handle_immediate_request_error(rpc_response: bool, payload: nuropb.interface.RequestPayloadDict | nuropb.interface.ResponsePayloadDict, error: typing.Dict[str, typing.Any] | BaseException) -> nuropb.interface.ResponsePayloadDict
:canonical: nuropb.rmq_api.RMQAPI._handle_immediate_request_error
:classmethod:

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI._handle_immediate_request_error
```

````

````{py:method} request(service: str, method: str, params: typing.Dict[str, typing.Any], context: typing.Dict[str, typing.Any], ttl: typing.Optional[int] = None, trace_id: typing.Optional[str] = None, rpc_response: bool = True, encrypted: bool = False) -> typing.Union[nuropb.interface.ResponsePayloadDict, typing.Any]
:canonical: nuropb.rmq_api.RMQAPI.request
:async:

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.request
```

````

````{py:method} command(service: str, method: str, params: typing.Dict[str, typing.Any], context: typing.Dict[str, typing.Any], ttl: typing.Optional[int] = None, trace_id: typing.Optional[str] = None, encrypted: bool = False) -> None
:canonical: nuropb.rmq_api.RMQAPI.command

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.command
```

````

````{py:method} publish_event(topic: str, event: typing.Dict[str, typing.Any], context: typing.Dict[str, typing.Any], trace_id: typing.Optional[str] = None, encrypted: bool = False) -> None
:canonical: nuropb.rmq_api.RMQAPI.publish_event

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.publish_event
```

````

````{py:method} describe_service(service_name: str, refresh: bool = False) -> typing.Dict[str, typing.Any] | None
:canonical: nuropb.rmq_api.RMQAPI.describe_service
:async:

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.describe_service
```

````

````{py:method} requires_encryption(service_name: str, method_name: str) -> bool
:canonical: nuropb.rmq_api.RMQAPI.requires_encryption
:async:

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.requires_encryption
```

````

````{py:method} has_public_key(service_name: str) -> bool
:canonical: nuropb.rmq_api.RMQAPI.has_public_key
:async:

```{autodoc2-docstring} nuropb.rmq_api.RMQAPI.has_public_key
```

````

`````
