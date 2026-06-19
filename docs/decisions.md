# Design Decisions

Running log of architectural decisions for the Next.js rewrite + Pi-side
HTTP API. Append new entries; keep alternatives and rationale so the
"why" survives.

---

## ▶ Implementation resume state (rpi-implement) — updated 2026-06-19 (Phase 7 pause)

**Plan:** `docs/agents/plans/2026-06-19-sunflower-radio-rewrite.md` (10 phases).

**DONE — Phases 1–7** (all committed; pushed to `origin` + `gitlab`):
- **Phase 1** baseline regression anchor — knob fixed (re-wired to GPIO
  17/27/22; was mis-wired to 18/23/14 via the G341 splitter, NOT a code bug);
  real ensemble fixture captured.
- **Phase 2** repo cutover/restructure (`461e62a`); **Phase 3** backpressure
  scaffold (`tools/check`, pre-commit hook, advisory Stop hook).
- **Phase 4** `RadioCli` async seam + committed `fake_radio_cli` + ensemble
  fixture; **Phase 5** async core — `events`/`state`/`stations`/`settings`/
  `dispatch`/`__main__`, D10 reconciliation, rotary parity verified on the Pi.
- **Phase 6** (`387910c`) HTTP API + SSE broadcaster: `broadcaster.py`,
  `api.py` (6 endpoints, structured `{error:{code,message}}`), single
  Dispatcher mutation path, uvicorn + rotary in one process. 60 pytest green;
  live SSE convergence verified locally against the fake binary.
- **Phase 7** Next.js static-export scaffold: `app/` shell, `lib/`
  (`types`/`api`/`useStateStream`), Vitest smoke test, `output:'export'` build
  → `out/`. Same-origin serving (`/` + `/api/*` on one port) proven locally.

**NEXT — Phase 8 (Sunflower UI):** build the single screen — `SunflowerCircle`
(ring of dots, tappable → immediate tune), `StationStepper`, `VolumeSlider`
(debounced commit; freeze SSE reconciliation while dragging, resume on release —
D7/Q15c), `RescanButton` + `ScanningOverlay`; yellow-on-dark theme; Vitest for
the debounce/drag-gating logic + the Playwright e2e multi-client SSE convergence
suite under `web/tests/e2e/`. After Phase 8 the **full** `tools/check web`
(incl. Playwright) goes green. Model: Sonnet 4.6 (escalate to Opus if SSE-client
convergence bugs appear).

**Deferred to Phase 9 (Pi-dependent, by user 2026-06-19):** `tools/smoke`
against the live service + the `http://<pi>/` browser check. Both need the
backend deps (`fastapi`/`uvicorn`/`sse-starlette`) installed on the Pi, which
folds into the Phase-9 install. Pi probed read-only this session: Python 3.13 /
Debian trixie, `~/sunflower-deploy/` present, `dabboard` stopped — no writes.

**Still uncommitted (intentional):** `files/.../simple-dab-radio.service`
deletion is Phase 9's drop; this resume block lives in `decisions.md`.

---

## How to resume this grilling session

Open Claude Code in this repo. Invoke the `grill-me` skill. Then say:

> Resume the grilling session from `docs/decisions.md`. Pick up at the
> currently-open question. Continue down the open-follow-ups list.

The current open question, all prior decisions, and the remaining
follow-ups are listed below. The Flutter reference app lives at
`/Users/julia.klapper/Projects/own/DABRadio/flutterDABRadio` (read-only
reference — being deprecated, not ported file-for-file).

**Currently on the table:** NOTHING — **all questions resolved.** The
grilling session is COMPLETE; the design tree is fully walked. Next step is
the implementation plan (rpi-plan), not more grilling. **Post-grilling
addendum (2026-06-19, during rpi-plan):** **D10** added — station
persistence & reconciliation robustness (`ServId`→`Label`→fallback), prompted
by a real renamed-station incident. See the D10 block below.

**Next session — model strategy:** run **rpi-plan on the strongest model
(Opus 4.8)** — planning is the highest-leverage, lowest-reversibility step
and has NO automated backpressure catching mistakes. **Instruction for the
plan:** tag EACH phase with a suggested model tier — default
**Sonnet 4.6** for implementation (mechanical, guarded by the Q18
backpressure harness: `tools/check` + pre-commit gate + Stop hook), but
**Opus 4.8** for the concurrency-heavy phases (the async SSE broadcaster +
coalesce-to-latest D7a, and the rotary/event-source seam Q13.5) where
subtle bugs can slip past unit tests. Haiku not suitable for this codebase's
async logic. Then `/model` to switch per phase during rpi-implement. **Q18 FULLY CLOSED —
agentic-coding backpressure:** two layers (agent-loop + pre-commit gate)
documented in CLAUDE.md (Q18.1); stack ruff/mypy/pytest + eslint/prettier/
tsc/vitest (Q18.2); one `tools/check` orchestrator, run-all-and-report
(Q18.3); `core.hooksPath` + committed hook calling `tools/check` (Q18.4);
fast-subset whole-repo gate, no e2e in hook (Q18.5); auto-fix via
`--fix` in agent-loop / report-only hook (Q18.6); advisory code-scoped Stop
hook (Q18.7); early "scaffold" phase after Phase 2 restructure (Q18.8). NB:
this RE-USED the Q18 slot; the *old* Q18 (SSE slow-client backpressure) is
now **D7a DECIDED — coalesce-to-latest**. **Q17 DECIDED:** wrap Pi ops in `tools/` scripts (deploy/restart/
logs/smoke), pre-approve script names in checked-in settings, no broad
raw-ssh. **Q16 DECIDED:** root + per-component CLAUDE.md (root =
cross-cutting only; `pi-backend/` + `web/` component-specific; no overlap).
**Q15 FULLY CLOSED:** (a) hybrid keep
sunflower, (b) single screen / no nav / Notes deleted / Favourites cut,
(b2) scan = secondary Rescan button + overlay + reconciliation, (c)
horizontal volume slider debounced + SSE-reconciled, (d) one-step
immediate-tune live circle + dots + stepper, (e) sunflower yellow-on-dark
theme honoring `prefers-color-scheme`. **Q15(b2) DECIDED:** scan = secondary
"Rescan" button + scanning overlay + post-scan reconciliation.
**Q15(b) DECIDED:** single screen, no nav, Notes deleted, Favourites cut
from v1 (top post-v1 feature). **Q15(a) DECIDED:** Hybrid — keep the sunflower circle + "Sunflower" branding,
build a fresh single-screen panel that ADDS volume + SSE live updates and
DROPS the placeholder tabs (Favourite stub + geolocation Notes); not a
file-for-file port (Flutter lacks volume + live updates; its architecture
doesn't translate). See the D9/Q15 block for the Flutter survey grounding.
**Q14 DECIDED:** App Router (static export supported, future-proof; accept
liberal `"use client"`).
**Q13 (test strategy) FULLY CLOSED:** Q13.1 dual seam,
Q13.2 async 5-method seam, Q13.3 fake binary (Python dumb recorder, static
fixture under `pi-backend/tests/fixtures/`, constructor-arg injection),
Q13.4 pytest+pytest-asyncio / Vitest+Playwright, Q13.5 rotary
injected-source seam + SSE two-layer split, Q13.6 no CI for v1, Q13.7
automated curl smoke (SSH from laptop) + manual knob/audio checklist.
**Q13.3 FULLY CLOSED** this session: (a) language → Python, (b)
contract → dumb recorder (no arg-grammar validation; assertions live in
the integration tests), (c) location → static committed extensionless
`fake_radio_cli` + `ensemble_scan.json` under
`pi-backend/tests/fixtures/`, (d) injection → constructor arg + env
default (Option A). Q13 progress: Q13.1 (dual seam), Q13.2 (async
5-method seam, raw `0–63`), Q13.3 (all four) DECIDED. Q12 (phasing) fully
closed: Q12.1 (service rename stays Phase 8), Q12.2 (git-identity at start
of Phase 1, restructure Phase 2), Q12.3 (keep history / repoint origin).
Resolved so far through Q12 + Q13.1 + Q13.2 + Q13.3.
Closed since last session: Q8b (volume `0–100`, structured errors), Q8c
(DLS deferred), Q8 versioning (unversioned `/api/*`), Q9 (built-in DAC
only, I2S dropped), Q10 (LAN-only, no auth), Q11 (`sunflower-radio`, own
repo).

---

## D1 — Motivation

**Decision:** 50% agentic-coding practice / 50% platform reach
(LAN-controllable web UI for the household radio).

**Implication:** the agentic workflow (brainstorm → plan → TDD → verify)
matters, *and* the end product has to actually work from any browser on
the LAN.

---

## D2 — Pi integration into the agentic loop

**Decision:** combine three models — `(i) + (ii) + (iii)`.

| Model | What | Verdict |
|---|---|---|
| (i) Pi as deploy + verify target via SSH from laptop | Chosen — primary loop |
| (ii) Verification subagent owning deploy+smoke-test | Chosen — defer until (i) is noisy |
| (iii) Hardware-stub split (fake `radio_cli` for local tests) | Chosen — biggest accelerator |
| (iv) Auto-deploy hook on edit | Rejected — removes intent-to-deploy checkpoint |
| (v) VSCode Remote SSH + Claude inside the Pi | Rejected — Pi Zero 2 W is RAM-anemic |
| (vi) Claude Code natively on the Pi | Rejected — 512 MB RAM, unrealistic |

**SSH target:** `ssh gingerberry@192.168.1.106`
**Prerequisite:** key-based SSH login (`ssh-copy-id`) — passwordless sudo
already configured.

---

## D3 — Starting point for the Pi backend rewrite

**Decision:** `(P3)` — reset to last-good commit, deploy, confirm rotary
works, *then* do the architectural rewrite.

| Path | Verdict |
|---|---|
| (P1) Stabilize current broken file, then rewrite | Rejected — debugging code we'll throw away |
| (P2) Skip ahead, rewrite directly with broken file as reference only | Rejected — no working baseline to compare against |
| (P3) `git checkout 4ca7605` to last-good, deploy, then rewrite | Chosen |

**Rationale:** the current local edits (sudo additions, half-commented
I2S, duplicated function bodies) appear to be the cause of the rotary
failure; reverting is one command and restores a working baseline. The
intent of those edits can be re-introduced cleanly in the new design.

---

## D4 — Pi backend architecture

**Decision:** `(B1)` — merge rotary loop and HTTP API into one async
process.

| Option | Verdict |
|---|---|
| (B1) Merge into one async process (`asyncio` + FastAPI + async evdev) | Chosen |
| (B2) Two processes, IPC between rotary daemon and HTTP server | Rejected — more moving parts, extra RAM, harder state sync |
| (B3) HTTP-only, drop rotary | Rejected — physical knob is intentional |
| (B4) Fix the existing broken Flask server in place | Rejected — doesn't fix the two-process race |

**Rationale:**

1. **Correctness:** one process owns `radio_cli` → no race condition.
2. **State sync for free:** rotary events and HTTP handlers mutate the
   same in-memory `Radio` state; pushing knob changes to web via SSE
   becomes ~20 lines.
3. **Pi Zero 2 W RAM:** one process keeps memory low on a 512 MB box.

**Implication:** the existing Flask server in `DABRadio/raspi_flask_server.py`
is reference-only. Its endpoint paths (`raspi/v1/...`) are kept for
client compatibility; the code is discarded.

---

## D5 — Where the Next.js frontend runs in production

**Decision:** `(C1)` — static export, served by the Pi's FastAPI
process.

| Option | Topology | Verdict |
|---|---|---|
| **(C1) Static export served by the Pi** | `next build` on laptop → static `out/` → rsync to Pi → FastAPI serves it from `/` while API lives at `/raspi/v1/*`. Same origin, same port. | **Chosen** |
| (C2) Node-based Next.js on the Pi | A Node process runs `next start` on the Pi alongside the Python API. Reverse-proxy in front. | Rejected — second daemon on 512 MB; gains features unused by a radio UI |
| (C3) Hosted off-Pi (Vercel / Cloudflare / always-on box) | Frontend on Vercel; browser calls back to the Pi via tunnel/public URL. | Rejected — adds CORS, auth, public attack surface for no LAN benefit |

**Why C1:**

- One device, one URL, one daemon. Phone / laptop / tablet all open
  `http://192.168.1.106/`.
- Same origin → no CORS, no auth needed for LAN use.
- Composes with D4: FastAPI mounts `/raspi/v1` for API and
  `StaticFiles` at `/` for the Next.js build. One process, one port.
- Pi Zero 2 W serves static files comfortably.
- Dev DX preserved: `next dev` on the laptop with
  `NEXT_PUBLIC_API_BASE_URL=http://192.168.1.106` for hot-reload work.

**What you give up with C1:**

- No Server Actions, no Next.js route handlers, no middleware,
  no `next/image` Pi-side optimization.
- None of these are relevant for a JSON-API radio client.
- Switching to (C2) later, if a future feature ever needs them, is
  mechanical, not architectural.

**Caveat to know:** in (C1), the FastAPI app is a single point of
failure for *both* the UI and radio control. Acceptable trade-off for a
home appliance; flagged so it's an informed choice.

---

## D6 — Repo strategy

**Decision:** `(R1)` — monorepo, restructure this repo, rename
permitted.

| Option | Verdict |
|---|---|
| (R1) Monorepo — restructure `simple-dab-radio` into `pi-backend/` + `web/` + `tools/` + `docs/`, optional rename | Chosen |
| (R2) Two repos — `simple-dab-radio` for Pi, new repo for Next.js | Rejected — atomic API+client changes become two PRs; doubled context |
| (R3) Monorepo — restructure `DABRadio` instead | Rejected — Flutter platform dirs (`web/`, `android/`, …) cause cleanup and naming collisions |

**Constraints to carry forward:**

- Both the **rotary encoder** *and* the **web UI** are first-class
  control surfaces. The new service must accept inputs from both and
  reflect each other's state changes in real time. (This is the
  motivation for the merged-process design in D4.)

