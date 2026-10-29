#!/usr/bin/env bash
#
# check-image-versions.sh - verify that every docker tool bakes its image version into the files it ships.
#
# For each tool directory (default: every directory holding a Dockerfile and a VERSION file) it checks:
#   1. VERSION is a plain X.Y.Z.
#   2. The tool Makefile sets VERSION_ARG and includes ../docker.mk, which passes --build-arg $(VERSION_ARG)=$(VERSION) at
#      least twice (build and push), and the Dockerfile declares ARG <ARG>.
#   3. Every file the Dockerfile COPYs into the image that names the tool's own image has the reference pinned at build
#      time by a sed in the Dockerfile that uses <ARG>. Two reference shapes are recognised:
#        - ghcr.io/<repo>:latest   (sed must rewrite <repo>:latest)
#        - IMAGE_TAG:-latest       (sed must rewrite IMAGE_TAG:-latest)
#        - DEFAULT_IMAGE_TAG=latest (sed must rewrite it)
#   4. Every baking sed that uses <ARG> still matches something in a shipped file, so a renamed variable cannot silently
#      turn the pin into a no-op.
#   5. No shipped file names ghcr.io/<repo> on a docker or assignment line without any tag, which no sed can fix.
#   6. Across the whole repo (docs, examples, tests included), no line that runs or assigns a ghcr.io/rondomondo image
#      leaves the tag off. A bare reference silently means :latest.
#
# Static only: it does not build anything or contact a registry.

set -euo pipefail

prog="$(basename "$0")"
root="$(cd "$(dirname "$0")/.." && pwd)"
errors=0

usage() {
  cat <<EOF
Usage: $prog [-h] [TOOL_DIR ...]

Check that image versions are baked into every shipped file that references the tool's own image.
With no arguments, checks every top-level directory that has both a Dockerfile and a VERSION file.
Exits 0 when all tools pass and 1 when any check fails.
EOF
}

fail() {
  printf '  FAIL  %s: %s\n' "$tool" "$1" >&2
  errors=$((errors + 1))
}

# Dockerfile with backslash continuations joined onto one line each
joined_dockerfile() {
  awk '{ if (sub(/\\$/, "")) { buf = buf $0 " " } else { print buf $0; buf = "" } }' "$1"
}

