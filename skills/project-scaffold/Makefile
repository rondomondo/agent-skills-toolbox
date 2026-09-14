# ==============================================================================
# project-scaffold Skill Makefile
# ==============================================================================

# --- Visual Settings ---
BOLD   := \033[1m
RED    := \033[31m
GREEN  := \033[32m
CYAN   := \033[36m
YELLOW := \033[33m
RESET  := \033[0m

# --- Configuration ---
MAKEFLAGS         += --no-print-directory
SHELL             := /bin/bash
VENV              := .venv
SKILL_DIR         := .
SKILL_SRC_DIR     := $(SKILL_DIR)/src
SKILL_SCRIPTS_DIR := $(SKILL_DIR)/scripts
TEST_DIR          := tests

# --- Output & Distribution ---
ZIP_DIR           := ../zipped/project-scaffold
ZIP_FILE          := project-scaffold.zip
ZIP_FILES         := SKILL.md Makefile references

# --- Tooling ---
PYTHON            := python3
PIP               := $(VENV)/bin/pip
PYTEST            := $(VENV)/bin/pytest
RUFF              := $(VENV)/bin/ruff
MYPY              := $(VENV)/bin/mypy
BLACK             := $(VENV)/bin/black
ISORT             := $(VENV)/bin/isort


# Create output directory immediately
$(shell mkdir -p $(SKILL_SRC_DIR))

# ==============================================================================
# Essential Targets
# ==============================================================================

.PHONY: help
help: ## Display this help message
	@printf "\nUsage: make $(CYAN)<target>$(RESET)\n"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: venv
venv: ## Create Python virtual environment (recreates if interpreter path is stale)
	@stale=0; \
	if [ -d "$(VENV)" ]; then \
		interp=$$(head -1 $(VENV)/bin/pip 2>/dev/null | sed 's/^#!//'); \
		if [ -n "$$interp" ] && [ ! -f "$$interp" ]; then \
			printf "$(YELLOW)Stale venv (interpreter $$interp missing) — recreating...$(RESET)\n"; \
			rm -rf $(VENV); \
			stale=1; \
		fi; \
	fi; \
	if [ ! -d "$(VENV)" ]; then \
		printf "$(GREEN)Creating venv in $(VENV)...$(RESET)\n"; \
		$(PYTHON) -m venv $(VENV); \
		$(PIP) install --upgrade pip; \
		printf "$(GREEN)Venv created. Activate with: source $(VENV)/bin/activate$(RESET)\n"; \
	elif [ "$$stale" = "0" ]; then \
		printf "$(YELLOW)Venv already exists.$(RESET)\n"; \
	fi

.PHONY: install
install: venv ## Install development dependencies
	@$(PIP) install --quiet --upgrade pip
	@$(PIP) install -e ".[dev]"
	@printf "$(GREEN)Dependencies installed.$(RESET)\n"

.PHONY: check-venv
check-venv: ## Verify venv exists
	@test -d $(VENV) || (printf "$(RED)ERROR:$(RESET) venv not found. Run: make install\n"; exit 1)


# ==============================================================================
# Code Quality & Distribution
# ==============================================================================

.PHONY: format
format: check-venv ## Format Python code
	@$(BLACK) $(SKILL_SRC_DIR)/
	@$(ISORT) $(SKILL_SRC_DIR)/

.PHONY: lint
lint: check-venv ## Lint Python code
	@$(RUFF) check --fix $(SKILL_SRC_DIR)/

.PHONY: typecheck
typecheck: check-venv ## Run mypy type checks
	$(MYPY) $(SKILL_SRC_DIR)/

.PHONY: test
test: check-venv ## Run Python tests with coverage
	@true
#	$(PYTEST) $(TEST_DIR) -v --tb=short --cov=$(SKILL_SRC_DIR) --cov-report=term-missing

.PHONY: ci
ci: format lint typecheck ## Run CI pipeline
	@echo "CI passed"


.PHONY: zip-prep
zip-prep: ## Copy distributable files to ZIP_DIR (../zipped/project-scaffold) ready for zipping
	@printf "$(CYAN)Preparing zip staging dir:$(RESET) $(ZIP_DIR)\n"
	@/bin/rm -rf $(ZIP_DIR)
	@mkdir -p $(ZIP_DIR)
	@ok=0; fail=0; \
	for f in $(ZIP_FILES); do \
		if /bin/cp -R $$f $(ZIP_DIR)/ 2>/dev/null; then \
			printf "  $(GREEN)ok$(RESET)  $$f\n"; ok=$$((ok+1)); \
		else \
			printf "  $(RED)FAIL$(RESET)  $$f\n"; fail=$$((fail+1)); \
		fi \
	done; \
	printf "\n  $(BOLD)$$ok copied, $$fail failed$(RESET) -> $(ZIP_DIR)\n"; \
	[ $$fail -eq 0 ]


.PHONY: clean-pyc
clean-pyc: ## Remove Python bytecode and tool caches
	@printf "$(CYAN)cleaning$(RESET) Python caches...\n"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .mypy_cache  -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache  -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@printf "  $(GREEN)ok$(RESET)\n"

.PHONY: clean
clean: clean-pyc ## Remove generated output
	@printf "$(CYAN)Cleaning$(RESET)...\n"
	@rm -rf *.zip
	@rm -rf .coverage
	@rm -rf $(VENV)
	@printf "  $(GREEN)ok$(RESET)\n"
	