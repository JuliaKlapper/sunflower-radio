"""Unit tests for the ensemble-scan parser (reuses the legacy read_stations logic).

Drives the real captured `tests/fixtures/ensemble_scan.json` (a non-hand-authored
`radio_cli -b D -u -k` capture) so the parser is exercised against the true shape,
plus small hand-built dicts for the edge cases (invalid ensemble, data services).
"""

import json
from pathlib import Path

from sunflower_radio.stations import Station, parse_stations

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_real_capture_yields_only_audio_services_from_valid_ensembles() -> None:
    dabinfo = json.loads((FIXTURES / "ensemble_scan.json").read_text())
    stations = parse_stations(dabinfo)

    assert stations, "the real capture has audio services"
    # ids are positional and contiguous from 0 (the ephemeral wire id, Q8b)
    assert [s.id for s in stations] == list(range(len(stations)))
    # every parsed station carries the off-the-wire tuning triple
    for s in stations:
        assert isinstance(s.srvid, int)
        assert isinstance(s.compid, int)
        assert isinstance(s.tune_idx, int)
        assert isinstance(s.name, str)


def test_parse_skips_invalid_ensembles_and_data_services() -> None:
    dabinfo = {
        "ensembleList": [
            {
                "DigradStatus": {"valid": False, "tune_index": 0},
                "DigitalServiceList": {
                    "ServiceList": [
                        {
                            "ServId": 1,
                            "AudioOrDataFlag": 0,
                            "Label": "Should be skipped (invalid ensemble)",
                            "ComponentList": [{"comp_ID": 10}],
                        }
                    ]
                },
            },
            {
                "DigradStatus": {"valid": True, "tune_index": 4},
                "DigitalServiceList": {
                    "ServiceList": [
                        {
                            "ServId": 2,
                            "AudioOrDataFlag": 1,  # data service → skipped
                            "Label": "EPG Data",
                            "ComponentList": [{"comp_ID": 20}],
                        },
                        {
                            "ServId": 3,
                            "AudioOrDataFlag": 0,  # audio service → kept
                            "Label": "Real Audio Station",
                            "ComponentList": [{"comp_ID": 30}],
                        },
                    ]
                },
            },
        ]
    }

    stations = parse_stations(dabinfo)

    assert stations == [Station(id=0, name="Real Audio Station", srvid=3, compid=30, tune_idx=4)]


def test_parse_tolerates_an_empty_ensemble_list() -> None:
    assert parse_stations({"ensembleList": []}) == []
