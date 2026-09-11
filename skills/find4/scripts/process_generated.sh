#!/usr/bin/env bash
# Split combined JSON, generate share URLs, and produce standalone HTML files.
set -euo pipefail

FIND4_SCRIPTS="${FIND4_SCRIPTS:-$(cd "$(dirname "$0")" && pwd)}"
FIND4_URL="${FIND4_URL:-https://find4.org}"
RUNDIR="${RUNDIR:-$(pwd)}"

# Source utilities (find4_final_json resolver + manifest builder)
. "${FIND4_SCRIPTS}/find4_utils.sh"

# Resolve find4_final.json — accepts FINAL_JSON env override or searches
FINAL_JSON=$(find4_final_json "${FINAL_JSON:-}") || exit 1

[[ -f "$FINAL_JSON" ]] || { echo "ERROR: $FINAL_JSON not found" >&2; exit 1; }

split_details=$("${FIND4_SCRIPTS}/game_split.py" --mark-combined --skill-root "$RUNDIR" "$FINAL_JSON")

while IFS= read -r split_detail; do
  [[ -n "$split_detail" ]] || continue

  while IFS= read -r split_json_file; do
    [[ -f "$split_json_file" ]] || { echo "WARN: not found: $split_json_file" >&2; continue; }

    slug=$(basename "$split_json_file" .json)
    mkdir -p "output/games/html"

    # share_game.sh writes JSON content; generate_html.py reads _share_url.txt as JSON.
    # Extension is .txt by convention — content is JSON ({"share_url": "https://..."}). 
    share_url_txt="output/games/html/${slug}.html_share_url.txt"

    FIND4_URL="$FIND4_URL" bash "${FIND4_SCRIPTS}/share_game.sh" \
      --compress \
      --no-compact \
      --format json \
      --output-filename "$share_url_txt" \
      "$split_json_file"

    python3 "${FIND4_SCRIPTS}/generate_html.py" \
      --game-json "$split_json_file" \
      --as-widget \
      --output "output/games/html/${slug}.html"

  done < <(echo "$split_detail" | jq -r '.splitfilenames[]')
done <<< "$split_details"
