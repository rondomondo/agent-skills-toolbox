# sanitise-ascii

**Strip non-ASCII characters from text files -- replacing known offenders with ASCII equivalents
and flagging anything it cannot fix for manual review.**

Safe to run repeatedly, clean files are left untouched. Designed for Markdown, SKILL files,
and any plain text content that must survive automated pipelines, version control, or tooling
that expects pure ASCII.

> **Also available as an [Agent Skill](#claude-code-skill)** -- install it to sanitise files
> directly from Claude Code with no terminal required. Use the `/sanitise-ascii` slash command
> or just describe what you want and your AI Agent will handle it.

---

## Why this exists

Text files passed through automated pipelines, version control, or tools that expect plain ASCII
often contain Unicode characters that look fine on screen but cause silent failures:

- Smart quotes (U+2018/2019/201C/201D) break shell one-liners embedded in code blocks and config snippets.
- En/em dashes (U+2013/2014) confuse argument parsers when docs are piped into scripts.
- Non-breaking spaces (U+00A0) and zero-width characters (U+200B) produce invisible diffs that make
  code-review noise and can break grep patterns.
- BOMs and variation selectors (U+FEFF, U+FE0F) corrupt tooling that reads files byte-by-byte.
- Copy-paste from word processors, browsers, Notion, or Confluence is a major source -- these apps
  aggressively apply typographic substitutions.

---

## Quick Start

```bash
# Check a single file (default - no writes)
sanitise-ascii README.md

# Check all text files in the repo
sanitise-ascii --dir .

# Auto-fix in place
sanitise-ascii --fix --dir .

# Fix but allow emoji through
sanitise-ascii --fix --allow-emoji README.md
```

---

## Installation

### Install `sanitise-ascii` to `/usr/local/bin`

```bash
# 1. Clone the toolbox repo
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/sanitise-ascii

# 2. Install sanitise-ascii to /usr/local/bin
make install
```

This copies `sanitise-ascii.py` to `/usr/local/bin/sanitise-ascii.py` and creates an
extension-less symlink so the tool is callable as `sanitise-ascii` on PATH.

### Uninstall

```bash
make uninstall
```

---

## Usage

```
sanitise-ascii [files...]            Check specific files (default - no writes)
sanitise-ascii --check [files...]    Same as above, explicit
sanitise-ascii --fix [files...]      Auto-fix in place
sanitise-ascii --dir <path>          Check all common text files under a directory (recursive)
sanitise-ascii --fix --dir <path>    Fix all common text files under a directory (recursive)
sanitise-ascii --allow-emoji ...     Treat emoji as acceptable - skip them
sanitise-ascii --quiet ...           Suppress OK lines, show only FIX and WARN
```

`--check` and `--fix` are mutually exclusive. The default mode is `--check` (no writes).

### Environment variable

| Variable | Values | Effect |
|----------|--------|--------|
| `SANITISE_ACTION` | `check` (default) | Check only, no writes |
| `SANITISE_ACTION` | `fix` | Allow in-place fixes (equivalent to `--fix`) |

`--fix` and `--check` always override `SANITISE_ACTION`.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | All clean (or all auto-fixed successfully) |
| 1 | Unfixable non-ASCII characters remain (or any non-ASCII in check mode) |

### Output prefixes

| Prefix | Meaning |
|--------|---------|
| `OK` | File is clean, no changes needed |
| `FIX` | One or more characters were replaced |
| `WARN` | Character not in the fix map - requires manual review |
| `ERROR` | File is not valid UTF-8 and was skipped |

---

## Examples

```bash
# Check a single file (default - no writes)
sanitise-ascii README.md

# Check all text files in the repo
sanitise-ascii --dir .

# Explicit check (same as above)
sanitise-ascii --check --dir .

# Auto-fix all text files in the repo
sanitise-ascii --fix --dir .

# Fix specific files
sanitise-ascii --fix docs/notes.md CHANGELOG.md

# Use the environment variable to default to fix mode
SANITISE_ACTION=fix sanitise-ascii --dir .

# Allow emoji (do not flag them)
sanitise-ascii --allow-emoji --dir .

# Quiet mode - only show problems
sanitise-ascii --quiet --dir .
```

---

## What it fixes automatically

| Category | Characters replaced |
|----------|-------------------|
| Dashes | En dash, em dash, figure dash, non-breaking hyphen, horizontal bar |
| Quotes | Smart single/double quotes, low-9 quotes, prime/double-prime |
| Spaces | Non-breaking space, narrow no-break space, thin space, zero-width space (dropped), BOM (dropped) |
| Punctuation | Ellipsis, bullet, middle dot, triangular bullet |
| Arrows | Right/left/bidirectional arrows, double-right arrow |
| Math | Multiplication, division, not-equal, less/greater-or-equal, plus-minus, degree, minus sign |
| Typography | Registered, copyright, trademark symbols |
| Symbols | Variation selector-16 (dropped) |
| Box drawing | Box-drawing dash runs on comment lines (`#`) replaced with plain hyphens |

Characters not in the fix map are reported as `WARN` and left for manual review.

---

## File types scanned

When using `--dir`, the following file types are searched recursively:

`*.md`, `*.txt`, `*.rst`, `*.yaml`, `*.yml`, `*.json`, `*.jsonl`, `*.toml`, `*.sh`, `*.py`, `*akefile`

---

## Makefile targets

```bash
make check             # Check all text files in the repo (default - no writes)
make fix               # Auto-fix all text files in the repo
make usage             # Show sanitise-ascii --help output
make install           # Install sanitise-ascii to /usr/local/bin
make uninstall         # Remove sanitise-ascii from /usr/local/bin
make sync-skill        # Sync skill files to ~/Code/agent-skills-toolbox/skills/sanitise-ascii
```

---

## Claude Code skill

<details>
<summary>Install the <code>/sanitise-ascii</code> slash command for Claude Code</summary>

This repository ships a `/sanitise-ascii` slash command skill for [Claude Code](https://claude.ai/code)
that lets Claude check and fix your files -- no terminal required. Just describe what you want
and Claude will invoke the skill automatically.

### What it accepts

| Input | Example |
|---|---|
| Single file | `README.md` |
| Multiple files | `SKILL.md README.md CLAUDE.md` |
| Local directory | `.` -- checks every supported text file recursively |

### Invoking the skill

Use the slash command directly:

```
/sanitise-ascii README.md
/sanitise-ascii --fix --dir .
/sanitise-ascii --fix --allow-emoji SKILL.md
```

Or just describe what you want in natural language -- Claude will invoke the skill automatically:

> *"Check my SKILL.md for non-ASCII before I push"*
>
> *"Fix all the smart quotes and em dashes in the docs folder"*
>
> *"Sanitise everything before syncing to the agent harness"*

### Installing the skill

#### Option A -- sync locally via `make`

Copy the skill files into your agent skills directory so Claude Code picks them up automatically:

```bash
# from inside the sanitise directory
make sync-skill
```

This syncs `SKILL.md`, `sanitise-ascii.py`, and `README.md` to:

```
~/Code/agent-skills-toolbox/skills/sanitise-ascii/
```

Override the target directory with `SKILLS_DIR`:

```bash
make sync-skill SKILLS_DIR=/path/to/your/project/.claude/skills/sanitise-ascii
```

#### Option B -- copy manually

```bash
mkdir -p .claude/skills/sanitise-ascii
cp SKILL.md sanitise-ascii.py README.md .claude/skills/sanitise-ascii/
```

</details>

---

## Requirements

- Python 3.9+
- `make` (for Makefile targets)
