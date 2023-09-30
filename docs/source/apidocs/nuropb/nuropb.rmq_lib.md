# {py:mod}`nuropb.rmq_lib`

```{py:module} nuropb.rmq_lib
```

```{autodoc2-docstring} nuropb.rmq_lib
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`build_amqp_url <nuropb.rmq_lib.build_amqp_url>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.build_amqp_url
    :summary:
    ```
* - {py:obj}`build_rmq_api_url <nuropb.rmq_lib.build_rmq_api_url>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.build_rmq_api_url
    :summary:
    ```
* - {py:obj}`rmq_api_url_from_amqp_url <nuropb.rmq_lib.rmq_api_url_from_amqp_url>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.rmq_api_url_from_amqp_url
    :summary:
    ```
* - {py:obj}`get_client_connection_properties <nuropb.rmq_lib.get_client_connection_properties>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.get_client_connection_properties
    :summary:
    ```
* - {py:obj}`get_connection_parameters <nuropb.rmq_lib.get_connection_parameters>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.get_connection_parameters
    :summary:
    ```
* - {py:obj}`management_api_session_info <nuropb.rmq_lib.management_api_session_info>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.management_api_session_info
    :summary:
    ```
* - {py:obj}`blocking_rabbitmq_channel <nuropb.rmq_lib.blocking_rabbitmq_channel>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.blocking_rabbitmq_channel
    :summary:
    ```
* - {py:obj}`configure_nuropb_rmq <nuropb.rmq_lib.configure_nuropb_rmq>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.configure_nuropb_rmq
    :summary:
    ```
* - {py:obj}`nack_message <nuropb.rmq_lib.nack_message>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.nack_message
    :summary:
    ```
* - {py:obj}`reject_message <nuropb.rmq_lib.reject_message>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.reject_message
    :summary:
    ```
* - {py:obj}`ack_message <nuropb.rmq_lib.ack_message>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.ack_message
    :summary:
    ```
* - {py:obj}`get_virtual_host_queues <nuropb.rmq_lib.get_virtual_host_queues>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.get_virtual_host_queues
    :summary:
    ```
* - {py:obj}`get_virtual_hosts <nuropb.rmq_lib.get_virtual_hosts>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.get_virtual_hosts
    :summary:
    ```
* - {py:obj}`create_virtual_host <nuropb.rmq_lib.create_virtual_host>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.create_virtual_host
    :summary:
    ```
* - {py:obj}`delete_virtual_host <nuropb.rmq_lib.delete_virtual_host>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.delete_virtual_host
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <nuropb.rmq_lib.logger>`
  - ```{autodoc2-docstring} nuropb.rmq_lib.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: nuropb.rmq_lib.logger
:value: >
   None

```{autodoc2-docstring} nuropb.rmq_lib.logger
```

````

````{py:function} build_amqp_url(host: str, port: str | int, username: str, password: str, vhost: str) -> str
:canonical: nuropb.rmq_lib.build_amqp_url

```{autodoc2-docstring} nuropb.rmq_lib.build_amqp_url
```
````

````{py:function} build_rmq_api_url(scheme: str, host: str, port: str | int, username: str | None, password: str | None) -> str
:canonical: nuropb.rmq_lib.build_rmq_api_url

```{autodoc2-docstring} nuropb.rmq_lib.build_rmq_api_url
```
````

````{py:function} rmq_api_url_from_amqp_url(amqp_url: str, scheme: typing.Optional[str] = None, port: typing.Optional[int | str] = None) -> str
:canonical: nuropb.rmq_lib.rmq_api_url_from_amqp_url

```{autodoc2-docstring} nuropb.rmq_lib.rmq_api_url_from_amqp_url
```
````

````{py:function} get_client_connection_properties(name: typing.Optional[str] = None, instance_id: typing.Optional[str] = None, client_only: typing.Optional[bool] = None) -> typing.Dict[str, str]
:canonical: nuropb.rmq_lib.get_client_connection_properties

