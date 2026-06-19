"""Unit tests for settings load/save (~/.sunflower-radio.json).

Persists volume + the selection as ServId+Label (NOT a bare index — D10), with
NO I2S keys (Q9). An absent file yields defaults (volume 25, no selection).
"""

import json
from pathlib import Path

from sunflower_radio.settings import Settings, load_settings, save_settings
from sunflower_radio.state import Selection


def test_absent_file_yields_defaults(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "nope.json")
    assert settings == Settings(volume=25, selection=None)


def test_round_trip_persists_volume_and_servid_label(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    original = Settings(volume=42, selection=Selection(srvid=300, label="Deutschlandfunk"))
    save_settings(original, path)
    assert load_settings(path) == original


def test_saved_file_carries_servid_label_and_no_i2s_keys(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    save_settings(Settings(volume=10, selection=Selection(srvid=7, label="X")), path)
    raw = json.loads(path.read_text())
    assert raw["volume"] == 10
    assert raw["station"] == {"srvid": 7, "label": "X"}
    assert "i2s" not in raw


def test_save_with_no_selection_persists_null_station(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    save_settings(Settings(volume=30, selection=None), path)
    raw = json.loads(path.read_text())
    assert raw["station"] is None
    assert load_settings(path) == Settings(volume=30, selection=None)
