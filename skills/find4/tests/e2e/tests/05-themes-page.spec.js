// tests/05-themes-page.spec.js
// Tests the themes.html library page: loading, search filtering,
// table/card rendering, and config-link navigation.

const { test, expect } = require('@playwright/test');

const SEL = {
  tableBody:    '#table-body',
  cardContainer:'#card-container',
  searchInput:  '#search',
  refreshFab:   '.refresh-fab',
  tableRow:     '#table-body tr',
  card:         '.theme-card',
  chip:         '.mdl-chip__text',
};

test.describe('Themes / Library page', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/themes.html');
    // Wait until at least one row (or card) is rendered
    await page.waitForFunction(() => {
      const tbody = document.getElementById('table-body');
      return tbody && tbody.querySelectorAll('tr').length > 0;
    }, { timeout: 10_000 });
  });

  test('page title is "Category & Theme"', async ({ page }) => {
    await expect(page).toHaveTitle('Category & Theme');
  });

  test('table body has at least one data row', async ({ page }) => {
    const rows = page.locator(SEL.tableRow);
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('each row contains a config button', async ({ page }) => {
    const rows = await page.locator(SEL.tableRow).all();
    for (const row of rows.slice(0, 3)) { // check first 3 to keep test fast
      const btn = row.locator('button.theme-link-button');
      await expect(btn).toBeVisible();
    }
  });

  test('search filters rows by theme name', async ({ page }) => {
    const totalBefore = await page.locator(SEL.tableRow).count();

    // Type a unique string from the default themes.json
    await page.locator(SEL.searchInput).fill('school');
    await page.waitForTimeout(300); // debounce

    const totalAfter = await page.locator(SEL.tableRow).count();
    expect(totalAfter).toBeLessThan(totalBefore);
    expect(totalAfter).toBeGreaterThan(0);
  });

  test('search with no match shows zero rows', async ({ page }) => {
    await page.locator(SEL.searchInput).fill('zzzxxx_no_match_999');
    await page.waitForTimeout(300);
    const rowCount = await page.locator(SEL.tableRow).count();
    expect(rowCount).toBe(0);
  });

  test('clearing search restores all rows', async ({ page }) => {
    const total = await page.locator(SEL.tableRow).count();

    await page.locator(SEL.searchInput).fill('school');
    await page.waitForTimeout(300);

    await page.locator(SEL.searchInput).fill('');
    await page.waitForTimeout(300);

    const restored = await page.locator(SEL.tableRow).count();
    expect(restored).toBe(total);
  });

  test('refresh FAB re-fetches and re-renders themes', async ({ page }) => {
    const before = await page.locator(SEL.tableRow).count();
    await page.locator(SEL.refreshFab).click();

    // Wait for re-render
    await page.waitForFunction(() => {
      const tbody = document.getElementById('table-body');
      return tbody && tbody.querySelectorAll('tr').length > 0;
    }, { timeout: 8_000 });

    const after = await page.locator(SEL.tableRow).count();
    expect(after).toBe(before);
  });

  test('category chips are visible in rows', async ({ page }) => {
    const firstRowChips = page.locator(`${SEL.tableRow}:first-child .mdl-chip__text`);
    await expect(firstRowChips.first()).toBeVisible();
  });

  test('config button opens index.html with config param', async ({ page, context }) => {
    // Click the first config button and capture the new tab/window
    const [newPage] = await Promise.all([
      context.waitForEvent('page'),
      page.locator('button.theme-link-button').first().click(),
    ]);
    await newPage.waitForLoadState('domcontentloaded');
    expect(newPage.url()).toMatch(/index\.html\?config=/);
    await newPage.close();
  });

});

// Mobile card view (narrow viewport)
test.describe('Themes page — mobile card view', () => {

  test.use({ viewport: { width: 375, height: 812 } });

  test.beforeEach(async ({ page }) => {
    await page.goto('/themes.html');
    await page.waitForFunction(() => {
      const c = document.getElementById('card-container');
      return c && c.querySelectorAll('.theme-card').length > 0;
    }, { timeout: 10_000 });
  });

  test('card container is visible on mobile', async ({ page }) => {
    await expect(page.locator('#card-container')).toBeVisible();
  });

  test('at least one theme card is rendered', async ({ page }) => {
    const cards = page.locator('.theme-card');
    await expect(cards.first()).toBeVisible();
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('mobile card shows theme title', async ({ page }) => {
    const title = page.locator('.theme-card .mdl-card__title-text').first();
    await expect(title).toBeVisible();
    const text = await title.textContent();
    expect(text.trim().length).toBeGreaterThan(0);
  });

});
