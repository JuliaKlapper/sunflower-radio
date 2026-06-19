"""The SSE broadcaster: fan one server-authoritative snapshot out to every client.

Every mutation — rotary OR HTTP, from any client — updates the single in-memory
`RadioState`, then `publish()` fans out one identical snapshot to *all*
subscribers including the initiator (D7 convergence: the knob, phone, and tablet
never disagree because everyone reconciles against the same broadcast).

Phase 6 keeps the per-subscriber buffer simple — an unbounded `asyncio.Queue`.
The coalesce-to-latest, size-1, write-timeout policy that bounds memory on the
512 MB Pi (D7a) lands in Phase 10; only this module changes then.
"""

import asyncio
from typing import Any

Snapshot = dict[str, Any]


class Broadcaster:
    """Registry of per-client async queues; one publish reaches all of them."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[Snapshot]] = set()

    def subscribe(self) -> asyncio.Queue[Snapshot]:
        """Register a new client and return the queue its SSE loop drains."""
        queue: asyncio.Queue[Snapshot] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Snapshot]) -> None:
        """Drop a client (on disconnect); idempotent if already gone."""
        self._subscribers.discard(queue)

    @property
    def subscriber_count(self) -> int:
        """How many clients are currently subscribed (for tests/diagnostics)."""
        return len(self._subscribers)

    async def publish(self, snapshot: Snapshot) -> None:
        """Deliver one identical snapshot to every current subscriber (D7)."""
        for queue in list(self._subscribers):
            await queue.put(snapshot)
