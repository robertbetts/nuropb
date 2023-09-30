# {py:mod}`nuropb.interface`

```{py:module} nuropb.interface
```

```{autodoc2-docstring} nuropb.interface
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ErrorDescriptionType <nuropb.interface.ErrorDescriptionType>`
  -
* - {py:obj}`EventType <nuropb.interface.EventType>`
  - ```{autodoc2-docstring} nuropb.interface.EventType
    :summary:
    ```
* - {py:obj}`RequestPayloadDict <nuropb.interface.RequestPayloadDict>`
  - ```{autodoc2-docstring} nuropb.interface.RequestPayloadDict
    :summary:
    ```
* - {py:obj}`CommandPayloadDict <nuropb.interface.CommandPayloadDict>`
  - ```{autodoc2-docstring} nuropb.interface.CommandPayloadDict
    :summary:
    ```
* - {py:obj}`EventPayloadDict <nuropb.interface.EventPayloadDict>`
  - ```{autodoc2-docstring} nuropb.interface.EventPayloadDict
    :summary:
    ```
* - {py:obj}`ResponsePayloadDict <nuropb.interface.ResponsePayloadDict>`
  - ```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict
    :summary:
    ```
* - {py:obj}`TransportServicePayload <nuropb.interface.TransportServicePayload>`
  - ```{autodoc2-docstring} nuropb.interface.TransportServicePayload
    :summary:
    ```
* - {py:obj}`TransportRespondPayload <nuropb.interface.TransportRespondPayload>`
  - ```{autodoc2-docstring} nuropb.interface.TransportRespondPayload
    :summary:
    ```
* - {py:obj}`NuropbInterface <nuropb.interface.NuropbInterface>`
  - ```{autodoc2-docstring} nuropb.interface.NuropbInterface
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <nuropb.interface.logger>`
  - ```{autodoc2-docstring} nuropb.interface.logger
    :summary:
    ```
* - {py:obj}`NUROPB_VERSION <nuropb.interface.NUROPB_VERSION>`
  - ```{autodoc2-docstring} nuropb.interface.NUROPB_VERSION
    :summary:
    ```
* - {py:obj}`NUROPB_PROTOCOL_VERSION <nuropb.interface.NUROPB_PROTOCOL_VERSION>`
  - ```{autodoc2-docstring} nuropb.interface.NUROPB_PROTOCOL_VERSION
    :summary:
    ```
* - {py:obj}`NUROPB_PROTOCOL_VERSIONS_SUPPORTED <nuropb.interface.NUROPB_PROTOCOL_VERSIONS_SUPPORTED>`
  - ```{autodoc2-docstring} nuropb.interface.NUROPB_PROTOCOL_VERSIONS_SUPPORTED
    :summary:
    ```
* - {py:obj}`NUROPB_MESSAGE_TYPES <nuropb.interface.NUROPB_MESSAGE_TYPES>`
  - ```{autodoc2-docstring} nuropb.interface.NUROPB_MESSAGE_TYPES
    :summary:
    ```
* - {py:obj}`NuropbSerializeType <nuropb.interface.NuropbSerializeType>`
  - ```{autodoc2-docstring} nuropb.interface.NuropbSerializeType
    :summary:
    ```
* - {py:obj}`NuropbMessageType <nuropb.interface.NuropbMessageType>`
  - ```{autodoc2-docstring} nuropb.interface.NuropbMessageType
    :summary:
    ```
* - {py:obj}`NuropbLifecycleState <nuropb.interface.NuropbLifecycleState>`
  - ```{autodoc2-docstring} nuropb.interface.NuropbLifecycleState
    :summary:
    ```
* - {py:obj}`PayloadDict <nuropb.interface.PayloadDict>`
  - ```{autodoc2-docstring} nuropb.interface.PayloadDict
    :summary:
    ```
* - {py:obj}`ServicePayloadTypes <nuropb.interface.ServicePayloadTypes>`
  - ```{autodoc2-docstring} nuropb.interface.ServicePayloadTypes
    :summary:
    ```
* - {py:obj}`ResponsePayloadTypes <nuropb.interface.ResponsePayloadTypes>`
  - ```{autodoc2-docstring} nuropb.interface.ResponsePayloadTypes
    :summary:
    ```
* - {py:obj}`ResultFutureResponsePayload <nuropb.interface.ResultFutureResponsePayload>`
  - ```{autodoc2-docstring} nuropb.interface.ResultFutureResponsePayload
    :summary:
    ```
