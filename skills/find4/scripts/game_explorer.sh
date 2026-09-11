#!/usr/bin/env bash

set -e

JSON_FILE="${1:-}"

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

_init_colors() {
  if [[ -n "${NO_COLOR:-}" ]] || [[ ! -t 2 ]]; then
    RED='' GREEN='' YELLOW='' CYAN='' BOLD='' RESET=''
  fi
}
_init_colors

USE_LOGGING="${DEBUG:-true}"
case "${USE_LOGGING}" in
  true|1)  USE_LOGGING=true  ;;
  false|0) USE_LOGGING=false ;;
  *) printf "ERROR: DEBUG must be true/false/1/0, got '%s'\n" "${USE_LOGGING}" >&2; exit 1 ;;
esac
SCRIPT_NAME=$(basename "$0")

ok()   { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${GREEN}${*}${RESET}\n"  >&2; return 0; }
warn() { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${YELLOW}${*}${RESET}\n" >&2; return 0; }
fail() { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${RED}${*}${RESET}\n"    >&2; return 0; }
log()  { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${CYAN}${*}${RESET}\n"   >&2; return 0; }

print_usage() {
    printf "${BOLD}Usage:${RESET} $0 ${YELLOW}<json_file>${RESET} ${YELLOW}[command]${RESET} ${YELLOW}[arg]${RESET}\n" >&2
    printf "\n${BOLD}Commands:${RESET}\n" >&2
    printf "  ${CYAN}summary${RESET}    Show themes, game_set_ids, and record counts\n" >&2
    printf "  ${CYAN}themes${RESET}     List all unique themes\n" >&2
    printf "  ${CYAN}experts${RESET}    List all 'Expert' level categories\n" >&2
    printf "  ${CYAN}search${RESET}     Search for a specific word (requires 3rd arg)\n" >&2
    printf "  ${CYAN}flatten${RESET}    Export a CSV-like list of Category, Color, and Skill\n" >&2
    printf "  ${CYAN}stats${RESET}      Count categories by skill level\n" >&2
    printf "  ${CYAN}game${RESET}       Show full JSON for a game_set_id (requires 3rd arg)\n" >&2
    printf "  ${CYAN}counts${RESET}     Show totals: game_sets, group_sets, and categories\n" >&2
    printf "\n${BOLD}Examples:${RESET}\n" >&2
    printf "  $0 library/world-cup-facts.json\n" >&2
    printf "  $0 library/world-cup-facts.json summary\n" >&2
    printf "  $0 library/world-cup-facts.json themes\n" >&2
    printf "  $0 library/world-cup-facts.json counts\n" >&2
    printf "  $0 library/world-cup-facts.json stats\n" >&2
    printf "  $0 library/world-cup-facts.json experts\n" >&2
    printf "  $0 library/world-cup-facts.json search \"penalty\"\n" >&2
    printf "  $0 library/world-cup-facts.json game 45c395\n" >&2
    printf "  $0 library/world-cup-facts.json flatten | column -t -s \$'\\t'\n" >&2
}

check_deps() {
    if ! command -v jq &> /dev/null; then
        fail "'jq' is not installed. Please install it to use this script."
        exit 1
    fi
}

check_file() {
    if [[ -z "$1" || ! -f "$1" ]]; then
        fail "JSON file not found or not provided."
        print_usage
        exit 1
    fi
}

require_arg() {
    local val="$1" name="$2" hint="$3"
    if [[ -z "$val" ]]; then
        fail "$name required as the 3rd argument."
        [[ -n "$hint" ]] && log "$hint"
        exit 1
    fi
}

cmd_summary() {
    echo "### DATA SUMMARY ###"
    jq -r '.game_sets[] | "[\(.game_set_id)] \(.theme) -- \(.group_sets | length) group_set(s), \([.group_sets[][] ] | length) categories"' "$JSON_FILE"
}

cmd_themes() {
    jq -r '.game_sets[].theme' "$JSON_FILE" | sort -u
}

cmd_experts() {
    echo "### EXPERT LEVEL CONTENT ###"
    jq -r '.game_sets[].group_sets[][] | select(.skill_level == "Expert") | "- \(.category) (\(.theme))"' "$JSON_FILE"
}

cmd_search() {
    local query="$1"
    require_arg "$query" "Search term" ""
    echo "Searching for: $query..."
    jq --arg q "$query" '.game_sets[].group_sets[][] | select(.words[] | contains($q))' "$JSON_FILE"
}

cmd_flatten() {
    printf "CATEGORY\tCOLOR\tSKILL\n"
    jq -r '.game_sets[].group_sets[][] | [ .category, .color, .skill_level ] | @tsv' "$JSON_FILE"
}

cmd_stats() {
    echo "### SKILL LEVEL DISTRIBUTION ###"
    jq -r '[.game_sets[].group_sets[][] .skill_level] | group_by(.) | .[] | "\(.[0]): \(length)"' "$JSON_FILE"
}

cmd_game() {
    local id="$1"
    require_arg "$id" "game_set_id" "Run '$0 $JSON_FILE summary' to list available IDs."
    local result
    result=$(jq --arg id "$id" '.game_sets[] | select(.game_set_id == $id)' "$JSON_FILE")
    if [[ -z "$result" ]]; then
        fail "No game_set found with id '$id'."
        log "Run '$0 $JSON_FILE summary' to list available IDs."
        exit 1
    fi
    echo "$result"
}

cmd_counts() {
    echo "### COUNTS ###"
    jq -r '
      "Game sets:   \(.game_sets | length)",
      "Group sets:  \([.game_sets[].group_sets[]] | length)",
      "Categories:  \([.game_sets[].group_sets[][] ] | length)"
    ' "$JSON_FILE"
}

# --- Validation ---
check_deps
check_file "$JSON_FILE"

COMMAND="${2:-summary}"

# --- Dispatch ---
case "$COMMAND" in
    summary)  cmd_summary ;;
    themes)   cmd_themes ;;
    experts)  cmd_experts ;;
    search)   cmd_search "${3:-}" ;;
    flatten)  cmd_flatten ;;
    stats)    cmd_stats ;;
    game)     cmd_game "${3:-}" ;;
    counts)   cmd_counts ;;
    *)
        fail "Unknown command '$COMMAND'"
        print_usage
        exit 1
        ;;
esac