**Proposed name candidates:** `dabberry-station` (matches setup notes)
or `sunflower-radio` (matches Flutter UI theme). Repo name TBD; product
UI name can stay "Sunflower" regardless.

---

## D7 — How the server pushes state changes to the web UI

**Decision:** `(E2)` — Server-Sent Events (SSE) for state push, REST
POSTs for commands. Plus: **server-authoritative broadcast-to-all.**

| Option | Mechanism | Verdict |
|---|---|---|
| (E1) Polling | Client `GET /state` every 1–2 s | Rejected — bandwidth waste; UI lag bounded by interval; knob turn feels sluggish |
| (E2) SSE | Server holds open `text/event-stream`; pushes `state` events on every change. Browser `EventSource`. FastAPI side: `sse-starlette`. | **Chosen** |
| (E3) WebSocket | Bidirectional duplex; both state pushes and commands over one channel | Rejected — bidirectional weight unused since commands are rare REST POSTs; heavier, no `curl` debug |

**Rationale:** traffic is asymmetric — frequent small state pushes out,
occasional commands in. SSE fits that shape with the least machinery,
runs over plain HTTP (no protocol upgrade, no second port), and
`EventSource` gives reconnect-on-drop for free. WebSocket's duplex buys
nothing here. Polling fights the requirement (a knob turn shouldn't wait
up to 2 s to appear elsewhere).

**Convergence model (server-authoritative):** every mutation — rotary OR
HTTP, from any client — updates the single in-memory `Radio` state, then
the server fans out one `state` event to *all* subscribers including the
initiator. Clients reconcile against the server's broadcast rather than
optimistically updating and skipping their own echo. This is what makes
the knob, phone, and tablet never disagree.

**Caveat (escape hatch preserved):** if continuous volume-slider sliding
ever needs per-tick commits without HTTP-per-tick, debounce client-side
first; only add a `/commands` WebSocket later if it actually bites. SSE
doesn't preclude this.

---

## D8 — API contract (in progress)

Old contract (reference, being retired): RPC-style verbs under
`/raspi/v1/` — `GET retrieveRadioStations` (also triggered a full rescan
on every read), `POST setRadioStation` (accepted 4 interchangeable field
names: `station`/`index`/`station_index`/`srvid`), `POST setVolume`,
`GET health`. Errors as `{"error": "<msg>"}`. Old Flutter client
deprecating → free to redesign.

### D8a — Endpoint style, path prefix, scan/list split

**Decision:**

- **Resource-style names**, not verb-style.
- **Drop the `/raspi/v1` prefix; use `/api`.** Nothing depends on the old
  prefix once the Flutter app is retired.
- **Split "read station list" (cheap, no scan) from "scan airwaves"
  (slow, explicit).** The old design glued them together, making every
  list-fetch expensive. Now list-fetch is instant; scan only on demand.
- Prefer simple `POST /api/volume` / `POST /api/station` over
  `PUT /api/state/...` — tiny home-appliance API, simplicity wins.

**Endpoint map:**

| Purpose | Method + path | Cost |
|---|---|---|
| Current volume + station (page load, SSE reconcile) | `GET /api/state` | cheap |
| Station list | `GET /api/stations` | cheap, no scan |
| Re-scan airwaves | `POST /api/scan` | slow, explicit |
| Set volume | `POST /api/volume` | — |
| Set station | `POST /api/station` | — |
| Live update stream (D7 SSE) | `GET /api/events` | long-lived |

**Still open under Q8:** request/response body shapes per endpoint,
error model, versioning policy, station object wire shape.

---

## Active question (resume here)

### Q8b — Body shapes + error model (PROPOSED, awaiting two decisions)

D8a settled the endpoint map. The following shapes were proposed and are
the working recommendation; **two sub-decisions are still awaiting the
user** (see bottom of this block).

**Station object on the wire** (drop old per-station `volume`; it was
never a station property):
```json
{ "id": 0, "name": "BR Klassik" }
```
Internally the Pi still tracks `srvid`/`compid`/`tune_idx` to drive
`radio_cli`; those stay OFF the wire.

**State object** (`GET /api/state`, and the payload of every SSE `state`
event):
```json
{ "volume": 25, "station": { "id": 0, "name": "BR Klassik" } }
```

