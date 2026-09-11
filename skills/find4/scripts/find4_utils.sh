#!/usr/bin/env bash
# find4_utils.sh — sourced utility functions for the Find4 skill pipeline.
#
# Source this at the top of any script that needs it:
#   . "$(dirname "$0")/find4_utils.sh"
#
# Functions provided:
#   find4_final_json [HINT]   -- resolve find4_final.json to absolute path
#   find4_manifest [RUNDIR]   -- emit a JSON manifest of all output files

# ---------------------------------------------------------------------------
# find4_final_json [HINT]
#
# Resolves find4_final.json to an absolute path. Tries candidates in order:
#
#   1. FINAL_JSON env var (if set and file exists)
#   2. HINT argument (if provided and file exists)
#   3. $RUNDIR/output/tmp/find4_final.json       (sandbox / standard layout)
#   4. results/output/tmp/find4_final.json       (repo layout, relative to cwd)
#   5. output/tmp/find4_final.json               (cwd-relative fallback)
#   6. find(1) search under cwd and $HOME        (last resort)
#
# Prints the absolute path to stdout on success.
# Prints an error to stderr and returns 1 on failure.
#
# Usage:
#   FINAL_JSON=$(find4_final_json)               # no hint
#   FINAL_JSON=$(find4_final_json "some/path")   # with hint
# ---------------------------------------------------------------------------
find4_final_json() {
    local hint="${1:-}"
    local candidate abs

    _f4_abs() {
        # Resolve a path to absolute without requiring it to exist yet.
        # Uses pwd -P to avoid symlink confusion.
        case "$1" in
            /*) printf '%s' "$1" ;;
            *)  printf '%s/%s' "$(pwd -P)" "$1" ;;
        esac
    }

    _f4_try() {
        local p="$1"
        [ -z "$p" ] && return 1
        [ -f "$p" ] || return 1
        abs="$(_f4_abs "$p")"
        printf '%s\n' "$abs"
        return 0
    }

    # 1. Env var
    _f4_try "${FINAL_JSON:-}" && return 0

    # 2. Caller hint
    _f4_try "$hint" && return 0

    # 3. $RUNDIR/output/tmp/find4_final.json
    if [ -n "${RUNDIR:-}" ]; then
        _f4_try "${RUNDIR}/output/tmp/find4_final.json" && return 0
    fi

    # 4. results/output/tmp/find4_final.json (repo layout, process_generated.sh cwd)
    _f4_try "results/output/tmp/find4_final.json" && return 0

    # 5. output/tmp/find4_final.json (plain cwd-relative)
    _f4_try "output/tmp/find4_final.json" && return 0

    # 6. Last resort: find under cwd, then HOME (cap at 4 levels deep to stay fast)
    for searchroot in "$(pwd -P)" "${HOME:-}"; do
        [ -z "$searchroot" ] && continue
        candidate=$(find "$searchroot" -maxdepth 4 -name "find4_final.json" \
                         ! -path "*/gh-push/*" \
                         ! -path "*/zip_stage/*" \
                         -print -quit 2>/dev/null)
        _f4_try "$candidate" && return 0
    done

    printf 'find4_utils: find4_final.json not found (set FINAL_JSON or RUNDIR)\n' >&2
    return 1
}

# ---------------------------------------------------------------------------
# find4_manifest [RUNDIR]
#
# Walks the output tree under RUNDIR (defaults to $RUNDIR env var, then cwd)
# and emits a JSON object with:
#
#   {
#     "generated_at": "<ISO timestamp>",
#     "rundir": "<absolute path>",
#     "tree": "<ASCII tree string>",
#     "files": [
#       { "path": "<relative path>",
#         "abs": "<absolute path>",
#         "size_bytes": 12345,
#         "type": "json|html|png|zip|txt|other" },
#       ...
#     ],
#     "counts": { "json": N, "html": N, "png": N, "zip": N, "txt": N, "other": N, "total": N }
#   }
#
# Writes JSON to stdout. Use 2>/dev/null to suppress find noise.
#
# Usage:
#   find4_manifest               # uses $RUNDIR or cwd
#   find4_manifest /home/claude  # explicit root
#   find4_manifest > output/tmp/manifest.json
# ---------------------------------------------------------------------------
find4_manifest() {
    local root="${1:-${RUNDIR:-$(pwd -P)}}"
    root="$(cd "$root" && pwd -P)"
    local outdir="${root}/output"

    if [ ! -d "$outdir" ]; then
        printf '{"error":"output dir not found","rundir":"%s"}\n' "$root"
        return 1
    fi

    # -- ASCII tree (uses filetree.sh if available, plain find otherwise) ----
    local tree_str=""
    local filetree_bin=""

    # Locate filetree.sh: alongside this script, or in FIND4_SCRIPTS
    for candidate in \
        "$(dirname "$0")/filetree.sh" \
        "${FIND4_SCRIPTS:-}/filetree.sh" \
        "$(command -v filetree.sh 2>/dev/null)"
    do
        [ -x "$candidate" ] && { filetree_bin="$candidate"; break; }
    done

    if [ -n "$filetree_bin" ]; then
        tree_str=$("$filetree_bin" \
            --exclude-dirs "gh-push:zip_stage:__pycache__" \
            "$outdir" 2>/dev/null || true)
    else
        # Fallback: plain indented find
        tree_str=$(find "$outdir" \
            \( -name "gh-push" -o -name "zip_stage" -o -name "__pycache__" \) -prune \
            -o -print 2>/dev/null | sort | sed "s|${outdir}||" | sed 's|^/||')
    fi
    # Escape tree string for JSON (backslash, quote, newline, tab)
    tree_str=$(printf '%s' "$tree_str" \
        | sed 's/\\/\\\\/g; s/"/\\"/g' \
        | awk '{printf "%s\\n", $0}' \
        | sed 's/\\n$//')

    # -- File list via find + awk for JSON assembly --------------------------
    local files_json
    files_json=$(find "$outdir" \
        \( -name "gh-push" -o -name "zip_stage" -o -name "__pycache__" \) -prune \
        -o -type f -print 2>/dev/null \
        | sort \
        | awk -v root="$root" -v outdir="$outdir" '
        BEGIN {
            ORS = ""
            print "["
            first = 1
        }
        {
            abs = $0
            rel = abs
            sub("^" root "/", "", rel)

            # size via wc -c (portable, no stat -c needed)
            cmd = "wc -c < \"" abs "\" 2>/dev/null"
            sz = 0
            if ((cmd | getline line) > 0) sz = line + 0
            close(cmd)

            # type bucket
            n = split(abs, parts, ".")
            ext = (n > 1) ? parts[n] : ""
            if      (ext == "json")            t = "json"
            else if (ext == "html")            t = "html"
            else if (ext == "png")             t = "png"
            else if (ext == "zip")             t = "zip"
            else if (ext == "txt")             t = "txt"
            else if (ext == "sh" || ext == "py") t = "script"
            else                               t = "other"

            if (!first) print ","
            first = 0
            printf "{\"path\":\"%s\",\"abs\":\"%s\",\"size_bytes\":%d,\"type\":\"%s\"}",
                rel, abs, sz, t
        }
        END { print "]" }
    ')

    # -- Counts via a second pass (awk over the file list) -------------------
    local counts_json
    counts_json=$(find "$outdir" \
        \( -name "gh-push" -o -name "zip_stage" -o -name "__pycache__" \) -prune \
        -o -type f -print 2>/dev/null \
        | awk '
        BEGIN { json=0; html=0; png=0; zip=0; txt=0; script=0; other=0 }
        {
            n = split($0, p, ".")
            ext = (n > 1) ? p[n] : ""
            if      (ext == "json")              json++
            else if (ext == "html")              html++
            else if (ext == "png")               png++
            else if (ext == "zip")               zip++
            else if (ext == "txt")               txt++
            else if (ext == "sh" || ext == "py") script++
            else                                 other++
        }
        END {
            total = json+html+png+zip+txt+script+other
            printf "{\"json\":%d,\"html\":%d,\"png\":%d,\"zip\":%d,\"txt\":%d,\"script\":%d,\"other\":%d,\"total\":%d}",
                json, html, png, zip, txt, script, other, total
        }
    ')

    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

    printf '{\n'
    printf '  "generated_at": "%s",\n' "$ts"
    printf '  "rundir": "%s",\n' "$root"
    printf '  "tree": "%s",\n' "$tree_str"
    printf '  "files": %s,\n' "$files_json"
    printf '  "counts": %s\n' "$counts_json"
    printf '}\n'
}
