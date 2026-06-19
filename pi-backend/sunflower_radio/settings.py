"""Persisted settings: ~/.sunflower-radio.json (volume + selection).

The selection is persisted as ServId + Label (the two broadcaster-mutable keys),
NOT the bare positional index the legacy code used (D10) — the index is recomputed
at startup by reconciling against the freshly-loaded station list. There are NO
I2S keys (Q9, dropped). An absent file yields defaults (volume 70, no selection),
so a fresh Pi boots cleanly.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from sunflower_radio.state import Selection

DEFAULT_SETTINGS_PATH = Path.home() / ".sunflower-radio.json"
_DEFAULT_VOLUME = 70


@dataclass
class Settings:
    """The persisted state restored on startup."""

    volume: int = _DEFAULT_VOLUME
    selection: Selection | None = None


def load_settings(path: Path = DEFAULT_SETTINGS_PATH) -> Settings:
    """Load settings, tolerating an absent file (returns defaults)."""
    if not path.exists():
        return Settings()
    data = json.loads(path.read_text())
    station = data.get("station")
    selection = (
        Selection(srvid=station["srvid"], label=station["label"]) if station is not None else None
    )
    return Settings(volume=data.get("volume", _DEFAULT_VOLUME), selection=selection)


def save_settings(settings: Settings, path: Path = DEFAULT_SETTINGS_PATH) -> None:
    """Write settings as JSON (volume + ServId/Label selection, no I2S keys)."""
    station = (
        None
        if settings.selection is None
        else {"srvid": settings.selection.srvid, "label": settings.selection.label}
    )
    path.write_text(json.dumps({"volume": settings.volume, "station": station}, indent=2))
