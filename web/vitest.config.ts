import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

const root = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Match the tsconfig `@/*` -> `./*` path alias for component/lib imports.
    alias: { '@': root },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    // Playwright e2e lives under tests/e2e (Phase 8) and is run by its own runner.
    exclude: ['node_modules', 'tests/e2e/**'],
  },
});
