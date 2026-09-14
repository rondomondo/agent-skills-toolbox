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
- Splitting combined JSON → **always use** `game_split.py` (via `process_generated.sh`)

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
- **Output file**: `output/games/<suggested_name>/<suggested_name>.json`

Present the plan, using `$SECRETS_STATUS` (already set in Step 0.2) for the GitHub push line:

```
Generating <game_count_max> new games.

  Source        : <resolved source>
  Games         : <game_count_max> game set(s)
  Combined      : output/games/<basename>/<basename>.json
  Split JSONs   : output/games/<basename>/<slug>.json (one per game set)
  HTML files    : output/games/<basename>/html/<slug>.html (one per game set)
  HTML w files  : output/games/<basename>/html/<slug>.w.html (one per game set)
  Screenshots   : output/games/<basename>/screenshots/<slug>.html.png (one per game set)
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

**Each game_set must have a unique `theme` string.** If two game_sets share a theme, `game_split.py` will overwrite the first with the second. Use descriptive subtitles to differentiate: e.g. `"Linux — Commands & Tools"` and `"Linux — Concepts & Architecture"`.

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

## Step 6 — Save combined JSON

Derive the combined output path from `metadata.suggested_name`. The combined JSON always lands inside its own subdirectory: `output/games/<basename>/<basename>.json`.

```bash
# Derive basename from metadata (safer than globbing output/games/ which may have multiple JSONs)
parent_stem=$(python3 -c "import json; m=json.load(open('output/tmp/find4_final.json'))['metadata']; print(m['suggested_name'].replace('.json',''))")
# Fall back to a slug derived from the first game_set theme if suggested_name is absent
if [ -z "$parent_stem" ]; then
  parent_stem=$(python3 -c "import json,re; gs=json.load(open('output/tmp/find4_final.json'))['game_sets'][0]; t=gs['theme']; print(re.sub(r'[^a-z0-9]+','-',t.lower()).strip('-'))")
fi

mkdir -p "output/games/${parent_stem}"
cp output/tmp/find4_final.json "output/games/${parent_stem}/${parent_stem}.json"
```

The combined file is always `output/games/${parent_stem}/${parent_stem}.json` — never directly under `output/games/`.

Inform the user of the resolved path.

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

### Step 6b — Split, share URLs, and standalone HTML

`process_generated.sh` does everything in one call: splits the combined JSON into per-game-set files (writing them beside the combined JSON in `output/games/<basename>/`), generates share URLs, and produces standalone HTML.

```bash
FINAL_JSON="$RUNDIR/output/tmp/find4_final.json" \
  bash "${FIND4_SCRIPTS}/process_generated.sh"
