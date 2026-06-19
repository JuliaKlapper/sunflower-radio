---
date: 2026-06-19T10:27:49+00:00
git_commit: 4ca7605c3aa0f76b45c981c133617fabc8372e08
branch: master
topic: "sunflower-radio — async Pi backend + Next.js web UI rewrite"
tags: [plan, pi-backend, web, tools, sse, rotary, backpressure]
status: draft
---

# sunflower-radio Implementation Plan

## Overview

Rewrite the minimal DAB+ radio controller into **`sunflower-radio`**: a single
async Python process on the Raspberry Pi that owns the `radio_cli` board, the
rotary encoder, and a FastAPI HTTP+SSE API — fronted by a statically-exported
Next.js single-screen web UI served by the same process. Both the physical knob
and any LAN browser are first-class control surfaces that converge in real time
via server-authoritative Server-Sent Events.

This plan translates the **completed** decision log (`docs/decisions.md`,
D1–D9 / Q8–Q18, all resolved) into 10 phased, checkbox-tracked phases. No design
questions remain open. Each phase is tagged with a suggested model tier per the
decision-log resume header.

## Current State Analysis

- **Single broken file:** `files/usr/local/sbin/simple-dab-radio.py` is a
  concatenated/duplicated paste — a second mangled `__main__` block
  (`:216-416`) with a stray module-level `else:`, duplicated method
  definitions, and `sudo` prepended to `radio_cli` args. This is the cause of
  the rotary failure (D3).
- **`4ca7605` is already `HEAD`** and `origin/master`. "Revert to last-good" is
  therefore a working-tree `git restore` of one file, **not** a commit-level
  revert (Q12.3 grounding correction).
- **Synchronous `subprocess.call` seam:** all `radio_cli` invocations are
  blocking `subprocess.call` in `Radio.start/stop/update_volume/update_tuner`
  + `read_stations`. No abstraction, no tests anywhere in the repo.
- **I2S branch present** (`read_settings`, `update_tuner`, `stop`) — dropped
  entirely by Q9; the `self._i2s_pid` `AttributeError` follow-up becomes moot
  because the whole branch is deleted, not patched.
- **`tools/install`** hardcodes `PROJECT="simple-dab-radio"`, appends rotary
  overlays to legacy `/boot/config.txt`, and enables `simple-dab-radio.service`
  — but the Pi actually runs **`dabboard.service`** (`files/etc/systemd/system/dabboard.service`).
- **License:** the repo **is GPL3** (`LICENSE` + `Readme.md` git-tracked,
  copyright "Bernhard Bablok"). The decision log's own verification follow-up
  (`decisions.md:1099-1104`) already flags that Q12.3's "no LICENSE → no
  attribution requirement" sub-rationale was wrong. The keep-history decision is
  unaffected: the rewrite is a derivative work and stays GPL3; bablokb's
  copyright + attribution are preserved.
- **`tools/install` mirror model:** `files/` → filesystem root. Post-restructure
  it ships `pi-backend/` source + `web/out/` and never ships `tests/`.

## Desired End State

- A monorepo `sunflower-radio` (own GitHub repo, fork link dropped, GPL3 kept)
  laid out as `pi-backend/` + `web/` + `tools/` + `docs/`.
- One async Python service: rotary + HTTP API + SSE in a single `asyncio` loop,
  with a `RadioCli` async seam and an injected rotary event-source seam, both
  unit-tested against fakes; one integration layer exercises a committed fake
  `radio_cli` binary.
- A statically-exported Next.js App Router UI (single sunflower screen: live
  circle, prev/next stepper, tappable dots, debounced volume slider, secondary
  Rescan, yellow-on-dark theme) served from `/` by FastAPI, API at `/api/*`.
- A backpressure harness (`tools/check` + pre-commit gate + advisory `Stop`
  hook) gating every feature commit from Phase 3 onward.
- Clean install on the Pi via `tools/install`, running `sunflower-radio.service`
  with an `ExecStop=radio_cli -k`, controllable from `http://<pi>/` and the knob.

## What We're NOT Doing

- **No I2S** audio path (`arecord | aplay`, `amixer`) — built-in DAC only (Q9).
- **No DLS / now-playing text** on the wire — deferred post-v1, purely additive (Q8c).
- **No Favourites, no geolocation Notes, no bottom-nav** — single screen (Q15b).
- **No auth / no versioned API** — LAN-only, unversioned `/api/*` (Q10, Q8).
- **No CI** — local `tools/check` + on-Pi smoke is the gate (Q13.6).
- **No manual theme toggle** — honor `prefers-color-scheme` only; toggle is post-v1 (Q15e).
- **No file-for-file Flutter port** — only the sunflower visual identity ports (Q15a).
- **No relicensing** — stays GPL3 (confirmed).
- **No firmware-load automation** beyond an idempotent boot check (verification follow-up).

## UI Mockups

Single screen, sunflower yellow-on-dark, no navigation (Q15a/b/c/d/e):

