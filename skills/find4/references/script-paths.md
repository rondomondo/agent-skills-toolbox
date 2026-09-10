# Resolving skill, script paths and IS_SANDBOX check

Run this block at the start of every session, before calling any script.

```bash
if [ "${IS_SANDBOX:-no}" = "yes" ] || [ "${IS_SANDBOX:-no}" = "1" ] || [ "${IS_SANDBOX:-no}" = "true" ]; then
    SKILL_DIR="/mnt/skills/user/find4"
    mkdir -p /tmp/find4
    cp -r "$SKILL_DIR/scripts/." /tmp/find4/scripts/
    cp -r "$SKILL_DIR/references/." /tmp/find4/references
    chmod +x /tmp/find4/scripts/*.sh
    chmod +x /tmp/find4/scripts/*.py
    JQ_VERSION="1.7.1"
    YQ_VERSION="4.2.0"
    LINUX_PLATFORM="amd64"
    command -v jq >/dev/null 2>&1 || \
      { apt-get update -q 2>/dev/null && apt-get install -y -q jq 2>/dev/null; } || \
      { wget -q "https://github.com/jqlang/jq/releases/download/jq-${JQ_VERSION}/jq-linux-${LINUX_PLATFORM}" \
          -O /usr/local/bin/jq && chmod +x /usr/local/bin/jq; } || \
      { echo "ERROR: jq install failed via apt and wget" >&2; exit 1; }
    command -v yq >/dev/null 2>&1 || \
      { wget -q "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_${LINUX_PLATFORM}" \
          -O /usr/local/bin/yq && chmod +x /usr/local/bin/yq; } || \
      { echo "ERROR: yq install failed via wget" >&2; exit 1; }
    command -v uv >/dev/null 2>&1 || \
      { curl -LsSf https://astral.sh/uv/install.sh | sh; } || \
      { echo "ERROR: uv install failed" >&2; exit 1; }
    FIND4_SCRIPTS="/tmp/find4/scripts"
    FIND4_REFERENCES="/tmp/find4/references"
else
    SKILL_DIR=""
    for candidate in \
        "$HOME/.claude/skills/find4" \
        ".claude/skills/find4" \
        ".claude/plugins/marketplaces/*/skills/find4" \
        "skills/find4"; do
        if [ -d "$candidate/scripts" ]; then
            SKILL_DIR="$candidate"
            break
        fi
    done
    if [ -z "$SKILL_DIR" ]; then
        echo "ERROR: find4 skill not found in any expected location" >&2
        exit 1
    fi
    FIND4_SCRIPTS="$SKILL_DIR/scripts"
    FIND4_REFERENCES="$SKILL_DIR/references"
fi

echo "($(pwd)) SKILL_DIR is '$SKILL_DIR'"
```

After the block resolves `$SKILL_DIR`, capture the run directory and create output directories beneath it:

```bash
RUNDIR="$(pwd)"
mkdir -p "$RUNDIR/output" \
         "$RUNDIR/output/tmp" \
         "$RUNDIR/output/games" \
         "$RUNDIR/output/games/html" \
         "$RUNDIR/output/games/screenshots" \
         "$RUNDIR/output/library"
```

`$RUNDIR` is the directory from which the skill was invoked. All `output/` paths in SKILL.md are relative to `$RUNDIR`, not the skill installation directory. Script calls still use `$FIND4_SCRIPTS`, never hardcoded paths.

---

## ⚠️ CRITICAL — persisting these variables across tool calls

**Every `bash_tool` call is a brand-new shell process.** Nothing exported here —
`$SKILL_DIR`, `$FIND4_SCRIPTS`, `$FIND4_REFERENCES`, `$RUNDIR`, or even the current
working directory set by `cd` — survives into the next tool call. This is not
optional behaviour to guard against; it is guaranteed on every call.

**The shell is `/bin/sh` (`dash`), not `bash`.** `dash` has no `source` builtin —
only the POSIX `.` (dot) command works. Using `source` fails with
`sh: source: not found` (exit 127) and, because these blocks do not run under
`set -e`, the script keeps going with the target variable silently unset. A
downstream `[ -f "$FIND4_SCRIPTS/..." ]` check then silently evaluates against a
garbage path and reports false — this exact failure mode caused a real bug where
an existing `dingdong.enc` was reported as missing.

**The fix — write the resolved variables to a file, then reload with `.`:**

Immediately after resolving the block above, persist the variables:

```bash
cat > "$RUNDIR/.find4_env" <<EOF
export SKILL_DIR="$SKILL_DIR"
export FIND4_SCRIPTS="$FIND4_SCRIPTS"
export FIND4_REFERENCES="$FIND4_REFERENCES"
export RUNDIR="$RUNDIR"

# a recursive find 
rfind() {
    local term="${1:?Usage: rfind <term> [directory]}"
    local dir="${2:-.}"
    find "$dir" -follow -type f -name "*" -exec grep --color "$term" {} +
}

EOF
```

Then **every subsequent `bash_tool` call in every step (1 through 9) must begin**
with:

```bash
. "$RUNDIR_ABSOLUTE_PATH/.find4_env"   # use the literal absolute path, cwd is not persisted either
cd "$RUNDIR"
```

Since `$RUNDIR` itself isn't available until the file is sourced, the first line
must use the actual absolute path written out in full (e.g. `. "/home/claude/.find4_env"`),
not the variable.

Never use `source`. Never assume a `cd` or `export` from a previous call is still
in effect. If a step needs real bash features (`source`, `[[`, arrays — e.g. the
secrets heredoc in `secrets-loading.md`), wrap that specific block in
`bash << 'EOF' ... EOF`, exactly as `secrets-loading.md` already does — `.find4_env`
itself only needs POSIX `export` lines, so the portable `.` is sufficient for it.
