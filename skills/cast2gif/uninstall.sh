#!/bin/bash
# shellcheck disable=SC2016  # single quotes are deliberate: the echoed text is written into generated scripts verbatim
set -euo pipefail

BOLD='\033[1m'
CYAN='\033[0;36m'
RESET='\033[0m'

TOOL="cast2gif"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-ghcr.io}"
IMAGE_REPO="${IMAGE_REPO:-rondomondo/cast2gif}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE="${IMAGE_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}"

# Streaming uninstall: docker run ... uninstall | sh
# Emits a self-contained sh script that removes the wrapper from the host.
if [[ ! -t 1 ]]; then
    cat <<'HEADER'
#!/bin/sh
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

ok()   { printf "${GREEN}ok${RESET}    %s\n" "$1"; }
warn() { printf "${YELLOW}warn${RESET}  %s\n" "$1"; }
info() { printf "${CYAN}info${RESET}  %s\n" "$1"; }

try_remove_bin() {
    local name="$1"
    local removed=0
    local dir target
    for dir in /usr/local/bin "$HOME/.local/bin"; do
        target="$dir/$name"
        [ -f "$target" ] || [ -L "$target" ] || continue
        if rm -f "$target" 2>/dev/null; then
            ok "removed $target"
            removed=1
        elif sudo rm -f "$target" 2>/dev/null; then
            ok "removed $target (via sudo)"
            removed=1
        else
            warn "could not remove $target (permission denied)"
        fi
    done
    [ "$removed" -eq 0 ] && info "$name not found in /usr/local/bin or ~/.local/bin -- nothing to remove" || true
}

HEADER

    printf 'TOOL="%s"\n' "$TOOL"
    printf 'printf "\\n${BOLD}Uninstalling %%s...${RESET}\\n" "$TOOL"\n'
    echo 'try_remove_bin "$TOOL"'
    echo
    cat <<'FOOTER'
printf '\n%bDone.%b\n\n' "$BOLD" "$RESET"
FOOTER

    exit 0
fi

# Interactive: print usage instructions
printf "\n"
printf "${BOLD}${CYAN}Uninstall %s${RESET}\n" "$TOOL"
printf "\n"
printf "Run the following to remove %s from this host:\n" "$TOOL"
printf "\n"
printf "  ${BOLD}docker run --rm %s uninstall | sh${RESET}\n" "$IMAGE"
printf "\n"
printf "This removes ${BOLD}%s${RESET} from /usr/local/bin or ~/.local/bin\n" "$TOOL"
printf "\n"
