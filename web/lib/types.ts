// The frozen `/api/*` wire contract (Q8b). Volume is 0-100 (the Pi converts to
// the board's raw 0-63 internally); `srvid/compid/tune_idx` stay server-side.

export interface Station {
  id: number;
  name: string;
}

// Shape of `GET /api/state`, every command echo, and every SSE `state` event.
export interface RadioState {
  volume: number;
  station: Station | null;
  // Additive optional advisory (D10): set when the persisted station was lost or
  // no stations are scanned; null when clear.
  advisory: string | null;
}

// Structured error model (Q8b): the UI branches on the stable `code`.
export interface ApiError {
  error: { code: string; message: string };
}
