# Background

## Where does the name originate from?
NuroPb is a contraction of the term nervous [system] and the scientific symbol for Lead and its
association with plumbing. So then NuroPb, the plumbing, routing and communications for connected services.

## History, Pattern and Approach
NuroPb is a pattern and approach that supports event driven and service mesh engineering requirements. The
early roots evolved in the 2000's, and during the 2010's the pattern was used to drive hedge funds, startups,
banks and crypto and blockchain ventures. It's core development is in Python, and the pattern has been used
alongside Java, JavasScript and GoLang, Unfortunately those efforts are copyrighted. Any platform with support
for RabbitMQ should be able to implement the pattern and exist on the same mesh as Python Services.

RabbitMQ is the underlying message broker for the NuroPb service mesh library. Various message brokers and
broker-less tools and approaches have been tried with the nuropb pattern. Some of these are Kafka, MQSeries and
ZeroMQ. RabbitMQ's AMPQ routing capabilities, low maintenance and robustness have proved the test of time. With
RabbitMQ's release of the streams feature, and offering message/logs streaming capabilities, there are new
and interesting opportunities all on a single platform.

**Why not Kafka**? Kafka is a great tool, but it's not a message broker. It's a distributed log stream and
probably one of the best available. There are many use cases where NuroPb + RabbitMQ would integrate very
nicely alongside Kafka. Especially inter-process rpc and orderless event driven flows that are orchestrated
by NuroPb and ordered log/event streaming over Kafka. Kafka is also been used as to ingest all nuropb traffic
for auditing and tracing.