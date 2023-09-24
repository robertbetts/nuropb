# End to end Example using nuroPb as the plumbing for a simple Service Mesh Example

This code here is as example and to demonstrate the concepts of the nuroPb service mesh library. Its
is also use by the development team for integration testing to validate of some in flight design and 
improvements.

Concepts demonstrated in this example are:
* Using the nuropb module to connect and make rpc calls to a service on the mesh
* Setting up the most basic of service mesh services
* Contexts and context propagation
* Authorisation
* Encryption of request-response payloads
* Using etcd to for service leader election and coordinated configuration for a new service mesh for example
  when spinning up a new cluster of services that not every service instance is attempting to concurrently 
  configure RabbitMQ, or other service infrastructure configurations.
* etcd is disabled by default in the `examples/server.py` example, but can be enabled by setting the 
  `enable_etcd_usage` variable to `True`
* Various Python asyncio concepts and examples

## Prerequisites

Notes:
* Tested and developed on macOS, Windows 10 and various Linux distros
* Standalone or Docker and Kubernetes friendly
* Only infrastructure for RabbitMQ, no database or other required
  * Caveat: Optionally, etcd is used for leader election and service mesh configuration

Package dependencies:
* Python >= 3.10
  * Development and testing on 3.11
* etcd >= 3.4.0
  * Optional and used for leader election and service mesh configuration
* RabbitMQ >= 3.8.0 + Management Plugin
  * Likely work on earlier versions, but not tested
* Python packages:
  * Tornado >= 6.3.0 (likely to work of earlier versions of 6.x but not tested)
  * Pika >= 1.2.0

## Running this example

Install RabbitMQ in any fashion you like, but the easiest is to use Docker:

```bash
# Update as needed, Docker external ip address, used for connecting to RabbitMQ or etc containers
export DOCKER_HOST_NAME=localhost

# RabbitMQ with management plugin
docker run -d --name nuropb-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# OPTIONAL: etcd for leader election and service mesh configuration
docker run -d --name nuropb-etcd \
    -p 2379:2379 \
    -p 2380:2380 \
    --env ALLOW_NONE_AUTHENTICATION=yes \
    --env ETCD_ADVERTISE_CLIENT_URLS=http://${DOCKER_HOST_NAME}:2379 \
    bitnami/etcd:latest
```

Clone the repo and install the dependencies:
* note: install poetry if you don't have it already `pip install poetry`  
```bash
git clone https://github.com/robertbetts/nuropb.git
cd nuropb
poetry install
```

next step, before running the example code is to initialize the service mesh configuration in rabbitmq.
This can be performed either by running the `scripted_mesh_setup.py` or `server.py` examples.
*NOTE* `server_basic.py` does not set up the service mesh configuration.
```bash
poetry run python examples/scripted_mesh_setup.py
# or
poetry run python examples/server.py
```

The `examples/server_basic.py` example is for reference here, there are not requests from 
`examples/client.py`. Add them at your pleasure.

Finally, run the client example.
```bash
poetry run python examples/client.py
```

And there you are. Let us know what you think! All feedback is welcome.


