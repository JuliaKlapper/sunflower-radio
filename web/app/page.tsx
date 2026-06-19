'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiRequestError, getStations, scan, setStation, setVolume } from '@/lib/api';
import { useStateStream } from '@/lib/useStateStream';
import type { Station } from '@/lib/types';
import { SunflowerCircle } from '@/components/SunflowerCircle';
import { StationStepper } from '@/components/StationStepper';
import { VolumeSlider } from '@/components/VolumeSlider';
import { RescanButton } from '@/components/RescanButton';
import { ScanningOverlay } from '@/components/ScanningOverlay';

// The single-screen sunflower control panel (Q15a-e). The SSE stream is the one
// source of truth for the live state; the station *list* is fetched once and
// again after a rescan (it isn't carried on the state snapshot). Every control
// commits through the typed api client and converges back via the stream (D7).
export default function Home() {
  const { state, connected } = useStateStream();
  const [stations, setStations] = useState<Station[]>([]);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStations()
      .then(setStations)
      .catch(() => {
        // first-load station list is best-effort; the stream still drives state
      });
  }, []);

  const selectedId = state?.station?.id ?? null;
  const volume = state?.volume ?? 0;

  const report = (err: unknown) => {
    setError(err instanceof ApiRequestError ? err.message : 'Request failed');
  };

  const handleSelect = useCallback((id: number) => {
    setError(null);
    setStation(id).catch(report);
  }, []);

  const handleVolume = useCallback((value: number) => {
    setError(null);
    setVolume(value).catch(report);
  }, []);

  const handleScan = useCallback(async () => {
    setScanning(true);
    setError(null);
    try {
      await scan();
      // The list changed: reload it, then the scan echo / SSE reconciles the
      // selection by identity (D10) back into the new list.
      setStations(await getStations());
    } catch (err) {
      report(err);
    } finally {
      setScanning(false);
    }
  }, []);

  return (
    <main className="panel">
      <header className="panel-header">
        <h1>🌻 Sunflower</h1>
        <span
          className={`status ${connected ? 'status-on' : 'status-off'}`}
          data-testid="connection"
        >
          {connected ? 'live' : 'connecting…'}
        </span>
      </header>

      <SunflowerCircle
        stations={stations}
        selectedId={selectedId}
        onSelect={handleSelect}
        disabled={scanning}
      />

      <StationStepper
        stations={stations}
        selectedId={selectedId}
        onSelect={handleSelect}
        disabled={scanning}
      />

      <VolumeSlider volume={volume} onCommit={handleVolume} disabled={scanning} />

      {state?.advisory ? (
        <p className="advisory" data-testid="advisory">
          {state.advisory}
        </p>
      ) : null}
      {error ? (
        <p className="error" data-testid="error">
          {error}
        </p>
      ) : null}

      <div className="panel-footer">
        <RescanButton onScan={handleScan} disabled={scanning} />
      </div>

      <ScanningOverlay visible={scanning} />
    </main>
  );
}
