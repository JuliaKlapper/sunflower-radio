# web — CLAUDE.md

The single-screen sunflower control UI: a Next.js App Router app **statically
exported** (`output: 'export'`) and served from `/` by the Pi's FastAPI process.
The full app is scaffolded in Phase 7 and built in Phase 8; this directory
currently holds only the harness config (`package.json`, `tsconfig.json`,
eslint/prettier).

## Toolchain

```bash
npm install             # run from web/ (or: npm --prefix web install)
npm run lint            # eslint (next + typescript rules)
npm run typecheck       # tsc --noEmit
npm run test            # vitest (unit)
npm run test:e2e        # playwright (multi-client SSE convergence)
npm run build           # static export -> out/
```

Until `web/node_modules` exists, `tools/check web` skips the web steps with a
notice — they activate automatically once deps are installed in Phase 7.

## Quality Gate

Same rule as the root: **after editing, run `tools/check web`; loop until green;
never commit until green.** `tools/check --fast` runs eslint + tsc + Vitest unit
tests and **excludes** the Playwright e2e suite (full `tools/check` includes it).

## Architecture (target — Phases 7-8)

- `app/` — `layout.tsx`, `page.tsx` (mostly `"use client"`).
- `components/` — `SunflowerCircle`, `StationStepper`, `VolumeSlider`,
  `RescanButton`, `ScanningOverlay`.
- `lib/` — `api.ts` (typed fetch client), `useStateStream.ts` (`EventSource`
  hook), `types.ts` (mirrors the frozen `/api/*` wire contract).

## Conventions

- Server-authoritative SSE convergence: state flows from `/api/events`; commands
  echo full state. The volume slider debounces commits and **freezes
  reconciliation while actively dragging**, resuming on release.
- Theme: yellow/gold on dark; honor `prefers-color-scheme`, no manual toggle.
