# Find4 Post-Processing Scripts

These scripts form the post-processing pipeline that transforms raw LLM-generated JSON
into a fully enriched, frontend-ready Find4 game files. They are also used as standalone
tools for validation and library management.

---

## What is Find4?

Find4 is a Connections style word grouping game hosted at https://find4.org

Players are presented with 16 words or short phrases, and must find 4 groups of 4 that
share a common connection or theme. Each group is colour coded and has an assigned difficulty
level for the topic.

The game is entirely data driven: every game, every round and every group is described
by a single JSON file. These scripts beng described exist to reliably produce, process and use
those files.

---

## JSON Object Structure

A fully post-processed game file has this shape:

```
{root}
├-- metadata              <- provenance and fingerprint of the whole file
├-- game_sets[]           <- one or more independent games (different themes)
│   └-- group_sets[][]    <- rounds within a game (each round = one 16-word board)
│       └-- group{}       <- one colour block of 4 words
└-- id_registry           <- flat lookup of all IDs (mirrors metadata.id_registry)
```

### Top level

```json
{
  "metadata": { ... },
  "game_sets": [ ... ],
  "id_registry": { ... }
}
```

| Field         | Type   | Description |
|---------------|--------|-------------|
| `metadata`    | object | Provenance, timestamps, IDs, source info |
| `game_sets`   | array  | One entry per independent game/theme |
| `id_registry` | object | Top-level copy of `metadata.id_registry` for fast frontend lookup |

---

### `metadata`

```json
"metadata": {
  "generated_at": "2026-05-06T11:00:00Z",
  "source": "https://example.com/article",
  "suggested_name": "linux-booting-concepts.json",
  "modified_at": "2026-05-06T21:32:36.273019",
  "source_id": "https://example.com/article",
  "step": "finalize_metadata",
  "promoted": true,
  "id_registry": {
    "group_set_ids": ["f50e540921cc", ...],
    "game_set_ids":  ["029399d4a35c", ...],
    "group_item_ids": ["039063a3d0f0", ...]
  },
  "id": "xGs5JACqTNLQFdDr"
}
```

| Field            | Set by              | Description |
|------------------|---------------------|-------------|
| `generated_at`   | LLM (step 2)        | ISO timestamp when the raw JSON was generated |
| `source`         | LLM (step 2)        | Human-readable origin (URL, filename, "stdin") |
| `suggested_name` | LLM (step 2)        | Kebab-case filename to save the file as |
| `modified_at`    | `finalize_metadata` | ISO timestamp of the finalization pass |
| `source_id`      | `finalize_metadata` | Same as `--source` arg; used for traceability |
| `step`           | `finalize_metadata` | Marks which script last touched the file |
| `promoted`       | `finalize_metadata` | `true` once `id_registry` has been moved into metadata |
| `id_registry`    | `finalize_metadata` | All IDs collected by `add_ids.py`, promoted here |
| `id`             | `finalize_metadata` | URL-safe base64 hash of the full payload (unique fingerprint) |

---

### `game_sets[]`

Each entry in `game_sets` represents one independent game with its own theme.
A single JSON file typically contains 2 game sets (the default), though the LLM can
produce more with `--game-count-max N`.

```json
{
  "theme": "Linux -- Booting and Init Systems",
  "game_set_id": "029399d4a35c",
  "group_sets": [ [...], [...] ]
}
```

| Field         | Type   | Description |
|---------------|--------|-------------|
| `theme`       | string | Human-readable description of the game's subject |
| `game_set_id` | string | 12-char hex ID (added by `add_ids.py`) |
| `group_sets`  | array  | List of rounds; each round is an array of 4 groups |

---

### `group_sets[][]` -- rounds

`group_sets` is an array of arrays. Each inner array is one *round* -- a single 16-word
board that the player sees at once. A game typically has 2 rounds (2 inner arrays),
giving the player 2 progressively different views of the same theme.

```json
"group_sets": [
  [ group, group, group, group ],   <- round 1: beginner-friendly board
  [ group, group, group, group ]    <- round 2: harder board
]
```

---

### `group{}` -- one colour block

This is the core unit. Each group represents a category of 4 words that share a hidden
connection. It appears as one coloured tile on the game board.

```json
{
  "words": ["SUSHI", "RAMEN", "GYOZA", "MATCHA"],
  "category": "Japanese Food",
  "color": "red",
  "url": "https://www.japan.travel/en/guide/japanese-food/",
  "description": "Classic dishes and drinks from Japanese cuisine",
  "skill_level": "Beginner",
  "additional_sources": [
    "https://www.justonecookbook.com/",
    "https://www.bbc.co.uk/food/cuisines/japanese"
  ],
  "theme": "Food -- Cuisines, Cooking and Ingredients",
  "group_item_id": "039063a3d0f0",
  "group_set_id": "f50e540921cc"
}
```

