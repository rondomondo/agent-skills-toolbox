# ============================================================
# mermaid-render -- Makefile
# ============================================================
.DEFAULT_GOAL := help
MAKEFLAGS     += --no-print-directory
SHELL         := /bin/bash

# -- Colors ---------------------------------------------------
BOLD   := \033[1m
GREEN  := \033[32m
CYAN   := \033[36m
RED    := \033[31m
RESET  := \033[0m

# -- Paths ----------------------------------------------------
SKILL_NAME        := mermaid-render
DESTDIR           := /usr/local/bin
SKILL_NAME_TARGET := $(DESTDIR)/$(SKILL_NAME)

# -- Skill distribution ---------------------------------------
SKILLS_DIR            ?= $(HOME)/Code/agent-skills-toolbox/skills/$(SKILL_NAME)
SKILL_FILES           := SKILL.md Makefile README.md mermaid-render examples references evals

# -- Test -----------------------------------------------------
TEST_INPUT     ?= examples/example1.md

# -- Help -----------------------------------------------------
.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} \
	  /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0,5) } \
	  /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)

##@ Install

.PHONY: install
install: ## Install mermaid-render to $(DESTDIR)
	@install -m 755 $(SKILL_NAME) $(SKILL_NAME_TARGET)
	@printf "$(GREEN)Installed$(RESET) $(SKILL_NAME_TARGET)\n"

.PHONY: uninstall
uninstall: ## Remove mermaid-render from $(DESTDIR)
	@rm -f $(SKILL_NAME_TARGET)
	@printf "$(GREEN)Removed$(RESET) $(SKILL_NAME_TARGET)\n"

##@ mermaid-render

.PHONY: mermaid-render-usage
mermaid-render-usage: ## Show mermaid-render usage
	@bash $(SKILL_NAME)

.PHONY: test
test: ## Render TEST_INPUT as SVG and PNG to verify the full pipeline (override: TEST_INPUT=examples/foo.md)
	@printf "$(BOLD)$(CYAN)--- SVG render ---$(RESET)\n"
	@bash $(SKILL_NAME) $(TEST_INPUT) -f svg
	@printf "$(BOLD)$(CYAN)--- PNG render ---$(RESET)\n"
	@bash $(SKILL_NAME) $(TEST_INPUT) -f png --width 960 --height 640
	@printf "$(GREEN)Test renders complete$(RESET)\n"

.PHONY: clean
clean: ## Remove rendered output files from examples/ and data/
	@printf "$(CYAN)Removing$(RESET) rendered output files...\n"
	@find examples/ data/ -type f \( -name "*.svg.md" -o -name "*.png.md" -o -name "*.pdf.md" -o -name "*.md-[0-9]*.svg" -o -name "*.md-[0-9]*.png" -o -name "*.md-[0-9]*.pdf" \) -delete 2>/dev/null || true
	@printf "$(GREEN)Clean$(RESET)\n"

.PHONY: check
check: ## Verify mermaid-render is installed and reachable
	@command -v mermaid-render >/dev/null 2>&1 \
	  && printf "$(GREEN)OK$(RESET)  mermaid-render found at $$(command -v mermaid-render)\n" \
	  || { printf "$(RED)FAIL$(RESET)  mermaid-render not found in PATH -- run: make install\n"; exit 1; }

##@ Doctor

.PHONY: doctor
doctor: ## Show environment info useful for bug reports
	@printf "$(BOLD)mermaid-render doctor$(RESET)\n\n"
	@printf "  Shell:    %s\n" "$$SHELL"
	@printf "  Wrapper:  "; ls -lh "$(SKILL_NAME)" 2>/dev/null || printf "$(RED)not found$(RESET)\n"
	@echo ""

##@ Skill distribution

ZIPPED_DIR            ?= $(CURDIR)/../../skills/zipped/$(SKILL_NAME)

.PHONY: zip-prep
zip-prep: ## Stage SKILL_FILES into skills/zipped/mermaid/ ready for zipping
	@printf "$(CYAN)Staging$(RESET) $(SKILL_NAME) -> $(ZIPPED_DIR)\n"
	@rm -rf $(ZIPPED_DIR)
	@mkdir -p $(ZIPPED_DIR)/scripts $(ZIPPED_DIR)/examples $(ZIPPED_DIR)/data $(ZIPPED_DIR)/references
	@for f in $(SKILL_FILES); do \
			/bin/cp -R $$f $(ZIPPED_DIR)/ && \
			printf "  $(GREEN)ok$(RESET)  $$f\n" || \
			{ printf "  $(RED)FAIL$(RESET)  $$f\n"; exit 1; }; \
	done
	@printf "$(GREEN)Staged$(RESET) $(ZIPPED_DIR)\n"

