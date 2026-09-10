#!/usr/bin/env bash
# bootstrap_node_backend.sh
#
# Sets up the qr-cli Node backend in sandboxed/airgapped environments where
# Docker is unavailable and the default `python3 -m qr_cli --install` fails
# because node-gyp tries to download Node.js headers from nodejs.org (blocked).
#
# This script is IDEMPOTENT -- safe to re-run after upgrades or reinstalls.
# It is invoked automatically by qr-skill.sh when the Node backend is needed
# and the canvas binary is missing or broken.
#
# What it does:
#   1. Installs qr-cli + colourmapper-dev from PyPI
#   2. Installs apt system libs required to compile canvas natively
#      (libcairo2-dev, libpango1.0-dev, librsvg2-dev, libjpeg-dev, libgif-dev)
#   3. Compiles canvas using system Node headers (npm_config_nodedir=/usr)
#      -- avoids the nodejs.org header download entirely
#   4. Installs jsdom (required for qr-code-styling DOM rendering in Node)
#   5. Drops the patched index.js into the qr_cli node directory, which:
#      a) subclasses JSDOM to strip { resources:"usable" } (prevents network hangs)
#      b) guards stdin reads so the process doesn't block when stdout is captured
#
# Background / why each step is needed:
#   - canvas is a native addon; node-gyp needs Node C++ headers to compile it.
#     The default path fetches them from nodejs.org -- blocked in most sandboxes.
#     But Ubuntu ships them in /usr/include/node/ via the nodejs package.
#     Setting npm_config_nodedir=/usr points node-gyp there instead.
#   - librsvg2-dev is needed so canvas can load SVG data URIs. Without it,
#     qr-code-styling's internal SVG→canvas pipeline fails silently.
#   - qr-code-styling is a browser library that calls new jsdom({ resources:"usable" })
#     which opens external resource fetches. In a sandbox those fetches hang
#     forever. Subclassing JSDOM to strip that option fixes it.
#   - When python3 -m qr_cli captures Node's stdout via subprocess, stdin is
#     not a TTY. The original index.js did fs.readFileSync("/dev/stdin") which
#     blocks waiting for input that never arrives. The guard checks for --data
#     or --json flags before attempting the stdin read.
#
# Requirements:
#   - Ubuntu/Debian (uses apt-get)
#   - python3 + pip
#   - node + npm (system-installed)
#   - sudo or root (for apt-get; skip apt steps if already installed)

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log()  { echo "[qr-bootstrap] $*" >&2; }
ok()   { echo "[qr-bootstrap] ✓ $*" >&2; }
fail() { echo "[qr-bootstrap] ✗ $*" >&2; exit 1; }

# -- 1. Python packages --------------------------------------------------------

log "Installing qr-cli and colourmapper-dev from PyPI..."
pip install --quiet --break-system-packages qr-cli colourmapper-dev 2>/dev/null \
  || pip install --quiet qr-cli colourmapper-dev 2>/dev/null \
  || fail "pip install failed. Ensure pip is available."
ok "PyPI packages installed"

