'use client';

import type { Station } from '@/lib/types';

interface StationStepperProps {
  stations: Station[];
  selectedId: number | null;
  // Stepping tunes the neighbour immediately — reliable on a dense dial (Q15d).
  onSelect: (id: number) => void;
  disabled?: boolean;
}

/**
 * Prev/next stepper around the selected station. Wraps at both ends client-side
 * (the backend 404s an out-of-range id; the wire id is the positional index, so
 * `(index + dir) mod n` is the neighbouring station's id).
 */
export function StationStepper({
  stations,
  selectedId,
  onSelect,
  disabled = false,
}: StationStepperProps) {
  const count = stations.length;
  const index = stations.findIndex((s) => s.id === selectedId);
  const current = index >= 0 ? stations[index] : null;

  const step = (direction: 1 | -1) => {
    if (count === 0) return;
    const base = index < 0 ? 0 : index;
    const next = (base + direction + count) % count;
    onSelect(stations[next].id);
  };

  const stepDisabled = disabled || count === 0;

  return (
    <div className="stepper">
      <button
        type="button"
        className="stepper-btn"
        aria-label="Previous station"
        disabled={stepDisabled}
        onClick={() => step(-1)}
      >
        ◀
      </button>
      <span className="stepper-name" data-testid="stepper-name">
        {current ? current.name : '—'}
      </span>
      <button
        type="button"
        className="stepper-btn"
        aria-label="Next station"
        disabled={stepDisabled}
        onClick={() => step(1)}
      >
        ▶
      </button>
    </div>
  );
}
