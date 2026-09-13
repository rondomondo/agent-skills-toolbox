#!/usr/bin/env bash
#
# share_game.sh - Encodes find4 game JSON for URL sharing.
#
#  # Verify URL from stdin against the original file
#  echo "https://find4.org/#game=..." | share_game.sh --verify - games/foo.json
#
#  # Verify URL from a file against the original
#  share_game.sh --verify url.txt games/foo.json
#
#  # Decode and pretty-print only (no original to compare)
#  echo "https://find4.org/#game=..." | share_game.sh --verify -
#


set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Configuration ---
GAME_URL="${FIND4_URL:-https://find4.org}"
MAX_JSON_SIZE=5120  # 5KB threshold for safe Base64 URLs

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

# --- Functions ---

ok()   { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${GREEN}${*}${RESET}\n"  >&2; return 0; }
warn() { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${YELLOW}${*}${RESET}\n" >&2; return 0; }
fail() { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${RED}${*}${RESET}\n"    >&2; return 0; }
log()  { ${USE_LOGGING} && printf "${BOLD}[$SCRIPT_NAME]${RESET} ${CYAN}${*}${RESET}\n"   >&2; return 0; }

usage() {
    printf "${GREEN}" >&2
    cat >&2 <<EOF
Usage: $0 [--url URL] [--game-set-json FILE] [--compress] [--compact] [--format json|text] [--output-filename FILE] [FILE]
       $0 --verify [FILE]  (reads share URL from stdin or FILE, decodes and compares)
       Reads from stdin if no file is given.
       Default: deflate compression enabled, no compacting. Use --no-compress to disable compression.
       Use --compact to strip non-essential fields before encoding.
       Use --format text to output the share URL only (default: json with stats).
       Use --output-filename FILE to write output to a file instead of stdout.
         Auto-derive path: output/games/html/<SLUG>.html_share_url.txt (if input is a .json file).
EOF
    printf "${RESET}" >&2
    exit 1
}

log "called with arguments '$*'"

# Logic to determine where the data is coming from
resolve_input_source() {
    local file_arg="$1"
    if [[ -n "$file_arg" && "$file_arg" != "-" ]]; then
        [[ -f "$file_arg" ]] || { fail "Error: file not found: $file_arg"; exit 1; }
        echo "$file_arg"
    elif [[ "$file_arg" == "-" ]]; then
        echo "-"
    else
        if [[ -t 0 ]]; then
            fail "Error: no file specified and stdin is a terminal"
            usage
        fi
        echo "-"
    fi
}

# Check file size and warn if it exceeds the safe limit for URL sharing
check_payload_size() {
    local source="$1"
    local size
    
    if [[ "$source" == "-" ]]; then
        # For stdin, we'd have to buffer it to check size, so we'll skip 
        # or check after Python reads it. If it's a file, we check now:
        return 0
    fi

    size=$(wc -c < "$source")
    if [ "$size" -gt "$MAX_JSON_SIZE" ]; then
        warn "Game file is large ($size bytes). Share URLs over 8KB may be truncated by some browsers/apps."
    fi
}

# Perform the compression and encoding using Python.
# Field order must match SHARE_SCHEMA in find4.js.
# Outputs three tab-separated fields: <b64> <raw_bytes> <enc_bytes>
# raw_bytes and enc_bytes are equal when compression is disabled.
encode_payload() {
    local source="$1"
    local compress="$2"
    local do_compact="$3"
    python3 -c "
import sys, base64, zlib, json

SHARE_SCHEMA = ['words', 'category', 'color', 'group_item_id', 'group_set_id']

def compact(data):
    return {
        'v': 2,
        'game_sets': [
            {
                'theme': gs['theme'],
                'game_set_id': gs['game_set_id'],
                'group_sets': [
                    [[item.get(k) for k in SHARE_SCHEMA] for item in group_set]
                    for group_set in gs['group_sets']
                ],
            }
            for gs in data['game_sets']
        ],
    }

try:
    raw = open(sys.argv[1], 'rb').read() if sys.argv[1] != '-' else sys.stdin.buffer.read()
    data = json.loads(raw)
    out = compact(data) if sys.argv[3] == '1' else data
    payload = json.dumps(out, separators=(',', ':')).encode()
    raw_bytes = len(payload)
    if sys.argv[2] == '1':
        payload = zlib.compress(payload, level=9, wbits=-15)
    enc_bytes = len(payload)
    b64 = base64.urlsafe_b64encode(payload).decode().strip()
    print(f'{b64}\t{raw_bytes}\t{enc_bytes}')
except Exception as e:
    print(f'Encoding error: {e}', file=sys.stderr)
    sys.exit(1)
" "$source" "$compress" "$do_compact"
}

# Decode a share URL and compare its payload against the original game file
verify_payload() {
    local source="$1"
    local original="${2:--}"
    local do_compact="${3:-0}"
    python3 -c "
import sys, base64, zlib, json, urllib.parse

SHARE_SCHEMA = ['words', 'category', 'color', 'group_item_id', 'group_set_id']

def compact(data):
    return {
        'v': 2,
        'game_sets': [
            {
                'theme': gs['theme'],
                'game_set_id': gs['game_set_id'],
                'group_sets': [
                    [[item.get(k) for k in SHARE_SCHEMA] for item in group_set]
                    for group_set in gs['group_sets']
                ],
            }
            for gs in data['game_sets']
        ],
    }

def decode_b64(b64):
    # Try decompressed first, fall back to raw JSON
    raw = base64.urlsafe_b64decode(b64 + '==')
    try:
        return json.loads(zlib.decompress(raw, wbits=-15))
    except Exception:
        return json.loads(raw)

try:
    url_line = (open(sys.argv[1]).read() if sys.argv[1] != '-' else sys.stdin.read()).strip()
    fragment = url_line.split('#game=', 1)
    if len(fragment) != 2:
        print('Error: no #game= fragment found in input', file=sys.stderr)
        sys.exit(1)
    b64 = fragment[1].strip()
    decoded = decode_b64(b64)

    if sys.argv[2] != '-':
        original = json.loads(open(sys.argv[2], 'rb').read())
        expected = compact(original) if sys.argv[3] == '1' else original
        if decoded == expected:
            print('OK: decoded payload matches original')
        else:
            import difflib
            a = json.dumps(expected, indent=2).splitlines()
            b = json.dumps(decoded, indent=2).splitlines()
            diff = list(difflib.unified_diff(a, b, fromfile='original', tofile='decoded', lineterm=''))
            if diff:
                print('MISMATCH: differences found:', file=sys.stderr)
                print('\n'.join(diff), file=sys.stderr)
            else:
                print('MISMATCH: objects differ but no textual diff (type/order issue)', file=sys.stderr)
            sys.exit(1)
    else:
        print(json.dumps(decoded, indent=2))
except Exception as e:
    print(f'Verify error: {e}', file=sys.stderr)
    sys.exit(1)
" "$source" "$original" "$do_compact"
}

# Derive the default output filename from the input JSON path.
# Extension matches --format: .json for json output, .txt for text.
derive_output_filename() {
    local source="$1"
    local fmt="$2"
    if [[ "$source" == "-" ]]; then
        echo ""
        return
    fi
    local slug ext
    slug=$(basename "$source" .json)
    [[ "$fmt" == "json" ]] && ext="json" || ext="txt"
    echo "output/games/html/${slug}.html_share_url.${ext}"
}

# Format the final URL, with optional JSON output including stats
print_share_link() {
    local b64="$1"
    local source="$2"
    local fmt="$3"
    local output_file="$4"
    local options_summary="$5"
    local raw_bytes="$6"   # uncompressed payload size; empty if compression not used
    local enc_bytes="$7"   # compressed payload size; empty if compression not used
    local share_url="${GAME_URL}/#game=${b64}"

    local slug=""
    [[ "$source" != "-" ]] && slug=$(basename "$source" .json)

    local content
    if [[ "$fmt" == "text" ]]; then
        content="$share_url"
    elif [[ "$source" == "-" ]]; then
        content=$(jq -n \
            --arg share_url "$share_url" \
            --arg raw_bytes "$raw_bytes" \
            --arg enc_bytes "$enc_bytes" \
            '{
                source: "stdin",
                share_url: $share_url,
                compression: (if $raw_bytes != "" then {
                    raw_bytes: ($raw_bytes | tonumber),
                    enc_bytes: ($enc_bytes | tonumber),
                    ratio: (($enc_bytes | tonumber) / ($raw_bytes | tonumber) * 100 | round | tostring + "%")
                } else null end)
            }')
    else
        content=$(jq \
            --arg source "$source" \
            --arg slug "$slug" \
            --arg share_url "$share_url" \
            --arg raw_bytes "$raw_bytes" \
            --arg enc_bytes "$enc_bytes" \
            '{
                source: $source,
                slug: $slug,
                stats: {
                    game_sets: (.game_sets | length),
                    group_sets: ([.game_sets[].group_sets | length] | add // 0),
                    items: ([.game_sets[].group_sets[][] | .words | length] | add // 0),
                    themes: [.game_sets[].theme]
                },
                compression: (if $raw_bytes != "" then {
                    raw_bytes: ($raw_bytes | tonumber),
                    enc_bytes: ($enc_bytes | tonumber),
                    ratio: (($enc_bytes | tonumber) / ($raw_bytes | tonumber) * 100 | round | tostring + "%")
                } else null end),
                share_url: $share_url
            }' "$source")
    fi

    if [[ -n "$output_file" ]]; then
        mkdir -p "$(dirname "$output_file")"
        printf "%s\n" "$content" > "$output_file"
        log "share_game.sh %s" "$options_summary"
        ok "Share link written to $output_file"
        jq -n --arg input_file "$source" --arg output_file "$output_file" \
            '{input_file: $input_file, share_url_file: $output_file}'
    else
        printf "%s\n" "$content"
    fi
}

# --- Main Logic ---

main() {
    local game_file=""
    local compress="1"
    local do_compact="0"
    local verify="0"
    local verify_against=""
    local fmt="json"
    local output_file=""
    local output_file_explicit=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --url)            GAME_URL="$2"; shift 2 ;;
            --game-set-json)  game_file="$2"; shift 2 ;;
            --compress)       compress="1"; shift ;;
            --no-compress)    compress="0"; shift ;;
            --compact)        do_compact="1"; shift ;;
            --no-compact)     do_compact="0"; shift ;;
            --verify)         verify="1"; shift ;;
            --output-filename)
                output_file_explicit="$2"
                shift 2 ;;
            --format)
                case "$2" in
                    json|text) fmt="$2"; shift 2 ;;
                    *) fail "Error: --format must be json or text, got '$2'"; usage ;;
                esac ;;
            --help|-h)        usage ;;
            -)                game_file="-"; shift ;;
            -*)               fail "Error: unknown flag: $1"; usage ;;
            *)
                if [[ "$verify" == "1" ]]; then
                    # First positional arg after --verify is the share URL source;
                    # second (optional) is the original game file to compare against.
                    if [[ -z "$game_file" ]]; then
                        game_file="$1"
                    else
                        verify_against="$1"
                    fi
                elif [[ "$1" != */* && ! -f "$1" ]]; then
                    game_file="games/$1"
                else
                    game_file="$1"
                fi
                shift ;;
        esac
    done

    if [[ "$verify" == "1" ]]; then
        local url_source
        url_source=$(resolve_input_source "$game_file")
        # Resolve original file path the same way the encode path does
        local original_source="${verify_against:-}"
        if [[ -n "$original_source" && "$original_source" != */* && ! -f "$original_source" ]]; then
            original_source="games/$original_source"
        fi
        verify_payload "$url_source" "${original_source:--}" "$do_compact"
        return
    fi

    local source
    source=$(resolve_input_source "$game_file")

    # Resolve output filename: explicit flag > auto-derived from input path
    if [[ -n "$output_file_explicit" ]]; then
        output_file="$output_file_explicit"
    else
        output_file=$(derive_output_filename "$source" "$fmt")
    fi

    # Build a summary of the options used, for the output file header
    local options_summary
    options_summary="$(
        [[ "$compress"   == "1" ]] && printf -- "--compress "   || printf -- "--no-compress "
        [[ "$do_compact" == "1" ]] && printf -- "--compact "    || printf -- "--no-compact "
        printf -- "--format %s " "$fmt"
        [[ -n "$output_file" ]] && printf -- "--output-filename %s " "$output_file"
    )"

    # Run the size check
    check_payload_size "$source"

    # Generate the Base64 plus payload size metrics
    local encode_out b64_string raw_bytes enc_bytes
    encode_out=$(encode_payload "$source" "$compress" "$do_compact")
    b64_string=$(printf "%s" "$encode_out" | cut -f1)
    raw_bytes=$(printf "%s"  "$encode_out" | cut -f2)
    enc_bytes=$(printf "%s"  "$encode_out" | cut -f3)

    # Only pass sizes when compression was applied; equal values mean no compression
    local ratio_raw="" ratio_enc=""
    if [[ "$compress" == "1" ]]; then
        ratio_raw="$raw_bytes"
        ratio_enc="$enc_bytes"
    fi

    # Final Output
    print_share_link "$b64_string" "$source" "$fmt" "$output_file" "$options_summary" "$ratio_raw" "$ratio_enc"
}
main "$@"
log "[$*] completed successfully"
