// Typed fetch client for the `/api/*` command surface (D8a). Commands echo the
// full state object, so each mutating call resolves to the new RadioState — the
// same shape `GET /api/state` and the SSE stream deliver (one shape of truth).

import type { ApiError, RadioState, Station } from './types';

// Empty base = same origin (the Pi serves both the export and the API). Point
// `next dev` at the Pi by setting NEXT_PUBLIC_API_BASE_URL=http://<pi>.
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

// Carries the server's stable error `code` so callers can branch on it (Q8b).
export class ApiRequestError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = 'ApiRequestError';
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    let code = 'http_error';
    let message = `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as ApiError;
      code = body.error.code;
      message = body.error.message;
    } catch {
      // non-JSON error body — keep the HTTP-status fallback
    }
    throw new ApiRequestError(code, message);
  }
  return (await res.json()) as T;
}

export function getState(): Promise<RadioState> {
  return request<RadioState>('/api/state');
}

export function getStations(): Promise<Station[]> {
  return request<Station[]>('/api/stations');
}

export function setVolume(volume: number): Promise<RadioState> {
  return request<RadioState>('/api/volume', {
    method: 'POST',
    body: JSON.stringify({ volume }),
  });
}

export function setStation(id: number): Promise<RadioState> {
  return request<RadioState>('/api/station', {
    method: 'POST',
    body: JSON.stringify({ id }),
  });
}

export function scan(): Promise<RadioState> {
  return request<RadioState>('/api/scan', { method: 'POST' });
}