# Locate the qr_cli node directory
QR_NODE_DIR=$(python3 -c "
import importlib.util, os
spec = importlib.util.find_spec('qr_cli')
print(os.path.join(os.path.dirname(spec.origin), 'node'))
" 2>/dev/null) || fail "Could not locate qr_cli package. Is it installed?"

log "qr_cli node dir: $QR_NODE_DIR"

# -- 2. System libraries (canvas native deps) ----------------------------------

REQUIRED_PKGS=(
    libcairo2-dev      # Cairo 2D graphics -- core canvas dep
    libpango1.0-dev    # Pango text rendering (pangocairo)
    librsvg2-dev       # SVG support -- needed for qr-code-styling SVG→canvas pipeline
    libjpeg-dev        # JPEG encoding
    libgif-dev         # GIF support
    libpng-dev         # PNG support (usually present but ensure it)
)

MISSING_PKGS=()
for pkg in "${REQUIRED_PKGS[@]}"; do
    dpkg -l "$pkg" &>/dev/null || MISSING_PKGS+=("$pkg")
done

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    log "Installing missing system packages: ${MISSING_PKGS[*]}"
    if command -v sudo &>/dev/null; then
        sudo apt-get install -y -qq "${MISSING_PKGS[@]}" \
            || fail "apt-get install failed. Try: sudo apt-get install ${MISSING_PKGS[*]}"
    else
        apt-get install -y -qq "${MISSING_PKGS[@]}" \
            || fail "apt-get install failed (no sudo). Try running as root."
    fi
    ok "System packages installed"
else
    ok "All system packages already present"
fi

# -- 3. Verify Node headers are available -------------------------------------

NODE_HEADERS="/usr/include/node/node_api.h"
if [[ ! -f "$NODE_HEADERS" ]]; then
    log "Node headers not found at /usr/include/node/. Trying nodejs-dev..."
    if command -v sudo &>/dev/null; then
        sudo apt-get install -y -qq nodejs-dev 2>/dev/null || true
    else
        apt-get install -y -qq nodejs-dev 2>/dev/null || true
    fi
    [[ -f "$NODE_HEADERS" ]] || fail "Node headers missing at /usr/include/node/. Install nodejs-dev."
fi
ok "Node headers found at /usr/include/node/"

# -- 4. Compile canvas using system headers ------------------------------------

CANVAS_NODE="$QR_NODE_DIR/node_modules/canvas/build/Release/canvas.node"

needs_recompile() {
    # Recompile if binary missing OR librsvg not linked (SVG support absent)
    [[ ! -f "$CANVAS_NODE" ]] && return 0
    ldd "$CANVAS_NODE" 2>/dev/null | grep -q "librsvg" || return 0
    return 1
}

if needs_recompile; then
    log "Compiling canvas with system Node headers (npm_config_nodedir=/usr)..."
    log "This takes ~25 seconds..."
    (
        cd "$QR_NODE_DIR"
        # Use npm rebuild to recompile in-place against system headers.
        # `npm install canvas` may use a cached binary without librsvg;
        # `npm rebuild` forces recompilation from source.
        npm_config_nodedir=/usr npm rebuild canvas 2>&1 \
            | grep -v "^npm warn" | tail -5 || true
    )
    # Verify
    if needs_recompile; then
        fail "canvas compile failed. Check apt deps and try again."
    fi
    ok "canvas compiled with SVG support (librsvg linked)"
else
    ok "canvas already compiled with SVG support"
fi

# -- 5. Install jsdom ----------------------------------------------------------

JSDOM_PKG="$QR_NODE_DIR/node_modules/jsdom/package.json"
if [[ ! -f "$JSDOM_PKG" ]]; then
    log "Installing jsdom..."
    (cd "$QR_NODE_DIR" && npm_config_nodedir=/usr npm install jsdom --save 2>&1 | tail -3)
    ok "jsdom installed"
else
    ok "jsdom already installed"
fi

# -- 6. Drop in patched index.js -----------------------------------------------

PATCHED_INDEX="$SCRIPT_DIR/index.js"
TARGET_INDEX="$QR_NODE_DIR/index.js"

if [[ ! -f "$PATCHED_INDEX" ]]; then
    fail "Patched index.js not found at $PATCHED_INDEX. Skill installation may be incomplete."
fi

# Check if current index.js already has our patches by looking for the sentinel comment
if grep -q "SANDBOX PATCHES" "$TARGET_INDEX" 2>/dev/null; then
    ok "index.js already patched (sentinel found)"
else
    log "Applying patched index.js..."
    cp "$PATCHED_INDEX" "$TARGET_INDEX"
    ok "index.js patched (JSDOM subclass + stdin guard applied)"
fi

# -- 7. Smoke test -------------------------------------------------------------

log "Running smoke test..."
RESULT=$(cd "$QR_NODE_DIR" && \
    timeout 15 node index.js --data="https://example.com" --format=png 2>/dev/null) \
    || fail "Smoke test failed. Run manually: cd $QR_NODE_DIR && node index.js --data=https://example.com"

SUCCESS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success'))" 2>/dev/null) || true
if [[ "$SUCCESS" != "True" ]]; then
    fail "Smoke test returned success=false. Result: $RESULT"
fi

ok "Smoke test passed"
echo ""
echo "[qr-bootstrap] Node backend is ready. QR codes will use: python3 -m qr_cli --backend=node" >&2
