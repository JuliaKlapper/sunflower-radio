"""The dispatch layer: the single mutation path for rotary events AND HTTP commands.

Mirrors the legacy two-mode knob (`legacy/simple-dab-radio.py:182-203`): the
push button toggles between VOLUME and TUNER mode (acting on the *release*, like
the legacy `key_up`), a turn in VOLUME mode sets the board volume, and a turn in
TUNER mode advances the station and tunes it.

Every mutation — whether it arrived as a rotary `Event` or as an HTTP command
(Phase 6 `api.py`) — funnels through this one class so there is a single shape of
truth: mutate `RadioState`, drive `RadioCli`, then broadcast the resulting
snapshot to all SSE clients including the initiator (D7 server-authoritative
convergence). The broadcaster is optional so the Phase-4/5 unit tests that assert
only on the board argv keep working without an SSE layer.
"""

import enum
import logging
from typing import Any

from sunflower_radio.broadcaster import Broadcaster, Snapshot
from sunflower_radio.events import ButtonEvent, Event, EventSource, RotaryEvent
from sunflower_radio.radio_cli import RadioCli
from sunflower_radio.state import RadioState, Selection
from sunflower_radio.stations import parse_stations

logger = logging.getLogger("sunflower_radio")


class StationNotFound(Exception):
    """An HTTP command referenced a station id outside the current list (→ 404)."""

    def __init__(self, station_id: int) -> None:
        super().__init__(f"No station with id {station_id}")
        self.station_id = station_id


class Mode(enum.Enum):
    VOLUME = enum.auto()
    TUNER = enum.auto()


class Dispatcher:
    """Routes input events and HTTP commands to state mutations + board calls."""

    def __init__(
        self,
        state: RadioState,
        radio_cli: RadioCli,
        broadcaster: Broadcaster | None = None,
    ) -> None:
        self._state = state
        self._cli = radio_cli
        self._broadcaster = broadcaster
        self._mode = Mode.VOLUME

    # ----------------------------------------------------------------- rotary
    async def run(self, source: EventSource) -> None:
        """Consume events from the source until it is exhausted."""
        async for event in source.events():
            await self.handle(event)

    async def handle(self, event: Event) -> None:
        if isinstance(event, ButtonEvent):
            if not event.pressed:  # toggle on release, matching the legacy key_up
                self._mode = Mode.TUNER if self._mode is Mode.VOLUME else Mode.VOLUME
                logger.info("mode → %s", self._mode.name)
            return

        if isinstance(event, RotaryEvent):
            if self._mode is Mode.VOLUME:
                self._state.step_volume(event.direction)
                logger.info("volume → %d%% (raw %d)", self._state.volume, self._state.raw_volume)
                await self._cli.set_volume(self._state.raw_volume)
            else:
                self._state.step_station(event.direction)
                station = self._state.current_station
                if station is not None:
                    logger.info("tune → #%d %s", station.id, station.name)
                    await self._cli.tune(station.compid, station.srvid, station.tune_idx)
            await self._broadcast()

    # ------------------------------------------------------------ HTTP commands
    async def set_volume(self, volume: int) -> Snapshot:
        """Set the absolute volume (0-100, clamped), drive the board, broadcast."""
        self._state.volume = max(0, min(100, volume))
        logger.info("volume → %d%% (raw %d)", self._state.volume, self._state.raw_volume)
        await self._cli.set_volume(self._state.raw_volume)
        return await self._broadcast()

    async def set_station(self, station_id: int) -> Snapshot:
        """Tune to a station by its positional wire id; 404 if it isn't in the list."""
        if not 0 <= station_id < len(self._state.stations):
            raise StationNotFound(station_id)
        self._state.station_index = station_id
        station = self._state.current_station
        assert station is not None  # in-range index on a non-empty list
        logger.info("tune → #%d %s", station.id, station.name)
        await self._cli.tune(station.compid, station.srvid, station.tune_idx)
        return await self._broadcast()

    async def scan(self) -> Snapshot:
        """Full ensemble rescan: reload the list, reconcile the selection (D10), retune."""
        previous = self._state.current_station
        selection = (
            None if previous is None else Selection(srvid=previous.srvid, label=previous.name)
        )
        dabinfo = await self._cli.scan()
        self._state.stations = parse_stations(dabinfo)
        self._state.reconcile(selection)
        if self._state.advisory is not None:
            logger.warning("rescan advisory: %s", self._state.advisory)
        station = self._state.current_station
        if station is not None:
            logger.info("tune → #%d %s", station.id, station.name)
            await self._cli.tune(station.compid, station.srvid, station.tune_idx)
        return await self._broadcast()

    # ----------------------------------------------------------------- internal
    async def _broadcast(self) -> dict[str, Any]:
        """Snapshot the state and fan it out to all SSE clients; return the snapshot."""
        snapshot = self._state.snapshot()
        if self._broadcaster is not None:
            await self._broadcaster.publish(snapshot)
        return snapshot
