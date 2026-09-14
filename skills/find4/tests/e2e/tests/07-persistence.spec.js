// tests/07-persistence.spec.js
// Tests localStorage-backed state: games persist across page reloads,
// "Clear saved games" wipes state, and high scores are recorded.

const { test, expect, SEL } = require('./fixtures/game.fixture');

test.describe('localStorage persistence', () => {

  test('game state persists after reload (same game words)', async ({ gamePage, page }) => {
    await gamePage.goto();

    // Capture current word set
    const wordsBefore = await page.locator(SEL.wordTile).evaluateAll(
      els => els.map(el => el.getAttribute('data-word')).sort()
    );

    await page.reload();
    await gamePage.goto(); // re-waits for grid

    const wordsAfter = await page.locator(SEL.wordTile).evaluateAll(
      els => els.map(el => el.getAttribute('data-word')).sort()
    );

    expect(wordsAfter).toEqual(wordsBefore);
  });

  test('high score is stored after winning', async ({ gamePage, page }) => {
    await gamePage.goto();
    await gamePage.autoSolveAll();

    // Wait for the win message
    await page.locator(SEL.retryBtn).waitFor({ state: 'visible', timeout: 10_000 });

    const scores = await page.evaluate(() =>
      JSON.parse(localStorage.getItem('connectionHighScores') || '{}')
    );
    expect(Object.keys(scores).length).toBeGreaterThan(0);
  });

  test('clearing saved games via mobile sheet resets to default', async ({ gamePage, page }) => {
    await gamePage.goto();

    // Use the JS API directly (simulates the "Clear saved games" button)
    await page.evaluate(() => localStorage.clear());
    await page.reload();

    await page.waitForFunction(() => {
      const grid = document.getElementById('game-grid');
      return grid && grid.children.length > 0;
    }, { timeout: 10_000 });

    // Should still render a playable grid from the built-in defaults
    const tiles = page.locator(SEL.wordTile);
    await expect(tiles).toHaveCount(16);
  });

  test('puzzle count updates after loading a new config', async ({ gamePage, page }) => {
    await page.goto('/?config=/games/everyday-life-age-12.json');
    await page.waitForFunction(() => {
      const grid = document.getElementById('game-grid');
      return grid && grid.children.length > 0;
    }, { timeout: 10_000 });

    const count = parseInt(await page.locator(SEL.puzzleCount).textContent(), 10);
    // everyday-life-age-12.json has 2 game_sets
    expect(count).toBeGreaterThanOrEqual(2);
  });

});
