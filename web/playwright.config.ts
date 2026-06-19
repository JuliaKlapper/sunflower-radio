import { defineConfig, devices } from '@playwright/test';

// Multi-client SSE-convergence + reconnect specs (Q13.5 Layer 2). The webServer
// launches the REAL Python backend against the committed fake radio_cli + the
// built static export, so the browsers exercise the actual uvicorn/SSE fan-out —
// the unit/Vitest layer can only fake the stream. `pretest:e2e` (package.json)
// builds web/out first; the backend serves it same-origin on :8137.
//
// On macOS the rotary task fails its lazy `import evdev` in an isolated asyncio
// task; the HTTP/SSE server is unaffected (that path only runs on the Pi).
const PORT = 8137;
const BASE_URL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: './tests/e2e',
  // One backend, shared state — keep tests serial so they don't fight over it.
  workers: 1,
  fullyParallel: false,
  use: { baseURL: BASE_URL, ...devices['Desktop Chrome'] },
  webServer: {
    command:
      // Absolute RADIO_CLI_PATH: scan() runs the binary with cwd=home, so a
      // relative path would not resolve.
      `cd ../pi-backend && RADIO_CLI_PATH="$(pwd)/tests/fixtures/fake_radio_cli" ` +
      `SUNFLOWER_STATIC_DIR=../web/out SUNFLOWER_PORT=${PORT} ` +
      `uv run python -m sunflower_radio`,
    url: `${BASE_URL}/api/state`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
