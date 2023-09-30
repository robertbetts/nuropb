# {py:mod}`nuropb.service_runner`

```{py:module} nuropb.service_runner
```

```{autodoc2-docstring} nuropb.service_runner
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ServiceRunner <nuropb.service_runner.ServiceRunner>`
  - ```{autodoc2-docstring} nuropb.service_runner.ServiceRunner
    :summary:
    ```
* - {py:obj}`ServiceContainer <nuropb.service_runner.ServiceContainer>`
  -
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <nuropb.service_runner.logger>`
  - ```{autodoc2-docstring} nuropb.service_runner.logger
    :summary:
    ```
* - {py:obj}`LEADER_KEY <nuropb.service_runner.LEADER_KEY>`
  - ```{autodoc2-docstring} nuropb.service_runner.LEADER_KEY
    :summary:
    ```
* - {py:obj}`LEASE_TTL <nuropb.service_runner.LEASE_TTL>`
  - ```{autodoc2-docstring} nuropb.service_runner.LEASE_TTL
    :summary:
    ```
* - {py:obj}`ContainerRunningState <nuropb.service_runner.ContainerRunningState>`
  - ```{autodoc2-docstring} nuropb.service_runner.ContainerRunningState
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: nuropb.service_runner.logger
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.logger
```

````

````{py:data} LEADER_KEY
:canonical: nuropb.service_runner.LEADER_KEY
:value: >
   '/leader'

```{autodoc2-docstring} nuropb.service_runner.LEADER_KEY
```

````

````{py:data} LEASE_TTL
:canonical: nuropb.service_runner.LEASE_TTL
:value: >
   15

```{autodoc2-docstring} nuropb.service_runner.LEASE_TTL
```

````

`````{py:class} ServiceRunner
:canonical: nuropb.service_runner.ServiceRunner

```{autodoc2-docstring} nuropb.service_runner.ServiceRunner
```

````{py:attribute} service_name
:canonical: nuropb.service_runner.ServiceRunner.service_name
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceRunner.service_name
```

````

````{py:attribute} leader_id
:canonical: nuropb.service_runner.ServiceRunner.leader_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceRunner.leader_id
```

````

````{py:attribute} configured
:canonical: nuropb.service_runner.ServiceRunner.configured
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceRunner.configured
```

````

````{py:attribute} ready
:canonical: nuropb.service_runner.ServiceRunner.ready
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceRunner.ready
```

````

````{py:attribute} consume
:canonical: nuropb.service_runner.ServiceRunner.consume
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceRunner.consume
```

````

````{py:attribute} hw_mark
:canonical: nuropb.service_runner.ServiceRunner.hw_mark
:type: int
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceRunner.hw_mark
```

````

````{py:attribute} _etc_client
:canonical: nuropb.service_runner.ServiceRunner._etc_client
:type: etcd3.Client
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceRunner._etc_client
```

````

`````

````{py:data} ContainerRunningState
:canonical: nuropb.service_runner.ContainerRunningState
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ContainerRunningState
```

````

`````{py:class} ServiceContainer(rmq_api_url: str, instance: nuropb.rmq_api.RMQAPI, etcd_config: typing.Optional[typing.Dict[str, typing.Any]] = None)
:canonical: nuropb.service_runner.ServiceContainer

Bases: {py:obj}`nuropb.service_runner.ServiceRunner`

````{py:attribute} _instance
:canonical: nuropb.service_runner.ServiceContainer._instance
:type: nuropb.rmq_api.RMQAPI
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._instance
```

````

````{py:attribute} _rmq_api_url
:canonical: nuropb.service_runner.ServiceContainer._rmq_api_url
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._rmq_api_url
```

````

````{py:attribute} _service_name
:canonical: nuropb.service_runner.ServiceContainer._service_name
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._service_name
```

````

````{py:attribute} _transport
:canonical: nuropb.service_runner.ServiceContainer._transport
:type: nuropb.rmq_transport.RMQTransport
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._transport
```

````

````{py:attribute} _running_state
:canonical: nuropb.service_runner.ServiceContainer._running_state
:type: nuropb.service_runner.ContainerRunningState
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._running_state
```

````

````{py:attribute} _rmq_config_ok
:canonical: nuropb.service_runner.ServiceContainer._rmq_config_ok
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._rmq_config_ok
```

````

````{py:attribute} _shutdown
:canonical: nuropb.service_runner.ServiceContainer._shutdown
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._shutdown
```

````

````{py:attribute} _is_leader
:canonical: nuropb.service_runner.ServiceContainer._is_leader
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._is_leader
```

````

````{py:attribute} _leader_reference
:canonical: nuropb.service_runner.ServiceContainer._leader_reference
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._leader_reference
```

````

````{py:attribute} _etcd_config
:canonical: nuropb.service_runner.ServiceContainer._etcd_config
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._etcd_config
```

````

````{py:attribute} _etcd_client
:canonical: nuropb.service_runner.ServiceContainer._etcd_client
:type: etcd3.Client | None
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._etcd_client
```

````

````{py:attribute} _etcd_lease
:canonical: nuropb.service_runner.ServiceContainer._etcd_lease
:type: etcd3.stateful.lease.Lease | None
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._etcd_lease
```

````

````{py:attribute} _etcd_watcher
:canonical: nuropb.service_runner.ServiceContainer._etcd_watcher
:type: etcd3.stateful.watch.Watcher | None
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._etcd_watcher
```

````

````{py:attribute} _etcd_prefix
:canonical: nuropb.service_runner.ServiceContainer._etcd_prefix
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._etcd_prefix
```

````

````{py:attribute} _container_running_future
:canonical: nuropb.service_runner.ServiceContainer._container_running_future
:type: typing.Awaitable[bool] | None
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._container_running_future
```

````

````{py:attribute} _container_shutdown_future
:canonical: nuropb.service_runner.ServiceContainer._container_shutdown_future
:type: typing.Awaitable[bool] | None
:value: >
   None

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer._container_shutdown_future
```

````

````{py:property} running_state
:canonical: nuropb.service_runner.ServiceContainer.running_state
:type: nuropb.service_runner.ContainerRunningState

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer.running_state
```

````

````{py:method} init_etcd(on_startup: bool = True) -> bool
:canonical: nuropb.service_runner.ServiceContainer.init_etcd
:async:

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer.init_etcd
```

````

````{py:method} nominate_as_leader() -> None
:canonical: nuropb.service_runner.ServiceContainer.nominate_as_leader

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer.nominate_as_leader
```

````

````{py:method} update_etcd_service_property(key: str, value: typing.Any) -> bool
:canonical: nuropb.service_runner.ServiceContainer.update_etcd_service_property

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer.update_etcd_service_property
```

````

````{py:method} check_and_configure_rmq() -> None
:canonical: nuropb.service_runner.ServiceContainer.check_and_configure_rmq

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer.check_and_configure_rmq
```

````

````{py:method} etcd_event_handler(event: etcd3.stateful.watch.Event) -> None
:canonical: nuropb.service_runner.ServiceContainer.etcd_event_handler

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer.etcd_event_handler
```

````

````{py:method} startup_steps() -> None
:canonical: nuropb.service_runner.ServiceContainer.startup_steps
:async:

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer.startup_steps
```

````

````{py:method} start() -> bool
:canonical: nuropb.service_runner.ServiceContainer.start
:async:

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer.start
```

````

````{py:method} stop() -> None
:canonical: nuropb.service_runner.ServiceContainer.stop
:async:

```{autodoc2-docstring} nuropb.service_runner.ServiceContainer.stop
```

````

`````
