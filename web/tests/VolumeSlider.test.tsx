import { fireEvent, render, screen } from '@testing-library/react';
import { act } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { VolumeSlider } from '@/components/VolumeSlider';

afterEach(() => {
  vi.useRealTimers();
});

describe('VolumeSlider', () => {
  it('commits debounced — one call with the settled value, not per-pixel', () => {
    vi.useFakeTimers();
    const onCommit = vi.fn();
    render(<VolumeSlider volume={0} onCommit={onCommit} />);
    const slider = screen.getByRole('slider');

    fireEvent.change(slider, { target: { value: '10' } });
    fireEvent.change(slider, { target: { value: '20' } });
    fireEvent.change(slider, { target: { value: '30' } });
    expect(onCommit).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(150);
    });

    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(30);
  });

  it('ignores SSE reconciliation while dragging, then reconciles on release', () => {
    const onCommit = vi.fn();
    const { rerender } = render(<VolumeSlider volume={20} onCommit={onCommit} />);
    const slider = screen.getByRole('slider') as HTMLInputElement;
    expect(slider.value).toBe('20');

    // Start dragging, then a knob/other-client change arrives via the prop.
    fireEvent.pointerDown(slider);
    rerender(<VolumeSlider volume={80} onCommit={onCommit} />);
    expect(slider.value).toBe('20'); // frozen — not yanked mid-drag

    // Release resumes reconciliation to the latest server value.
    fireEvent.pointerUp(slider);
    expect(slider.value).toBe('80');
  });

  it('does not snap back to the pre-drag value on release', () => {
    vi.useFakeTimers();
    const onCommit = vi.fn();
    const { rerender } = render(<VolumeSlider volume={20} onCommit={onCommit} />);
    const slider = screen.getByRole('slider') as HTMLInputElement;

    fireEvent.pointerDown(slider);
    fireEvent.change(slider, { target: { value: '75' } });
    // Release before the server echo arrives (prop still 20).
    fireEvent.pointerUp(slider);
    expect(slider.value).toBe('75'); // keeps the optimistic value, no snap to 20
    expect(onCommit).toHaveBeenCalledWith(75); // flushed immediately on release

    // The echo finally arrives with our committed value — no visible jump.
    rerender(<VolumeSlider volume={75} onCommit={onCommit} />);
    expect(slider.value).toBe('75');
  });
});
