# Roadmap Features

* Service Discovery - Service Mesh
* Self Describing Services and Service Registry
* Service Instance Health Checks
* Service Instance Metrics
* NuroPb Metric Streaming
* NuroPb Metric Dashboard

## Experimental Paradigms 

* Call Again (retry v. call-again)
* Split (Map / Reduce)

### Call Again
When a message is nacked and requeued, there is no current way to track how many
times this may have occurred for the same message. To ensure stability, 
predictability and to limit the abuse of patterns, the use of NuropbCallAgain is 
limited to once and only once. This is enforced at the transport layer. For RabbitMQ
if the incoming message is a requeued/redelivered message, and 
basic_deliver.redelivered is True. Call again for all redelivered messages will be 
rejected.

#### retry v call-again
Retry is a pattern that is used to ensure that a message is processed. It is currently
the view that if required, this is managed at the application level, and not at the 
transport layer. In NuroPb, call-again is a once and once only pattern that is managed 
from the transport where the underlying message broker supports redelivery.  