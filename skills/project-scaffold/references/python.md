# Python Reference

## devcontainer.json

Two variants depending on build mode chosen in Step 2.
The JSON body is identical between them -- only the `"build"` vs `"image"` key differs.
`UV_LINK_MODE` is kept for future use; it has no effect with pip.

### Dockerfile-based (recommended)

```json
{
  "$schema": "https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json",
  "name": "<PROJECT_NAME>",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".."
  },
  "runArgs": [
    "--cap-add=NET_ADMIN",
    "--cap-add=NET_RAW"
  ],
  "init": true,
  "updateRemoteUserUID": true,
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=cached",
  "workspaceFolder": "/workspace",
  "remoteUser": "vscode",
  "containerUser": "vscode",
  "postCreateCommand": "chmod +x /workspace/.devcontainer/scripts/postCreate.sh && /workspace/.devcontainer/scripts/postCreate.sh",
  "mounts": [
    "source=claude-code-bashhistory-${devcontainerId},target=/commandhistory,type=volume",
    "source=${localEnv:HOME}/.claude,target=/home/vscode/.claude,type=bind",
    "source=${localEnv:HOME}/.ssh,target=/home/vscode/.ssh,type=bind,consistency=cached",
    "source=${localEnv:HOME}/.gitconfig,target=/home/vscode/.gitconfig,type=bind,readonly"
  ],
  "containerEnv": {
    "NODE_OPTIONS": "--max-old-space-size=4096",
    "CLAUDE_CONFIG_DIR": "/home/vscode/.claude",
    "POWERLEVEL9K_DISABLE_GITSTATUS": "true",
    "GIT_CONFIG_GLOBAL": "/home/vscode/.gitconfig.local",
    "NPM_CONFIG_IGNORE_SCRIPTS": "true",
    "NPM_CONFIG_AUDIT": "true",
    "NPM_CONFIG_FUND": "false",
    "NPM_CONFIG_SAVE_EXACT": "true",
    "NPM_CONFIG_UPDATE_NOTIFIER": "false",
    "NPM_CONFIG_MINIMUM_RELEASE_AGE": "1440",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PIP_DISABLE_PIP_VERSION_CHECK": "1"
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "anthropic.claude-code@2.1.111",
        "ms-python.python",
        "ms-python.debugpy",
        "ms-python.pylint",
        "ms-python.autopep8",
        "ms-python.vscode-pylance",
        "ms-python.mypy-type-checker",
        "ms-python.vscode-python-envs",
        "ms-python.isort",
        "njpwerner.autodocstring",
        "charliermarsh.ruff"
      ],
      "settings": {
        "terminal.integrated.defaultProfile.linux": "zsh",
        "terminal.integrated.profiles.linux": {
          "bash": { "path": "bash", "icon": "terminal-bash" },
          "zsh": { "path": "zsh" }
        },
        "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
        "python.useEnvironmentsExtension": true,
        "editor.formatOnSave": true,
        "[python]": {
          "editor.defaultFormatter": "charliermarsh.ruff",
          "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit",
            "source.fixAll.ruff": "explicit"
          }
        },
        "ruff.enable": true,
        "mypy-type-checker.args": ["--ignore-missing-imports"],
        "autopep8.args": ["--in-place", "--aggressive", "--max-line-length", "119"],
        "pylint.cwd": "${fileDirname}",
        "pylint.enabled": true,
        "pylint.args": ["--max-line-length", "119", "--disable", "C0111"],
        "python.terminal.useEnvFile": true
      }
    }
  }
}
```

### Base image + postCreate script (standard)

Replace the `"build"` block with:

```json
"image": "mcr.microsoft.com/devcontainers/python:3.12-bullseye",
"features": {
  "ghcr.io/devcontainers/features/github-cli:1": {},
  "ghcr.io/devcontainers/features/python:1": { "version": "3.12" }
},
```

Everything else (mounts, containerEnv, customizations) is identical to the Dockerfile-based variant above.

---

## .devcontainer/Dockerfile (Dockerfile-based mode only)

Layer ordering is chosen for cache efficiency: things that change rarely go first.
Node + fnm are always included -- they are required for Claude Code.