**Commands** — each echoes the FULL state object back (one "shape of
truth": same shape as `GET /api/state` and the SSE broadcast):
- `POST /api/volume` → body `{ "volume": 25 }` → returns state object
- `POST /api/station` → body `{ "id": 0 }` → returns state object

**Error model** (DECIDED — structured, machine-readable):
```json
{ "error": { "code": "station_not_found", "message": "No station with id 99" } }
```
with standard HTTP status codes: `400` bad input, `404` unknown station
id, `409`/`503` radio not ready, `500` unexpected. The UI branches on the
stable `code`; `message` is human/debug text. Chosen over flat
`{"error":"message"}` because string-matching error text in the UI is
brittle.

**DECIDED:**

1. **Volume range on the wire → `0–100` percentage.** The Pi converts to
   the hardware range internally (`0–63` for the built-in DAC). UI and
   hardware changes don't leak through the API contract. Conversion lives
   in exactly one place (the Pi, per D7 server-authoritative). Chosen over
   raw `0–63` because raw bakes in a built-in-DAC assumption that breaks
   the moment any other audio backend is used. **Rounding note:** 63 < 100
   steps, so adjacent percentages can map to the same `radio_cli -l` value;
   imperceptible for a volume knob.

2. **Error code style → structured `{error:{code,message}}`.** (see
   Error model block above.) **Both Q8b sub-decisions resolved; Q8b
   closed.**

### Q8c — Now-playing DLS text on the wire (DECIDED: deferred to post-v1)

**Decision:** **defer.** v1 state object stays `{ volume, station }` with
station `{ id, name }`. No existing version (Pi script or Flutter app)
ever used live DLS — both only use the static station `Label`. `radio_cli`
DLS support is unverified, and DLS is a broadcaster *push* stream needing
a polling/monitor loop on the Pi. Adding it later is **purely additive**
(`{ volume, station, nowPlaying? }`) — no breaking change, no version
bump — so deferring costs nothing. (Feasibility check added to
Verification follow-ups.)

### Q8 wrap-up — Versioning policy (DECIDED: unversioned `/api/*`)

**Decision:** **stay unversioned** — `/api/state`, `/api/volume`, etc., no
`/v1` segment. The client (static export) and server ship from the same
FastAPI process in one deploy (D5/C1), so version skew is structurally
impossible — there is no independently-deployed consumer to keep
compatible, and the old Flutter client is retired. Versioning only earns
its keep with clients you can't redeploy in lockstep; that condition is
absent. Adding `/api/v2` (or remounting old routes under `/api/v1`) later
is mechanical, so this is not a one-way door. Revisit only if an external
API consumer (e.g. Home Assistant integration) is ever planned.

**Q8 fully closed** (endpoint map D8a + bodies/errors Q8b + DLS Q8c +
versioning). Wire contract is frozen for v1.

### Q10 — Auth / security posture (DECIDED: LAN-only, no auth)

**Decision:** **no auth.** Trust the home LAN. Same-origin single
appliance (D5/C1); worst-case abuse is changing station/volume — no data,
no irreversible action — so a login screen is pure friction for a
non-existent threat. Accepted trade-off: anyone on the home Wi-Fi can
control the radio (that's the feature, not a bug).

**Guardrails (hygiene, not auth) — to document in CLAUDE.md:**
1. FastAPI binds to the LAN interface; **never port-forward** the Pi to
   the public internet.
2. If remote access is ever wanted, do it as a **separate** project via
   **Tailscale or Cloudflare Tunnel** (identity-based access without
   bolting auth onto the appliance). Revisit only for an untrusted-LAN
   scenario (e.g. many guests), where a light shared secret/PIN would
   suffice.

### Q11 — Project name + repo (DECIDED: `sunflower-radio`, own repo)

**Decision:** unify the project's four competing names under one brand:
**`sunflower-radio`** — matches the existing "Sunflower" UI brand (D6),
so repo → systemd service → UI all say the same thing. Apply everywhere:

| Surface | Old | New |
|---|---|---|
| GitHub repo | `bablokb/simple-dab-radio` (fork) | `klapper-julia/sunflower-radio` (own) |
| local dir | `simple-dab-radio` | `sunflower-radio` |
| `tools/install` `PROJECT` | `simple-dab-radio` | `sunflower-radio` |
| systemd service | `dabboard.service` | `sunflower-radio.service` |
| entrypoint | `simple-dab-radio.py` | (rewrite; name TBD in new layout) |
| settings file | `~/.simple-dab-radio.json` | `~/.sunflower-radio.json` |

**Git remote:** create own repo, set as `origin`, **drop the fork link**
to bablokb — the async + FastAPI + Next.js rewrite diverges too far to
remain a fork. (No `upstream` remote kept.)

**Settings migration:** none needed — reverting to `4ca7605` + rewriting
the settings format anyway, so `~/.sunflower-radio.json` regenerates on
first run; persisted last-station/volume is regenerated, not migrated.

### Q12 — Implementation phasing (RESOLVED — all sub-decisions closed)

Refined the log's original 8-step sequence by inserting an explicit
**repo cutover/restructure** phase (was missing; later phases assume the
new monorepo layout). Dependency that fixes the order: confirm the
old-baseline rotary works *on the current flat layout first* (so a
regression can't be blamed on the restructure), then cut over, then build
everything new directly in the final layout so no file moves twice.

**Proposed 9-phase plan:**

| Phase | Work | Verify |
|---|---|---|
| 1. Baseline | ssh-copy-id ✓, passwordless sudo ✓, revert script to `4ca7605`, deploy | **Rotary works** (regression target) |
| 2. Repo cutover *(new)* | Create own `sunflower-radio` repo, restructure → `pi-backend/web/tools/docs`, drop fork, commit baseline in new layout | builds/installs from new layout |
| 3. Hardware stub | Fake `radio_cli` for local dev | local tests run without the Pi |
| 4. Async Pi rewrite | rotary + state, no HTTP yet | regression vs Phase-1 rotary baseline |
| 5. HTTP + SSE | API endpoints + event stream | laptop `curl` integration |
| 6. Next.js scaffold | App Router, static export | smoke against Pi |
| 7. Sunflower UI | UI port + SSE subscription | live state in browser |
| 8. Install + cutover | `tools/install` deploys Python svc + `web/out/`; `dabboard.service` → `sunflower-radio.service` | clean install on Pi |
| 9. Polish | errors, theme, multi-client convergence | end-to-end |

**RESOLVED — cutover timing.** Order of operations:
**(A) git-identity at very start of Phase 1** (create
`klapper-julia/sunflower-radio`, set `origin`, drop fork) → **Phase 1
baseline** (revert `simple-dab-radio.py` to `4ca7605`, deploy, confirm
rotary) lands directly in the new repo's history (regression anchor born
in its final home, nothing to migrate) → **(B) directory restructure in
Phase 2** (`files/...` → `pi-backend/web/tools/docs`), after rotary is
confirmed on the flat layout so a regression can't be blamed on the move.
Restructure once while the codebase is tiny; all new code thereafter
lands in the final layout (no double moves). Rejected: bundling
git-identity into Phase 2 (baseline commit would be made against
bablokb's fork, then migrated — extra step, anchor hash shifts);
restructuring before baseline (can't tell if a baseline misbehave is the
revert or the move).

**Q12.1 — service rename timing (RESOLVED: stays Phase 8).** The systemd
unit rename (`dabboard.service` → `sunflower-radio.service`) is a
deploy-side op only verifiable once `tools/install` emits the new
`.service` file, which isn't reworked until Phase 8. Renaming in Phase 2
would leave the Pi running `dabboard.service` while the repo claims
`sunflower-radio.service` — a worse split than leaving the old unit name
visibly intact. So Phase 2 = files + repo-identity only; the unit swaps
atomically in Phase 8.

**Q12.3 — new-repo history strategy (RESOLVED: keep history / repoint
origin).** Grounded findings: this clone's `origin` points at
**bablokb/simple-dab-radio directly** (not a personal GitHub fork); all
10 commits are authored by `Bernhard Bablok`; `4ca7605` is simultaneously
`HEAD`, `origin/master`, `origin/HEAD`; **the user has zero own commits**
— every change so far (broken edits, `docs/`, `CLAUDE.md`, `.claude/`) is
uncommitted working-tree state; **no LICENSE and no README** exist.
Decision: create empty `klapper-julia/sunflower-radio`,
`git remote set-url origin <new>`, push — keeping the 10 commits.
Ownership is unaffected: (1) repo ownership = the GitHub account it lives
under (fully the user's); (2) no "forked from" banner because it's a
fresh repo pushed to, not a Fork-button fork; (3) commit authorship is
per-commit — bablokb's stay his, every new commit is authored by the
user. Fresh `git init` would only buy vanity "100% mine from commit #1"
history at the cost of misattributing bablokb's original work. No LICENSE
means no legal attribution requirement, but honest provenance + less work
still favor keeping history.

**Corrected Phase-1 baseline mechanics (from the same git inspection):**
`4ca7605` is already `HEAD`, so "revert to last-good" is NOT a
commit-level revert — it's discarding the uncommitted modification to
`files/usr/local/sbin/simple-dab-radio.py` (`git restore <file>`). The
regression anchor is an existing commit, not something to recreate.

**Q12 FULLY CLOSED.**

After Q12: Q13 (tests), Q14 (App Router), Q15 (UI scope),
Q16 (CLAUDE.md restructure), Q17 (pre-approvals), Q18 (agentic-coding
backpressure — automated feedback loops; set up EARLY, document in CLAUDE.md).
[Old Q18 = SSE backpressure, now D7a DECIDED — coalesce-to-latest.]

---

## Q13 — Test strategy (IN PROGRESS — resume at Q13.3)

Grounding facts (verified this session): **zero tests exist anywhere** in
the repo; the only external dependency is `radio_cli`, invoked via
`subprocess.call` in the four/five call sites of `simple-dab-radio.py`.

### Q13.1 — `radio_cli` test seam (DECIDED: dual seam A + B)

**Decision:** use **both** stubbing mechanisms, with **(A) as the
backbone**:

- **(A) Python abstraction seam** — one thin `RadioCli` wrapper class is
  the *only* code that touches `subprocess`. The `Radio` state core
  (volume clamp, station wraparound, `0–100`→`0–63` conversion, SSE
  convergence) depends on an *injected* interface; unit tests inject a
  fake object. Fast, no subprocess, no PATH games. Carries the bulk
  (~90%) of unit tests.
- **(B) Fake `radio_cli` binary** — a real executable used as a fixture
  for a thin **integration** layer that exercises the *actual*
  subprocess + `shlex` + arg-construction path — exactly where the
  current broken file fails (duplicated bodies, stray `sudo`, mangled
  tuner args).

**Rationale:** global CLAUDE.md mandates "mock external deps, test your
own code paths" + "tests must fail if the real impl breaks" → A delivers
that for the logic; D2(iii) called the fake binary "the biggest
accelerator" and the recovered-from failure mode lives in the arg layer
only B exercises. Rejected single-mechanism options: A-only leaves the
subprocess/arg layer untested; B-only makes every pure-logic test pay
subprocess + PATH cost.

### Q13.2 — Seam shape + async (DECIDED: async 5-method, raw 0–63)

**Decision:**

- **Five operations cross the seam:** `boot()`, `shutdown()`,
  `set_volume(raw_0_63)`, `tune(compid, srvid, tune_idx)`,
  `scan() -> ensemble_json`. (Derived from current invocations: `-b D -o
  0` boot, `-k` kill, `-l <0–63>` volume, `-c/-e/-f/-p` tune, `-b D -u
  -k` scan.)
- **(a) Async seam** — methods are `async def` over
  `asyncio.create_subprocess_exec`. D4 is one `asyncio` loop and `scan`
  is slow (multi-second airwave sweep); a blocking scan would freeze
  rotary input *and* every SSE client. Fake object methods are trivially
  `async`; tests use `pytest-asyncio`. Rejected: blocking calls +
  `run_in_executor` (leaks thread-pool concerns into every call site).
- **(b) Seam speaks raw `0–63`**; the `0–100`→`0–63` percentage
  conversion (Q8b) lives in the **state core above the seam**, not inside
  the wrapper. Wrapper stays a dumb faithful translator → conversion is
  unit-tested with the fake object, and the B fixture can assert on the
  real `-l` value.

### Q13.3 — Fake binary contract + location + injection (FULLY CLOSED — (a)(b)(c)(d) all DECIDED)

Four coupled points, all now decided: **(a) language → Python**,
**(b) contract → dumb recorder**, **(c) location → static committed
fixture under `pi-backend/tests/fixtures/`**, **(d) injection →
constructor arg + env default**.

- **(a) Language → Python (DECIDED).** ~10 lines of logic given the (b)
  dumb-recorder decision (read argv → append to `$FAKE_RADIO_CLI_LOG` →
  if `-u` in argv print the canned JSON fixture → exit `$FAKE_RADIO_CLI_RC`;
  no grammar parsing). Chosen on *consistency*, not capability — both
  Python and bash do this trivially now that the fake validates nothing.
  Rationale: (1) whole test stack is pytest (Q13.4), so one language = no
  shell context-switch and the fake can share env-var-name constants with
  the tests instead of duplicating literals across `.sh`/`.py`; (2) the
  canned-JSON path grows gracefully in Python if a test ever needs varied
  or deliberately-malformed output (bash would need heredoc/quoting
  gymnastics — the original "brittle quoting" worry, just deferred);
  (3) `#!/usr/bin/env python3` + `chmod +x`, invoked by path per (d) — no
  portability issue (Mac dev + Pi both have `python3`). Rejected bash: its
  only edge (zero interpreter startup) is negligible across the handful of
  thin seam-B integration tests (~10% of the suite per Q13.1).
- **(b) Contract (DECIDED — dumb recorder, "Option 1").** (1) append each
  invocation's argv to a record file (path from env, e.g.
  `FAKE_RADIO_CLI_LOG`); (2) on `-u` scan, print a canned ensemble JSON
  fixture to stdout; (3) exit `0` by default but honour an env var (e.g.
  `FAKE_RADIO_CLI_RC=3`) to force non-zero return codes for error-path
  tests. Covers the three observable behaviours: side-effect dispatch,
  scan output, exit status. **The fake does NOT validate arg grammar** —
  it is a dumb fixture, not a referee. Arg-grammar correctness (exact flag
  set, order, no stray `sudo`) is asserted in the *integration tests*
  against the logged argv, NOT enforced by the fake.

  *Why Option 1 (dumb recorder) over Option 2 (validating fake):* a
  validating fake's only edge is catching a wrong-argv bug even when a
  test forgets to assert — but TDD (mandated by global CLAUDE.md + the
  test-driven-development skill) means the argv assertion is written
  *first*, red before green, so no test forgets it. A validating fake
  doesn't remove the assertion; it adds a *second* copy of the real
  binary's grammar (in the fixture) that can drift from the assertions —
  doubling grammar maintenance and adding a new failure mode
  (fixture-bug masquerading as code-bug) for zero reduction in assertions
  written. Single source of truth for "correct argv" = the test
  assertions. Concede to Option 2 only without strict TDD or with many
  authors writing tests loosely — neither applies here.
- **(c) Location (DECIDED).**
  `pi-backend/tests/fixtures/fake_radio_cli` (extensionless, static,
  committed, `chmod +x`) + `pi-backend/tests/fixtures/ensemble_scan.json`.
  - Under `tests/` because `tools/install` mirrors `files/` (post-Phase-2:
    deploys `pi-backend/` source) and **never** ships `tests/` — keeps the
    fake binary off the Pi, where a stray fake `radio_cli` would be a real
    hazard (PATH shadowing).
  - **(c1) Extensionless name** (not `fake_radio_cli.py`): it's invoked
    *as a binary* (the `RadioCli` wrapper execs a path via its shebang), so
    the extensionless name + `#!/usr/bin/env python3` + `chmod +x` keeps
    the "it IS the binary stand-in" mental model and discourages
    `import`-ing it.
  - **(c2) Static committed file** (flavour A), not a `tmp_path`-generated
    fixture (flavour B): a committed executable you can run by hand to see
    its behaviour is easier to debug and matches the "real binary fixture"
    intent that is the whole point of seam B over seam A. B's hermeticity
    buys little for read-only test scaffolding.
  - **Dependency:** `ensemble_scan.json` MUST be a real
    `radio_cli -b D -u -k` capture, NOT hand-authored (a hand-authored one
    encodes our *guess* of the format, defeating the fidelity purpose).
    **Capture it on the Pi during Phase 1 baseline** (board booted +
    proven) and commit it then. (Tracked as a Verification follow-up.)

- **(d) Injection (DECIDED — constructor arg + env default, "Option A").**
  The `RadioCli` wrapper takes the binary path as a **constructor
  argument** — pure dependency injection, the class reads no env itself
  and stays a faithful translator. At the **composition root** (service
  startup / `__main__`), the default path is resolved from a
  `RADIO_CLI_PATH` environment variable, falling back to a single
  hardcoded default constant. Tests construct `RadioCli(path=<fixture>)`
  directly and never touch env; the seam-B integration tests point that
  at `pi-backend/tests/fixtures/fake_radio_cli`; ops can override the real
  path via env without a code change.

  *Why A over the alternatives:* (B) settings-file key couples test
  injection to the settings-loading path and is heavier than needed;
  (C) env-only scatters env reads through the code (or forces the wrapper
  to read env, breaking its "dumb translator" property). A keeps the
  class pure and reads env exactly once, at the edge — testable *and*
  ops-overridable. **Bonus:** the single resolved-default constant is the
  one place to settle the open path discrepancy (setup notes say
  `/usr/local/lib/ugreen-dab+/bin/`, old code hardcodes
  `/usr/local/sbin/radio_cli`) — confirm the true path via `which
  radio_cli` on the Pi (Verification follow-up) and set the constant
  accordingly.

### Q13 — still-open sub-questions after Q13.3 (queue within Q13)

- **Q13.4 — Framework picks (DECIDED).**
  - **Python → pytest + `pytest-asyncio`.** The async add-on is forced by
    Q13.2 (the seam is `async def` over `asyncio.create_subprocess_exec`) —
    you can't test the async juggling without it. pytest over stdlib
    `unittest` for fixtures (`tmp_path`/`monkeypatch`/fake-binary-path),
    parametrization (the `0–100`→`0–63` volume table), less boilerplate.
    Rejected `anyio`'s plugin: its only edge is `trio` portability, but D4
    chose `asyncio` + FastAPI (asyncio-native), so it buys nothing.
  - **Next.js → Vitest + React Testing Library NOW; Playwright RESERVED
    for the SSE / multi-client e2e in Q13.5 (Option 2 of 3).** Vitest runs
    in jsdom, which has **no real `EventSource`**, so it can only *mock*
    SSE — the riskiest, most important part of the UI (D7 live updates +
    multi-client convergence). So: Vitest for fast component/logic tests,
    and a real browser (Playwright) for genuinely exercising live updates,
    decided in Q13.5. Rejected: Vitest-only (never truly tests SSE);
    Playwright-as-primary (slow/heavy for the simple logic tests too —
    wrong tool for 90% of cases). Two tools, each on its strength.
- **Q13.5 — Test boundary for the hard parts (IN PROGRESS — rotary half
  DECIDED; SSE half RESUME HERE).**
  - **Rotary loop (DECIDED — injected event-source seam, "Option 1").**
    The raw evdev input becomes an *injected* dependency: an async
    source that yields normalized events (`RotaryEvent(direction=±1)`,
    `ButtonEvent(pressed)`). Production backs it with evdev; tests inject a
    **fake source** that yields a scripted event sequence. Two layers get
    unit-tested above the seam: (1) the **decode layer** (raw evdev
    `RelEvent`/`KeyEvent` → normalized events), fed raw evdev-shaped
    structs; (2) the **dispatch layer** (event → `update_volume()`/
    `update_tuner()` → the right `RadioCli` call), asserted on the fake
    `RadioCli`'s recorded argv (ties to seam B). No `/dev/input`, no
    blocking, no hardware. **Mirrors the `RadioCli` seam** (Q13.1/Q13.3d) —
    one mental model: the only impure edge is injected; everything above is
    unit-testable. *Honest gap:* the real evdev-open+`select` binding is
    NOT unit-tested (replaced by the fake) — unavoidable without hardware,
    and exactly what the **Phase-1 on-Pi rotary smoke test** (regression
    anchor) covers; Q13.7 pins down where that smoke test lives. Rejected
    Option 2 (mock the `evdev` library directly): couples tests to evdev
    internals — the "expose/mock internals" pattern CLAUDE.md steers away
    from.
  - **SSE broadcast (DECIDED — two-layer split, "Option 1").** Two
    distinct properties, tested at two layers:
    - **Layer 1 — fan-out logic (the risky core), in pytest at the
      state-manager level, NOT over HTTP.** The broadcaster holds
      subscribers as an injected/registerable collection of async
      queues/callbacks. A test registers N fake subscribers, triggers a
      mutation via the same path a rotary/HTTP command uses, and asserts
      all N received exactly one identical `state` payload. Fast,
      deterministic, no browser, no running HTTP server — tests the actual
      D7 convergence ("everyone agrees, including the initiator"). Same
      philosophy as the other seams: test logic above the transport.
    - **Layer 2 — real transport (`EventSource` over HTTP), in
      Playwright** (the reserved Q13.4 tool, since jsdom has no real
      `EventSource`). One or two e2e smokes: open the page, change volume
      from a second client, assert the first client's DOM updates live +
      reconnect-on-drop. Smoke-level, not exhaustive.
    - Rejected Option 2 (HTTP-only — fan-out tested solely through real SSE
      connections against the running FastAPI app): slower, flakier
      (long-lived-stream async teardown timing), and tangles convergence
      logic with transport concerns that are perfectly separable.
    - **Q13.5 FULLY CLOSED** (rotary injected-source seam + SSE two-layer
      split).
- **Q13.6 — CI for v1 (DECIDED — no CI; "Option 1").** v1 ships with a
  local `make test` (pytest + vitest), optional `make smoke` for the Pi
  check, and the on-Pi smoke test as the real-behaviour gate. No GitHub
  Actions. Rationale: (1) solo dev on one laptop — CI's main payoff
  (catching cross-contributor / cross-env regressions) doesn't apply; the
  dev IS the gate. (2) The mandated real-behaviour test (rotary + radio on
  the actual Pi) can't run on a cloud runner anyway (no DAB board, no
  `/dev/input`) — CI could only run laptop-side units the dev already runs
  locally. (3) Heavy setup (toolchain pinning, Playwright browsers in CI)
  for little gain. (4) Not a one-way door — wrapping the same `make` target
  in an Actions YAML is ~20 min whenever a collaborator appears or PR
  badges are wanted. Rejected Option 2 (lightweight CI: fast units only —
  buys "never merge red" solo, but still unneeded now) and Option 3 (full
  CI incl. Playwright — most maintenance, least v1 value). Revisit when a
  second contributor joins.
- **Q13.7 — Smoke-test location + real-behaviour mandate (DECIDED —
  "Option 1": automated curl smoke + manual checklist).** The smoke test
  runs against the service **on the Pi** (only place with the real DAB
  board + rotary), split in two:
  - **Automated** — a script **invoked from the laptop over SSH** (per D2
    model (i)) after each deploy, hitting the live service with curl:
    `GET /api/state` returns a valid state shape, `POST /api/volume`
    actually changes it, `GET /api/stations` is non-empty. Exercises the
    **real `radio_cli` + real board end-to-end** → satisfies global
    CLAUDE.md's "at least one test verifies real behaviour" mandate. Likely
    `make smoke`.
  - **Manual** — a short written checklist for the two genuinely
    un-automatable things: **physically turn the knob** (station + volume
    change) and **confirm audio actually plays** from the speaker.
  - Rejected Option 2 (fully manual checklist — no repeatable automated
    real-behaviour gate) and Option 3 (pytest smoke suite running *on* the
    Pi — burdens the RAM-anemic Pi Zero 2 W with the test toolchain and
    still can't turn the knob). Option 1 automates the hardware path
    without a Pi-side framework and honestly carves out knob+audio as
    manual.
  - **Q13.7 closed → Q13 (test strategy) FULLY CLOSED.**

---

## D9 / Q15 — UI scope (IN PROGRESS — (a) DECIDED; sub-questions open)

**Grounding (Flutter reference survey, `DABRadio/flutterDABRadio/lib/`):**
- The **"sunflower circle" is NOT a knob** — it's a ring of colored dots
  (color/size encode distance from the selected station; purely visual)
  with a **horizontal slider underneath** that drives selection. Center
  shows "Station #N — Name". Files: `radio_station_overview.dart`,
  `radio_station_circle.dart`, `utils/getColorForDot.dart`.
- **NO volume control exists in the Flutter UI** — `setVolume` is defined
  in the API layer but never called from any widget. (v1 makes volume a
  first-class `0–100` control per Q8b/Q9 → must be ADDED.)
- **No live updates** — Flutter is fetch-on-load + manual "send". (v1's D7
  SSE knob↔web convergence is brand-new, not in the reference.)
- **3 bottom-nav tabs:** "Radio" (real) · "Favourite" (**empty stub** — 3
  nav buttons, no data/logic) · "Notes" (**geolocation demo** —
  latitude/longitude tracking, unrelated to radio).
- **"Sunflower" theme** = a **pink** Material seed color, default fonts, no
  branding assets. (Name is aspirational, not realized.)
- Architecture: BLoC/Cubit + go_router + get_it + hand-rolled http — none
  of it ports to React; only the *visual design* meaningfully ports.
- Old API contract (`retrieveRadioStations`/`setRadioStation`/`setVolume`,
  `raspi/v1`) already retired by D8.

### Q15(a) — Overall scope (DECIDED — Hybrid, "Option 2")

Keep the **sunflower-circle station selector + "Sunflower" branding** as
the signature visual identity, but build a **fresh single-screen control
panel** around it — NOT a file-for-file port. Rationale: a "faithful port"
can't be faithful (it omits v1's two defining features — volume control +
SSE live convergence — while importing cruft: geolocation, empty
favourites); and the Flutter architecture doesn't translate anyway, so
"port" only applies to the look. The circle is cheap (positioned dots, no
canvas) and is the project's namesake brand (D6/Q11), so it earns its
keep as identity. Rejected Option 1 (faithful port — omits core features,
imports cruft, code doesn't translate) and Option 3 (full redesign —
throws away the recognizable brand for no real gain).

### Q15(b) — Navigation + Favourites (DECIDED — single screen, "Option 1")

**Single screen, NO nav bar; geolocation Notes DELETED; Favourites CUT
from v1** (becomes the leading post-v1 feature — purely additive, no wire
contract change). Rationale: a radio remote is a one-screen appliance
(pick station, set volume, see now-playing) — a bottom nav with one real
tab is just chrome. Favourites is genuinely useful (most DAB stations are
noise; quick access to your 3–4 matters) but adds a data model +
server-authoritative persistence + star UI + favourites/all view —
deferred to keep v1 tight. Rejected Option 2 (build favourites in v1 — best
usability, real scope cost) and Option 3 (keep a 2-view nav — more chrome).

### Q15 — open sub-questions (resume here)

- **Q15(b2) — Station scan/rescan UI (DECIDED — secondary action, "Option
  1").** `POST /api/scan` (D8a) runs `radio_cli -b D -u -k` to (re)generate
  the station list — the ONLY way the station JSON is created/updated. It's
  slow (multi-second airwave sweep), disruptive (board reboots `-u -k`,
  radio can't play during scan), and rewrites the whole list (station
  indices can change → persisted selection may shift). **Decision:**
  integrate on the single screen as a **secondary "Rescan" utility button**
  (visible, not competing with dial/volume), with two required behaviours:
  (1) **scanning state** — progress overlay, station+volume controls
  disabled while the board is busy/audio interrupted; (2) **post-scan
  reconciliation** — UI reloads the new station list, re-syncs the current
  selection (indices may have shifted), SSE fans the new state to all
  clients. Rejected Option 2 (primary scan control — overweights a rare
  action) and Option 3 (hidden in a settings/gear panel — cleaner main
  screen but one tap further from a needed function).
- **Q15(c) — Volume control (DECIDED — horizontal slider, "Option 1").**
  Net-new UI (Flutter had none; v1 makes volume first-class `0–100` per
  Q8b/Q9). A **horizontal slider below the sunflower circle**, native
  `<input type="range">` (free keyboard + a11y), with two behaviours:
  (1) **debounced commits** — drag updates the UI live but only
  `POST /api/volume` on settle/throttle (no HTTP-per-pixel; realises the
  D7 escape-hatch caveat); (2) **SSE reconciliation** — a physical-knob
  change moves the slider via broadcast, EXCEPT while the user is actively
  dragging (don't yank the control; resume reconciling on release) —
  D7 server-authoritative convergence applied to the slider. Rejected
  Option 2 (arc/ring wrapping the dial — thematic but fiddly on touch, poor
  a11y, more work; let the station circle carry the identity) and Option 3
  (+/- step buttons — simplest, no drag tension, but slow for big changes
  and unexpected for volume).
- **Q15(d) — Circle interaction model (DECIDED — one-step immediate tune,
  "Option 1").** The circle is a **live display** (selected dot
  highlighted/centered; animates when the rotary or another client changes
  station via SSE). **Selection = immediate tune:** tap a dot OR use a
  prev/next stepper → instantly `POST /api/station` → server tunes +
  broadcasts → all clients + the circle converge. **No confirm step.**
  Both gestures provided: **tappable dots** (direct when big enough) +
  **prev/next stepper** (reliable one-at-a-time on a dense 40+-station
  dial). **Mirrors the rotary** ("each click tunes") and D7 (UI reconciles
  to the server broadcast). Accepted trade-off: a mis-tap briefly tunes the
  wrong station — same as the physical knob, re-tap fixes instantly.
  Rejected Option 2 (Flutter-style stage-then-confirm "Tune" button — avoids
  mis-taps but clunky, inconsistent with the knob) and Option 3
  (stepper-only — simplest but slow to jump across the list).
- **Q15(e) — Theme/branding (DECIDED — realize sunflower theme, "Option
  1").** Warm **yellow/gold accents on a dark base** as a single v1 theme;
  honor `prefers-color-scheme` (cheap); **defer a manual theme toggle** to
  post-v1. Resolves the name/look mismatch (product = "sunflower-radio" +
  petal-circle motif, but Flutter theme was pink). Dark base suits a
  low-light appliance (kitchen/bedside) and yellow pops on it. The dots'
  **distance-encoding palette** (red→orange→yellow→green = how far from
  current station) is *information*, separate from the brand accent — keep
  it, retuned to harmonize with the dark background. Rejected Option 2
  (keep pink — least effort, contradicts brand) and Option 3 (full
  light+dark+toggle theming — more work, unneeded for a personal
  appliance). **Q15 FULLY CLOSED** (a hybrid, b single-screen, b2 scan,
  c volume slider, d immediate-tune circle, e sunflower theme).

---

## Open follow-ups (queue order, resume in this sequence)

1. ~~**Q7 — Real-time state push protocol.**~~ Resolved → D7 (SSE +
   server-authoritative broadcast).
2. ~~**Q8 — API contract.**~~ Resolved → D8a (endpoint map) + Q8b
   (volume `0–100`, structured errors, station `{id,name}`, commands
   echo full state) + Q8c (DLS deferred) + versioning (unversioned
   `/api/*`). Wire contract frozen for v1.
3. ~~**Q9 — Audio output path.**~~ Resolved → **built-in DAC only; I2S
   dropped for v1.** User has no external I2S DAC/amp wired up and I2S
   buys nothing without one (its only advantage is audio fidelity /
   external amplification, not metadata). Removes the `arecord | aplay`
   subprocess, the `amixer` volume backend, and the second volume range
   entirely. The new service speaks `0–100` on the wire and converts to
   `radio_cli -l 0..63`. Revisit only if dedicated audio hardware is added.
   **Note:** audio path is orthogonal to station metadata / DLS now-playing
   text — that's tracked separately under Q8c below.
4. **Q10 — Auth / security posture.** LAN-only is the working
   assumption. Confirm; if exposed externally is ever wanted, that's a
   separate later project (Tailscale / Cloudflare Tunnel).
5. **Q11 — Repo rename.** `dabberry-station` favoured. Confirm or pick
   another name.
6. **Q12 — Implementation phasing.** Proposed sequence:
   1. Prep: ssh-copy-id done ✓, passwordless sudo done ✓, revert
      `simple-dab-radio.py` to `4ca7605`, deploy, confirm rotary works.
   2. Stand up hardware-stub for local dev (fake `radio_cli`).
   3. Async rewrite of Pi service (rotary + state, no HTTP yet);
      regression-test against rotary baseline.
   4. Add HTTP API + SSE; integration-test from laptop curl.
   5. Scaffold Next.js (App Router, static export); smoke against Pi.
   6. Sunflower UI port + state subscription via SSE.
   7. Extend `tools/install` to deploy both Python service and
      `web/out/` static build. Cut over `dabboard.service` → new
      service name.
   8. Polish (errors, theme, multi-client convergence).
7. **Q13 — Test strategy.** IN PROGRESS — see Q13 block above.
   DECIDED: Q13.1 (dual seam A+B), Q13.2 (async 5-method seam, raw
   `0–63`, conversion above the seam). **Resume at Q13.3** (fake-binary
   contract/location/injection, PROPOSED, awaiting answer). Then Q13.4
   (frameworks), Q13.5 (rotary/SSE test boundary), Q13.6 (CI: likely none
   for v1), Q13.7 (smoke-test location + real-behaviour mandate).
8. **Q14 — App Router vs Pages Router (DECIDED — App Router, "Option 1").**
   Use the App Router (`app/` dir). **Nearly a wash**: App Router's
   headline features (Server Components, server actions, route handlers,
   streaming SSR) are exactly what the D5/C1 **static export** disables, so
   for this client-side SPA the routers are functionally similar. Chosen
   anyway: (1) static export is fully supported (`output: 'export'`) — zero
   loss; (2) modern default — examples/docs/community assume `app/`,
   future-proofing against a later migration. Accepted cost: liberal
   `"use client"` markers (interactive control panel → mostly client
   components). Rejected Pages Router: simpler for a pure static SPA but
   starts a 2026 project on the maintenance-mode paradigm.
9. **Q15 — UI scope (FULLY CLOSED).** (a) Hybrid (keep sunflower circle +
   branding, fresh single-screen panel); (b) single screen, no nav, Notes
   deleted, Favourites cut to post-v1; (b2) station scan = secondary
   "Rescan" button + scanning overlay + post-scan reconciliation; (c)
   horizontal volume slider (debounced + SSE-reconciled); (d) one-step
   immediate-tune live circle + tappable dots + prev/next stepper; (e)
   sunflower yellow-on-dark theme honoring `prefers-color-scheme`, manual
   toggle deferred. See the D9/Q15 block above.
10. **Q16 — CLAUDE.md restructuring (DECIDED — root + per-component,
    "Option 1").** Three files: **root `CLAUDE.md`** = cross-cutting only
    (overall architecture D4, deploy/verify loop D2, frozen wire contract
    D8/Q8b, naming Q11, LAN-only posture Q10, where things live);
    **`pi-backend/CLAUDE.md`** = Python/asyncio, the `RadioCli` seam +
    `radio_cli` flags, the injected event-source seam, the SSE broadcaster,
    pytest + fixtures + fake binary; **`web/CLAUDE.md`** = Next.js App
    Router + static export, the `EventSource`/SSE client, the sunflower UI
    components, Vitest/Playwright, the theme. Leverages Claude Code's
    auto-load-nearest-CLAUDE.md behaviour (subtree-scoped guidance, less
    noise, scales with the monorepo). **Strict rule to prevent drift:**
    root = cross-cutting only, components = component-only, NO overlap;
    cross-link instead of copy. Rejected Option 2 (single root with
    component sections — always loads everything, grows unwieldy) and
    Option 3 (minimal pointer files leaning on `docs/` — indirection costs
    more than it saves; keep substance in the auto-loaded CLAUDE.md files).
11. **Q17 — Pre-approvals (DECIDED — wrap Pi ops in `tools/` scripts,
    approve the scripts, "Option 1").** Create `tools/deploy` (rsync build
    → Pi), `tools/restart` (ssh sudo systemctl restart), `tools/logs` (ssh
    journalctl -u), `tools/smoke` (ssh curl checks — already implied by
    Q13.7). Each script holds the host (`gingerberry@192.168.1.106`) in one
    place. Pre-approve **only the script names** (`Bash(tools/deploy*)`,
    etc.) in the **checked-in `.claude/settings.json`** (host-agnostic).
    **Do NOT** broadly approve raw `ssh <pi> *` — with passwordless sudo on
    the Pi that = unprompted arbitrary root for the session. Benefits:
    auditable bounded surface (unprompted Pi actions == scripts in
    `tools/`); ad-hoc remote commands still prompt once (right friction);
    single source of truth for host config; scripts are wanted anyway for
    the deploy loop; nothing private committed (IP can live in a local
    config / `settings.local.json` if preferred). Rejected Option 2 (broad
    raw `ssh`/`rsync`/`journalctl` wildcards — fastest but unprompted root)
    and Option 3 (no pre-approvals — safest but per-command friction kills
    the loop). The `update-config` / `fewer-permission-prompts` skills can
    help wire the allowlist.
12. **D7a — SSE backpressure policy (DECIDED — coalesce-to-latest,
    "Option 1").** (Formerly the open "Q18"; the Q18 slot is now reused for
    agentic-coding backpressure below. Confirmed settled via homework.md,
    which records "backpressure policy = coalesce-to-latest.") Policy for
    when an SSE subscriber is slow (weak Wi-Fi) or asleep (lid closed /
    phone backgrounded) and its outbound buffer fills — unbounded queues
    grow memory per stalled client, dangerous on the 512 MB Pi Zero 2 W.
    **Key insight:** every SSE event is a **full state snapshot**
    (`{volume, station}`, per Q8b), not a delta — a slow client needs only
    the *latest* state; intermediate events are worthless once superseded.
    **Chosen — coalesce-to-latest / conflation:** per-client buffer of
    effectively size 1; a new event overwrites an unflushed one. Memory
    bounded by construction (one state/client). Disconnect genuinely-dead
    clients on write timeout — `EventSource` auto-reconnects and
    `GET /api/state` resyncs, so dropping is safe/lossless. Rejected:
    (2) bounded FIFO last-N (hoards stale snapshots a client doesn't need),
    (3) disconnect-on-slow-only (churns connections for merely-slow
    clients). **Implementation:** last backend task (Phase 9); documented
    in `pi-backend/CLAUDE.md` (SSE broadcaster, per Q16) with a pointer from
    root CLAUDE.md.

13. **Q18 — Agentic-coding backpressure (IN PROGRESS — resume at Q18.1).**
    Goal: add *automated* quality-feedback loops so the AI agent identifies
    and corrects its own mistakes during a task, rather than the human
    hand-typing trivial feedback (missed import, formatting) — per
    https://banay.me/dont-waste-your-backpressure/. Definition (user):
    "automated feedback mechanisms that help AI agents identify and correct
    mistakes as they work… shift quality verification to automated systems
    that provide immediate, actionable feedback… increase leverage by
    delegating progressively more complex tasks while maintaining
    confidence. Establish a feedback loop. Never commit right away."
    Concretely the user wants: **linting + pre-commit hooks** at minimum.
    Scope spans the polyglot monorepo: `pi-backend/` (Python asyncio) +
    `web/` (Next.js App Router / TypeScript). Builds on already-decided
    tests (Q13: pytest + Vitest + Playwright) and the `tools/`-script
    pre-approval pattern (Q17). Open sub-questions (decision tree):
    - **Q18.1 — enforcement layers (DECIDED — "Option B", two layers).**
      (1) Agent-loop = primary fast feedback (agent runs checks, reads
      errors, fixes, loops until green); (2) pre-commit hook = hard backstop
      so a broken commit is impossible ("never commit right away"). The
      auto-enforcing Claude Code harness hook is NOT adopted now — deferred
      to Q18.7. **The backpressure model + the loop-until-green rule are
      DOCUMENTED in CLAUDE.md** (which file per Q16: root pointer +
      component specifics). Rejected: (A) pre-commit only (feedback arrives
      too late, kills the tight loop) and (C) all-three-now (harness
      automation needs its own cost/noise discussion first).
    - **Q18.2 — check stack (DECIDED).** `pi-backend/`: **ruff** (lint +
      format), **mypy** (types), **pytest + pytest-asyncio** (tests, per
      Q13.4). `web/`: **eslint** (+ `eslint-config-next`), **prettier**
      (format), **tsc --noEmit** (typecheck), **Vitest + Playwright** (tests,
      per Q13.4). Forks resolved: Python types → **mypy** (canonical,
      deterministic, over pyright); TS lint/format → **eslint + prettier**
      (keeps Next-specific rules; Biome rejected — doesn't fully replace
      `eslint-config-next`). Typecheckers (mypy / tsc) are mandatory, not
      optional — strong types are the highest-value backpressure per the
      article.
    - **Q18.3 — orchestration entry point (DECIDED).** One `tools/check`
      script (Q17 `tools/` pattern — pre-approved by name, runs LOCALLY on
      the laptop, not the Pi). Runs the full stack for both components;
      optional arg `tools/check pi-backend` / `tools/check web` scopes it.
      Thin orchestrator: each component owns its runners idiomatically
      (`web/` via `package.json` scripts lint/typecheck/test; `pi-backend/`
      via direct ruff/mypy/pytest or a tiny Makefile). BOTH the agent-loop
      and the pre-commit hook invoke `tools/check` — single source of truth
      for "green." Failure mode: **run-all-and-report** (aggregate every
      failure in one pass, not fail-fast) so the agent fixes everything per
      iteration. CLAUDE.md rule: "after editing run `tools/check`; loop
      until green; never commit until green."
    - **Q18.4 — pre-commit install mechanism (DECIDED — "Option 3",
      `core.hooksPath`).** Commit `tools/git-hooks/pre-commit` (tiny script
      that calls `tools/check`); activate with
      `git config core.hooksPath tools/git-hooks`, wired into `tools/install`
      (or `tools/setup`) as a one-time step. Zero new dependencies,
      version-controlled, reuses the single `tools/check` door — no second
      tool-runner. Rejected: (1) `pre-commit` framework (industry-standard,
      auto-managed tool envs, BUT a parallel runner competing with
      `tools/check` + can drift from our pinned versions) and (2)
      husky+lint-staged (JS-centric; drags node + root `npm install` into a
      polyglot repo). NB naming trap: the rejected tool is literally named
      "pre-commit"; we still use the pre-commit git *stage*.
    - **Q18.5 — pre-commit scope/speed (DECIDED — "Option B", whole-repo).**
      `tools/check` gets two modes: **full** (agent-loop) and a **fast
      subset** (the hook passes a flag). Pre-commit GATE = fast subset:
      ruff + mypy + eslint + `tsc --noEmit` + **unit tests** (pytest +
      Vitest), **excluding Playwright e2e** (slow + flaky → a flaky gate
      gets bypassed with `--no-verify`, defeating it). Playwright e2e lives
      in the **full `tools/check`** the agent runs in its loop before
      declaring done (NOT in any git hook — stays at the two layers from
      Q18.1; no new pre-push layer, avoid over-engineering). Scope =
      **whole-repo**, not changed-files (`tsc`/`mypy` are project-wide; repo
      is small; changed-files filtering was husky/lint-staged's pitch, which
      we rejected). Rejected: (A) full suite incl. e2e at commit
      (slow/flaky → bypassed) and (C) no tests at all (lets broken unit
      tests through).
    - **Q18.6 — auto-fix vs report-only (DECIDED — split).**
      **Agent-loop:** `tools/check --fix` applies all SAFE auto-fixes
      (`ruff format` + `ruff check --fix`, `prettier --write`,
      `eslint --fix`), then re-verifies and reports the rest; agent runs
      `--fix` then loops on what's left. **Pre-commit hook: report-only,
      zero side effects** — pure pass/fail verifier, never mutates/re-stages
      files (avoids committing unseen edits or forcing a double-commit;
      keeps "green" deterministic). Auto-fix is limited to **formatting +
      safe lint fixes only**; risky behavior-changing rewrites are
      *reported*, not applied. Rationale (the article's core point):
      backpressure is a limited resource — auto-fixing the ~formatting noise
      means the checker surfaces only the real bugs, so the agent's
      attention/cycles go to correctness, not punctuation.
    - **Q18.7 — harness enforcement hook (DECIDED — "Option B", advisory).**
      Add a Claude Code **`Stop` hook** (in `.claude/settings.json`) that
      fires when the agent ends a turn: **(1)** quick `git diff` check — if
      no tracked code changed (pure chat/planning turn), no-op instantly;
      **(2)** else run `tools/check --fast` and **print** the result so the
      agent sees failures automatically — **non-blocking** (a nudge, not a
      wall). Rationale: the pre-commit gate (Q18.4) already makes broken
      commits impossible, so the harness hook's job is only to tighten the
      loop *earlier*, not to be a safety net. Rejected: (A) no hook (relies
      purely on agent discipline) and (C) hard-blocking Stop hook (strongest
      but can TRAP the agent on flaky/env-dependent checks and prevents
      intentional mid-task pauses to ask the user). **Upgrade path:** B→C
      later if the agent is observed coasting up to the commit gate red.
      (Fits the homework "configure the harness" theme: hooks + permissions.)
    - **Q18.8 — phasing (DECIDED — "Option A", early scaffold).** A
      dedicated **"backpressure scaffold" phase right after the Phase 2
      monorepo restructure, before any feature code** — so every feature
      commit is gated from the start. Sets up: ruff/mypy/eslint/prettier/tsc
      configs, `tools/check` (+ `--fix` / `--fast`), the `core.hooksPath`
      pre-commit hook + install step (Q18.4), the advisory Stop hook
      (Q18.7), and the CLAUDE.md docs. Constraint: can't precede the
      skeleton's existence (folders appear at Phase 2). Caveats: Playwright
      e2e cases are added as `web/` grows (harness exists early, tests
      accrue); typecheck/lint strictness starts reasonable and tightens.
      Rejected: (B) incremental (earliest/most-foundational commits land
      ungated) and (C) last (defeats the purpose — build blind, then drown
      in violations; this is the OPPOSITE of the old SSE-Q18 "do last").

    **Q18 FULLY CLOSED.** All sub-questions (Q18.1–Q18.8) resolved. This was
    the final open question in the grilling session — NO open questions
    remain.

---

## D10 — Station persistence & reconciliation robustness (DECIDED during rpi-plan, 2026-06-19)

**Trigger (real-world incident):** a DAB broadcaster **renamed/moved a station**;
the persisted selection no longer matched the air → silence; the radio's own UI
suggested a rescan. A read-only probe of the Pi during planning confirmed the
mechanics: `~/.simple-dab-radio.json` is **absent** (the service boots to the
default **station index 0**), `stations.json` is **stale** (Feb 2 capture), and
each service exposes a numeric **`ServId`** + a **`Label`** — **both
broadcaster-mutable**. This case is the proof that name-only matching is fragile.

**Decision:**

- **Persist the selected station internally as `ServId` + `Label`** (NOT the bare
  positional index the old code used). The wire contract (Q8b) is **unchanged**:
  the web `station.id` stays positional/ephemeral for live use; persistence is an
  internal concern that never reaches the wire.
- **On startup AND on post-scan reconciliation (Q15b2), resolve the selection by:
  (1) match `ServId`; (2) else match `Label`; (3) else fall back to index 0 and
  flag "previous station unavailable / rescan recommended"** in state. The
  advisory is an **additive optional field** on the state object (consistent with
  Q8c's additive-only philosophy — no contract break, no version bump), surfaced
  over SSE to the UI. **Never crash, never silently tune a stale/garbage service.**
- **Startup robustness:** handle a **missing/empty station list** and an
  **out-of-range persisted index** (no `idx % 0` crash); boot into a
  "no stations — rescan" state rather than failing. The Rescan path is the
  recovery mechanism.

**Rejected:** Label-primary (broadcaster renames break it — exactly this
incident); positional-index-only (status-quo weakness — silently switches station
on any rescan reorder).

**Clarification (2026-06-19) — "out of range" vs "station gone":** because the
selection is restored by `ServId`/`Label` lookup (then the index is *recomputed*),
a stale **raw index is never restored** — the classic "index out of range" case is
designed out (and the live rotary index stays valid via `% len` wraparound). The
only real failure is **station-not-found**, whose fallback is **first station
(index 0) + advisory**. Caveat acknowledged: if the station vanished because the
*whole list is stale*, index 0 may also be silent — the advisory + Rescan is the
true recovery; auto-tuning index 0 is deliberately just best-effort "play something
so a headless boot isn't dead-silent." **Rejected for v1** (kept simple): the
"walk to the first *tunable* station" escalation (try index 0 → on tune-failure
step through the list → else "no signal") — deferred to **post-v1, and gated on
the Phase-1 probe** of whether `radio_cli` even reports tune failures. **Rejected:**
don't-auto-tune / silent "pick a station" state — wrong for a radio appliance on a
headless/knob-only boot.

**Implementation:** state core + `__main__` startup (plan Phase 5); the SAME
`ServId`→`Label`→fallback key is reused by `POST /api/scan` reconciliation (Phase
6) and the Rescan UI (Phase 8, Q15b2). New verification follow-up below tracks the
`radio_cli` stale-tune return-code question.

---

## Verification follow-ups (research, not decisions)

- **(D10) Confirm whether `radio_cli` tune (`-c -e -f -p`) returns a non-zero exit
  code when the target `ServId` no longer exists on air, or just produces silence.
  If it errors, the service can auto-detect a stale selection and raise the
  "rescan recommended" flag without waiting for the user. Probe in Phase 1 (do NOT
  probe while audio matters — it interrupts playback).**
- Confirm `which radio_cli` on the Pi — setup notes say
  `/usr/local/lib/ugreen-dab+/bin/`, project code hardcodes
  `/usr/local/sbin/radio_cli`. Resolve before rewrite.
- Firmware boot (`sudo radio_cli --boot=FIRMWARE`) is a one-time
  stateful prerequisite — decide whether the new service idempotently
  handles a not-yet-firmware-loaded board.
- Inspect the current local `simple-dab-radio.py` — file appears to be a
  concatenated/duplicated paste; understand what was actually intended
  before reverting (intent might be worth re-applying in the new design).
- **(Q13.3c) Capture `ensemble_scan.json` from a real
  `radio_cli -b D -u -k` run on the Pi during Phase 1 baseline** (board
  booted + proven working) and commit it to
  `pi-backend/tests/fixtures/`. Must NOT be hand-authored — the fake
  binary's fidelity depends on a real capture.
- (Q8c) Confirm whether `radio_cli` can report live DLS / dynamic-label
  now-playing text (and whether one-shot or stream) — only relevant if
  the deferred now-playing feature is picked up post-v1.
- The `radio.stop()` path references `self._i2s_pid`, but
  `read_settings` only sets it on the I2S branch — non-I2S code paths
  may hit `AttributeError` on shutdown. Worth fixing or designing
  around in the rewrite.
- **Q12.3 grounding correction:** Q12.3 states "no LICENSE and no README
  exist." Both `LICENSE` and `Readme.md` ARE git-tracked (confirmed via
  `git ls-files`). Decision (keep history) is unaffected, but the "no
  LICENSE → no legal attribution requirement" sub-rationale is wrong.
  **Check what that LICENSE actually is before dropping the fork link**
  to bablokb (Q11) — it may carry attribution terms.

---

## Session notes

- The Flask server in `DABRadio/raspi_flask_server.py` has never been
  deployed to the Pi — only `dabboard.service` running
  `simple-dab-radio.py` runs there. The Flask code is reference-only;
  do not migrate from it.
- Pi reports `hostname=PiZeroTwo`, arch `aarch64` (64-bit).
- SSH key auth confirmed working non-interactively from the laptop
  using `~/.ssh/id_ed25519` (`juli-klapper@web.de` identity).
- Passwordless sudo already configured on the Pi.

### Shutdown chain (verified, must be preserved by the rewrite)

- **Physical shutdown button:** wired to GPIO 3 (physical pin 5) + GND.
  Configured by a single line in `/boot/firmware/config.txt`:
  `dtoverlay=gpio-shutdown`. Defaults (active-low, internal pull-up,
  100 ms debounce, GPIO 3) suffice — no parameters. Kernel handles
  detection; sends signal to PID 1, systemd initiates orderly
  shutdown. GPIO 3 is also the only pin that can wake the Pi from
  halt (useful for "press to power on" if ever added).
- **Radio kill on shutdown:** handled by `dabboard.service`'s
  `ExecStop=/usr/local/sbin/radio_cli -k` (with `TimeoutStopSec=120s`).
  systemd guarantees `ExecStop` runs before the service is considered
  stopped, which happens before the final shutdown targets — this is
  the standard, reliable pattern.
- **`radio-cli-shutdown.service` exists but is `disabled`.** It is
  redundant with `dabboard.service`'s `ExecStop` and dormant in the
  current setup. Even if enabled, its `[Install]` section uses only
  `WantedBy=poweroff.target` etc. without `Before=shutdown.target`,
  so ordering is not strictly guaranteed. Leaving disabled as-is is
  the right call. The new unified service must keep an equivalent
  `ExecStop=radio_cli -k` directive.
- **Cleanup deferred (not blocking):** `simple-dab-radio.service`
  (bablokb's original, disabled) and stale `/boot/config.txt` (modern
  bookworm only reads `/boot/firmware/config.txt`). Address as part of
  the rewrite, not before.

### Phase 1 research findings (2026-06-19, on-Pi, `radio_cli_v3.2.1`)

- **Firmware boot is NOT a separate one-time stateful step.** In
  `radio_cli v3.2.1`, `-b/--boot=FIRMWARE` *is* the firmware load:
  `-b D` loads the DAB firmware **and** boots the Si468x in one call
  ("Boot up successful" → "Running with DAB firmware"). The Si468x
  loads firmware from the Pi on every `-b`, so the call is idempotent
  and safe to run on every service start. `dabboard.service`'s
  `ExecStartPre=… --boot=FIRMWARE` line is **commented out** and was
  redundant/misconceived (`FIRMWARE` is the metavar, not a literal
  arg). **Phase 5/9 design:** `__main__` boot just runs `-b D -o 0` on
  start; no special pre-step, no firmware-state detection needed.
- **(D10) Tune to a stale/vanished `ServId` exits `0` — NOT non-zero.**
  Probe: booted, tuned valid `Dlf` (`-c 10 -e 53776 -f 2 -p`) → exit 0,
  "Tuned. Playing service: 53776". Then tuned a bogus
  `-c 10 -e 99999 -f 2 -p` → **exit 0** but stdout "Tuned. Playing
  service: 99999 / **Could not start service**". So the service
  **cannot** rely on tune exit codes to detect a stale selection. It
  **must** reconcile the persisted `{ServId, Label}` against the fresh
  station list via the D10 helper (ServId→Label→fallback) *before*
  tuning. Secondary signal available if wanted: `RadioCli.tune` can
  scan stdout for "Could not start service" / absence of "Playing
  service:" to raise the "rescan recommended" advisory.
- **Ensemble-scan format confirmed.** `-u/--full_scan` does a full
  European sweep (multi-minute, writes `full_scan.json`) — this is the
  slow scan the plan flags as needing `async`. The live
  `/root/stations.json` is exactly that full-scan output (41 ensembles,
  5 valid, 60 audio services) in the `ensembleList` shape
  `read_stations` parses; captured verbatim to
  `pi-backend/tests/fixtures/ensemble_scan.json` (real, non-hand-authored).

### ⚠️ CRITICAL Phase 1 finding — the rotary knob has NEVER worked (hardware)

- **The rotary encoder + push button produce NO input events at the
  kernel level.** Diagnosed on-Pi (2026-06-19) after the user reported
  "knob does nothing / never worked":
  - Drivers probe fine: `rotary-encoder rotary@11: gray` → `input4`;
    `button@16` → `input0` (KEY_ENTER). Overlays present in
    `/boot/firmware/config.txt`: `rotary-encoder,pin_a=17,pin_b=27` and
    `gpio-key,gpio=22,keycode=28`.
  - Raw `evdev` monitor on ALL input devices, **60 s of continuous
    operation → 0 events** (heartbeat-confirmed alive).
  - **Decisive:** `/proc/interrupts` edge counters for GPIO 17, 27, 22
    are **flat (1 each) before and after 20 s of operation** — zero
    electrical edges reach the SoC. Pins read `ip | hi` (idle high,
    pull-ups present) but never toggle.
- **Conclusion:** encoder/button are **not electrically connected to
  GPIO 17/27/22** (disconnected, common-not-grounded, or wired to other
  pins). This is a **wiring/hardware problem, not a software bug** — the
  old Python never received events. The plan's **Phase 1 "restore the
  last-good working-knob baseline" premise is therefore invalid**: there
  is no working-knob state to anchor to.
- **Audio path is fine:** analog `-o 0` out of the board plays correctly
  (user confirmed once speaker powered on + volume raised); `radio_cli`
  boot/tune/volume all work. Only the **knob input** is dead.
- **Implications for the rewrite:** the new `EvdevEventSource` reuses the
  same overlays/pins and will ALSO see nothing until the wiring is
  fixed. The **web UI is independent** of the knob and will work
  regardless. Knob bring-up is now a hardware task (verify which GPIOs
  the encoder/common/button are actually wired to; `gpiomon` available
  on the Pi to scan other pins).

### Root cause located — knob wired to WRONG pins (gpiomon scan, 2026-06-19)

- Scanned all free GPIOs with `gpiomon` while the user operated the knob.
  **Actual physical wiring vs. what `config.txt` declares:**

  | Function    | Physically wired | `config.txt` overlay declares | OK? |
  |-------------|------------------|-------------------------------|-----|
  | Rotary A/B  | **GPIO 18 + 23** | `rotary-encoder,pin_a=17,pin_b=27` | ❌ |
  | Push button | **GPIO 14**      | `gpio-key,gpio=22`            | ❌ |

  Encoder = clean quadrature edges on 18 & 23; button = a mechanical
  bounce cluster (~7 ms/transition, not UART framing) on 14.
- **Fix = `config.txt`, not a rewire** for the encoder:
  `dtoverlay=rotary-encoder,pin_a=18,pin_b=23,relative_axis=1`
  (swap a/b if direction is inverted). Pins 18/23 are otherwise free → no
  conflict.
- **Button conflict:** GPIO 14 is **UART TXD**. `cmdline.txt` has
  `console=serial0,115200` and `serial-getty@ttyS0` is **active** → the
  mini-UART owns GPIO 14/15 in normal operation. A `gpio-key` on GPIO 14
  conflicts with the serial console. Resolution needs a choice:
  (a) move the button wire to a truly-free GPIO (e.g. 16/24/25/26), or
  (b) disable the serial console (drop `console=serial0` from
  `cmdline.txt` + disable `serial-getty@ttyS0`; SSH is the real access
  path anyway) to free GPIO 14.
- **RESOLVED (2026-06-19): re-wired the knob to 17/27/22** (the pins
  `config.txt` already expects), powering the Pi off first. The Geekworm
  **G341** is a passive 1:2 splitter (standard 1:1 pinout, confirmed via
  Geekworm wiki + the native-GPIO edges), so the standard 40-pin matrix
  applies to its headers. Post-rewire verification: raw `evdev` shows
  `rotary@11` REL_X `±1` (right=+1, natural direction → no CLK/DT swap)
  and `button@16` KEY_ENTER press/release; full functional test passed
  (volume audible, mode toggle, station change, audio).
- **Plan impact (final):** Phase 9 `config.txt` rotary overlay **keeps
  the existing `pin_a=17,pin_b=27` + button `gpio=22`** — the hardware
  now matches it. No `config.txt` / `cmdline.txt` change was made; the
  serial console on GPIO 14/15 is untouched.
