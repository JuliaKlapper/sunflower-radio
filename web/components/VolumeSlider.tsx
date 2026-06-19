'use client';

import { useEffect, useRef, useState } from 'react';

// Commit on settle/throttle rather than per-pixel (Q15c): a turn of the slider
// fires many `change` events, but the Pi only needs the value the user lands on.
const COMMIT_DEBOUNCE_MS = 150;

interface VolumeSliderProps {
  // Server-authoritative volume (0-100) from the SSE stream / command echoes.
  volume: number;
  // Fired (debounced) with the value to push to `POST /api/volume`.
  onCommit: (volume: number) => void;
  disabled?: boolean;
}

/**
 * The volume control. Two jobs that fight each other, reconciled per D7/Q15c:
 *
 *  1. **Commit debounced** — local drags update the thumb immediately but only
 *     commit to the board on settle, so we never fire one HTTP call per pixel.
 *  2. **Reconcile from the server** — a knob turn or another client moves the
 *     thumb live via the `volume` prop, **except while the local user is actively
 *     dragging** (don't yank the control out from under them); reconciliation
 *     resumes on release.
 *
 * The freeze is implemented by only consuming a `volume` change when it actually
 * differs from the last value we adopted (`adopted`) and we're not dragging — so
 * releasing the thumb does NOT snap back to the pre-drag server value, and an
 * external change that arrived mid-drag is applied on release.
 */
export function VolumeSlider({ volume, onCommit, disabled = false }: VolumeSliderProps) {
  const [display, setDisplay] = useState(volume);
  const [dragging, setDragging] = useState(false);
  const adopted = useRef(volume);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pending = useRef<number | null>(null);

  useEffect(() => {
    if (dragging) return; // frozen: ignore server reconciliation while dragging
    if (volume !== adopted.current) {
      adopted.current = volume;
      setDisplay(volume);
    }
  }, [volume, dragging]);

  // Clear any in-flight debounce on unmount.
  useEffect(() => () => clearTimer(timer), []);

  const scheduleCommit = (value: number) => {
    pending.current = value;
    clearTimer(timer);
    timer.current = setTimeout(() => {
      timer.current = null;
      flushPending(pending, onCommit);
    }, COMMIT_DEBOUNCE_MS);
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(event.target.value);
    setDisplay(value);
    scheduleCommit(value);
  };

  const endDrag = () => {
    setDragging(false);
    clearTimer(timer);
    flushPending(pending, onCommit); // commit immediately on release
  };

  return (
    <div className="volume">
      <span className="volume-icon" aria-hidden>
        🔊
      </span>
      <input
        type="range"
        min={0}
        max={100}
        value={display}
        disabled={disabled}
        aria-label="Volume"
        onChange={handleChange}
        onPointerDown={() => setDragging(true)}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
      />
      <span className="volume-value" data-testid="volume-value">
        {display}%
      </span>
    </div>
  );
}

function clearTimer(timer: React.RefObject<ReturnType<typeof setTimeout> | null>): void {
  if (timer.current) {
    clearTimeout(timer.current);
    timer.current = null;
  }
}

function flushPending(
  pending: React.RefObject<number | null>,
  onCommit: (volume: number) => void,
): void {
  if (pending.current !== null) {
    onCommit(pending.current);
    pending.current = null;
  }
}