```{autodoc2-docstring} nuropb.rmq_lib.get_client_connection_properties
```
````

````{py:function} get_connection_parameters(amqp_url: str | typing.Dict[str, typing.Any], name: typing.Optional[str] = None, instance_id: typing.Optional[str] = None, client_only: typing.Optional[bool] = None, **overrides: typing.Any) -> pika.ConnectionParameters | pika.URLParameters
:canonical: nuropb.rmq_lib.get_connection_parameters

```{autodoc2-docstring} nuropb.rmq_lib.get_connection_parameters
```
````

````{py:function} management_api_session_info(scheme: str, host: str, port: str | int, username: typing.Optional[str] = None, password: typing.Optional[str] = None, bearer_token: typing.Optional[str] = None, verify: bool = False, **headers: typing.Any) -> typing.Dict[str, typing.Any]
:canonical: nuropb.rmq_lib.management_api_session_info

```{autodoc2-docstring} nuropb.rmq_lib.management_api_session_info
```
````

````{py:function} blocking_rabbitmq_channel(rmq_url: str | typing.Dict[str, typing.Any]) -> pika.channel.Channel
:canonical: nuropb.rmq_lib.blocking_rabbitmq_channel

```{autodoc2-docstring} nuropb.rmq_lib.blocking_rabbitmq_channel
```
````

````{py:function} configure_nuropb_rmq(rmq_url: str | typing.Dict[str, typing.Any], events_exchange: str, rpc_exchange: str, dl_exchange: str, dl_queue: str, **kwargs: typing.Any) -> bool
:canonical: nuropb.rmq_lib.configure_nuropb_rmq

```{autodoc2-docstring} nuropb.rmq_lib.configure_nuropb_rmq
```
````

````{py:function} nack_message(channel: pika.channel.Channel, delivery_tag: int, properties: pika.spec.BasicProperties, mesg: nuropb.interface.PayloadDict | None, error: Exception | None = None) -> None
:canonical: nuropb.rmq_lib.nack_message

```{autodoc2-docstring} nuropb.rmq_lib.nack_message
```
````

````{py:function} reject_message(channel: pika.channel.Channel, delivery_tag: int, properties: pika.spec.BasicProperties, mesg: nuropb.interface.PayloadDict | None, error: Exception | None = None) -> None
:canonical: nuropb.rmq_lib.reject_message

```{autodoc2-docstring} nuropb.rmq_lib.reject_message
```
````

````{py:function} ack_message(channel: pika.channel.Channel, delivery_tag: int, properties: pika.spec.BasicProperties, mesg: nuropb.interface.PayloadDict | None, error: Exception | None = None) -> None
:canonical: nuropb.rmq_lib.ack_message

```{autodoc2-docstring} nuropb.rmq_lib.ack_message
```
````

````{py:function} get_virtual_host_queues(api_url: str, vhost_url: str) -> typing.Any | None
:canonical: nuropb.rmq_lib.get_virtual_host_queues

```{autodoc2-docstring} nuropb.rmq_lib.get_virtual_host_queues
```
````

````{py:function} get_virtual_hosts(api_url: str, vhost_url: str | typing.Dict[str, typing.Any]) -> typing.Any | None
:canonical: nuropb.rmq_lib.get_virtual_hosts

```{autodoc2-docstring} nuropb.rmq_lib.get_virtual_hosts
```
````

````{py:function} create_virtual_host(api_url: str, vhost_url: str | typing.Dict[str, typing.Any]) -> None
:canonical: nuropb.rmq_lib.create_virtual_host

```{autodoc2-docstring} nuropb.rmq_lib.create_virtual_host
```
````

````{py:function} delete_virtual_host(api_url: str, vhost_url: str | typing.Dict[str, typing.Any]) -> None
:canonical: nuropb.rmq_lib.delete_virtual_host

```{autodoc2-docstring} nuropb.rmq_lib.delete_virtual_host
```
````
