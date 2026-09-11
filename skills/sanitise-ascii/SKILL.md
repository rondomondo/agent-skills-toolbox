---
name: sanitise-ascii
description: >
    Sanitise non-ASCII characters from Markdown and SKILL files before they might be added to
    Agents, Harnesses, GitHub etc. General sharing. Use this skill whenever the user wants to
    check or clean .md files for non-ASCII, typographic, or mojibake characters. Trigger on
    "sanitise", "sanitize", "ascii clean", "check for non-ascii", "clean before push",
    "strip unicode", or any request to prepare skill/markdown files for Remote Agent use,
    GitHub or other sharing. Also trigger proactively at the end of any workflow that produces
    or edits .md files if the user has asked for ASCII-clean output.
---

# sanitise-ascii

Strips non-ASCII characters from text files, replacing known offenders with ASCII equivalents
and flagging anything it cannot fix for manual review.

---

## When to use this skill

Run `sanitise-ascii` before any of the following:

- Pushing `.md`, `.txt`, `SKILL.md`, or `CLAUDE.md` files to GitHub
- Syncing skills to an agent harness or Remote Agent
- Sharing docs that will pass through automated pipelines or tools that expect plain ASCII

Common problem sources: copy-paste from Notion, Confluence, Google Docs, or browsers that
apply typographic substitutions (smart quotes, em dashes, non-breaking spaces).

---

## Quickstart

```bash
# Check a single file (default - no writes)
sanitise-ascii README.md

# Check all text files in the current directory
sanitise-ascii --dir .

# Auto-fix in place
sanitise-ascii --fix --dir .

# Fix but allow emoji through
sanitise-ascii --fix --allow-emoji README.md

# Quiet mode - only show problems
sanitise-ascii --quiet --dir .
```

---

## Step 0 - Resolve environment and install tool

```bash
if [ "${IS_SANDBOX:-no}" = "yes" ] || [ "${IS_SANDBOX:-no}" = "1" ] || [ "${IS_SANDBOX:-no}" = "true" ]; then
    SKILL_DIR="/mnt/skills/user/sanitise-ascii"
    command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
    cp "$SKILL_DIR/sanitise-ascii.py" /usr/local/bin/sanitise-ascii.py
    chmod +x /usr/local/bin/sanitise-ascii.py
    ln -sf /usr/local/bin/sanitise-ascii.py /usr/local/bin/sanitise-ascii
else
    command -v sanitise-ascii >/dev/null 2>&1 || {
        echo "ERROR: sanitise-ascii not installed. Run: cd ~/Code/toolbox/sanitise-ascii && make install" >&2
        exit 1
    }
fi
```

## Step 1 - Check for the tool

```bash
which sanitise-ascii
```

If missing locally, install it:

```bash
cd ~/Code/toolbox/sanitise-ascii && make install
```

---

## Step 2 - Identify files to check

For a single file the user named, use that path directly.

For a directory (or when the user says "all files", "the repo", "before pushing"):

```bash
sanitise-ascii --check --dir <path>
```

Default target when no path is specified: `.` (current working directory).

---

## Step 3 - Check, report, and decide

Run in `--check` mode first (no writes). Read the output:

| Prefix  | Meaning                                          |
|---------|--------------------------------------------------|
| `OK`    | File is clean                                    |
| `FIX`   | Character can be auto-replaced                   |
| `WARN`  | Character not in fix map - needs manual review   |
| `ERROR` | File is not valid UTF-8 - skipped                |

Exit code `0` means all clean. Exit code `1` means non-ASCII remains.

If only `FIX` lines (no `WARN`): safe to auto-fix. Proceed to Step 4.

If `WARN` lines appear: show the user the flagged characters and ask whether to fix what can
be fixed and leave the WARNs, or review manually first.

---

## Step 4 - Fix

```bash
sanitise-ascii --fix --dir <path>
```

Or for specific files:

```bash
sanitise-ascii --fix file1.md file2.md
```

Re-run `--check` after fixing to confirm exit code `0`.

---

## What is fixed automatically

| Category    | Characters replaced                                              |
|-------------|------------------------------------------------------------------|
| Dashes      | En dash, em dash, figure dash, non-breaking hyphen, horizontal bar |
| Quotes      | Smart single/double quotes, low-9 quotes, prime/double-prime    |
| Spaces      | Non-breaking space, narrow no-break space, thin space, zero-width space (dropped), BOM (dropped) |
| Punctuation | Ellipsis, bullet, middle dot, triangular bullet                  |
| Arrows      | Right/left/bidirectional arrows, double-right arrow              |
| Math        | Multiplication, division, not-equal, less/greater-or-equal, plus-minus, degree, minus sign |
| Typography  | Registered, copyright, trademark symbols                         |
| Box drawing | Box-drawing dash runs on `#` comment lines replaced with hyphens |

Characters not in the fix map are reported as `WARN` and left for manual review.

---

## File types scanned (when using --dir)

`*.md`, `*.txt`, `*.rst`, `*.yaml`, `*.yml`, `*.json`, `*.jsonl`, `*.toml`, `*.sh`, `*.py`, `*akefile`

---

## Environment variable

`SANITISE_ACTION=fix` sets fix mode without passing `--fix` on every call. `--fix` and
`--check` flags always override this variable.

---

## Exit codes

| Code | Meaning                                                      |
|------|--------------------------------------------------------------|
| 0    | All clean (or all auto-fixed successfully)                   |
| 1    | Unfixable non-ASCII remains, or any non-ASCII in check mode  |
