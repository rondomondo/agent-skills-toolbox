# Find4 — Playwright E2E Test Suite

End-to-end tests for the Find4 word-connections game (`index.html` + `themes.html`).

---

## Quick start

```bash
# 1. Install dependencies (Node 18+ required)
cd find4-e2e
npm install

# 2. Install Playwright browsers (first time only)
npx playwright install

# 3. Start your local server (from the find4 project root)
#    e.g. openresty, Python's http.server, or any static server on port 8080
python3 -m http.server 8080
# or: npx serve . -p 8080

# 4. Run all tests
npm test
```

---

## Targeting a different URL

```bash
BASE_URL=https://ffind4.org npm test
BASE_URL=http://localhost:9000   npm test
```

---

## Useful commands

| Command | What it does |
|---|---|
| `npm test` | Run all tests in headless mode |
| `npm run test:headed` | Watch tests run in a real browser |
| `npm run test:ui` | Playwright's interactive test explorer |
| `npm run test:debug` | Step through tests with the Playwright debugger |
| `npm run test:chromium` | Chromium only (fastest) |
| `npm run test:mobile` | Mobile Chrome + Mobile Safari only |
| `npm run test:report` | Open the last HTML report |
| `npm run test:ci` | GitHub Actions reporter (for CI) |

Run a single spec file:
```bash
npx playwright test tests/03-guessing.spec.js
```

Run tests matching a name pattern:
```bash
npx playwright test --grep "auto-solving"
```

---

## Project structure

```
find4-e2e/
├── playwright.config.js          # Browser projects, base URL, reporters
├── package.json
├── tests/
│   ├── fixtures/
│   │   └── game.fixture.js       # Shared selectors, GamePage helper, custom fixture
│   ├── 01-page-load.spec.js      # Initial load, grid render, config param
│   ├── 02-tile-selection.spec.js # Click/deselect, 4-word limit, shuffle
│   ├── 03-guessing.spec.js       # Correct groups, incorrect guesses, game over
│   ├── 04-toolbar-and-hints.spec.js  # Toolbar toggle, hints, keyboard shortcuts, modals
│   ├── 05-themes-page.spec.js    # themes.html — search, table rows, mobile cards
│   ├── 06-mobile.spec.js         # FAB, bottom sheet, touch interactions
│   ├── 07-persistence.spec.js    # localStorage: reload, high scores, clear
│   └── 08-accessibility.spec.js  # ARIA, lang attr, keyboard focus
└── playwright-report/            # Generated after a run
```

---

## Test design decisions

**Auto-solve for "correct path" tests (`03-guessing.spec.js`)**  
The grid is shuffled on every load, so hardcoding word lists would be fragile.
`Ctrl+Shift+S` exercises the real `solveGroup()` → `endGame()` path without depending
on a specific word order.

**Cross-group guess detection**  
Before submitting an incorrect guess the helper reads `data-category` from each tile
and only proceeds if the 4 tiles span more than one category — avoiding a false-correct
submission on the rare occasion the first 4 tiles happen to share a category.

**`GamePage` fixture class**  
`tests/fixtures/game.fixture.js` exports a custom `test` that injects a `gamePage`
helper into every test. Add your own domain actions there rather than repeating logic
across specs.

---

## CI integration (GitHub Actions)

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - name: Install deps
        run: cd find4-e2e && npm ci
      - name: Install Playwright browsers
        run: cd find4-e2e && npx playwright install --with-deps chromium
      - name: Start static server
        run: npx serve . -p 8080 &
      - name: Run E2E tests
        run: cd find4-e2e && npm run test:ci
        env:
          BASE_URL: http://localhost:8080
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: find4-e2e/playwright-report/
```

---

## Extending the suite

1. **New spec file** — add `tests/09-my-feature.spec.js`; import from the fixture:
   ```js
   const { test, expect, SEL } = require('./fixtures/game.fixture');
   ```

2. **New selector** — add it to `SEL` in `game.fixture.js` (single source of truth).

3. **New page helper** — add a method to the `GamePage` class in `game.fixture.js`.
