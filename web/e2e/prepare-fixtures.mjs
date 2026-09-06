#!/usr/bin/env node
// E2E tests run against a small, fixed fixture dataset (web/e2e-fixtures/),
// not live Overture data -- CI has no network access to the Overture
// release and no ETL output checked in (data/etl/ is gitignored,
// regenerable-only per docs/adr/002). Deterministic fixtures also make the
// journey assertions in e2e/journey.spec.ts (specific scores, specific
// hotel names) stable across data refreshes.
//
// Run as part of the Playwright webServer command (see playwright.config.ts)
// so the fixture swap happens before `astro build`. Backs up any real
// generated data a developer has locally; e2e/global-teardown.ts restores it
// after the test run.
import { existsSync, mkdirSync, readdirSync, rmSync, cpSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC_DATA = path.join(ROOT, 'src', 'data');
const PUBLIC_DATA = path.join(ROOT, 'public', 'data');
const FIXTURES = path.join(ROOT, 'e2e-fixtures');
const BACKUP = path.join(ROOT, '.e2e-data-backup');

function backupAndReplace(realDir, fixtureDir, backupSubdir) {
  const backupDir = path.join(BACKUP, backupSubdir);
  if (existsSync(realDir)) {
    mkdirSync(backupDir, { recursive: true });
    for (const f of readdirSync(realDir)) {
      cpSync(path.join(realDir, f), path.join(backupDir, f));
    }
  }
  rmSync(realDir, { recursive: true, force: true });
  mkdirSync(realDir, { recursive: true });
  for (const f of readdirSync(fixtureDir)) {
    cpSync(path.join(fixtureDir, f), path.join(realDir, f));
  }
}

backupAndReplace(SRC_DATA, path.join(FIXTURES, 'src-data'), 'src-data');
backupAndReplace(PUBLIC_DATA, path.join(FIXTURES, 'public-data'), 'public-data');
console.log('[e2e] fixture data installed (real data backed up to .e2e-data-backup/)');
