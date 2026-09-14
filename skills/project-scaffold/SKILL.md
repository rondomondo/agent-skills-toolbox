---
name: project-scaffold
description: >
    0.0.3 Scaffold a production-ready Python project in one command. Generates the full project
    tree: devcontainer (Dockerfile-based or base image), VS Code settings and extensions,
    Makefile with venv/lint/test/ci targets, pyproject.toml, pytest setup, commit-msg hook,
    and .gitignore - all wired together and ready to open in VS Code. Optionally mounts a
    GitHub SSH key into the devcontainer for private repo access.
    Lite mode clones an existing scaffold to a new name, substitutes the project name throughout,
    and resets git history - no follow-up questions needed.
    Use this skill whenever the user asks to create a new project, initialize a repo, set up a
    workspace, or bootstrap a Python codebase. Also triggers on: "clone this scaffold",
    "copy this project", "reset project", "new copy of", "lite scaffold", "clean copy".
    Full mode triggers: "scaffold a project", "create a new project", "new repo",
    "set up a project", "bootstrap a project", "initialize a project". Python + pip only.
---

# Project Scaffold Skill

Generates a complete, ready-to-open Python project: devcontainer config, VS Code settings and
extensions, a full Makefile, pytest setup, commit-msg hook, and GitHub SSH wiring - everything
configured and consistent from the first commit.

---

## Step 1: Gather Requirements

Ask the user for the following. Collect all answers before generating anything.

**Required:**

- **Project name** -- used for the root folder name and package identifiers

**Optional (ask, but have sensible defaults):**

- **Devcontainer build mode** -- ask:
  _"Do you want a **Dockerfile-based** devcontainer (pre-baked image, fast container startup --
  recommended) or a **base image + postCreate script** (standard, pulls fresh each time)?"_
  Default: Dockerfile-based.
- **GitHub SSH private key path** -- for cloning private repos inside the devcontainer.
  Ask: _"Do you have a GitHub SSH private key you'd like wired into the devcontainer? If so,
  what's the path on your host machine (e.g. ~/.ssh/id_ed25519)?"_
  Default: skip if not provided.
- **Extra VS Code extensions** -- beyond the Python defaults.
  Ask: _"Any extra VS Code extensions you want pre-installed?"_
- **Project root folder for the new scaffolded project**:
    - Default: `~/Code` -- ask the user only if they want a different location

---

## Step 2: Choose Devcontainer Build Mode

Based on the user's answer:

### Dockerfile-based (recommended default)

Generate a `.devcontainer/Dockerfile` alongside `devcontainer.json`. The Dockerfile bakes all
heavy system-level installs into image layers (cached after first build). The `postCreate.sh`
is trimmed to only project-specific runtime steps (SSH key perms, workspace dirs, shell aliases,
exporting and adding environment variables to the shell ~/.zshrc and ~/.bashrc files).

In `devcontainer.json`, replace `"image": "..."` with:

```json
"build": {
  "dockerfile": "Dockerfile",
  "context": ".."
}
```

See `references/python.md` for the Dockerfile template.

### Base image + postCreate script (standard)

Use `"image": "..."` in `devcontainer.json` and run the full `postCreate.sh` on every new
container. Simpler but slower -- every `postCreate.sh` run re-downloads and installs everything.

---

## Step 3: Read the Reference Files

Read all of these before generating anything:

| File                                 | Purpose                                                      |
| ------------------------------------ | ------------------------------------------------------------ |
| `references/python.md`               | devcontainer.json, Dockerfile, postCreate.sh, boilerplate    |
| `references/common.md`               | Index of all templates + postStartCommand inline             |
| `references/makefile.template.md`    | Full Makefile -- copy and substitute `<PROJECT_NAME>`         |
| `references/gitignore.template.md`   | Full .gitignore -- use as-is                                  |
| `references/pyproject.template.toml` | Full pyproject.toml -- substitute all `<PLACEHOLDER>` values  |
| `references/readme.template.md`      | Full README.md -- substitute `<PROJECT_NAME>`                 |
| `references/commit-msg.template.sh`  | Full `.githooks/commit-msg` -- copy verbatim                  |
| `references/versions.md`             | All version pins -- read before writing Dockerfile/postCreate |

---

## Step 4: Generate the Project

Create all files under `~/Code/<project-name>` (or the user-specified root).

### Project structure

```
<project-name>/
├── .devcontainer/
│   ├── devcontainer.json
│   ├── Dockerfile              <- only if Dockerfile-based mode chosen
│   └── scripts/
│       └── postCreate.sh
├── .vscode/
│   ├── extensions.json
│   └── settings.json
├── .github/
│   └── (empty, ready for workflows)
├── src/
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_sample.py
├── Makefile
├── .gitignore
├── .githooks/
│   └── commit-msg
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .python-version
└── README.md
```

---

## Step 5: Makefile

