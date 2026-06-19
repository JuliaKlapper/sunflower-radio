'use client';

import { useStateStream } from '@/lib/useStateStream';

// Phase-7 scaffold: confirms the live round-trip — the SSE hook subscribes to
// `/api/events`, and the server-authoritative state renders here. The real
// single-screen sunflower control panel (circle, stepper, slider, rescan) is
// built in Phase 8 on top of this plumbing.
export default function Home() {
  const { state, connected } = useStateStream();

  return (
    <main>
      <h1>🌻 Sunflower Radio</h1>
      <p data-testid="connection">{connected ? 'connected' : 'connecting…'}</p>
      {state ? (
        <dl>
          <dt>Volume</dt>
          <dd data-testid="volume">{state.volume}%</dd>
          <dt>Station</dt>
          <dd data-testid="station">{state.station ? state.station.name : '—'}</dd>
          {state.advisory ? <dd data-testid="advisory">{state.advisory}</dd> : null}
        </dl>
      ) : (
        <p>Loading…</p>
      )}
    </main>
  );
}
