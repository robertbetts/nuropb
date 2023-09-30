# {py:mod}`nuropb.rmq_transport`

```{py:module} nuropb.rmq_transport
```

```{autodoc2-docstring} nuropb.rmq_transport
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`RabbitMQConfiguration <nuropb.rmq_transport.RabbitMQConfiguration>`
  -
* - {py:obj}`RMQTransport <nuropb.rmq_transport.RMQTransport>`
  - ```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`verbose <nuropb.rmq_transport.verbose>`
  - ```{autodoc2-docstring} nuropb.rmq_transport.verbose
    :summary:
    ```
* - {py:obj}`decode_rmq_body <nuropb.rmq_transport.decode_rmq_body>`
  - ```{autodoc2-docstring} nuropb.rmq_transport.decode_rmq_body
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <nuropb.rmq_transport.logger>`
  - ```{autodoc2-docstring} nuropb.rmq_transport.logger
    :summary:
    ```
* - {py:obj}`CONSUMER_CLOSED_WAIT_TIMEOUT <nuropb.rmq_transport.CONSUMER_CLOSED_WAIT_TIMEOUT>`
  - ```{autodoc2-docstring} nuropb.rmq_transport.CONSUMER_CLOSED_WAIT_TIMEOUT
    :summary:
    ```
* - {py:obj}`_verbose <nuropb.rmq_transport._verbose>`
  - ```{autodoc2-docstring} nuropb.rmq_transport._verbose
    :summary:
    ```
````

### API

`````{py:class} RabbitMQConfiguration()
:canonical: nuropb.rmq_transport.RabbitMQConfiguration

Bases: {py:obj}`typing.TypedDict`

````{py:attribute} rpc_exchange
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.rpc_exchange
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.rpc_exchange
```

````

````{py:attribute} events_exchange
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.events_exchange
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.events_exchange
```

````

````{py:attribute} dl_exchange
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.dl_exchange
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.dl_exchange
```

````

````{py:attribute} dl_queue
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.dl_queue
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.dl_queue
```

````

````{py:attribute} service_queue
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.service_queue
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.service_queue
```

````

````{py:attribute} response_queue
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.response_queue
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.response_queue
```

````

````{py:attribute} rpc_bindings
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.rpc_bindings
:type: typing.List[str]
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.rpc_bindings
```

````

````{py:attribute} event_bindings
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.event_bindings
:type: typing.List[str]
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.event_bindings
```

````

````{py:attribute} default_ttl
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.default_ttl
:type: int
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.default_ttl
```

````

````{py:attribute} client_only
:canonical: nuropb.rmq_transport.RabbitMQConfiguration.client_only
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RabbitMQConfiguration.client_only
```

````

`````

````{py:data} logger
:canonical: nuropb.rmq_transport.logger
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.logger
```

````

````{py:data} CONSUMER_CLOSED_WAIT_TIMEOUT
:canonical: nuropb.rmq_transport.CONSUMER_CLOSED_WAIT_TIMEOUT
:value: >
   10

```{autodoc2-docstring} nuropb.rmq_transport.CONSUMER_CLOSED_WAIT_TIMEOUT
```

````

````{py:data} _verbose
:canonical: nuropb.rmq_transport._verbose
:value: >
   False

```{autodoc2-docstring} nuropb.rmq_transport._verbose
```

````

````{py:function} verbose() -> bool
:canonical: nuropb.rmq_transport.verbose

```{autodoc2-docstring} nuropb.rmq_transport.verbose
```
````

````{py:function} decode_rmq_body(method: pika.spec.Basic.Deliver, properties: pika.spec.BasicProperties, body: bytes) -> nuropb.interface.TransportServicePayload
:canonical: nuropb.rmq_transport.decode_rmq_body

```{autodoc2-docstring} nuropb.rmq_transport.decode_rmq_body
```
````

````{py:exception} ServiceNotConfigured()
:canonical: nuropb.rmq_transport.ServiceNotConfigured

Bases: {py:obj}`Exception`

```{autodoc2-docstring} nuropb.rmq_transport.ServiceNotConfigured
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.rmq_transport.ServiceNotConfigured.__init__
```

````

`````{py:class} RMQTransport(service_name: str, instance_id: str, amqp_url: str | typing.Dict[str, typing.Any], message_callback: nuropb.interface.MessageCallbackFunction, default_ttl: typing.Optional[int] = None, client_only: typing.Optional[bool] = None, encryptor: typing.Optional[nuropb.encodings.encryption.Encryptor] = None, **kwargs: typing.Any)
:canonical: nuropb.rmq_transport.RMQTransport

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.__init__
```

````{py:attribute} _service_name
:canonical: nuropb.rmq_transport.RMQTransport._service_name
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._service_name
```

