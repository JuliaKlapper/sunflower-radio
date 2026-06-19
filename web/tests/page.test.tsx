import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { RadioState } from '@/lib/types';

// Mock the api client and the SSE hook so the page test exercises orchestration
// (list load, immediate-tune dispatch, scanning state) without real fetch/SSE.
const { api, streamRef } = vi.hoisted(() => ({
  api: {
    getStations: vi.fn(),
    scan: vi.fn(),
    setStation: vi.fn(),
    setVolume: vi.fn(),
    ApiRequestError: class ApiRequestError extends Error {},
  },
  streamRef: { current: { state: null as RadioState | null, connected: false } },
}));

vi.mock('@/lib/api', () => api);
vi.mock('@/lib/useStateStream', () => ({ useStateStream: () => streamRef.current }));

import Home from '@/app/page';

const STATIONS = [
  { id: 0, name: 'Alpha' },
  { id: 1, name: 'Bravo' },
];

beforeEach(() => {
  vi.clearAllMocks();
  api.getStations.mockResolvedValue(STATIONS);
  api.scan.mockResolvedValue({ volume: 30, station: STATIONS[0], advisory: null });
  api.setStation.mockResolvedValue({ volume: 30, station: STATIONS[1], advisory: null });
  streamRef.current = { state: null, connected: false };
});

describe('Home', () => {
  it('renders the header and the pre-stream connecting status', async () => {
    render(<Home />);
    expect(await screen.findByText('🌻 Sunflower')).toBeInTheDocument();
    expect(screen.getByTestId('connection')).toHaveTextContent('connecting');
  });

  it('renders the live station and volume from the stream', async () => {
    streamRef.current = {
      state: { volume: 62, station: { id: 1, name: 'Bravo' }, advisory: null },
      connected: true,
    };
    render(<Home />);
    expect(await screen.findByTestId('connection')).toHaveTextContent('live');
    expect(screen.getByTestId('sunflower-center')).toHaveTextContent('Bravo');
    expect(screen.getByTestId('volume-value')).toHaveTextContent('62%');
  });

  it('tapping a dot dispatches an immediate tune', async () => {
    streamRef.current = {
      state: { volume: 30, station: { id: 0, name: 'Alpha' }, advisory: null },
      connected: true,
    };
    render(<Home />);
    fireEvent.click(await screen.findByTestId('dot-1'));
    expect(api.setStation).toHaveBeenCalledWith(1);
  });

  it('Rescan shows the overlay, then reloads the station list', async () => {
    render(<Home />);
    await screen.findByTestId('dot-0'); // initial list loaded
    expect(screen.queryByTestId('scanning-overlay')).toBeNull();

    fireEvent.click(screen.getByText(/Rescan/));
    expect(api.scan).toHaveBeenCalled();
    expect(screen.getByTestId('scanning-overlay')).toBeInTheDocument();

    // Two getStations calls: the initial load + the post-scan reload.
    await waitFor(() => expect(api.getStations).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.queryByTestId('scanning-overlay')).toBeNull());
  });
});
