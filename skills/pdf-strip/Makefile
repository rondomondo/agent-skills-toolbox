# ============================================================
# pdf-strip -- Makefile  (tool-specific; shared targets live in ../docker.mk)
# ============================================================

DEBUG  := false

# -- Paths ----------------------------------------------------
TOOL := pdf-strip
PDF_STRIP := $(TOOL)

IMAGE_SHELL ?= bash
DOCKER_EXTRA_ARGS ?= --env DEBUG=$(DEBUG) --env USE_SHELL=$(IMAGE_SHELL)

TEST_PDF := $(CURDIR)/test/example.pdf

IMAGE_REPO  := rondomondo/pdf-strip
VERSION_ARG := PDF_STRIP_VERSION

include ../docker.mk

##@ Python / uv

.PHONY: venv
venv: ## Create .venv and install pikepdf via uv (local dev, non-sandbox)
	uv sync
	@printf "$(GREEN)venv ready$(RESET) -- activate with: source .venv/bin/activate\n"

.PHONY: run
run: ## Run strip.py directly via uv (auto-installs deps from inline script metadata)
	uv run strip.py

.PHONY: check-uv
check-uv: ## Verify uv is available
	@command -v uv >/dev/null 2>&1 || { printf "$(RED)uv not found$(RESET) -- install from https://docs.astral.sh/uv/\n" >&2; exit 1; }
	@printf "$(GREEN)uv found$(RESET): $$(uv --version)\n"

##@ pdf-strip

.PHONY: pdf-strip-usage
pdf-strip-usage: ## Show pdf-strip script usage
	@bash $(PDF_STRIP) --help

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
	@printf "\n$(BOLD)Strip all PDFs in a directory:$(RESET)\n"
	@printf "  pdf-strip /path/to/dir\n"
	@printf "\n$(BOLD)Strip one or more files:$(RESET)\n"
	@printf "  pdf-strip file.pdf\n"
	@printf "  pdf-strip file1.pdf file2.pdf\n"
	@printf "\n$(BOLD)Check PDFs for metadata (no stripping):$(RESET)\n"
	@printf "  pdf-strip --check file.pdf\n"
	@printf "  pdf-strip --check /path/to/dir\n"
	@printf "\n"
