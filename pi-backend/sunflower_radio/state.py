"""RadioState — the pure, server-authoritative state core (above both seams).

Holds the canonical wire volume (0-100, Q8b) and the current station selection,
and owns the two conversions the rest of the system depends on:

- volume 0-100 → hardware raw 0-63 (Q13.2b): the conversion lives here, NOT in
  the RadioCli wrapper, so the seam stays a dumb translator.
- the D10 selection-reconciliation key (ServId → Label → fall back to index 0 +
  advisory): the single helper reused by `__main__` startup, the scan endpoint
  (Phase 6), and the Rescan UI (Phase 8). It never crashes on a missing/empty
  list and never silently tunes a vanished service.
"""

from dataclasses import dataclass, field
from typing import Any

from sunflower_radio.stations import Station

_HARDWARE_MAX = 63  # the built-in DAC's raw volume ceiling (radio_cli -l 0..63)

# Advisory messages surfaced as an additive optional field on the snapshot (D10,
# consistent with Q8c additive-only — no wire-contract break).
_NO_STATIONS = "No stations found — run a scan."
_STATION_UNAVAILABLE = "Previous station is unavailable — a rescan is recommended."


@dataclass(frozen=True)
class Selection:
    """A persisted station selection, by the two broadcaster-mutable keys (D10)."""

    srvid: int
    label: str


@dataclass
class RadioState:
    """Mutable radio state: volume (0-100), the station list, and current index."""

    stations: list[Station]
    volume: int = 25
    station_index: int = 0
    advisory: str | None = field(default=None)

    @property
    def raw_volume(self) -> int:
        """The current wire volume converted to the board's raw 0-63 range."""
        return round(self.volume * _HARDWARE_MAX / 100)

    def step_volume(self, direction: int) -> None:
        """Nudge the volume by one detent, clamped to 0-100."""
        self.volume = max(0, min(100, self.volume + direction))

    def step_station(self, direction: int) -> None:
        """Advance the selection by one detent, wrapping; a no-op when empty."""
        if not self.stations:
            return
        self.station_index = (self.station_index + direction) % len(self.stations)

    @property
    def current_station(self) -> Station | None:
        """The currently-selected station, or None when the list is empty."""
        if not self.stations:
            return None
        return self.stations[self.station_index]

    def reconcile(self, persisted: Selection | None) -> None:
        """Resolve a persisted selection against the current list (D10).

        Order: (1) match ServId; (2) else match Label; (3) else fall back to
        index 0 and raise the "previous station unavailable" advisory. An empty
        list yields the "no stations" advisory. A fresh boot with no persisted
        selection is NOT an error — index 0, no advisory.
        """
        if not self.stations:
            self.station_index = 0
            self.advisory = _NO_STATIONS
            return

        if persisted is not None:
            for index, station in enumerate(self.stations):
                if station.srvid == persisted.srvid:
                    self.station_index = index
                    self.advisory = None
                    return
            for index, station in enumerate(self.stations):
                if station.name == persisted.label:
                    self.station_index = index
                    self.advisory = None
                    return

        self.station_index = 0
        self.advisory = _STATION_UNAVAILABLE if persisted is not None else None

    def snapshot(self) -> dict[str, Any]:
        """The server-authoritative state for the wire/SSE (Q8b/Q8c shape).

        `advisory` is an additive optional field (null when clear, D10).
        """
        station = self.current_station
        return {
            "volume": self.volume,
            "station": None if station is None else {"id": station.id, "name": station.name},
            "advisory": self.advisory,
        }
