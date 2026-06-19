import { defineConfig, devices } from '@playwright/test';

// Scope Playwright to tests/e2e so it never collects the Vitest unit specs under
// tests/. The multi-client SSE-convergence + reconnect specs land here in Phase 8
// (Q13.5 Layer 2); until then this directory is empty.
export default defineConfig({
  testDir: './tests/e2e',
  use: { ...devices['Desktop Chrome'] },
});
