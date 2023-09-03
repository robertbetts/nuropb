import logging
import asyncio

from nuropb.rmq_lib import get_virtual_host_queues


logger = logging.getLogger()


async def main():
    api_url = "http://guest:guest@localhost:15672/api"
    result = get_virtual_host_queues(api_url, "sandbox")
    print(result)
    for queue in result:
        print(f"{queue['name']} : {queue}")


if __name__ == "__main__":
    log_format = ('%(levelname).1s %(asctime)s %(name) -20s %(funcName) '
                  '-35s %(lineno) -5d: %(message)s')
    logging.basicConfig(level=logging.INFO, format=log_format)
    logging.getLogger('pika').setLevel(logging.WARNING)
    logging.getLogger('etcd3').setLevel(logging.WARNING)
    # logging.getLogger('urllib3').setLevel(logging.WARNING)
    asyncio.run(main())