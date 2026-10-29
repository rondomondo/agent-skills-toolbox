# ============================================================
# mermaid-render -- Makefile  (tool-specific; shared targets live in ../docker.mk)
# ============================================================

# -- Paths ----------------------------------------------------
TOOL := mermaid-render

IMAGE_SHELL ?= bash
DOCKER_EXTRA_ARGS ?= --env DEBUG=false --env USE_SHELL=$(IMAGE_SHELL)

# -- Test -----------------------------------------------------
TEST_INPUT     ?= examples/example1.md

IMAGE_REPO  := rondomondo/mermaid-render
VERSION_ARG := MERMAID_RENDER_VERSION
CLEAN_ALL_EXTRA := clean-output

include ../docker.mk

##@ mermaid-render

.PHONY: mermaid-render-usage
mermaid-render-usage: ## Show mermaid-render usage
	@bash $(TOOL)

.PHONY: test
test: ## Render TEST_INPUT as SVG and PNG to verify the full pipeline (override: TEST_INPUT=examples/foo.md)
	@printf "$(BOLD)$(CYAN)--- SVG render ---$(RESET)\n"
	@bash $(TOOL) $(TEST_INPUT) --scale 2 -f svg
	@printf "$(BOLD)$(CYAN)--- PNG render ---$(RESET)\n"
	@bash $(TOOL) $(TEST_INPUT) --scale 2 -f png --width 960 --height 640
	@printf "$(GREEN)Test renders complete$(RESET)\n"

.PHONY: clean-output
clean-output: ## Remove rendered output files from examples/ and data/
	@printf "$(CYAN)Removing$(RESET) rendered output files...\n"
	@find examples/ -maxdepth 1 -type f \( -name "*.svg.md" -o -name "*.png.md" -o -name "*.pdf.md" -o -name "*.webp.md" -o -name "*.gif.md" -o -name "*.jpg.md" -o -name "*.md-[0-9]*.svg" -o -name "*.md-[0-9]*.png" -o -name "*.md-[0-9]*.pdf" -o -name "*.md-[0-9]*.webp" -o -name "*.md-[0-9]*.gif" -o -name "*.md-[0-9]*.jpg" \) -delete 2>/dev/null || true
	@printf "$(GREEN)Clean$(RESET)\n"

.PHONY: check
check: ## Verify mermaid-render is installed and reachable
	@command -v mermaid-render >/dev/null 2>&1 \
	  && printf "$(GREEN)OK$(RESET)  mermaid-render found at $$(command -v mermaid-render)\n" \
	  || { printf "$(RED)FAIL$(RESET)  mermaid-render not found in PATH -- run: make install\n"; exit 1; }

##@ Docker

.PHONY: docker-shell
docker-shell: ## Open an interactive bash shell in the container with $PWD mounted at /data
	docker run --rm -it \
	  --volume $(PWD):/data \
	  --user mermaidcli \
	  $(DOCKER_EXTRA_ARGS) \
	  $(REMOTE):latest

##@ Info

.PHONY: example
example: ## Print cut-and-paste usage examples
	@printf "\n$(BOLD)Install onto your host$(RESET)\n"
	@printf "  docker run --rm $(REMOTE):latest install | sh\n"
	@printf "  docker run --rm $(REMOTE):latest uninstall | sh\n"
	@printf "\n$(BOLD)Render a markdown file:$(RESET)\n"
	@printf "  mermaid-render examples/example1.md\n"
	@printf "\n$(BOLD)Render as PNG:$(RESET)\n"
	@printf "  mermaid-render diagram.mmd -f png\n"
	@printf "\n"

##@ Legacy

.PHONY: doctor
doctor: ## Show environment info useful for bug reports
	@printf "$(BOLD)$(TOOL) doctor$(RESET)\n\n"
	@printf "  Shell:         %s\n" "$$SHELL"
	@printf "  Wrapper:       "; ls -lh "$(TOOL)" 2>/dev/null || printf "$(RED)not found$(RESET)\n"
	@printf "  Docker:        "; docker --version 2>/dev/null || printf "$(RED)not found$(RESET)\n"
	@printf "  Docker running: "; docker info >/dev/null 2>&1 && printf "$(GREEN)yes$(RESET)\n" || printf "$(RED)no$(RESET)\n"
	@printf "  $(TOOL) image: "; docker image inspect $(REMOTE):latest --format '{{.RepoTags}} ({{.Id}})' 2>/dev/null || printf "not pulled\n"
	@echo ""
