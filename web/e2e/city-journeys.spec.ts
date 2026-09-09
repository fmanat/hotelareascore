import { test, expect } from '@playwright/test';

// Bloc H item 2 (night mission #4): the full journey -- search -> hotel
// page -> compare -> city page -- exercised on all 12 launch cities, not
// just the original London/Bangkok fixture (journey.spec.ts). Each city
// gets one fixture hotel (web/e2e-fixtures/, generated for this pass) so
// a real navigation path exists everywhere; a per-city keyboard-only
// variant covers the same path without a mouse, matching the existing
// accessible-combobox pattern (docs/reports/phase-4-accessibility-audit.md).

const CITIES: Record<string, { hotelName: string; cityName: string }> = {
  london: { hotelName: 'Fixture Park Hotel', cityName: 'London' },
  bangkok: { hotelName: 'Fixture Riverside Hotel', cityName: 'Bangkok' },
  paris: { hotelName: 'Fixture Paris Hotel', cityName: 'Paris' },
  rome: { hotelName: 'Fixture Rome Hotel', cityName: 'Rome' },
  barcelona: { hotelName: 'Fixture Barcelona Hotel', cityName: 'Barcelona' },
  amsterdam: { hotelName: 'Fixture Amsterdam Hotel', cityName: 'Amsterdam' },
  lisbon: { hotelName: 'Fixture Lisbon Hotel', cityName: 'Lisbon' },
  sydney: { hotelName: 'Fixture Sydney Hotel', cityName: 'Sydney' },
  tokyo: { hotelName: 'Fixture Tokyo Hotel', cityName: 'Tokyo' },
  dubai: { hotelName: 'Fixture Dubai Hotel', cityName: 'Dubai' },
  new_york: { hotelName: 'Fixture New York City metro Hotel', cityName: 'New York City metro' },
  singapore: { hotelName: 'Fixture Singapore Hotel', cityName: 'Singapore' },
};

for (const [cityId, { hotelName, cityName }] of Object.entries(CITIES)) {
  // Never compare a hotel to itself -- London's own fixture is "Fixture
  // Park Hotel", the default second pick for every other city.
  const secondHotelName = hotelName === 'Fixture Park Hotel' ? 'Fixture Transit Hotel' : 'Fixture Park Hotel';
  const secondHotelSlug = hotelName === 'Fixture Park Hotel' ? 'fixture-transit-hotel-e2e002' : 'fixture-park-hotel-e2e001';

  test(`${cityId}: search -> hotel -> compare -> city page (mouse)`, async ({ page }) => {
    await page.goto('/');
    const search = page.getByLabel('Search for a hotel');
    await search.fill(hotelName);
    const option = page.getByRole('option', { name: new RegExp(hotelName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) });
    await expect(option).toBeVisible();
    await option.click();

    await expect(page).toHaveURL(/\/hotel\//);
    await expect(page.getByRole('heading', { name: hotelName, level: 1 })).toBeVisible();

    // ComparePicker is always on the hotel page (docs: "Compare with
    // another hotel"), independent of whether a comparable-hotels list
    // exists -- these single-hotel-per-city fixtures have none.
    const compareInput = page.getByLabel('Compare with another hotel');
    await compareInput.fill(secondHotelName);
    const compareOption = page.getByRole('option', { name: new RegExp(secondHotelName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) });
    await expect(compareOption).toBeVisible();
    await compareOption.click();
    await expect(page).toHaveURL(new RegExp(`/compare\\?a=.*&b=${secondHotelSlug}`));
    await expect(page.getByRole('heading', { name: hotelName })).toBeVisible();

    await page.goto(`/city/${cityId}`);
    await expect(page.getByRole('heading', { name: new RegExp(cityName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), level: 1 })).toBeVisible();
  });

  test(`${cityId}: search -> hotel, keyboard only (no mouse)`, async ({ page }) => {
    await page.goto('/');
    const search = page.getByLabel('Search for a hotel');
    await search.click();
    await search.fill(hotelName);
    const results = page.locator('#search-results');
    await expect(results).toBeVisible();
    await search.press('ArrowDown');
    await expect(search).toHaveAttribute('aria-activedescendant', /.+/);
    await search.press('Enter');
    await expect(page).toHaveURL(/\/hotel\//);
    await expect(page.getByRole('heading', { name: hotelName, level: 1 })).toBeVisible();

    // Same accessible-combobox pattern on ComparePicker, still no mouse.
    const compareInput = page.getByLabel('Compare with another hotel');
    await compareInput.click();
    await compareInput.fill(secondHotelName);
    const compareResults = page.locator('#compare-picker-results');
    await expect(compareResults).toBeVisible();
    await compareInput.press('ArrowDown');
    await compareInput.press('Enter');
    await expect(page).toHaveURL(new RegExp(`/compare\\?a=.*&b=${secondHotelSlug}`));
  });
}
