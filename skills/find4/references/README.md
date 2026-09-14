# Find4

A Connections-style word-grouping game where players find 4 groups of 4 words that share a hidden theme. Useful as an educational tool for any topic — generate a game from any article, document, or URL in seconds.

**Live app**: https://find4.org

---

## How to play

1. Open the app and load a game (drag-and-drop a JSON file, use the Library, or open a share link).
2. You see 16 words. Find the 4 groups of 4 that share a hidden connection.
3. Select 4 tiles and submit — the group reveals its category, description, and reference links.
4. Complete all 4 groups to win.

---

## Generating a game

Games are described by a single JSON file. Use Claude Code with the `find4` skill to generate one from any source:

```
# From a URL
/find4 https://example.com/some-article

# From a local file
/find4 --file path/to/notes.txt

# From pasted text
/find4
<paste your text>
```

Claude will:
1. Analyse the content and produce themed word groups
2. Run the post-processing pipeline (color assignment, IDs, metadata)
3. Save the result to `games/<name>.json`
4. Print a **share link** you can open directly in the browser

### Share links


After generation, Claude prints a URL of the form:

```
https://find4.org/#game=<base64>
```

And also a set of cards to play immediatly like 

[examples/back-in-my-day.html](https://find4.org/examples/back-in-my-day.html)

[examples/a-lovely-cup-of-tea.html](https://find4.org/examples/a-lovely-cup-of-tea.html)

[examples/distributed-systems-observability.html](https://find4.org/examples/distributed-systems-observability.html)

[examples/developer-tooling-platform-engineering.html](https://find4.org/examples/developer-tooling-platform-engineering.html)


Open it to play immediately — no file needed. Generate one manually:

```bash
bash scripts/share-game.sh games/my-game.json
```

---

## Development

### Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
make install
```

### Local dev server

```bash
make serve          # builds, copies to local/, serves on http://localhost:8080
```

Changes to JS/CSS/HTML trigger an automatic server restart.

#### Self-signed certificate warning (Chrome)

If the local server uses HTTPS with a self-signed cert and Chrome shows an HSTS or SSL error, simply focus the browser window and type `thisisunsafe` (no input field needed). Chrome will bypass the error and load the page.

### Build

```bash
make bundle         # combine JS + CSS (no minification)
make release        # minify + rebuild library index
```

### Tests

```bash
make test           # Python unit tests with coverage
make e2e            # Playwright end-to-end tests (requires Docker)
```

### Code quality

```bash
make format         # black + isort
make lint           # ruff + mypy
make ci             # lint + test
```

---

## Project layout

```
games/              ← game JSON files (source of truth)
config/             ← default.json defaults games index (derived, rebuild with make librarygen)
library/            ← themes.json and library.json = full library index (derived, rebuild with make librarygen - generate_library_all.py)
                      library files layout example like below
                      world-cup-facts
                      world-cup-facts.json
                      world-cup-facts/fifa-world-cup-trivia.json
                      world-cup-facts/world-cup-nations-and-records.json
                      
js/                 ← frontend JavaScript source
css/                ← frontend CSS source
dist/               ← bundled/minified output (gitignored)
scripts/            ← share-game.sh, generate_library_all.py and other utilities
tests/              ← Python unit tests + Playwright e2e tests
```

### Post-processing pipeline

Raw LLM JSON passes through three scripts before being saved:

```
fix_colors.py → add_ids.py → finalize_metadata.py → games/<name>.json
                                                           ↓
                                               generate_library_all.py → library/themes.json + library/library.json
```

See [`skills/find4/scripts/README.md`](skills/find4/scripts/README.md) for full pipeline documentation

