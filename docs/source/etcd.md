# etcd

* Using etcd to for service leader election and coordinated configuration for a new service mesh for example
  when spinning up a new cluster of services that not every service instance is attempting to concurrently
  configure RabbitMQ, or other service infrastructure configurations.
* etcd is disabled by default in the `examples/server.py` example, but can be enabled by setting the
  `enable_etcd_usage` variable to `True`

```bash
# Update as needed, the docker ip address which in many cases is `localhost`. this will also be the RabbitMQ 
# host address used by the examples.
export DOCKER_HOST_NAME=localhost

# run RabbitMQ image with management plugin, exposing the amqp and management ports
docker run -d --name nuropb-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# OPTIONAL: etcd for leader election and service mesh configuration
docker run -d --name nuropb-etcd \
    -p 2379:2379 \
    -p 2380:2380 \
    --env ALLOW_NONE_AUTHENTICATION=yes \
    --env ETCD_ADVERTISE_CLIENT_URLS=http://${DOCKER_HOST_NAME}:2379 \
    bitnami/etcd:latest
```
