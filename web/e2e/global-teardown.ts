// Restores whatever real generated data (or absence of it) existed before
// global-setup.ts swapped in the E2E fixtures.
import { existsSync, mkdirSync, readdirSync, rmSync, cpSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC_DATA = path.join(ROOT, 'src', 'data');
const PUBLIC_DATA = path.join(ROOT, 'public', 'data');
const BACKUP = path.join(ROOT, '.e2e-data-backup');

function restore(realDir: string, backupSubdir: string) {
  const backupDir = path.join(BACKUP, backupSubdir);
  rmSync(realDir, { recursive: true, force: true });
  if (existsSync(backupDir)) {
    mkdirSync(realDir, { recursive: true });
    for (const f of readdirSync(backupDir)) {
      cpSync(path.join(backupDir, f), path.join(realDir, f));
    }
  }
}

export default function globalTeardown() {
  restore(SRC_DATA, 'src-data');
  restore(PUBLIC_DATA, 'public-data');
  rmSync(BACKUP, { recursive: true, force: true });
}
