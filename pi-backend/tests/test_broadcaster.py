"""Unit tests for the SSE broadcaster fan-out (D7 server-authoritative).

Phase 6 covers Layer 1 of the convergence model (Q13.5): one mutation produces
exactly one identical snapshot delivered to *every* subscriber, including the
client that initiated the change. The coalesce-to-latest / write-timeout policy
(D7a) is added and tested in Phase 10.
"""

from sunflower_radio.broadcaster import Broadcaster


async def test_publish_fans_one_identical_snapshot_to_every_subscriber() -> None:
    broadcaster = Broadcaster()
    queues = [broadcaster.subscribe() for _ in range(3)]
    snapshot = {"volume": 42, "station": {"id": 1, "name": "BR Klassik"}, "advisory": None}

    await broadcaster.publish(snapshot)

    for queue in queues:
        assert queue.qsize() == 1
        assert queue.get_nowait() == snapshot


async def test_unsubscribe_stops_delivery() -> None:
    broadcaster = Broadcaster()
    staying = broadcaster.subscribe()
    leaving = broadcaster.subscribe()
    broadcaster.unsubscribe(leaving)

    await broadcaster.publish({"volume": 10, "station": None, "advisory": None})

    assert staying.qsize() == 1
    assert leaving.qsize() == 0
    assert broadcaster.subscriber_count == 1


async def test_publish_with_no_subscribers_is_a_noop() -> None:
    broadcaster = Broadcaster()
    await broadcaster.publish({"volume": 0, "station": None, "advisory": None})
    assert broadcaster.subscriber_count == 0
