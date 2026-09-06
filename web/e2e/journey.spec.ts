import { test, expect } from '@playwright/test';

// CLAUDE.md §9 E2E gate: search -> result -> persona -> compare, mobile
// (both desktop-chromium and mobile-chromium projects run this same spec —
// see playwright.config.ts), noindex rules, affiliate rel. Fixture data:
// web/e2e-fixtures/ (see e2e/prepare-fixtures.mjs for why this isn't live
// Overture data).

test('search -> result -> persona -> compare', async ({ page }) => {
  await page.goto('/');

  const search = page.getByLabel('Search for a hotel');
  await search.fill('Fixture Park');
  await expect(page.getByRole('link', { name: /Fixture Park Hotel/ })).toBeVisible();
  await page.getByRole('link', { name: /Fixture Park Hotel/ }).click();

  await expect(page).toHaveURL(/\/hotel\/fixture-park-hotel-e2e001/);
  await expect(page.getByRole('heading', { name: 'Fixture Park Hotel', level: 1 })).toBeVisible();
  await expect(page.getByText('Balanced score:')).toBeVisible();

  // Persona selector reweights the presented fit score without changing
  // the underlying dimension scores (docs/strategy.md §2D).
  await page.getByRole('tab', { name: 'Family' }).click();
  await expect(page.getByText(/Fit for.*family.*travelers/i)).toBeVisible();
  // Persona reweighting never changes the underlying dimension score.
  await expect(page.locator('.dim[data-dim="family_convenience"] .dim-score')).toHaveText('91');

  // Comparable-hotels "Compare" link (docs/strategy.md §2 journey B).
  await page.getByRole('link', { name: 'Compare' }).first().click();
  await expect(page).toHaveURL(/\/compare\?a=fixture-park-hotel-e2e001&b=/);
  await expect(page.getByRole('heading', { name: 'Fixture Park Hotel' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Fixture Transit Hotel' })).toBeVisible();
  await expect(page.getByText('View full result').first()).toBeVisible();
});

test('compare page picker works standalone', async ({ page }) => {
  await page.goto('/compare');
  await expect(page.getByText('Pick two hotels above')).toBeVisible();

  await page.getByLabel('Hotel A').fill('Fixture Riverside');
  await page.getByRole('button', { name: /Fixture Riverside Hotel/ }).click();
  await page.getByLabel('Hotel B').fill('Fixture Quiet');
  await page.getByRole('button', { name: /Fixture Quiet Hotel/ }).click();

  await expect(page.getByRole('heading', { name: 'Fixture Riverside Hotel' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Fixture Quiet Hotel' })).toBeVisible();
});

test('hotel and compare pages are noindex', async ({ page }) => {
  await page.goto('/hotel/fixture-park-hotel-e2e001');
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');

  await page.goto('/compare?a=fixture-park-hotel-e2e001&b=fixture-transit-hotel-e2e002');
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
});

test('affiliate CTA is a disabled placeholder, never an unflagged live link', async ({ page }) => {
  // AFFILIATE_ENABLED defaults off (CLAUDE.md §8) -- no real affiliate link
  // exists yet, so there must be nothing here for rel="sponsored" to be
  // missing FROM. This test's job is to fail loudly the day a real link is
  // added without that attribute (CLAUDE.md hard rule 9).
  await page.goto('/hotel/fixture-park-hotel-e2e001');
  const cta = page.locator('.cta');
  await expect(cta.getByText('Compare prices — coming soon')).toBeVisible();
  const ctaLinks = cta.locator('a[href^="http"]');
  await expect(ctaLinks).toHaveCount(0);
});

test('search box finds nothing for a nonsense query', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Search for a hotel').fill('zzz-nonexistent-hotel-zzz');
  await expect(page.getByText('No hotels found in our index.')).toBeVisible();
});
