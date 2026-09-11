DOCKER_REPO ?= rondomondo
IMAGE       := $(DOCKER_REPO)/qr-cli
TAG         := latest
PROJECT     ?= daveco

.DEFAULT_GOAL := help
SHELL := /bin/bash

BOLD   := \033[1m
CYAN   := \033[36m
GREEN  := \033[32m
RESET  := \033[0m

PYTHON   := python3
VENV     := .venv
PIP      := $(VENV)/bin/pip

.PHONY: build build-clean usage shell clean help examples gen-examples skill-examples skill-examples-local skill-install demo demo-all

help: ## Show this help message
	@printf "$(BOLD)$(IMAGE) -- available targets$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""

.PHONY: check-venv
check-venv: venv ## Verify the virtual environment is activated
	@if [ -z "$${VIRTUAL_ENV:-}" ]; then \
	  printf "\033[31mERROR:\033[0m virtual env not active.\n"; \
	  printf "Activate it first:\n\n"; \
	  printf "  \033[32msource $(VENV)/bin/activate\033[0m\n\n"; \
	  printf "Then re-run make.\n"; \
	  exit 1; \
	fi
	@echo "  venv active: $${VIRTUAL_ENV}"

.PHONY: venv
venv: ## Create Python virtual environment (if absent)
	@if [ ! -d "$(VENV)" ]; then \
	  echo "  creating venv in $(VENV)..."; \
	  $(PYTHON) -m venv $(VENV); \
	  $(VENV)/bin/pip install --upgrade pip; \
	  echo "  venv created - activate with: source $(VENV)/bin/activate"; \
	else \
	  echo "  venv already exists in $(VENV)"; \
	fi


build: ## Build the Docker image
	docker build -t $(IMAGE):$(TAG) .

build-clean: ## Build the Docker image with no layer cache
	docker build --no-cache -t $(IMAGE):$(TAG) .

usage: ## Show the generator's own --help as pretty-printed JSON
	docker run --rm $(IMAGE):$(TAG) --help | python3 -m json.tool

shell: ## Open an interactive bash shell inside the container
	docker run --rm -it --entrypoint bash $(IMAGE):$(TAG)

gen-examples: ## Parse EXAMPLES.md and (re)generate run_examples.sh
	@python3 scripts/extract_examples.py --project $(PROJECT) --image $(IMAGE):$(TAG)

skill-examples-local: ## Parse EXAMPLES.md and print equivalent /qr for local viewing
	@python3 scripts/extract_skill_examples.py

examples: gen-examples ## Parse EXAMPLES.md and run all bash examples
	@printf "$(GREEN)Generating examples$(RESET)\n"
	@bash scripts/run_examples.sh
	@printf "$(BOLD)$(CYAN)Generated images$(RESET)\n"
	@find assets/images -type f | xargs file

skill-examples: ## Parse EXAMPLES.md and print equivalent /qr skill commands
	@python3 .claude/skills/qr/scripts/extract_skill_examples.py
	@$(MAKE) skill-examples-local


skill-install: ## Install the /qr skill into ~/.claude/skills/misc/qr/ and install colourmapper
	@printf "$(GREEN)Installing .claude/skills/qr -> ~/.claude/skills/qr$(RESET)\n"
	@mkdir -p ~/.claude/skills/qr 2> /dev/null
	@chmod +x  .claude/skills/qr/scripts/*
	@/bin/cp -R .claude/skills/qr ~/.claude/skills/
	@pip install -i https://pypi.org/simple/ colourmapper-dev
	@printf "$(GREEN)Installed .claude/skills/qr  -> ~/.claude/skills/qr$(RESET)\n"

clean: ## Remove the Docker image and any build artifacts and caches
	@docker rmi $(IMAGE):$(TAG)  2>/dev/null || true
	@/bin/rm scripts/run_examples.sh 2>/dev/null || true
	@find assets/images/$(PROJECT) -mindepth 2 -type f -delete 2>/dev/null || true

