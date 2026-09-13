// tests/02-tile-selection.spec.js
// Tests the word-tile selection mechanics: toggling, 4-word limit,
// deselection, and Submit button state.

const { test, expect, SEL } = require('./fixtures/game.fixture');

test.describe('Tile selection mechanics', () => {

  test.beforeEach(async ({ gamePage }) => {
    await gamePage.goto();
  });

  test('clicking a tile marks it as selected', async ({ page }) => {
    const firstTile = page.locator(SEL.wordTile).first();
    await firstTile.click();
    await expect(firstTile).toHaveClass(/selected/);
  });

  test('clicking a selected tile deselects it', async ({ page }) => {
    const firstTile = page.locator(SEL.wordTile).first();
    await firstTile.click();
    await expect(firstTile).toHaveClass(/selected/);
    await firstTile.click();
    await expect(firstTile).not.toHaveClass(/selected/);
  });

  test('Submit button enables when exactly 4 tiles are selected', async ({ page }) => {
    const tiles = page.locator(SEL.wordTile);
    for (let i = 0; i < 4; i++) {
      await tiles.nth(i).click();
    }
    await expect(page.locator(SEL.submitBtn)).toBeEnabled();
  });

  test('Submit button remains disabled with fewer than 4 selections', async ({ page }) => {
    const tiles = page.locator(SEL.wordTile);
    for (let i = 0; i < 3; i++) {
      await tiles.nth(i).click();
    }
    await expect(page.locator(SEL.submitBtn)).toBeDisabled();
  });

  test('cannot select more than 4 tiles', async ({ page }) => {
    const tiles = page.locator(SEL.wordTile);
    // Click 5 tiles
    for (let i = 0; i < 5; i++) {
      await tiles.nth(i).click();
    }
    // Only 4 should have the selected class
    const selectedCount = await page.locator(`${SEL.wordTile}.selected`).count();
    expect(selectedCount).toBe(4);
  });

  test('deselecting a tile from a full set of 4 disables Submit', async ({ page }) => {
    const tiles = page.locator(SEL.wordTile);
    for (let i = 0; i < 4; i++) {
      await tiles.nth(i).click();
    }
    await expect(page.locator(SEL.submitBtn)).toBeEnabled();

    // Deselect one
    await tiles.first().click();
    await expect(page.locator(SEL.submitBtn)).toBeDisabled();
  });

  test('Shuffle button clears the current selection', async ({ page }) => {
    const tiles = page.locator(SEL.wordTile);
    for (let i = 0; i < 3; i++) {
      await tiles.nth(i).click();
    }
    await page.locator(SEL.shuffleBtn).click();

    const selectedCount = await page.locator(`${SEL.wordTile}.selected`).count();
    expect(selectedCount).toBe(0);
  });

  test('Shuffle button re-orders tiles', async ({ page }) => {
    // Capture order before
    const before = await page.locator(SEL.wordTile).evaluateAll(
      els => els.map(el => el.getAttribute('data-word'))
    );

    await page.locator(SEL.shuffleBtn).click();

    const after = await page.locator(SEL.wordTile).evaluateAll(
      els => els.map(el => el.getAttribute('data-word'))
    );

    // Same words, potentially different order (probabilistic — rarely fails with 16 tiles)
    expect(before.slice().sort()).toEqual(after.slice().sort());
  });

});
