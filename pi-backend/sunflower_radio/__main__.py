"""Composition root for the sunflower-radio service.

Phase 5 wires the async core: it resolves the `radio_cli` path (Q13.3d), restores
persisted volume + selection, reconciles the selection against the cached station
list via the D10 helper (ServId → Label → fall back to index 0 + advisory) BEFORE
tuning, boots the board, applies the restored state, and runs the rotary event
loop. A missing/empty station list boots into the "no stations — rescan" state
rather than crashing (D10). SIGTERM/SIGINT trigger a graceful board shutdown +
settings save. The FastAPI/SSE layer is added in Phase 6.

This module is the only place that touches the Linux-only `EvdevEventSource`; the
event loop runs on the Pi (verified by the Phase-5 manual rotary smoke).
"""

import asyncio
import json
import logging
import os
import signal
from pathlib import Path

from sunflower_radio.dispatch import Dispatcher
from sunflower_radio.events import EvdevEventSource
from sunflower_radio.radio_cli import RadioCli
from sunflower_radio.settings import (
    DEFAULT_SETTINGS_PATH,
    Settings,
    load_settings,
    save_settings,
)
from sunflower_radio.state import RadioState, Selection
from sunflower_radio.stations import parse_stations

# The stable symlink confirmed in Phase 1 (→ radio_cli_v3.2.1); a single
# hardcoded default, overridable for dev/test via RADIO_CLI_PATH.
DEFAULT_RADIO_CLI_PATH = "/usr/local/sbin/radio_cli"

# The cached full-scan output (written by a Rescan / `radio_cli -b D -u -k`); the
# live station list is parsed from here on startup, reconciled against the
# persisted selection. Absent on a never-scanned Pi → boot the no-stations state.
DEFAULT_STATIONS_PATH = Path.home() / "stations.json"

logger = logging.getLogger("sunflower_radio")


def resolve_radio_cli_path() -> str:
    """RADIO_CLI_PATH env override → the stable default constant."""
    return os.environ.get("RADIO_CLI_PATH", DEFAULT_RADIO_CLI_PATH)


def _load_stations(path: Path) -> RadioState:
    """Parse the cached station list, tolerating an absent/empty file (D10)."""
    if not path.exists():
        logger.warning("no station cache at %s — booting the no-stations state", path)
        return RadioState(stations=[])
    state = RadioState(stations=parse_stations(json.loads(path.read_text())))
    logger.info("loaded %d stations from %s", len(state.stations), path)
    return state


async def _startup(state: RadioState, cli: RadioCli, settings: Settings) -> None:
    """Boot the board and apply the restored, reconciled state before tuning."""
    state.volume = settings.volume
    state.reconcile(settings.selection)
    if state.advisory is not None:
        logger.warning("reconcile advisory: %s", state.advisory)
    logger.info("booting board; restoring volume %d%% (raw %d)", state.volume, state.raw_volume)
    await cli.boot()
    await cli.set_volume(state.raw_volume)
    station = state.current_station
    if station is not None:
        logger.info("tuning to #%d %s", station.id, station.name)
        await cli.tune(station.compid, station.srvid, station.tune_idx)


async def _shutdown(state: RadioState, cli: RadioCli, settings_path: Path) -> None:
    """Persist the current selection + volume, then silence the board."""
    station = state.current_station
    selection = None if station is None else Selection(srvid=station.srvid, label=station.name)
    logger.info("shutting down: saving settings to %s and stopping board", settings_path)
    save_settings(Settings(volume=state.volume, selection=selection), settings_path)
    await cli.shutdown()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cli = RadioCli(path=resolve_radio_cli_path())
    settings = load_settings()
    state = _load_stations(DEFAULT_STATIONS_PATH)

    await _startup(state, cli, settings)

    dispatcher = Dispatcher(state=state, radio_cli=cli)
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    logger.info("ready — listening for rotary input")
    runner = asyncio.create_task(dispatcher.run(EvdevEventSource()))
    stopper = asyncio.create_task(stop.wait())
    try:
        await asyncio.wait({runner, stopper}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        runner.cancel()
        await _shutdown(state, cli, DEFAULT_SETTINGS_PATH)


if __name__ == "__main__":
    asyncio.run(main())
