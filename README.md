# NuroPb

## The neural plumbing for an Asynchronous, Distributed, Event Driven Service Mesh

[![codecov](https://codecov.io/gh/robertbetts/nuropb/branch/main/graph/badge.svg?token=DVSBZY794D)](https://codecov.io/gh/robertbetts/nuropb)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CodeFactor](https://www.codefactor.io/repository/github/robertbetts/nuropb/badge)](https://www.codefactor.io/repository/github/robertbetts/nuropb)
[![License: Apache 2.0](https://img.shields.io/pypi/l/giteo)](https://www.apache.org/licenses/LICENSE-2.0.txt)

You have a Python class that you want to make available as a service to consumers.
* You potentially want to scale this service horizontally many times over, likely at an unknown scale.
* Your service may need to communicate to other services too
* There are event driven processes and flows across your service landscape
* You have websocket endpoints that need to integrate seamlessly across a service mesh and event driven architecture
* A growing army of MlOps and Datascience engineers are joining, and they need to be able to integrate their 
  work into your systems.

If any of these are of interest to you then NuroPb is worth considering. NuroPb It falls into the domain of other 
tools and frameworks that abstract the plumbing and allow software engineers to focus on the problems they're hired 
to solve.

First and foremost NuroPb is a pattern and approach for an event driven and service mesh requirements. It's early 
roots developed in the 2000's and during the 2010's was used to drive hedge funds, startups, banks and crypto and 
blockchain businesses. It's core development is python, but it's been used with other languages too. Anything that 
can talk to RabbitMQ can be used with NuroPb.

RabbitMQ is the underlying message broker for the core of NuroPb. Various message brokers and broker-less 
tools and approaches have been tried, some of these are Kafka, MQSeries and ZeroMQ. RabbitMQ's AMPQ routing 
capabilities, low maintenance and robustness have proved the test of time. Now with the streams feature, and
and one able to navigate message logs, provides a powerful tool for debugging and monitoring.

Why not focus on Kafka? Kafka is a great tool, but it's not a message broker. It's a distributed log and 
probably the best one out there. Where like many use cases where NuroPb on RabbitMQ would play very nicely side 
by side with Kafka. With interprocess rpc and event driven processes and flows, orchestrated with NeroPb/RabbitMQ
and ordered event streaming over Kafka. Kafka has also proved a great tool for auditing and logging of NuroPB 
messages.

Where does the name come from? NuroPb is a contraction of the word neural and the scientific symbol for Lead. Lead
associated with plumbing. So NuroPb is a system's neural plumbing framework. 

## Getting started
Install the Python package
```
pip install nuropb
```




