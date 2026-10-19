# Root Makefile - Modular Delegation

BOLD   := \033[1m
RED    := \033[31m
GREEN  := \033[32m
CYAN   := \033[36m
YELLOW := \033[33m
RESET  := \033[0m

# Configuration
MAKEFLAGS         += --no-print-directory

PROJECT := agent-skills-toolbox
DEST    ?= $(HOME)
SRC     ?= $(CURDIR)/skills
LOCAL_DEST ?= .claude

.DEFAULT_GOAL := help

.PHONY: help
help: ## Display this help message
	@printf "\nUsage: make $(CYAN)<target>$(RESET)\n"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

# Skill Delegation

##@ Skill Delegation

.PHONY: skill
skill: ## Run a target in a specific skill (Usage: make skill name=inspect-sandbox target=help)
	@if [ -z "$(name)" ]; then echo "Error: name=... is required"; exit 1; fi
	@if [ ! -f "skills/$(name)/Makefile" ]; then echo "Error: skills/$(name)/Makefile not found"; exit 1; fi
	$(MAKE) -C skills/$(name) $(target)

# Common Management & Installation

##@ Common Management & Installation

.PHONY: plugins
plugins: ## List all plugin configurations thus far
	@ls -1 .claude-plugin/*.json 2>/dev/null || echo "No plugins found."

.PHONY: marketplaces
marketplaces: ## View marketplace configuration
	@cat .claude-plugin/marketplace.json 2>/dev/null || echo "Marketplace config not found."

.PHONY: skill-install
skill-install: ## Install a skill (Usage: make skill-install name=qr [SRC=./skills] [LOCAL_DEST=.claude] [DEST=~])
	@if [ -z "$(name)" ]; then echo "Error: name=... is required"; exit 1; fi
	@if [ ! -d "$(SRC)/$(name)" ]; then echo "Error: $(SRC)/$(name) not found"; exit 1; fi
	@mkdir -p $(DEST)/$(LOCAL_DEST)/skills/$(name)
	@cp -aR $(SRC)/$(name)/* $(DEST)/$(LOCAL_DEST)/skills/$(name)/
	@printf "$(GREEN)Installed $(SRC)/$(name) -> $(DEST)/$(LOCAL_DEST)/skills/$(name)$(RESET)\n"

.PHONY: skill-install-local
skill-install-local: ## Install a skill locally (Usage: make skill-install-local name=qr [SRC=./skills] [LOCAL_DEST=.claude])
	@if [ -z "$(name)" ]; then echo "Error: name=... is required"; exit 1; fi
	@if [ ! -d "$(SRC)/$(name)" ]; then echo "Error: $(SRC)/$(name) not found"; exit 1; fi
	@mkdir -p $(LOCAL_DEST)/skills/$(name)
	@cp -aR $(SRC)/$(name)/* $(LOCAL_DEST)/skills/$(name)/
	@printf "$(GREEN)Installed $(SRC)/$(name) -> $(LOCAL_DEST)/skills/$(name)$(RESET)\n"

.PHONY: install-all-skills
install-all-skills: ## Install all skills (Usage: make install-all-skills [SRC=./skills] [LOCAL_DEST=.claude])
	@for d in $$(find $(SRC) -mindepth 1 -maxdepth 1 -type d -not -name 'zipped'); do \
		skill_name=$$(basename $$d); \
		$(MAKE) skill-install-local name=$$skill_name SRC=$(SRC) LOCAL_DEST=$(LOCAL_DEST); \
	done

.PHONY: skill-zip
skill-zip: ## Zip a skill dir into a zip file (Usage: make skill-zip src=./skills/qr dst=./skills/qr/qr.zip)
	@if [ -z "$(src)" ]; then echo "Error: src=... is required"; exit 1; fi
	@if [ -z "$(dst)" ]; then echo "Error: dst=... is required"; exit 1; fi
	@src_abs=$$(cd "$(src)" && pwd); \
	dst_abs=$$(cd "$$(dirname "$(dst)")" && pwd)/$$(basename "$(dst)"); \
	stage_dir=$$(mktemp -d); \
	trap "rm -rf $$stage_dir" EXIT; \
	if grep -q '^zip-prep:' "$$src_abs/Makefile" 2>/dev/null; then \
		printf "$(CYAN)Running zip-prep$(RESET) in $$src_abs\n"; \
		$(MAKE) -C "$$src_abs" zip-prep STAGE_DIR="$$stage_dir"; \
	else \
		cp -aR "$$src_abs/." "$$stage_dir/"; \
	fi; \
	dst_dir=$$(dirname "$$dst_abs"); \
	mkdir -p "$$dst_dir"; \
	cd "$$stage_dir" && zip -r "$$dst_abs" . \
		--exclude "*.zip" \
		--exclude ".DS_Store" \
		--exclude "__pycache__/*" \
		--exclude "*.pyc"
	@printf "$(GREEN)Written$(RESET) $(dst)\n"

# Plugin Generation

##@ Plugin Management

# Overridable metadata
PLUGIN_NAME        ?= $(PROJECT)
PLUGIN_DESCRIPTION ?= Practical Claude Code skills for SRE and AI coding workflows: inspect sandboxes, render Mermaid diagrams, generate QR codes, strip PDF metadata, sanitise non-ASCII text, record terminal sessions to GIF (asciinema, cast2gif, vhs), print file trees, reset git history, and maintain the toolbox itself.
PLUGIN_VERSION     ?= 0.2.0
PLUGIN_AUTHOR      ?= $(shell git config user.name 2>/dev/null || echo "Unknown")
PLUGIN_REPO        ?= $(shell git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/\.git$$//' || echo "")
PLUGIN_LICENSE     ?= MIT
PLUGIN_OUT         ?= .claude-plugin

.PHONY: plugin-generate
plugin-generate: ## Generate .claude-plugin/plugin.json and marketplace.json by auto-discovering skills/agents/hooks
	@printf "$(CYAN)Discovering skills, agents, hooks...$(RESET)\n"
	@python3 scripts/plugin_generate.py \
		"$(PLUGIN_NAME)" \
		"$(PLUGIN_DESCRIPTION)" \
		"$(PLUGIN_VERSION)" \
		"$(PLUGIN_AUTHOR)" \
		"$(PLUGIN_REPO)" \
		"$(PLUGIN_LICENSE)" \
		"$(PLUGIN_OUT)"
	@printf "$(BOLD)Done.$(RESET) Override: make plugin-generate PLUGIN_NAME=x PLUGIN_DESCRIPTION='...' PLUGIN_REPO=org/repo\n"

.PHONY: plugin-show
plugin-show: ## Print current plugin.json and marketplace.json
	@printf "$(CYAN)-- plugin.json --$(RESET)\n"
	@cat $(PLUGIN_OUT)/plugin.json 2>/dev/null || echo "(not generated yet)"
	@printf "$(CYAN)-- marketplace.json --$(RESET)\n"
	@cat $(PLUGIN_OUT)/marketplace.json 2>/dev/null || echo "(not generated yet)"

# Sanity Checks

.PHONY: ok
ok: ## Run sanity checks: verify each skill has a Makefile and SKILL.md
	@printf "$(CYAN)Checking skills...$(RESET)\n"
	@errors=0; \
	for d in $$(find skills -mindepth 1 -maxdepth 1 -type d -not -name 'zipped'); do \
		skill_name=$$(basename $$d); \
		ok=1; \
		if [ ! -f "$$d/Makefile" ]; then \
			printf "$(RED)MISSING$(RESET)  $$skill_name/Makefile\n"; \
			ok=0; errors=1; \
		fi; \
		if [ ! -f "$$d/SKILL.md" ]; then \
			printf "$(RED)MISSING$(RESET)  $$skill_name/SKILL.md\n"; \
			ok=0; errors=1; \
		fi; \
		if [ "$$ok" = "1" ]; then \
			printf "$(GREEN)OK$(RESET)       $$skill_name\n"; \
		fi; \
	done; \
	if [ "$$errors" = "0" ]; then \
		printf "$(GREEN)All skills OK.$(RESET)\n"; \
	else \
		printf "$(RED)Some checks failed.$(RESET)\n"; exit 1; \
	fi

