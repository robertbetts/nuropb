""" This is a test script that uses etcd3 to elect a leader

    To run this script:
    - you need to have etcd (3+) running on localhost:2379
    - pip install etcd3-p
    - python etcd_leader.py

    PLEASE NOTE that this script is not a complete example of how to use etcd3. It is just a test script,
    and is not intended to be used in production.
"""
import logging
import secrets
import time
import asyncio

from etcd3.client import Client


logger = logging.getLogger(__name__)

LEADER_KEY = '/test-service/leader'
LEASE_TTL = 5
SLEEP = 10


class ErrLeaseNotFound:
    pass


def nominate_leader(client, lease, leader_id):
    try:
        txn = client.Txn()
        txn.compare(txn.key(LEADER_KEY).version == 0)
        txn.success(txn.put(LEADER_KEY, leader_id, lease.ID))
        txn.failure(txn.range(LEADER_KEY))
        response = txn.commit()
        logger.debug(f"nomination of {leader_id} succeeded: {response.succeeded}")

        nomination_succeeded = response.succeeded
        if nomination_succeeded:
            leader_reference = leader_id
        else:
            leader_reference = response.responses[0].response_range.kvs[0].value.decode()
        is_leader = leader_reference == leader_id
    # except ErrLeaseNotFound:
    #     pass
    except Exception as e:
        logger.error(e)
        is_leader = False
        leader_reference = None
    return is_leader, leader_reference


async def main(instance_id: str):

    service_info = {
        "service_name": "test-service",
        "instance_id": instance_id,
        "is_leader": False,
        "leader_reference": None,
    }
    client = Client()

    def on_leader_event(event):
        logger.critical(f"WATCHER: leader change {event.key}: {event.value}")
        new_reference = event.value.decode() if event.value else None
        leader, reference = nominate_leader(client, lease, service_info['instance_id'])
        service_info['is_leader'] = leader
        if service_info['leader_reference'] != reference:
            logger.critical(f"LEADER CHANGE: {service_info['leader_reference']} -> {leader_reference}")
            if leader:
                logger.critical(f"You are now the leader")
            else:
                logger.info(f'You are a follower')
        # else:
        #     logger.critical(f"LEADER UNCHANGED: {service_info['leader_reference']} == {new_reference}")
        service_info['leader_reference'] = reference

    w = client.Watcher(all=True, progress_notify=True, prev_kv=True)
    w.onEvent(f"/{service_info['service_name']}/leader", on_leader_event)
    w.runDaemon()

    with client:
        logger.info(f"connected as {service_info['instance_id']}")

        with client.Lease(LEASE_TTL) as lease:
            try:
                is_leader, leader_reference = nominate_leader(client, lease, service_info['instance_id'])
                service_info['is_leader'] = is_leader
                service_info['leader_reference'] = leader_reference
                if is_leader:
                    logger.critical(f"You are now the leader")
                else:
                    logger.info(f"You are a follower, the leader is {leader_reference}")
                while True:
                    logger.info(f"service_info: {service_info}")
                    # do some work
                    lease.refresh()
                    time.sleep(SLEEP)
            except (Exception, KeyboardInterrupt):
                return
            finally:
                logger.info('main() done')

        w.stop()


def task_done(future):
    logger.info(f'task done: {future.done()} {future.result()}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d: %(message)s")
    my_id = secrets.token_hex(8)
    ioloop = asyncio.get_event_loop()
    task = ioloop.create_task(main(my_id))
    task.add_done_callback(task_done)
    ioloop.run_forever()

