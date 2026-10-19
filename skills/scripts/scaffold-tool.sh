#!/usr/bin/env bash
# =============================================================================
# scaffold-tool.sh
#
# Bootstrap a new toolbox tool with all the skill-aware scaffolding in place.
# Creates the toolbox subdirectory, a matching agent-skills-toolbox/skills/
# entry, and optionally patches the root Makefile.
#
# Usage:
#   scaffold-tool.sh <name> [--type script|docker] [--description "..."]
#                           [--toolbox-dir DIR] [--skills-dir DIR]
#                           [--no-makefile-patch] [--dry-run]
#
#   <name>                   Tool name (kebab-case, e.g. my-tool)
#   --type script|docker     Type of tool (default: script)
#   --description "..."      One-line description for SKILL.md and README.md
#   --toolbox-dir DIR        Path to toolbox root (default: parent of this script)
#   --skills-dir DIR         Path to agent-skills-toolbox/skills/ (default: ~/Code/agent-skills-toolbox/skills)
#   --no-makefile-patch      Skip patching the root Makefile
#   --dry-run                Print what would be created without writing files
#
# What it creates:
#   toolbox/<name>/
#     Makefile        -- skill-aware, install/uninstall/sync-skill targets
#     SKILL.md        -- agent instruction document (frontmatter + steps)
#     README.md       -- user documentation with Claude Code skill section
#     <name>[.sh]     -- main script stub (.sh for script-type, bare for docker-type)
#     [Dockerfile]    -- minimal Dockerfile stub (docker-type only)
#     [entrypoint.sh] -- container entrypoint stub (docker-type only)
#     [install.sh]    -- streaming installer: docker run ... install | sh (docker-type only)
#     [uninstall.sh]  -- streaming uninstaller (docker-type only)
#     [VERSION]       -- image version, bumped by make release (docker-type only)
#
#   agent-skills-toolbox/skills/<name>/
#     Makefile  SKILL.md  README.md  <name>[.sh]   -- (mirrored)
#
#   toolbox/Makefile  -- SCRIPT_TOOLS or DOCKER_TOOLS line patched to include <name>
#
# Requirements: bash 3.2+
# =============================================================================

set -euo pipefail

# -- colour helpers ------------------------------------------------------------
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { printf "${CYAN}[scaffold]${RESET}  %s\n" "$*"; }
success() { printf "${GREEN}[scaffold]${RESET}  %s\n" "$*"; }
warn()    { printf "${YELLOW}[scaffold]${RESET}  %s\n" "$*"; }
die()     { printf "${RED}[scaffold]${RESET}  ERROR: %s\n" "$*" >&2; exit 1; }
dry()     { printf "${YELLOW}[dry-run]${RESET}   %s\n" "$*"; }

# -- defaults ------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLBOX_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_ROOT="${HOME}/Code/agent-skills-toolbox/skills"

TOOL_NAME=""
TOOL_TYPE="script"
TOOL_DESC=""
NO_MAKEFILE_PATCH=false
DRY_RUN=false

# -- usage ---------------------------------------------------------------------
usage() {
  sed -n '3,28p' "$0" | sed 's/^# \{0,2\}//'
  exit 0
}

# -- arg parsing ---------------------------------------------------------------
parse_args() {
  [[ $# -eq 0 ]] && usage

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)           usage ;;
      --type)              TOOL_TYPE="${2:?--type requires a value}"; shift 2 ;;
      --description)       TOOL_DESC="${2:?--description requires a value}"; shift 2 ;;
      --toolbox-dir)       TOOLBOX_ROOT="${2:?--toolbox-dir requires a value}"; shift 2 ;;
      --skills-dir)        SKILLS_ROOT="${2:?--skills-dir requires a value}"; shift 2 ;;
      --no-makefile-patch) NO_MAKEFILE_PATCH=true; shift ;;
      --dry-run)           DRY_RUN=true; shift ;;
      -*)                  die "Unknown option: $1" ;;
      *)
        [[ -z "$TOOL_NAME" ]] || die "Unexpected argument: $1 (tool name already set to '$TOOL_NAME')"
        TOOL_NAME="$1"; shift ;;
    esac
  done

  [[ -n "$TOOL_NAME" ]] || die "Tool name is required. Usage: scaffold-tool.sh <name> [options]"

  [[ "$TOOL_NAME" =~ ^[a-z][a-z0-9-]*$ ]] \
    || die "Tool name must be lowercase kebab-case (e.g. my-tool). Got: '$TOOL_NAME'"

  [[ "$TOOL_TYPE" == "script" || "$TOOL_TYPE" == "docker" ]] \
    || die "--type must be 'script' or 'docker'. Got: '$TOOL_TYPE'"

  [[ -n "$TOOL_DESC" ]] || TOOL_DESC="${TOOL_NAME} -- TODO: add a description"
}

# -- file writers --------------------------------------------------------------
# Each write_<kind> function takes the destination path as $1 and writes
# directly to it (no command-substitution capture, so heredoc tabs are safe).