````

````{py:attribute} _instance_id
:canonical: nuropb.rmq_transport.RMQTransport._instance_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._instance_id
```

````

````{py:attribute} _amqp_url
:canonical: nuropb.rmq_transport.RMQTransport._amqp_url
:type: str | typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._amqp_url
```

````

````{py:attribute} _rpc_exchange
:canonical: nuropb.rmq_transport.RMQTransport._rpc_exchange
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._rpc_exchange
```

````

````{py:attribute} _events_exchange
:canonical: nuropb.rmq_transport.RMQTransport._events_exchange
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._events_exchange
```

````

````{py:attribute} _dl_exchange
:canonical: nuropb.rmq_transport.RMQTransport._dl_exchange
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._dl_exchange
```

````

````{py:attribute} _dl_queue
:canonical: nuropb.rmq_transport.RMQTransport._dl_queue
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._dl_queue
```

````

````{py:attribute} _service_queue
:canonical: nuropb.rmq_transport.RMQTransport._service_queue
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._service_queue
```

````

````{py:attribute} _response_queue
:canonical: nuropb.rmq_transport.RMQTransport._response_queue
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._response_queue
```

````

````{py:attribute} _rpc_bindings
:canonical: nuropb.rmq_transport.RMQTransport._rpc_bindings
:type: typing.Set[str]
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._rpc_bindings
```

````

````{py:attribute} _event_bindings
:canonical: nuropb.rmq_transport.RMQTransport._event_bindings
:type: typing.Set[str]
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._event_bindings
```

````

````{py:attribute} _prefetch_count
:canonical: nuropb.rmq_transport.RMQTransport._prefetch_count
:type: int
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._prefetch_count
```

````

````{py:attribute} _default_ttl
:canonical: nuropb.rmq_transport.RMQTransport._default_ttl
:type: int
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._default_ttl
```

````

````{py:attribute} _client_only
:canonical: nuropb.rmq_transport.RMQTransport._client_only
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._client_only
```

````

````{py:attribute} _message_callback
:canonical: nuropb.rmq_transport.RMQTransport._message_callback
:type: nuropb.interface.MessageCallbackFunction
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._message_callback
```

````

````{py:attribute} _encryptor
:canonical: nuropb.rmq_transport.RMQTransport._encryptor
:type: nuropb.encodings.encryption.Encryptor | None
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._encryptor
```

````

````{py:attribute} _connected_future
:canonical: nuropb.rmq_transport.RMQTransport._connected_future
:type: typing.Any
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._connected_future
```

````

````{py:attribute} _disconnected_future
:canonical: nuropb.rmq_transport.RMQTransport._disconnected_future
:type: typing.Any
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._disconnected_future
```

````

````{py:attribute} _is_leader
:canonical: nuropb.rmq_transport.RMQTransport._is_leader
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._is_leader
```

````

````{py:attribute} _is_rabbitmq_configured
:canonical: nuropb.rmq_transport.RMQTransport._is_rabbitmq_configured
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._is_rabbitmq_configured
```

````

````{py:attribute} _connection
:canonical: nuropb.rmq_transport.RMQTransport._connection
:type: pika.adapters.asyncio_connection.AsyncioConnection | None
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._connection
```

````