Always generate a `Makefile`. See `references/common.md` -> `makefile.template.md` for the full template.

**Required targets** (all projects):

- `make help` -- prints available targets (always first, always default)
- `make check-sys-deps` -- verify required system packages are on PATH
- `make check-venv` -- verify the virtual environment is activated
- `make venv` -- creates `.venv` using the correct Python version
- `make install` -- installs `requirements.txt` + `requirements-dev.txt` into the active venv
- `make format` -- runs `black` + `isort`
- `make lint` -- runs `ruff` + `mypy`
- `make typecheck` -- runs `mypy`
- `make test` -- runs `pytest` with coverage
- `make ci` -- runs format + lint + typecheck + test in sequence
- `make clean` -- removes build artifacts, caches, `.venv`

**Conditional targets:**

- `make github-check` -- include only if the user provided an SSH key path

---

## Step 6: GitHub SSH Setup

### If the user provided an SSH key path

Extract the filename from the path (e.g. `~/.ssh/id_ed25519` -> `id_ed25519`).
Call that `<SSH_KEY_FILENAME>` -- substitute it everywhere below.

**devcontainer.json** -- mount only that file, not the whole `~/.ssh` directory:

```json
"mounts": [
  "source=<key-path>,target=/home/vscode/.ssh/<SSH_KEY_FILENAME>,type=bind,consistency=cached"
]
```

**postCreate.sh** -- replace the `SSH_KEY=<SSH_KEY_FILENAME>` placeholder with the actual filename.
The `if` block in the template then handles permissions and `known_hosts` automatically.

**Makefile** -- add the `github-check` target (see `references/makefile.template.md`).

### If no SSH key was provided

- Skip the SSH mount in `devcontainer.json` entirely -- do not mount `~/.ssh`
- Remove the `SSH_KEY` / `if` block from `postCreate.sh`
- Omit the `github-check` Makefile target

---

## Step 7: Git Init

After generating all files:

1. `.gitignore` -- from `references/gitignore.template.md`, use as-is
2. `.githooks/commit-msg` -- from `references/commit-msg.template.sh`, copy verbatim, `chmod +x`
3. `README.md` -- from `references/readme.template.md`, substitute `<PROJECT_NAME>`; remove the GitHub SSH section if no key was configured
4. Tell the user to run:
    ```bash
    cd <project-name>
    git init
    git config core.hooksPath .githooks
    git add .
    git commit -m "chore: initial scaffold"
    ```

---

---

## Lite Mode: Clone / Reset an Existing Scaffold

Use this mode when the user wants to copy an existing scaffolded project to a new name -- no
questions about devcontainer mode, SSH keys, or extensions. Everything is copied from the source
project and the project name is substituted throughout.

### Trigger phrases

- "clone this scaffold as `<name>`"
- "copy this project to `<name>`"
- "reset project / clean copy"
- "lite scaffold for `<name>`"
- "new copy of this project"

### Step L1: Gather Requirements

Ask only:

- **New project name** -- used for the destination folder and all `<PROJECT_NAME>` substitutions
- **Source project path** -- default: current working directory
- **Destination root** -- default: same parent directory as the source project

### Step L2: Copy and Substitute

1. Copy the entire source project tree to `<destination-root>/<new-project-name>/`
2. Exclude: `.venv/`, `__pycache__/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`,
   `dist/`, `build/`, `*.egg-info/`, `.coverage`, `htmlcov/`, `*.pyc`, `.git/`
3. In every copied file, replace all occurrences of the old project name with the new project name.
   Files to update (at minimum):
    - `Makefile` -- comment header
    - `pyproject.toml` -- `name`, `[tool.mypy]` source root if present
    - `README.md` -- title and any references
    - `src/__init__.py` -- docstring
    - `.devcontainer/devcontainer.json` -- `"name"` field
    - `.devcontainer/scripts/postCreate.sh` -- any echo banners
    - `.devcontainer/scripts/postStartCommand.sh` -- comment header

### Step L3: Reset Git History

After copying:

1. Delete the copied `.git/` directory (start clean)
2. Tell the user to run:
    ```bash
    cd <new-project-name>
    git init
    git config core.hooksPath .githooks
    git add .
    git commit -m "chore: initial scaffold"
    ```

### Step L4: Output (Lite Mode)

Print a one-line confirmation:

```
Cloned scaffold -> <destination-root>/<new-project-name>/
Substituted project name: <old-name> -> <new-name>
Git history reset -- run the commands above to initialise a fresh repo.
```

---

## Output

Print a summary tree of everything created, then list the `make` targets available.
Remind the user:

- Open the folder in VS Code and it will prompt to **Reopen in Container**
- Activate venv: `source .venv/bin/activate`
- Run `make install` to install dependencies
- Run `make test` to verify everything works
- If SSH was configured, run `make github-check` to verify connectivity