write_makefile_script() {
  local path="$1" name="$2"
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"
  cat > "$path" <<MAKEFILE
# ============================================================
# ${name} -- Makefile
# ============================================================
.DEFAULT_GOAL := help
MAKEFLAGS     += --no-print-directory
SHELL         := /bin/bash

# -- Colors ---------------------------------------------------
BOLD   := \033[1m
GREEN  := \033[32m
CYAN   := \033[36m
RED    := \033[31m
YELLOW := \033[33m
RESET  := \033[0m

# -- Paths ----------------------------------------------------
SCRIPT  := ${name}
DESTDIR := /usr/local/bin

# -- Skill distribution ---------------------------------------
SKILL_NAME  := ${name}
SKILLS_DIR  ?= \$(HOME)/Code/agent-skills-toolbox/skills/\$(SKILL_NAME)
SKILL_FILES := \$(SCRIPT).sh SKILL.md README.md

# -- Help -----------------------------------------------------
.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} \
	  /^\#\#@/ { printf "\n\033[1m%s\033[0m\n", substr(\$\$0,5) } \
	  /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", \$\$1, \$\$2 }' \
	  \$(MAKEFILE_LIST)

##@ Install

.PHONY: install
install: ## Install ${name}; tries /usr/local/bin (direct then sudo), falls back to ~/.local/bin
	@if install -m 755 \$(SCRIPT).sh /usr/local/bin/\$(SCRIPT).sh 2>/dev/null; then \\
	  IDIR=/usr/local/bin; \\
	elif sudo install -m 755 \$(SCRIPT).sh /usr/local/bin/\$(SCRIPT).sh 2>/dev/null; then \\
	  IDIR=/usr/local/bin; \\
	else \\
	  mkdir -p "\$\$HOME/.local/bin"; \\
	  install -m 755 \$(SCRIPT).sh "\$\$HOME/.local/bin/\$(SCRIPT).sh"; \\
	  IDIR="\$\$HOME/.local/bin"; \\
	  case ":\$\$PATH:" in \\
	    *":\$\$IDIR:"*) ;; \\
	    *) RCFILE=""; \\
	       case "\$\${SHELL##*/}" in \\
	         zsh)  RCFILE="\$\$HOME/.zshrc" ;; \\
	         bash) RCFILE="\$\$HOME/.bashrc" ;; \\
	         fish) RCFILE="\$\$HOME/.config/fish/config.fish" ;; \\
	       esac; \\
	       if [ -n "\$\$RCFILE" ]; then \\
	         if ! grep -qF "\$\$IDIR" "\$\$RCFILE" 2>/dev/null; then \\
	           mkdir -p "\$\$(dirname "\$\$RCFILE")"; \\
	           case "\$\$RCFILE" in \\
	             */config.fish) printf '\nfish_add_path "%s"\n' "\$\$IDIR" >> "\$\$RCFILE" ;; \\
	             *) printf '\nexport PATH="%s:\$\$PATH"\n' "\$\$IDIR" >> "\$\$RCFILE" ;; \\
	           esac; \\
	           printf "\$(GREEN)Added\$(RESET)     \$\$IDIR to PATH in \$\$RCFILE\n"; \\
	           printf "\$(YELLOW)Restart\$(RESET)   your shell or run: source \$\$RCFILE\n"; \\
	         else \\
	           printf "\$(CYAN)Skipped\$(RESET)   \$\$IDIR already referenced in \$\$RCFILE\n"; \\
	         fi; \\
	       else \\
	         printf "\$(YELLOW)Warning\$(RESET)   \$\$IDIR is not on PATH -- add: export PATH=\"\$\$IDIR:\\$\$PATH\"\n"; \\
	       fi ;; \\
	  esac; \\
	fi; \\
	printf "\$(GREEN)Installed\$(RESET) \$\$IDIR/\$(SCRIPT).sh\n"; \\
	ln -sf "\$\$IDIR/\$(SCRIPT).sh" "\$\$IDIR/\$(SCRIPT)"; \\
	printf "\$(GREEN)Linked\$(RESET)    \$\$IDIR/\$(SCRIPT) -> \$(SCRIPT).sh\n"

.PHONY: uninstall
uninstall: ## Remove ${name} from /usr/local/bin and ~/.local/bin
	@for dir in /usr/local/bin "\$\$HOME/.local/bin"; do \\
	  for name in \$(SCRIPT).sh \$(SCRIPT); do \\
	    if [ -f "\$\$dir/\$\$name" ] || [ -L "\$\$dir/\$\$name" ]; then \\
	      if rm -f "\$\$dir/\$\$name" 2>/dev/null || sudo rm -f "\$\$dir/\$\$name"; then \\
	        printf "\$(GREEN)Removed\$(RESET)   \$\$dir/\$\$name\n"; \\
	      fi; \\
	    fi; \\
	  done; \\
	done

##@ Usage

.PHONY: usage
usage: ## Show ${name} usage
	@bash \$(SCRIPT).sh --help

##@ Skill distribution

.PHONY: sync-skill
sync-skill: ## Sync this repo into SKILLS_DIR (default: ~/Code/agent-skills-toolbox/skills/${name})
	@printf "\$(CYAN)Syncing to\$(RESET) \$(SKILLS_DIR)\n"
	@mkdir -p \$(SKILLS_DIR)
	@ok=0; fail=0; \\
	for f in \$(SKILL_FILES); do \\
		if /bin/cp -R \$\$f \$(SKILLS_DIR)/ 2>/dev/null; then \\
			printf "  \$(GREEN)ok\$(RESET)  \$\$f\n"; ok=\$\$((\$\$ok+1)); \\
		else \\
			printf "  \$(RED)FAIL\$(RESET)  \$\$f\n"; fail=\$\$((\$\$fail+1)); \\
		fi \\
	done; \\
	printf "\n  \$(BOLD)\$\$ok synced, \$\$fail failed\$(RESET) -> \$(SKILLS_DIR)\n"; \\
	[ \$\$fail -eq 0 ]
MAKEFILE
  success "Created $path"
}

