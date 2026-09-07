// @ts-check
import { defineConfig } from 'astro/config';

// Static-first per docs/adr/001 — no adapter, no SSR. Phase 2 has no live
// backend: every page is prerendered from the JSON exported by
// `make webdata` (see src/hotelareascore/webdata.py).
export default defineConfig({
  output: 'static',
  // Phase 4 performance audit (docs/reports/phase-4-performance-audit.md):
  // Astro's default 'auto' left one page type (hotel) with a small extra
  // external stylesheet request that every other page type didn't have.
  // 'always' inlines every page's CSS uniformly -- same rules, no visual
  // or functional change, one fewer request on hotel pages.
  build: {
    inlineStylesheets: 'always',
  },
});
