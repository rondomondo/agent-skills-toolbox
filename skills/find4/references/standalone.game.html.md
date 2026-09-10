
### Generating standalone HTML

**Always use `generate_html.py`** to produce standalone game HTML files. Never assemble
them by hand or with inline scripting. The script owns the full HTML structure, all meta
tags, icon selection, and the lazy-href play button.

For a complete worked example of the full output including all Open Graph, Twitter Card,
and Schema.org meta tags, see `references/standalone.game.html.with.meta.html`.

```bash
python3 $FIND4_SCRIPTS/generate_html.py \
  --game-json output/games/<slug>.json \
  --output output/games/html/<slug>.html
```

- `--game-json` must be a split single-game-set file (exactly one entry in `game_sets`).
- `--output` is the final HTML path.
- `--share-url-file` is optional; defaults to `<output>_share_url.txt` (e.g. `output/games/html/<slug>.html_share_url.txt`). The share URL file must be written by `share_game.sh` before calling this script.

The script automatically derives:
- `<meta name="description">`, `<meta name="keywords">`
- Open Graph (`og:title`, `og:description`, `og:url`, `og:image`)
- Twitter Card (`twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`)
- `<script type="application/ld+json">` with `EducationalOccupationalCredential` schema
- Theme icon emoji and background colour from the game theme
- Dominant skill level, round count, and word count for the header meta line

---

### Standalone Game HTML reference (informational only)

The structure below is what `generate_html.py` produces. Do not replicate it manually.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Find4 — <GAME THEME></title>
<style>
/* ── Page shell ─────────────────────────────────────────────────── */
body {
    font-family: system-ui, sans-serif;
    max-width: 720px;
    margin: 2rem auto;
    padding: 0 1rem;
    background: #f5f5f3;
    color: #111;
}

/* ── Game card ───────────────────────────────────────────────────── */
.f4-game {
    background: #ffffff;
    border: 0.5px solid rgba(0, 0, 0, 0.3);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 48px;
}

/* ── Game header ─────────────────────────────────────────────────── */
.f4-game-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}
.f4-game-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 20px;
}
.f4-game-title-block {
    flex: 1;
    min-width: 0;
}
.f4-game-title {
    font-size: 15px;
    font-weight: 500;
    margin: 0;
    color: #111;
}
.f4-game-meta {
    font-size: 12px;
    color: #666;
    margin: 0;
}

/* ── Play button ─────────────────────────────────────────────────── */
.play-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: #0f6e56;
    color: #ffffff;
    border-radius: 10px;
    text-decoration: none;
    font-size: 13px;
    font-weight: 500;
    margin-left: auto;
    transition: background 0.15s;
}
.play-btn:hover {
    background: #085041;
}




/* ── Group list ──────────────────────────────────────────────────── */
.f4-groups {
    display: flex;
    flex-direction: column;
    gap: 5px;
}
.f4-round {
    font-size: 11px;
    font-weight: 500;
    color: #888;
    padding: 8px 0 3px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.f4-group {
    display: grid;
    grid-template-columns: 13px 1fr 90px 2fr;
    align-items: start;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 8px;
    border: 0.5px solid #e0e0de;
    background: #fafaf9;
}

/* ── Group row elements ──────────────────────────────────────────── */
.f4-dot {
    width: 11px;
    height: 11px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 3px;
}
.f4-cat {
    font-size: 13px;
    font-weight: 500;
    line-height: 1.3;
}
.f4-skill {
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 20px;
    text-align: center;
    white-space: nowrap;
}
.f4-words {
    font-size: 11px;
    color: #666;
    line-height: 1.5;
    word-break: break-word;
}

/* ── Skill level badges ──────────────────────────────────────────── */
.sk-b { background: #e1f5ee; color: #085041; }
.sk-i { background: #e6f1fb; color: #0c447c; }
.sk-a { background: #faeeda; color: #633806; }
.sk-e { background: #fcebeb; color: #791f1f; }

/* ── Colour dots ─────────────────────────────────────────────────── */
.dot-red    { background: #e24b4a; }
.dot-green  { background: #639922; }
.dot-blue   { background: #378add; }
.dot-yellow { background: #ba7517; }
.dot-purple { background: #7f77dd; }
.dot-teal   { background: #1d9e75; }
.dot-orange { background: #d85a30; }
.dot-indigo { background: #534ab7; }
</style>
</head>
<body>

<div class="f4-game">
  <div class="f4-game-header">
    <div class="f4-game-icon" style="background: <ICON_BG_COLOR>;">
      <ICON_EMOJI>
    </div>
    <div class="f4-game-title-block">
      <p class="f4-game-title"><GAME THEME></p>
      <p class="f4-game-meta"><N> group sets · <N*16> words</p>
    </div>
    <span id="u_<GAME_SLUG>" style="display:none"><FULL_SHARE_URL></span>
    <a class="play-btn" href="#"
       onclick="event.preventDefault();window.open(document.getElementById('u_<GAME_SLUG>').textContent.trim(),'_blank');">&#9654; Play on find4.org</a>
  </div>

  <div class="f4-groups">
    <!-- one .f4-round label + one .f4-group row per group, per group_set -->
    <div class="f4-round">Round 1</div>
    <div class="f4-group">
      <div class="f4-dot dot-<COLOR>"></div>
      <div class="f4-cat"><CATEGORY NAME></div>
      <span class="f4-skill sk-<LEVEL>"><SKILL LEVEL></span>
      <div class="f4-words">WORD1 &middot; WORD2 &middot; WORD3 &middot; WORD4</div>
    </div>
    <!-- ... repeat for all 4 groups in round 1 ... -->

    <div class="f4-round">Round 2</div>
    <!-- ... repeat for all 4 groups in round 2 ... -->
  </div>
</div>

</body>
</html>
```

---

### Icon guidance

Choose a fitting emoji for `.f4-game-icon` based on the game theme, and pair it with
a light background tint from the palette. Here are some examples for example themes:

| Theme type             | Emoji    | Background            |
| ---------------------- | -------- | --------------------- |
| Science / space / tech | 🚀 🔬 💡 | `#e6f1fb` (blue-50)   |
| History / culture      | 🏛️ 📜 🗺️ | `#faeeda` (amber-50)  |
| Nature / biology       | 🌿 🧬 🌍 | `#e1f5ee` (teal-50)   |
| People / society       | 👥 ⭐ 🎓 | `#faeeda` (amber-50)  |
| General / mixed        | 🧩 📚 🎯 | `#eeedfe` (purple-50) |

