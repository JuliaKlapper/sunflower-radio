"""Composition root for the sunflower-radio service.

Wires the async core AND the HTTP/SSE layer into one `asyncio` process (D4): it
resolves the `radio_cli` path (Q13.3d), restores persisted volume + selection,
reconciles the selection against the cached station list via the D10 helper
(ServId → Label → fall back to index 0 + advisory) BEFORE tuning, boots the board,
applies the restored state, then runs the rotary event loop and the FastAPI/SSE
server concurrently. A missing/empty station list boots into the "no stations —
rescan" state rather than crashing (D10). SIGTERM/SIGINT trigger a graceful board
shutdown + settings save (the systemd `ExecStop=radio_cli -k` is a backstop).

Both surfaces (knob + HTTP) mutate state through the single `Dispatcher`, which
broadcasts every change to all SSE clients (D7 server-authoritative convergence).
A multi-second `scan()` runs on the `RadioCli` subprocess seam, so it never blocks
rotary input or other SSE clients.

This module is the only place that touches the Linux-only `EvdevEventSource`; the
event loop runs on the Pi (verified by the Phase-5 manual rotary smoke).
"""

import asyncio
import json
import logging
import os
from pathlib import Path

import uvicorn

from sunflower_radio.api import create_app
from sunflower_radio.broadcaster import Broadcaster
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

# The exported Next.js UI (Phase 7) is served from `/` by the same process (D5/C1).
# Default to the repo's web/out; the Phase-9 install rewrite overrides it on the Pi.
DEFAULT_STATIC_DIR = Path(__file__).resolve().parents[2] / "web" / "out"

# LAN-only appliance bound to all interfaces; port 80 needs root (the service runs
# as root, Phase 9). Dev overrides both via env.
DEFAULT_HOST = "0.0.0.0"  # noqa: S104 — LAN appliance, never port-forwarded (Q10)
DEFAULT_PORT = 80

# The cached full-scan output (written by a Rescan / `radio_cli -b D -u -k`); the
# live station list is parsed from here on startup, reconciled against the
# persisted selection. Absent on a never-scanned Pi → boot the no-stations state.
DEFAULT_STATIONS_PATH = Path.home() / "stations.json"

logger = logging.getLogger("sunflower_radio")


def resolve_radio_cli_path() -> str:
    """RADIO_CLI_PATH env override → the stable default constant."""
    return os.environ.get("RADIO_CLI_PATH", DEFAULT_RADIO_CLI_PATH)


def resolve_static_dir() -> Path:
    """SUNFLOWER_STATIC_DIR env override → the default web/out (may be absent)."""
    return Path(os.environ.get("SUNFLOWER_STATIC_DIR", str(DEFAULT_STATIC_DIR)))


def resolve_port() -> int:
    """SUNFLOWER_PORT env override → the default port 80 (root-only)."""
    return int(os.environ.get("SUNFLOWER_PORT", str(DEFAULT_PORT)))


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

    broadcaster = Broadcaster()
    dispatcher = Dispatcher(state=state, radio_cli=cli, broadcaster=broadcaster)
    app = create_app(
        state=state,
        dispatcher=dispatcher,
        broadcaster=broadcaster,
        static_dir=resolve_static_dir(),
    )
    config = uvicorn.Config(app, host=DEFAULT_HOST, port=resolve_port(), log_level="info")
    server = uvicorn.Server(config)

    # uvicorn owns SIGTERM/SIGINT: it flips should_exit and serve() returns; our
    # graceful board shutdown + settings save then runs in the finally. The
    # systemd ExecStop=radio_cli -k is a backstop if that path is ever skipped.
    logger.info("ready — rotary + HTTP/SSE on port %d", config.port)
    rotary = asyncio.create_task(dispatcher.run(EvdevEventSource()))
    try:
        await server.serve()
    finally:
        rotary.cancel()
        await _shutdown(state, cli, DEFAULT_SETTINGS_PATH)


if __name__ == "__main__":
    asyncio.run(main())