````{py:attribute} _channel
:canonical: nuropb.rmq_transport.RMQTransport._channel
:type: pika.channel.Channel | None
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._channel
```

````

````{py:attribute} _consumer_tags
:canonical: nuropb.rmq_transport.RMQTransport._consumer_tags
:type: typing.Set[typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._consumer_tags
```

````

````{py:attribute} _consuming
:canonical: nuropb.rmq_transport.RMQTransport._consuming
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._consuming
```

````

````{py:attribute} _connecting
:canonical: nuropb.rmq_transport.RMQTransport._connecting
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._connecting
```

````

````{py:attribute} _closing
:canonical: nuropb.rmq_transport.RMQTransport._closing
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._closing
```

````

````{py:attribute} _connected
:canonical: nuropb.rmq_transport.RMQTransport._connected
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._connected
```

````

````{py:attribute} _was_consuming
:canonical: nuropb.rmq_transport.RMQTransport._was_consuming
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport._was_consuming
```

````

````{py:property} service_name
:canonical: nuropb.rmq_transport.RMQTransport.service_name
:type: str

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.service_name
```

````

````{py:property} instance_id
:canonical: nuropb.rmq_transport.RMQTransport.instance_id
:type: str

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.instance_id
```

````

````{py:property} amqp_url
:canonical: nuropb.rmq_transport.RMQTransport.amqp_url
:type: str | typing.Dict[str, typing.Any]

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.amqp_url
```

````

````{py:property} is_leader
:canonical: nuropb.rmq_transport.RMQTransport.is_leader
:type: bool

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.is_leader
```

````

````{py:property} connected
:canonical: nuropb.rmq_transport.RMQTransport.connected
:type: bool

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.connected
```

````

````{py:property} rpc_exchange
:canonical: nuropb.rmq_transport.RMQTransport.rpc_exchange
:type: str

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.rpc_exchange
```

````

````{py:property} events_exchange
:canonical: nuropb.rmq_transport.RMQTransport.events_exchange
:type: str

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.events_exchange
```

````

````{py:property} response_queue
:canonical: nuropb.rmq_transport.RMQTransport.response_queue
:type: str

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.response_queue
```

````

````{py:property} rmq_configuration
:canonical: nuropb.rmq_transport.RMQTransport.rmq_configuration
:type: nuropb.rmq_transport.RabbitMQConfiguration

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.rmq_configuration
```

````

````{py:method} configure_rabbitmq(rmq_configuration: typing.Optional[nuropb.rmq_transport.RabbitMQConfiguration] = None, amqp_url: typing.Optional[str | typing.Dict[str, typing.Any]] = None, rmq_api_url: typing.Optional[str] = None) -> None
:canonical: nuropb.rmq_transport.RMQTransport.configure_rabbitmq

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.configure_rabbitmq
```

````

````{py:method} start() -> None
:canonical: nuropb.rmq_transport.RMQTransport.start
:async:

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.start
```

````

````{py:method} stop() -> None
:canonical: nuropb.rmq_transport.RMQTransport.stop
:async:

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.stop
```

````

````{py:method} connect() -> asyncio.Future[bool]
:canonical: nuropb.rmq_transport.RMQTransport.connect

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.connect
```

````

````{py:method} disconnect() -> typing.Awaitable[bool]
:canonical: nuropb.rmq_transport.RMQTransport.disconnect

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.disconnect
```

````

````{py:method} on_connection_open(_connection: pika.adapters.asyncio_connection.AsyncioConnection) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_connection_open

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_connection_open
```

````

````{py:method} on_connection_open_error(conn: pika.adapters.asyncio_connection.AsyncioConnection, reason: Exception) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_connection_open_error

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_connection_open_error
```

````

````{py:method} on_connection_closed(_connection: pika.adapters.asyncio_connection.AsyncioConnection, reason: Exception) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_connection_closed

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_connection_closed
```

````

````{py:method} open_channel() -> None
:canonical: nuropb.rmq_transport.RMQTransport.open_channel

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.open_channel
```

````

````{py:method} on_channel_open(channel: pika.channel.Channel) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_channel_open

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_channel_open
```

