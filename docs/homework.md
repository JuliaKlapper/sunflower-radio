# Homework — Agentic Coding Process

**Project:** `sunflower-radio` — a DAB+ radio controller for Raspberry Pi
(rewrite: async Python backend + Next.js web UI), built with Claude Code.

**Goal of the exercise:** practise an *agentic* workflow — let the AI agent
research, challenge, and document decisions with me, instead of just
generating code.

## Tools used

- **Claude Code** (Anthropic CLI agent) — main driver.
- **`grill-me` skill** — structured decision interview.
- **`Explore` subagent** — read-only codebase/reference research.
- **AgentVibes (TTS)** — reads the session aloud (macOS `say`, voice "Zoe").
- **Claude Code hooks & permissions** (`.claude/settings.json`) — automation
  + allowlists.
- **Agent memory** — persists my preferences across sessions.
- **Backpressure toolchain** — the automated quality gate the agent loops
  against (stood up in Phase 3). One umbrella script, `tools/check`, fans out
  to:
  - **pi-backend** (Python, run via **uv**): **ruff** (lint + format),
    **mypy** (strict types), **pytest** (+ `pytest-asyncio`) for unit +
    integration tests.
  - **web** (TypeScript): **eslint**, **tsc --noEmit** (types), **Vitest**
    (unit), **Playwright** (e2e — full run only, gated out of `--fast`).
  - **Modes:** `tools/check` (run-all-and-report), `--fast` (lint + types +
    unit, what the hook runs), `--fix` (safe ruff/eslint/prettier auto-fix),
    plus per-component scoping (`tools/check pi-backend|web`).
  - **Enforcement:** a `core.hooksPath` **pre-commit hook** runs
    `tools/check --fast` (report-only); an advisory **`Stop` hook** surfaces
    failures mid-session. `tools/setup` wires the hook once.

---

## How the backpressure toolchain works

`tools/check` is a **thin orchestrator**: it doesn't lint or type-check
anything itself — it just *calls* each tool and aggregates the **PASS/FAIL
result**. The agent never reads ruff/mypy/pytest internals; it only acts on
what `tools/check` reports (the per-step list + the exit code). The scripts
exist precisely so the agent works with the *result*, not the raw machinery —
that is the backpressure signal it loops against.

It is **run-all-and-report**: every step runs even if an earlier one failed, so
one pass surfaces *all* problems at once (exit non-zero if any failed).

**Order the agent-loop runs (`--fast`), cheap-and-broad → slow-and-narrow:**

*pi-backend* (via `uv`): **1.** ruff format `--check` → **2.** ruff check
(lint) → **3.** mypy (strict types) → **4.** pytest (unit + integration).
*web*: **5.** prettier `--check` → **6.** eslint → **7.** tsc `--noEmit` →
**8.** Vitest (unit). The full check appends **9.** Playwright e2e (gated out
of `--fast`). `--fix` prepends the auto-fixers (ruff/eslint then format last).

Format/lint run first because they're the fastest and most common failures;
types next; tests last because they're the slowest. The agent fixes top-down
and re-runs until green.

**Example agent-loop iteration:**

```text
$ tools/check --fast            # agent runs the gate after an edit
▶ pi-backend: ruff format --check   [PASS]
▶ pi-backend: ruff check            [PASS]
▶ pi-backend: mypy                  [FAIL]   ← agent reads only this result
    radio_cli.py:43: Returning Any from function declared to return "dict[...]"
▶ pi-backend: pytest                [PASS]
=== 1 check(s) failed ===
  - pi-backend: mypy

# agent fixes the one reported failure (cast the json.loads result), re-runs:
$ tools/check --fast
=== all checks passed ===        # green → only now is a commit allowed
```

---

## 1. Workflow: brainstorm → grill → decide → log

I did **not** start by writing code. I ran a structured
**decision-making process** first:

1. **`grill-me` skill** — the agent interviews me relentlessly, one
   question at a time, walking the whole design tree. For each question it
   gives a **recommendation + reasoning + alternatives**, then I choose.
2. **Decision log (`docs/decisions.md`)** — every answered question is
   written down as a `DECIDED` entry with the chosen option, the rationale,
   and the *rejected* options (so the "why" survives). A resume header at
   the top lets me pause and continue across sessions.
