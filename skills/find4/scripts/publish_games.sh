#!/usr/bin/env bash
# Publish generated games from output/games/ into the skill's games/ and library/ directories.

set -euo pipefail

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

USE_LOGGING="${DEBUG:-false}"
case "${USE_LOGGING}" in
  true|1)  USE_LOGGING=true  ;;
  false|0) USE_LOGGING=false ;;
  *) printf "ERROR: DEBUG must be true/false/1/0, got '%s'\n" "${USE_LOGGING}" >&2; exit 1 ;;
esac
SCRIPT_NAME=$(basename "$0")

ok()   { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${GREEN}${*}${RESET}\n"  >&2; return 0; }
warn() { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${YELLOW}${*}${RESET}\n" >&2; return 0; }
fail() {                   printf "${BOLD}[$SCRIPT_NAME]${RESET} ${RED}${*}${RESET}\n"    >&2; return 0; }
log()  { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${CYAN}${*}${RESET}\n"   >&2; return 0; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Publish generated games from <src>/games/ into a Find4 skill directory.

Options:
  --src DIR      Root directory containing games/ (default: .)
  --dst DIR      Skill root to publish into (default: <src>/skills/find4)
  --dry-run      Print what would be copied without doing it
  --remove-src   Recursively delete --src after publishing
  -h, --help     Show this help and exit

Examples:
  $(basename "$0") --src /tmp/generated
  $(basename "$0") --src /tmp/generated --dst skills/find4 --dry-run
EOF
}

SRC_ROOT="."
DST_ROOT=""
DRY_RUN=false
REMOVE_SRC=false

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --src)        SRC_ROOT="$2"; shift 2 ;;
      --dst)        DST_ROOT="$2"; shift 2 ;;
      --dry-run)    DRY_RUN=true; shift ;;
      --remove-src) REMOVE_SRC=true; shift ;;
      -h|--help) usage; exit 0 ;;
      *) printf "Unknown option: %s\n" "$1" >&2; usage >&2; exit 1 ;;
    esac
  done

  SRC_ROOT="${SRC_ROOT%/}"

  if [[ -z "$DST_ROOT" ]]; then
    DST_ROOT="${SRC_ROOT}/skills/find4"
  fi
  DST_ROOT="${DST_ROOT%/}"
}

validate_dirs() {
  local games_src="$1" games_dst="$2" library_dst="$3"
  if [[ ! -d "$games_src" ]];   then fail "source directory not found: $games_src";        exit 1; fi
  if [[ ! -d "$games_dst" ]];   then fail "destination games/ not found: $games_dst";      exit 1; fi
  if [[ ! -d "$library_dst" ]]; then fail "destination library/ not found: $library_dst";  exit 1; fi
}

copy_file() {
  local src="$1" dst="$2"
  if [[ "$DRY_RUN" == true ]]; then
    ok "[dry-run] cp -R $src  ->  $dst"
  else
    cp -R "$src" "$dst"
    ok "copied  $src  ->  $dst"
  fi
}

_read_split_info() {
  local json_file="$1"
  python3 - "$json_file" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
si = d.get("metadata", {}).get("split_info", {})
print(si.get("role", ""))
print(si.get("parent_file", ""))
print(si.get("slug", ""))
PYEOF
}

copy_split_to_library() {
  local json_file="$1" library_dst="$2"
  local role parent_file split_slug parent_stem lib_subdir info

  info="$(_read_split_info "$json_file" 2>/dev/null || true)"
  role="$(sed -n '1p' <<< "$info")"
  [[ "$role" == "split" ]] || return 0

  parent_file="$(sed -n '2p' <<< "$info")"
  split_slug="$(sed -n '3p' <<< "$info")"
  [[ -n "$parent_file" && -n "$split_slug" ]] || return 0

  parent_stem="$(basename "${parent_file%.json}")"
  lib_subdir="${library_dst}/${parent_stem}"

  if [[ "$DRY_RUN" == true ]]; then
    ok "[dry-run] mkdir -p $lib_subdir"
    ok "[dry-run] cp $json_file  ->  ${lib_subdir}/${split_slug}.json"
  else
    mkdir -p "$lib_subdir"
    cp "$json_file" "${lib_subdir}/${split_slug}.json"
    ok "copied  $json_file  ->  ${lib_subdir}/${split_slug}.json"
  fi
}

archive_src_dir() {
  local src_dir="$1"
  if [[ ! -d "$src_dir" ]]; then
    warn "archive_src_dir: $src_dir not found, skipping"
    return 0
  fi

  local timestamp slug zip_name log_dir
  timestamp="$(date '+%Y%m%d%H%M')"
  slug="$(printf '%s' "$src_dir" | tr '/' '_' | sed 's/^_//')"
  zip_name="output.${slug}.${timestamp}.zip"
  log_dir="logs/raw/$(date '+%Y%m%d')"

  if [[ "$DRY_RUN" == true ]]; then
    ok "[dry-run] zip -r /tmp/${zip_name} $src_dir"
    log "[dry-run] mkdir -p $log_dir"
    log "[dry-run] mv /tmp/${zip_name} ${log_dir}/${zip_name}"
    return 0
  fi

  zip -r "/tmp/${zip_name}" "$src_dir"
  mkdir -p "$log_dir"
  mv "/tmp/${zip_name}" "${log_dir}/${zip_name}"
  ok "archived $src_dir -> ${log_dir}/${zip_name}"
}

publish_game() {
  local slug="$1" games_src="$2" games_dst="$3" library_dst="$4"
  local game_dir="${games_src}/${slug}"
  local combined="${games_src}/${slug}.json"

  if [[ -f "$combined" ]]; then
    copy_file "$combined" "${library_dst}/"
  fi

  for json_file in "${game_dir}"/*.json; do
    [[ -f "$json_file" ]] || continue
    copy_file "$json_file" "${games_dst}/"
    copy_split_to_library "$json_file" "$library_dst"
  done
}

copy_asset_dirs() {
  local games_src="$1" games_dst="$2"
  for subdir in html screenshots; do
    local src_subdir="${games_src}/${subdir}"
    [[ -d "$src_subdir" ]] || continue
    if [[ "$DRY_RUN" == true ]]; then
      ok "[dry-run] cp -Ra $src_subdir/.  ->  ${games_dst}/${subdir}/"
    else
      cp -Ra "$src_subdir/." "${games_dst}/${subdir}/"
      ok "copied  $src_subdir/.  ->  ${games_dst}/${subdir}/"
    fi
  done
}

remove_src() {
  if [[ "$REMOVE_SRC" == true ]]; then
    if [[ "$DRY_RUN" == true ]]; then
      ok "[dry-run] rm -rf $SRC_ROOT"
    else
      rm -rf "$SRC_ROOT"
      ok "removed $SRC_ROOT"
    fi
  fi
}

publish_all() {
  local games_src="${SRC_ROOT}/games"
  local games_dst="${DST_ROOT}/games"
  local library_dst="${DST_ROOT}/library"

  validate_dirs "$games_src" "$games_dst" "$library_dst"

  for game_dir in "${games_src}"/*/; do
    [[ -d "$game_dir" ]] || continue
    local slug
    slug="$(basename "$game_dir")"
    publish_game "$slug" "$games_src" "$games_dst" "$library_dst"
  done

  copy_asset_dirs "$games_src" "$games_dst"
  archive_src_dir "$SRC_ROOT"
  ok "Done."
}

log "running ${SCRIPT_NAME} with args: $*"
parse_args "$@"
publish_all
remove_src
