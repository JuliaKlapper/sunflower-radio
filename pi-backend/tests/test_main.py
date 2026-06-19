"""Unit tests for the composition-root path resolution (Q13.3d).

The full wiring (RadioState, event loop, FastAPI) lands in Phases 5-6; here we
only pin the radio_cli path-resolution policy: env override → stable default.
"""

import pytest

from sunflower_radio.__main__ import DEFAULT_RADIO_CLI_PATH, resolve_radio_cli_path


def test_defaults_to_the_stable_symlink(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RADIO_CLI_PATH", raising=False)
    assert resolve_radio_cli_path() == DEFAULT_RADIO_CLI_PATH
    assert DEFAULT_RADIO_CLI_PATH == "/usr/local/sbin/radio_cli"


def test_env_override_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RADIO_CLI_PATH", "/tmp/fake_radio_cli")
    assert resolve_radio_cli_path() == "/tmp/fake_radio_cli"
