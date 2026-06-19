'use client';

import type { CSSProperties } from 'react';
import type { Station } from '@/lib/types';

interface SunflowerCircleProps {
  stations: Station[];
  selectedId: number | null;
  // Tapping a dot tunes that station immediately (Q15d).
  onSelect: (id: number) => void;
  disabled?: boolean;
}

// Ring radius and dot scaling, expressed as percentages of the square container
// so the layout is purely CSS-driven (no canvas, Q15a).
const RING_RADIUS = 42;

/**
 * The sunflower dial: a ring of tappable dots around the selected station, shown
 * large in the centre as `#NN — Name`. Each dot's hue and size encode its
 * circular distance from the selection (near = warm/green, far = cool/red), so
 * the whole dial reads as a petal spread that animates as the selection moves.
 */
export function SunflowerCircle({
  stations,
  selectedId,
  onSelect,
  disabled = false,
}: SunflowerCircleProps) {
  const count = stations.length;
  const selectedIndex = stations.findIndex((s) => s.id === selectedId);
  const selected = selectedIndex >= 0 ? stations[selectedIndex] : null;
  const maxDistance = Math.max(1, Math.floor(count / 2));

  return (
    <div className="sunflower" data-testid="sunflower">
      <div className="sunflower-ring">
        {stations.map((station, index) => {
          const angle = (index / Math.max(count, 1)) * 2 * Math.PI - Math.PI / 2;
          const x = 50 + RING_RADIUS * Math.cos(angle);
          const y = 50 + RING_RADIUS * Math.sin(angle);
          const distance = selectedIndex < 0 ? 0 : circularDistance(index, selectedIndex, count);
          const t = distance / maxDistance; // 0 = selected, 1 = farthest
          const isSelected = station.id === selectedId;

          const style: CSSProperties = {
            left: `${x}%`,
            top: `${y}%`,
            // 120° (green, near) → 0° (red, far); selected dot uses the accent.
            ['--dot-hue' as string]: `${Math.round(120 - 120 * t)}`,
            ['--dot-scale' as string]: `${isSelected ? 1.6 : 1 - 0.4 * t}`,
          };

          return (
            <button
              key={station.id}
              type="button"
              className={`dot${isSelected ? ' dot-selected' : ''}`}
              data-testid={`dot-${station.id}`}
              aria-label={`Tune ${station.name}`}
              aria-pressed={isSelected}
              disabled={disabled}
              style={style}
              onClick={() => onSelect(station.id)}
            />
          );
        })}
      </div>

      <div className="sunflower-center" data-testid="sunflower-center">
        {selected ? (
          <>
            <span className="station-number">#{String(selected.id).padStart(2, '0')}</span>
            <span className="station-name">{selected.name}</span>
          </>
        ) : (
          <span className="station-name station-name-empty">—</span>
        )}
      </div>
    </div>
  );
}

// Shortest hop count between two indices around the ring.
function circularDistance(a: number, b: number, count: number): number {
  const direct = Math.abs(a - b);
  return Math.min(direct, count - direct);
}