3. **Pause / resume** — I work in cycles: pause → the agent updates the
   resume state → I come back and continue at the next open question.

This turns design into an explicit, auditable artifact rather than ad-hoc
chat.

## 2. Decisions taken this way (examples)

Worked through ~18 questions, e.g.:

- **Architecture:** one merged async process (rotary + HTTP API + SSE).
- **Frontend:** Next.js App Router, **static export** served by the Pi
  (one daemon on a 512 MB Pi Zero — explained & documented separately in
  `docs/explanations/static-export.md`).
- **Live updates:** Server-Sent Events, server-authoritative convergence;
  backpressure policy = coalesce-to-latest.
- **Testing:** TDD; a `RadioCli` seam + a fake `radio_cli` binary; pytest +
  Vitest + Playwright; on-Pi smoke test for real-hardware behaviour.
- **UI:** keep the "sunflower" circle, single screen, immediate-tune,
  volume slider, scan button, yellow-on-dark theme.
- **Ops:** wrap Pi commands (deploy/restart/logs/smoke) in `tools/` scripts
  and pre-approve only those — auditable, no blanket SSH root access.
- **Backpressure (agentic-coding feedback loop):** automated quality
  verification so the agent self-corrects instead of me hand-typing trivial
  feedback (per *"Don't waste your back pressure"*). Two layers — a tight
  **agent-loop** (`tools/check` runs ruff/mypy/eslint/tsc + unit tests; the
  agent loops until green) plus a **pre-commit gate** (`core.hooksPath` hook
  calling the same `tools/check`) so a broken commit is impossible — "never
  commit right away." Formatting is auto-fixed (`--fix`) so backpressure is
  spent on real bugs, not punctuation; an **advisory `Stop` hook** surfaces
  failures automatically. Stood up *early* (before feature code) so every
  commit is gated. Strong types (mypy/tsc) are treated as the
  highest-value backpressure.

## 3. AgentVibes — hearing the session out loud

I used the **AgentVibes** TTS integration so the agent **reads each
question, recommendation, and explanation aloud** (macOS `say`, voice
"Zoe"), not just on screen. This let me review long design reasoning by
ear. I set a standing preference: *print the text first, then read it
aloud*, in short chunks.

## 4. Configuring the harness (hooks & permissions)

I also customised the Claude Code agent itself:

- **Permissions:** allow-listed the TTS hook so it never prompts.
- **`SessionEnd` hook:** auto-cleans the TTS audio cache on exit (keeps the
  background-music folder) — an *event-triggered* automation, configured in
  `.claude/settings.json`.
- **Agent memory:** saved my working preferences (read-aloud, pause
  routine) so they persist across sessions.
- **GitHub CLI (`gh`):** installed and authenticated it (account
  `JuliaKlapper`, `repo` scope, SSH) so the agent can create the repo and
  open pull requests **automatically** — no manual github.com step. This is
  what lets the planned Phase-1 cutover (`gh repo create … --push`) and the
  PR-based workflow run hands-off. Side benefit: the access check caught
  that my real username is `JuliaKlapper`, not the `klapper-julia` the
  decision log had guessed.

## 5. Next step: decisions → phased plan (`rpi-plan`)

With the decision log complete, the next move is **not** to start coding —
it's to turn `docs/decisions.md` into an actionable, phased implementation
plan using the **`rpi-plan` skill**. This continues the same agentic
discipline: research and structure first, code second.

- **Input:** `docs/decisions.md` (the full `DECIDED` log).
- **Action:** run `rpi-plan` over it — interactively research the codebase,
  then produce a detailed, phase-by-phase plan with automated + manual
  verification steps per phase.
- **Output:** a written plan file I review and approve before any
  implementation (`rpi-implement`) begins.

This keeps the decisions as the source of truth and makes the plan a
separate, reviewable artifact — so execution is gated on an approved plan,
not improvised from chat.

## 6. What this demonstrates

- Using an AI agent as a **design partner** (challenge + justify), not just
  a code generator.
- **Documenting decisions and their rationale** as a first-class artifact.
- **Configuring the agent's environment** (skills, hooks, permissions,
  memory, TTS) to fit my workflow.

**Key artifacts:** `docs/decisions.md` (full decision log),
`docs/explanations/` (plain-language write-ups), `.claude/settings.json`
(hooks/permissions).
