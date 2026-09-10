---
name: find4
description: >
    Generates Find4 game JSON from any text source — a URL, a local file, or piped stdin content.
    Find4 is a Connections-style word-grouping game (https://find4.org) where players
    find groups of 4 words that share a hidden theme. Use this skill whenever the user wants to:
    create a Find4 game, generate game content from a document or webpage, produce a game JSON
    file, analyse text into themed word groups, or populate the Find4 library. Also trigger
    when the user mentions "connections game", "word groups", "concept groups", or "game JSON",
    or uses vague phrasing like "make a game from this" or "turn this into something interactive"
    when a URL, file, or document is present.
---

# Find4 Game Generator

Generates a fully post-processed, drag-and-drop-ready JSON file for the Find4 game
(https://find4.org) from any text input: local file, URL, pasted text, or dropped file.

---

## ⚠️ CRITICAL — NO CUSTOM SCRIPTING. EVER.

**Never write your own Python, bash, or any other code to replicate what the Find4 scripts already do.**
This applies unconditionally to:

- Share URL / base64 encoding → **always use** `share_game.sh`
- Color fixing → **always use** `fix_colors.py`
- ID generation → **always use** `add_ids.py`
- Metadata finalization → **always use** `finalize_metadata.py`
- Library rebuilding → **always use** `generate_library_all.py`
- Splitting combined JSON → **always use** `game_split.py`

If a script call fails, fix the input and retry. Do not work around it with inline code.

---

## Step 0.1 — Resolve skill, script paths, references paths and IS_SANDBOX

**This is the very first thing to do — before presenting any plan or asking any question.**

Follow `references/script-paths.md` (hardcoded path because `$FIND4_REFERENCES` is not set yet) to set `$SKILL_DIR`, `$FIND4_SCRIPTS`, `$FIND4_REFERENCES`, `$RUNDIR` and create the output directories - **including the env-file persistence step it describes**, needed because `bash_tool` gives no shell state across calls.

⚠️ **Every `bash_tool` call is a fresh `/bin/sh` (`dash`) process: no exported variable, no `cd`, survives between calls, and `dash` has no `source` — only POSIX `.`.**

From this point on, **all script calls must use `$FIND4_SCRIPTS`**, never hardcoded paths.

From this point on, **all reference file paths must use `$FIND4_REFERENCES`**, never hardcoded paths.

From Step 1 onward, every command block must start by re-loading `$RUNDIR/.find4_env` via `. "<absolute path>/.find4_env"`. See `references/script-paths.md` for the exact pattern and the failure mode it prevents (a real prior bug where this caused an existing `dingdong.enc` to be reported as missing).

### Step 0.1 checklist

- [ ] `$FIND4_SCRIPTS` is set
- [ ] `$FIND4_REFERENCES` is set
- [ ] `$SKILL_DIR` is set
- [ ] `$SECRETS_STATUS` is set (set in Step 0.2 immediately below)

## Step 0.2 — Check for secrets file

Immediately after paths are resolved (Step 0.1 checklist is complete) check for the secrets file and set `$SECRETS_STATUS`:

```bash
if [ -n "$GITHUB_TOKEN" ]; then
    SECRETS_STATUS="ready"
elif [ -f "$FIND4_SCRIPTS/secrets/dingdong.enc" ]; then
    SECRETS_STATUS="passphrase required (will prompt below)"
else
    SECRETS_STATUS="skipped — no secrets file"
fi
```

---

## Step 0.3 — Confirm before starting

- [ ] Steps 0.1 and 0.2 must be complete

Any split JSON objects created will land in `output/games/<basename>/` not directly in `output/games/`

Determine:

- **Input source**: Will be one of URL, file path, attachment, or pasted text
- **game_count_max**: default `2` (user can override with `--game-count-max N`)
- **Output file**: `output/games/<suggested_name>.json`

Present the plan, using `$SECRETS_STATUS` (already set in Step 0.2) for the GitHub push line:

```
Generating <game_count_max> new games.

  Source        : <resolved source>
  Games         : <game_count_max> game set(s)
  Combined      : output/games/<expected filename or TBD>
  Split JSONs   : output/games/<basename>/<slug>.json (one per game set)
  HTML files    : output/games/html/<slug>.html (one per game set)
  HTML w files  : output/games/html/<slug>.w.html (one per game set)
  Screenshots   : output/games/screenshots/<slug>.html.png (one per game set)
  Zip           : output/<suggested_name>.zip
  GitHub push   : <GITHUB_REPO> → <GITHUB_BRANCH>  (<SECRETS_STATUS>)
```

**If `$SECRETS_STATUS` is `"passphrase required (will prompt below)"`**, ask for the passphrase immediately after presenting the plan — before saying anything else:

> "To push to GitHub I'll need your master passphrase. Please provide it now, or say 'skip' to skip the GitHub push."

Wait for the user's reply. If they say 'skip', note that Step 9 will be skipped and continue. Otherwise treat the reply as the passphrase and proceed to Step 0.4.

Once the passphrase is in hand (or GitHub push is confirmed skipped), proceed through all remaining steps **without pausing for further confirmation**.
Do NOT ask clarifying questions mid-run unless a hard error requires user input.

---

## Step 0.4 — Load secrets

**Do this immediately after the passphrase is received in Step 0.3** — before Step 1 begins. Step 0.1 has already resolved paths at this point; the passphrase was collected during the Step 0.3 confirmation exchange, so do not ask for it again here.

Follow `$FIND4_REFERENCES/secrets-loading.md` for the full procedure — checks, heredoc pattern, security rules, and failure handling.

---

## Step 1 — Resolve and fetch the input text

Select **one** of the following based on the user's message:

### URL

**URL** (`--url https://...` or a bare URL in the message):

Follow `$FIND4_REFERENCES/url-fetch-methods.md` to select the correct fetch method (wkhtmltopdf or WebFetch) and write the result to `output/tmp/find4_input.txt`.

### File

**File** (`--file path/to/file`, recognisable file path, or dropped attachment):

For plaintext files (`.txt`, `.md`, `.csv`, `.json`):

```bash
cp "<filepath>" output/tmp/find4_input.txt
```

For non-plaintext files (`.pdf`, `.docx`, `.html`, etc.), use the appropriate skill or tool to extract text first, then write it to `output/tmp/find4_input.txt`.

Verify the file exists before copying; if it doesn't, report and stop.

### Stdin / inline text

User has pasted raw text, or provided a topic with no file or URL.

Save to `output/tmp/find4_input.txt` using the `Write` tool. Also save a timestamped backup: `output/tmp/find4_input.<HUMANREADABLETIME>.txt`.

---

**After any of the above:** truncate to ~30,000 words if input exceeds that, and log a warning.
Record the source identifier (`<URL>`, `<filename>`, or `"stdin"`) — required for Step 5.

---

## Step 2 — Generate the game JSON

Read `output/tmp/find4_input.txt`. Reference `$FIND4_REFERENCES/schemas.md` for constraints and `$FIND4_REFERENCES/game.schema.json` for the exact JSON structure.

**Output ONLY valid JSON** — no prose, no markdown fences, no comments.

### Parameters

| Parameter        | Default                                                                | Override flag         |
| ---------------- | ---------------------------------------------------------------------- | --------------------- |
| `game_count_max` | `2`                                                                    | `--game-count-max N`  |
| `colors`         | `red`, `yellow`, `green`, `blue`, `purple`, `teal`, `orange`, `indigo` | fixed — do not change |
| `skill_levels`   | `Beginner`, `Intermediate`, `Advanced`, `Expert`                       | fixed                 |

Produce exactly `game_count_max` game_sets. Each `group_set` must have exactly 4 groups, each with exactly 4 unique words. Colors within a single `group_set` must all be different.

Write the raw JSON to `output/tmp/find4_raw.json` and a timestamped backup `output/tmp/find4_raw.<HUMANREADABLETIME>.json`.

**Validate before proceeding**: if the JSON is clearly malformed (missing brackets, truncated), regenerate once. If still invalid, report and stop.

---

## Step 3 — Fix colors

```bash
cat output/tmp/find4_raw.json | python3 $FIND4_SCRIPTS/fix_colors.py > output/tmp/find4_colored.json
```

On non-zero exit: inspect stderr, fix the input JSON, retry once. If it fails again, report and stop. Do not skip this step.

---

## Step 4 — Add IDs

```bash
cat output/tmp/find4_colored.json | python3 $FIND4_SCRIPTS/add_ids.py > output/tmp/find4_ids.json
```

Stamps `game_set_id`, `group_set_id`, and `group_item_id` throughout the hierarchy. On non-zero exit: report and stop.

---

## Step 5 — Finalize metadata

```bash
cat output/tmp/find4_ids.json | python3 $FIND4_SCRIPTS/finalize_metadata.py \
  --source "<source_identifier>" > output/tmp/find4_final.json
```

Adds `modified_at`, `source_id`, promotes `id_registry` into `metadata`, and generates a top-level hash ID. On non-zero exit: report and stop.

---

## Step 6 — Save, split, and present

Determine the output filename from `metadata.suggested_name` in the final JSON.
Fall back to `find4_game_<slug_of_theme>.json` if absent.

```bash
cp output/tmp/find4_final.json output/games/<output_filename>
```

inform the user what the actual value of `output/games/<output_filename>` is

### Step 6a — Widget (chat display, display only)

The widget HTML is generated by `generate_html.py --as-widget`, which writes a `.w.html` alongside the main HTML file. Render one `.f4-game` block per game set using the `show_widget` tool.

**The widget is display only.** Never embed share URLs anywhere in it — not in `href`, hidden `<span>` tags, or JS string literals. The `show_widget` tool has a ~10KB payload limit; share URLs alone (~2KB each) would push a two-game widget over the limit.

#### Platform rendering support

`show_widget` renders in an iframe. Support varies by platform:

| Platform                                      | Widget     | Screenshots                    | HTML files |
| --------------------------------------------- | ---------- | ------------------------------ | ---------- |
| claude.ai website (desktop or mobile browser) | ✅ renders | ✅                             | ✅         |
| Claude native iOS / Android app               | ❌ blank   | ❌ inline, use `present_files` | ✅         |

**Always** call `show_widget` regardless of platform — it works on the website. Then **always** also call `present_files` with the PNG screenshots and HTML files as a fallback.

After calling `show_widget`, tell the user which platform they're likely on and what to expect. Use this pattern:

- **If on claude.ai website**: "The preview above shows both games. Download the HTML files below to play."
- **If on native app** (no widget rendered, or user reports blank): "The inline widget doesn't render in the native app — use the files below to preview and play. Screenshots are attached."

If the user reports the widget is blank or empty, immediately follow up with `present_files` for the PNGs and HTML.

### Step 6b — Per-game-set standalone HTML files

Split the final JSON into per-theme files, generate share URLs, and produce standalone HTML.

The split files land in a subdirectory named after the combined JSON basename:
`output/games/<basename>/` (e.g. `output/games/ebpf-what-is-ebpf/`).

```bash
bash "${FIND4_SCRIPTS}/process_generated.sh"
```

#### ⚠️ CRITICAL — Share URL file I/O

See `$FIND4_REFERENCES/share-url-file-io-patterns.md` for the safe patterns and anti-patterns when handling share URLs.

#### Step 6b checklist

- [ ] `game_split.py` called on the combined JSON (never inline Python)
- [ ] Split JSONs land in `output/games/<basename>/` not directly in `output/games/`
- [ ] Share URL written to file via `share_game.sh` (never a variable)
- [ ] `generate_html.py` called for each split JSON
- [ ] One `.html` file per `game_set` in `output/games/html/`
- [ ] Widget contains no share URLs

In sandbox: copy HTML files to outputs and call `present_files`:

```bash
cp output/games/html/<slug>.html /mnt/user-data/outputs/<slug>.html
```

---

### Step 6c — Screenshot game cards as preview artifacts

For each standalone HTML file, capture the `.f4-game` card as a PNG.
Use the slugs from `output/tmp/split_paths.txt` written in Step 6b:

```bash
while IFS= read -r SPLIT_JSON; do
  SLUG=$(basename "$SPLIT_JSON" .json)
  python3 $FIND4_SCRIPTS/screenshot_game.py \
    --html output/games/html/${SLUG}.html \
    --output output/games/screenshots/${SLUG}.html.png
done < output/tmp/split_paths.txt
```

Backend auto-selected (no configuration needed):

| Environment                     | Backend                                                       |
| ------------------------------- | ------------------------------------------------------------- |
| macOS/Linux with Docker Desktop | `docker` — pulls `mcr.microsoft.com/playwright:v1.56.0-jammy` |
| Claude sandbox / CI (no Docker) | `local` — uses pre-installed `playwright` Python package      |
| Override                        | `--backend docker\|local\|auto`                               |

This step is **non-critical** — if it fails, skip and continue with HTML files.

In sandbox: copy PNGs to outputs and call `view` on each for inline rendering:

```bash
while IFS= read -r SPLIT_JSON; do
  SLUG=$(basename "$SPLIT_JSON" .json)
  cp output/games/screenshots/${SLUG}.html.png /mnt/user-data/outputs/${SLUG}.html.png
done < output/tmp/split_paths.txt
```

Then call `present_files` with all `.html` and `.png` paths.

#### Step 6c checklist

- [ ] `screenshot_game.py` called once per game set
- [ ] One `.html.png` per game set in `output/games/screenshots/`
- [ ] In sandbox: PNG copied to `/mnt/user-data/outputs/`
- [ ] `present_files` called with all HTML and PNG outputs

---

## Step 7 — Rebuild the library index

`generate_library_all.py` runs in two passes:

- **Pass 1** scans `--games-dir` and writes `themes.json` (the lightweight index).
- **Pass 2** reads `themes.json` and assembles `library.json` (full word data). For each entry it resolves `config_file` as `library_root / "library/<parent_stem>/<slug>.json"` — so the split JSONs must be copied there first.

```bash
# Derive parent stem from metadata (safer than globbing output/games/ which may have multiple JSONs)
COMBINED_BASENAME=$(python3 -c "import json; m=json.load(open('output/tmp/find4_final.json'))['metadata']; print(m['suggested_name'].replace('.json',''))")

# Pre-copy: resolve_config_path needs split JSONs at output/library/<parent_stem>/
mkdir -p "output/library/${COMBINED_BASENAME}"
cp output/tmp/find4_final/*.json "output/library/${COMBINED_BASENAME}/"

python3 "$FIND4_SCRIPTS/generate_library_all.py" \
  --games-dir output/tmp/find4_final \
  --config-dir output/library \
  --output-dir output/library \
  --library-root output \
  --trigger "find4-skill" \
  --force
```

**Why these args:**

| Arg              | Value                    | Reason                                                                                  |
| ---------------- | ------------------------ | --------------------------------------------------------------------------------------- |
| `--games-dir`    | `output/tmp/find4_final` | Split JSONs to scan (Step 1 input)                                                      |
| `--config-dir`   | `output/library`         | Where `themes.json` is written                                                          |
| `--output-dir`   | `output/library`         | Where `library.json` is written (must match `--config-dir` or it defaults to `config/`) |
| `--library-root` | `output`                 | Step 2 resolves `config_file` as `library_root/library/<parent_stem>/<slug>.json`       |

Do **not** use `--library-dir` — it is a suppressed alias for `--games-dir` and does not appear in `--help`.

Both outputs are critical — on non-zero exit log a warning and continue. Safe to re-run at any time. Pass `--themes-only` to skip the `library.json` step.

### Step 7.1 — Present published short links

After `library/themes.json` has been rebuilt in Step 7 WE MUST look up `.short_link` and `.short_path`.
These values are used to populate the `ui-widget-short-link.html.md` widget - VERY IMPORTANT.

⚠️ **Step 7.1 must complete before Step 8.** The card widget HTML and its screenshot are included in
the zip. Generate and screenshot the card widget here, then proceed to Step 8.

The card widget covers all game sets in one file, so its filename is derived from `$COMBINED_BASENAME`
(already in scope from Step 7), not a per-game slug:

- HTML: `output/games/html/${COMBINED_BASENAME}.card.html`
- Screenshot: `output/games/screenshots/${COMBINED_BASENAME}.card.html.png`

Follow `$FIND4_REFERENCES/ui-widget-short-link.html.md` for the card widget layout, writing the HTML to
`output/games/html/${COMBINED_BASENAME}.card.html`.

Screenshot it using `screenshot_game.py`, targeting the `.f4-cards` element via `--element`:

```bash
python3 "$FIND4_SCRIPTS/screenshot_game.py" \
  --html "output/games/html/${COMBINED_BASENAME}.card.html" \
  --output "output/games/screenshots/${COMBINED_BASENAME}.card.html.png" \
  --element ".f4-cards"
```

In sandbox: copy both to outputs:

```bash
cp "output/games/html/${COMBINED_BASENAME}.card.html" \
   "/mnt/user-data/outputs/${COMBINED_BASENAME}.card.html"
cp "output/games/screenshots/${COMBINED_BASENAME}.card.html.png" \
   "/mnt/user-data/outputs/${COMBINED_BASENAME}.card.html.png"
```

Examine fields:

```bash
cat output/library/themes.json | jq -r '.[] | "\(.game_set_id) \(.short_link) \(.short_path)"'
```

Data mapping from each `library/themes.json` entry:

| Widget element         | Field                                       |
| ---------------------- | ------------------------------------------- |
| `f4-card-title`        | `theme`                                     |
| `f4-link-short` href   | `https://find4.org/?` + `short_link`        |
| `f4-link` (plain) href | `https://find4.org/?config=` + `short_path` |

Render one card per game round (two cards for the default two-game-set output).

---

## Step 8 — Zip output files

Follow `$FIND4_REFERENCES/find4-step8-zip.md` for the full procedure.

---

## Step 9 — Push output to GitHub

⚠️ **Read `$FIND4_REFERENCES/find4-step9-github-push.md` in full before writing any bash.**
Do not reconstruct the Step 9 heredoc from memory — copy the patterns verbatim from the reference.
In particular: never add `set -euo pipefail` to the Step 9 heredoc, and always use the two-line
`RAND6` pattern for the scratch branch name. Both errors have occurred when the reference was skipped.

---

Follow `$FIND4_REFERENCES/find4-step9-github-push.md` for the full procedure.

## Error handling

See `$FIND4_REFERENCES/error-handling-matrix.md`.

---

## Notes

**Why two game_sets by default?** LLM output for complex structured JSON can be unreliable for large outputs. Two game_sets gives a good payload while keeping quality high. Request more with `--game-count-max N`.

**Color palette** — `fix_colors.py` enforces valid colors. Do not skip step 3.

**IDs are content-addressed** — the same content always produces the same IDs, enabling safe deduplication across JSON files in the library.

**Tmp directory** — all intermediate files land in `output/tmp/`. Timestamped backups allow manual recovery if a later step fails.