````

````{py:method} on_channel_closed(channel: pika.channel.Channel, reason: Exception) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_channel_closed

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_channel_closed
```

````

````{py:method} declare_service_queue(frame: pika.frame.Method) -> None
:canonical: nuropb.rmq_transport.RMQTransport.declare_service_queue

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.declare_service_queue
```

````

````{py:method} on_service_queue_declareok(frame: pika.frame.Method, _userdata: str) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_service_queue_declareok

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_service_queue_declareok
```

````

````{py:method} declare_response_queue() -> None
:canonical: nuropb.rmq_transport.RMQTransport.declare_response_queue

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.declare_response_queue
```

````

````{py:method} on_response_queue_declareok(frame: pika.frame.Method, _userdata: str) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_response_queue_declareok

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_response_queue_declareok
```

````

````{py:method} on_bindok(_frame: pika.frame.Method, userdata: str) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_bindok

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_bindok
```

````

````{py:method} on_basic_qos_ok(_frame: pika.frame.Method) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_basic_qos_ok

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_basic_qos_ok
```

````

````{py:method} on_consumer_cancelled(method_frame: pika.frame.Method) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_consumer_cancelled

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_consumer_cancelled
```

````

````{py:method} on_message_returned(channel: pika.channel.Channel, method: pika.spec.Basic.Return, properties: pika.spec.BasicProperties, body: bytes) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_message_returned

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_message_returned
```

````

````{py:method} send_message(payload: typing.Dict[str, typing.Any], expiry: typing.Optional[int] = None, priority: typing.Optional[int] = None, encoding: str = 'json', encrypted: bool = False) -> None
:canonical: nuropb.rmq_transport.RMQTransport.send_message

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.send_message
```

````

````{py:method} acknowledge_service_message(channel: pika.channel.Channel, delivery_tag: int, action: typing.Literal[ack, nack, reject], redelivered: bool) -> None
:canonical: nuropb.rmq_transport.RMQTransport.acknowledge_service_message
:classmethod:

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.acknowledge_service_message
```

````

````{py:method} metadata_metrics(metadata: typing.Dict[str, typing.Any]) -> None
:canonical: nuropb.rmq_transport.RMQTransport.metadata_metrics
:classmethod:

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.metadata_metrics
```

````

````{py:method} on_service_message_complete(channel: pika.channel.Channel, basic_deliver: pika.spec.Basic.Deliver, properties: pika.spec.BasicProperties, private_metadata: typing.Dict[str, typing.Any], response_messages: typing.List[nuropb.interface.TransportRespondPayload], acknowledgement: nuropb.interface.AcknowledgeAction) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_service_message_complete

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_service_message_complete
```

````

````{py:method} on_service_message(queue_name: str, channel: pika.channel.Channel, basic_deliver: pika.spec.Basic.Deliver, properties: pika.spec.BasicProperties, body: bytes) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_service_message

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_service_message
```

````

````{py:method} on_response_message_complete(channel: pika.channel.Channel, basic_deliver: pika.spec.Basic.Deliver, properties: pika.spec.BasicProperties, private_metadata: typing.Dict[str, typing.Any], response_messages: typing.List[nuropb.interface.TransportRespondPayload], acknowledgement: nuropb.interface.AcknowledgeAction) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_response_message_complete

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_response_message_complete
```

````

````{py:method} on_response_message(_queue_name: str, channel: pika.channel.Channel, basic_deliver: pika.spec.Basic.Deliver, properties: pika.spec.BasicProperties, body: bytes) -> None
:canonical: nuropb.rmq_transport.RMQTransport.on_response_message

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.on_response_message
```

````

````{py:method} stop_consuming() -> None
:canonical: nuropb.rmq_transport.RMQTransport.stop_consuming
:async:

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.stop_consuming
```

````

````{py:method} close_channel() -> None
:canonical: nuropb.rmq_transport.RMQTransport.close_channel

```{autodoc2-docstring} nuropb.rmq_transport.RMQTransport.close_channel
```

````

`````