* - {py:obj}`ResultFutureAny <nuropb.interface.ResultFutureAny>`
  - ```{autodoc2-docstring} nuropb.interface.ResultFutureAny
    :summary:
    ```
* - {py:obj}`AcknowledgeAction <nuropb.interface.AcknowledgeAction>`
  - ```{autodoc2-docstring} nuropb.interface.AcknowledgeAction
    :summary:
    ```
* - {py:obj}`AcknowledgeCallbackFunction <nuropb.interface.AcknowledgeCallbackFunction>`
  - ```{autodoc2-docstring} nuropb.interface.AcknowledgeCallbackFunction
    :summary:
    ```
* - {py:obj}`MessageCompleteFunction <nuropb.interface.MessageCompleteFunction>`
  - ```{autodoc2-docstring} nuropb.interface.MessageCompleteFunction
    :summary:
    ```
* - {py:obj}`MessageCallbackFunction <nuropb.interface.MessageCallbackFunction>`
  - ```{autodoc2-docstring} nuropb.interface.MessageCallbackFunction
    :summary:
    ```
* - {py:obj}`ConnectionCallbackFunction <nuropb.interface.ConnectionCallbackFunction>`
  - ```{autodoc2-docstring} nuropb.interface.ConnectionCallbackFunction
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: nuropb.interface.logger
:value: >
   None

```{autodoc2-docstring} nuropb.interface.logger
```

````

````{py:data} NUROPB_VERSION
:canonical: nuropb.interface.NUROPB_VERSION
:value: >
   '0.1.7'

```{autodoc2-docstring} nuropb.interface.NUROPB_VERSION
```

````

````{py:data} NUROPB_PROTOCOL_VERSION
:canonical: nuropb.interface.NUROPB_PROTOCOL_VERSION
:value: >
   '0.1.1'

```{autodoc2-docstring} nuropb.interface.NUROPB_PROTOCOL_VERSION
```

````

````{py:data} NUROPB_PROTOCOL_VERSIONS_SUPPORTED
:canonical: nuropb.interface.NUROPB_PROTOCOL_VERSIONS_SUPPORTED
:value: >
   ('0.1.1',)

```{autodoc2-docstring} nuropb.interface.NUROPB_PROTOCOL_VERSIONS_SUPPORTED
```

````

````{py:data} NUROPB_MESSAGE_TYPES
:canonical: nuropb.interface.NUROPB_MESSAGE_TYPES
:value: >
   ('request', 'response', 'event', 'command')

```{autodoc2-docstring} nuropb.interface.NUROPB_MESSAGE_TYPES
```

````

````{py:data} NuropbSerializeType
:canonical: nuropb.interface.NuropbSerializeType
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbSerializeType
```

````

````{py:data} NuropbMessageType
:canonical: nuropb.interface.NuropbMessageType
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbMessageType
```

````

````{py:data} NuropbLifecycleState
:canonical: nuropb.interface.NuropbLifecycleState
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbLifecycleState
```

````

`````{py:class} ErrorDescriptionType()
:canonical: nuropb.interface.ErrorDescriptionType

Bases: {py:obj}`typing.TypedDict`

````{py:attribute} error
:canonical: nuropb.interface.ErrorDescriptionType.error
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ErrorDescriptionType.error
```

````

````{py:attribute} description
:canonical: nuropb.interface.ErrorDescriptionType.description
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ErrorDescriptionType.description
```

````

````{py:attribute} context
:canonical: nuropb.interface.ErrorDescriptionType.context
:type: typing.Optional[typing.Dict[str, typing.Any]]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ErrorDescriptionType.context
```

````

`````

`````{py:class} EventType()
:canonical: nuropb.interface.EventType

Bases: {py:obj}`typing.TypedDict`

```{autodoc2-docstring} nuropb.interface.EventType
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.EventType.__init__
```

````{py:attribute} topic
:canonical: nuropb.interface.EventType.topic
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventType.topic
```

````

````{py:attribute} payload
:canonical: nuropb.interface.EventType.payload
:type: typing.Any
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventType.payload
```

````

````{py:attribute} target
:canonical: nuropb.interface.EventType.target
:type: typing.Optional[typing.List[typing.Any]]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventType.target
```

````

`````

