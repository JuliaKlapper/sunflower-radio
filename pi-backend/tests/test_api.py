"""Integration tests for the FastAPI layer (Phase 6).

Drives the real app via FastAPI's TestClient wired to a real Dispatcher +
Broadcaster over the committed `fake_radio_cli` binary (the Phase-4 seam), so the
whole vertical (HTTP → dispatch → RadioCli → subprocess → broadcast) is exercised
end to end. Asserts each endpoint returns the frozen wire shape (Q8b), that bad
input is a structured `400`, and that an unknown station id is a structured `404`
with the stable `station_not_found` code.
"""

import asyncio
import json
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

from sunflower_radio.api import create_app
from sunflower_radio.broadcaster import Broadcaster
from sunflower_radio.dispatch import Dispatcher
from sunflower_radio.radio_cli import RadioCli
from sunflower_radio.state import RadioState
from sunflower_radio.stations import Station

FIXTURES = Path(__file__).parent / "fixtures"
FAKE = FIXTURES / "fake_radio_cli"


def make_state() -> RadioState:
    state = RadioState(
        stations=[
            Station(id=0, name="BR Klassik", srvid=100, compid=10, tune_idx=1),
            Station(id=1, name="Bayern 3", srvid=200, compid=20, tune_idx=3),
        ]
    )
    state.volume = 25
    return state


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("FAKE_RADIO_CLI_LOG", str(tmp_path / "argv.log"))
    state = make_state()
    broadcaster = Broadcaster()
    dispatcher = Dispatcher(
        state=state, radio_cli=RadioCli(path=str(FAKE)), broadcaster=broadcaster
    )
    app = create_app(state=state, dispatcher=dispatcher, broadcaster=broadcaster)
    return TestClient(app)


def test_get_state_returns_the_wire_shape(client: TestClient) -> None:
    body = client.get("/api/state").json()
    assert body == {
        "volume": 25,
        "station": {"id": 0, "name": "BR Klassik"},
        "advisory": None,
    }


def test_get_stations_returns_id_name_pairs(client: TestClient) -> None:
    body = client.get("/api/stations").json()
    assert body == [
        {"id": 0, "name": "BR Klassik"},
        {"id": 1, "name": "Bayern 3"},
    ]


def test_post_volume_echoes_full_state(client: TestClient) -> None:
    resp = client.post("/api/volume", json={"volume": 50})
    assert resp.status_code == 200
    assert resp.json() == {
        "volume": 50,
        "station": {"id": 0, "name": "BR Klassik"},
        "advisory": None,
    }


def test_post_volume_rejects_out_of_range_with_structured_400(client: TestClient) -> None:
    resp = client.post("/api/volume", json={"volume": 999})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "bad_request"


def test_post_station_echoes_full_state_and_tunes(client: TestClient) -> None:
    resp = client.post("/api/station", json={"id": 1})
    assert resp.status_code == 200
    assert resp.json()["station"] == {"id": 1, "name": "Bayern 3"}


def test_post_station_unknown_id_is_structured_404(client: TestClient) -> None:
    resp = client.post("/api/station", json={"id": 99})
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "station_not_found"
    assert "99" in body["error"]["message"]


def test_post_scan_reloads_the_station_list(client: TestClient) -> None:
    # The fake replays the real 41-ensemble capture; after a scan the list is the
    # parsed real stations, not the two hand-authored fixtures.
    resp = client.post("/api/scan")
    assert resp.status_code == 200
    stations = client.get("/api/stations").json()
    assert len(stations) > 2


async def test_events_stream_opens_with_the_current_state() -> None:
    # The SSE endpoint holds the connection open forever (and HTTP test clients
    # buffer/deadlock on that), so drive the ASGI app directly: capture the first
    # response body chunk, then signal disconnect so the generator unwinds. This
    # asserts a fresh client converges immediately on the current state (D7).
    state = make_state()
    broadcaster = Broadcaster()
    dispatcher = Dispatcher(
        state=state, radio_cli=RadioCli(path=str(FAKE)), broadcaster=broadcaster
    )
    app = create_app(state=state, dispatcher=dispatcher, broadcaster=broadcaster)

    scope: MutableMapping[str, Any] = {
        "type": "http",
        "method": "GET",
        "path": "/api/events",
        "headers": [],
        "query_string": b"",
    }
    sent: list[MutableMapping[str, Any]] = []
    disconnect = asyncio.Event()

    async def receive() -> MutableMapping[str, Any]:
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message: MutableMapping[str, Any]) -> None:
        sent.append(message)
        if message["type"] == "http.response.body" and message.get("body"):
            disconnect.set()  # got our first chunk — let the generator unwind

    await asyncio.wait_for(app(scope, receive, send), timeout=5)

    start = next(m for m in sent if m["type"] == "http.response.start")
    assert start["status"] == 200
    assert (b"content-type", b"text/event-stream") in [
        (k, v.split(b";")[0].strip()) for k, v in start["headers"]
    ]
    body = next(m["body"] for m in sent if m["type"] == "http.response.body" and m.get("body"))
    data_line = next(line for line in body.decode().splitlines() if line.startswith("data:"))
    assert json.loads(data_line[len("data:") :].strip()) == {
        "volume": 25,
        "station": {"id": 0, "name": "BR Klassik"},
        "advisory": None,
    }