```

**What it does internally:**
1. Reads `output/tmp/find4_final.json` to derive `parent_stem`
2. Calls `game_split.py` on `output/games/<parent_stem>/<parent_stem>.json` — split JSONs land beside it in `output/games/<parent_stem>/`
3. For each split JSON: runs `share_game.sh`, then `generate_html.py --as-widget`

#### ⚠️ CRITICAL — Share URL file I/O

See `$FIND4_REFERENCES/share-url-file-io-patterns.md` for the safe patterns and anti-patterns when handling share URLs.

#### Step 6b checklist

- [ ] `process_generated.sh` called with `FINAL_JSON` set
- [ ] Split JSONs land in `output/games/<basename>/` beside the combined JSON
- [ ] Share URL written to file via `share_game.sh` (never a variable)
- [ ] `generate_html.py` called for each split JSON
- [ ] One `.html` and one `.w.html` per game_set in `output/games/<basename>/html/`
- [ ] Widget contains no share URLs

In sandbox: copy HTML files to outputs and call `present_files`:

```bash
cp output/games/<basename>/html/<slug>.html /mnt/user-data/outputs/<slug>.html
```

---

### Step 6c — Screenshot game cards as preview artifacts

For each split JSON, capture the `.f4-game` card as a PNG.

```bash
mkdir -p "output/games/${parent_stem}/screenshots"
for split_json in output/games/${parent_stem}/*.json; do
  # Skip the combined JSON
  basename_json=$(basename "$split_json" .json)
  [ "$basename_json" = "$parent_stem" ] && continue
  python3 "$FIND4_SCRIPTS/screenshot_game.py" \
    --html "output/games/${parent_stem}/html/${basename_json}.html" \
    --output "output/games/${parent_stem}/screenshots/${basename_json}.html.png"
done
```

Backend auto-selected (no configuration needed):

| Environment                     | Backend                                                        |
| ------------------------------- | -------------------------------------------------------------- |
| macOS/Linux with Docker Desktop | `docker` — pulls `mcr.microsoft.com/playwright:v1.56.0-jammy` |
| Claude sandbox / CI (no Docker) | `local` — uses pre-installed `playwright` Python package       |
| Override                        | `--backend docker\|local\|auto`                                |

This step is **non-critical** — if it fails, skip and continue with HTML files.

In sandbox: copy PNGs to outputs:

```bash
for png in output/games/${parent_stem}/screenshots/*.html.png; do
  cp "$png" /mnt/user-data/outputs/
done
```

Then call `present_files` with all `.html` and `.png` paths.

#### Step 6c checklist

- [ ] `screenshot_game.py` called once per split JSON (combined JSON skipped)
- [ ] One `.html.png` per game_set in `output/games/<basename>/screenshots/`
- [ ] In sandbox: PNG copied to `/mnt/user-data/outputs/`
- [ ] `present_files` called with all HTML and PNG outputs

---

## Step 7 — Rebuild the library index

`generate_library_all.py` runs in two passes:

- **Pass 1** scans `--games-dir` and writes `themes.json` (the lightweight index).
- **Pass 2** reads `themes.json` and assembles `library.json` (full word data). For each entry it resolves `config_file` as `library_root / "library/<parent_stem>/<slug>.json"` — so the split JSONs must be copied there first.

```bash
# Split JSONs are now in output/games/${parent_stem}/ alongside the combined JSON.
# Pre-copy split JSONs to output/library/<parent_stem>/ for Pass 2 resolution.
mkdir -p "output/library/${parent_stem}"
for split_json in output/games/${parent_stem}/*.json; do
  basename_json=$(basename "$split_json" .json)
  [ "$basename_json" = "$parent_stem" ] && continue  # skip combined
  cp "$split_json" "output/library/${parent_stem}/"
done

python3 "$FIND4_SCRIPTS/generate_library_all.py" \
  --games-dir "output/games/${parent_stem}" \
  --config-dir output/library \
  --output-dir output/library \
  --library-root output \
  --trigger "find4-skill" \
  --force
```

**Why these args:**

| Arg              | Value                             | Reason                                                                                   |
| ---------------- | --------------------------------- | ---------------------------------------------------------------------------------------- |
| `--games-dir`    | `output/games/${parent_stem}`     | Where split JSONs now live (alongside the combined)                                      |
| `--config-dir`   | `output/library`                  | Where `themes.json` is written                                                           |
| `--output-dir`   | `output/library`                  | Where `library.json` is written (must match `--config-dir` or it defaults to `config/`) |
| `--library-root` | `output`                          | Pass 2 resolves `config_file` as `library_root/library/<parent_stem>/<slug>.json`        |

Do **not** use `--library-dir` — it is a suppressed alias for `--games-dir` and does not appear in `--help`.

⚠️ **`generate_library_all.py` uses a flat `glob("*.json")` — it does not recurse into subdirectories.**
`--games-dir` must point directly at the directory containing the split JSONs, not a parent of it.

⚠️ **`short_path` fix required after every `generate_library_all.py` run.**
The script computes `short_path` as `games/<filename>` (relative to `--games-dir`), which is correct
only when `--games-dir` is flat. Since split JSONs live inside a `<parent_stem>/` subdir, the generated
`short_path` will be `games/<slug>.json` instead of the correct `games/<parent_stem>/<slug>.json`.
Patch it immediately after the run:

```bash
python3 - << 'PYEOF'
import json
from pathlib import Path

themes_path = Path("output/library/themes.json")
themes = json.loads(themes_path.read_text(encoding="utf-8"))

for entry in themes:
    config_file = entry.get("config_file", "")
    if config_file.startswith("library/"):
        rest = config_file[len("library/"):]           # <parent_stem>/<slug>.json
        correct_short_path = f"games/{rest}"           # games/<parent_stem>/<slug>.json
        entry["short_path"] = correct_short_path
        # Recompute short_link (FNV-1a 32-bit)
        h = 2166136261
        for ch in correct_short_path:
            h ^= ord(ch)
            h = (h * 16777619) & 0xFFFFFFFF
        entry["short_link"] = f"ff-{h:08x}"

themes_path.write_text(json.dumps(themes, indent=2, ensure_ascii=False), encoding="utf-8")
print("themes.json short_path patched")
for e in themes:
    print(f"  {e['game_set_id']}  {e['short_link']}  {e['short_path']}")
PYEOF
```

Then rebuild `library.json` from the patched `themes.json` without re-running the scan:

```bash
python3 - << 'PYEOF'
import sys, types, json
from pathlib import Path
import importlib.machinery

loader = importlib.machinery.SourceFileLoader("gla", str(Path(sys.argv[1])))
mod = types.ModuleType("gla")
loader.exec_module(mod)

library = mod.build_full_library(
    themes_path=Path("output/library/themes.json"),
    library_root=Path("output"),
    trigger="find4-skill",
    themes_data=None,
)
Path("output/library/library.json").write_text(
    json.dumps(library, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(f"library.json rebuilt: {len(library.get('game_sets', []))} game_sets")
PYEOF
```

Pass `$FIND4_SCRIPTS/generate_library_all.py` as `sys.argv[1]` when calling the above.

Both outputs are critical — on non-zero exit log a warning and continue. Safe to re-run at any time.

### Step 7.1 — Present published short links

After `library/themes.json` has been rebuilt and patched in Step 7 WE MUST look up `.short_link` and `.short_path`.
These values are used to populate the `ui-widget-short-link.html.md` widget - VERY IMPORTANT.

⚠️ **Step 7.1 must complete before Step 8.** The card widget HTML and its screenshot are included in
the zip. Generate and screenshot the card widget here, then proceed to Step 8.

The card widget covers all game sets in one file, so its filename is derived from `$parent_stem`
(already in scope from Step 6), not a per-game slug:

- HTML: `output/games/${parent_stem}/html/${parent_stem}.card.html`
- Screenshot: `output/games/${parent_stem}/screenshots/${parent_stem}.card.html.png`

Follow `$FIND4_REFERENCES/ui-widget-short-link.html.md` for the card widget layout, writing the HTML to
`output/games/${parent_stem}/html/${parent_stem}.card.html`.

Screenshot it using `screenshot_game.py`, targeting the `.f4-cards` element via `--element`:

```bash
mkdir -p "output/games/${parent_stem}/screenshots"
python3 "$FIND4_SCRIPTS/screenshot_game.py" \
  --html "output/games/${parent_stem}/html/${parent_stem}.card.html" \
  --output "output/games/${parent_stem}/screenshots/${parent_stem}.card.html.png" \
  --element ".f4-cards"
```

In sandbox: copy both to outputs:

```bash
cp "output/games/${parent_stem}/html/${parent_stem}.card.html" \
   "/mnt/user-data/outputs/${parent_stem}.card.html"
cp "output/games/${parent_stem}/screenshots/${parent_stem}.card.html.png" \
   "/mnt/user-data/outputs/${parent_stem}.card.html.png"
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

**Unique themes are required.** `game_split.py` derives the output filename from the theme slug. Two game_sets with identical themes produce the same slug — the second overwrites the first. Always use distinct, descriptive theme strings.

**Color palette** — `fix_colors.py` enforces valid colors. Do not skip step 3.

**IDs are content-addressed** — the same content always produces the same IDs, enabling safe deduplication across JSON files in the library.

**Tmp directory** — intermediate files land in `output/tmp/`. Timestamped backups allow manual recovery if a later step fails.
