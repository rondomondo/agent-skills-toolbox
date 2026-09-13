// tests/06-mobile.spec.js
// Tests the mobile-specific UI: the floating action button (FAB),
// the bottom sheet menu, and touch interactions on the game grid.
// All tests in this file use a narrow viewport.

const { test, expect, SEL } = require('./fixtures/game.fixture');

// Override viewport for the whole file
test.use({ viewport: { width: 390, height: 844 } }); // iPhone 14 Pro

test.describe('Mobile FAB and bottom sheet', () => {

  test.beforeEach(async ({ gamePage }) => {
    await gamePage.goto();
  });

  test('mobile FAB is visible on narrow viewport', async ({ page }) => {
    await expect(page.locator(SEL.mobileFab)).toBeVisible();
  });

  test('tapping FAB opens the bottom sheet', async ({ page }) => {
    await page.locator(SEL.mobileFab).tap();
    await expect(page.locator(SEL.mobileSheet)).toBeVisible({ timeout: 3_000 });
  });

  test('bottom sheet contains Help, Library, Create, Detail, Export buttons', async ({ page }) => {
    await page.locator(SEL.mobileFab).tap();
    const sheet = page.locator(SEL.mobileSheet);
    await sheet.waitFor({ state: 'visible' });

    for (const label of ['Help', 'Library', 'Create game', 'Detail', 'Export']) {
      await expect(sheet.getByText(label, { exact: true })).toBeVisible();
    }
  });

  test('tapping Help in bottom sheet opens tutorial modal', async ({ page }) => {
    await page.locator(SEL.mobileFab).tap();
    await page.locator(SEL.mobileSheet).waitFor({ state: 'visible' });
    await page.locator(SEL.mobileSheet).getByText('Help', { exact: true }).tap();
    await expect(page.locator(SEL.tutorialModal)).toBeVisible({ timeout: 3_000 });
  });

  test('tapping backdrop closes the bottom sheet', async ({ page }) => {
    await page.locator(SEL.mobileFab).tap();
    await page.locator(SEL.mobileSheet).waitFor({ state: 'visible' });
    await page.locator('#mobile-sheet-backdrop').tap();
    await expect(page.locator(SEL.mobileSheet)).not.toBeVisible({ timeout: 3_000 });
  });

  test('word tiles are tappable on mobile', async ({ page }) => {
    const firstTile = page.locator(SEL.wordTile).first();
    await firstTile.tap();
    await expect(firstTile).toHaveClass(/selected/);
  });

  test('can select 4 tiles by tapping on mobile', async ({ page }) => {
    const tiles = page.locator(SEL.wordTile);
    for (let i = 0; i < 4; i++) {
      await tiles.nth(i).tap();
    }
    await expect(page.locator(SEL.submitBtn)).toBeEnabled();
  });

});
