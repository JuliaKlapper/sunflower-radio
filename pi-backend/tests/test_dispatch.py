"""Unit tests for the dispatch layer (event → state mutation → RadioCli call).

Drives a scripted `FakeEventSource` through the `Dispatcher` wired to a REAL
`RadioCli` over the committed `fake_radio_cli` binary (the Phase-4 seam), then
asserts on the argv the board actually received — proving the whole vertical
(events → mode toggle → state → RadioCli → subprocess) end to end. A turn in
VOLUME mode emits `-l`; the button toggles to TUNER mode; a turn there emits the
`-c/-e/-f/-p` tune for the wrapped-around station.
"""

from collections.abc import Sequence
from pathlib import Path

import pytest

from sunflower_radio.dispatch import Dispatcher
from sunflower_radio.events import ButtonEvent, Event, FakeEventSource, RotaryEvent
from sunflower_radio.radio_cli import RadioCli
from sunflower_radio.state import RadioState
from sunflower_radio.stations import Station

FAKE = Path(__file__).parent / "fixtures" / "fake_radio_cli"


def make_state() -> RadioState:
    state = RadioState(
        stations=[
            Station(id=0, name="BR Klassik", srvid=100, compid=10, tune_idx=1),
            Station(id=1, name="Bayern 3", srvid=200, compid=20, tune_idx=3),
        ]
    )
    state.volume = 50
    state.station_index = 0
    return state


async def run_dispatch(
    state: RadioState, log: Path, monkeypatch: pytest.MonkeyPatch, script: Sequence[Event]
) -> list[list[str]]:
    monkeypatch.setenv("FAKE_RADIO_CLI_LOG", str(log))
    dispatcher = Dispatcher(state=state, radio_cli=RadioCli(path=str(FAKE)))
    await dispatcher.run(FakeEventSource(script))
    if not log.exists():
        return []
    return [line.split() for line in log.read_text().splitlines()]


async def test_turn_in_volume_mode_sets_volume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = make_state()
    calls = await run_dispatch(state, tmp_path / "log", monkeypatch, [RotaryEvent(direction=1)])
    # 50 → 51 percent → round(51*63/100) = 32 raw
    assert calls == [["-l", "32"]]
    assert state.volume == 51


async def test_button_toggles_into_tuner_mode_then_turn_tunes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = make_state()
    script: list[Event] = [
        ButtonEvent(pressed=True),  # press-down: ignored
        ButtonEvent(pressed=False),  # release: toggle → TUNER mode
        RotaryEvent(direction=1),  # advance station 0 → 1 (Bayern 3) and tune
    ]
    calls = await run_dispatch(state, tmp_path / "log", monkeypatch, script)
    assert calls == [["-c", "20", "-e", "200", "-f", "3", "-p"]]
    assert state.station_index == 1


async def test_second_button_press_returns_to_volume_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = make_state()
    script: list[Event] = [
        ButtonEvent(pressed=False),  # → TUNER
        ButtonEvent(pressed=False),  # → back to VOLUME
        RotaryEvent(direction=-1),  # volume down: 50 → 49 → round(49*63/100)=31
    ]
    calls = await run_dispatch(state, tmp_path / "log", monkeypatch, script)
    assert calls == [["-l", "31"]]
    assert state.volume == 49
