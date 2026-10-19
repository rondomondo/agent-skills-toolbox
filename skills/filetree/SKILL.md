---
name: filetree
description: >
    Generate ASCII file trees from a directory for use in READMEs, documentation, or to
    communicate project structure. Use this skill whenever the user wants to visualise a
    directory structure, produce a tree diagram, add a file tree to a README, or understand
    the layout of a project. Trigger on "file tree", "directory tree", "show structure",
    "tree diagram", "show me the layout", "add a tree to README", or any request to render
    a folder hierarchy as text.
---

# filetree Skill

You are generating ASCII file trees using `filetree` (a pure-bash wrapper around `find`),
which walks a directory recursively and renders an ASCII tree suitable for READMEs and docs.

---

## When to use this skill

- User wants to see or document a directory structure
- User asks to "add a file tree" or "show me the layout" of a project
- User wants a tree diagram for a README or documentation page

---

## Quickstart

```bash
# Tree of the current directory
filetree .

# Tree of a specific directory
filetree src/

# ASCII style (instead of unicode)
filetree --style ascii .

# Exclude extra directories
filetree --exclude-dirs dist:build src/
```

---

## Step 0 - Resolve environment and install tool

```bash
if [ "${IS_SANDBOX:-no}" = "yes" ] || [ "${IS_SANDBOX:-no}" = "1" ] || [ "${IS_SANDBOX:-no}" = "true" ]; then
    SKILL_DIR="/mnt/skills/user/filetree"
    cp "$SKILL_DIR/filetree.sh" /usr/local/bin/filetree.sh
    chmod +x /usr/local/bin/filetree.sh
    ln -sf /usr/local/bin/filetree.sh /usr/local/bin/filetree
else
    command -v filetree >/dev/null 2>&1 || {
        echo "ERROR: filetree not installed. Run: make -C ~/Code/toolbox/filetree install" >&2
        exit 1
    }
fi
```

## Step 1 - Check for the tool

```bash
which filetree
```

If missing locally (there is no Docker image for this tool, install from a clone of the toolbox repo):

```bash
make -C ~/Code/toolbox/filetree install
```

---

## Step 2 - Determine the target directory

Use the directory the user specifies, or default to the current working directory (`.`).

---

## Step 3 - Run filetree

```bash
# Default (unicode, current dir)
filetree .

# Specific directory
filetree <path>

# ASCII style (portable, no unicode box-drawing)
filetree --style ascii <path>

# Compact (minimal indentation)
filetree --style compact <path>

# Exclude extra dirs (colon-separated)
filetree --exclude-dirs dist:build:coverage <path>
```

---

## Step 4 - Use the output

Paste the tree output directly into a README fenced block:

````markdown
```
.
├── src/
│   ├── main.py
│   └── utils.py
└── tests/
    └── test_main.py
```
````

---

## Options reference

| Option | Description |
|---|---|
| `[DIR]` | Directory to tree (default: `.`) |
| `-s, --style STYLE` | `unicode` (default), `ascii`, `compact` |
| `-e, --exclude-dirs DIRS` | Colon-separated extra dirs to exclude |
| `-h, --help` | Show help |

## Default excluded directories

`.git`, `.venv`, `venv`, `node_modules`, `__pycache__`, `.DS_Store`, `dist`, `.idea`,
`.mypy_cache`, `.pytest_cache`, `.tox`

Excludes match by name at any depth (files too), so `--exclude-dirs build` also hides `src/build/`.

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Tree rendered successfully |
| 1 | Directory not found or invalid option |

---

## Error handling

| Symptom | Likely cause | Fix |
|---|---|---|
| `filetree not found` | Not installed | Run `make install` from `toolbox/filetree/` |
| `directory not found: <path>` | Path does not exist | Check the path with `ls` |
| Unicode boxes look wrong | Terminal doesn't support unicode | Use `--style ascii` |
