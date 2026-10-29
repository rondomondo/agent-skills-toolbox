# ============================================================
# screenshot -- Makefile  (tool-specific; shared targets live in ../docker.mk)
# ============================================================

TOOL := screenshot

# -- Paths & Directory Defaults -------------------------------
SCREENSHOTS_DIR ?= $(CURDIR)/screenshots
PDFS_DIR        ?= $(CURDIR)/pdfs
HTML_DIR        ?= $(CURDIR)/html
WORKSPACE_DIR   ?= $(CURDIR)/workspace
SESSIONS_DIR    := $(WORKSPACE_DIR)/sessions

SESSION         ?= default
SESSION_FILE    := $(SESSIONS_DIR)/$(SESSION).json

# MCP server port. 3000 is Playwright MCP's default but conflicts with Grafana; override as needed.
MCP_PORT        ?= 3000
MCP_SSE_URL     := http://localhost:$(MCP_PORT)/sse
MCP_HTTP_URL    := http://localhost:$(MCP_PORT)/mcp

# Alternatives: 
# https://en.wikipedia.org/wiki/Special:Random
# https://en.wikipedia.org/wiki/1822_Vermont_gubernatorial_election
EXAMPLE_URL     ?= https://jax-ml.github.io/scaling-book/index

IMAGE_REPO  := rondomondo/screenshot
VERSION_ARG := SCREENSHOT_VERSION
BUILDER         := screenshotter-builder
INSTALL_ASSETS  := url2capture.sh:url2capture
INSTALL_LINKS   := url2pdf url2image
CLEAN_ALL_EXTRA := clean-generated clean-python clean-node

include ../docker.mk

##@ Test

.PHONY: test
test: ## Run the unit test suite
	uv run pytest

##@ Dev Operations

# Helper definition: Checks if MCP server is running via JSON-RPC ping; if not, starts it temporarily.
define RUN_MCP_CLIENT
	@mkdir -p "$(SCREENSHOTS_DIR)" "$(PDFS_DIR)" "$(HTML_DIR)" "$(SESSIONS_DIR)"
	@WAS_RUNNING=1; \
	if ! curl -fs --max-time 3 -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
	   -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1"}}}' \
	   $(MCP_HTTP_URL) >/dev/null 2>&1; then \
		WAS_RUNNING=0; \
		printf "$(CYAN)MCP server not detected. Spinning up background container...$(RESET)\n"; \
		$(MAKE) mcp-up SESSION=$(SESSION) MCP_PORT=$(MCP_PORT) >/dev/null; \
	fi; \
	uv run ssc.py $(1) --url $(MCP_SSE_URL) $(TARGET) $(ARGS); \
	EXIT_CODE=$$?; \
	if [ "$$WAS_RUNNING" -eq 0 ]; then \
		printf "$(CYAN)Cleaning up temporary MCP container...$(RESET)\n"; \
		$(MAKE) mcp-down SESSION=$(SESSION) >/dev/null; \
	fi; \
	exit $$EXIT_CODE
endef

.PHONY: screenshot
screenshot: ## Take a full-page screenshot (defaults to EXAMPLE_URL): make screenshot [TARGET=https://...] [ARGS="--no-scroll"]
	$(eval TARGET ?= $(EXAMPLE_URL))
	$(call RUN_MCP_CLIENT,screenshot)

.PHONY: pdf
pdf: ## Save page as PDF (defaults to EXAMPLE_URL): make pdf [TARGET=https://...] [ARGS="--pause 1000"]
	$(eval TARGET ?= $(EXAMPLE_URL))
	$(call RUN_MCP_CLIENT,pdf)

.PHONY: mcp-up
mcp-up: ## Start the MCP server in the background (SESSION=default selects the browser session to load)
	@mkdir -p "$(SESSIONS_DIR)"
	@if [ ! -f "$(SESSION_FILE)" ]; then \
	  printf '{}' > "$(SESSION_FILE)"; \
	  printf "$(CYAN)Created$(RESET) empty session: $(SESSION_FILE)\n"; \
	fi
	SESSION=$(SESSION) docker compose up -d mcp
	@printf "$(GREEN)Started$(RESET) MCP server on port $(MCP_PORT) (session: $(SESSION))\n"

.PHONY: mcp-down
mcp-down: ## Stop and remove the MCP server container
	SESSION=$(SESSION) docker compose down mcp
	@printf "$(GREEN)Stopped$(RESET) MCP server\n"

.PHONY: mcp-shell
mcp-shell: ## Open a shell in the MCP container (useful for inspecting /workspace)
	@mkdir -p "$(SESSIONS_DIR)"
	docker run --rm -it \
	  -v $(WORKSPACE_DIR):/workspace \
	  --entrypoint bash \
	  $(REMOTE):latest

.PHONY: docker-shell
docker-shell: ## Open an interactive bash shell in the image
	docker run --rm -it --entrypoint bash $(REMOTE):$(VERSION)

##@ Devices

DEVICES_URL := https://rondomondo.github.io/pw-device-list/devices.py