# Files (relative to the tool dir) that the Dockerfile COPYs from the build context
shipped_files() {
  local dir="$1" line tok src
  local -a toks
  joined_dockerfile "$dir/Dockerfile" | grep -E '^[[:space:]]*COPY[[:space:]]' | while IFS= read -r line; do
    case "$line" in *--from*) continue ;; esac
    read -r -a toks <<<"$line"
    local -a srcs=()
    for tok in "${toks[@]:1}"; do
      case "$tok" in --*) ;; *) srcs+=("$tok") ;; esac
    done
    local last=$((${#srcs[@]} - 1))
    for ((i = 0; i < last; i++)); do
      src="${srcs[$i]}"
      # shellcheck disable=SC2231  # glob expansion of COPY sources is intended
      for match in "$dir"/$src; do
        [ -e "$match" ] || continue
        if [ -d "$match" ]; then
          find "$match" -type f
        else
          printf '%s\n' "$match"
        fi
      done
    done
  done | sort -u
}

# Search patterns of every sed in the Dockerfile that uses the build arg, one per line
bake_patterns() {
  joined_dockerfile "$1" | grep -F 'sed ' | grep -E "\\\$\{?$2\}?" | awk '{
    s = $0
    while (match(s, /"s[|\/]/)) {
      d = substr(s, RSTART + 2, 1)
      s = substr(s, RSTART + 3)
      n = index(s, d)
      print substr(s, 1, n - 1)
      s = substr(s, n + 1)
    }
  }'
}

# True when some sed line in the Dockerfile rewrites the pattern in the named file using the build arg
baked() {
  local dockerfile="$1" pattern="$2" file="$3" arg="$4"
  joined_dockerfile "$dockerfile" | grep -F 'sed ' | grep -F -- "$pattern" \
    | grep -E "(^|[ /])$(basename "$file")([ ;\\\\]|\$)" | grep -qE "\\\$\{?$arg\}?"
}

check_tool() {
  local tool="$1" dir="$root/$1" version repo arg builds file rel pattern
  local -a shipped=()
  [ -f "$dir/Dockerfile" ] && [ -f "$dir/VERSION" ] && [ -f "$dir/Makefile" ] || {
    fail "needs Dockerfile, VERSION and Makefile"
    return
  }

  version="$(tr -d '[:space:]' <"$dir/VERSION")"
  printf '%s' "$version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$' || fail "VERSION '$version' is not X.Y.Z"

  repo="$(sed -n 's/^IMAGE_REPO[[:space:]]*:=[[:space:]]*//p' "$dir/Makefile" | tr -d '[:space:]')"
  [ -n "$repo" ] || { fail "no IMAGE_REPO in Makefile"; return; }

  arg="$(sed -n 's/^VERSION_ARG[[:space:]]*:=[[:space:]]*//p' "$dir/Makefile" | tr -d '[:space:]')"
  [ -n "$arg" ] || { fail "Makefile sets no VERSION_ARG"; return; }
  grep -qE '^include[[:space:]]+\.\./docker\.mk' "$dir/Makefile" || fail "Makefile does not include ../docker.mk"
  # shellcheck disable=SC2016  # the make variable references are literal text to match
  builds="$(grep -cF -- '--build-arg $(VERSION_ARG)=$(VERSION)' "$root/docker.mk" || true)"
  [ "$builds" -ge 2 ] || fail "docker.mk passes --build-arg \$(VERSION_ARG) in $builds place(s); expected build and push"
  grep -qE "^ARG $arg\$" "$dir/Dockerfile" || fail "Dockerfile has no 'ARG $arg'"

  while IFS= read -r file; do
    rel="${file#"$root"/}"
    grep -Iq . "$file" 2>/dev/null || continue

    if grep -qF -- "$repo:latest" "$file" && ! baked "$dir/Dockerfile" "$repo:latest" "$file" "$arg"; then
      fail "$rel references $repo:latest but the Dockerfile has no sed using \$$arg to pin it"
    fi
    if grep -qF -- 'IMAGE_TAG:-latest' "$file" && ! baked "$dir/Dockerfile" 'IMAGE_TAG:-latest' "$file" "$arg"; then
      fail "$rel defaults IMAGE_TAG to latest but the Dockerfile has no sed using \$$arg to pin it"
    fi
    if grep -qF -- 'DEFAULT_IMAGE_TAG=latest' "$file" && ! baked "$dir/Dockerfile" 'DEFAULT_IMAGE_TAG=latest' "$file" "$arg"; then
      fail "$rel defaults DEFAULT_IMAGE_TAG to latest but the Dockerfile has no sed using \$$arg to pin it"
    fi
    if grep -nE "ghcr\\.io/$repo([^:[:alnum:]_.-]|\$)" "$file" | grep -E 'docker |=' >/dev/null; then
      fail "$rel names ghcr.io/$repo with no tag on a docker or assignment line; write :latest so it can be pinned"
    fi
    shipped+=("$file")
  done < <(shipped_files "$dir")

  while IFS= read -r pattern; do
    [ -n "$pattern" ] || continue
    grep -qF -- "$pattern" "${shipped[@]}" 2>/dev/null || fail "Dockerfile seds '$pattern' but no shipped file contains it"
  done < <(bake_patterns "$dir/Dockerfile" "$arg")
}

# Fail on any docker or assignment line that names a ghcr.io/rondomondo image without a tag
check_bare_refs() {
  local f hits
  command -v git >/dev/null 2>&1 && git -C "$root" rev-parse --git-dir >/dev/null 2>&1 || return 0
  while IFS= read -r f; do
    [ "$f" = "scripts/$prog" ] && continue
    grep -Iq . "$root/$f" 2>/dev/null || continue
    # URLs are links, not pulls
    hits="$(sed -E 's#https?://ghcr\.io/[^[:space:])"]*##g' "$root/$f" \
      | grep -nE 'ghcr\.io/rondomondo/[a-z0-9-]+($|[^a-z0-9:_.-])' | grep -E 'docker (run|pull)|=|image:' || true)"
    [ -z "$hits" ] || {
      tool="(repo)"
      while IFS= read -r line; do fail "$f:${line%%:*} names a ghcr.io/rondomondo image with no tag; write :latest or a version"; done <<<"$hits"
    }
  done < <({ git -C "$root" ls-files; git -C "$root" ls-files -o --exclude-standard; } | sort -u)
}

main() {
  local -a tools=()
  local tool before
  case "${1:-}" in -h | --help) usage; exit 0 ;; esac

  if [ "$#" -gt 0 ]; then
    tools=("$@")
  else
    for d in "$root"/*/; do
      [ -f "$d/Dockerfile" ] && [ -f "$d/VERSION" ] && tools+=("$(basename "$d")")
    done
  fi
  [ "${#tools[@]}" -gt 0 ] || { printf '%s: no docker tools found\n' "$prog" >&2; exit 1; }

  for tool in "${tools[@]}"; do
    tool="$(basename "$tool")"
    before=$errors
    check_tool "$tool"
    if [ "$errors" -eq "$before" ]; then
      printf '  ok    %s %s\n' "$tool" "$(tr -d '[:space:]' <"$root/$tool/VERSION")"
    fi
  done

  before=$errors
  check_bare_refs
  if [ "$errors" -eq "$before" ]; then
    printf '  ok    no untagged ghcr.io/rondomondo image references\n'
  fi

  if [ "$errors" -gt 0 ]; then
    printf '%s: %d problem(s) found\n' "$prog" "$errors" >&2
    exit 1
  fi
}

main "$@"