`````{py:class} RequestPayloadDict()
:canonical: nuropb.interface.RequestPayloadDict

Bases: {py:obj}`typing.TypedDict`

```{autodoc2-docstring} nuropb.interface.RequestPayloadDict
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.RequestPayloadDict.__init__
```

````{py:attribute} tag
:canonical: nuropb.interface.RequestPayloadDict.tag
:type: typing.Literal[request]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.RequestPayloadDict.tag
```

````

````{py:attribute} correlation_id
:canonical: nuropb.interface.RequestPayloadDict.correlation_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.RequestPayloadDict.correlation_id
```

````

````{py:attribute} context
:canonical: nuropb.interface.RequestPayloadDict.context
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.RequestPayloadDict.context
```

````

````{py:attribute} trace_id
:canonical: nuropb.interface.RequestPayloadDict.trace_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.RequestPayloadDict.trace_id
```

````

````{py:attribute} service
:canonical: nuropb.interface.RequestPayloadDict.service
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.RequestPayloadDict.service
```

````

````{py:attribute} method
:canonical: nuropb.interface.RequestPayloadDict.method
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.RequestPayloadDict.method
```

````

````{py:attribute} params
:canonical: nuropb.interface.RequestPayloadDict.params
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.RequestPayloadDict.params
```

````

`````

`````{py:class} CommandPayloadDict()
:canonical: nuropb.interface.CommandPayloadDict

Bases: {py:obj}`typing.TypedDict`

```{autodoc2-docstring} nuropb.interface.CommandPayloadDict
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.CommandPayloadDict.__init__
```

````{py:attribute} tag
:canonical: nuropb.interface.CommandPayloadDict.tag
:type: typing.Literal[command]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.CommandPayloadDict.tag
```

````

````{py:attribute} correlation_id
:canonical: nuropb.interface.CommandPayloadDict.correlation_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.CommandPayloadDict.correlation_id
```

````

````{py:attribute} context
:canonical: nuropb.interface.CommandPayloadDict.context
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.CommandPayloadDict.context
```

````

````{py:attribute} trace_id
:canonical: nuropb.interface.CommandPayloadDict.trace_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.CommandPayloadDict.trace_id
```

````

````{py:attribute} service
:canonical: nuropb.interface.CommandPayloadDict.service
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.CommandPayloadDict.service
```

````

````{py:attribute} method
:canonical: nuropb.interface.CommandPayloadDict.method
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.CommandPayloadDict.method
```

````

````{py:attribute} params
:canonical: nuropb.interface.CommandPayloadDict.params
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.CommandPayloadDict.params
```

````

`````

`````{py:class} EventPayloadDict()
:canonical: nuropb.interface.EventPayloadDict

Bases: {py:obj}`typing.TypedDict`

```{autodoc2-docstring} nuropb.interface.EventPayloadDict
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.EventPayloadDict.__init__
```

````{py:attribute} tag
:canonical: nuropb.interface.EventPayloadDict.tag
:type: typing.Literal[nuropb.interface.EventPayloadDict.event]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventPayloadDict.tag
```

````

````{py:attribute} correlation_id
:canonical: nuropb.interface.EventPayloadDict.correlation_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventPayloadDict.correlation_id
```

````

````{py:attribute} context
:canonical: nuropb.interface.EventPayloadDict.context
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventPayloadDict.context
```

````

````{py:attribute} trace_id
:canonical: nuropb.interface.EventPayloadDict.trace_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventPayloadDict.trace_id
```

````

````{py:attribute} topic
:canonical: nuropb.interface.EventPayloadDict.topic
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventPayloadDict.topic
```

````

````{py:attribute} event
:canonical: nuropb.interface.EventPayloadDict.event
:type: typing.Any
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventPayloadDict.event
```

````

````{py:attribute} target
:canonical: nuropb.interface.EventPayloadDict.target
:type: typing.Optional[typing.List[typing.Any]]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.EventPayloadDict.target
```

````

`````

`````{py:class} ResponsePayloadDict()
:canonical: nuropb.interface.ResponsePayloadDict

Bases: {py:obj}`typing.TypedDict`

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict.__init__
```

````{py:attribute} tag
:canonical: nuropb.interface.ResponsePayloadDict.tag
:type: typing.Literal[response]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict.tag
```

````

````{py:attribute} correlation_id
:canonical: nuropb.interface.ResponsePayloadDict.correlation_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict.correlation_id
```

````

````{py:attribute} context
:canonical: nuropb.interface.ResponsePayloadDict.context
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict.context
```

