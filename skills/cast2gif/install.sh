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

TOOL_SRC="/usr/local/bin/${TOOL}"

examples() {
    printf "\n"
    printf "${BOLD}${CYAN}Install %s${RESET}\n" "$TOOL"
    printf "\n"
    printf "Run the following to install %s on this host:\n" "$TOOL"
    printf "\n"
    printf "  ${BOLD}docker run --rm %s install | sh${RESET}\n" "$IMAGE"
    printf "\n"
    printf "This installs:\n"
    printf "  ${BOLD}%s${RESET} -> /usr/local/bin/%s (or ~/.local/bin/%s)\n" "$TOOL" "$TOOL" "$TOOL"
    printf "\n"
    printf "To remove it again:\n"
    printf "\n"
    printf "  ${BOLD}docker run --rm %s uninstall | sh${RESET}\n" "$IMAGE"
    printf "\n"
    printf "Pass DEBUG=1 to trace the docker command: ${BOLD}DEBUG=1 %s ...${RESET}\n" "$TOOL"
    printf "\n"
}

# Streaming install: docker run ... install | sh
# Emits a self-contained sh script that installs the wrapper on the host.
if [[ ! -t 1 ]]; then
    [ -f "$TOOL_SRC" ] || { printf "install.sh: missing asset: %s\n" "$TOOL_SRC" >&2; exit 1; }

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

add_to_path_if_needed() {
    local dir="$1"
    local rcfile

    case ":$PATH:" in
        *":$dir:"*) return 0 ;;
    esac

    case "${SHELL##*/}" in
        zsh)  rcfile="$HOME/.zshrc" ;;
        bash) rcfile="$HOME/.bashrc" ;;
        fish) rcfile="$HOME/.config/fish/config.fish" ;;
        *)    rcfile="" ;;
    esac

    if [ -n "$rcfile" ]; then
        if ! grep -qF "$dir" "$rcfile" 2>/dev/null; then
            mkdir -p "$(dirname "$rcfile")"
            case "$rcfile" in
                */config.fish) printf '\nfish_add_path "%s"\n' "$dir" >> "$rcfile" ;;
                *)             printf '\nexport PATH="%s:$PATH"\n' "$dir" >> "$rcfile" ;;
            esac
            ok "added $dir to PATH in $rcfile"
            warn "restart your shell or run: source $rcfile"
        else
            info "$dir already referenced in $rcfile -- skipping"
        fi
    else
        warn "$dir is not on PATH -- add: export PATH=\"$dir:\$PATH\""
    fi
}

# Prefer /usr/local/bin (direct, then sudo), fall back to ~/.local/bin.
try_install() {
    USE_SUDO=0

    if install -m 755 /dev/null /usr/local/bin/.install_probe 2>/dev/null; then
        rm -f /usr/local/bin/.install_probe
        bin_dir=/usr/local/bin
    elif sudo install -m 755 /dev/null /usr/local/bin/.install_probe 2>/dev/null; then
        sudo rm -f /usr/local/bin/.install_probe
        bin_dir=/usr/local/bin
        USE_SUDO=1
    else
        bin_dir="$HOME/.local/bin"
        mkdir -p "$bin_dir"
        add_to_path_if_needed "$bin_dir"
    fi

    if [ "$USE_SUDO" = "1" ]; then
        sudo install -m 755 "$tmp_asset" "$bin_dir/$TOOL"
    else
        install -m 755 "$tmp_asset" "$bin_dir/$TOOL"
    fi
    ok "$bin_dir/$TOOL"
}

HEADER

    printf 'TOOL="%s"\n' "$TOOL"
    printf 'IMAGE="%s"\n' "$IMAGE"
    echo 'tmp_asset=$(mktemp)'
    echo 'trap '"'"'rm -f "$tmp_asset"'"'"' EXIT'
    printf '\nprintf "\\n${BOLD}Installing %%s...${RESET}\\n" "$TOOL"\n'
    echo "cat > \"\$tmp_asset\" << 'TOOL_ASSET_EOF'"
    cat "$TOOL_SRC"
    echo "TOOL_ASSET_EOF"
    echo "try_install"
    echo
    cat <<'FOOTER'
command -v docker >/dev/null 2>&1 || warn "docker was not found on PATH -- $TOOL needs it at run time"

printf '\n%bDone.%b\n\n' "$BOLD" "$RESET"
printf 'Installed %b%s%b -> %s/%s\n' "$BOLD" "$TOOL" "$RESET" "$bin_dir" "$TOOL"
printf 'Run %b%s --help%b to get started.\n' "$CYAN" "$TOOL" "$RESET"
printf 'Pass DEBUG=1 to trace the docker command: DEBUG=1 %s ...\n\n' "$TOOL"
printf 'To remove it: docker run --rm %s uninstall | sh\n\n' "$IMAGE"
FOOTER

    exit 0
fi

# Interactive: print usage instructions
examples
