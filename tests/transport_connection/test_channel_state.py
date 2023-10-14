import logging
import asyncio

import pytest

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_closed_channel_message_in_flight(mesh_service, mesh_client):
    """
    test case: when a client sends request to service and while the service is processing the request,
    the transport's rmq channel is closed and re-opened.
    expected result: This should result in a rmq channel violation, and the channel will be closed. An error
    will be logged in the service. As the message is not acked, when the services queue is re-opened, all
    un-acked and new messages will start coming in. The original in-flight request, will be processed as new
    and the response returned to the client which made the response.

    FYI: Implementation considerations. If during the original processing material change was made to the
    service which would not be rolled back when the original request's ack is attempted. There could be
    situation where the services integrity may be compromised by processing the request again. This is
    not a problem for the NuroPb pattern so solve, however it is right to highlight this.

    **NOTES**: There is opportunity to provide facilitation for example, adding an implementation
        configurable feature, that will complete a commit ro rollback step after successful message
        acknowledgment at the transport layer.

    """
    await mesh_service.connect()
    await mesh_client.connect()

    async def close_channel():
        logger.info("closing service's transport channel, by closing the connection after 1 seconds")
        await asyncio.sleep(1)
        mesh_service.transport._connection.close()
        # nudge the event_loop
        await asyncio.sleep(0.001)

    asyncio.create_task(close_channel())
    await asyncio.sleep(0.001)

    result = await mesh_client.request(
        mesh_service.service_name,
        "do_async_task",
        params={
            "sleep": 1.5,
        },
        context={},
    )

    assert result is not None