````

````{py:attribute} trace_id
:canonical: nuropb.interface.ResponsePayloadDict.trace_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict.trace_id
```

````

````{py:attribute} result
:canonical: nuropb.interface.ResponsePayloadDict.result
:type: typing.Any
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict.result
```

````

````{py:attribute} error
:canonical: nuropb.interface.ResponsePayloadDict.error
:type: typing.Optional[typing.Dict[str, typing.Any]]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict.error
```

````

````{py:attribute} warning
:canonical: nuropb.interface.ResponsePayloadDict.warning
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict.warning
```

````

````{py:attribute} reply_to
:canonical: nuropb.interface.ResponsePayloadDict.reply_to
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResponsePayloadDict.reply_to
```

````

`````

````{py:data} PayloadDict
:canonical: nuropb.interface.PayloadDict
:value: >
   None

```{autodoc2-docstring} nuropb.interface.PayloadDict
```

````

````{py:data} ServicePayloadTypes
:canonical: nuropb.interface.ServicePayloadTypes
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ServicePayloadTypes
```

````

````{py:data} ResponsePayloadTypes
:canonical: nuropb.interface.ResponsePayloadTypes
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResponsePayloadTypes
```

````

`````{py:class} TransportServicePayload()
:canonical: nuropb.interface.TransportServicePayload

Bases: {py:obj}`typing.TypedDict`

```{autodoc2-docstring} nuropb.interface.TransportServicePayload
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.TransportServicePayload.__init__
```

````{py:attribute} nuropb_protocol
:canonical: nuropb.interface.TransportServicePayload.nuropb_protocol
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportServicePayload.nuropb_protocol
```

````

````{py:attribute} correlation_id
:canonical: nuropb.interface.TransportServicePayload.correlation_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportServicePayload.correlation_id
```

````

````{py:attribute} trace_id
:canonical: nuropb.interface.TransportServicePayload.trace_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportServicePayload.trace_id
```

````

````{py:attribute} ttl
:canonical: nuropb.interface.TransportServicePayload.ttl
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportServicePayload.ttl
```

````

````{py:attribute} nuropb_type
:canonical: nuropb.interface.TransportServicePayload.nuropb_type
:type: nuropb.interface.NuropbMessageType
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportServicePayload.nuropb_type
```

````

````{py:attribute} nuropb_payload
:canonical: nuropb.interface.TransportServicePayload.nuropb_payload
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportServicePayload.nuropb_payload
```

````

`````

`````{py:class} TransportRespondPayload()
:canonical: nuropb.interface.TransportRespondPayload

Bases: {py:obj}`typing.TypedDict`

```{autodoc2-docstring} nuropb.interface.TransportRespondPayload
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.TransportRespondPayload.__init__
```

````{py:attribute} nuropb_protocol
:canonical: nuropb.interface.TransportRespondPayload.nuropb_protocol
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportRespondPayload.nuropb_protocol
```

````

````{py:attribute} correlation_id
:canonical: nuropb.interface.TransportRespondPayload.correlation_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportRespondPayload.correlation_id
```

````

````{py:attribute} trace_id
:canonical: nuropb.interface.TransportRespondPayload.trace_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportRespondPayload.trace_id
```

````

````{py:attribute} ttl
:canonical: nuropb.interface.TransportRespondPayload.ttl
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportRespondPayload.ttl
```

````

````{py:attribute} nuropb_type
:canonical: nuropb.interface.TransportRespondPayload.nuropb_type
:type: nuropb.interface.NuropbMessageType
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportRespondPayload.nuropb_type
```

````

````{py:attribute} nuropb_payload
:canonical: nuropb.interface.TransportRespondPayload.nuropb_payload
:type: nuropb.interface.ResponsePayloadTypes
:value: >
   None

```{autodoc2-docstring} nuropb.interface.TransportRespondPayload.nuropb_payload
```

````

`````

````{py:data} ResultFutureResponsePayload
:canonical: nuropb.interface.ResultFutureResponsePayload
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResultFutureResponsePayload
```

````

