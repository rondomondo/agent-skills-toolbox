# ============================================================
# cast2gif -- Makefile  (tool-specific; shared targets live in ../docker.mk)
# ============================================================

DEBUG  := false

# -- Paths ----------------------------------------------------
TOOL := cast2gif
CAST2GIF := $(TOOL)

IMAGE_SHELL ?= zsh
DOCKER_EXTRA_ARGS ?= --env DEBUG=$(DEBUG) --env USE_SHELL=$(IMAGE_SHELL)

IMAGE_REPO  := rondomondo/cast2gif
VERSION_ARG := CAST2GIF_VERSION
# The base image ghcr.io/asciinema/agg is published for linux/amd64 only; add linux/arm64 once it is.
PLATFORMS      := linux/amd64,linux/arm64
#PLATFORMS     := linux/amd64

include ../docker.mk

##@ cast2gif

.PHONY: cast2gif-usage
cast2gif-usage: ## Show cast2gif usage
	@bash $(CAST2GIF)

##@ Docker

.PHONY: docker-shell
docker-shell: ## Open an interactive zsh shell in the container with $PWD mounted at /data
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
	@printf "\n$(BOLD)Convert a cast file:$(RESET)\n"
	@printf "  cast2gif demo.cast\n"
	@printf "\n$(BOLD)Pass args straight to agg:$(RESET)\n"
	@printf "  cast2gif -- --help\n"
	@printf "\n"
