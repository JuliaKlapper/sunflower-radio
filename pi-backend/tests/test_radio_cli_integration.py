"""Integration test for the RadioCli seam against the committed fake binary.

This is the ONE test that exercises the real subprocess path (Q13.1/13.3): it
constructs RadioCli over `tests/fixtures/fake_radio_cli` and asserts on the argv
the wrapper actually handed the binary — exact flags, exact order, and crucially
NO stray `sudo` (the bug the legacy file shipped). The fake records argv to a log
file; the assertions read that log.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from sunflower_radio.radio_cli import RadioCli

FIXTURES = Path(__file__).parent / "fixtures"
FAKE = FIXTURES / "fake_radio_cli"


@dataclass
class Harness:
    """A RadioCli wired to the fake binary plus the argv log it writes to."""

    cli: RadioCli
    log: Path

    def calls(self) -> list[list[str]]:
        """The argv of each invocation recorded so far, in order."""
        if not self.log.exists():
            return []
        return [line.split() for line in self.log.read_text().splitlines()]


@pytest.fixture
def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Harness:
    log = tmp_path / "argv.log"
    monkeypatch.setenv("FAKE_RADIO_CLI_LOG", str(log))
    # scan_dir = tmp_path: the fake writes ensemblescan__.json there (its cwd),
    # and scan() reads it back from the same dir.
    return Harness(cli=RadioCli(path=str(FAKE), scan_dir=tmp_path), log=log)


async def test_boot_passes_dab_analog_flags(harness: Harness) -> None:
    await harness.cli.boot()
    assert harness.calls() == [["-b", "D", "-o", "0"]]


async def test_shutdown_passes_kill_flag(harness: Harness) -> None:
    await harness.cli.shutdown()
    assert harness.calls() == [["-k"]]


async def test_set_volume_passes_raw_level(harness: Harness) -> None:
    await harness.cli.set_volume(63)
    assert harness.calls() == [["-l", "63"]]


async def test_tune_passes_component_service_index(harness: Harness) -> None:
    await harness.cli.tune(compid=49186, srvid=3771797692, tune_idx=2)
    assert harness.calls() == [["-c", "49186", "-e", "3771797692", "-f", "2", "-p"]]


async def test_no_invocation_is_prefixed_with_sudo(harness: Harness) -> None:
    await harness.cli.boot()
    await harness.cli.shutdown()
    await harness.cli.set_volume(10)
    await harness.cli.tune(compid=1, srvid=2, tune_idx=3)
    assert all("sudo" not in call for call in harness.calls())


async def test_scan_passes_full_ensemble_flags_and_returns_file_json(
    harness: Harness,
) -> None:
    # radio_cli writes the scan to ensemblescan__.json (not stdout) and the `-k`
    # that aborts the scan is dropped.
    result = await harness.cli.scan()
    assert harness.calls() == [["-b", "D", "-u"]]
    expected = json.loads((FIXTURES / "ensemble_scan.json").read_text())
    assert result == expected


async def test_nonzero_exit_is_surfaced(harness: Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAKE_RADIO_CLI_RC", "7")
    with pytest.raises(RuntimeError):
        await harness.cli.boot()
