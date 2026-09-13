#!/usr/bin/env -S uv run python3
"""
generate_html.py - Generates a self-contained standalone HTML file for a single Find4 game set.

Reads a game JSON file (one game_set) and a share URL file, then produces a complete
HTML file with Open Graph, Twitter Card, and Schema.org metadata derived from the game
content. The HTML is fully self-contained: no external fonts or stylesheets.

Usage:
    python3 generate_html.py \\
        --game-json output/games/my-theme.json \\
        --output output/games/html/my-theme.html

    The share URL file defaults to <output>_share_url.txt, e.g.:
        output/games/html/my-theme.html_share_url.txt

    Override with --share-url-file if needed.

The input JSON must contain exactly one entry in game_sets (a split file, not the
combined multi-game file).
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

FIND4_BASE_URL = "https://find4.org"
FIND4_PREVIEW_IMAGE = f"{FIND4_BASE_URL}/preview-image.png"

SKILL_LEVEL_MAP = {
    "Beginner": ("b", "sk-b"),
    "Intermediate": ("i", "sk-i"),
    "Advanced": ("a", "sk-a"),
    "Expert": ("e", "sk-e"),
}

COLOR_DOT_MAP = {
    "red": "dot-red",
    "green": "dot-green",
    "blue": "dot-blue",
    "yellow": "dot-yellow",
    "purple": "dot-purple",
    "teal": "dot-teal",
    "orange": "dot-orange",
    "indigo": "dot-indigo",
}

THEME_ICON_MAP = [
    (["space", "astro", "rocket", "orbit", "nasa", "lunar", "mars"], "&#x1F680;", "#e6f1fb"),
    (["science", "lab", "physics", "chem", "bio", "molecule", "genome", "dna"], "&#x1F52C;", "#e6f1fb"),
    (["tech", "software", "code", "program", "devops", "cloud", "kube", "ray", "vllm", "llm", "ai", "ml", "sre", "infra", "platform", "container", "docker", "kubernetes"], "&#x2699;&#xFE0F;", "#e6f1fb"),
    (["history", "ancient", "roman", "greek", "medieval", "empire", "war", "battle"], "&#x1F3DB;&#xFE0F;", "#faeeda"),
    (["nature", "animal", "plant", "forest", "ocean", "climate", "ecology", "earth"], "&#x1F33F;", "#e1f5ee"),
    (["people", "society", "culture", "art", "music", "film", "sport", "food"], "&#x1F465;", "#faeeda"),
    (["math", "algebra", "calculus", "geometry", "statistics", "logic"], "&#x1F4D0;", "#eeedfe"),
    (["language", "literature", "writing", "grammar", "poetry"], "&#x1F4DA;", "#faeeda"),
]

DEFAULT_ICON = ("&#x1F9E9;", "#eeedfe")

CSS1 = """\
        body{font-family:system-ui,-apple-system,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;background:#f5f5f3;color:#111;}
        .f4-game{background:#fff;border:0.5px solid rgba(0,0,0,0.3);border-radius:12px;padding:1rem 1.25rem;margin-bottom:48px;box-shadow:0 4px 6px -1px rgb(0 0 0 / 0.1);}
        .f4-game-header{display:flex;align-items:center;gap:10px;margin-bottom:1rem;flex-wrap:wrap;}
        .f4-game-icon{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:20px;}
        .f4-game-title-block{flex:1;min-width:0;}
        .f4-game-title{font-size:15px;font-weight:500;margin:0;color:#111;}
        .f4-game-meta{font-size:12px;color:#666;margin:0;}
        .play-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 14px;background:#0f6e56;color:#fff;border-radius:10px;text-decoration:none;font-size:13px;font-weight:500;margin-left:auto;transition:background 0.2s;}
        .play-btn:hover{background:#085041;}
        .f4-groups{display:flex;flex-direction:column;gap:5px;}
        .f4-round{font-size:11px;font-weight:500;color:#888;padding:8px 0 3px;text-transform:uppercase;letter-spacing:0.05em;}
        .f4-group{display:grid;grid-template-columns:13px 1fr 90px 2fr;align-items:start;gap:8px;padding:8px 10px;border-radius:8px;border:0.5px solid #e0e0de;background:#fafaf9;}
        .f4-dot{width:11px;height:11px;border-radius:50%;flex-shrink:0;margin-top:3px;}
        .f4-cat{font-size:13px;font-weight:500;line-height:1.3;}
        .f4-skill{font-size:11px;padding:2px 7px;border-radius:20px;text-align:center;white-space:nowrap;}
        .f4-words{font-size:11px;color:#666;line-height:1.5;word-break:break-word;}
        .sk-b{background:#e1f5ee;color:#085041;}.sk-i{background:#e6f1fb;color:#0c447c;}.sk-a{background:#faeeda;color:#633806;}.sk-e{background:#fcebeb;color:#791f1f;}
        .dot-red{background:#e24b4a;}.dot-green{background:#639922;}.dot-blue{background:#378add;}.dot-yellow{background:#ba7517;}
        .dot-purple{background:#7f77dd;}.dot-teal{background:#1d9e75;}.dot-orange{background:#d85a30;}.dot-indigo{background:#534ab7;}\
"""

CSS1_WIDGET_EXTRA = "        .play-btn{pointer-events:none;cursor:default;}"

CSS = """\
        body{font-family:system-ui,-apple-system,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;background:#f5f5f3;color:#111;}
        .f4-game{background:#fff;border:0.5px solid rgba(0,0,0,0.15);border-radius:12px;padding:1rem 1.25rem;margin-bottom:48px;box-shadow:0 4px 6px -1px rgb(0 0 0 / 0.1);}
        .f4-game-header{display:flex;align-items:center;gap:10px;margin-bottom:1rem;flex-wrap:wrap;}
        .f4-game-icon{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:20px;}
        .f4-game-title-block{flex:1;min-width:0;}
        .f4-game-title{font-size:15px;font-weight:500;margin:0;color:#111;}
        .f4-game-meta{font-size:12px;color:#666;margin:0;}
        .play-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 14px;background:#0f6e56;color:#fff;border-radius:10px;text-decoration:none;font-size:13px;font-weight:500;margin-left:auto;transition:background 0.2s;}
        .play-btn:hover{background:#085041;}
        .f4-groups{display:flex;flex-direction:column;gap:5px;}
        .f4-round{font-size:11px;font-weight:500;color:#888;padding:8px 0 3px;text-transform:uppercase;letter-spacing:0.05em;}
        .f4-group{display:grid;grid-template-columns:13px 1fr 90px 2fr;align-items:start;gap:8px;padding:8px 10px;border-radius:8px;border:0.5px solid #e0e0de;background:#fafaf9;}
        .f4-dot{width:11px;height:11px;border-radius:50%;flex-shrink:0;margin-top:3px;}
        .f4-cat{font-size:13px;font-weight:500;line-height:1.3;}
        .f4-skill{font-size:11px;padding:2px 7px;border-radius:20px;text-align:center;white-space:nowrap;}
        .f4-words{font-size:11px;color:#666;line-height:1.5;word-break:break-word;}
        .sk-b{background:#e1f5ee;color:#085041;}.sk-i{background:#e6f1fb;color:#0c447c;}.sk-a{background:#faeeda;color:#633806;}.sk-e{background:#fcebeb;color:#791f1f;}
        .dot-red{background:#e24b4a;}.dot-green{background:#639922;}.dot-blue{background:#378add;}.dot-yellow{background:#ba7517;}
        .dot-purple{background:#7f77dd;}.dot-teal{background:#1d9e75;}.dot-orange{background:#d85a30;}.dot-indigo{background:#534ab7;}
        @media(prefers-color-scheme:dark){
          body{background:#1a1a18;color:#e8e6e1;}
          .f4-game{background:#2c2c2a;border-color:rgba(255,255,255,0.1);box-shadow:0 4px 6px -1px rgb(0 0 0 / 0.4);}
          .f4-game-title{color:#e8e6e1;}
          .f4-game-meta{color:#888780;}
          .f4-round{color:#888780;}
          .f4-group{background:#222220;border-color:#3a3a38;}
          .f4-cat{color:#e8e6e1;}
          .f4-words{color:#888780;}
          .sk-b{background:#04342c;color:#9fe1cb;}.sk-i{background:#042c53;color:#b5d4f4;}.sk-a{background:#412402;color:#fac775;}.sk-e{background:#501313;color:#f7c1c1;}
        }\
"""

CSS_WIDGET_EXTRA = """\
        .play-btn{pointer-events:none;cursor:default;}
        @media(prefers-color-scheme:dark){
          body{background:transparent;}
        }\
"""

def slugify(text: str) -> str:
    text = text.lower().replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def pick_icon(theme: str) -> tuple[str, str]:
    lower = theme.lower()
    for keywords, emoji, bg in THEME_ICON_MAP:
        if any(kw in lower for kw in keywords):
            return emoji, bg
    return DEFAULT_ICON


def extract_keywords(game_set: dict[str, Any]) -> list[str]:
    """Pull category names and theme words into a keyword list."""
    keywords: list[str] = [game_set.get("theme", "")]
    for group_set in game_set.get("group_sets", []):
        for item in group_set:
            cat = item.get("category", "")
            if cat:
                keywords.append(cat)
    seen: set[str] = set()
    result: list[str] = []
    for kw in keywords:
        if kw and kw not in seen:
            seen.add(kw)
            result.append(kw)
    return result[:10]


def dominant_skill(game_set: dict[str, Any]) -> str:
    """Return the most common skill level across all groups."""
    counts: dict[str, int] = {}
    for group_set in game_set.get("group_sets", []):
        for item in group_set:
            level = item.get("skill_level", "")
            counts[level] = counts.get(level, 0) + 1
    return max(counts, key=counts.get) if counts else "Mixed"  # type: ignore[arg-type]


def word_count(game_set: dict[str, Any]) -> int:
    total = 0
    for group_set in game_set.get("group_sets", []):
        for item in group_set:
            total += len(item.get("words", []))
    return total


def round_count(game_set: dict[str, Any]) -> int:
    return len(game_set.get("group_sets", []))


def build_meta(game_set: dict[str, Any], share_url: str) -> dict[str, str]:
    theme = game_set.get("theme", "Find4 Game")
    skill = dominant_skill(game_set)
    rounds = round_count(game_set)
    words = word_count(game_set)
    keywords = extract_keywords(game_set)

    description = (
        f"A {skill}-level Find4 word-grouping game on '{theme}'. "
        f"{rounds} round{'s' if rounds != 1 else ''}, {words} words. "
        f"Find the hidden connections between groups of 4."
    )

    return {
        "title": theme,
        "description": description,
        "keywords": ", ".join(keywords),
        "og_title": theme,
        "og_description": f"Test your knowledge on {theme}. {rounds} round{'s' if rounds != 1 else ''}, {words} words.",
        "og_url": share_url,
        "twitter_title": theme,
        "twitter_description": f"{skill}-level challenge covering {theme}.",
        "skill": skill,
        "rounds": str(rounds),
        "words": str(words),
    }


def build_schema_org(game_set: dict[str, Any]) -> dict[str, Any]:
    theme = game_set.get("theme", "Find4 Game")
    skill = dominant_skill(game_set)
    categories = []
    for group_set in game_set.get("group_sets", []):
        for item in group_set:
            cat = item.get("category", "")
            if cat:
                categories.append(cat)
    abstract = f"Covers concepts including: {', '.join(categories[:4])}." if categories else theme

    return {
        "@context": "https://schema.org",
        "@type": "EducationalOccupationalCredential",
        "name": theme,
        "educationalLevel": skill,
        "abstract": abstract,
    }


def build_group_rows(group_set: list[dict[str, Any]]) -> str:
    rows = []
    for item in group_set:
        color = item.get("color", "blue")
        dot_class = COLOR_DOT_MAP.get(color, "dot-blue")
        category = html.escape(item.get("category", ""))
        skill_level = item.get("skill_level", "Beginner")
        _, skill_css = SKILL_LEVEL_MAP.get(skill_level, ("b", "sk-b"))
        words = " &middot; ".join(html.escape(w) for w in item.get("words", []))
        aria_label = html.escape(f"{skill_level} Level Category")
        rows.append(
            f'    <div class="f4-group">\n'
            f'        <div class="f4-dot {dot_class}" role="img" aria-label="{aria_label}"></div>\n'
            f'        <div class="f4-cat">{category}</div>\n'
            f'        <span class="f4-skill {skill_css}">{skill_level}</span>\n'
            f'        <div class="f4-words">{words}</div>\n'
            f'    </div>'
        )
    return "\n".join(rows)


def build_groups_html(game_set: dict[str, Any]) -> str:
    parts = []
    for i, group_set in enumerate(game_set.get("group_sets", []), start=1):
        parts.append(f'    <h2 class="f4-round">Round {i}</h2>')
        parts.append(build_group_rows(group_set))
    return "\n".join(parts)


def _game_card_html(theme: str, icon_bg: str, icon_emoji: str, rounds: str, words: str, skill: str, share_url: str | None, groups_html: str) -> str:
    """Render the inner game card markup shared by full and widget outputs."""
    if share_url is not None:
        play_btn = f'<a class="play-btn" href="{share_url}" target="_blank" rel="noopener"><span>&#9654;</span> Play on find4.org</a>'
    else:
        play_btn = '<span class="play-btn">&#9654; Play on find4.org</span>'
    return f"""<div class="f4-game f4-capture">
  <div class="f4-game-header">
    <div class="f4-game-icon" style="background:{icon_bg};" aria-hidden="true">{icon_emoji}</div>
    <div class="f4-game-title-block">
      <h1 class="f4-game-title">{html.escape(theme)}</h1>
      <p class="f4-game-meta">{rounds} round{"s" if int(rounds) != 1 else ""} &middot; {words} words &middot; {html.escape(skill)} level</p>
    </div>
    {play_btn}
  </div>

  <div class="f4-groups">
{groups_html}
  </div>
</div>"""


def generate_html(game_json_path: Path, share_url: str, output_path: Path, as_widget: bool = False) -> None:
    """Generate a standalone HTML file for a single Find4 game set.

    Args:
        game_json_path: Path to a split single-game-set JSON file.
        share_url: The canonical share URL for the game.
        output_path: Destination path for the full HTML output.
        as_widget: When True, also write a .w.html widget variant alongside the main output.
    """
    with open(game_json_path, encoding="utf-8") as f:
        data = json.load(f)

    game_sets = data.get("game_sets", [])
    if len(game_sets) != 1:
        print(
            f"Error: expected exactly 1 game_set in {game_json_path}, found {len(game_sets)}",
            file=sys.stderr,
        )
        sys.exit(1)

    game_set = game_sets[0]
    theme = game_set.get("theme", "Find4 Game")
    slug = slugify(theme)
    icon_emoji, icon_bg = pick_icon(theme)
    meta = build_meta(game_set, share_url)
    schema_org = build_schema_org(game_set)
    groups_html = build_groups_html(game_set)
    rounds = meta["rounds"]
    words = meta["words"]

    card_html = _game_card_html(theme, icon_bg, icon_emoji, rounds, words, meta["skill"], share_url, groups_html)
    widget_card_html = _game_card_html(theme, icon_bg, icon_emoji, rounds, words, meta["skill"], None, groups_html)

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Find4 &mdash; {html.escape(theme)}</title>

    <meta name="description" content="{html.escape(meta['description'])}">
    <meta name="keywords" content="{html.escape(meta['keywords'])}">
    <meta name="author" content="Find4">
    <meta name="theme-color" content="#0f6e56">

    <meta property="og:type" content="website">
    <meta property="og:url" content="{html.escape(share_url)}">
    <meta property="og:title" content="{html.escape(meta['og_title'])}">
    <meta property="og:description" content="{html.escape(meta['og_description'])}">
    <meta property="og:image" content="{FIND4_PREVIEW_IMAGE}">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{html.escape(meta['twitter_title'])}">
    <meta name="twitter:description" content="{html.escape(meta['twitter_description'])}">
    <meta name="twitter:image" content="{FIND4_PREVIEW_IMAGE}">

    <script type="application/ld+json">
    {json.dumps(schema_org, indent=2)}
    </script>

    <style>
{CSS}
    </style>
</head>
<body>
{card_html}
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_out, encoding="utf-8")
    print(f"[generate_html] wrote {output_path}", file=sys.stderr)

    if as_widget:
        widget_path = output_path.with_suffix("").with_suffix(".w.html") if output_path.suffix == ".html" else Path(str(output_path) + ".w.html")
        widget_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
{CSS}
{CSS_WIDGET_EXTRA}
    </style>
</head>
<body>
{widget_card_html}
</body>
</html>
"""
        widget_path.write_text(widget_out, encoding="utf-8")
        print(f"[generate_html] wrote {widget_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a standalone Find4 HTML file for one game set")
    parser.add_argument("--game-json", required=True, metavar="FILE", help="Path to a split single-game-set JSON file")
    parser.add_argument("--share-url-file", metavar="FILE", help="File containing the share URL (output of share_game.sh); defaults to <output>_share_url.txt")
    parser.add_argument("--output", required=True, metavar="FILE", help="Output HTML file path")
    parser.add_argument("--as-widget", action="store_true", help="Also write a .w.html widget variant with CSS inlined and play button disabled")
    args = parser.parse_args()

    game_json_path = Path(args.game_json)
    if not game_json_path.exists():
        print(f"Error: game JSON not found: {game_json_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    share_url_path = Path(args.share_url_file) if args.share_url_file else Path(str(output_path) + "_share_url.txt")

    if not share_url_path.exists():
        print(f"Error: share URL file not found: {share_url_path}", file=sys.stderr)
        sys.exit(1)

    try:
        share_data = json.loads(share_url_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: share URL file is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    share_url = share_data.get("share_url", "")
    if not share_url.startswith("http"):
        print(f"Error: share URL file does not contain a valid URL: {share_url!r}", file=sys.stderr)
        sys.exit(1)

    generate_html(game_json_path, share_url, output_path, as_widget=args.as_widget)


if __name__ == "__main__":
    main()
