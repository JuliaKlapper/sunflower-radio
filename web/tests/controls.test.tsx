import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { RescanButton } from '@/components/RescanButton';
import { ScanningOverlay } from '@/components/ScanningOverlay';

describe('RescanButton', () => {
  it('fires onScan when clicked', () => {
    const onScan = vi.fn();
    render(<RescanButton onScan={onScan} />);
    fireEvent.click(screen.getByText(/Rescan/));
    expect(onScan).toHaveBeenCalledTimes(1);
  });

  it('is disabled while scanning', () => {
    render(<RescanButton onScan={vi.fn()} disabled />);
    expect(screen.getByText(/Rescan/).closest('button')).toBeDisabled();
  });
});

describe('ScanningOverlay', () => {
  it('renders nothing when not visible', () => {
    render(<ScanningOverlay visible={false} />);
    expect(screen.queryByTestId('scanning-overlay')).toBeNull();
  });

  it('renders the overlay when visible', () => {
    render(<ScanningOverlay visible />);
    expect(screen.getByTestId('scanning-overlay')).toHaveTextContent('Scanning airwaves');
  });
});
