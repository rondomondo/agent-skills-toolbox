// tests/04-toolbar-and-hints.spec.js
// Tests toolbar toggle, the hint button, keyboard shortcuts, and
// the tutorial / resource modals.

const { test, expect, SEL } = require('./fixtures/game.fixture');

test.describe('Toolbar', () => {

  test.beforeEach(async ({ gamePage }) => {
    await gamePage.goto();
  });

  test('toolbar toggle expands the toolbar section', async ({ page }) => {
    const section = page.locator('#toolbar-section');
    // Default: collapsed
    await expect(section).toHaveClass(/section-collapsed/);

    await page.locator(SEL.toolbarToggle).click();
    await expect(section).not.toHaveClass(/section-collapsed/);
  });

  test('double-clicking the toolbar section also toggles it', async ({ page }) => {
    const section = page.locator('#toolbar-section');
    await section.dblclick();
    await expect(section).not.toHaveClass(/section-collapsed/);
  });

  test('Ctrl+Shift+O toggles the toolbar via keyboard', async ({ page }) => {
    const section = page.locator('#toolbar-section');
    await page.keyboard.press('Control+Shift+O');
    await expect(section).not.toHaveClass(/section-collapsed/);
    await page.keyboard.press('Control+Shift+O');
    await expect(section).toHaveClass(/section-collapsed/);
  });

  test('level select dropdown is present and has at least 1 option', async ({ page }) => {
    const opts = page.locator(`${SEL.levelSelect} option`);
    await expect(opts).toHaveCount(1, { timeout: 5_000 });
    // Or more if multiple game_sets loaded
    const count = await opts.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('changing level select starts a new game', async ({ gamePage, page }) => {
    // Only meaningful if there are 2+ games; skip gracefully otherwise
    const opts = await page.locator(`${SEL.levelSelect} option`).count();
    test.skip(opts < 2, 'Only one game loaded — level switching not testable');

    const wordsBefore = await page.locator(SEL.wordTile).evaluateAll(
      els => els.map(el => el.getAttribute('data-word'))
    );
    await page.locator(SEL.levelSelect).selectOption({ index: 1 });
    await page.waitForTimeout(500);
    const wordsAfter = await page.locator(SEL.wordTile).evaluateAll(
      els => els.map(el => el.getAttribute('data-word'))
    );
    expect(wordsAfter).not.toEqual(wordsBefore);
  });

});

test.describe('Hint button', () => {

  test.beforeEach(async ({ gamePage }) => {
    await gamePage.goto();
  });

  test('clicking Hint shows a hint toast', async ({ page }) => {
    await page.locator(SEL.hintBtn).click();
    await expect(page.locator('.toast-hint')).toBeVisible({ timeout: 5_000 });
    const text = await page.locator('.toast-hint').textContent();
    expect(text).toMatch(/Hint:/i);
  });

  test('hints-left count decrements after using a hint', async ({ page }) => {
    const before = parseInt(await page.locator(SEL.hintsDisplay).textContent(), 10);
    await page.locator(SEL.hintBtn).click();
    const after = parseInt(await page.locator(SEL.hintsDisplay).textContent(), 10);
    expect(after).toBe(before - 1);
  });

  test('hint button disables when no hints remain', async ({ page }) => {
    // Exhaust all hints
    const initialHints = parseInt(await page.locator(SEL.hintsDisplay).textContent(), 10);
    for (let i = 0; i < initialHints; i++) {
      await page.locator(SEL.hintBtn).click();
      await page.waitForTimeout(100);
    }
    await expect(page.locator(SEL.hintBtn)).toBeDisabled();
  });

});

test.describe('Keyboard shortcuts', () => {

  test.beforeEach(async ({ gamePage }) => {
    await gamePage.goto();
  });

  test('Ctrl+Shift+H opens the tutorial modal', async ({ page }) => {
    await page.keyboard.press('Control+Shift+H');
    await expect(page.locator(SEL.tutorialModal)).toBeVisible({ timeout: 3_000 });
  });

  test('Ctrl+Shift+D opens the resource/detail modal', async ({ page }) => {
    await page.keyboard.press('Control+Shift+D');
    await expect(page.locator(SEL.resourcesModal)).toBeVisible({ timeout: 3_000 });
  });

  test('Ctrl+Shift+S auto-solves the game', async ({ page }) => {
    await page.keyboard.press('Control+Shift+S');
    await expect(page.locator(SEL.solvedCategory)).toHaveCount(4, { timeout: 8_000 });
  });

});

test.describe('Tutorial modal', () => {

  test.beforeEach(async ({ gamePage }) => {
    await gamePage.goto();
  });

  test('Help toolbar button opens tutorial modal', async ({ page }) => {
    await page.locator('.help-btn').click();
    await expect(page.locator(SEL.tutorialModal)).toBeVisible({ timeout: 3_000 });
  });

  test('tutorial modal can be closed', async ({ page }) => {
    await page.locator('.help-btn').click();
    await page.locator(SEL.tutorialModal).waitFor({ state: 'visible' });

    // Close via the × button inside the modal
    const closeBtn = page.locator(`${SEL.tutorialModal} .close-btn, ${SEL.tutorialModal} [aria-label="Close"]`).first();
    await closeBtn.click();
    await expect(page.locator(SEL.tutorialModal)).not.toBeVisible({ timeout: 3_000 });
  });

});
