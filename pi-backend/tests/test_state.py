"""Unit tests for RadioState — the pure state core above the seams.

Covers: the 0-100 wire volume → 0-63 hardware conversion (Q8b/Q13.2b), volume
clamping, station wraparound, the snapshot wire shape (Q8b/Q8c), and the D10
selection-reconciliation helper (ServId → Label → fallback-to-index-0 + advisory)
including the empty-list / station-gone edge cases that must never crash.
"""

import pytest

from sunflower_radio.state import RadioState, Selection
from sunflower_radio.stations import Station


def make_stations() -> list[Station]:
    return [
        Station(id=0, name="BR Klassik", srvid=100, compid=10, tune_idx=1),
        Station(id=1, name="Bayern 3", srvid=200, compid=20, tune_idx=1),
        Station(id=2, name="Deutschlandfunk", srvid=300, compid=30, tune_idx=2),
    ]


# --- volume conversion + clamp ------------------------------------------------


@pytest.mark.parametrize(
    ("pct", "raw"),
    [(0, 0), (100, 63), (50, 32), (1, 1), (49, 31), (75, 47), (25, 16)],
)
def test_wire_volume_converts_to_hardware_raw(pct: int, raw: int) -> None:
    state = RadioState(stations=make_stations())
    state.volume = pct
    assert state.raw_volume == raw


def test_step_volume_clamps_to_0_and_100() -> None:
    state = RadioState(stations=make_stations())
    state.volume = 0
    state.step_volume(-1)
    assert state.volume == 0
    state.volume = 100
    state.step_volume(1)
    assert state.volume == 100


def test_step_volume_moves_by_one_percent_per_detent() -> None:
    state = RadioState(stations=make_stations())
    state.volume = 50
    state.step_volume(1)
    assert state.volume == 51
    state.step_volume(-1)
    assert state.volume == 50


# --- station wraparound -------------------------------------------------------


def test_step_station_wraps_at_both_ends() -> None:
    state = RadioState(stations=make_stations())
    state.station_index = 2
    state.step_station(1)
    assert state.station_index == 0  # wrap forward
    state.step_station(-1)
    assert state.station_index == 2  # wrap backward


def test_step_station_is_a_noop_on_an_empty_list() -> None:
    state = RadioState(stations=[])
    state.step_station(1)  # must not raise (no idx % 0)
    assert state.current_station is None


# --- snapshot wire shape ------------------------------------------------------


def test_snapshot_shape_with_a_selection() -> None:
    state = RadioState(stations=make_stations())
    state.volume = 50
    state.station_index = 1
    assert state.snapshot() == {
        "volume": 50,
        "station": {"id": 1, "name": "Bayern 3"},
        "advisory": None,
    }


def test_snapshot_station_is_null_when_no_stations() -> None:
    state = RadioState(stations=[])
    state.reconcile(None)  # the realistic startup path sets the "no stations" advisory
    snap = state.snapshot()
    assert snap["station"] is None
    assert snap["advisory"] is not None  # "no stations — rescan"


# --- D10 reconciliation -------------------------------------------------------


def test_reconcile_matches_by_servid_first() -> None:
    state = RadioState(stations=make_stations())
    # ServId 300 == Deutschlandfunk (index 2); Label deliberately stale/wrong
    state.reconcile(Selection(srvid=300, label="Some Old Name"))
    assert state.station_index == 2
    assert state.advisory is None


def test_reconcile_falls_through_to_label_when_servid_changed() -> None:
    state = RadioState(stations=make_stations())
    # broadcaster renumbered the ServId, but the Label still matches index 1
    state.reconcile(Selection(srvid=99999, label="Bayern 3"))
    assert state.station_index == 1
    assert state.advisory is None


def test_reconcile_falls_back_to_index_0_with_advisory_when_station_gone() -> None:
    state = RadioState(stations=make_stations())
    state.reconcile(Selection(srvid=99999, label="Vanished Station"))
    assert state.station_index == 0
    assert state.advisory is not None  # "previous station unavailable / rescan"


def test_reconcile_on_empty_list_does_not_crash_and_advises() -> None:
    state = RadioState(stations=[])
    state.reconcile(Selection(srvid=100, label="BR Klassik"))
    assert state.current_station is None
    assert state.advisory is not None


def test_reconcile_with_no_persisted_selection_defaults_to_index_0_quietly() -> None:
    state = RadioState(stations=make_stations())
    state.reconcile(None)
    assert state.station_index == 0
    assert state.advisory is None  # a fresh boot is not an error condition
