# CLAUDE.md

Cross-cutting guidance for the **sunflower-radio** monorepo. Component-specific
detail lives in `pi-backend/CLAUDE.md` and `web/CLAUDE.md`.

## Project Overview

`sunflower-radio` is a DAB+ radio controller for the Raspberry Pi. A single
async Python service owns the proprietary `radio_cli` board, the rotary encoder,
and a FastAPI HTTP+SSE API; a statically-exported Next.js UI (served by the same
process) and the physical knob are both first-class control surfaces that
converge in real time via server-authoritative Server-Sent Events.

It is a GPL-3.0 derivative of [`simple-dab-radio`](https://github.com/bablokb/simple-dab-radio)
by Bernhard Bablok (attribution preserved in `LICENSE` / `Readme.md`).

## Repository Layout

- `pi-backend/` — the async Python service (`sunflower_radio/` package + `tests/`).
  See `pi-backend/CLAUDE.md`. `pi-backend/legacy/simple-dab-radio.py` is the
  **frozen** pre-rewrite original, kept only as a port reference and deleted once
  Phases 4-6 finish; it is excluded from all checks.
- `web/` — the Next.js static-export UI. See `web/CLAUDE.md`.
- `tools/` — install/deploy/quality scripts (`check`, `setup`, `install`, ...).
- `docs/` — decision log (`decisions.md`, the source of truth), plans, explanations.

## Quality Gate (Backpressure)

Automated quality feedback gates every feature commit. **The rule:**

> After editing code, run `tools/check`. Loop until green. **Never commit until green.**

- `tools/check` — full check, both components, run-all-and-report (every step
  runs; non-zero exit if any failed).
- `tools/check pi-backend` / `tools/check web` — scope to one component.
- `tools/check --fast` — lint + types + **unit** tests only (no Playwright e2e);
  this is what the pre-commit hook runs.
- `tools/check --fix` — apply safe auto-fixes (ruff/eslint/prettier), then re-report.
- `tools/setup` — one-time: wires `core.hooksPath` so the pre-commit hook runs
  `tools/check --fast` (report-only; it never mutates or re-stages files).

Run `tools/setup` once after cloning. The pre-commit hook blocks a commit whose
fast check fails; fix it (`tools/check --fix`) and commit again.

## Key External Dependency

`/usr/local/sbin/radio_cli` — the uGreen proprietary CLI (a stable symlink on the
Pi), installed separately. Flags used: `-b D -o 0` (boot), `-k` (stop),
`-l <0-63>` (volume), `-c <compid> -e <srvid> -f <tune_idx> -p` (tune),
`-b D -u -k` (full ensemble scan).
