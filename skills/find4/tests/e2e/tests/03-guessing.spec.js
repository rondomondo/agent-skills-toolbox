// tests/03-guessing.spec.js
// Tests correct group submission, incorrect guess penalties (lives),
// and the auto-solve shortcut.
//
// Strategy: use Ctrl+Shift+S (autoSolveAll) for "correct guess" paths since
// the word order is shuffled — this avoids hard-coding word lists while still
// exercising the real submit → solveGroup path.
// For incorrect guesses we select 4 tiles that cross groups and submit.

const { test, expect, SEL } = require('./fixtures/game.fixture');

test.describe('Guessing — correct path', () => {
    test.beforeEach(async ({ gamePage }) => {
        await gamePage.goto();
    });

    test('clicking Play Again resets the grid', async ({ gamePage, page }) => {
        await gamePage.autoSolveAll();
        await page.locator(SEL.retryBtn).waitFor({ state: 'visible', timeout: 60_000 });
        await page.waitForTimeout(300);

        await page.locator(SEL.retryBtn).click();

        // Grid should be back to 16 unsolved tiles
        await expect(page.locator(SEL.wordTile)).toHaveCount(16, { timeout: 60_000 });
        await expect(page.locator(SEL.solvedCategory)).toHaveCount(0);
    });

    test('auto-solving via Ctrl+Shift+S solves all 4 groups', async ({ gamePage, page }) => {
        await gamePage.autoSolveAll();

        // Wait until 4 solved categories appear
        await expect(page.locator(SEL.solvedCategory)).toHaveCount(4, { timeout: 60_000 });
    });

    test('solved group tiles get a solved-color attribute', async ({ gamePage, page }) => {
        await gamePage.autoSolveAll();
        await expect(page.locator(SEL.solvedTile).first()).toBeVisible({ timeout: 60_000 });
        const solved = await page.locator(SEL.solvedTile).count();
        expect(solved).toBe(4);
    });

    test('winning shows a success toast with "Fantastico"', async ({ gamePage, page }) => {
        await gamePage.autoSolveAll();
        await expect(page.locator(SEL.toastSuccess).first()).toBeVisible({ timeout: 60_000 });

        // Poll until we see the win message (other toasts appear first)
        await expect(async () => {
            const text = await page.locator(SEL.toastSuccess).first().textContent();
            expect(text).toMatch(/correct group/i);
        }).toPass({ timeout: 10_000 });
    });

    test('Submit is disabled after winning', async ({ gamePage, page }) => {
        await gamePage.autoSolveAll();
        await page.locator(SEL.solvedCategory).nth(3).waitFor({ state: 'visible', timeout: 60_000 });
        await expect(page.locator(SEL.submitBtn)).toBeDisabled({ timeout: 60_000 });
    });

    test('Play Again button appears after winning', async ({ gamePage, page }) => {
        await gamePage.autoSolveAll();
        await expect(page.locator(SEL.retryBtn)).toBeVisible({ timeout: 60_000 });
    });
});

test.describe('Guessing — incorrect path', () => {
    test.beforeEach(async ({ gamePage }) => {
        await gamePage.goto();
    });

    // Helper: pick 4 tiles that are unlikely to form a valid group
    // by taking 1 from each of the first 4 tiles in document order.
    // Since tiles are shuffled across all 4 groups this will almost
    // certainly be a cross-group guess (16! permutations).
    async function submitCrossGroupGuess(page) {
        const tiles = page.locator(SEL.wordTile);
        const words = await tiles.evaluateAll((els) => els.slice(0, 4).map((el) => el.getAttribute('data-word')));
        for (const word of words) {
            await page.locator(`${SEL.wordTile}[data-word="${word}"]`).click();
        }
        // Only submit if they happen NOT to all belong to the same group
        // We'll check the group membership via the data-category attribute
        const categories = await Promise.all(
            words.map((w) => page.locator(`${SEL.wordTile}[data-word="${w}"]`).getAttribute('data-category')),
        );
        const allSame = categories.every((c) => c === categories[0]);
        if (allSame) {
            // Accidentally picked a valid group — deselect and try offset tiles
            for (const word of words) {
                await page.locator(`${SEL.wordTile}[data-word="${word}"]`).click();
            }
            const moreWords = await tiles.evaluateAll((els) =>
                [els[0], els[2], els[5], els[9]].map((el) => el.getAttribute('data-word')),
            );
            for (const word of moreWords) {
                await page.locator(`${SEL.wordTile}[data-word="${word}"]`).click();
            }
        }
        await page.locator(SEL.submitBtn).click();
    }

    test('incorrect guess decrements lives by 1', async ({ gamePage, page }) => {
        const livesBefore = await gamePage.getLives();
        await submitCrossGroupGuess(page);
        const livesAfter = await gamePage.getLives();
        expect(livesAfter).toBe(livesBefore - 1);
    });

    test('incorrect guess shows an error toast', async ({ gamePage, page }) => {
        await submitCrossGroupGuess(page);
        await expect(page.locator(SEL.toastError)).toBeVisible({ timeout: 30_000 });
    });

    test('incorrect guess shakes the grid', async ({ gamePage, page }) => {
        // After an incorrect guess the grid animation is reset to "shake"
        await submitCrossGroupGuess(page);
        const animation = await page.locator(SEL.gameGrid).evaluate((el) => el.style.animation);
        expect(animation).toMatch(/shake/);
    });

    test('game ends after 4 incorrect guesses', async ({ gamePage, page }) => {
        for (let i = 0; i < 4; i++) {
            await submitCrossGroupGuess(page);
            // Brief pause so grid re-renders between guesses
            await page.waitForTimeout(300);
        }
        // Poll until we see the win message (other toasts appear first)
        await expect(async () => {
            const text = await page.locator(SEL.toastError).first().textContent();
            expect(text).toMatch(/game over/i);
        }).toPass({ timeout: 30_000 });
        await expect(page.locator(SEL.retryBtn)).toBeVisible({ timeout: 60_000 });
    });

    test('game-over shows Play Again button', async ({ gamePage, page }) => {
        for (let i = 0; i < 4; i++) {
            await submitCrossGroupGuess(page);
            await page.waitForTimeout(200);
        }
        await expect(page.locator(SEL.retryBtn)).toBeVisible({ timeout: 10_000 });
    });
});
