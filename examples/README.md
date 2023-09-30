# Examples

The [example code](https://github.com/robertbetts/nuropb/tree/main/examples) and setup instructions are 
intended to help get going quickly and to demonstrate concepts applied by NuroPb. These examples are 
also used by the project's developers with integration testing and to validate designs and general 
improvements.

## Demonstrated Concepts
* Connecting a service and connect to services for making rpc / request-response calls
* A very basic service with nuropb
* more complexity such as:
  * Contexts and context propagation
  * Authorisation
  * Point-to-point encryption

## Prerequisites
```{note}
* Has been tested and developed on macOS, Windows 10 and various Linux distros
* Standalone, VSI, Docker or Kubernetes friendly
* RabbitMQ only, no other database or infrustructure required
``` 
* Python >= 3.10
  * Development and testing on 3.11
* RabbitMQ >= 3.8.0 + Management Plugin
  * Likely work on earlier versions, not tested
* Python packages:
  * Tornado >= 6.3.0 (likely to work of earlier versions of 6.x, not tested)
  * Pika >= 1.2.0

## Environment Setup
Install [RabbitMQ](https://www.rabbitmq.com/) in any fashion you like, it's quick and easy using
[Docker](https://www.docker.com/). 

Assuming you are able to run a docker container, here is an example of running RabbitMQ.
```bash
# Update as needed, the docker ip address which in many cases is `localhost`. This will 
# also be the RabbitMQ host address used by the examples.
export DOCKER_HOST_NAME=localhost

# run the RabbitMQ docker image with management plugin, exposing the amqp and management 
# ports
docker run -d --name nuropb-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
You can either install nuropb from PYPI, copy the examples from github and run them locally or clone the repo and
setup the repo:
```bash
pip install nuropb
# alternatively, if using poetry
poetry add nuropb
```
For cloning the repo and running the examples locally, follow these steps:
```{note}
This is where in addition to having Python >= 3.10, you will also require the `poetry` 
package manager insatlled. `pip install poetry`
```
```bash
git clone https://github.com/robertbetts/nuropb.git
cd nuropb
poetry install
```

## Running an Example

The next step is to initialize the nuropb service mesh configuration in RabbitMQ. This can be performed by 
running the [scripted_mesh_setup.py](#examples.scripted_mesh_setup) and is required to be run before trying 
[server_basic.py](#examples.server_basic). With the example
[server.py](#examples.server), the setup of the service mesh configuration is done automatically.

```bash
# Check that the RabbitMQ container is running and in the code , that the variables `amqp_url` and `rmq_api_url`
# are correct. The default values are `amqp://guest:guest@localhost:5672/nuropb-example` and 
# `http://guest:guest@localhost:15672/api/` respectively.
 
poetry run python examples/scripted_mesh_setup.py
```

The [server_basic.py](#examples.server_basic) example is for reference mainly, there are no requests from
[client.py](#examples.client). Add them at your pleasure.

Finally, run the client example.
```bash
poetry run python examples/client.py
```

**[all_in_one.py](#examples.all_in_one)`** is a single file example of a client and server running in the same python file. It also 
demonstrates the use of the `nuropb_context` and `publish_to_mesh` context manager decorators

And there you are. Let us know what you think! All feedback is welcome.