write_makefile_docker() {
  local path="$1" name="$2" verarg
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"
  verarg="$(printf '%s' "$name" | tr 'a-z-' 'A-Z_')_VERSION"
  sed -e "s|@TOOL@|${name}|g" -e "s|@VERARG@|${verarg}|g" > "$path" <<'MAKEFILE_EOF'
# ============================================================
# @TOOL@ -- Makefile  (Docker image + @TOOL@ wrapper)
# ============================================================
.DEFAULT_GOAL := help
MAKEFLAGS     += --no-print-directory
SHELL         := /bin/bash

# -- Colors ---------------------------------------------------
BOLD   := \033[1m
GREEN  := \033[32m
CYAN   := \033[36m
RED    := \033[31m
YELLOW := \033[33m
RESET  := \033[0m

DEBUG  := false

# -- Paths ----------------------------------------------------
TOOL := @TOOL@

# -- Skill distribution ---------------------------------------
SKILL_NAME  := @TOOL@
SKILLS_DIR  ?= $(HOME)/Code/agent-skills-toolbox/skills/$(SKILL_NAME)
SKILL_FILES := $(TOOL) SKILL.md README.md

# -- Image & Build Config -------------------------------------
REGISTRY   ?= ghcr.io
IMAGE_REPO := rondomondo/@TOOL@
REMOTE     := $(REGISTRY)/$(IMAGE_REPO)
VERSION     = $(shell cat VERSION 2>/dev/null | tr -d '[:space:]')
PLATFORMS  := linux/amd64,linux/arm64
BUILDER    := @TOOL@-builder
NO_CACHE   ?= 0
CACHE_FLAG  = $(if $(filter 1,$(NO_CACHE)),--no-cache,)
RC_VERSION  = $(VERSION)-rc.1
# Pre-release versions (containing a hyphen) must never move :latest
LATEST_TAG  = $(if $(findstring -,$(VERSION)),,--tag $(REMOTE):latest)
IMAGE_SHELL ?= bash
DOCKER_EXTRA_ARGS ?= --env DEBUG=$(DEBUG) --env USE_SHELL=$(IMAGE_SHELL)

# -- Help -----------------------------------------------------
.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} \
	  /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0,5) } \
	  /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)

##@ Install

.PHONY: install
install: ## Install @TOOL@; tries /usr/local/bin (direct then sudo), falls back to ~/.local/bin
	@if install -m 755 $(TOOL) /usr/local/bin/$(TOOL) 2>/dev/null; then \
	  IDIR=/usr/local/bin; \
	elif sudo install -m 755 $(TOOL) /usr/local/bin/$(TOOL) 2>/dev/null; then \
	  IDIR=/usr/local/bin; \
	else \
	  mkdir -p "$$HOME/.local/bin"; \
	  install -m 755 $(TOOL) "$$HOME/.local/bin/$(TOOL)"; \
	  IDIR="$$HOME/.local/bin"; \
	  case ":$$PATH:" in \
	    *":$$IDIR:"*) ;; \
	    *) RCFILE=""; \
	       case "$${SHELL##*/}" in \
	         zsh)  RCFILE="$$HOME/.zshrc" ;; \
	         bash) RCFILE="$$HOME/.bashrc" ;; \
	         fish) RCFILE="$$HOME/.config/fish/config.fish" ;; \
	       esac; \
	       if [ -n "$$RCFILE" ]; then \
	         if ! grep -qF "$$IDIR" "$$RCFILE" 2>/dev/null; then \
	           mkdir -p "$$(dirname "$$RCFILE")"; \
	           case "$$RCFILE" in \
	             */config.fish) printf '\nfish_add_path "%s"\n' "$$IDIR" >> "$$RCFILE" ;; \
	             *) printf '\nexport PATH="%s:$$PATH"\n' "$$IDIR" >> "$$RCFILE" ;; \
	           esac; \
	           printf "$(GREEN)Added$(RESET)     $$IDIR to PATH in $$RCFILE\n"; \
	           printf "$(YELLOW)Restart$(RESET)   your shell or run: source $$RCFILE\n"; \
	         else \
	           printf "$(CYAN)Skipped$(RESET)   $$IDIR already referenced in $$RCFILE\n"; \
	         fi; \
	       else \
	         printf "$(YELLOW)Warning$(RESET)   $$IDIR is not on PATH -- add: export PATH=\"$$IDIR:\$$PATH\"\n"; \
	       fi ;; \
	  esac; \
	fi; \
	printf "$(GREEN)Installed$(RESET) $$IDIR/$(TOOL)\n"

.PHONY: uninstall
uninstall: ## Remove @TOOL@ from /usr/local/bin and ~/.local/bin
	@for dir in /usr/local/bin "$$HOME/.local/bin"; do \
	  if [ -f "$$dir/$(TOOL)" ] || [ -L "$$dir/$(TOOL)" ]; then \
	    if rm -f "$$dir/$(TOOL)" 2>/dev/null || sudo rm -f "$$dir/$(TOOL)"; then \
	      printf "$(GREEN)Removed$(RESET)   $$dir/$(TOOL)\n"; \
	    fi; \
	  fi; \
	done

##@ @TOOL@

.PHONY: usage
usage: ## Show @TOOL@ usage
	@bash $(TOOL)

##@ Build

.PHONY: build
build: bump ## Build single-arch image for local testing (loads into Docker daemon). NO_CACHE=1 to bust cache.
	docker build $(CACHE_FLAG) --build-arg @VERARG@=$(VERSION) -t $(REMOTE):$(VERSION) -t $(REMOTE):latest .
	@printf "$(GREEN)Built$(RESET) $(REMOTE):$(VERSION) and $(REMOTE):latest (local arch only)\n"

.PHONY: builder-init
builder-init: ## Create/reuse the multi-platform buildx builder
	@if ! docker buildx inspect $(BUILDER) >/dev/null 2>&1; then \
	  docker buildx create --name $(BUILDER) --driver docker-container --bootstrap; \
	  printf "$(GREEN)Created$(RESET) buildx builder: $(BUILDER)\n"; \
	else \
	  printf "$(CYAN)Reusing$(RESET) buildx builder: $(BUILDER)\n"; \
	fi

##@ Release

.PHONY: bump
bump: ## Increment patch version in VERSION file
	@old=$(VERSION); \
	new=$$(awk -F. '{printf "%d.%d.%d", $$1, $$2, $$3+1}' VERSION); \
	echo "$$new" > VERSION; \
	printf "$(GREEN)Bumped$(RESET) $$old -> $$new\n"

