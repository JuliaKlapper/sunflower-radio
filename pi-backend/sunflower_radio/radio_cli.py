"""RadioCli — the async subprocess seam over the proprietary `radio_cli` board.

A faithful translator: each method maps to one `radio_cli` invocation with the
exact flags the board expects, run via `asyncio.create_subprocess_exec` so a
multi-second `scan()` never blocks the rotary loop or any SSE client. The ctor
takes the binary `path` (pure DI, Q13.3d) so tests can point it at the fake.

Volume is spoken in the board's native raw 0-63 range (Q13.2b); the 0-100→0-63
conversion lives above this seam in RadioState. No `sudo` is ever prepended —
that was the legacy bug.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, cast

# radio_cli v3.2.1 writes the full-scan result to this fixed filename in its
# working directory (the --usage text claims "full_scan.json", but the shipped
# binary actually uses this name). The JSON is NOT printed to stdout.
_SCAN_FILENAME = "ensemblescan__.json"


class RadioCli:
    """Async wrapper around the uGreen `radio_cli` board CLI."""

    def __init__(self, path: str, scan_dir: Path | None = None) -> None:
        self._path = path
        # `scan()` runs radio_cli here (so its ensemblescan__.json lands in a
        # known, writable place) and reads the result back. Defaults to the home
        # dir of the running user (the service runs as root → /root).
        self._scan_dir = scan_dir if scan_dir is not None else Path.home()

    async def boot(self) -> None:
        """Load DAB firmware + boot, analog (built-in DAC) output."""
        await self._run("-b", "D", "-o", "0")

    async def shutdown(self) -> None:
        """Stop the board (silences audio); used by systemd ExecStop too."""
        await self._run("-k")

    async def set_volume(self, raw_0_63: int) -> None:
        """Set volume in the board's native 0-63 range."""
        await self._run("-l", str(raw_0_63))

    async def tune(self, compid: int, srvid: int, tune_idx: int) -> None:
        """Tune to a service: component id, service id, ensemble tune index."""
        await self._run("-c", str(compid), "-e", str(srvid), "-f", str(tune_idx), "-p")

    async def scan(self) -> dict[str, Any]:
        """Full ensemble scan (reboots the board, ~30s); returns the parsed JSON.

        radio_cli writes the result to `ensemblescan__.json` in its working dir
        (NOT stdout), so we run it in `scan_dir` and read the file back. A
        trailing `-k` (in the plan's original flags) shuts the board down before
        the scan completes, so it is deliberately omitted.
        """
        await self._run("-b", "D", "-u", cwd=self._scan_dir)
        return cast(dict[str, Any], json.loads((self._scan_dir / _SCAN_FILENAME).read_text()))

    async def _run(self, *args: str, cwd: Path | None = None) -> str:
        proc = await asyncio.create_subprocess_exec(
            self._path,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            # the scan prints a location questionnaire to stdin; never block on it
            stdin=asyncio.subprocess.DEVNULL,
            cwd=None if cwd is None else str(cwd),
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"radio_cli {' '.join(args)} exited {proc.returncode}: "
                f"{stderr.decode(errors='replace').strip()}"
            )
        return stdout.decode()
