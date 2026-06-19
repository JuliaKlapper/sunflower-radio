import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SunflowerCircle } from '@/components/SunflowerCircle';
import type { Station } from '@/lib/types';

const STATIONS: Station[] = [
  { id: 0, name: 'Alpha' },
  { id: 1, name: 'Bravo' },
  { id: 2, name: 'Charlie' },
];

describe('SunflowerCircle', () => {
  it('tapping a dot tunes that station immediately', () => {
    const onSelect = vi.fn();
    render(<SunflowerCircle stations={STATIONS} selectedId={0} onSelect={onSelect} />);
    fireEvent.click(screen.getByTestId('dot-2'));
    expect(onSelect).toHaveBeenCalledWith(2);
  });

  it('shows the selected station in the centre as #NN — Name', () => {
    render(<SunflowerCircle stations={STATIONS} selectedId={1} onSelect={vi.fn()} />);
    const center = screen.getByTestId('sunflower-center');
    expect(center).toHaveTextContent('#01');
    expect(center).toHaveTextContent('Bravo');
  });

  it('marks the selected dot pressed', () => {
    render(<SunflowerCircle stations={STATIONS} selectedId={1} onSelect={vi.fn()} />);
    expect(screen.getByTestId('dot-1')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('dot-0')).toHaveAttribute('aria-pressed', 'false');
  });

  it('disables every dot while scanning', () => {
    render(<SunflowerCircle stations={STATIONS} selectedId={0} onSelect={vi.fn()} disabled />);
    expect(screen.getByTestId('dot-1')).toBeDisabled();
  });

  it('renders an empty centre with no stations', () => {
    render(<SunflowerCircle stations={[]} selectedId={null} onSelect={vi.fn()} />);
    expect(screen.getByTestId('sunflower-center')).toHaveTextContent('—');
  });
});
