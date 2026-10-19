# ============================================================
# vhs -- Makefile  (Docker image + vhs-rec wrapper)
# ============================================================
.DEFAULT_GOAL := help
MAKEFLAGS     += --no-print-directory
SHELL         := /bin/bash

# -- Colors ---------------------------------------------------
BOLD   := \033[1m
GREEN  := \033[32m
CYAN   := \033[36m
RED    := \033[31m
YELLOW := \033[33m
RESET  := \033[0m

# -- Paths ----------------------------------------------------
TOOL := vhs-rec
VHS_REC := $(TOOL)
DEMO_SRC := vhs-demo.py
DEMO_TOOL := vhs-demo

# -- Image & Build Config -------------------------------------
REGISTRY   ?= ghcr.io
IMAGE_REPO := rondomondo/vhs-rec
REMOTE     := $(REGISTRY)/$(IMAGE_REPO)
INSTALL_TAG ?= latest
VERSION     = $(shell cat VERSION 2>/dev/null | tr -d '[:space:]')
PLATFORMS  := linux/amd64,linux/arm64
#PLATFORMS  := linux/amd64
BUILDER    := vhs-rec-builder
NO_CACHE   ?= 0
CACHE_FLAG  = $(if $(filter 1,$(NO_CACHE)),--no-cache,)
CACHE_REF   := $(REMOTE):buildcache
REGISTRY_CACHE = --cache-from type=registry,ref=$(CACHE_REF) --cache-to type=registry,ref=$(CACHE_REF),mode=max,image-manifest=true,oci-mediatypes=true
RC_VERSION  = $(VERSION)-rc.1
# Pre-release versions (containing a hyphen) must never move :latest
LATEST_TAG  = $(if $(findstring -,$(VERSION)),,--tag $(REMOTE):latest)
IMAGE_SHELL ?= zsh
DOCKER_SOCK ?= /var/run/docker.sock
DOCKER_EXTRA_ARGS ?= --volume $(DOCKER_SOCK):$(DOCKER_SOCK) --env DOCKER_SOCK=$(DOCKER_SOCK) --env USE_SHELL=$(IMAGE_SHELL)

# -- Help -----------------------------------------------------
# Scans this Makefile for targets annotated with ## comments and prints a
# formatted usage table, grouped by ##@ section headers.
.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} \
	  /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0,5) } \
	  /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)

##@ Install

.PHONY: install
install: ## Install vhs-rec and vhs-demo; tries /usr/local/bin (direct then sudo), falls back to ~/.local/bin
	@if install -m 755 /dev/null /usr/local/bin/.install_probe 2>/dev/null; then \
	  rm -f /usr/local/bin/.install_probe; IDIR=/usr/local/bin; SUDO=; \
	elif sudo install -m 755 /dev/null /usr/local/bin/.install_probe 2>/dev/null; then \
	  sudo rm -f /usr/local/bin/.install_probe; IDIR=/usr/local/bin; SUDO=sudo; \
	else \
	  mkdir -p "$$HOME/.local/bin"; IDIR="$$HOME/.local/bin"; SUDO=; \
	  case ":$$PATH:" in \
	    *":$$IDIR:"*) ;; \
	    *) RCFILE=""; \
	       case "$${SHELL##*/}" in \
	         zsh)  RCFILE="$$HOME/.zshrc" ;; \
	         bash) RCFILE="$$HOME/.bashrc" ;; \
	         fish) RCFILE="$$HOME/.config/fish/config.fish" ;; \
	       esac; \
	       if [ -n "$$RCFILE" ]; then \
	         if ! grep -qF "$$IDIR" "$$RCFILE" 2>/dev/null; then \
	           mkdir -p "$$(dirname "$$RCFILE")"; \
	           case "$$RCFILE" in \
	             */config.fish) printf '\nfish_add_path "%s"\n' "$$IDIR" >> "$$RCFILE" ;; \
	             *) printf '\nexport PATH="%s:$$PATH"\n' "$$IDIR" >> "$$RCFILE" ;; \
	           esac; \
	           printf "$(GREEN)Added$(RESET)     $$IDIR to PATH in $$RCFILE\n"; \
	           printf "$(YELLOW)Restart$(RESET)   your shell or run: source $$RCFILE\n"; \
	         else \
	           printf "$(CYAN)Skipped$(RESET)   $$IDIR already referenced in $$RCFILE\n"; \
	         fi; \
	       else \
	         printf "$(YELLOW)Warning$(RESET)   $$IDIR is not on PATH -- add: export PATH=\"$$IDIR:\$$PATH\"\n"; \
	       fi ;; \
	  esac; \
	fi; \
	$$SUDO install -m 755 $(TOOL) "$$IDIR/$(TOOL)"; \
	printf "$(GREEN)Installed$(RESET) $$IDIR/$(TOOL)\n"; \
	$$SUDO install -m 755 $(DEMO_SRC) "$$IDIR/$(DEMO_TOOL)"; \
	printf "$(GREEN)Installed$(RESET) $$IDIR/$(DEMO_TOOL)\n"; \
	command -v uv >/dev/null 2>&1 || printf "$(YELLOW)Warning$(RESET)   uv was not found on PATH -- $(DEMO_TOOL) needs it\n"

