#!/usr/bin/env node
// Build guard (found necessary 2026-09-07, first Cloudflare Pages deploy):
// web/src/lib/data.ts and the sitemap-hotels.xml.ts route import these
// JSON exports directly (`import hotelsLondon from '../data/hotels-london
// .json'`), so a missing file used to fail as a bare, cryptic
// UNRESOLVED_IMPORT deep in the bundler's own error output -- no mention
// of which file, or that these are committed data artifacts, not code.
// This runs as an npm `prebuild` hook (package.json), before `astro
// build` ever starts, so a missing export fails fast with an explicit,
// actionable message instead.
import { existsSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const WEB_ROOT = path.resolve(fileURLToPath(import.meta.url), '../..');

// docs/reports/phase-4-launch-runbook.md / README.md "Web data exports":
// these are committed artifacts (web/.gitignore un-ignores them), not
// build-time-generated -- regenerate with the command in the error below
// only if you have the Phase 1 ETL output (data/etl/) locally.
const REQUIRED = [
  'src/data/hotels-london.json',
  'src/data/hotels-bangkok.json',
  'src/data/city-baselines.json',
  'src/data/city-pages.json',
  'src/data/meta.json',
  'src/data/personas.json',
  'public/data/search-index.json',
];

const REGEN_COMMAND =
  'python3 -m hotelareascore.cli webdata --city london,bangkok  ' +
  '(from the repo root, needs data/etl/ -- run ingest+score+validate first if it is missing)';

const missing = [];
const empty = [];
for (const rel of REQUIRED) {
  const abs = path.join(WEB_ROOT, rel);
  if (!existsSync(abs)) {
    missing.push(rel);
    continue;
  }
  if (statSync(abs).size === 0) {
    empty.push(rel);
  }
}

if (missing.length > 0 || empty.length > 0) {
  console.error('');
  console.error('ERROR: web data export(s) missing or empty -- the build cannot continue.');
  console.error('');
  if (missing.length > 0) {
    console.error('Missing:');
    for (const f of missing) console.error(`  - web/${f}`);
  }
  if (empty.length > 0) {
    console.error('Present but empty (0 bytes):');
    for (const f of empty) console.error(`  - web/${f}`);
  }
  console.error('');
  console.error('These are committed data artifacts (web/.gitignore un-ignores them),');
  console.error('not generated during this build -- a checkout is expected to already');
  console.error('have them. If you are seeing this in CI/Cloudflare, the commit being');
  console.error('built is likely missing them; check they were actually committed and');
  console.error('pushed. If you are regenerating them locally, run:');
  console.error('');
  console.error(`  ${REGEN_COMMAND}`);
  console.error('');
  process.exit(1);
}
