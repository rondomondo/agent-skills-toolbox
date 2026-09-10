# ============================================================
# find4 -- Makefile
# ============================================================
.DEFAULT_GOAL := help
MAKEFLAGS     += --no-print-directory
SHELL         := /bin/bash

# Snapshot env vars that the user may have exported before loading .env,
# so they can override the .env defaults.
_ENV_FIND4_HOST  := $(FIND4_HOST)
_ENV_CERT_DOMAIN := $(CERT_DOMAIN)

# Load .env if present (silently skip if absent)
-include .env

# Restore any values that were set in the calling environment.
ifneq ($(_ENV_FIND4_HOST),)
FIND4_HOST := $(_ENV_FIND4_HOST)
endif
ifneq ($(_ENV_CERT_DOMAIN),)
CERT_DOMAIN := $(_ENV_CERT_DOMAIN)
endif

# -- Colors ---------------------------------------------------
BOLD   := \033[1m
RED    := \033[31m
GREEN  := \033[32m
BLUE   := \033[34m
CYAN   := \033[36m
YELLOW := \033[33m
RESET  := \033[0m

# -- Project --------------------------------------------------
PROJECT     := find4
GAME_URL    ?= https://find4.org
VERSION     := 3.12
LINE_LENGTH := 119

# -- GitHub drop ----------------------------------------------
GH_REPO          ?= $(shell git -C $(SKILL_DIR) remote get-url origin 2>/dev/null | sed 's|.*github.com[/:]||;s|\.git$$||')
GH_WORKFLOW      ?= publish-find4-games-workflow-call.yaml
GH_BRANCH_PROD   ?= find4-prod
RESULTS_SRC      := results/output
DROP_BRANCH_PREFIX := find4-drop
FORCE            ?= 0

# -- Distribution ---------------------------------------------
ZIP_DIR   := ../zipped/find4
ZIP_FILES := SKILL.md Makefile README.md scripts references vendor

# -- Tooling --------------------------------------------------
UV      := uv
NPM     := $(shell which npm || echo "npm not found")
ESBUILD := $(shell which esbuild || echo "esbuild not found")

# -- Directories ----------------------------------------------
VENV              := .venv
DIST_DIR          := dist
TEST_DIR          := tests
GAMES_DIR         := games
LIBRARY_DIR       := library
CONFIG_DIR        := library
OUTPUT_DIR        := library
DEPLOY_LOCAL_DIR  := local
DEPLOY_WEBAPP_DIR := webapp
SKILL_DIR         := .
SKILL_GH_ACTION_JSON := $(SKILL_DIR)/json
SKILL_SCRIPTS_DIR    := $(SKILL_DIR)/scripts
SKILL_RESOURCES_DIR  := $(SKILL_DIR)/references
SKILL_DOCS_DIR       := $(SKILL_DIR)/docs
JS_DIR            := js
CSS_DIR           := css

# -- Source files ---------------------------------------------
MAIN_SCRIPT        := $(SKILL_SCRIPTS_DIR)/analyzer.py
JS_FILES           := $(wildcard $(JS_DIR)/*.js)
CSS_FILES          := $(wildcard $(CSS_DIR)/*.css)
JSON_CONTENT_FILES := $(GAMES_DIR)/*.json $(LIBRARY_DIR)/*.json

# Ensure required directories exist (except DEPLOY_LOCAL_DIR -- created on demand)
$(shell mkdir -p $(DIST_DIR))
$(shell mkdir -p $(GAMES_DIR))
$(shell mkdir -p $(CONFIG_DIR))
$(shell mkdir -p $(LIBRARY_DIR))
$(shell mkdir -p $(SKILL_GH_ACTION_JSON))

# -- Certificates ---------------------------------------------
CERT_DOMAIN ?= $(FIND4_HOST)
CERT_DIR    := certs
GEN_CERT    := $(UV) run python $(SKILL_SCRIPTS_DIR)/gen_cert.py
CERT        := $(CERT_DIR)/$(CERT_DOMAIN).crt
KEY         := $(CERT_DIR)/$(CERT_DOMAIN).key

# -- Local server ---------------------------------------------
WATCHMEDO := $(UV) run watchmedo
PORT      ?= 443
HTTP_PORT ?= 80
HTML_ROOT := $(DEPLOY_WEBAPP_DIR)

# -- E2E ------------------------------------------------------
E2E_DIR        := $(TEST_DIR)/e2e
PLAYWRIGHT_IMG := mcr.microsoft.com/playwright:v1.59.1-jammy
BASE_URL       := http://host.docker.internal:8080
PLAYWRIGHT_ARGS :=

# -- Webapp deploy --------------------------------------------
WEBAPP_DIR           := webapp
#DEPLOY_WEBAPP_FILES  := index.html themes.html $(DIST_DIR) vendor games library config favicon.ico
DEPLOY_WEBAPP_FILES  := index.html themes.html $(DIST_DIR) examples vendor games config library results favicon.ico

$(shell mkdir -p $(WEBAPP_DIR))

# -- Help -----------------------------------------------------
.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} \
	  /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0,5) } \
	  /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)


##@ Setup

.PHONY: check-uv
check-uv: ## Verify uv is available
	@command -v $(UV) >/dev/null 2>&1 || \
	  (printf "$(RED)ERROR:$(RESET) uv not found. Install: https://docs.astral.sh/uv/\n"; exit 1)

.PHONY: check-deps
check-deps: ## Verify all required tools are installed
	@for cmd in $(NPM) $(ESBUILD); do \
		if [[ $$cmd == *"not found" ]]; then \
			echo "Error: $$cmd"; \
			exit 1; \
		fi \
	done

.PHONY: github-check
github-check: ## Test GitHub SSH connectivity
	ssh -T git@github.com || true

.PHONY: install
install: check-uv npm-install ## Install Python and JS dependencies
	$(UV) sync --all-extras
	@printf "$(GREEN)Dependencies installed.$(RESET)\n"

.PHONY: npm-install
npm-install: node_modules/.package-stamp ## Install JS dependencies (runs automatically when package.json changes)

node_modules/.package-stamp: package.json
	$(NPM) install
	@touch $@


##@ Development

.PHONY: format
format: ## Format Python code (ruff)
	$(UV) run --extra dev ruff format $(SKILL_SCRIPTS_DIR)/
	$(UV) run --extra dev ruff check --fix --select I $(SKILL_SCRIPTS_DIR)/

.PHONY: lint
lint: ## Lint Python code (ruff + mypy)
	$(UV) run --extra dev ruff check --fix $(SKILL_SCRIPTS_DIR)/
	$(UV) run --extra dev mypy $(SKILL_SCRIPTS_DIR)/

.PHONY: typecheck
typecheck: ## Run mypy type checks
	$(UV) run --extra dev mypy $(SKILL_SCRIPTS_DIR)/

.PHONY: test
test: ## Run Python tests with coverage
	$(UV) run --extra dev pytest $(TEST_DIR) -v --tb=short --cov=$(SKILL_SCRIPTS_DIR) --cov-report=term-missing

.PHONY: ci
ci: lint test ## Run lint + test (CI pipeline)
	@echo "CI passed"


##@ Build

.PHONY: librarygen
librarygen: ## Create themes.json and library.json in one pass
	$(UV) run python $(SKILL_SCRIPTS_DIR)/generate_library_all.py \
		--library-dir $(LIBRARY_DIR) \
		--output-dir $(OUTPUT_DIR) \
		--config-dir $(CONFIG_DIR) \
		--library-root . \
		--trigger "make librarygen" \
		--force

.PHONY: bundle
bundle: node_modules/.package-stamp ## Combine JS and CSS files (no minification)
	$(NPM) run bundle

.PHONY: minify
minify: node_modules/.package-stamp ## Minify JS and CSS bundles
	$(NPM) run minify

.PHONY: release
release: librarygen node_modules/.package-stamp ## Build and minify JS and CSS bundles
	$(NPM) run release


##@ Validate

SCHEMA := $(SKILL_RESOURCES_DIR)/find4.schema.json

.PHONY: validate-schema
validate-schema: ## Validate all games/*.json library/*.json against resources/find4.schema.json
	@printf "$(GREEN)validating game and library json files against $(CYAN)$(SCHEMA)$(RESET)...$(RESET)\n";
	@ok=0; fail=0; \
	for f in $(JSON_CONTENT_FILES); do \
		[ "$$f" = "$(GAMES_DIR)/themes.json" ] && continue; \
		if $(UV) run python -c \
			"import json,jsonschema; jsonschema.validate(json.load(open('$$f')), json.load(open('$(SCHEMA)')))" \
			2>/dev/null; then \
			printf "  $(GREEN)ok$(RESET)  $$f\n"; ok=$$((ok+1)); \
		else \
			printf "  $(RED)FAIL$(RESET)  $$f\n"; \
			$(UV) run python -c \
				"import json,jsonschema; jsonschema.validate(json.load(open('$$f')), json.load(open('$(SCHEMA)')))" \
				2>&1 | head -5; \
			fail=$$((fail+1)); \
		fi \
	done; \
	printf "\n  $(BOLD)$$ok passed, $$fail failed$(RESET)\n"; \
	[ $$fail -eq 0 ]

.PHONY: validate
validate: validate-schema ## Validate all games/*.json library/*.json for sensible values
	@printf "$(GREEN)validating game and library json files for sensible values...$(RESET)\n";
	@ok=0; fail=0; \
	for f in $(JSON_CONTENT_FILES); do \
		[ "$$f" = "$(GAMES_DIR)/themes.json" ] && continue; \
		if $(UV) run python $(SKILL_SCRIPTS_DIR)/validate.py --strict --game-set-json "$$f"; \
			2>/dev/null; then \
			printf "  $(GREEN)ok$(RESET)  $$f\n"; ok=$$((ok+1)); \
			printf "\n"; \
		else \
			printf "  $(RED)FAIL$(RESET)  $$f\n"; \
			$(UV) run python $(SKILL_SCRIPTS_DIR)/validate.py --strict --game-set-json "$$f"; \
			2>&1 | head -5; \
			fail=$$((fail+1)); \
			printf "\n"; \
		fi \
	done; \
	printf "\n  $(BOLD)$$ok passed, $$fail failed$(RESET)\n"; \
	[ $$fail -eq 0 ]


##@ Deploy

.PHONY: share
share: ## Print share URL for a game (usage: make share game=foo.json)
	@FIND4_URL=$(GAME_URL) $(SKILL_SCRIPTS_DIR)/share_game.sh $(game)

.PHONY: publish
publish: ## Publish a game JSON to S3 with short-code redirect (usage: make publish game=path/to/game.json)
	$(UV) run python $(SKILL_SCRIPTS_DIR)/publish_game.py $(game)

.PHONY: drop
drop: ## Push results/output to a scratch branch and trigger the publish workflow (FORCE=1 to force retrigger)
	@set -e; \
	GH_REPO="$(GH_REPO)"; \
	GH_WORKFLOW="$(GH_WORKFLOW)"; \
	GH_BRANCH_PROD="$(GH_BRANCH_PROD)"; \
	RESULTS_SRC="$(RESULTS_SRC)"; \
	DROP_BRANCH_PREFIX="$(DROP_BRANCH_PREFIX)"; \
	SKILL_DIR="$(SKILL_DIR)"; \
	if [ -z "$$GH_REPO" ]; then \
		printf "$(RED)ERROR:$(RESET) GH_REPO could not be inferred from git remote. Set it explicitly:\n"; \
		printf "  make drop GH_REPO=owner/repo\n"; \
		exit 1; \
	fi; \
	if ! command -v gh >/dev/null 2>&1; then \
		printf "$(RED)ERROR:$(RESET) gh CLI not found. Install from https://cli.github.com\n"; \
		exit 1; \
	fi; \
	if [ ! -d "$$RESULTS_SRC" ]; then \
		printf "$(RED)ERROR:$(RESET) $$RESULTS_SRC does not exist - nothing to drop.\n"; \
		exit 1; \
	fi; \
	RAND=$$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 6); \
	DROP_BRANCH="$${DROP_BRANCH_PREFIX}-$$(date +%Y%m%d-%H%M%S)-$${RAND}"; \
	REPO_ROOT="$$(git -C "$$SKILL_DIR" rev-parse --show-toplevel)"; \
	CLONE_DIR="$${REPO_ROOT}/skills/find4/results/tmp/gh-drop-$${DROP_BRANCH}"; \
	printf "$(CYAN)Drop branch:$(RESET) $$DROP_BRANCH\n"; \
	printf "$(CYAN)Repo:$(RESET)        $$GH_REPO\n"; \
	printf "$(CYAN)Source:$(RESET)      $$RESULTS_SRC\n"; \
	printf "$(GREEN)Sparse-cloning $$GH_REPO...$(RESET)\n"; \
	git clone \
	  --depth 1 \
	  --filter=blob:none \
	  --sparse \
	  "https://x-access-token:$$(gh auth token)@github.com/$${GH_REPO}.git" \
	  "$$CLONE_DIR" 2>&1; \
	cd "$$CLONE_DIR"; \
	git sparse-checkout set skills/find4/results; \
	git checkout -b "$$DROP_BRANCH"; \
	DEST="$$CLONE_DIR/skills/find4/results/output"; \
	mkdir -p "$$DEST"; \
	if [ "$(FORCE)" = "1" ]; then \
		cp -r "$${REPO_ROOT}/skills/find4/$${RESULTS_SRC}/." "$$DEST/" || true; \
		FILE_COUNT=$$(find "$${REPO_ROOT}/skills/find4/$${RESULTS_SRC}" -maxdepth 1 -type f | wc -l | tr -d ' '); \
		printf "{\n  \"retrigger\": true,\n  \"branch\": \"$$DROP_BRANCH\",\n  \"triggered_at\": \"$$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\n  \"triggered_by\": \"$$(git config user.name || echo unknown)\",\n  \"source\": \"$$RESULTS_SRC\",\n  \"file_count\": $$FILE_COUNT\n}\n" > "$$DEST/.force-retrigger.json"; \
	else \
		cp -rn "$${REPO_ROOT}/skills/find4/$${RESULTS_SRC}/." "$$DEST/" || true; \
	fi; \
	git add skills/find4/results/; \
	if git diff --cached --quiet; then \
		printf "$(YELLOW)No new files - nothing to push. Use FORCE=1 to override.$(RESET)\n"; \
		cd "$$REPO_ROOT/skills/find4"; rm -rf "$$CLONE_DIR"; exit 0; \
	fi; \
	git config user.email "find4-drop@abcdef.ai"; \
	git config user.name "find4 drop"; \
	git commit -m "feat(find4): drop results for publish [$$DROP_BRANCH]" --quiet; \
	git push origin "$$DROP_BRANCH" --quiet; \
	printf "$(GREEN)Pushed$(RESET) $$DROP_BRANCH\n"; \
	cd "$${REPO_ROOT}/skills/find4"; rm -rf "$$CLONE_DIR"; \
	printf "$(GREEN)Triggering workflow...$(RESET)\n"; \
	gh workflow run "$$GH_WORKFLOW" \
	  --repo "$$GH_REPO" \
	  --ref "$$DROP_BRANCH" \
	  --field "source_branch=$$DROP_BRANCH" \
	  --field "branch_prod=$$GH_BRANCH_PROD"; \
	printf "$(GREEN)Done.$(RESET) Workflow dispatched for branch $$DROP_BRANCH\n"; \
	printf "  Track: https://github.com/$$GH_REPO/actions\n"

.PHONY: deploy-webapp
deploy-webapp: minify ## Copy deployable files to the webapp directory (WEBAPP_DIR=webapp)
	@mkdir -p $(WEBAPP_DIR)
	@/bin/rm -rf $(WEBAPP_DIR)/*
	@printf "$(GREEN)deploying to $(CYAN)$(WEBAPP_DIR)/$(RESET)...\n"
	@ok=0; fail=0; \
	for f in $(DEPLOY_WEBAPP_FILES); do \
		if /bin/cp -R $$f $(WEBAPP_DIR)/ 2>/dev/null; then \
			printf "  $(GREEN)ok$(RESET)  $$f\n"; ok=$$((ok+1)); \
		else \
			printf "  $(RED)FAIL$(RESET)  $$f\n"; fail=$$((fail+1)); \
		fi \
	done; \
	printf "certs\n" >> $(WEBAPP_DIR)/.gitignore; \
	/bin/rm -rf $(WEBAPP_DIR)/certs; \
	printf "\n  $(BOLD)$$ok copied, $$fail failed$(RESET)\n"; \
	[ $$fail -eq 0 ]

.PHONY: zip-prep
zip-prep: ## Copy distributable files to ZIP_DIR (../zipped/find4) ready for zipping
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
	printf "\n  $(BOLD)$$ok copied, $$fail failed$(RESET)\n"; \
	[ $$fail -eq 0 ]


##@ Certificates

.PHONY: gen-cert
gen-cert: check-uv ## Generate self-signed TLS cert (CERT_DOMAIN=$(FIND4_HOST))
	$(GEN_CERT) --domain $(CERT_DOMAIN) --wildcard --cert-dir $(CERT_DIR)
	@printf "$(GREEN)Certificate written to$(RESET) $(CERT_DIR)/\n"

.PHONY: gen-cert-snippet
gen-cert-snippet: ## Print Makefile snippet for HTTPS dev server (usage: make gen-cert-snippet [CERT_DOMAIN=yourdomain.com])
	$(GEN_CERT) --makefile-snippet -d $(CERT_DOMAIN)

.PHONY: clean-certs
clean-certs: ## Remove generated TLS certificates
	@printf "$(CYAN)Removing$(RESET) $(CERT_DIR)/...\n"
	@rm -f $(CERT_DIR)/*.crt $(CERT_DIR)/*.key 2>/dev/null || true
	@printf "  $(GREEN)ok$(RESET)\n"


##@ Local Server

.PHONY: check-hosts
check-hosts: ## Warn if CERT_DOMAIN is not present in /etc/hosts
	@if grep -q "$(CERT_DOMAIN)" /etc/hosts && ! grep -Eq "^[^#]*$(CERT_DOMAIN)" /etc/hosts; then \
		printf "$(YELLOW)\nWARNING:$(RESET) '$(CERT_DOMAIN)' is commented out in /etc/hosts -- HTTPS may not resolve.\n"; \
		printf "         Uncomment or add: $(BOLD)127.0.0.1  $(CERT_DOMAIN)$(RESET)\n\n"; \
	elif ! grep -q "$(CERT_DOMAIN)" /etc/hosts; then \
		printf "$(YELLOW)WARNING:$(RESET) '$(CERT_DOMAIN)' not found in /etc/hosts -- HTTPS may not resolve as expected.\n"; \
		printf "         Add an entry like: $(BOLD)127.0.0.1  $(CERT_DOMAIN)$(RESET)\n\n"; \
	else \
		printf "$(GREEN)ok$(RESET)  /etc/hosts contains '$(CERT_DOMAIN)'\n\n"; \
	fi

.PHONY: serve
serve: gen-cert deploy-webapp ## Auto-restart HTTPS server on file changes
	/bin/cp -R $(SKILL_DIR)/certs $(HTML_ROOT)/certs && \
	$(WATCHMEDO) auto-restart \
	  --patterns="$(JS_DIR)/*.js;$(CSS_DIR)/*.css;index.html" \
	  --recursive \
	  --debounce-interval=0.5 \
	  -- python3 -c "\
import ssl, http.server, os; \
os.chdir('$(HTML_ROOT)'); \
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); \
ctx.load_cert_chain('$(CERT)', '$(KEY)'); \
httpd = http.server.HTTPServer(('0.0.0.0', $(PORT)), http.server.SimpleHTTPRequestHandler); \
httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True); \
print('Serving HTTPS on $(GAME_URL):$(PORT)'); \
httpd.serve_forever()"

.PHONY: serve-http
serve-http: deploy-webapp ## Auto-restart plain HTTP server on file changes (HTTP_PORT=8080)
	$(WATCHMEDO) auto-restart \
	  --patterns="$(JS_DIR)/*.js;$(CSS_DIR)/*.css;index.html" \
	  --recursive \
	  --debounce-interval=0.5 \
	  -- python3 -c "\
import http.server, os; \
os.chdir('$(HTML_ROOT)'); \
httpd = http.server.HTTPServer(('0.0.0.0', $(HTTP_PORT)), http.server.SimpleHTTPRequestHandler); \
print('Serving HTTP on http://localhost:$(HTTP_PORT)'); \
httpd.serve_forever()"


##@ E2E

.PHONY: e2e
e2e: ## Run Playwright e2e tests in Docker (BASE_URL=... PLAYWRIGHT_ARGS=... PLAYWRIGHT_IMG=... to override)
	@printf "\n$(GREEN)Running playwright test in a docker container$(RESET)\n"
	docker run --rm \
		--add-host=host.docker.internal:host-gateway \
		-v $(PWD)/$(E2E_DIR):/tests \
		-w /tests \
		-e BASE_URL=$(BASE_URL) \
		$(PLAYWRIGHT_IMG) \
		sh -c "npm install && npx playwright test $(PLAYWRIGHT_ARGS)";
	@printf "\n$(CYAN)Report:$(RESET) $(E2E_DIR)/playwright-report/index.html\n"


##@ Cleanup

.PHONY: clean-pyc
clean-pyc: ## Remove Python bytecode and tool caches
	@printf "$(CYAN)cleaning$(RESET) Python caches...\n"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .mypy_cache  -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache  -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@printf "  $(GREEN)ok$(RESET)\n"

.PHONY: clean-build
clean-build: ## Remove dist/, build/, egg-info and coverage reports
	@printf "$(CYAN)cleaning$(RESET) build artifacts...\n"
	@rm -rf $(DIST_DIR)/ build/ 2>/dev/null || true
	@find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf coverage/ .coverage htmlcov/ 2>/dev/null || true
	@printf "  $(GREEN)ok$(RESET)\n"

.PHONY: clean-node
clean-node: ## Remove node_modules/
	@printf "$(CYAN)cleaning$(RESET) node_modules...\n"
	@rm -rf node_modules/ 2>/dev/null || true
	@printf "  $(GREEN)ok$(RESET)\n"

.PHONY: clean-venv
clean-venv: ## Remove Python virtual environment
	@printf "$(CYAN)cleaning$(RESET) venv...\n"
	@rm -rf $(VENV)/ 2>/dev/null || true
	@printf "  $(GREEN)ok$(RESET)\n"

.PHONY: clean-local
clean-local: ## Remove local deploy directory (DEPLOY_LOCAL_DIR=local)
	@printf "$(CYAN)cleaning$(RESET) $(DEPLOY_LOCAL_DIR)/...\n"
	@rm -rf $(DEPLOY_LOCAL_DIR)/ 2>/dev/null || true
	@printf "  $(GREEN)ok$(RESET)\n"

.PHONY: clean-generated
clean-generated: ## Remove generated game files (games/export/, games/themes.json)
	@printf "$(CYAN)cleaning$(RESET) generated game files...\n"
	@rm -rf games/export/ 2>/dev/null || true
	@rm -f games/themes.json 2>/dev/null || true
	@printf "  $(GREEN)ok$(RESET)\n"

.PHONY: clean
clean: clean-pyc clean-build clean-local clean-node ## Remove common artifacts (pyc, build, local deploy, generated games)

.PHONY: distclean
distclean: clean clean-node clean-venv clean-certs ## Full reset -- removes everything including node_modules, venv, and certs
