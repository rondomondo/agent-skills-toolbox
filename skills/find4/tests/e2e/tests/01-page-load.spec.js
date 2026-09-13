// tests/01-page-load.spec.js
// Verifies the app loads correctly, the grid populates, and initial UI state
// matches expectations before any player interaction.

const { test, expect, SEL } = require('./fixtures/game.fixture');

test.describe('Page load & initial state', () => {

  test('title is "Find4"', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle('Find4');
  });

  test('game grid renders with 16 tiles', async ({ gamePage, page }) => {
    await gamePage.goto();
    const tiles = page.locator(SEL.wordTile);
    await expect(tiles).toHaveCount(16);
  });

  test('every tile has a data-word attribute', async ({ gamePage, page }) => {
    await gamePage.goto();
    const tiles = await page.locator(SEL.wordTile).all();
    for (const tile of tiles) {
      const word = await tile.getAttribute('data-word');
      expect(word).toBeTruthy();
    }
  });

  test('Submit button is disabled on load', async ({ gamePage, page }) => {
    await gamePage.goto();
    await expect(page.locator(SEL.submitBtn)).toBeDisabled();
  });

  test('lives display shows 4', async ({ gamePage, page }) => {
    await gamePage.goto();
    await expect(page.locator(SEL.livesDisplay)).toHaveText('4');
  });

  test('puzzle count is at least 1', async ({ gamePage, page }) => {
    await gamePage.goto();
    const count = await page.locator(SEL.puzzleCount).textContent();
    expect(parseInt(count, 10)).toBeGreaterThanOrEqual(1);
  });

  test('timer starts at 00:00', async ({ gamePage, page }) => {
    await gamePage.goto();
    await expect(page.locator(SEL.timer)).toHaveText('00:00');
  });

  test('timer increments after one second', async ({ gamePage, page }) => {
    await gamePage.goto();
    await page.waitForTimeout(1100);
    const timerText = await page.locator(SEL.timer).textContent();
    expect(timerText).not.toBe('00:00');
  });

  test('no solved categories on load', async ({ gamePage, page }) => {
    await gamePage.goto();
    await expect(page.locator(SEL.solvedCategory)).toHaveCount(0);
  });

  test('toolbar toggle button is visible', async ({ gamePage, page }) => {
    await gamePage.goto();
    await expect(page.locator(SEL.toolbarToggle)).toBeVisible();
  });

  test('toast appears on startup with "Find4 is ready" message', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator(SEL.toastSuccess).first()).toBeVisible({ timeout: 8_000 });
    const text = await page.locator(SEL.toastSuccess).first().textContent();
    expect(text).toMatch(/Find4 is ready/i);
  });

  test('app loads game from ?config= URL param', async ({ page }) => {
    // Load the included everyday-life-age-12.json via query param
    await page.goto('/?config=/games/everyday-life-age-12.json');
    await page.waitForFunction(() => {
      const grid = document.getElementById('game-grid');
      return grid && grid.children.length > 0;
    }, { timeout: 10_000 });
    const tiles = page.locator(SEL.wordTile);
    await expect(tiles).toHaveCount(16);
  });

});
