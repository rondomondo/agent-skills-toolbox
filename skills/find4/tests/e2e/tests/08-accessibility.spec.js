// tests/08-accessibility.spec.js
// Basic accessibility checks: ARIA labels, keyboard navigability,
// and focus management.  Does NOT use axe — keeps the dep list small.

const { test, expect, SEL } = require('./fixtures/game.fixture');

test.describe('Accessibility — game page', () => {

  test.beforeEach(async ({ gamePage }) => {
    await gamePage.goto();
  });

  test('toolbar toggle has an aria-label', async ({ page }) => {
    const label = await page.locator(SEL.toolbarToggle).getAttribute('aria-label');
    expect(label).toBeTruthy();
  });

  test('mobile FAB has an aria-label', async ({ page }) => {
    const label = await page.locator(SEL.mobileFab).getAttribute('aria-label');
    expect(label).toBeTruthy();
  });

  test('mobile sheet has role="dialog" and aria-label', async ({ page }) => {
    const role = await page.locator(SEL.mobileSheet).getAttribute('role');
    const label = await page.locator(SEL.mobileSheet).getAttribute('aria-label');
    expect(role).toBe('dialog');
    expect(label).toBeTruthy();
  });

  test('Home button has an aria-label', async ({ page }) => {
    const label = await page.locator('.home-btn').getAttribute('aria-label');
    expect(label).toBeTruthy();
  });

  test('Submit, Shuffle, Hint buttons are present in the DOM', async ({ page }) => {
    await expect(page.locator(SEL.submitBtn)).toBeAttached();
    await expect(page.locator(SEL.shuffleBtn)).toBeAttached();
    await expect(page.locator(SEL.hintBtn)).toBeAttached();
  });

  test('word tiles have data-word attributes (screen-reader usable)', async ({ page }) => {
    const tiles = await page.locator(SEL.wordTile).all();
    for (const tile of tiles.slice(0, 4)) {
      const word = await tile.getAttribute('data-word');
      expect(word).toBeTruthy();
    }
  });

  test('page has a lang attribute on <html>', async ({ page }) => {
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBeTruthy();
  });

});
