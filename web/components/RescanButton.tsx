'use client';

interface RescanButtonProps {
  // Triggers `POST /api/scan` (a multi-second full ensemble rescan, Q15b2).
  onScan: () => void;
  disabled?: boolean;
}

/** Secondary utility button that kicks off a full ensemble rescan. */
export function RescanButton({ onScan, disabled = false }: RescanButtonProps) {
  return (
    <button type="button" className="rescan" disabled={disabled} onClick={onScan}>
      <span aria-hidden>⟳</span> Rescan
    </button>
  );
}
