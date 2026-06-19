"""Ensemble-scan JSON → flat station list.

A faithful port of the legacy `read_stations` parse (`legacy/simple-dab-radio.py`):
walk every *valid* ensemble, keep its audio services (skip data services), and
carry the board's tuning triple (`srvid`, `compid`, `tune_idx`). The `id` is
purely positional — it is the station's index in this list and is the only field
that reaches the wire (Q8b); `srvid/compid/tune_idx` stay server-side.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Station:
    """One tunable audio service. `id` is the ephemeral positional wire id (Q8b)."""

    id: int
    name: str
    srvid: int
    compid: int
    tune_idx: int


def parse_stations(dabinfo: dict[str, Any]) -> list[Station]:
    """Parse a `radio_cli -b D -u -k` capture into positionally-ided stations."""
    stations: list[Station] = []
    for ensemble in dabinfo.get("ensembleList", []):
        digrad = ensemble["DigradStatus"]
        if not digrad["valid"]:
            continue
        tune_idx = digrad["tune_index"]
        for service in ensemble["DigitalServiceList"]["ServiceList"]:
            if service["AudioOrDataFlag"]:
                continue  # data service, not audio
            stations.append(
                Station(
                    id=len(stations),
                    name=service["Label"],
                    srvid=service["ServId"],
                    compid=service["ComponentList"][0]["comp_ID"],
                    tune_idx=tune_idx,
                )
            )
    return stations
