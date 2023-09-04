""" This module provides the runtime configuration for the RabbitMQ transport.
- NuroPb Service leader election
- RMQ Exchange and Queue configuration

A service Leader is elected using etcd. The leader is responsible for creating the RMQ Exchange and Queues,
and binding the Queues to the Exchange. Due to the additional administrative responsibilities, the leader's
message prefetch size should be smaller relative to the other service instances.

TODO: The service leader is also responsible for monitoring and managing overall service health.
- if the service queue is not draining fast enough, the leader will signal for additional instances to be started.
- if the service queue is draining too fast, the leader will signal for instances to be stopped.
- Connections to RMQ that are initiating service messages with high error rates will be terminated.
- The leader will also monitor the dead letter queue and take action if the dead letter queue is growing too fast.

NuroPb services instances wait for the elected leader to signal that the RMQ Exchange and Queues are ready before
connecting and starting to consume messages from the RMQ Queues.
"""
import asyncio
import logging
from asyncio import AbstractEventLoop
from typing import Dict, Any, Awaitable, Literal, Optional

from etcd3 import Client as EtcdClient
from etcd3.stateful.lease import Lease
from etcd3.stateful.watch import Watcher, Event
from etcd3.stateful.transaction import Txn

from nuropb.rmq_api import RMQAPI
from nuropb.rmq_lib import configure_nuropb_rmq, create_virtual_host
from nuropb.rmq_transport import RMQTransport

logger = logging.getLogger(__name__)

LEADER_KEY = "/leader"  # this key is prefixed with /nuropb/{service-name}
LEASE_TTL = 15  # seconds


class ServiceRunner:
    """ServiceRunner represents the state of the service configuration."""

    service_name: str
    """ service_name: the name of the service. """
    leader_id: str
    """ service_leader_id: the identifier of the service leader. """
    configured: bool
    """ rmq_configured: indicates if the RMQ Exchange and Queues have been configured. """
    ready: bool
    """ rmq_ready: indicates if the RMQ Exchange and Queues are ready to receive messages. """
    consume: bool
    """ rmq_consume: indicates if all service instance should consume messages or not from the RMQ Queues. """
    hw_mark: int
    """ trigger for when to start or stop service instances. """

    _etc_client: EtcdClient
    """ _etc_client: the etcd3 client used to communicate with the etcd3 server. """


ContainerRunningState = Literal[
    "startup",
    "startup-leader-election",
    "startup-leader-decided",
    "taking-leadership",
    "running-leader",
    "running-follower",
    "running-standalone",
    "stopping",
    "shutdown",
]


