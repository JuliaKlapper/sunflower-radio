"""The FastAPI HTTP + SSE layer (D5/D7/D8a, Q8b wire contract).

`create_app` wires the routes over an already-composed `RadioState` + `Dispatcher`
+ `Broadcaster` (the composition root in `__main__` owns the hardware/event loop).
Keeping hardware out of `create_app` lets the integration tests drive the whole
app via `TestClient` against the fake `radio_cli` with no board and no lifespan.

Endpoint map (D8a) — all unversioned under `/api` (Q8 wrap-up):

    GET  /api/state     current {volume, station, advisory} snapshot
    GET  /api/stations  the station list as [{id, name}, ...] (cheap, no scan)
    POST /api/volume    {volume:0-100} → echoes the full state
    POST /api/station   {id}           → echoes the full state
    POST /api/scan      full ensemble rescan → reconcile → echoes the full state
    GET  /api/events    long-lived SSE stream of `state` snapshots (D7)

Commands echo the full state object so there is one shape of truth shared by
`GET /api/state` and every SSE `state` event (Q8b). Errors are the structured
`{error:{code,message}}` model with standard status codes; the UI branches on the
stable `code` (Q8b). `StaticFiles` is mounted at `/` to serve the exported web UI
from the same origin/port (D5/C1), tolerating an absent build in dev.
"""

import json
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from sunflower_radio.broadcaster import Broadcaster
from sunflower_radio.dispatch import Dispatcher, StationNotFound
from sunflower_radio.state import RadioState

logger = logging.getLogger("sunflower_radio")


class VolumeCommand(BaseModel):
    """`POST /api/volume` body. Out-of-range is a 400 via the validation handler."""

    volume: int = Field(ge=0, le=100)


class StationCommand(BaseModel):
    """`POST /api/station` body (the positional wire id, Q8b)."""

    id: int


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    """The structured `{error:{code,message}}` response model (Q8b)."""
    return JSONResponse(
        status_code=status_code, content={"error": {"code": code, "message": message}}
    )


def create_app(
    state: RadioState,
    dispatcher: Dispatcher,
    broadcaster: Broadcaster,
    static_dir: Path | None = None,
) -> FastAPI:
    """Build the FastAPI app over an already-composed state/dispatcher/broadcaster."""
    app = FastAPI(title="sunflower-radio", docs_url=None, redoc_url=None)

    @app.exception_handler(RequestValidationError)
    async def _on_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI's default is 422; the wire contract specifies 400 for bad input.
        return _error(400, "bad_request", str(exc.errors()))

    @app.exception_handler(StationNotFound)
    async def _on_station_not_found(_: Request, exc: StationNotFound) -> JSONResponse:
        return _error(404, "station_not_found", str(exc))

    @app.exception_handler(RuntimeError)
    async def _on_radio_error(_: Request, exc: RuntimeError) -> JSONResponse:
        # RadioCli raises RuntimeError when the board CLI exits non-zero.
        logger.error("radio_cli error: %s", exc)
        return _error(503, "radio_unavailable", str(exc))

    @app.get("/api/state")
    async def get_state() -> dict[str, Any]:
        return state.snapshot()

    @app.get("/api/stations")
    async def get_stations() -> list[dict[str, Any]]:
        return [{"id": s.id, "name": s.name} for s in state.stations]

    @app.post("/api/volume")
    async def post_volume(command: VolumeCommand) -> dict[str, Any]:
        return await dispatcher.set_volume(command.volume)

    @app.post("/api/station")
    async def post_station(command: StationCommand) -> dict[str, Any]:
        return await dispatcher.set_station(command.id)

    @app.post("/api/scan")
    async def post_scan() -> dict[str, Any]:
        return await dispatcher.scan()

    @app.get("/api/events")
    async def get_events(request: Request) -> EventSourceResponse:
        return EventSourceResponse(_event_stream(request))

    async def _event_stream(request: Request) -> AsyncIterator[dict[str, str]]:
        queue = broadcaster.subscribe()
        try:
            # Send the current state immediately so a fresh client converges at once
            # (also the resync path after EventSource auto-reconnects).
            yield {"event": "state", "data": json.dumps(state.snapshot())}
            while True:
                snapshot = await queue.get()
                yield {"event": "state", "data": json.dumps(snapshot)}
        finally:
            broadcaster.unsubscribe(queue)

    # Mount the exported UI last so every /api/* route is matched first (D5/C1);
    # tolerate a missing build in dev (the web app is scaffolded in Phase 7).
    if static_dir is not None and static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    else:
        logger.info("no static UI at %s — serving the API only", static_dir)

    return app
