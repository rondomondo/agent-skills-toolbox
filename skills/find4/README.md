# Find4

A Connections-style word-grouping game where players find 4 groups of 4 words that share a hidden theme. Useful as an educational tool for any topic - generate a game from any article, document, or URL in seconds.

**Live app**: https://find4.org

It generates a fully post-processed, drag-and-drop-ready JSON file compatible with the runner [Find4 game app](https://find4.org)

**Triggers when:** you type `/find4`, ask to create a Find4 game, generate game content from a document or webpage, or mention "connections game", "word groups", or "game JSON" etc.

**Input sources:**

You can give it any of:

- A URL (webpage content is fetched, cleaned and examined)
- A local file (text, Markdown, PDF)
- Piped stdin content

**Output:**

- A Find4 Game Payload - a validated, ID-assigned JSON file ready for use with the Game App
- Colour-fixed and metadata-finalised via the skill's own post-processing scripts
- Standalone `.html` files (one per game set) you can open and play immediately in any browser
- PNG screenshot previews of each game card

<br>

**Examples:**

<details>
<summary>Pasting a URL into this chat...

![Prompt: /find4 quiz me on 'brendangregg.com/ebpf.html'][img-brendan-gregg]

</summary>

Generated this particular find4 game card
[![bpftrace One-Liners & Internals game][img-bpftrace]][link-bpftrace]

</details>

-----

<details>
<summary>Typing the text below into the chat...

![Prompt: /find4 generate some games from this PDF][img-highschoolers-prompt]

</summary>

Came back with History and Geography questions

[![World Geography for High Schoolers game][img-world-geo]][link-world-geo]


</details>

-----

<details>
<summary>Pasting in a document as a source to the chat...

![Prompt: /find4 generate some games from this pdf][img-pdf-prompt]

</summary>

Came back with these items

[![Kubernetes Operators: Core Concepts][img-k8s-operators]][link-k8s-operators]


</details>


## How to play

1. Open the app and load a game (drag-and-drop a JSON file, use the Library, or open a share link).
2. You see 16 words arranged in a 4x4 grid. Find the 4 groups of 4 that share a hidden connection.
3. Select 4 tiles and submit - the group reveals its category, description, and reference links.
4. Complete all 4 groups to win.

**Lives:** you have 4 incorrect guesses before game over. Each wrong submission shakes the grid and costs one life.

**Shortcuts:** `Ctrl+Shift+S` auto-solves all groups (useful for testing or demo).

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

# Request more games (default is 2)
/find4 --game-count-max 4 https://example.com/some-article
```

Claude will:
1. Analyse the content and produce themed word groups
2. Run the post-processing pipeline (colour assignment, IDs, metadata)
3. Save the result to `output/games/<name>.json`
4. Generate one standalone `.html` file per game set
5. Screenshot each game card as a `.png` preview
6. Print a **share link** you can open directly in the browser

### Share links

After generation, Claude prints a URL of the form:

```
https://find4.org/#game=<base64>
```

And also a set of cards to play immediately like

[examples/equine-vet-strengths-clinical-and-emergency.html](https://find4.org/examples/equine-vet-strengths-clinical-and-emergency.html)

[examples/opentelemetry-architecture-and-signals.html](https://find4.org/examples/opentelemetry-architecture-and-signals.html)

[examples/fifa-world-cup-records-and-legends.html](https://find4.org/examples/fifa-world-cup-records-and-legends.html)

[examples/vllm-faster-llm-inference-and-serving.html](https://find4.org/examples/vllm-faster-llm-inference-and-serving.html)



Open it to play immediately - no file needed. Generate one manually:

```bash
bash scripts/share_game.sh games/my-game.json
```

---

## Game JSON format

A game file contains one or more `game_sets`. Each `game_set` is an independently playable round with a theme and at least two `group_sets` (boards of 16 words).

### Annotated example

```json
{
  "metadata": {
    "generated_at": "2026-05-04T14:10:00Z",
    "source": "https://ebpf.io/what-is-ebpf/",
    "suggested_name": "ebpf-core-concepts.json",
    "modified_at": "2026-05-04T14:19:11Z",
    "source_id": "https://ebpf.io/what-is-ebpf/",
    "id": "42ec491b61f410059dd248",
    "id_registry": {
      "game_set_ids": ["8a468e"],
      "group_set_ids": ["20520c", "fdd62e"],
      "group_item_ids": ["9202b0", "9fa41f", "f41978", "276c23", ...]
    }
  },
  "game_sets": [
    {
      "theme": "eBPF Core Architecture & Runtime",
      "game_set_id": "8a468e",
      "group_sets": [
        [
          {
            "words": ["KPROBE", "UPROBE", "TRACEPOINT", "SYSCALL HOOK"],
            "category": "eBPF Hook Types",
            "color": "blue",
            "url": "https://ebpf.io/what-is-ebpf/#hook-overview",
            "description": "Predefined attachment points where eBPF programs are triggered in the kernel",
            "skill_level": "Intermediate",
            "additional_sources": ["https://docs.kernel.org/trace/kprobes.html"],
            "group_item_id": "9202b0",
            "group_set_id": "20520c"
          },
          { "...": "3 more groups, each with a distinct colour" }
        ]
      ]
    }
  ]
}
```

### Field reference

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `metadata.suggested_name` | string | kebab-case, `.json` suffix | Used as the output filename |
| `metadata.id` | string | URL-safe base64 | Payload-level fingerprint, added by pipeline |
| `game_sets[].theme` | string | - | Displayed as the round title |
| `game_sets[].game_set_id` | string | 6-char hex | Content-addressed MD5, added by pipeline |
| `group_sets[]` | array | exactly 4 items | One playable board of 16 words |
| `group_item.words` | array | exactly 4 strings, UPPERCASE | The tiles shown on the board |
| `group_item.category` | string | - | Revealed after a correct guess |
| `group_item.color` | string | `red` `blue` `green` `yellow` `orange` `indigo` `purple` `teal` | Must be unique within a `group_set` |
| `group_item.skill_level` | string | `Beginner` `Intermediate` `Advanced` `Expert` | Shown as a badge on the card |
| `group_item.url` | string | valid URI | Primary reference for the category |
| `group_item.description` | string | - | Short explanation shown on reveal |
| `group_item.additional_sources` | array | valid URIs | Extra references |
| `group_item.group_item_id` | string | 6-char hex | Content-addressed MD5, added by pipeline |
| `group_item.group_set_id` | string | 6-char hex | Same value for all 4 items in a round |

### Colour palette

Each `group_set` must use exactly 4 different colours chosen from the 8 available:

`red` `blue` `green` `yellow` `orange` `indigo` `purple` `teal`

The `fix_colors.py` pipeline step enforces this automatically - if the LLM repeats a colour, the script reassigns the first 4 palette colours positionally.

---

## Post-processing pipeline

Raw LLM JSON passes through three scripts before being saved. The scripts are the single source of truth for output format - never reimplement their logic inline.

```
raw JSON
   |
   v
fix_colors.py        enforces 4 unique colours per group_set
   |
   v
add_ids.py           stamps content-addressed MD5 IDs at 3 hierarchy levels
   |                 writes id_registry at top level
   v
finalize_metadata.py stamps modified_at, source_id, promotes id_registry
   |                 into metadata, generates payload-level hash id
   v
output/games/<name>.json
   |
   v
generate_library_all.py  scans all game files, deduplicates by game_set_id,
                         rebuilds output/library/themes.json and library.json
```

### Why each step exists

**`fix_colors.py`** - LLM output occasionally repeats a colour within a round. The frontend uses colour as the primary visual differentiator, so duplicates break the UI. This step corrects silently rather than failing generation.

**`add_ids.py`** - IDs are content-addressed (MD5 of the category, sorted words, colour, and description). The same content always produces the same ID, which makes cross-file deduplication in the library safe. The `id_registry` at the top level lets the frontend resolve any ID in O(1).

**`finalize_metadata.py`** - Adds `modified_at` for freshness tracking, `source_id` for traceability back to the origin URL or file, and a payload-level `id` hash so two files with the same content are detectable.

**`generate_library_all.py`** - Builds `themes.json` (a compact index the Library panel loads on startup) and `library.json` (full word data for every game set) in a single pass. It reads every game file, extracts summary metadata (theme, categories, skill levels, colours, word count), and deduplicates by `game_set_id` keeping the most-recently-modified copy. Pass `--themes-only` to stop after `themes.json`.

### Running scripts manually

```bash
# Full pipeline from a raw JSON file
cat output/tmp/find4_raw.json \
  | python3 scripts/fix_colors.py \
  | python3 scripts/add_ids.py \
  | python3 scripts/finalize_metadata.py --source "https://example.com" \
  > output/games/my-game.json

# Rebuild library index after adding games manually
python3 scripts/generate_library_all.py \
  --config-dir output/library --library-dir output/games --library-root output --force

# Generate a share URL
bash scripts/share_game.sh output/games/my-game.json

# Screenshot a game card
python3 scripts/screenshot_game.py \
  --html output/games/html/my-game.html \
  --output output/games/screenshots/my-game.html.png
```

---

## Designing good games

A well-designed Find4 game is educational without being frustrating. These guidelines apply whether you are prompting Claude to generate a game or authoring JSON directly.

**Words should be short and unambiguous.** Tiles display in a small grid - aim for 1-2 words per tile, all uppercase. Avoid phrases longer than 3 words.

**Category names reveal the connection, not the words.** "eBPF Hook Types" is good; "Things that start with K" is not. Players see the category only after guessing correctly, so it should feel like an "ah ha" confirmation.

**Descriptions add depth.** Use the `description` field to give a one-sentence explanation of *why* these four items belong together. This turns a fun moment into a learning moment.

**Skill levels signal difficulty, not obscurity.** Use `Beginner` for foundational terms any newcomer would encounter on day one, `Intermediate` for concepts requiring some practical exposure, `Advanced` for things that need real depth to reason about, and `Expert` for specialist or cutting-edge content. A well-balanced game has at least one of each level per board.

**Colours are visual only.** The `color` field controls tile appearance on reveal - it has no semantic meaning. The pipeline assigns colours automatically; you only need to ensure 4 different colours appear within each `group_set`.

**Cross-cutting distractors make games hard.** The best games have at least one word that *could* plausibly belong to two categories. Players who understand the topic deeply will notice the distinction; those who do not will be tripped up. This is intentional.

**Keep `additional_sources` honest.** These links appear on the reveal card. Only include URLs that actually exist and go directly to content relevant to the category.

---

## Development

### Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
make install
```

### Local dev server

```bash
make serve          # builds, copies to local/, serves HTTPS on https://find4.org
```

Changes to JS/CSS/HTML trigger an automatic server restart. The server uses a self-signed TLS cert matched to the production hostname so share-URL behaviour is identical to prod.

Generate a cert for local development (one-time):

```bash
make gen-cert
```

### Build

```bash
make bundle         # combine JS + CSS (no minification)
make minify         # minify JS and CSS bundles
make release        # minify + rebuild library index
```

### Tests

```bash
make test           # Python unit tests with coverage
make e2e            # Playwright end-to-end tests (requires Docker)
```

The e2e suite covers: page load, tile selection, correct/incorrect guessing, lives count, win/game-over states, toolbar and hints, the Library panel, mobile layout, persistence, and accessibility.

### Validation

```bash
make validate-schema   # validate all games/*.json against find4.schema.json
make validate          # validate schema + sensible-values check (strict mode)
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
games/              - game JSON files (source of truth)
library/            - themes.json library index (derived, rebuild with make librarygen)
output/             - generated output from skill runs
  tmp/              - intermediate pipeline files (timestamped backups kept here)
  games/            - final game JSON files
  games/html/       - standalone HTML files (one per game set)
  games/screenshots/- PNG screenshots of game cards
  library/          - generated themes.json
js/                 - frontend JavaScript source
css/                - frontend CSS source
dist/               - bundled/minified output (gitignored)
vendor/             - Material Design JS/CSS (checked in, no build step)
scripts/            - post-processing pipeline and utility scripts
  fix_colors.py     - colour validation and correction
  add_ids.py        - content-addressed ID generation
  finalize_metadata.py - metadata stamping and id_registry promotion
  generate_library_all.py - themes.json index + library.json builder
  generate_html.py  - standalone HTML file generator
  screenshot_game.py   - game card PNG renderer (Docker or local Playwright)
  share_game.sh     - share URL encoder (base64 + compression)
  validate.py       - JSON schema and value validation
references/         - schemas, UI templates, and design notes
  game.schema.json  - raw JSON template (pre-pipeline structure)
  find4.schema.json - formal JSON Schema (post-pipeline, used by make validate-schema)
  schemas.md        - generation constraints and persona guidance
  ui-templates.md   - widget HTML patterns for chat display
tests/              - Python unit tests and Playwright e2e tests
certs/              - TLS certs for local HTTPS dev server (gitignored)
```

---

## Deployment

```bash
make deploy-webapp   # copies deployable files to webapp
```

The app is a static single-page app - no server required. Deploy to any static host.


<!-- Link and image references -->

[img-bpftrace]: https://find4.org/examples/bpftrace-one-liners-and-internals.html.png

[link-bpftrace]: https://find4.org/?ff-93cf4694

[img-brendan-gregg]: https://find4.org/examples/brendan-gregg.png

[img-world-geo]: https://find4.org/examples/world-geography-for-high-schoolers.html.png

[link-world-geo]: https://find4.org/#game=tZhdc-I6Eob_ioqLPTcwId-BOwcI8W74WOOpqTO7qZSwhdGMLXklORwyNf_9vC0DgeRMVWZytooqG1tqSd2P3m75W6MQjqfc8Ub3WyMTShjuRPrAXaPbOGmfXLTa562Tdtxud_3vc6PZsLoyicB761Kp6EGVZcJSN8ULerGU2dImS63z1lJap826lQmdGV4u1x--WE2dCp3Khfyroa66553u-emHdvvs8uxiN-CDTPfHdKLE34VUPJdP4mG3jGZDpg9GZBjXrP2ijK7KByscDNhG9z8NvhCd03M05B0-Ty5xs1jMLy7o5oqfJ2LRuG82Mqxkv9PxxdVpStaTS77otH0Tb1g6UWwbXZwez8_ITidtz0-OcXOeHJ9dzXFzynnaSan_6fGJSHBz0k475_Tq7PIynZ_RqzY_PengZt6ZX53SYJ0FP7uiqbbF6eX5AjcXl1f8lHrNF-05p8YXJ1fi3C_nIjm-PMGN6CQnncvG_XfyBZzUfhhdXepSxq7fSp4-dxrfn9dH8_7WcEvhA_dJmzxlw22s2EIbdotgspmPpjC20Xx2KPVF55U29fKDUfB5MkaLcXg3wOX3YDyMP9PdKJzN6DedhuS5BIxlmsLTGBrBHYvkI2wzvWCYCfOzIH_oXBu0meeVwN_K5MSWc6XtHh2tVqsPcyMdV0om_EOii6My54k4Cgr-pFXLm0SvVNjEyNJJUNdtxDC_IvO_WVZo69iCF7qyzPgJdP3wY5kLxlXKaksMpkvhhHdGrhWh3vQNf-cqc0-CScsCKzlMHrweSWvpV5aSpYZLZf3jpeDG0VLH2rglBhEGCyCkv8o8f8jFo6B1XgNhpfwSeJpKmj_PH-qt4L297wjF6_fbXSYT7xChHqXRqhDKHWFQmeTiSGF1Lb9cisQvBH4DPMVli-n-FqNNWW-n7809NmbBbRAFaDucXIe4BHHQAy90FwXXYTB-wcVNHZe-sMI4uwfDWuS5Xr0dhxlfcsNfgTDiX7DEtDZfx71uSdF0e5Tk3FBI2VK7TfM6ukM9lwwaI1yyFJbxxGhrWQJXG557Hup2geMJL2BWsd6SyHphPzVyR0xg-FxytVk1S3UBeXPCbnBKU3QfcOveB8tf75p6mq166HejsROut6ARR0EYs8kNG4bXUXAXBxE6Pj-9nUSjj5R4riez6ST6ODt4Owrugl4veIHPzFEey2TCPuFqVny9z5ATPP8JgmBLupZetIZyjuA6_lpXxtwYvWJWcFZyazmQoS2-rDJBkGzmIosSe56rRHTZzhb0BaFLHETE5Vxhl3rxGQnEURjDleCqyW61KaonauuMzi2bwu-EyrDKF0zLvMmutYV17Jlcqq-WXWPuX9kME3L6pbERx8tkh3qG6cFDbC7cSgjFpjxBaq6nEaqUhpkk6GhfcRekj7Sa9Ne5e3ZuvcJ3k7fLlG8gL44m07BHPA3-_TGIJ8TdNApHAzYaRGGfVIn0qReHPdYLox6y2iFmd1JRoFWtCLmeiz3KMgNnvgUzm0gBLx6J_1UcxdIruMKCY3tzs2ZGLIShthRksdGtQd2NpfJRoiMSTCFtuURDW8vK1MgC-oE842NJmdtnKumqVLAnYTRDDh7SdFcyWdadYoOKIfEU9yjGxuPQ4yWylTaKFdx89Q1tpSBjiwrJjHQS-XxrIjAJ0dyTBonHd6h5K2SqEEbXQleGDCv-9uSnTYbkl6yTXJdAn29de_RuvHb11w_wum_uV0SjyXg28SXR4I6Nw_EEd1Cu_oB9Csd9Au-fg5hBzAbB6AVavVwW-Mf-wT6hQkI02WyNorfY1zGJzZnpn0Gs0MpqX38fIkbsIm2tNkOV3EEuFADbdLAMBlVGAmfJ12xTz2g20xVVMT7fDXIUT_-t2u3FsQaO1lQlUNvKCSZf0vGiAph1-luBV6BiODBcYTGUDfUjkOISfGctu5QlE3-UWK2PcY3VF-F84uUFLoLqRjpiFLscvB0HmwS9iPHXwhUqrK8gNJz4FfHa-nOQt8ZS6feXUttq_gVWmwPJgWpF4XhIme8mjKi2ngVjFoz7QGjGboKPd7Gvt_utIL4LxqRcULIhNbwNKVeiKGfXA7Q6xC1GBtJYHrsRdYT2MDNe4N-YLSMKHOT8Rhrxg6prsRmCtAWdECi3GX2jaGSDXpINBj97Aam1YwvTSoK6R50nXOmtzs0gboFKQYal1MaJLGXh_wJlfpU7X4PhuIgnalueoapq7fJuJNNM1F1tCTMpzcOXdKJufYs9mfM17JNVkbIVyWydJJGb8xxAp_XcaEe8H7u3aJt3YWvnwr9B47YnyjfA2B_cTKLBLA7i0OtcfzAbRHF4E_a2Tz5G18E4nG3_DlGuhcEdiwakei8xvK0KBDEsSp44yqt3SDo24eUBj1ADHLN-RvZSgYUjO3lvvqLyE6pDlGoYGZFHOJMl7FPoKeTwrhKuyw5MIMsVECqPAZ75KxgzBRqnzc05gTitW4N2mF7Qs5xUCYkUyrk9TVRmzpW0dVO4fIVjBLCg_YFTGlviTIBRwXiGDSZJe4Xzp2a7NL7Uk6gH7FJQWuf2UGaNtOL_QuGPjpcvlv5uFncfNd7A4rA_JZnr0_nyOoziWxYFcf35YRjV_B3S1ieH6JIWgDw71WWV11EYQUJeiGBZmTJ_E3SOCqejjHJRC0c48CGTVml0WiXuFXv_EmtWbEYjffIYst3XMpwT-tPnBgL1Pw6FCUPSLavNqbHeM_trgR6JP-i7xdzXp8jquUNNJjCDen1EIHRQUHKFbqC-WzfZXNL3CJ84IZwJwCqfPUJcko1CZmYDdd3GF3QA1Q9Mgi40_LQ7S_ik8I6DwzI1HyqVll726ANfi_RYmCPvqFb6vOqWpFW_G7jNx7MfAnd_-HEQbzZfBL_ff_8T


[img-highschoolers-prompt]: https://find4.org/examples/game-for-highschoolers.png

[img-k8s-operators]: https://find4.org/examples/kubernetes-operators-core-concepts.html.png
[link-k8s-operators]: https://find4.org/?ff-155d0fed

[img-pdf-prompt]: https://find4.org/examples/pdf-file-attachment.png
