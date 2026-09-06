import { defineConfig, devices } from '@playwright/test';

// docs/CLAUDE.md §9: "E2E (search -> result -> persona -> compare, mobile,
// noindex rules, affiliate rel)". Runs against a static `astro preview`
// server over fixture data (e2e-fixtures/), not live Overture data --
// see e2e/prepare-fixtures.mjs for why.
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  globalTeardown: './e2e/global-teardown.ts',
  use: {
    baseURL: 'http://localhost:4322',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'desktop-chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-chromium', use: { ...devices['Pixel 7'] } },
  ],
  webServer: {
    // Not `astro preview`: this Astro version's preview command manages
    // itself as a persistent background daemon rather than blocking in the
    // foreground, which Playwright's webServer can't reliably start/stop
    // per run -- see e2e/static-server.mjs.
    command: 'node e2e/prepare-fixtures.mjs && npm run build && node e2e/static-server.mjs',
    url: 'http://localhost:4322',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
