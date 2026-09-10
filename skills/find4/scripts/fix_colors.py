#!/usr/bin/env -S uv run python3
"""
fix_colors.py - Post-processing step 2 for find4 skill.

Validates and corrects the color assignments across every group_set.
The Find4 frontend uses color as the primary visual differentiator for
each group, so the following invariants must hold:
  - Every group must have a color from the official 8-color palette:
    red, blue, green, yellow, orange, indigo, purple, teal
  - Within a single group_set (one round of 4 groups), all 4 colors
    must be distinct -- no two groups can share a color.

If those invariants are already satisfied the data is passed through
unchanged. If not, the first 4 palette colors are assigned positionally.

Reads JSON from stdin (default) or --game-set-json FILE.
Writes corrected JSON to stdout.

Usage:
    # from stdin (default -- use in pipeline)
    cat output/tmp/find4_raw.json | python3 fix_colors.py > output/tmp/find4_colored.json

    # from a file
    python3 fix_colors.py --game-set-json output/tmp/find4_raw.json > output/tmp/find4_colored.json

    # check whether colors are already valid (exit code 0 = clean pass-through)
    python3 fix_colors.py --game-set-json my_game.json | diff my_game.json -
"""

import argparse
import json
import sys
from typing import Any

COLOR_PALETTE = ["red", "blue", "green", "yellow", "orange", "indigo", "purple", "teal"]
REQUIRED_COUNT = 4


def fix_color_groups(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and fix colors in every group_set.
    Each group_set must have exactly 4 groups, each with a distinct valid color.
    If colors are invalid or duplicated, assigns the first 4 palette colors in order.
    """
    if "game_sets" not in data:
        return data

    for game_set in data["game_sets"]:
        if "group_sets" not in game_set:
            continue

        for group_set in game_set["group_sets"]:
            # Collect current colors
            current_colors = [g.get("color", "").lower() for g in group_set]
            current_color_set = set(current_colors)

            # Valid if: exactly 4 distinct colors, all from palette
            valid = len(current_color_set) == REQUIRED_COUNT and current_color_set.issubset(set(COLOR_PALETTE))

            if not valid:
                # Assign first 4 palette colors positionally
                for i, group in enumerate(group_set):
                    group["color"] = COLOR_PALETTE[i % REQUIRED_COUNT]

    return data


def main():
    parser = argparse.ArgumentParser(description="Fix colors in find4 game JSON")
    parser.add_argument("--game-set-json", metavar="FILE", help="Input JSON file (default: read from stdin)")
    args = parser.parse_args()

    try:
        if args.game_set_json:
            with open(args.game_set_json, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.load(sys.stdin)
    except FileNotFoundError:
        print(f"Error: File not found: {args.game_set_json}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(1)

    result = fix_color_groups(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