.PHONY: devices-fetch
devices-fetch: ## Fetch devices.py from the public endpoint (rondomondo.github.io/pw-device-list)
	@printf "$(CYAN)Fetching devices.py from $(DEVICES_URL)...$(RESET)\n"
	@curl -fsSL "$(DEVICES_URL)" -o devices.py
	@count=$$(grep -c '"userAgent"' devices.py); printf "$(GREEN)Fetched$(RESET) devices.py ($$count devices)\n"

##@ Info

.PHONY: example
example: ## Print cut-and-paste usage example
	@printf "\n$(BOLD)Install onto your host$(RESET)\n"
	@printf "  docker run --rm $(REMOTE):latest install | sh\n"
	@printf "  docker run --rm $(REMOTE):latest uninstall | sh\n"
	@printf "\n$(BOLD)url2image / url2pdf (after install)$(RESET)\n"
	@printf "  url2image $(EXAMPLE_URL)\n"
	@printf "  url2image $(EXAMPLE_URL) --convert webp\n"
	@printf "  url2image $(EXAMPLE_URL) --no-scroll --viewport-size 1920x1080\n"
	@printf "  url2pdf   $(EXAMPLE_URL)\n"
	@printf "  url2pdf   $(EXAMPLE_URL) --convert jpeg\n"
	@printf "  url2pdf   $(EXAMPLE_URL) --paper-format Letter --wait-for-timeout 5000\n"
	@printf "  DEBUG=1   url2pdf $(EXAMPLE_URL)\n"
	@printf "\n$(BOLD)Docker directly$(RESET)\n"
	@printf "  docker run --rm \\\\\n"
	@printf "    -v \$$(pwd)/screenshots:/screenshots \\\\\n"
	@printf "    -v \$$(pwd)/pdfs:/pdfs \\\\\n"
	@printf "    $(REMOTE):latest screenshot $(EXAMPLE_URL)\n"
	@printf "  docker run --rm \\\\\n"
	@printf "    -v \$$(pwd)/screenshots:/screenshots \\\\\n"
	@printf "    -v \$$(pwd)/pdfs:/pdfs \\\\\n"
	@printf "    -v \$$(pwd)/html:/html:ro \\\\\n"
	@printf "    $(REMOTE):latest screenshot my-page.html\n"
	@printf "\n$(BOLD)make screenshot / make pdf (via MCP client)$(RESET)\n"
	@printf "  make screenshot TARGET=$(EXAMPLE_URL)\n"
	@printf "  make screenshot TARGET=$(EXAMPLE_URL) ARGS=\"--convert webp\"\n"
	@printf "  make screenshot TARGET=my-page.html\n"
	@printf "  make pdf        TARGET=$(EXAMPLE_URL)\n"
	@printf "  make pdf        TARGET=$(EXAMPLE_URL) ARGS=\"--paper-format Letter\"\n"
	@printf "\n$(BOLD)MCP server$(RESET)\n"
	@printf "  make mcp-up\n"
	@printf "  make mcp-up SESSION=mysite\n"
	@printf "  make mcp-down\n"
	@printf "  make status\n"
	@printf "\n"

.PHONY: status
status: ## Show running containers, health, and MCP connection details
	@echo ""
	@printf "$(BOLD)Containers$(RESET)\n"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true
	@echo ""
	@if docker compose ps --status running 2>/dev/null | grep -q "mcp"; then \
	  printf "$(BOLD)MCP server$(RESET)\n"; \
	  printf "  HTTP/SSE endpoint : $(GREEN)http://localhost:$(MCP_PORT)$(RESET)\n"; \
	  printf "  Health check      : "; \
	  if curl -fs --max-time 3 -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
	     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1"}}}' \
	     $(MCP_HTTP_URL) >/dev/null 2>&1; then \
	    printf "$(GREEN)healthy$(RESET)\n"; \
	  else \
	    printf "$(RED)unreachable$(RESET)\n"; \
	  fi; \
	  printf "  Session file      : $(SESSION_FILE)\n"; \
	  printf "  MCP endpoint      : $(MCP_HTTP_URL)\n"; \
	  printf "  SSE endpoint      : $(MCP_SSE_URL)\n"; \
	fi
	@echo ""

##@ Cleanup

.PHONY: clean-generated
clean-generated: ## Empty screenshots/ and pdfs/ output directories
	@rm -rf "$(SCREENSHOTS_DIR)"/* "$(PDFS_DIR)"/* "$(HTML_DIR)"/*.png "$(HTML_DIR)"/*.pdf
	@printf "$(GREEN)Cleared$(RESET) $(SCREENSHOTS_DIR) and $(PDFS_DIR)\n"

.PHONY: clean-python
clean-python: ## Remove __pycache__, *.pyc, *.pyo, .mypy_cache, .pytest_cache, .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true
	@rm -rf .mypy_cache .pytest_cache .ruff_cache
	@printf "$(GREEN)Removed$(RESET) Python caches\n"

.PHONY: clean-node
clean-node: ## Remove all node_modules directories recursively
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@printf "$(GREEN)Removed$(RESET) node_modules\n"