| Field               | Type            | Constraints | Description |
|---------------------|-----------------|-------------|-------------|
| `words`             | array of string | Exactly 4   | The words/phrases shown on tiles |
| `category`          | string          | --          | The hidden category name (revealed on correct guess) |
| `color`             | string          | See palette | Visual colour for this group's tiles |
| `url`               | string          | Valid URL   | Primary reference for this category |
| `description`       | string          | --          | One-sentence explanation of the connection |
| `skill_level`       | string          | See levels  | Difficulty indicator |
| `additional_sources`| array of string | 2-3 URLs    | Extra reading/reference links |
| `theme`             | string          | --          | Copy of the parent `game_set.theme` (denormalised for frontend access) |
| `group_item_id`     | string          | 12 hex      | Content-addressed ID (added by `add_ids.py`) |
| `group_set_id`      | string          | 12 hex      | ID of the round this group belongs to (added by `add_ids.py`) |

**Colour palette** (exactly one per group; all 4 in a round must be distinct):

```
red  blue  green  yellow  orange  indigo  purple  teal
```

**Skill levels:**

```
Beginner  Intermediate  Advanced  Expert
```

---

### `id_registry`

A flat index of every ID present in the file, duplicated at the top level and inside
`metadata`. The frontend uses it to resolve any ID without traversing the full tree.

```json
"id_registry": {
  "group_set_ids":  ["f50e540921cc", "8401b9c8aeb1"],
  "game_set_ids":   ["029399d4a35c"],
  "group_item_ids": ["039063a3d0f0", "ab1ef956d27d", ...]
}
```

---

## ID Design and Purpose

IDs are **content-addressed** 12-character lowercase hex strings generated by MD5-hashing
the content that defines that entity:

| ID type        | Hashed from |
|----------------|-------------|
| `group_item_id`| `category + sorted(words) + color + description` |
| `group_set_id` | All group items' hash content joined |
| `game_set_id`  | Theme + all group_set hash content |

**Why content-addressed?**

