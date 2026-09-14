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

# Derive combined JSON path from output/games/ — game_split.py writes split files
# beside the combined JSON, so it must be called on the games/ copy, not the tmp file.
parent_stem=$(python3 -c "import json; m=json.load(open(\"$FINAL_JSON\"))[\"metadata\"]; print(m[\"suggested_name\"].replace(\".json\",\"\"))")
combined_json="output/games/${parent_stem}/${parent_stem}.json"
if [[ ! -f "$combined_json" ]]; then
  mkdir -p "output/games/${parent_stem}"
  cp "$FINAL_JSON" "$combined_json"
  echo "INFO: copied $(basename "$FINAL_JSON") to $combined_json" >&2
fi

split_details=$("${FIND4_SCRIPTS}/game_split.py" --mark-combined --skill-root "$RUNDIR" "$combined_json")

while IFS= read -r split_detail; do
  [[ -n "$split_detail" ]] || continue

  parent_stem=$(echo "$split_detail" | jq -r '.slug')

  while IFS= read -r split_json_file; do
    [[ -f "$split_json_file" ]] || { echo "WARN: not found: $split_json_file" >&2; continue; }

    slug=$(basename "$split_json_file" .json)
    mkdir -p "output/games/${parent_stem}/html"
    # No cp needed — game_split.py already wrote split files beside the combined JSON

    # share_game.sh writes JSON content; generate_html.py reads _share_url.txt as JSON.
    # Extension is .txt by convention — content is JSON ({"share_url": "https://..."}).
    share_url_txt="output/games/${parent_stem}/html/${slug}.html_share_url.txt"

    FIND4_URL="$FIND4_URL" bash "${FIND4_SCRIPTS}/share_game.sh" \
      --compress \
      --no-compact \
      --format json \
      --output-filename "$share_url_txt" \
      "$split_json_file"

    python3 "${FIND4_SCRIPTS}/generate_html.py" \
      --game-json "$split_json_file" \
      --as-widget \
      --output "output/games/${parent_stem}/html/${slug}.html"

  done < <(echo "$split_detail" | jq -r '.splitfilenames[]')
done <<< "$split_details"
