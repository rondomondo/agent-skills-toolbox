#!/usr/bin/env bash
# Moves all untracked files/dirs out to a temp stash, leaving only git-tracked content.
# Run with 'restore' to bring them back.
#
# Usage:
#   ./scripts/git-stash-untracked.sh [stash]    -- move untracked out (default)
#   ./scripts/git-stash-untracked.sh restore    -- move them back
#   ./scripts/git-stash-untracked.sh list       -- show what is stashed

set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
STASH_DIR="${HOME}/.git-untracked-stash/$(basename "$REPO_ROOT")"
MANIFEST="${STASH_DIR}/.manifest"

cmd="${1:-stash}"

case "$cmd" in
stash)
    untracked="$(git -C "$REPO_ROOT" ls-files --others --exclude-standard)"
    if [[ -z "$untracked" ]]; then
        echo "Nothing untracked to stash." >&2
        exit 0
    fi

    mkdir -p "$STASH_DIR"
    : > "$MANIFEST"

    count=0
    while IFS= read -r path; do
        abs="$REPO_ROOT/$path"
        dest="$STASH_DIR/$path"
        mkdir -p "$(dirname "$dest")"
        mv "$abs" "$dest"
        echo "$path" >> "$MANIFEST"
        echo "stashed: $path"
        (( count++ )) || true
    done <<< "$untracked"

    echo ""
    echo "Stashed $count item(s) to $STASH_DIR"
    echo "Run '$(basename "$0") restore' to bring them back."
    ;;

restore)
    if [[ ! -f "$MANIFEST" ]]; then
        echo "No stash manifest found at $MANIFEST" >&2
        exit 1
    fi

    restored=0
    while IFS= read -r path; do
        src="$STASH_DIR/$path"
        dest="$REPO_ROOT/$path"
        if [[ -e "$src" || -d "$src" ]]; then
            mkdir -p "$(dirname "$dest")"
            mv "$src" "$dest"
            echo "restored: $path"
            (( restored++ )) || true
        else
            echo "missing (already restored?): $path" >&2
        fi
    done < "$MANIFEST"

    rm -f "$MANIFEST"
    echo ""
    echo "Restored $restored item(s)."
    ;;

list)
    if [[ ! -f "$MANIFEST" ]]; then
        echo "No stash found." >&2
        exit 0
    fi
    echo "Stashed items in $STASH_DIR:"
    cat "$MANIFEST"
    ;;

*)
    echo "Usage: $(basename "$0") [stash|restore|list]" >&2
    exit 1
    ;;
esac
