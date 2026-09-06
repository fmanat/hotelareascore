// @ts-check
import { defineConfig } from 'astro/config';

// Static-first per docs/adr/001 — no adapter, no SSR. Phase 2 has no live
// backend: every page is prerendered from the JSON exported by
// `make webdata` (see src/hotelareascore/webdata.py).
export default defineConfig({
  output: 'static',
});