- The same group appearing in two different files always gets the same `group_item_id`.
- This makes cross-file deduplication safe and deterministic.
- The frontend can track player progress (which groups they've solved) using stable IDs
  even if the file is regenerated or moved.
- `generate_library_all.py` uses `game_set_id` to deduplicate across all the json files in
  the `games/` directory.

**The file-level `metadata.id`** is different -- it is a MurmurHash128 (or SHA-256 fallback)
of the entire serialised payload, encoded as URL-safe base64. It changes whenever
*anything* in the file changes, so it works as a cache-busting fingerprint.

---

## The Post-Processing Pipeline

Raw LLM output goes through three scripts in sequence before being saved:

```
LLM output (raw JSON)
      │
      ▼
fix_colors.py        <- step 1: enforce valid, distinct colours per round
      │
      ▼
add_ids.py           <- step 2: stamp game_set_id, group_set_id, group_item_id + id_registry
      │
      ▼
finalize_metadata.py <- step 3: add modified_at, source_id, promote id_registry, hash id
      │
      ▼
games/<name>.json    <- saved game file (frontend-ready)
      │
      ▼
generate_library_all.py  <- step 4: rebuild library/themes.json + library/library.json
      │
      ▼  (--create-meta)
results/meta.json    <- step 5 (opt-in): combined meta for publish workflow email
results/<slug>/<stem>.meta.json  <- one file per game set
```

One-liner full pipeline:

```bash
cat output/tmp/find4_raw.json \
  | python3 fix_colors.py \
  | python3 add_ids.py \
  | python3 finalize_metadata.py --source "https://example.com" \
  > games/my-game.json

python3 generate_library_all.py \
  --games-dir ./games --output-dir ./library --library-root . --force

# optionally regenerate results/meta.json at the same time
python3 generate_library_all.py \
  --games-dir ./games --output-dir ./library --library-root . \
  --themes-only --create-meta --meta-dir results \
  --meta-source-id "https://example.com" --meta-zip my-topic --force
```

---

## Scripts Reference

### `fix_colors.py` -- Step 1

Enforces the colour invariants across every round. Pass-through if already valid;
assigns the first 4 palette colours positionally if not.

```bash
# stdin -> stdout (pipeline)
cat output/tmp/find4_raw.json | python3 fix_colors.py > output/tmp/find4_colored.json

# file input
python3 fix_colors.py --game-set-json output/tmp/find4_raw.json > output/tmp/find4_colored.json

# check whether a file needs fixing (diff is empty if clean)
python3 fix_colors.py --game-set-json my_game.json | diff my_game.json -
```

---

### `add_ids.py` -- Step 2

Walks the hierarchy and stamps IDs at every level. Also writes `id_registry` at the
root. Idempotent -- re-running on a file that already has IDs produces the same IDs.

```bash
# stdin -> stdout (pipeline)
cat output/tmp/find4_colored.json | python3 add_ids.py > output/tmp/find4_ids.json

# file input
python3 add_ids.py --game-set-json output/tmp/find4_colored.json > output/tmp/find4_ids.json
```

---

### `finalize_metadata.py` -- Step 3

The last enrichment pass. Must be run after `add_ids.py` so `id_registry` is present
to promote. Always provide `--source` so the file's origin is recorded.

```bash
# from a URL source
cat output/tmp/find4_ids.json \
  | python3 finalize_metadata.py --source "https://example.com/article" \
  > output/tmp/find4_final.json

# from a file source, using file input flag
python3 finalize_metadata.py \
  --game-set-json output/tmp/find4_ids.json \
  --source "my-notes.txt" \
  > output/tmp/find4_final.json

# when source was pasted text
cat output/tmp/find4_ids.json | python3 finalize_metadata.py --source stdin > games/my-game.json
```

---

### `validate.py` -- Standalone validator

Two modes: default (structural only) and `--strict` (also requires IDs and metadata).
Exits 0 on success, 1 on any error. Errors go to stderr; summary to stdout.

```bash
# validate a finished game file (requires IDs + metadata)
python3 validate.py --game-set-json config/default.json --strict

# validate raw LLM output before the pipeline
cat output/tmp/find4_raw.json | python3 validate.py

# use as a gate in a pipeline -- stops if invalid
cat raw.json | python3 validate.py && echo "OK, continuing..."

# validate every saved game in bulk
for f in games/*.json; do
  python3 scripts/validate.py --game-set-json "$f" --strict || echo "FAILED: $f"
done

```

---

### `generate_library_all.py` -- Library builder (themes + full library + meta)

Scans `games/` and writes `library/themes.json` (compact index) then `library/library.json`
(full word data). The Find4 frontend fetches `themes.json` to populate the Library panel
(in `themes.html`), and then `library/library.json` to load complete game data.

With `--create-meta` it also writes `results/meta.json` and one
`results/<slug>/<stem>.meta.json` per game set -- the format consumed by the publish
workflow to populate the success email.

```bash
# standard rebuild after adding a new game (writes both library files)
python3 generate_library_all.py \
  --games-dir ./games --output-dir ./library --library-root . --force

# themes.json only -- skip library.json
python3 generate_library_all.py \
  --games-dir ./games --output-dir ./library --themes-only --force

# rebuild with randomised word order (for shuffle mode)
python3 generate_library_all.py \
  --games-dir ./games --output-dir ./library --shuffle --force

# also regenerate results/meta.json and per-game meta files
python3 generate_library_all.py \
  --games-dir ./games --output-dir ./library --library-root . \
  --themes-only --create-meta --meta-dir results \
  --meta-source-id stdin --meta-zip my-topic --force

# override the base URL (defaults to FIND4_BASE_URL env var or https://find4.org)
python3 generate_library_all.py \
  --games-dir ./games --output-dir ./library --library-root . \
  --themes-only --create-meta --meta-dir results \
  --base-url https://staging.find4.org --force

# inspect validation errors without writing output
python3 generate_library_all.py --games-dir ./games --output-dir ./library 2>&1
```

All output files are **derived artifacts** -- delete them and rebuild with `--force` at
any time. The individual `games/*.json` files are always the source of truth.

**`--create-meta` flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--meta-dir DIR` | `results` | Root output directory for meta files |
| `--base-url URL` | `$FIND4_BASE_URL` or `https://find4.org` | Base URL for short_url and path_url |
| `--meta-source-id TEXT` | `""` | Populates `source_id` in `results/meta.json` |
| `--meta-zip NAME` | `""` | Populates `zip` in `results/meta.json` |

---

## File Lifecycle

```
games/
└-- linux-booting-concepts.json     <- canonical source of truth
config/
└-- default.json                    <- default index
library/
└-- themes.json                     <- derived games index - rebuilt by generate_library_all.py
└-- library.json                    <- full information on all games - rebuilt by generate_library_all.py
output/tmp/
├-- find4_input.txt                 <- resolved input text
├-- find4_raw.json                  <- raw LLM output (step 2)
├-- find4_colored.json              <- after fix_colors.py (step 3)
├-- find4_ids.json                  <- after add_ids.py (step 4)
└-- find4_final.json                <- after finalize_metadata.py (step 5)
```

Timestamped backups (`find4_raw.20260506-213200.json`) are written at each step so
any intermediate state can be recovered if a later step fails.

---

## How the Frontend Uses These Files

The Find4 frontend is a static single-page app. It loads game data in two ways:

1. **Library panel**: fetches `library/themes.json` to list available games. Each entry
   contains summary metadata (theme, word count, skill levels, short_link) and the
   `short_path` , which is the path to the games json to load on demand.
   No full game data is fetched until the player selects a game.

2. **Direct load**: the player drags and drops a `games/*.json` file directly onto the
   app. The frontend reads the file client-side -- no server required.

The frontend tracks player progress using `game_set_id` and `group_item_id` stored in
`localStorage`. Because these IDs are content-addressed, progress is preserved even
if the file is re-fetched or the library is rebuilt.

When a player correctly identifies a group, the frontend reveals `category`,
`description`, `url`, and `additional_sources` as learning content -- making Find4
an educational tool as well as a word game.