```dockerfile
# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=v23.3.0
ARG FNM_VERSION=1.37.1
ARG GIT_DELTA_VERSION=0.18.2
ARG ZSH_IN_DOCKER_VERSION=1.2.1
ARG CLAUDE_CODE_VERSION=2.1.111

# -- Base --------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bullseye AS base

ARG NODE_VERSION
ARG FNM_VERSION
ARG GIT_DELTA_VERSION
ARG ZSH_IN_DOCKER_VERSION
ARG CLAUDE_CODE_VERSION

ENV DEBIAN_FRONTEND=noninteractive \
    DEVCONTAINER=true \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_OPTIONS="--max-old-space-size=4096" \
    NPM_CONFIG_IGNORE_SCRIPTS=true \
    NPM_CONFIG_AUDIT=true \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_SAVE_EXACT=true \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_MINIMUM_RELEASE_AGE=1440 \
    POWERLEVEL9K_DISABLE_GITSTATUS=true \
    FNM_DIR=/opt/fnm \
    PATH=/opt/fnm:/workspace:/home/vscode/.local/bin:$PATH

# -- Layer 1: System packages (changes rarely -- long cache life) --------------
RUN apt-get update && apt-get install -y --no-install-recommends \
      less git procps sudo curl wget unzip gnupg2 \
      zsh fzf man-db vim jq make strace htop \
      iptables ipset iproute2 dnsutils aggregate ssh-client docker.io \
      python3-pip python3-venv libmagic1 libmagic-dev mlocate \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# -- Layer 2: git-delta -------------------------------------------------------
RUN ARCH=$(dpkg --print-architecture) && \
    wget -q "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
    dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
    rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

# -- Layer 3: Node via fnm (required for Claude Code) ------------------------
RUN curl -fsSL https://fnm.vercel.app/install | bash -s -- --install-dir "$FNM_DIR" --skip-shell && \
    export PATH="$FNM_DIR:$PATH" && \
    eval "$(fnm env)" && \
    fnm install ${NODE_VERSION} && \
    fnm default ${NODE_VERSION} && \
    fnm exec --using=${NODE_VERSION} node --version

# -- Layer 4: Claude Code (global npm install) --------------------------------
RUN export PATH="$FNM_DIR:$PATH" && eval "$(fnm env)" && \
    npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# -- Layer 5: Zsh + Oh My Zsh ------------------------------------------------
RUN sh -c "$(curl -fsSL https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
      -p git -x && \
    echo "alias ll='ls -lrta'" >> /root/.zshrc && \
    echo "alias c=clear"       >> /root/.zshrc && \
    echo "alias ll='ls -lrta'" >> /root/.bashrc && \
    echo "alias c=clear"       >> /root/.bashrc && \
    echo "eval \$(fnm env)"    >> /root/.bashrc && \
    echo "eval \$(fnm env)"    >> /root/.zshrc && \
    echo "PATH=$FNM_DIR:/workspace:/home/vscode/.local/bin:\$PATH" >> /root/.bashrc && \
    echo "PATH=$FNM_DIR:/workspace:/home/vscode/.local/bin:\$PATH" >> /root/.zshrc

# -- Layer 6: vscode user + persistent directories ---------------------------
RUN groupadd --gid 1000 vscode && \
    useradd  --uid 1000 --gid 1000 -m -s /bin/zsh vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/vscode && \
    mkdir -p /commandhistory /workspace /home/vscode/.claude /opt && \
    touch /commandhistory/.bash_history /commandhistory/.zsh_history && \
    cp /root/.zshrc /home/vscode/.zshrc && \
    cp /root/.bashrc /home/vscode/.bashrc && \
    cp -vR /root/.oh-my-zsh /home/vscode/.oh-my-zsh && \
    chown -R vscode:vscode /commandhistory /workspace /home/vscode && \
    usermod -aG docker vscode && \
    updatedb || true

USER vscode
WORKDIR /workspace
```

**Layer cache strategy:**
- Layer 1: OS packages -- rarely changes, longest cache life
- Layer 2: git-delta -- rebuilds only when `GIT_DELTA_VERSION` changes
- Layer 3: Node/fnm -- rebuilds only when `NODE_VERSION` changes
- Layer 4: Claude Code -- rebuilds only when `CLAUDE_CODE_VERSION` bumps
- Layers 5-6: Shell config + user -- rebuilds only if zsh config changes

To rebuild after changing a version pin: `docker build --no-cache .devcontainer/ -t <project>-dev`

---

## .devcontainer/scripts/postCreate.sh

### Dockerfile-based mode (slim -- system packages already baked in)

`SSH_KEY` is substituted with the filename of the key the user provided (e.g. `id_ed25519`).
If no SSH key was configured, remove the entire `if` block.