.PHONY: push
push: builder-init ## Build multi-platform image and push to ghcr.io (amd64 + arm64). NO_CACHE=1 to bust cache.
	docker buildx build \
	  --builder $(BUILDER) \
	  $(CACHE_FLAG) \
	  --build-arg @VERARG@=$(VERSION) \
	  --platform $(PLATFORMS) \
	  --tag $(REMOTE):$(VERSION) \
	  $(LATEST_TAG) \
	  --push \
	  .
	@printf "$(GREEN)Pushed$(RESET) $(REMOTE):$(VERSION) $(if $(LATEST_TAG),and $(REMOTE):latest )($(PLATFORMS))\n"

.PHONY: release
release: bump push ## Bump patch version, build multi-platform, and push to ghcr.io

.PHONY: release-rc
release-rc: ## One-off: push $(RC_VERSION) to ghcr.io without bumping VERSION or moving :latest
	$(MAKE) push VERSION=$(RC_VERSION)

.PHONY: retag
retag: ## Re-tag an existing remote image without pulling: make retag FROM=latest TAG=v0.1.1
	@if [ -z "$(FROM)" ] || [ -z "$(TAG)" ]; then \
	  printf "$(RED)Error: FROM and TAG are required. Usage: make retag FROM=latest TAG=v0.1.1$(RESET)\n"; \
	  exit 1; \
	fi
	docker buildx imagetools create -t $(REMOTE):$(TAG) $(REMOTE):$(FROM)
	@printf "$(GREEN)Retagged$(RESET) $(REMOTE):$(FROM) -> $(REMOTE):$(TAG)\n"

##@ Docker

.PHONY: docker-shell
docker-shell: ## Open an interactive bash shell in the container with $PWD mounted at /data
	docker run --rm -it \
	  --volume $(PWD):/data \
	  $(DOCKER_EXTRA_ARGS) \
	  $(REMOTE):latest

##@ Info

.PHONY: example
example: ## Print cut-and-paste usage examples
	@printf "\n$(BOLD)Install onto your host$(RESET)\n"
	@printf "  docker run --rm $(REMOTE):latest install | sh\n"
	@printf "  docker run --rm $(REMOTE):latest uninstall | sh\n"
	@printf "\n"

.PHONY: size
size: ## Show local image sizes
	@docker images $(REMOTE) --format "table {{.Tag}}\t{{.Size}}\t{{.ID}}" | head -10

.PHONY: version
version: ## Print current version
	@echo $(VERSION)

.PHONY: inspect
inspect: ## Show manifest platforms for the remote :latest image
	docker buildx imagetools inspect $(REMOTE):latest

##@ Skill distribution

.PHONY: sync-skill
sync-skill: ## Sync this repo into SKILLS_DIR
	@printf "$(CYAN)Syncing to$(RESET) $(SKILLS_DIR)\n"
	@mkdir -p $(SKILLS_DIR)
	@ok=0; fail=0; \
	for f in $(SKILL_FILES); do \
		if /bin/cp -R $$f $(SKILLS_DIR)/ 2>/dev/null; then \
			printf "  $(GREEN)ok$(RESET)  $$f\n"; ok=$$((ok+1)); \
		else \
			printf "  $(RED)FAIL$(RESET)  $$f\n"; fail=$$((fail+1)); \
		fi \
	done; \
	printf "\n  $(BOLD)$$ok synced, $$fail failed$(RESET) -> $(SKILLS_DIR)\n"; \
	[ $$fail -eq 0 ]

##@ Cleanup

.PHONY: clean
clean: ## Remove local image tags for this image
	@for tag in "$(REMOTE):$(VERSION)" "$(REMOTE):latest"; do \
	  if docker image inspect "$$tag" >/dev/null 2>&1; then \
	    docker rmi "$$tag" && printf "$(GREEN)Removed$(RESET) $$tag\n"; \
	  else \
	    printf "$(YELLOW)Not found$(RESET)  $$tag\n"; \
	  fi; \
	done

.PHONY: clean-builder
clean-builder: ## Remove the buildx builder instance
	@docker buildx rm $(BUILDER) 2>/dev/null && \
	  printf "$(GREEN)Removed$(RESET) builder: $(BUILDER)\n" || \
	  printf "$(YELLOW)Not found$(RESET)  builder: $(BUILDER)\n"

.PHONY: clean-all
clean-all: clean clean-builder ## Run all clean targets
MAKEFILE_EOF
  printf '0.1.0\n' > "$(dirname "$path")/VERSION"
  success "Created $path"
}

