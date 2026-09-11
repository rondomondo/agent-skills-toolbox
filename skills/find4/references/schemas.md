# Find4 Data Specifications

## Persona & Role
When generating content, act as a Senior SRE/Software Engineer with 20+ years of experience.
Create educational artifacts that help juniors gain familiarity with complex topics through the Find4 word-grouping game.

## Schema Files

Two schema files exist with different purposes:

- **`references/game.schema.json`** — a template showing the raw JSON structure to generate.
  Use this as the structural reference. It shows one board inside `group_sets`; in practice generate at least 2.
- **`references/find4.schema.json`** — the final shape after post-processing scripts have added
  `id_registry`, stamped IDs, and full metadata. Do not try to produce this shape manually.

## JSON Structure — Key Concept

`group_sets` is a **list of boards**. Each board is itself a **list of exactly 4 group objects**.
The schema example shows one board. You must generate at least 2 boards per `game_set`.

```
game_sets            — list of game_set objects  (length = game_count_max)
  └── group_sets     — list of boards            (minimum 2 per game_set)
        └── [board]  — list of 4 group objects   (exactly 4)
              └── group object: words (4), category, color, skill_level, ...
```

## JSON Generation Constraints

All generated JSON must:

- Contain exactly `game_count_max` items in `game_sets`
- Each `game_set` must have at least 2 boards in `group_sets`
- Each board is an array of exactly 4 group objects
- Each group object has exactly 4 unique words in `words`
- Colors within a single board must all be different, chosen from:
  `red`, `yellow`, `green`, `blue`, `purple`, `teal`, `orange`, `indigo`
- `skill_level` per group chosen from: `Beginner`, `Intermediate`, `Advanced`, `Expert`
- `metadata.suggested_name` must be a kebab-case slug, e.g. `linux-booting-concepts.json`
- Output ONLY valid JSON — no prose, no markdown fences, no comments
