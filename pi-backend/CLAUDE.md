# pi-backend — CLAUDE.md

The async Python service: rotary input + HTTP/SSE API + the `radio_cli` board in
one `asyncio` process. Built in Phases 4-6; see `docs/agents/plans/`.

## Toolchain

Managed by **uv** (Python pinned to 3.11 via `.python-version` to match the Pi).

```bash
uv sync                 # create .venv + install deps (run from pi-backend/)
uv run pytest           # run tests
uv run ruff check .     # lint
uv run mypy .           # type-check (strict)
```

`evdev` is a Linux-only dependency (platform marker in `pyproject.toml`); it is
not installed on macOS dev machines, so anything importing it must be confined to
the `EvdevEventSource` seam.

## Quality Gate

Same rule as the root: **after editing, run `tools/check pi-backend`; loop until
green; never commit until green.** The pre-commit hook runs `tools/check --fast`.

## Architecture (target — Phases 4-6)

Two seams isolate every impure edge; everything above them is unit-tested:

- `radio_cli.py` — `RadioCli` async wrapper over `radio_cli` (ctor takes `path`,
  pure DI); speaks raw 0-63 volume. The subprocess seam.
- `events.py` — `RotaryEvent`/`ButtonEvent`, `EventSource` protocol,
  `EvdevEventSource` (decode) + test `FakeEventSource`. The input seam.
- `state.py` — `RadioState`: volume clamp + 0-100→0-63 conversion, station
  wraparound, selection reconciliation (ServId→Label→fallback), `snapshot()`.
- `dispatch.py` — event/command → state mutation → `RadioCli` call → broadcast.
- `broadcaster.py` — SSE subscriber registry; **coalesce-to-latest** size-1
  buffer (Phase 10) bounds memory on the 512 MB Pi.
- `api.py` — FastAPI `/api/*` + `StaticFiles` mount at `/`.
- `__main__.py` — composition root (resolves `RADIO_CLI_PATH`, wires everything).

## Conventions

- TDD: assertions first. Test through the seams against fakes; the one
  integration test drives the committed `tests/fixtures/fake_radio_cli`.
- Never put test fixtures under the install-shipped source (PATH-shadowing hazard
  for the fake binary) — they live under `tests/`.
- `legacy/` is the frozen pre-rewrite reference; never edit or lint it.
