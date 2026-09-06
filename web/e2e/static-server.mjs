#!/usr/bin/env node
// Plain static file server for the built `dist/` output, used by
// Playwright's webServer instead of `astro preview` -- this Astro version's
// preview command manages itself as a persistent background daemon (its
// own lock file, `astro preview stop/status/logs`) rather than blocking in
// the foreground the way Playwright's webServer expects, which made it
// unreliable to start/stop per test run. This server is a plain child
// process: starts, blocks, and exits cleanly when Playwright kills it.
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'dist');
const PORT = Number(process.env.PORT ?? 4322);

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
};

const server = createServer(async (req, res) => {
  try {
    const urlPath = decodeURIComponent(new URL(req.url ?? '/', 'http://localhost').pathname);
    let filePath = path.join(ROOT, urlPath);
    let st = await stat(filePath).catch(() => null);
    if (st?.isDirectory()) {
      filePath = path.join(filePath, 'index.html');
      st = await stat(filePath).catch(() => null);
    }
    if (!st) {
      // Astro's static build emits /foo/index.html for /foo -- also try that.
      const asDir = path.join(ROOT, urlPath, 'index.html');
      st = await stat(asDir).catch(() => null);
      if (st) filePath = asDir;
    }
    if (!st) {
      res.writeHead(404).end('Not found');
      return;
    }
    const body = await readFile(filePath);
    res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath)] ?? 'application/octet-stream' });
    res.end(body);
  } catch (err) {
    res.writeHead(500).end(String(err));
  }
});

server.listen(PORT, () => {
  console.log(`[e2e] static server serving ${ROOT} on http://localhost:${PORT}`);
});