```
┌──────────────────────────────────────────┐
│                🌻 Sunflower                │
│                                            │
│                 ·   ·   ·                  │
│             ·               ·              │
│          ·       ┌───────┐     ·           │
│         ·        │  #03  │      ·          │   ← ring of dots; color/size
│         ·        │BR Klas│      ·          │     encodes distance from
│          ·       └───────┘     ·           │     selected (red→…→green)
│             ·               ·              │
│                 ·   ·   ·                  │
│                                            │
│            ◀     BR Klassik     ▶          │   ← prev/next stepper (immediate tune)
│                                            │
│     🔊 ─────────●──────────────   62%      │   ← horizontal volume slider (debounced)
│                                            │
│                            [ ⟳  Rescan ]   │   ← secondary utility button
└──────────────────────────────────────────┘
```

Scanning state (Q15b2) — overlay, controls disabled, board busy/audio interrupted:

```
┌──────────────────────────────────────────┐
│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│░                                          ░│
│░          Scanning airwaves…              ░│
│░          ▓▓▓▓▓▓▓▓▓░░░░░░░░░░              ░│
│░       (station + volume disabled)        ░│
│░                                          ░│
│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
└──────────────────────────────────────────┘
```

A physical-knob turn (or another client's change) moves the highlighted dot and
the slider live via SSE — except the slider freezes while the local user is
actively dragging, resuming reconciliation on release (Q15c, D7).

## Architecture and Code Reuse

**Two seams isolate every impure edge; everything above is unit-tested (Q13).**

```
            ┌──────────────── one asyncio process (D4) ────────────────┐
 rotary ──▶ EvdevEventSource ─┐                                        │
 (evdev)    (decode raw)       │                                       │
                               ▼                                       │
            FastAPI /api/* ─▶ Dispatch ─▶ RadioState ─▶ RadioCli ─▶ radio_cli
            (HTTP commands)   (event→     (clamp, 0-100  (async 5-     (subprocess)
                               mutation)  →0-63, wrap)    method seam)
                                  │            │
                                  └────────────┴─▶ Broadcaster ─SSE─▶ all clients
                                       (coalesce-to-latest, D7a)
```

Reuse from the current file: the **ensemble-scan JSON parse** (`read_stations`,
`:104-128`) and the **`radio_cli` flag knowledge** (`-b D -o 0`, `-k`,
`-l <0-63>`, `-c/-e/-f/-p`, `-b D -u -k`). Everything else is rewritten async.
Old Flask server (`DABRadio/raspi_flask_server.py`) and the Flutter app are
read-only reference, never migrated.

**Affected file tree (post-restructure):**

- `pi-backend/`
  - `sunflower_radio/`
    - `__main__.py` — composition root: resolve `RADIO_CLI_PATH` env → default constant; wire `RadioCli`, `EvdevEventSource`, `RadioState`, `Broadcaster`, FastAPI; run uvicorn
    - `radio_cli.py` — `RadioCli` async wrapper; ctor `path` arg; `boot/shutdown/set_volume(raw_0_63)/tune(compid,srvid,tune_idx)/scan()` (Q13.2)
    - `state.py` — `RadioState`: volume clamp + `0-100`→`0-63` conversion, station wraparound, current-snapshot `{volume, station:{id,name}}`
    - `events.py` — `RotaryEvent`/`ButtonEvent` dataclasses, `EventSource` protocol, `EvdevEventSource` (decode), test `FakeEventSource` (Q13.5)
    - `dispatch.py` — event/command → `RadioState` mutation → `RadioCli` call → broadcast
    - `broadcaster.py` — subscriber registry of async queues; **coalesce-to-latest** size-1 buffer; write-timeout disconnect (D7a)
    - `api.py` — FastAPI: `GET /api/state|stations|events`, `POST /api/scan|volume|station`; structured error model; `StaticFiles` mount at `/` (D5/C1)
    - `settings.py` — load/save `~/.sunflower-radio.json` (no I2S keys)
    - `stations.py` — ensemble-scan JSON → `[{id,name, srvid,compid,tune_idx}]`
  - `tests/`
    - `fixtures/fake_radio_cli` — committed extensionless executable, dumb recorder (Q13.3)
    - `fixtures/ensemble_scan.json` — **real** `radio_cli -b D -u -k` capture
    - `test_state.py`, `test_dispatch.py`, `test_broadcaster.py`, `test_events.py`, `test_radio_cli_integration.py`, `test_api.py`
  - `pyproject.toml` — deps + ruff/mypy/pytest config
  - `CLAUDE.md` — Python/asyncio component guidance (Q16)
- `web/`
  - `app/` — `layout.tsx`, `page.tsx` (App Router, mostly `"use client"`)
  - `components/` — `SunflowerCircle.tsx`, `StationStepper.tsx`, `VolumeSlider.tsx`, `RescanButton.tsx`, `ScanningOverlay.tsx`
  - `lib/` — `api.ts` (fetch client), `useStateStream.ts` (`EventSource` hook), `types.ts`
  - `tests/` — Vitest component/logic; `e2e/` Playwright SSE/multi-client
  - `next.config.js` (`output: 'export'`), `package.json`, `tsconfig.json`, `.eslintrc`, `.prettierrc`
  - `CLAUDE.md` — Next.js component guidance (Q16)
- `tools/`
  - `install` (rewritten), `deploy`, `restart`, `logs`, `smoke`, `check`, `setup`
  - `git-hooks/pre-commit` — calls `tools/check --fast`
- `docs/` — `decisions.md`, `homework.md`, `explanations/`, `agents/plans/`
- `CLAUDE.md` — root, cross-cutting only (Q16); `LICENSE` (GPL3), `Readme.md`

## Performance Considerations

- **Pi Zero 2 W, 512 MB:** one process keeps RAM low (D4). The SSE broadcaster's
  **coalesce-to-latest** size-1 per-client buffer (D7a) bounds memory by
  construction — a stalled/asleep client can't grow an unbounded queue.
- **`scan()` is multi-second and reboots the board** — it must be `async` so it
  never blocks rotary input or other SSE clients (Q13.2). UI disables controls +
  shows the scanning overlay while it runs (Q15b2).
- **Volume slider** is debounced client-side (no HTTP-per-pixel); only commits on
  settle/throttle (Q15c, D7 escape hatch).
- **Static export** served by FastAPI `StaticFiles` is trivial load for the Pi.

## Migration Notes

- **Settings:** none — `~/.sunflower-radio.json` regenerates on first run; old
  `~/.simple-dab-radio.json` is abandoned (Q11). New format drops all I2S keys.
- **Git history:** kept; `git remote set-url origin <new>`, push to fresh
  `JuliaKlapper/sunflower-radio` over SSH (Q12.3). No "forked from" banner. GPL3 + per-commit
  authorship preserved.
- **Service cutover:** `dabboard.service` → `sunflower-radio.service` swaps
  atomically in **Phase 9 of this plan** with `ExecStop=radio_cli -k` preserved
  (shutdown chain). NB: Q12.1 calls this "Phase 8" in the decision log's
  *original 9-phase numbering*; inserting the Phase-3 backpressure scaffold (Q18.8)
  shifted every later phase down by one, so the log's "Phase 8" = this plan's Phase 9.
- **Boot config:** migrate rotary overlays to `/boot/firmware/config.txt`
  (modern bookworm); legacy `/boot/config.txt` is stale.

---

## Phase 1: Baseline regression anchor

**Model: Sonnet 4.6** (mechanical git + on-Pi ops, no async logic)

Establish a known-good rotary baseline in the project's final git home, on the
current flat layout, before any restructure — so a later regression can't be
blamed on the move (Q12 order-of-operations).

**Tasks**:
- [x] **(A) Git identity first:** created the **public** repo `JuliaKlapper/sunflower-radio` and repointed origin to `git@github.com:JuliaKlapper/sunflower-radio.git`; baseline history pushed. No `upstream` remnant; bablokb URL gone (Q12.3)
- [x] `git restore files/usr/local/sbin/simple-dab-radio.py` — discarded the broken working-tree edit (file returned to `4ca7605` content — NOT a commit revert)
- [x] Confirmed the restored file is byte-identical to `git show 4ca7605:files/usr/local/sbin/simple-dab-radio.py`
- [x] Deployed restored 238-line file to the Pi `/usr/local/sbin/simple-dab-radio.py`, restarted `dabboard.service` → `active`; logs show "Boot up successful / Tuned. Playing service: 53776"
- [x] **Captured the real ensemble scan**: the live `/root/stations.json` is the full-scan output (41 ensembles, 5 valid, 60 audio services) in the `ensembleList` shape; pulled verbatim to `pi-backend/tests/fixtures/ensemble_scan.json` (40 KB, real, non-hand-authored). Stashed locally; commit in Phase 4
- [x] ~~Resolve `which radio_cli` on the Pi~~ **RESOLVED (2026-06-19):** `/usr/local/sbin/radio_cli` is a stable symlink → `radio_cli_v3.2.1`. Use the symlink as the Phase-4 default constant
- [x] **Research only:** firmware boot is NOT a separate stateful step — `-b D` loads DAB firmware + boots in one idempotent call; commented `ExecStartPre=--boot=FIRMWARE` was redundant. Recorded in `decisions.md` (Phase 1 findings)
- [x] **Research only (D10):** tune to a stale/vanished `ServId` (`-e 99999`) exits **0** but prints "Could not start service" — exit code is NOT reliable. Service must reconcile persisted `{ServId,Label}` against the fresh list *before* tuning. Recorded in `decisions.md`
- [x] Baseline committed/pushed: `git restore` returned the file to the already-committed `4ca7605` HEAD, so the baseline is the pushed history (no new commit needed)

**Automated Verification**:
- [x] `git diff` shows `simple-dab-radio.py` restored to baseline (byte-identical to `4ca7605`)
- [x] `git remote -v` shows the new JuliaKlapper SSH origin, no bablokb URL
- [x] `ssh gingerberry@192.168.1.106 systemctl is-active dabboard.service` returns `active`
- [x] `ensemble_scan.json` parses as valid JSON, non-empty `ensembleList` (41 ensembles)

**Manual Verification** (regression target — the whole point of this phase) — **PASSED 2026-06-19** (after a hardware fix; see note):
- [x] **Physically turn the knob** on the Pi: rotation changes volume, push toggles to tuner mode, rotation changes station — verified working end-to-end
- [x] **Audio actually plays** from the speaker on the selected station — verified (analog `-o 0`)

> **NB — the knob never worked because of WIRING, not code.** The encoder/button were physically wired (via a Geekworm **G341** passive 1:2 GPIO splitter) to **GPIO 18/23 (encoder) + GPIO 14 (button)**, while `config.txt` listens on **17/27/22**. Diagnosed with `gpiomon` (no events on 17/27/22; live edges on 18/23/14). **Resolution: re-wired the knob to 17/27/22** to match the existing `config.txt` — confirmed via raw `evdev` (rotary REL_X ±1, button KEY_ENTER) then full functional test. **No software/config change was needed.** Plan impact: Phase 9 keeps the rotary overlay on **17/27/22** (the existing values), NOT 18/23. Full detail in `docs/decisions.md`.

---

## Phase 2: Repo cutover & restructure

**Model: Sonnet 4.6** (mechanical file moves + config)

Restructure once while the codebase is tiny; all new code thereafter lands in the
final layout (Q12, Q6/R1). Files-only + repo-identity; the systemd unit rename is
deferred to Phase 9 (Q12.1 — "Phase 8" in the log's original numbering; see
Migration Notes for the off-by-one from the inserted scaffold phase).

**Tasks**:
- [x] Create the monorepo skeleton: `pi-backend/`, `web/`, `tools/`, `docs/agents/plans/` (docs already exists) — created `web/` (placeholder `.gitkeep`); `pi-backend/`, `tools/`, `docs/agents/plans/` already present
- [x] Move the baseline `files/...` tree into the new layout as the install source root — `git mv files/usr/local/sbin/simple-dab-radio.py → pi-backend/legacy/simple-dab-radio.py` (history preserved, `--follow` traces to `2d53d7d`); systemd unit kept under `files/` for Phase 9 (`files/` mirror reworked then)
- [x] Move `tools/install` under the new `tools/` (already there); internals left for Phase 9
- [x] **Preserve GPL3:** `LICENSE` untouched; `Readme.md` now explicitly names Bernhard Bablok + GPL-3.0 derivative-work note (attribution strengthened)
- [x] Update root `Readme.md` lead to describe `sunflower-radio` (rename note), keeping original attribution section
- [x] Commit the restructure as one atomic "repo cutover" commit — `461e62a` (decisions.md edit + stale `simple-dab-radio.service` deletion deliberately excluded; the latter is Phase 9's drop)

**Automated Verification**:
- [x] `find . -maxdepth 2 -type d` shows `pi-backend web tools docs` present
- [x] `git log --oneline` shows preserved history (`2d53d7d`…`3118f89`) + the cutover commit `461e62a`
- [x] `grep -rl "Bernhard Bablok" LICENSE Readme.md` still matches (matches `Readme.md`, attribution intact)

---

## Phase 3: Backpressure scaffold

**Model: Sonnet 4.6** (config + scripts, no async logic)

Stand up automated quality feedback **before any feature code**, so every feature
commit from here is gated (Q18.8). Two enforcement layers + advisory harness hook.

**Tasks**:
- [x] `pi-backend/pyproject.toml`: configured **ruff** (lint+format), **mypy** (strict) + per-module evdev ignore, **pytest + pytest-asyncio** (`asyncio_mode=auto`, `pythonpath=["."]`); deps `fastapi/uvicorn/sse-starlette/evdev` (+httpx for TestClient). Managed by **uv**, Python pinned to **3.11** (`.python-version`) to match the Pi; `evdev` gated `sys_platform=='linux'` so `uv sync` works on macOS. `legacy/` excluded from ruff+mypy
- [x] `web/` scaffold config: `package.json` scripts (`lint`/`typecheck`/`test`/`test:e2e`/`format`), **eslint** (`next/core-web-vitals`+`next/typescript`), **prettier**, `tsconfig.json` (`tsc --noEmit`). Config only — npm install + app scaffold are Phase 7
- [x] `tools/check` orchestrator: **run-all-and-report** (collects failures, non-zero if any); `tools/check pi-backend|web` scopes it; thin — delegates to `uv run …` / `npm run …`. Web steps skip gracefully until `web/node_modules` exists
- [x] `tools/check --fix`: SAFE auto-fixes — **lint-fix first, then format last** (ruff check --fix → ruff format; eslint --fix → prettier) so whitespace wins; then re-verify
- [x] `tools/check --fast`: ruff + mypy + eslint + `tsc --noEmit` + **unit tests** (pytest + Vitest), Playwright e2e **gated out**; whole-repo scope
- [x] `tools/git-hooks/pre-commit` → `tools/check --fast`, **report-only, zero side effects**; `tools/setup` wires `git config core.hooksPath tools/git-hooks`
- [x] Advisory **`Stop` hook** in `.claude/settings.json`: when `git diff` shows `pi-backend|web|tools` changed, runs `tools/check --fast` and prints (non-blocking, `|| true`)
- [x] Pre-approved `tools/` script names in checked-in `.claude/settings.json` (`Bash(tools/check*|setup*|install*|deploy*|restart*|logs*|smoke*)`) — no broad ssh (user explicitly approved the settings edit past the self-modification guard)
- [x] Wrote the backpressure rule into root + `pi-backend/` + `web/` CLAUDE.md (root rewritten to cross-cutting per Q16: layout, gate, pointers)

**Automated Verification**:
- [x] `tools/check` exits **1** on an introduced lint error (`import os`/`x=1` scratch), **0** when clean
- [x] `tools/check --fix` auto-fixed the scratch file and ended fully clean (exit 0) — after correcting the fix ordering (lint-fix before format)
- [x] `tools/check --fast` completed (exit 0); Playwright not invoked (gated behind `FAST -eq 0`; web skipped pre-install)
- [x] `git config core.hooksPath` → `tools/git-hooks` after `tools/setup`
- [x] A commit with a lint error was **rejected** by the pre-commit hook (exit 1); the two clean Phase-3 commits succeeded through the hook

---

## Phase 4: Hardware stub — `RadioCli` seam + fake binary

**Model: Sonnet 4.6** (mechanical seam + fixture, guarded by Phase 3 harness)

Build the test scaffolding that makes the async rewrite testable without the Pi
(D2-iii "biggest accelerator", Q13.1/13.3). TDD throughout (assertions first).

**Tasks**:
- [ ] `sunflower_radio/radio_cli.py`: `RadioCli` async wrapper — ctor takes `path` (pure DI, Q13.3d); 5 methods over `asyncio.create_subprocess_exec`: `boot()` (`-b D -o 0`), `shutdown()` (`-k`), `set_volume(raw_0_63)` (`-l <n>`), `tune(compid, srvid, tune_idx)` (`-c -e -f -p`), `scan() -> ensemble_json` (`-b D -u -k`). Faithful translator; speaks **raw 0–63** (Q13.2b); **no `sudo`**
- [ ] Composition-root path resolution (in `__main__.py` stub): `RADIO_CLI_PATH` env → single hardcoded default constant = **`/usr/local/sbin/radio_cli`** (the stable symlink confirmed in Phase 1) (Q13.3d)
- [ ] `pi-backend/tests/fixtures/fake_radio_cli`: committed extensionless `#!/usr/bin/env python3`, `chmod +x` — **dumb recorder** (Q13.3a/b): append argv to `$FAKE_RADIO_CLI_LOG`; on `-u` print canned `ensemble_scan.json` to stdout; exit `0` unless `$FAKE_RADIO_CLI_RC` set. **Validates nothing**
- [ ] Commit the real `ensemble_scan.json` captured in Phase 1 to `pi-backend/tests/fixtures/`
- [ ] Place fixtures under `pi-backend/tests/` (never under the install-shipped source) so `tools/install` cannot mirror the fake binary onto the Pi (PATH-shadowing hazard, Q13.3c); add a code comment recording this constraint for the Phase 9 install rewrite to honour
- [ ] `tests/test_radio_cli_integration.py`: construct `RadioCli(path=<fixture>)`, drive each method, **assert on the logged argv** (exact flags, order, no stray `sudo`) and on `scan()` returning the fixture JSON; an error-path test sets `FAKE_RADIO_CLI_RC` and asserts the wrapper surfaces non-zero

**Automated Verification**:
- [ ] `fake_radio_cli` is executable and runnable by hand (`./fake_radio_cli -k` exits 0, logs argv)
- [ ] `test_radio_cli_integration` (Integration) passes — argv assertions green, scan returns fixture JSON, error path surfaces non-zero
- [ ] `tools/check pi-backend` passes

---

## Phase 5: Async core — rotary event-source seam + state

**Model: Opus 4.8** (concurrency-heavy; rotary/event-source seam where subtle bugs slip past unit tests — resume-header guidance)

The async heart: rotary input via an injected event-source seam, the pure state
core, and the dispatch layer — no HTTP yet. Regression-test against the Phase-1
rotary baseline (Q12 phase 4, Q13.5 rotary half).

**Tasks**:
- [ ] `sunflower_radio/events.py`: `RotaryEvent(direction=±1)` / `ButtonEvent(pressed)` dataclasses; `EventSource` async protocol yielding normalized events; `EvdevEventSource` decoding raw evdev `RelEvent`/`KeyEvent` (reuse the decode logic from the **Phase-1-restored** `process_events` — the good `4ca7605` copy, not the duplicated broken block); test `FakeEventSource` yields a scripted sequence (Q13.5 Option 1)
- [ ] `sunflower_radio/state.py`: `RadioState` — holds `volume (0–100)`, `station_index`, station list; volume clamp `0–100`; **`0-100`→`0-63` conversion** (Q8b/Q13.2b, conversion lives above the seam); station wraparound; `snapshot() -> {volume, station:{id,name}}` plus an **additive optional advisory** when the persisted station was lost (D10 — "rescan recommended"); **guard the empty-list case** (no `idx % 0` — D10)
- [ ] `sunflower_radio/stations.py`: parse ensemble-scan JSON → `[{id, name, srvid, compid, tune_idx}]` (reuse `read_stations` parse from the restored baseline); keep `srvid/compid/tune_idx` OFF the wire (Q8b)
- [ ] `sunflower_radio/settings.py`: load/save `~/.sunflower-radio.json` — persist the selection as **`ServId` + `Label`** (NOT bare index — D10), plus `volume`; **no I2S keys** (Q9); tolerate an absent file (defaults: volume 25, no selection)
- [ ] **(D10) Selection reconciliation helper** (in `state.py`): resolve a persisted `{ServId, Label}` against the current station list by **(1) ServId → (2) Label → (3) fall back to index 0 + raise the "previous station unavailable" advisory**; reused by `__main__` startup, the scan endpoint (Phase 6), and the Rescan UI (Phase 8). Handle missing/empty list + out-of-range index without crashing
- [ ] `sunflower_radio/dispatch.py`: **decode layer** + **dispatch layer** — event → `RadioState` mutation → correct `RadioCli` call (volume turn → `set_volume`, station turn/button → `tune`); assert on the fake `RadioCli` argv (ties to Phase 4 seam)
- [ ] `__main__.py`: wire `EvdevEventSource` + `RadioState` + `RadioCli`; restore last volume; **reconcile the persisted selection via the D10 helper** (ServId→Label→fallback) before tuning; boot board; apply restored state; if the list is empty/missing, boot into the "no stations — rescan" state instead of crashing; run the async event loop; `SIGTERM`/`SIGINT` → graceful `shutdown()` + save settings (replace old signal handler)
- [ ] Deploy to the Pi and confirm rotary parity with the Phase-1 baseline

**Automated Verification**:
- [ ] `test_state.py` (Unit): `0-100`→`0-63` conversion table parametrized; clamp at 0/100; station wraparound at both ends
- [ ] `test_state.py` (Unit, **D10 reconciliation**): persisted `{ServId, Label}` matches by ServId; falls through to Label when ServId changed; falls back to index 0 + raises the advisory when both changed/removed; empty list + out-of-range index don't crash
- [ ] `test_events.py` (Unit): raw evdev structs → correct normalized `RotaryEvent`/`ButtonEvent`
- [ ] `test_dispatch.py` (Unit): scripted `FakeEventSource` sequence → expected `RadioCli` argv on the fake (volume vs tuner mode, button toggle)
- [ ] `tools/check pi-backend` passes

**Manual Verification** (rotary smoke — un-automatable hardware edge, Q13.5/13.7):
- [ ] On the Pi: **knob rotation changes volume**, **push toggles mode**, **rotation changes station**, **audio plays** — matches the Phase-1 baseline (no regression from the async rewrite)

---

## Phase 6: HTTP API + SSE broadcaster

**Model: Opus 4.8** (SSE fan-out concurrency; server-authoritative convergence — resume-header guidance)

Add the FastAPI layer and the server-authoritative SSE broadcaster in the same
process (D4/D5, D7, D8a). Integration-test from laptop curl (Q12 phase 5).

**Tasks**:
- [ ] `sunflower_radio/broadcaster.py`: subscriber registry of async queues; register/unregister; `publish(snapshot)` fans out one identical `state` payload to **all** subscribers including the initiator (D7 convergence). (Coalesce-to-latest policy added in Phase 10; here a simple bounded queue is fine)
- [ ] Route every mutation (rotary via dispatch, HTTP commands) through one path that updates `RadioState` then calls `broadcaster.publish(snapshot)` — single shape of truth
- [ ] `sunflower_radio/api.py` (FastAPI): `GET /api/state` (snapshot), `GET /api/stations` (cheap, no scan), `POST /api/volume {volume:0-100}` → echoes full state, `POST /api/station {id}` → echoes full state, `POST /api/scan` (async `radio_cli -b D -u -k` → reload list → **reconcile selection via the D10 ServId→Label→fallback helper** → broadcast), `GET /api/events` (SSE via `sse-starlette`)
- [ ] **Structured error model** (Q8b): `{error:{code,message}}` with `400`/`404`/`409`/`503`/`500`; codes like `station_not_found`
- [ ] Mount `StaticFiles` at `/` (serves `web/out/` in prod) while `/api/*` handles the API — same origin, same port (D5/C1). Tolerate missing `web/out/` in dev
- [ ] Run FastAPI + the rotary event loop in one `asyncio` process; ensure a slow `scan()` never blocks rotary or SSE
- [ ] `tools/smoke`: laptop→Pi-over-SSH curl checks — `GET /api/state` valid shape, `POST /api/volume` changes it, `GET /api/stations` non-empty (Q13.7 automated half; satisfies the real-behaviour mandate)

**Automated Verification**:
- [ ] `test_broadcaster.py` (Unit): register N fake subscribers, trigger a mutation, assert all N receive exactly one identical snapshot (D7 fan-out, Layer 1 — Q13.5)
- [ ] `test_api.py` (Integration, FastAPI `TestClient` + fake `RadioCli`): each endpoint returns the documented shape; bad input → `400`; unknown station id → `404` with `station_not_found`; commands echo full state
- [ ] `tools/check pi-backend` passes
- [ ] `tools/smoke` (laptop→Pi over SSH) against the live service passes — `GET /api/state` valid shape, `POST /api/volume` actually changes it, `GET /api/stations` non-empty; exercises real `radio_cli` + board end-to-end (Q13.7 real-behaviour mandate, agent-runnable)

---

## Phase 7: Next.js scaffold

**Model: Sonnet 4.6** (mechanical scaffold)

Stand up the App Router static-export shell and the SSE/api client plumbing
(Q14, D5/C1). Smoke against the Pi (Q12 phase 6).

**Tasks**:
- [ ] `web/` Next.js App Router project; `next.config.js` with `output: 'export'`; `app/layout.tsx` + `app/page.tsx` (`"use client"` as needed)
- [ ] `web/lib/types.ts`: `State`, `Station`, error types mirroring the frozen wire contract (Q8b)
- [ ] `web/lib/api.ts`: typed fetch client for `GET /api/state|stations`, `POST /api/volume|station|scan`; `NEXT_PUBLIC_API_BASE_URL` for `next dev` against the Pi
- [ ] `web/lib/useStateStream.ts`: `EventSource` hook subscribing to `/api/events`, exposing latest `State` + connection status; auto-reconnect (native `EventSource`)
- [ ] `web/tests/`: Vitest + React Testing Library setup (jsdom); a smoke render test of `page.tsx`
- [ ] Build static export and serve it via the Pi's FastAPI; confirm the shell loads from `http://<pi>/`

**Automated Verification**:
- [ ] `npm run build` produces a static `out/` with no SSR/route-handler errors
- [ ] `tools/check web` passes (eslint + tsc + Vitest)

**Manual Verification**:
- [ ] Open `http://192.168.1.106/` — the scaffold page loads and `GET /api/state` data is visible in the UI (live data round-trips through the static export served by the Pi)

---

## Phase 8: Sunflower UI

**Model: Sonnet 4.6** (component build, guarded by harness; SSE-client reconciliation is the trickiest part — escalate to Opus if convergence bugs appear)

Build the single-screen sunflower control panel and wire it to the SSE stream
(Q15a–e). Live state in the browser (Q12 phase 7).

**Tasks**:
- [ ] `components/SunflowerCircle.tsx`: ring of positioned dots (no canvas), color/size encode distance from selected; selected dot highlighted/centered with station `#N — Name`; **tappable dots → immediate `POST /api/station`** (Q15d); animates on SSE change
- [ ] `components/StationStepper.tsx`: prev/next `◀ ▶` → immediate tune (reliable on a dense dial, Q15d)
- [ ] `components/VolumeSlider.tsx`: native `<input type="range">` `0–100`; **debounced commit** on settle/throttle; **SSE reconciliation** moves the slider on knob/other-client change **except while actively dragging**, resume on release (Q15c, D7)
- [ ] `components/RescanButton.tsx` + `components/ScanningOverlay.tsx`: secondary "Rescan" → `POST /api/scan`; **scanning state** disables station+volume + shows overlay; **post-scan reconciliation** reloads list + re-syncs selection via SSE (Q15b2)
- [ ] Theme: yellow/gold accents on dark base; honor `prefers-color-scheme`; retune the dot distance-palette to harmonize on dark (Q15e). No manual toggle
- [ ] `web/tests/`: Vitest for component logic (debounce, drag-vs-reconcile gating, immediate-tune dispatch); `web/tests/e2e/` Playwright — open page, change volume from a second client, assert first client's DOM updates live + reconnect-on-drop (Q13.5 Layer 2, the reserved Playwright tool)

**Automated Verification**:
- [ ] Vitest: volume slider commits debounced (not per-pixel); slider ignores SSE while dragging, reconciles on release; tapping a dot / stepping dispatches `POST /api/station`
- [ ] Playwright e2e: second-client volume change updates the first client's DOM live; reconnect after a dropped stream resyncs via `GET /api/state`
- [ ] `tools/check` (full, incl. Playwright) passes

**Manual Verification** (multi-surface convergence — the project's defining feature):
- [ ] Open the UI on two devices + use the physical knob: a change on any surface (knob, phone, tablet) converges on all others live via SSE
- [ ] Trigger Rescan: overlay shows, controls disable, list reloads after the scan; **audio plays** on the reconciled station
- [ ] Rescan while a station is selected: confirm the selection reconciles to the **same station by identity** even if its list index shifted, or falls back sensibly if that station vanished from the new scan (Q15b2 index-shift handling)

---

## Phase 9: Install & service cutover

**Model: Sonnet 4.6** (deploy scripts + systemd, mechanical)

Make `tools/install` deploy both the Python service and the `web/out/` build, and
atomically swap `dabboard.service` → `sunflower-radio.service` (Q11, Q12.1, Q17).

**Tasks**:
- [ ] Rewrite `tools/install`: `PROJECT="sunflower-radio"`; install `pi-backend/` source + `web/out/` static build; never ship `tests/`; configure rotary overlays in **`/boot/firmware/config.txt`** (modern bookworm), not legacy `/boot/config.txt`
- [ ] New `files/etc/systemd/system/sunflower-radio.service`: `ExecStart` the new entrypoint, **`ExecStop=<radio_cli> -k`** preserved, `TimeoutStopSec=120s`, `Restart=on-failure`, `User=root`, `WantedBy=multi-user.target` (shutdown chain must survive — session notes)
- [ ] Cutover: disable+remove `dabboard.service`, enable `sunflower-radio.service`, atomic swap (no window where the repo and Pi disagree on unit name)
- [ ] `tools/deploy` (rsync build → Pi), `tools/restart` (ssh systemctl restart), `tools/logs` (ssh journalctl -u) — each holds the host `gingerberry@192.168.1.106` in one place (Q17); confirm script names pre-approved (Phase 3)
- [ ] Verify `gpio-shutdown` overlay + GPIO 3 shutdown button still work post-cutover (session notes — preserve)
- [ ] Drop the stale `simple-dab-radio.service`, legacy `/boot/config.txt` notes, and disabled `radio-cli-shutdown.service` per the deferred-cleanup session note

**Automated Verification**:
- [ ] `tools/install` on the Pi completes without error; `systemctl is-enabled sunflower-radio.service` → `enabled`; `dabboard.service` gone
- [ ] `tools/smoke` passes against the freshly-installed service
- [ ] `tools/restart` / `tools/logs` work and require no broad-ssh approval prompt

**Manual Verification** (clean-install acceptance):
- [ ] Fresh `tools/install` + reboot: radio auto-starts, knob works, `http://<pi>/` works, **audio plays**
- [ ] Press the physical **GPIO-3 shutdown button**: orderly shutdown; `radio_cli -k` runs via `ExecStop` (board silenced cleanly)

---

## Phase 10: Polish & backpressure-bounded SSE

**Model: Opus 4.8** (D7a coalesce-to-latest concurrency — resume-header guidance)

Final correctness + resource-safety pass (Q12 phase 8, D7a). Last backend task.

**Tasks**:
- [ ] `broadcaster.py`: implement **coalesce-to-latest** (D7a) — per-client effective buffer size 1; a new snapshot overwrites an unflushed one; disconnect genuinely-dead clients on write timeout (`EventSource` auto-reconnects, `GET /api/state` resyncs → lossless). Bounded memory by construction on the 512 MB Pi
- [ ] Harden the error model end-to-end: UI branches on stable `code`, surfaces `message` for debug; cover `409`/`503` radio-not-ready (board mid-scan/booting)
- [ ] Finalize the theme + dot palette polish; verify `prefers-color-scheme` light/dark both legible
- [ ] Document the SSE broadcaster + coalesce-to-latest policy in `pi-backend/CLAUDE.md` with a root-CLAUDE.md pointer (Q16, D7a)
- [ ] Full end-to-end multi-client convergence + slow-client soak

**Automated Verification**:
- [ ] `test_broadcaster.py` (Unit): a slow subscriber that doesn't drain receives only the **latest** snapshot (intermediate coalesced away); buffer never grows beyond 1
- [ ] `test_broadcaster.py` (Unit): a subscriber past the write timeout is dropped, others unaffected
- [ ] `tools/check` (full) passes; full pytest + Vitest + Playwright green

**Manual Verification** (resource-safety + convergence under real conditions):
- [ ] Background/sleep one client (close laptop lid), keep changing station/volume from the knob for a minute, reopen — the slept client resyncs to current state, no memory growth observed on the Pi (`free -m` stable)
- [ ] Three-surface rapid changes (knob + 2 browsers) all converge with no divergence or stale display

---

## References

- Decision log (source of truth): `docs/decisions.md` (D1–D9, Q8–Q18 — all resolved)
- Static-export rationale: `docs/explanations/static-export.md`
- Agentic-process write-up: `docs/homework.md`
- Current broken entrypoint (revert target): `files/usr/local/sbin/simple-dab-radio.py` (`4ca7605`)
- Reuse — ensemble parse: `files/usr/local/sbin/simple-dab-radio.py:104-128`
- Reuse — rotary decode: `files/usr/local/sbin/simple-dab-radio.py:182-203`
- Current install model: `tools/install` (`files/` → root mirror)
- Current service (rename source): `files/etc/systemd/system/dabboard.service`
- Backpressure article: https://banay.me/dont-waste-your-backpressure/
- Pi target: `ssh gingerberry@192.168.1.106` (`PiZeroTwo`, aarch64, passwordless sudo)