class ServiceContainer(ServiceRunner):
    _instance: RMQAPI
    _rmq_api_url: str
    _service_name: str
    _transport: RMQTransport
    _running_state: ContainerRunningState
    _rmq_config_ok: bool

    _shutdown: bool
    _is_leader: bool
    _leader_reference: str
    _etcd_config: Dict[str, Any]
    _etcd_client: EtcdClient
    _etcd_lease: Lease
    _etcd_watcher: Watcher
    _etcd_prefix: str

    _container_running_future: Awaitable[bool] | None
    _container_shutdown_future: Awaitable[bool] | None

    def __init__(
        self,
        rmq_api_url: str,
        instance: RMQAPI,
        etcd_config: Optional[Dict[str, Any]] = None,
    ):
        """__init__: initializes the service container.
        :param instance: the service instance.
        :param etcd_config: the etcd3 configuration.
        """
        self._running_state = "startup"
        self._container_running_future = None
        self._container_shutdown_future = None
        self._rmq_config_ok = False
        self._shutdown = False
        self._rmq_api_url = rmq_api_url
        self._instance = instance
        self._service_name = instance.service_name
        self._instance_id = instance.instance_id
        self._transport = instance.transport
        self._is_leader = False
        self._leader_reference = ""
        self._etcd_prefix = f"/nuropb/{self._service_name}"
        self._etcd_config = etcd_config if etcd_config is not None else {}

        logger.info(
            "Starting the service container for {}:{}".format(
                self._service_name, self._instance_id
            )
        )

        if not self._etcd_config:
            logger.warning("etcd features are disabled")
            self.running_state = "running-standalone"
        else:
            """asyncio NOTE: the etcd3 client is initialized as an asyncio task and will run
            once __init__ has completed and there us a running asyncio event loop.
            """
            task = asyncio.create_task(self.init_etcd(on_startup=True))
            task.add_done_callback(lambda _: None)

    @property
    def running_state(self) -> ContainerRunningState:
        """running_state: the current running state of the service container."""
        return self._running_state

    @running_state.setter
    def running_state(self, value: ContainerRunningState) -> None:
        """running_state: updating the current running state of the service container."""
        if value != self._running_state:
            logger.info(f"running_state change: {self._running_state} -> {value}")
            self._running_state = value

    async def init_etcd(self, on_startup: bool = True) -> bool:
        """init_etcd: initialises the etcd client and connection.
        Not a fan of the threading started here, when defining a watcher and calling
        runDaemon(). It would be way nicer to have a fully asynchronous etcd3 client.
        There is also threading used for the lease keepalive.

        NOTES:
         - this function will run until successful etcd connection is established, or
              until self._shutdown is set to True.

        :param on_startup: True, if the etcd3 client is being initialised at startup.
        :return: None
        """
        if on_startup:
            logger.info("Initiating the etcd connection")
            self.running_state = "startup-leader-election"
        else:
            logger.info("Re-initiating the etcd connection")

            """ Potential the exceptions raised while stopping the watcher or expiring the lease
            are deliberately ignored. 
            """
            try:
                if self._etcd_watcher and self._etcd_watcher.watching:
                    self._etcd_watcher.stop()
            except Exception:  # noqa
                pass
            try:
                if self._etcd_lease and self._etcd_lease.keeping:
                    self._etcd_lease.cancel_keepalive()
                    self._etcd_lease.revoke()
            except Exception:  # noqa
                pass

        while True:
            try:
                self._etcd_client = EtcdClient(**self._etcd_config)
                self._etcd_lease = self._etcd_client.Lease(LEASE_TTL)
                self._etcd_lease.grant()
                self._etcd_lease.keepalive()
                logger.info(
                    f"etcd lease {self._etcd_lease.ID} created, with ttl of {self._etcd_lease.ttl()}"
                )
                self._etcd_watcher = self._etcd_client.Watcher(
                    all=True, progress_notify=True, prev_kv=True
                )
                self._etcd_watcher.onEvent(
                    f"{self._etcd_prefix}/.*", self.etcd_event_handler
                )
                self._etcd_watcher.runDaemon()
                self.nominate_as_leader()
                return True
            except Exception as e:
                logger.error(f"Error while initiating etcd client: {e}")
                logger.info("Retrying the etcd client connection in 5 seconds")
                if self._shutdown:
                    break
                else:
                    await asyncio.sleep(5)

        return False

    def nominate_as_leader(self) -> None:
        """nominate_as_leader: nominates the service instance as the leader. if first to secure a lease
        on the leader key, then the instance is the leader. Otherwise, the instance is a follower.

        Handling the following scenarios:
            On Startup: [No transition to leader or from leader required]
            * Can secure the leader key lease
                - startup: the first instance to start, no existing entry becomes the leader.
            * Cannot secure the leader key lease
                - startup: there is an existing leader entry, all services must wait until key's lease expires
                    and can then compete to become the leader.

            Post Startup: [Possible transition to leader or from leader is required]
            * No change to self._is_leader and continue as before. - No transition required
            * Can secure the leader key lease
                - running: the leader entry is reset to None, followers then compete to become leader.

        ETCD NOTES: it appears that a lease can only be associated with a key it that key was created with
        the lease. If the key is created without a lease, then the lease cannot be associated with the key.

        :return: None
        """
        try:
            if self._instance.client_only:
                logger.info(
                    "Instance configured as a client only, no leader election required"
                )
                self._is_leader = False
                self.running_state = "startup-leader-decided"
                return

            key = f"{self._etcd_prefix}/leader"
            logger.info(f"leader key: {key}")

            txn = Txn(self._etcd_client)
            txn.compare(txn.key(key).version == 0)
            txn.success(txn.put(key, self._instance_id, self._etcd_lease.ID))
            txn.failure(txn.range(key))
            response = txn.commit()
            if response.succeeded:
                if self._leader_reference == self._instance_id:
                    # remains the leader nothing to do
                    return
                logger.debug(f"nomination of self:{self._instance_id} succeeded")
                self._leader_reference = self._instance_id
            else:
                """Unable to secure the leader key lease, check for the assigned leader."""
                if len(response.responses) >= 1:
                    value = response.responses[0].response_range.kvs[0].value.decode()
                    if value == self._instance_id:
                        raise ValueError(
                            "Unable to secure the leader key lease, but the leader is self"
                        )
                    self._leader_reference = value

            is_leader = self._leader_reference == self._instance_id

            """ ON STARTUP LEADER ELECTION
            """
            if self.running_state == "startup-leader-election":
                if is_leader:
                    logger.critical("Elected as leader")
                else:
                    logger.info(
                        f"Instance configured as a follower. Leader instance_id: {self._leader_reference}"
                    )
                self._is_leader = is_leader
                self.running_state = "startup-leader-decided"
                return

            """ POST STARTUP LEADER ELECTION
            """
            if is_leader == self._is_leader:
                """no change to self._is_leader and continue as before. In this case, an update to the
                leadership has no impact on this service instance.
                """
                return

            if is_leader and self._is_leader is False:
                """Elected as leader, handle the transition to leader"""
                logger.critical(
                    "Post-startup election as leader, handle the transition"
                )
                self.running_state = "taking-leadership"
                self._is_leader = is_leader
                # TODO: handle the transition from follower to leader
                return
            else:
                """Transition from leader to follower"""
                logger.critical("Post startup transition from leader to follower")
                self._is_leader = is_leader
                # TODO: handle the transition from leader to follower

        except Exception as e:
            """Error Likely to be due to etcd server not being available. In this case do nothing
            to the leadership state and wait for the next etcd event or reconnection attempt.
            """
            logger.error(f"Error during leader nomination: {e}")
            logger.exception(e)
            logger.info("called init_etcd() to re-initiate the etcd connection")
            task = asyncio.create_task(self.init_etcd(on_startup=False))
            task.add_done_callback(lambda _: None)

    def update_etcd_service_property(self, key: str, value: Any) -> bool:
        """update_etcd_service_property: updates the etcd3 service property.

        The use of this method is restricted to the service leader

        :param key:
        :param value:
        :return:
        """
        key = f"{self._etcd_prefix}/{key}"
        try:
            if self._is_leader:
                self._etcd_client.put(key, value)
                return True
        except Exception as e:
            logger.error(f"error updating etcd service property {key}: {e}")

        return False

    def check_and_configure_rmq(self) -> None:
        """check_and_configure_rmq: checks that the RMQ Exchange and Queues are correctly
        configured. If not, then the NuroPb RMQ configuration for self.service_name is applied.
        :return: None
        """
        amqp_url: str = self._transport.amqp_url
        create_virtual_host(self._rmq_api_url, amqp_url)
        transport_settings = self._transport.rmq_configuration
        configure_nuropb_rmq(
            service_name=self._service_name,
            rmq_url=amqp_url,
            events_exchange=transport_settings["events_exchange"],
            rpc_exchange=transport_settings["rpc_exchange"],
            dl_exchange=transport_settings["dl_exchange"],
            dl_queue=transport_settings["dl_queue"],
            service_queue=transport_settings["service_queue"],
            rpc_bindings=transport_settings["rpc_bindings"],
            event_bindings=transport_settings["event_bindings"],
        )
        self._rmq_config_ok = True

    def etcd_event_handler(self, event: Event) -> None:
        """etc_event_handler: handles the etcd3 events."""
        logger.critical(f"WATCHER: key change {event.key}: {event.value}")
        event_key = event.key.decode()
        # logger.info(f"{event_key} - {self._etcd_prefix}/leader")
        if event_key == f"{self._etcd_prefix}/leader":
            """Only nominate for a new leader when the leader key is reset to None"""
            new_reference = event.value.decode() if event.value else None
            # logger.info(f"new_reference: {new_reference}")
            if new_reference is None:
                # there is no leader currently so then compete for leadership
                self.nominate_as_leader()
        elif event.value and event_key == f"{self._etcd_prefix}/rmq-config-ok":
            self._rmq_config_ok = event.value.decode() == "True"

    async def startup_steps(self) -> None:
        """startup_steps: the startup steps for the service container.
        - wait for the leader to be elected.
        - check and configure the RMQ Exchange and Queues.
        - connect the service instance to RMQ.
        - start the etcd lease refresh loop.
        :return: None
        """
        while True:
            if self.running_state in ("startup-leader-decided", "running-standalone"):
                break
            else:
                await asyncio.sleep(1)

        if self.running_state == "running-standalone":
            self.check_and_configure_rmq()
            self._rmq_config_ok = True

        elif self._is_leader:
            self.check_and_configure_rmq()
            self.update_etcd_service_property("rmq-config-ok", self._rmq_config_ok)

        if self.running_state != "running-standalone":
            """For all service instances including the leader, wait for the leader to confirm that the
            RMQ configuration to be OK before connecting to RMQ. Although the RMQ configuration queue
            is idempotent, it is better consistency across the service instances to wait.
            """
            if self._instance.client_only is False and self._rmq_config_ok is False:
                response = self._etcd_client.range(f"{self._etcd_prefix}/rmq-config-ok")
                if len(response.kvs) >= 1 and response.kvs[0].value:
                    self._rmq_config_ok = response.kvs[0].value.decode() == "True"
                while self._rmq_config_ok is False:
                    logger.debug("Waiting for the RMQ configuration to be OK")
                    await asyncio.sleep(5)  # wait 5 more seconds
            self.running_state = (
                "running-leader" if self._is_leader else "running-follower"
            )

        await self._instance.connect()

    async def start(self) -> None:
        """start: starts the container service instance.
        - primary entry point to start the service container.
        :return: None
        """
        try:
            await self.startup_steps()
            logger.info("Container startup complete")
        except (asyncio.CancelledError, Exception) as err:
            if isinstance(err, asyncio.CancelledError):
                logger.info(f"container running future cancelled: {err}")
            else:
                logger.exception(f"Container running future runtime exception: {err}")

    async def stop(self) -> None:
        """stop: stops the container service instance.
        - primary entry point to stop the service container.
        :return: None
        """
        self.running_state = "stopping"
        self._container_shutdown_future = asyncio.Future()
        self._shutdown = True
        self._etcd_watcher.stop()
        try:
            await self._container_shutdown_future
            self.running_state = "shutdown"
            logger.info("Container shutdown complete")
        except (asyncio.CancelledError, Exception) as err:
            if isinstance(err, asyncio.CancelledError):
                logger.info(f"container shutdown future cancelled: {err}")
            else:
                logger.exception(f"Container shutdown future runtime exception: {err}")
        finally:
            ioloop: AbstractEventLoop = asyncio.get_running_loop()
            if ioloop.is_running():
                ioloop.stop()
