import type { NextConfig } from 'next';

// Static export (D5/C1): `next build` emits a fully static `out/` that the Pi's
// FastAPI process serves from `/` (no Node server on the Pi). This disables
// SSR/route handlers/streaming — the single sunflower screen is client-rendered
// and talks to `/api/*` over fetch + SSE.
const nextConfig: NextConfig = {
  output: 'export',
};

export default nextConfig;
