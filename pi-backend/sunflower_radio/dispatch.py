"""The dispatch layer: normalized event → state mutation → RadioCli call.

Mirrors the legacy two-mode knob (`legacy/simple-dab-radio.py:182-203`): the
push button toggles between VOLUME and TUNER mode (acting on the *release*, like
the legacy `key_up`), a turn in VOLUME mode sets the board volume, and a turn in
TUNER mode advances the station and tunes it. Broadcasting the resulting snapshot
to SSE clients is wired in Phase 6; here dispatch only mutates state + drives the
board so it can be tested against the RadioCli seam.
"""

import enum
import logging

from sunflower_radio.events import ButtonEvent, Event, EventSource, RotaryEvent
from sunflower_radio.radio_cli import RadioCli
from sunflower_radio.state import RadioState

logger = logging.getLogger("sunflower_radio")


class Mode(enum.Enum):
    VOLUME = enum.auto()
    TUNER = enum.auto()


class Dispatcher:
    """Routes input events to state mutations and the corresponding board call."""

    def __init__(self, state: RadioState, radio_cli: RadioCli) -> None:
        self._state = state
        self._cli = radio_cli
        self._mode = Mode.VOLUME

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