````{py:data} ResultFutureAny
:canonical: nuropb.interface.ResultFutureAny
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ResultFutureAny
```

````

````{py:data} AcknowledgeAction
:canonical: nuropb.interface.AcknowledgeAction
:value: >
   None

```{autodoc2-docstring} nuropb.interface.AcknowledgeAction
```

````

````{py:data} AcknowledgeCallbackFunction
:canonical: nuropb.interface.AcknowledgeCallbackFunction
:value: >
   None

```{autodoc2-docstring} nuropb.interface.AcknowledgeCallbackFunction
```

````

````{py:data} MessageCompleteFunction
:canonical: nuropb.interface.MessageCompleteFunction
:value: >
   None

```{autodoc2-docstring} nuropb.interface.MessageCompleteFunction
```

````

````{py:data} MessageCallbackFunction
:canonical: nuropb.interface.MessageCallbackFunction
:value: >
   None

```{autodoc2-docstring} nuropb.interface.MessageCallbackFunction
```

````

````{py:data} ConnectionCallbackFunction
:canonical: nuropb.interface.ConnectionCallbackFunction
:value: >
   None

```{autodoc2-docstring} nuropb.interface.ConnectionCallbackFunction
```

````

`````{py:exception} NuropbException(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbException

Bases: {py:obj}`Exception`

```{autodoc2-docstring} nuropb.interface.NuropbException
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbException.__init__
```

````{py:attribute} description
:canonical: nuropb.interface.NuropbException.description
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbException.description
```

````

````{py:attribute} payload
:canonical: nuropb.interface.NuropbException.payload
:type: nuropb.interface.PayloadDict | nuropb.interface.TransportServicePayload | nuropb.interface.TransportRespondPayload | typing.Dict[str, typing.Any] | None
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbException.payload
```

````

````{py:attribute} exception
:canonical: nuropb.interface.NuropbException.exception
:type: BaseException | None
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbException.exception
```

````

````{py:method} to_dict() -> typing.Dict[str, typing.Any]
:canonical: nuropb.interface.NuropbException.to_dict

```{autodoc2-docstring} nuropb.interface.NuropbException.to_dict
```

````

`````

````{py:exception} NuropbTimeoutError(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbTimeoutError

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbTimeoutError
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbTimeoutError.__init__
```

````

`````{py:exception} NuropbTransportError(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None, close_connection: bool = False)
:canonical: nuropb.interface.NuropbTransportError

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbTransportError
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbTransportError.__init__
```

````{py:attribute} _close_connection
:canonical: nuropb.interface.NuropbTransportError._close_connection
:type: bool
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbTransportError._close_connection
```

````

````{py:property} close_connection
:canonical: nuropb.interface.NuropbTransportError.close_connection
:type: bool

```{autodoc2-docstring} nuropb.interface.NuropbTransportError.close_connection
```

````

`````

````{py:exception} NuropbMessageError(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbMessageError

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbMessageError
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbMessageError.__init__
```

````

````{py:exception} NuropbHandlingError(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbHandlingError

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbHandlingError
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbHandlingError.__init__
```

````

````{py:exception} NuropbDeprecatedError(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbDeprecatedError

Bases: {py:obj}`nuropb.interface.NuropbHandlingError`

```{autodoc2-docstring} nuropb.interface.NuropbDeprecatedError
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbDeprecatedError.__init__
```

````

````{py:exception} NuropbValidationError(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbValidationError

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbValidationError
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbValidationError.__init__
```

````

````{py:exception} NuropbAuthenticationError(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbAuthenticationError

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbAuthenticationError
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbAuthenticationError.__init__
```

````

````{py:exception} NuropbAuthorizationError(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbAuthorizationError

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbAuthorizationError
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbAuthorizationError.__init__
```

````

````{py:exception} NuropbNotDeliveredError(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbNotDeliveredError

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbNotDeliveredError
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbNotDeliveredError.__init__
```

````

````{py:exception} NuropbCallAgainReject(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbCallAgainReject

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbCallAgainReject
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbCallAgainReject.__init__
```

````

````{py:exception} NuropbCallAgain(description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.PayloadDict] = None, exception: typing.Optional[BaseException] = None)
:canonical: nuropb.interface.NuropbCallAgain

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbCallAgain
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbCallAgain.__init__
```

````

`````{py:exception} NuropbSuccess(result: typing.Any, description: typing.Optional[str] = None, payload: typing.Optional[nuropb.interface.ResponsePayloadDict] = None, events: typing.Optional[typing.List[nuropb.interface.EventType]] = None)
:canonical: nuropb.interface.NuropbSuccess

Bases: {py:obj}`nuropb.interface.NuropbException`

```{autodoc2-docstring} nuropb.interface.NuropbSuccess
```

```{rubric} Initialization
```

```{autodoc2-docstring} nuropb.interface.NuropbSuccess.__init__
```

````{py:attribute} result
:canonical: nuropb.interface.NuropbSuccess.result
:type: typing.Any
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbSuccess.result
```

````

````{py:attribute} payload
:canonical: nuropb.interface.NuropbSuccess.payload
:type: nuropb.interface.ResponsePayloadDict | None
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbSuccess.payload
```

````

````{py:attribute} events
:canonical: nuropb.interface.NuropbSuccess.events
:type: typing.List[nuropb.interface.EventType]
:value: >
   []

```{autodoc2-docstring} nuropb.interface.NuropbSuccess.events
```

````

`````

`````{py:class} NuropbInterface
:canonical: nuropb.interface.NuropbInterface

Bases: {py:obj}`abc.ABC`

```{autodoc2-docstring} nuropb.interface.NuropbInterface
```

````{py:attribute} _service_name
:canonical: nuropb.interface.NuropbInterface._service_name
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbInterface._service_name
```

````

````{py:attribute} _instance_id
:canonical: nuropb.interface.NuropbInterface._instance_id
:type: str
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbInterface._instance_id
```

````

````{py:attribute} _service_instance
:canonical: nuropb.interface.NuropbInterface._service_instance
:type: object
:value: >
   None

```{autodoc2-docstring} nuropb.interface.NuropbInterface._service_instance
```

````

````{py:property} service_name
:canonical: nuropb.interface.NuropbInterface.service_name
:type: str

```{autodoc2-docstring} nuropb.interface.NuropbInterface.service_name
```

````

````{py:property} instance_id
:canonical: nuropb.interface.NuropbInterface.instance_id
:type: str

```{autodoc2-docstring} nuropb.interface.NuropbInterface.instance_id
```

````

````{py:method} connect() -> None
:canonical: nuropb.interface.NuropbInterface.connect
:abstractmethod:
:async:

```{autodoc2-docstring} nuropb.interface.NuropbInterface.connect
```

````

````{py:method} disconnect() -> None
:canonical: nuropb.interface.NuropbInterface.disconnect
:abstractmethod:
:async:

```{autodoc2-docstring} nuropb.interface.NuropbInterface.disconnect
```

````

````{py:property} connected
:canonical: nuropb.interface.NuropbInterface.connected
:abstractmethod:
:type: bool

```{autodoc2-docstring} nuropb.interface.NuropbInterface.connected
```

````

````{py:property} is_leader
:canonical: nuropb.interface.NuropbInterface.is_leader
:abstractmethod:
:type: bool

```{autodoc2-docstring} nuropb.interface.NuropbInterface.is_leader
```

````

````{py:method} receive_transport_message(service_message: nuropb.interface.TransportServicePayload, message_complete_callback: nuropb.interface.MessageCompleteFunction, metadata: typing.Dict[str, typing.Any]) -> None
:canonical: nuropb.interface.NuropbInterface.receive_transport_message
:abstractmethod:

```{autodoc2-docstring} nuropb.interface.NuropbInterface.receive_transport_message
```

````

````{py:method} request(service: str, method: str, params: typing.Dict[str, typing.Any], context: typing.Dict[str, typing.Any], ttl: typing.Optional[int] = None, trace_id: typing.Optional[str] = None, rpc_response: bool = True) -> typing.Union[nuropb.interface.ResponsePayloadDict, typing.Any]
:canonical: nuropb.interface.NuropbInterface.request
:abstractmethod:
:async:

```{autodoc2-docstring} nuropb.interface.NuropbInterface.request
```

````

````{py:method} command(service: str, method: str, params: typing.Dict[str, typing.Any], context: typing.Dict[str, typing.Any], ttl: typing.Optional[int] = None, trace_id: typing.Optional[str] = None) -> None
:canonical: nuropb.interface.NuropbInterface.command
:abstractmethod:

```{autodoc2-docstring} nuropb.interface.NuropbInterface.command
```

````

````{py:method} publish_event(topic: str, event: typing.Any, context: typing.Dict[str, typing.Any], trace_id: typing.Optional[str] = None) -> None
:canonical: nuropb.interface.NuropbInterface.publish_event
:abstractmethod:

```{autodoc2-docstring} nuropb.interface.NuropbInterface.publish_event
```

````

`````