.PHONY: docker-install
docker-install: ## Install from the published image: docker run --rm $(REMOTE):$(INSTALL_TAG) install | sh
	docker run --rm $(REMOTE):$(INSTALL_TAG) install | sh

.PHONY: uninstall
uninstall: ## Remove vhs-rec and vhs-demo from /usr/local/bin and ~/.local/bin
	@for name in $(TOOL) $(DEMO_TOOL); do \
	  for dir in /usr/local/bin "$$HOME/.local/bin"; do \
	    if [ -f "$$dir/$$name" ] || [ -L "$$dir/$$name" ]; then \
	      if rm -f "$$dir/$$name" 2>/dev/null || sudo rm -f "$$dir/$$name"; then \
	        printf "$(GREEN)Removed$(RESET)   $$dir/$$name\n"; \
	      fi; \
	    fi; \
	  done; \
	done

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

##@ Build

.PHONY: build
build: bump builder-init ## Build single-arch image for local testing (loads into Docker daemon). NO_CACHE=1 to bust cache.
	docker buildx build --builder $(BUILDER) --load $(CACHE_FLAG) --build-arg VHS_REC_VERSION=$(VERSION) -t $(REMOTE):$(VERSION) -t $(REMOTE):latest .
	@printf "$(GREEN)Built$(RESET) $(REMOTE):$(VERSION) and $(REMOTE):latest (local arch only)\n"

.PHONY: builder-init
builder-init: ## Create/reuse the multi-platform buildx builder
	@if ! docker buildx inspect $(BUILDER) >/dev/null 2>&1; then \
	  docker buildx create --name $(BUILDER) --driver docker-container --bootstrap; \
	  printf "$(GREEN)Created$(RESET) buildx builder: $(BUILDER)\n"; \
	else \
	  printf "$(CYAN)Reusing$(RESET) buildx builder: $(BUILDER)\n"; \
	fi

##@ Release

.PHONY: bump
bump: ## Increment patch version in VERSION file
	@old=$(VERSION); \
	new=$$(awk -F. '{printf "%d.%d.%d", $$1, $$2, $$3+1}' VERSION); \
	echo "$$new" > VERSION; \
	printf "$(GREEN)Bumped$(RESET) $$old -> $$new\n"

.PHONY: push
push: builder-init ## Build multi-platform image and push to ghcr.io (amd64 + arm64). NO_CACHE=1 to bust cache.
	docker buildx build \
	  --builder $(BUILDER) \
	  $(CACHE_FLAG) \
	  $(REGISTRY_CACHE) \
	  --build-arg VHS_REC_VERSION=$(VERSION) \
	  --platform $(PLATFORMS) \
	  --tag $(REMOTE):$(VERSION) \
	  $(LATEST_TAG) \
	  --push \
	  .
	@printf "$(GREEN)Pushed$(RESET) $(REMOTE):$(VERSION) $(if $(LATEST_TAG),and $(REMOTE):latest )($(PLATFORMS))\n"

.PHONY: release
release: bump push ## Bump patch version, build multi-platform, and push to ghcr.io

.PHONY: release-rc
release-rc: ## One-off: push $(RC_VERSION) to ghcr.io without bumping VERSION or moving :latest
	$(MAKE) push VERSION=$(RC_VERSION)

.PHONY: retag
retag: ## Re-tag an existing remote image without pulling: make retag FROM=latest TAG=v0.1.1
	@if [ -z "$(FROM)" ] || [ -z "$(TAG)" ]; then \
	  printf "$(RED)Error: FROM and TAG are required. Usage: make retag FROM=latest TAG=v0.1.1$(RESET)\n"; \
	  exit 1; \
	fi
	docker buildx imagetools create -t $(REMOTE):$(TAG) $(REMOTE):$(FROM)
	@printf "$(GREEN)Retagged$(RESET) $(REMOTE):$(FROM) -> $(REMOTE):$(TAG)\n"

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

.PHONY: size
size: ## Show local image sizes
	@docker images $(REMOTE) --format "table {{.Tag}}\t{{.Size}}\t{{.ID}}" | head -10

.PHONY: version
version: ## Print current version
	@echo $(VERSION)

.PHONY: inspect
inspect: ## Show manifest platforms for the remote :latest image
	docker buildx imagetools inspect $(REMOTE):latest

##@ Cleanup

.PHONY: clean
clean: ## Remove local image tags for this image
	@for tag in "$(REMOTE):$(VERSION)" "$(REMOTE):latest"; do \
	  if docker image inspect "$$tag" >/dev/null 2>&1; then \
	    docker rmi "$$tag" && printf "$(GREEN)Removed$(RESET) $$tag\n"; \
	  else \
	    printf "$(YELLOW)Not found$(RESET)  $$tag\n"; \
	  fi; \
	done

.PHONY: clean-builder
clean-builder: ## Remove the buildx builder instance
	@docker buildx rm $(BUILDER) 2>/dev/null && \
	  printf "$(GREEN)Removed$(RESET) builder: $(BUILDER)\n" || \
	  printf "$(YELLOW)Not found$(RESET)  builder: $(BUILDER)\n"

.PHONY: clean-all
clean-all: clean clean-builder ## Run all clean targets