```bash
#!/usr/bin/env bash
set -euo pipefail

SSH_KEY=<SSH_KEY_FILENAME>

if [ -f "$HOME/.ssh/$SSH_KEY" ]; then
  chmod 700 "$HOME/.ssh"
  chmod 600 "$HOME/.ssh/$SSH_KEY"
  ssh-keyscan github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null || true
  echo "==> SSH key permissions set for $SSH_KEY."
fi

mkdir -p /workspace "$HOME/.claude"
chown -R "$(id -u):$(id -g)" /workspace "$HOME/.claude" 2>/dev/null || true
sed -i 's|/root/.oh-my-zsh|/home/vscode/.oh-my-zsh|g' ~/.zshrc ~/.bashrc
echo "eval \$(fnm env)" >> "/home/vscode/.zshrc"
echo "==> Container ready. Activate your venv and run 'make install'"
```

### Base image + postCreate script (full -- installs everything at container start)

Installs system packages, Node/fnm, and Claude Code then exits.
Run `make install` after activating the venv.

Same SSH key substitution rule applies: replace `<SSH_KEY_FILENAME>` with the key filename,
or remove the `if` block entirely if no key was provided.

```bash
#!/usr/bin/env bash
set -euo pipefail

SSH_KEY=<SSH_KEY_FILENAME>

if [ -f "$HOME/.ssh/$SSH_KEY" ]; then
  chmod 700 "$HOME/.ssh"
  chmod 600 "$HOME/.ssh/$SSH_KEY"
  ssh-keyscan github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null || true
  echo "==> SSH key permissions set for $SSH_KEY."
fi

echo "==> Installing system packages..."
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    less git procps sudo curl wget unzip gnupg2 \
    zsh fzf man-db vim jq make strace htop \
    iptables ipset iproute2 dnsutils aggregate ssh-client docker.io \
    python3-pip python3-venv libmagic1 libmagic-dev mlocate \
    && sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*

export NODE_VERSION=v23.3.0
export FNM_DIR="$HOME/.fnm"

curl -fsSL https://fnm.vercel.app/install | bash -s -- --install-dir "$FNM_DIR" --skip-shell && \
  export PATH="$FNM_DIR:$PATH" && \
  eval "$(fnm env)" && \
  fnm install ${NODE_VERSION} && \
  fnm default ${NODE_VERSION}

export GIT_DELTA_VERSION=0.18.2
ARCH=$(dpkg --print-architecture) && \
  sudo wget -q "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  sudo dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  sudo rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

export ZSH_IN_DOCKER_VERSION=1.2.1
sh -c "$(curl -fsSL https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git -x

mkdir -p /commandhistory /workspace "$HOME/.claude" /opt && \
  touch /commandhistory/.bash_history /commandhistory/.zsh_history && \
  chown -R "$(id -u):$(id -g)" /commandhistory /workspace "$HOME/.claude" /opt

sudo cp -vR /root/.oh-my-zsh /home/vscode/.oh-my-zsh && \
    sudo chown -R vscode:vscode /home/vscode/.oh-my-zsh && \
    sudo updatedb || true

sudo usermod -aG docker vscode

export CLAUDE_CODE_VERSION=2.1.111
export PATH="$FNM_DIR:$PATH" && eval "$(fnm env)"
sudo npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

echo "alias ll='ls -lrta'" >> "${HOME}/.zshrc"
echo "alias c=clear"       >> "${HOME}/.zshrc"
echo "eval \$(fnm env)"    >> "${HOME}/.zshrc"
echo "alias ll='ls -lrta'" >> "${HOME}/.bashrc"
echo "alias c=clear"       >> "${HOME}/.bashrc"
echo "eval \$(fnm env)"    >> "${HOME}/.bashrc"
echo "PATH=$HOME/.local/bin:/workspace:\$PATH" >> "${HOME}/.bashrc"

sed -i 's|/root/.oh-my-zsh|/home/vscode/.oh-my-zsh|g' ~/.zshrc ~/.bashrc

sudo updatedb || true

echo "==> System packages installed. Activate your venv and run 'make install'"
```

---

## Package manager: pip

`pip` is the only supported package manager.

**requirements.txt**

```
# Runtime dependencies -- add your deps here
```

**requirements-dev.txt**

```
pytest>=8.0
pytest-cov>=5.0
black>=24.0
isort>=5.13
ruff>=0.4
mypy>=1.9
autopep8
```

**pyproject.toml** -- see [`references/pyproject.template.toml`](pyproject.template.toml) for the full template.

---

## Boilerplate files

### .python-version

```
3.12
```

### src/__init__.py

```python
"""<PROJECT_NAME> package."""
```

### tests/__init__.py

```python
```

### tests/test_sample.py

```python
"""Sample test -- replace with real tests."""


def test_placeholder() -> None:
    assert True
```
