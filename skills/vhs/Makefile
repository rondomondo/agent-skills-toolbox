# ============================================================
# vhs -- Makefile  (tool-specific; shared targets live in ../docker.mk)
# ============================================================

# -- Paths ----------------------------------------------------
TOOL := vhs-rec
VHS_REC := $(TOOL)
DEMO_SRC := vhs-demo.py
DEMO_TOOL := vhs-demo

IMAGE_SHELL ?= zsh
DOCKER_SOCK ?= /var/run/docker.sock
DOCKER_EXTRA_ARGS ?= --volume $(DOCKER_SOCK):$(DOCKER_SOCK) --env DOCKER_SOCK=$(DOCKER_SOCK) --env USE_SHELL=$(IMAGE_SHELL)

IMAGE_REPO  := rondomondo/vhs-rec
VERSION_ARG := VHS_REC_VERSION
INSTALL_ASSETS := $(TOOL):$(TOOL) $(DEMO_SRC):$(DEMO_TOOL)
INSTALL_POST   := command -v uv >/dev/null 2>&1 || printf "$(YELLOW)Warning$(RESET)   uv was not found on PATH -- $(DEMO_TOOL) needs it\n"

include ../docker.mk

##@ vhs-rec

# Invokes the vhs-rec script with no arguments, which prints its built-in
# usage/help text without starting a recording or pulling an image.
.PHONY: vhs-rec-usage
vhs-rec-usage: ## Show vhs-rec usage
	@bash $(VHS_REC)

##@ Test

.PHONY: test
test: ## Run the vhs-rec wrapper tests (no Docker needed)
	uv run pytest

##@ Docker

.PHONY: docker-shell
docker-shell: ## Open an interactive zsh shell in the container with $PWD mounted at /vhs
	docker run --rm -it \
	  --volume $(PWD):/vhs \
	  --user vhs \
	  $(DOCKER_EXTRA_ARGS) \
	  $(REMOTE):latest

##@ Info

.PHONY: example
example: ## Print cut-and-paste usage examples
	@printf "\n$(BOLD)Install onto your host$(RESET)\n"
	@printf "  docker run --rm $(REMOTE):latest install | sh\n"
	@printf "  docker run --rm $(REMOTE):latest uninstall | sh\n"
	@printf "\n$(BOLD)Record a tape:$(RESET)\n"
	@printf "  vhs-rec demo.tape\n"
	@printf "\n$(BOLD)Record without a tape (one shot):$(RESET)\n"
	@printf "  vhs-rec demo -o demo.gif --install pdf-strip --snippet -- pdf-strip --check a.pdf\n"
	@printf "\n"
