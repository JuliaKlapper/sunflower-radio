'use client';

interface ScanningOverlayProps {
  visible: boolean;
}

/**
 * Full-screen overlay shown while a rescan runs (Q15b2): the board reboots and
 * audio is interrupted for several seconds, so the controls are disabled and
 * this covers the panel until the new station list arrives.
 */
export function ScanningOverlay({ visible }: ScanningOverlayProps) {
  if (!visible) return null;

  return (
    <div className="overlay" role="status" aria-live="polite" data-testid="scanning-overlay">
      <div className="overlay-box">
        <p className="overlay-title">Scanning airwaves…</p>
        <div className="overlay-bar">
          <div className="overlay-bar-fill" />
        </div>
        <p className="overlay-note">station + volume disabled</p>
      </div>
    </div>
  );
}
