# project-scaffold

One command to a production-ready Python project. Generates a full project tree with a
Dockerfile-based devcontainer, VS Code settings and extensions, a Makefile with venv/lint/test/ci
targets, pyproject.toml, pytest scaffolding, a commit-msg hook, and a .gitignore - all consistent
and ready to open in VS Code or elsewhere. Optional GitHub SSH wiring mounts your key directly into the
devcontainer. `Lite` mode clones any existing scaffold/project to a new name with a clean git history so you canbe sure you have all the relevent build tools available.

---

## Install

Clone this repo and run the install target from the repo root:

```bash
git clone https://github.com/rondomondo/agent-skills-beta.git
cd agent-skills-beta
make skill-install name=project-scaffold
```

This copies the skill to `~/.claude/skills/project-scaffold/`. Claude Code picks it up automatically from that path.

---

## Quick start

### 1. Create a new Python project with all the build tools.

```
/project-scaffold create a new Python project called data-pipeline
```

Claude might ask a few follow-up questions (about devcontainer mode, SSH key, extra VS Code extensions) unless you already specified, then generates the full project tree under `~/Code/data-pipeline/`.

### 2. Lite mode - clone an existing scaffold

```
/project-scaffold clone the `data-pipeline` project as `my-new-service`
```

This copies an existing scaffolded project to a new name, substitutes the project name throughout all files, and resets git history. No questions about devcontainer or SSH - everything is carried over from the source project.

### 3. Free-text prompts

The skill responds to natural language, not just the slash command prefix. These all work:

```
scaffold a new project called ml-pipeline, wire in my SSH key at ~/.ssh/id_ed25519
```

```
create a new repo called invoice-api, use a Dockerfile-based devcontainer
```

```
bootstrap a Python workspace under ~/Projects for a service called auth-proxy
```

### 4. Run non-interactively with `claude -p`

Use `claude -p` to scaffold without any interactive prompts - pass all requirements in the message:

```bash
claude -p "scaffold a new Python project called batch-runner, Dockerfile-based devcontainer, no SSH key, project root ~/Code"
```

Or in lite mode:

```bash
claude -p "clone this scaffold as reporting-service, source project ~/Code/data-pipeline"
```

### 5. Build the devcontainer image locally with `docker-build`

Once a project is scaffolded, you can build the devcontainer image outside of VS Code using the generated Makefile:

```bash
cd ~/Code/data-pipeline
make docker-build
```

Override the image name or tag as needed:

```bash
make docker-build IMAGE_NAME=my-registry/data-pipeline IMAGE_TAG=0.1.0
```

The generated project also includes `make docker-run` and `make docker-shell` for running the image interactively.

---

## What it generates

```
<project-name>/
├── .devcontainer/
│   ├── devcontainer.json
│   ├── Dockerfile              <- Dockerfile-based mode only
│   └── scripts/
│       └── postCreate.sh
├── .vscode/
│   ├── extensions.json
│   └── settings.json
├── .github/
├── src/
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_sample.py
├── .githooks/
│   └── commit-msg
├── Makefile
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .python-version
├── .gitignore
└── README.md
```

---

## Devcontainer build modes

### Dockerfile-based (recommended default)

Bakes system packages, Claude Code, Oh My Zsh, and tooling into image layers. Container startup is fast after the first build. `postCreate.sh` is trimmed to SSH key permissions and workspace setup only.

### Base image + postCreate (standard)

Uses a Microsoft devcontainer base image and runs the full `postCreate.sh` on every new container. Simpler but slower - re-downloads and installs everything each time.

---

## Makefile targets (generated project)

| Target | Description |
|--------|-------------|
| `make help` | Show all available targets (default) |
| `make venv` | Create `.venv` using the correct Python version |
| `make install` | Install dependencies into venv |
| `make format` | Run black + isort |
| `make lint` | Run ruff + mypy |
| `make typecheck` | Run mypy |
| `make test` | Run pytest with coverage |
| `make ci` | Run format + lint + typecheck + test in sequence |
| `make docker-build` | Build the devcontainer image locally |
| `make docker-run` | Run the image interactively, mounting project root |
| `make docker-shell` | Open a bash shell in the image |
| `make clean` | Remove build artifacts, caches, `.venv` |
| `make github-check` | Test GitHub SSH connectivity (if SSH key configured) |

---

## After scaffolding

1. Open the folder in VS Code - it will prompt **Reopen in Container**
2. Wait for the container to build (first time only - subsequent starts use Docker layer cache)
3. Run `make install` to install project dependencies
4. Run `make test` to verify the setup works
5. If SSH was configured, run `make github-check` to verify GitHub connectivity
6. Commit the initial scaffold:
   ```bash
   cd <project-name>
   git init
   git config core.hooksPath .githooks
   git add .
   git commit -m "chore: initial scaffold"
   ```

---

## VS Code extensions included by default

`ms-python.python`, `ms-python.debugpy`, `ms-python.pylint`, `ms-python.autopep8`, `ms-python.vscode-pylance`, `ms-python.mypy-type-checker`, `ms-python.isort`, `charliermarsh.ruff`, `njpwerner.autodocstring`, `anthropic.claude-code`
