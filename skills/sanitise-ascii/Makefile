# sanitise-ascii Skill Makefile
# Self-contained: works standalone or as part of agent-skills-toolbox.
.DEFAULT_GOAL := help
MAKEFLAGS     += --no-print-directory
SHELL         := /bin/bash

# -- Colors ---------------------------------------------------
BOLD   := \033[1m
RED    := \033[31m
GREEN  := \033[32m
CYAN   := \033[36m
YELLOW := \033[33m
RESET  := \033[0m

# -- Paths ----------------------------------------------------
PYTHON            := python3
SANITISE          := sanitise-ascii
SANITISE_SCRIPT   := sanitise-ascii.py
DESTDIR           := /usr/local/bin
SRCDIR            ?= .

.PHONY: help
help: ## Display this help message
	@printf "\nUsage: make $(CYAN)<target>$(RESET)\n"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Install

.PHONY: install
install: ## Install sanitise-ascii to $(DESTDIR) (system-wide)
	@install -m 755 $(SANITISE_SCRIPT) $(DESTDIR)/$(SANITISE).py
	@ln -sf $(DESTDIR)/$(SANITISE).py $(DESTDIR)/$(SANITISE)
	@printf "$(GREEN)Installed$(RESET) $(DESTDIR)/$(SANITISE)\n"

.PHONY: uninstall
uninstall: ## Remove sanitise-ascii from $(DESTDIR)
	@rm -f $(DESTDIR)/$(SANITISE) $(DESTDIR)/$(SANITISE).py
	@printf "$(GREEN)Removed$(RESET) $(DESTDIR)/$(SANITISE)\n"

##@ Sanitise

.PHONY: check
check: ## Check all text files under SRCDIR for non-ASCII (no writes)
	@printf "$(CYAN)[check]$(RESET) Scanning files under $(SRCDIR)...\n"
	@$(PYTHON) $(SANITISE_SCRIPT) --check --dir $(SRCDIR) && \
		printf "$(GREEN)[check]$(RESET) All files are ASCII-clean\n"

.PHONY: fix
fix: ## Fix known non-ASCII characters in all text files under SRCDIR
	@printf "$(CYAN)[fix]$(RESET) Sanitising files under $(SRCDIR)...\n"
	@$(PYTHON) $(SANITISE_SCRIPT) --fix --dir $(SRCDIR)
	@printf "$(GREEN)[fix]$(RESET) Done\n"

.PHONY: fix-file
fix-file: ## Fix a single file: make fix-file FILE=path/to/file.md
	@if [ -z "$(FILE)" ]; then printf "$(RED)ERROR:$(RESET) FILE is required. Usage: make fix-file FILE=path/to/file.md\n"; exit 1; fi
	@$(PYTHON) $(SANITISE_SCRIPT) $(FILE)
	@printf "$(GREEN)[fix-file]$(RESET) Done -> $(FILE)\n"

##@ Git hooks

.PHONY: install-hook
install-hook: ## Install pre-commit hook into current repo (.git/hooks/)
	@printf "$(CYAN)[install-hook]$(RESET) Installing hook...\n"
	@if [ ! -d .git ]; then printf "$(RED)ERROR:$(RESET) not in a git repo root (no .git dir found)\n"; exit 1; fi
	@cp .githooks/pre-commit-sanitise-ascii .git/hooks/pre-commit-sanitise-ascii
	@chmod +x .git/hooks/pre-commit-sanitise-ascii
	@printf "$(GREEN)[install-hook]$(RESET) Installed -> .git/hooks/pre-commit-sanitise-ascii\n"

.PHONY: install-hook-global
install-hook-global: ## Install pre-commit hook globally (~/.githooks/)
	@printf "$(CYAN)[install-hook-global]$(RESET) Installing global hook...\n"
	@mkdir -p ~/.githooks
	@cp .githooks/pre-commit-sanitise-ascii ~/.githooks/pre-commit-sanitise-ascii
	@chmod +x ~/.githooks/pre-commit-sanitise-ascii
	@cp $(SANITISE_SCRIPT) ~/sanitise-ascii.py
	@git config --global core.hooksPath ~/.githooks
	@printf "$(GREEN)[install-hook-global]$(RESET) Hook installed; script copied to ~/sanitise-ascii.py\n"

##@ Skill distribution

SKILL_NAME := sanitise-ascii
SKILL_FILES := SKILL.md $(SKILL_NAME).py Makefile README.md .githooks
ZIPPED_DIR  ?= $(CURDIR)/../zipped/$(SKILL_NAME)

.PHONY: zip-prep
zip-prep: ## Stage SKILL_FILES into skills/zipped/sanitise-ascii/ ready for zipping
	@printf "$(CYAN)Staging$(RESET) $(SKILL_NAME) -> $(ZIPPED_DIR)\n"
	@rm -rf $(ZIPPED_DIR)
	@mkdir -p $(ZIPPED_DIR)
	@for f in $(SKILL_FILES); do \
		/bin/cp -R $$f $(ZIPPED_DIR)/ && \
		printf "  $(GREEN)ok$(RESET)  $$f\n" || \
		{ printf "  $(RED)FAIL$(RESET)  $$f\n"; exit 1; }; \
	done
	@printf "$(GREEN)Staged$(RESET) $(ZIPPED_DIR)\n"

