import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Home from '@/app/page';

// jsdom has no EventSource; stub a minimal one that never fires so the page
// renders its pre-event "Loading…" state deterministically.
class MockEventSource {
  readonly url: string;
  constructor(url: string) {
    this.url = url;
  }
  addEventListener(): void {}
  close(): void {}
}

beforeEach(() => {
  vi.stubGlobal('EventSource', MockEventSource);
});

describe('Home', () => {
  it('renders the sunflower title and the pre-stream loading state', () => {
    render(<Home />);
    expect(screen.getByText(/Sunflower Radio/i)).toBeInTheDocument();
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
    expect(screen.getByTestId('connection')).toHaveTextContent('connecting');
  });
});
