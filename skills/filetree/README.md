# filetree

**Generate ASCII file trees from a directory -- suitable for READMEs, documentation, and communicating project structure.**

[filetree.sh](filetree.sh) is a pure-bash script that walks a directory recursively with `find`
and renders a unicode (or ASCII) tree. No dependencies beyond bash and standard POSIX tools.

> **Also available as an [Agent Skill](#claude-code-skill)** -- install it to generate file trees directly from Claude Code with no terminal required. Use the `/filetree` slash command or just describe what you want and your AI Agent will handle it.

---

## Try it now

This tool is a single bash script (no Docker image), so it installs from a clone:

```bash
# 1. Clone the toolbox repo
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/filetree

# 2. Install filetree to /usr/local/bin
make install
```

This copies `filetree.sh` to `/usr/local/bin` (else `sudo`, else `~/.local/bin`) and creates an
extension-less symlink so the tool is callable as `filetree` on PATH.

> To uninstall: `make uninstall` (from `toolbox/filetree/`)

Then:

```bash
# Tree of the current directory
filetree .

# Tree of a specific directory
filetree src/

# ASCII-safe output (no unicode box-drawing)
filetree --style ascii .

# Exclude extra directories
filetree --exclude-dirs dist:build src/
```

---

## Usage

```
filetree [OPTIONS] [DIR]

  DIR defaults to "." if not provided.
  Walks DIR recursively with find and renders an ASCII tree.

Options:
  -s, --style STYLE          Tree style: unicode (default), ascii, compact
  -e, --exclude-dirs DIRS    Colon-separated extra dirs to exclude
  -h, --help                 Show this help
```

### Tree styles

| Style | Description | Example branch |
|---|---|---|
| `unicode` (default) | Box-drawing characters | `├──` / `└──` |
| `ascii` | Portable ASCII only | `+--` / `` `-- `` |
| `compact` | Minimal indentation | `  ` |

### Default excluded directories

`.git`, `.venv`, `venv`, `node_modules`, `__pycache__`, `.DS_Store`, `dist`,
`.idea`, `.mypy_cache`, `.pytest_cache`, `.tox`

Excludes match by name at any depth, so `--exclude-dirs build` also hides `src/build/`. Files with a matching
name are hidden too.

---

## Examples

```bash
# Tree of the current directory
filetree .

# Tree of a specific path
filetree ~/Code/myproject/

# ASCII style (no unicode box-drawing)
filetree --style ascii .

# Exclude additional directories
filetree --exclude-dirs dist:build:coverage src/

# Compact style
filetree --style compact .
```

### Sample output

```
.
├── Makefile
├── README.md
├── SKILL.md
└── filetree.sh
```

---

## How it works

| File | Role |
|---|---|
| `filetree.sh` | Main script. Parses options, uses `find` to walk the directory, and renders the tree using `awk` for portable two-pass processing. |
| `Makefile` | Developer workflow: install/uninstall the script. |

### What the script does on each invocation

1. Parses options (`--style`, `--exclude-dirs`, `--help`).
2. Validates the target directory exists.
3. Builds a `find` prune expression from default + extra excludes.
4. Collects all matching paths sorted alphabetically.
5. Converts slash-delimited paths to indented depth form.
6. Passes indented lines through an `awk` renderer that produces the correct tree connectors.

---

## Makefile targets

```
make help         Show all targets
make install      Install filetree to /usr/local/bin (else ~/.local/bin)
make uninstall    Remove filetree from /usr/local/bin and ~/.local/bin
make usage        Show filetree usage
make sync-skill   Sync skill files to ~/Code/agent-skills-toolbox/skills/filetree
```

---

## Claude Code skill

<details>
<summary>Install the <code>/filetree</code> slash command for Claude Code</summary>

This repository ships a `/filetree` slash command skill for [Claude Code](https://claude.ai/code)
that lets Claude generate ASCII file trees -- no terminal required. Just describe what you want
and Claude will invoke the skill automatically.

### What it accepts

| Input | Example |
|---|---|
| Current directory | `.` |
| Specific path | `src/` |
| With style | `--style ascii .` |
| With excludes | `--exclude-dirs dist:build src/` |

### Invoking the skill

Use the slash command directly:

```
/filetree .
/filetree src/
/filetree --style ascii .
```

Or just describe what you want in natural language -- Claude will invoke the skill automatically:

> *"Show me the file tree for this project"*
>
> *"Add a directory tree to the README"*
>
> *"What's the structure of the src/ folder?"*

### Installing the skill

#### Option A -- sync locally via `make`

```bash
# from inside the filetree directory
make sync-skill
```

This syncs `filetree.sh`, `SKILL.md`, and `README.md` to:

```
~/Code/agent-skills-toolbox/skills/filetree/
```

Override the target directory with `SKILLS_DIR`:

```bash
make sync-skill SKILLS_DIR=/path/to/your/project/.claude/skills/filetree
```

#### Option B -- copy manually

```bash
mkdir -p .claude/skills/filetree
cp filetree.sh SKILL.md README.md .claude/skills/filetree/
```

</details>

---

## Requirements

- `bash` 3.2+ (the macOS default is fine)
- `find`, `awk`, `sort` (standard POSIX tools -- available on macOS and Linux)
- `make` (for Makefile targets)
