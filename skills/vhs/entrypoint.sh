#!/bin/bash
set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Set DEBUG=true/1 to enable verbose logging of invocation args via the log() helper.
USE_LOGGING="${DEBUG:-false}"
case "${USE_LOGGING}" in
  true|1)  USE_LOGGING=true  ;;
  false|0) USE_LOGGING=false ;;
  *) printf "ERROR: DEBUG must be true/false/1/0, got '%s'\n" "${USE_LOGGING}" >&2; exit 1 ;;
esac
SCRIPT_NAME=$(basename "$0")

ok() { ${USE_LOGGING} && printf '%b[%s:%s]%b %b%s%b\n' "$BOLD" "$SCRIPT_NAME" "$HOSTNAME" "$RESET" "$GREEN" "$*" "$RESET" >&2; return 0; }
warn() { ${USE_LOGGING} && printf '%b[%s:%s]%b %b%s%b\n' "$BOLD" "$SCRIPT_NAME" "$HOSTNAME" "$RESET" "$YELLOW" "$*" "$RESET" >&2; return 0; }
fail() { ${USE_LOGGING} && printf '%b[%s:%s]%b %b%s%b\n' "$BOLD" "$SCRIPT_NAME" "$HOSTNAME" "$RESET" "$RED" "$*" "$RESET" >&2; return 0; }
log()  { ${USE_LOGGING} && printf '%b[%s:%s]%b %b%s%b\n' "$BOLD" "$SCRIPT_NAME" "$HOSTNAME" "$RESET" "$CYAN" "$*" "$RESET" >&2; return 0; }

log "invoked with args '$*'"

docker_sock="${DOCKER_SOCK:-}"
# DOCKER_SOCK may be unset (plain docker run) or a host path that does not exist in here (older vhs-rec); the
# socket is always mounted at /var/run/docker.sock inside the container.
if [ ! -S "$docker_sock" ]; then
  docker_sock=/var/run/docker.sock
fi

log "invoked with args '$*'" 

check_docker_sock() {
  local DOCKER_SOCK="${1:-/var/run/docker.sock}"
  test -S "$DOCKER_SOCK" && ok "$DOCKER_SOCK exists and is a socket" || { warn "$DOCKER_SOCK is missing or not a socket"; return 1; }
}

if check_docker_sock "$docker_sock"; then
    sudo chgrp vhs "$docker_sock"
    ok "ran chgrp vhs $docker_sock"
fi

if [ -n "${HOST_PWD:-}" ]; then
    cd "$HOST_PWD"
    [ "$HOST_PWD" = "$(pwd)" ] && ok "successfully changed directory to $HOST_PWD" || { fail "failed to change dir to $HOST_PWD"; exit 1; }
fi

if [ $# -gt 0 ] && [ "$1" = "install" ]; then
    log "install was requested with args: '$@'" 
    shift
    exec /install.sh "$@"
fi

if [ $# -gt 0 ] && [ "$1" = "uninstall" ]; then
    log "uninstall was requested with args: '$*'"
    shift
    exec /uninstall.sh "$@"
fi

if [ $# -gt 0 ] && { [ "$1" = "vhs" ] || [ "$1" = "$(command -v vhs)" ]; }; then
    shift
fi

if [ -n "${USE_SHELL:-}" ]; then
    log "USE_SHELL was set so dropping into shell: $USE_SHELL" 
    exec "$(command -v "$USE_SHELL")"
else
    log "calling $(command -v vhs) with args: '$@'" 
    exec "$(command -v vhs)" "$@"
fi

fail "$0 we should never get here" ; return 1;
