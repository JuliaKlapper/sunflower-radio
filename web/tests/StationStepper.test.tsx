import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { StationStepper } from '@/components/StationStepper';
import type { Station } from '@/lib/types';

const STATIONS: Station[] = [
  { id: 0, name: 'Alpha' },
  { id: 1, name: 'Bravo' },
  { id: 2, name: 'Charlie' },
];

describe('StationStepper', () => {
  it('steps next to the following station id', () => {
    const onSelect = vi.fn();
    render(<StationStepper stations={STATIONS} selectedId={0} onSelect={onSelect} />);
    fireEvent.click(screen.getByLabelText('Next station'));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it('wraps from the first station to the last on previous', () => {
    const onSelect = vi.fn();
    render(<StationStepper stations={STATIONS} selectedId={0} onSelect={onSelect} />);
    fireEvent.click(screen.getByLabelText('Previous station'));
    expect(onSelect).toHaveBeenCalledWith(2);
  });

  it('wraps from the last station to the first on next', () => {
    const onSelect = vi.fn();
    render(<StationStepper stations={STATIONS} selectedId={2} onSelect={onSelect} />);
    fireEvent.click(screen.getByLabelText('Next station'));
    expect(onSelect).toHaveBeenCalledWith(0);
  });

  it('disables stepping with an empty list', () => {
    const onSelect = vi.fn();
    render(<StationStepper stations={[]} selectedId={null} onSelect={onSelect} />);
    expect(screen.getByLabelText('Next station')).toBeDisabled();
    expect(screen.getByLabelText('Previous station')).toBeDisabled();
  });
});