write_skill_md() {
  local path="$1" name="$2" desc="$3" type="$4"
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"

  if [[ "$type" == "docker" ]]; then
    local install_block="    cp \"\$SKILL_DIR/${name}\" /usr/local/bin/${name}
    chmod +x /usr/local/bin/${name}"
    local install_local="cd ~/Code/toolbox/${name} && make install"
    local tool_check="which ${name}
docker info >/dev/null 2>&1 || echo \"ERROR: Docker is not running\""
  else
    local install_block="    cp \"\$SKILL_DIR/${name}.sh\" /usr/local/bin/${name}.sh
    chmod +x /usr/local/bin/${name}.sh
    ln -sf /usr/local/bin/${name}.sh /usr/local/bin/${name}"
    local install_local="cd ~/Code/toolbox && make -C scripts install"
    local tool_check="which ${name}"
  fi

  cat > "$path" <<SKILLMD
---
name: ${name}
description: >
    ${desc}
    Trigger on "${name}" or any request related to this tool.
---

# ${name} Skill

You are using \`${name}\` to TODO: describe what the tool does.

---

## When to use this skill

- TODO: list trigger conditions

---

## Quickstart

\`\`\`bash
# TODO: add quickstart examples
${name} --help
\`\`\`

---

## Step 0 - Resolve environment and install tool

\`\`\`bash
if [ "\${IS_SANDBOX:-no}" = "yes" ] || [ "\${IS_SANDBOX:-no}" = "1" ] || [ "\${IS_SANDBOX:-no}" = "true" ]; then
    SKILL_DIR="/mnt/skills/user/${name}"
${install_block}
else
    command -v ${name} >/dev/null 2>&1 || {
        echo "ERROR: ${name} not installed. Run: ${install_local}" >&2
        exit 1
    }
fi
\`\`\`

## Step 1 - Check for the tool

\`\`\`bash
${tool_check}
\`\`\`

If missing locally:

\`\`\`bash
${install_local}
\`\`\`

---

## Step 2 - TODO

TODO: describe inputs and usage steps.

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |

---

## Error handling

| Symptom | Likely cause | Fix |
|---|---|---|
| \`${name} not found\` | Not installed | Run \`make install\` from \`toolbox/${name}/\` |
SKILLMD
  success "Created $path"
}

write_readme() {
  local path="$1" name="$2" desc="$3" type="$4"
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"

  if [[ "$type" == "docker" ]]; then
    local req_extra="- Docker (running locally)"$'\n'
    local script_file="$name"
    local sync_files="\`${name}\`, \`SKILL.md\`, and \`README.md\`"
  else
    local req_extra=""
    local script_file="${name}.sh"
    local sync_files="\`${name}.sh\`, \`SKILL.md\`, and \`README.md\`"
  fi

  cat > "$path" <<README
# ${name}

**${desc}**

> **Also available as an [Agent Skill](#claude-code-skill)** -- install it to use \`${name}\` directly from Claude Code with no terminal required. Use the \`/${name}\` slash command or just describe what you want and your AI Agent will handle it.

---

## Quick Start

\`\`\`bash
# TODO: add quickstart examples
${name} --help
\`\`\`

---

## Installation

\`\`\`bash
# 1. Clone the toolbox repo
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/${name}

# 2. Install ${name}
make install
\`\`\`

### Uninstall

\`\`\`bash
make uninstall
\`\`\`

---

## Usage

\`\`\`
${name}              Show help
${name} -h | --help  Show help
\`\`\`

---

## How it works

| File | Role |
|---|---|
| \`${script_file}\` | Main script. TODO: describe. |
| \`Makefile\` | Developer workflow: install/uninstall/sync-skill. |

---

## Makefile targets

\`\`\`
make help         Show all targets
make install      Install ${name} to /usr/local/bin
make uninstall    Remove ${name} from /usr/local/bin
make usage        Show ${name} usage
make sync-skill   Sync skill files to ~/Code/agent-skills-toolbox/skills/${name}
\`\`\`

---

## Claude Code skill

<details>
<summary>Install the <code>/${name}</code> slash command for Claude Code</summary>

This repository ships a \`/${name}\` slash command skill for [Claude Code](https://claude.ai/code)
that lets Claude use \`${name}\` -- no terminal required. Just describe what you want and
Claude will invoke the skill automatically.

### Invoking the skill

Use the slash command directly:

\`\`\`
/${name} --help
\`\`\`

Or just describe what you want in natural language -- Claude will invoke the skill automatically:

> *"TODO: add example natural language prompts"*

### Installing the skill

#### Option A -- sync locally via \`make\`

\`\`\`bash
# from inside the ${name} directory
make sync-skill
\`\`\`

This syncs ${sync_files} to:

\`\`\`
~/Code/agent-skills-toolbox/skills/${name}/
\`\`\`

Override the target directory with \`SKILLS_DIR\`:

\`\`\`bash
make sync-skill SKILLS_DIR=/path/to/your/project/.claude/skills/${name}
\`\`\`

#### Option B -- copy manually

\`\`\`bash
mkdir -p .claude/skills/${name}
cp ${script_file} SKILL.md README.md .claude/skills/${name}/
\`\`\`

</details>

---

## Requirements

${req_extra}- \`bash\` 4+
- \`make\` (for Makefile targets)
README
  success "Created $path"
}

write_script_stub() {
  local path="$1" name="$2"
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"
  cat > "$path" <<'STUB'
#!/usr/bin/env bash
# =============================================================================
# TOOL_NAME.sh
#
# TODO: describe what this script does
#
# Usage:
#   TOOL_NAME [OPTIONS]
#
# Options:
#   -h, --help    Show this help
#
# Requirements: bash 3.2+
# =============================================================================

set -euo pipefail

# -- colour helpers ------------------------------------------------------------
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()  { printf "${CYAN}[TOOL_NAME]${RESET}  %s\n" "$*"; }
ok()    { printf "${GREEN}[TOOL_NAME]${RESET}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[TOOL_NAME]${RESET}  %s\n" "$*"; }
die()   { printf "${RED}[TOOL_NAME]${RESET}  ERROR: %s\n" "$*" >&2; exit 1; }

# -- usage ---------------------------------------------------------------------
usage() {
  sed -n '3,12p' "$0" | sed 's/^# \{0,2\}//'
  exit 0
}

# -- main ----------------------------------------------------------------------
main() {
  case "${1:-}" in
    -h|--help) usage ;;
  esac

  # TODO: implement
  die "Not yet implemented"
}

main "$@"
STUB
  # Replace TOOL_NAME placeholder with actual name
  sed -i.bak "s/TOOL_NAME/${name}/g" "$path" && rm -f "${path}.bak"
  chmod +x "$path"
  success "Created $path"
}

write_docker_wrapper_stub() {
  local path="$1" name="$2"
  local upper
  upper="$(printf '%s' "$name" | tr 'a-z-' 'A-Z_')"
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"
  cat > "$path" <<STUB
#!/usr/bin/env bash
# =============================================================================
# ${name}
#
# Wrapper script for the ghcr.io/rondomondo/${name} Docker image.
# TODO: describe what this tool does.
#
# Usage:
#   ${name} [OPTIONS] [ARGS...]
#   ${name} -- [args...]     Pass args directly to the container entrypoint
#
# Requirements: Docker (running locally), bash 3.2+
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

USE_LOGGING="\${DEBUG:-false}"
case "\${USE_LOGGING}" in
  true|1)  USE_LOGGING=true  ;;
  false|0) USE_LOGGING=false ;;
  *) printf "ERROR: DEBUG must be true/false/1/0, got '%s'\n" "\${USE_LOGGING}" >&2; exit 1 ;;
esac
SCRIPT_NAME=\$(basename "\$0")

log()  { \${USE_LOGGING} && printf "\${BOLD}[\$SCRIPT_NAME]\${RESET} \${CYAN}%s\${RESET}\n"   "\$*" >&2; return 0; }
ok()   { \${USE_LOGGING} && printf "\${BOLD}[\$SCRIPT_NAME]\${RESET} \${GREEN}%s\${RESET}\n"  "\$*" >&2; return 0; }
warn() { \${USE_LOGGING} && printf "\${BOLD}[\$SCRIPT_NAME]\${RESET} \${YELLOW}%s\${RESET}\n" "\$*" >&2; return 0; }

IMAGE="\${${upper}_IMAGE:-ghcr.io/rondomondo/${name}:latest}"

if ! command -v docker &>/dev/null; then
  printf "\${RED}Error:\${RESET} docker is required but not found in PATH\n" >&2
  exit 1
fi

usage() {
  printf "\n\${BOLD}${name}\${RESET} -- TODO: one-line description\n\n"
  printf "Usage:\n"
  printf "  ${name} [OPTIONS]        TODO: describe\n"
  printf "  ${name} -- [args...]     Pass args directly to the container\n\n"
  printf "Environment variables:\n"
  printf "  DEBUG=true/1            Enable verbose logging\n"
  printf "  ${upper}_IMAGE=<ref>  Override Docker image (default: \$IMAGE)\n\n"
  exit 0
}

case "\${1:-}" in
  -h|--help|"") usage ;;
esac

log "invoked with args '\$*'"

# TODO: implement input handling and docker run invocation
printf "\${RED}Error:\${RESET} Not yet implemented\n" >&2
exit 1
STUB
  chmod +x "$path"
  success "Created $path"
}

write_dockerfile_stub() {
  local path="$1" name="$2" verarg
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"
  verarg="$(printf '%s' "$name" | tr 'a-z-' 'A-Z_')_VERSION"
  sed -e "s|@TOOL@|${name}|g" -e "s|@VERARG@|${verarg}|g" > "$path" <<'DOCKERFILE'
# ============================================================
# @TOOL@ -- Dockerfile
# ============================================================
FROM debian:bookworm-slim

# TODO: replace base image and install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=root:root entrypoint.sh /entrypoint.sh
COPY --chown=root:root install.sh    /install.sh
COPY --chown=root:root uninstall.sh  /uninstall.sh
COPY --chown=root:root @TOOL@        /usr/local/bin/@TOOL@
RUN chmod +x /entrypoint.sh /install.sh /uninstall.sh /usr/local/bin/@TOOL@

# Bake the image version into the wrapper so installed copies default to this tag.
ARG @VERARG@
RUN if [ -n "$@VERARG@" ]; then \
      sed "s|rondomondo/@TOOL@:latest|rondomondo/@TOOL@:$@VERARG@|g" /usr/local/bin/@TOOL@ > /tmp/wrapper.pinned \
      && cat /tmp/wrapper.pinned > /usr/local/bin/@TOOL@ && rm -f /tmp/wrapper.pinned; \
    fi

WORKDIR /data
ENTRYPOINT ["/entrypoint.sh"]
DOCKERFILE
  success "Created $path"
}

write_entrypoint_stub() {
  local path="$1"
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"
  cat > "$path" <<'ENTRY'
#!/usr/bin/env bash
set -euo pipefail

# install / uninstall emit a streaming sh script: docker run ... install | sh
if [ $# -gt 0 ] && [ "$1" = "install" ]; then
  shift
  exec /install.sh "$@"
fi

if [ $# -gt 0 ] && [ "$1" = "uninstall" ]; then
  shift
  exec /uninstall.sh "$@"
fi

# TODO: implement entrypoint logic
exec "$@"
ENTRY
  chmod +x "$path"
  success "Created $path"
}

write_install_sh_stub() {
  local path="$1" name="$2"
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"
  sed -e "s|@TOOL@|${name}|g" -e "s|@IMAGE@|${name}|g" > "$path" <<'SCRIPT_EOF'
#!/bin/bash
set -euo pipefail

BOLD='\033[1m'
CYAN='\033[0;36m'
RESET='\033[0m'

TOOL="@TOOL@"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-ghcr.io}"
IMAGE_REPO="${IMAGE_REPO:-rondomondo/@IMAGE@}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE="${IMAGE_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}"

TOOL_SRC="/usr/local/bin/${TOOL}"

examples() {
    printf "\n"
    printf "${BOLD}${CYAN}Install %s${RESET}\n" "$TOOL"
    printf "\n"
    printf "Run the following to install %s on this host:\n" "$TOOL"
    printf "\n"
    printf "  ${BOLD}docker run --rm %s install | sh${RESET}\n" "$IMAGE"
    printf "\n"
    printf "This installs:\n"
    printf "  ${BOLD}%s${RESET} -> /usr/local/bin/%s (or ~/.local/bin/%s)\n" "$TOOL" "$TOOL" "$TOOL"
    printf "\n"
    printf "To remove it again:\n"
    printf "\n"
    printf "  ${BOLD}docker run --rm %s uninstall | sh${RESET}\n" "$IMAGE"
    printf "\n"
    printf "Pass DEBUG=1 to trace the docker command: ${BOLD}DEBUG=1 %s ...${RESET}\n" "$TOOL"
    printf "\n"
}

# Streaming install: docker run ... install | sh
# Emits a self-contained sh script that installs the wrapper on the host.
if [[ ! -t 1 ]]; then
    [ -f "$TOOL_SRC" ] || { printf "install.sh: missing asset: %s\n" "$TOOL_SRC" >&2; exit 1; }

    cat <<'HEADER'
#!/bin/sh
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

ok()   { printf "${GREEN}ok${RESET}    %s\n" "$1"; }
warn() { printf "${YELLOW}warn${RESET}  %s\n" "$1"; }
info() { printf "${CYAN}info${RESET}  %s\n" "$1"; }

add_to_path_if_needed() {
    local dir="$1"
    local rcfile

    case ":$PATH:" in
        *":$dir:"*) return 0 ;;
    esac

    case "${SHELL##*/}" in
        zsh)  rcfile="$HOME/.zshrc" ;;
        bash) rcfile="$HOME/.bashrc" ;;
        fish) rcfile="$HOME/.config/fish/config.fish" ;;
        *)    rcfile="" ;;
    esac

    if [ -n "$rcfile" ]; then
        if ! grep -qF "$dir" "$rcfile" 2>/dev/null; then
            mkdir -p "$(dirname "$rcfile")"
            case "$rcfile" in
                */config.fish) printf '\nfish_add_path "%s"\n' "$dir" >> "$rcfile" ;;
                *)             printf '\nexport PATH="%s:$PATH"\n' "$dir" >> "$rcfile" ;;
            esac
            ok "added $dir to PATH in $rcfile"
            warn "restart your shell or run: source $rcfile"
        else
            info "$dir already referenced in $rcfile -- skipping"
        fi
    else
        warn "$dir is not on PATH -- add: export PATH=\"$dir:\$PATH\""
    fi
}

# Prefer /usr/local/bin (direct, then sudo), fall back to ~/.local/bin.
try_install() {
    USE_SUDO=0

    if install -m 755 /dev/null /usr/local/bin/.install_probe 2>/dev/null; then
        rm -f /usr/local/bin/.install_probe
        bin_dir=/usr/local/bin
    elif sudo install -m 755 /dev/null /usr/local/bin/.install_probe 2>/dev/null; then
        sudo rm -f /usr/local/bin/.install_probe
        bin_dir=/usr/local/bin
        USE_SUDO=1
    else
        bin_dir="$HOME/.local/bin"
        mkdir -p "$bin_dir"
        add_to_path_if_needed "$bin_dir"
    fi

    if [ "$USE_SUDO" = "1" ]; then
        sudo install -m 755 "$tmp_asset" "$bin_dir/$TOOL"
    else
        install -m 755 "$tmp_asset" "$bin_dir/$TOOL"
    fi
    ok "$bin_dir/$TOOL"
}

HEADER

    printf 'TOOL="%s"\n' "$TOOL"
    printf 'IMAGE="%s"\n' "$IMAGE"
    echo 'tmp_asset=$(mktemp)'
    echo 'trap '"'"'rm -f "$tmp_asset"'"'"' EXIT'
    printf '\nprintf "\\n${BOLD}Installing %%s...${RESET}\\n" "$TOOL"\n'
    echo "cat > \"\$tmp_asset\" << 'TOOL_ASSET_EOF'"
    cat "$TOOL_SRC"
    echo "TOOL_ASSET_EOF"
    echo "try_install"
    echo
    cat <<'FOOTER'
command -v docker >/dev/null 2>&1 || warn "docker was not found on PATH -- $TOOL needs it at run time"

printf '\n%bDone.%b\n\n' "$BOLD" "$RESET"
printf 'Installed %b%s%b -> %s/%s\n' "$BOLD" "$TOOL" "$RESET" "$bin_dir" "$TOOL"
printf 'Run %b%s --help%b to get started.\n' "$CYAN" "$TOOL" "$RESET"
printf 'Pass DEBUG=1 to trace the docker command: DEBUG=1 %s ...\n\n' "$TOOL"
printf 'To remove it: docker run --rm %s uninstall | sh\n\n' "$IMAGE"
FOOTER

    exit 0
fi

# Interactive: print usage instructions
examples
SCRIPT_EOF
  chmod +x "$path"
  success "Created $path"
}

write_uninstall_sh_stub() {
  local path="$1" name="$2"
  if $DRY_RUN; then dry "Would write: $path"; return; fi
  mkdir -p "$(dirname "$path")"
  sed -e "s|@TOOL@|${name}|g" -e "s|@IMAGE@|${name}|g" > "$path" <<'SCRIPT_EOF'
#!/bin/bash
set -euo pipefail

BOLD='\033[1m'
CYAN='\033[0;36m'
RESET='\033[0m'

TOOL="@TOOL@"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-ghcr.io}"
IMAGE_REPO="${IMAGE_REPO:-rondomondo/@IMAGE@}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE="${IMAGE_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}"

# Streaming uninstall: docker run ... uninstall | sh
# Emits a self-contained sh script that removes the wrapper from the host.
if [[ ! -t 1 ]]; then
    cat <<'HEADER'
#!/bin/sh
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

ok()   { printf "${GREEN}ok${RESET}    %s\n" "$1"; }
warn() { printf "${YELLOW}warn${RESET}  %s\n" "$1"; }
info() { printf "${CYAN}info${RESET}  %s\n" "$1"; }

try_remove_bin() {
    local name="$1"
    local removed=0
    local dir target
    for dir in /usr/local/bin "$HOME/.local/bin"; do
        target="$dir/$name"
        [ -f "$target" ] || [ -L "$target" ] || continue
        if rm -f "$target" 2>/dev/null; then
            ok "removed $target"
            removed=1
        elif sudo rm -f "$target" 2>/dev/null; then
            ok "removed $target (via sudo)"
            removed=1
        else
            warn "could not remove $target (permission denied)"
        fi
    done
    [ "$removed" -eq 0 ] && info "$name not found in /usr/local/bin or ~/.local/bin -- nothing to remove" || true
}

HEADER

    printf 'TOOL="%s"\n' "$TOOL"
    printf 'printf "\\n${BOLD}Uninstalling %%s...${RESET}\\n" "$TOOL"\n'
    echo 'try_remove_bin "$TOOL"'
    echo
    cat <<'FOOTER'
printf '\n%bDone.%b\n\n' "$BOLD" "$RESET"
FOOTER

    exit 0
fi

# Interactive: print usage instructions
printf "\n"
printf "${BOLD}${CYAN}Uninstall %s${RESET}\n" "$TOOL"
printf "\n"
printf "Run the following to remove %s from this host:\n" "$TOOL"
printf "\n"
printf "  ${BOLD}docker run --rm %s uninstall | sh${RESET}\n" "$IMAGE"
printf "\n"
printf "This removes ${BOLD}%s${RESET} from /usr/local/bin or ~/.local/bin\n" "$TOOL"
printf "\n"
SCRIPT_EOF
  chmod +x "$path"
  success "Created $path"
}

# -- mirror to skills dir ------------------------------------------------------
mirror_to_skills() {
  local toolbox_dir="$1" skills_dir="$2" name="$3" type="$4"
  if $DRY_RUN; then
    dry "Would mirror Makefile SKILL.md README.md + main script -> $skills_dir"
    return
  fi
  mkdir -p "$skills_dir"
  cp "$toolbox_dir/Makefile"  "$skills_dir/"
  cp "$toolbox_dir/SKILL.md"  "$skills_dir/"
  cp "$toolbox_dir/README.md" "$skills_dir/"
  if [[ "$type" == "script" ]]; then
    cp "$toolbox_dir/${name}.sh" "$skills_dir/"
  else
    cp "$toolbox_dir/${name}" "$skills_dir/"
  fi
  success "Mirrored files to $skills_dir"
}

# -- patch root Makefile -------------------------------------------------------
patch_root_makefile() {
  local root_makefile="$TOOLBOX_ROOT/Makefile" type="$1" name="$2"
  [[ -f "$root_makefile" ]] || { warn "Root Makefile not found at $root_makefile -- skipping patch"; return; }

  local var
  [[ "$type" == "script" ]] && var="SCRIPT_TOOLS" || var="DOCKER_TOOLS"

  if grep -q "\b${name}\b" "$root_makefile"; then
    info "'$name' already present in root Makefile $var line -- no patch needed"
    return
  fi

  if $DRY_RUN; then
    dry "Would patch $root_makefile: append '$name' to $var"
    return
  fi

  sed -i.bak "s/^\(${var}\s*:=.*\)$/\1 ${name}/" "$root_makefile"
  rm -f "${root_makefile}.bak"
  success "Patched $root_makefile: added '$name' to $var"
}

# -- main ----------------------------------------------------------------------
main() {
  parse_args "$@"

  local toolbox_dir="$TOOLBOX_ROOT/$TOOL_NAME"
  local skills_dir="$SKILLS_ROOT/$TOOL_NAME"

  printf "\n${BOLD}scaffold-tool${RESET}  %s  [type: %s]\n" "$TOOL_NAME" "$TOOL_TYPE"
  printf "%s\n\n" "$(printf '%0.s-' {1..50})"
  info "Toolbox dir : $toolbox_dir"
  info "Skills dir  : $skills_dir"
  info "Description : $TOOL_DESC"
  printf "\n"

  if [[ -d "$toolbox_dir" ]] && ! $DRY_RUN; then
    die "Directory already exists: $toolbox_dir\nRemove it first if you want to re-scaffold."
  fi

  # -- Makefile
  if [[ "$TOOL_TYPE" == "script" ]]; then
    write_makefile_script "$toolbox_dir/Makefile" "$TOOL_NAME"
  else
    write_makefile_docker "$toolbox_dir/Makefile" "$TOOL_NAME"
  fi

  # -- SKILL.md
  write_skill_md "$toolbox_dir/SKILL.md" "$TOOL_NAME" "$TOOL_DESC" "$TOOL_TYPE"

  # -- README.md
  write_readme "$toolbox_dir/README.md" "$TOOL_NAME" "$TOOL_DESC" "$TOOL_TYPE"

  # -- main script stub
  if [[ "$TOOL_TYPE" == "script" ]]; then
    write_script_stub "$toolbox_dir/${TOOL_NAME}.sh" "$TOOL_NAME"
  else
    write_docker_wrapper_stub "$toolbox_dir/${TOOL_NAME}" "$TOOL_NAME"
    write_dockerfile_stub     "$toolbox_dir/Dockerfile"   "$TOOL_NAME"
    write_entrypoint_stub     "$toolbox_dir/entrypoint.sh"
    write_install_sh_stub     "$toolbox_dir/install.sh"   "$TOOL_NAME"
    write_uninstall_sh_stub   "$toolbox_dir/uninstall.sh" "$TOOL_NAME"
  fi

  # -- mirror to agent-skills-toolbox
  mirror_to_skills "$toolbox_dir" "$skills_dir" "$TOOL_NAME" "$TOOL_TYPE"

  # -- patch root Makefile
  $NO_MAKEFILE_PATCH || patch_root_makefile "$TOOL_TYPE" "$TOOL_NAME"

  # -- summary
  printf "\n${GREEN}${BOLD}Done!${RESET}  Scaffolded '${TOOL_NAME}' (%s-type)\n\n" "$TOOL_TYPE"
  printf "Next steps:\n"
  if [[ "$TOOL_TYPE" == "script" ]]; then
    printf "  1. Edit ${CYAN}toolbox/${TOOL_NAME}/${TOOL_NAME}.sh${RESET}  -- implement the tool\n"
  else
    printf "  1. Edit ${CYAN}toolbox/${TOOL_NAME}/${TOOL_NAME}${RESET}     -- implement the wrapper\n"
    printf "     Edit ${CYAN}toolbox/${TOOL_NAME}/Dockerfile${RESET}       -- build the container\n"
  fi
  printf "  2. Edit ${CYAN}toolbox/${TOOL_NAME}/SKILL.md${RESET}           -- fill in agent instructions\n"
  printf "  3. Edit ${CYAN}toolbox/${TOOL_NAME}/README.md${RESET}          -- fill in user documentation\n"
  printf "\n  Run ${CYAN}make sync-skill${RESET} (from toolbox/${TOOL_NAME}/) after editing to re-sync.\n\n"
}

main "$@"
