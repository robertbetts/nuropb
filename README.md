# NuroPb

## The nervous system and plumbing for an Asynchronous, Distributed, Event Driven, Service Mesh

[![codecov](https://codecov.io/gh/robertbetts/nuropb/branch/main/graph/badge.svg?token=DVSBZY794D)](https://codecov.io/gh/robertbetts/nuropb)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CodeFactor](https://www.codefactor.io/repository/github/robertbetts/nuropb/badge)](https://www.codefactor.io/repository/github/robertbetts/nuropb)
[![License: Apache 2.0](https://img.shields.io/pypi/l/giteo)](https://www.apache.org/licenses/LICENSE-2.0.txt)

Do you have a Python class that you want to make available as a service to consumers or other services, or
* You potentially want to scale a service horizontally many times over, likely at an unknown scale.
* Your service may need to communicate to other services
* There are event driven processes and flows across your service landscape
* You have websocket endpoints that need to integrate seamlessly across a service mesh and event driven architecture
* A growing army of Ml-Ops and Datascience engineers are joining, with the need to to integrate their efforts
  across many systems.
* Needing a service proxy that bridges cloud VPNs and on-premise networks 

If any of these are of interest to you, then NuroPb is worth considering. NuroPb It falls into the domain of  
tools and frameworks for the abstraction of integration plumbing, enabling software engineers to focus on the 
problems they're hired to solve.

## Where does the name originate from? 
NuroPb is a contraction of the term nervous system and the scientific symbol for Lead. Lead
associated with plumbing. So NuroPb is a system's nervous system and plumbing.

## Pattern and Approach
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

## Getting started
The best way to get started is to look at the examples and the `examples/README.md` file. 

As a super quick reference this si what you need to get started:
* Python >= 3.10
* RabbitMQ >= 3.8.0 + Management Plugin
* `pip install nuropb`

This code block is an example of a client and server running in the same python file. 
```python
import logging
from typing import Any, Dict
from uuid import uuid4
import asyncio

from nuropb.contexts.context_manager import NuropbContextManager
from nuropb.contexts.context_manager_decorator import nuropb_context
from nuropb.contexts.describe import publish_to_mesh
from nuropb.rmq_api import RMQAPI

logger = logging.getLogger("nuropb-all-in-one")


def get_claims_from_token(bearer_token: str) -> Dict[str, Any] | None:
    """ This is a stub for the required implentation of validating and decoding the bearer token
    """
    _ = bearer_token
    return {
        "sub": "test_user",
        "user_id": "test_user",
        "scope": "openid, profile",
        "roles": "user, admin",
    }


class QuickExampleService:
    _service_name = "quick-example"
    _instance_id = uuid4().hex

    @nuropb_context
    @publish_to_mesh(authorise_func=get_claims_from_token)
    def test_requires_user_claims(self, ctx, **kwargs: Any) -> str:
        logger.info("test_requires_user_claims called")
        assert isinstance(ctx, NuropbContextManager)
        return f"hello {ctx.user_claims['user_id']}"

    def test_method(self, param1, param2: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("test_method called")
        _ = self
        return {
            "param1": param1,
            "param2": param2,
            "reply": "response from test_method",
        }


async def main():
    logging.info("All in one example done")
    amqp_url = "amqp://guest:guest@localhost:5672/nuropb-example"
    service_instance = QuickExampleService()
    transport_settings = {
        "rpc_bindings": [service_instance._service_name],
    }
    service_api = RMQAPI(
        service_instance=service_instance,
        service_name=service_instance._service_name,
        instance_id=service_instance._instance_id,
        amqp_url=amqp_url,
        transport_settings=transport_settings,
    )
    await service_api.connect()
    logger.info("Service Ready")

    client_api = RMQAPI(
        amqp_url=amqp_url,
    )
    await client_api.connect()
    logger.info("Client connected")

    context = {
        "Authorization": "Bearer 1234567890",
    }
    response = await client_api.request(
        service="quick-example",
        method="test_requires_user_claims",
        params={},
        context=context,
    )
    logger.info(f"Response: {response}")

    response = await client_api.request(
        service="quick-example",
        method="test_method",
        params={
            "param1": "value1",
            "param2": {
                "param2a": "value2a",
            }
        },
        context={},
    )
    logger.info(f"Response: {response}")

    await client_api.disconnect()
    await service_api.disconnect()

    logging.info("All in one example done")


if __name__ == "__main__":
    log_format = (
        "%(levelname).1s %(asctime)s %(name) -25s %(funcName) "
        "-35s %(lineno) -5d: %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("etcd3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    asyncio.run(main())
```





