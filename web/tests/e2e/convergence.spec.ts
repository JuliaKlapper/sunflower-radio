import { test, expect, type Page } from '@playwright/test';

// Server-authoritative SSE convergence (D7): a change on ONE client must appear
// on every other client live via the stream — no polling, no client re-fetch.
// The backend is the real Python service (fake radio_cli); see playwright.config.

async function waitLive(page: Page): Promise<void> {
  await expect(page.getByTestId('connection')).toHaveText('live');
}

// Populate the backend station list so both clients render the dial. A fresh scan
// reconciles the selection to index 0 (no persisted selection guaranteed).
test.beforeEach(async ({ request }) => {
  await request.post('/api/scan');
});

test('a station change in one client converges live on another via SSE', async ({ browser }) => {
  const ctxA = await browser.newContext();
  const ctxB = await browser.newContext();
  const pageA = await ctxA.newPage();
  const pageB = await ctxB.newPage();
  await pageA.goto('/');
  await pageB.goto('/');
  await waitLive(pageA);
  await waitLive(pageB);

  const before = (await pageB.getByTestId('stepper-name').textContent()) ?? '';

  // Change the station on A only (immediate tune via the stepper). A reflects the
  // change through its own SSE stream (not the POST echo), so wait for that first.
  await pageA.getByRole('button', { name: 'Next station' }).click();
  await expect(pageA.getByTestId('stepper-name')).not.toHaveText(before);
  const afterA = (await pageA.getByTestId('stepper-name').textContent()) ?? '';

  // B converges to A's new selection purely via SSE — B never re-fetched.
  await expect(pageB.getByTestId('stepper-name')).toHaveText(afterA);

  await ctxA.close();
  await ctxB.close();
});

test('a volume change in one client converges live, and a reconnect resyncs', async ({
  browser,
}) => {
  const ctxA = await browser.newContext();
  const ctxB = await browser.newContext();
  const pageA = await ctxA.newPage();
  const pageB = await ctxB.newPage();
  await pageA.goto('/');
  await pageB.goto('/');
  await waitLive(pageA);
  await waitLive(pageB);

  // Pick a target distinct from the current volume so the change is observable.
  const cur = await pageA.getByTestId('volume-value').textContent();
  const target = parseInt(cur ?? '0', 10) >= 50 ? '30' : '70';

  // Drag-free set on A's slider → debounced commit → SSE fan-out.
  await pageA.getByLabel('Volume').fill(target);
  await expect(pageB.getByTestId('volume-value')).toHaveText(`${target}%`);

  // Reconnect: a fresh EventSource replays the current state on connect (the
  // equivalent of GET /api/state), so B resyncs after a dropped stream.
  await pageB.reload();
  await waitLive(pageB);
  await expect(pageB.getByTestId('volume-value')).toHaveText(`${target}%`);

  await ctxA.close();
  await ctxB.close();
});
