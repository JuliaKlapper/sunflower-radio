'use client';

import { useEffect, useState } from 'react';
import type { RadioState } from './types';

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

export interface StateStream {
  // Latest server-authoritative state, or null until the first event arrives.
  state: RadioState | null;
  connected: boolean;
}

/**
 * Subscribe to the server-authoritative SSE stream (`GET /api/events`, D7).
 *
 * The server sends the current state immediately on connect and again on every
 * mutation from any surface (knob or another client), so this hook is the single
 * source of truth the UI reconciles against. Native `EventSource` reconnects
 * automatically on a dropped stream; each (re)connect replays the current state,
 * making the client lossless across disconnects.
 */
export function useStateStream(): StateStream {
  const [state, setState] = useState<RadioState | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const source = new EventSource(`${BASE}/api/events`);
    source.addEventListener('open', () => setConnected(true));
    source.addEventListener('error', () => setConnected(false));
    source.addEventListener('state', (event) => {
      setState(JSON.parse((event as MessageEvent).data) as RadioState);
    });
    return () => source.close();
  }, []);

  return { state, connected };
}
