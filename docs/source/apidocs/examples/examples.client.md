# {py:mod}`examples.client`

```{py:module} examples.client
```

```{autodoc2-docstring} examples.client
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`perform_request <examples.client.perform_request>`
  - ```{autodoc2-docstring} examples.client.perform_request
    :summary:
    ```
* - {py:obj}`perform_command <examples.client.perform_command>`
  - ```{autodoc2-docstring} examples.client.perform_command
    :summary:
    ```
* - {py:obj}`publish_event <examples.client.publish_event>`
  - ```{autodoc2-docstring} examples.client.publish_event
    :summary:
    ```
* - {py:obj}`main <examples.client.main>`
  - ```{autodoc2-docstring} examples.client.main
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <examples.client.logger>`
  - ```{autodoc2-docstring} examples.client.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: examples.client.logger
:value: >
   None

```{autodoc2-docstring} examples.client.logger
```

````

````{py:function} perform_request(api: nuropb.rmq_api.RMQAPI, encryption_test: bool = False)
:canonical: examples.client.perform_request
:async:

```{autodoc2-docstring} examples.client.perform_request
```
````

````{py:function} perform_command(api: nuropb.rmq_api.RMQAPI)
:canonical: examples.client.perform_command
:async:

```{autodoc2-docstring} examples.client.perform_command
```
````

````{py:function} publish_event(api: nuropb.rmq_api.RMQAPI)
:canonical: examples.client.publish_event
:async:

```{autodoc2-docstring} examples.client.publish_event
```
````

````{py:function} main()
:canonical: examples.client.main
:async:

```{autodoc2-docstring} examples.client.main
```
````
