# ============================================================
# docker.mk -- shared by the docker tool Makefiles
# ============================================================
# Each <tool>/Makefile sets its variables, then includes this file:
#
#   TOOL           := pdf-strip                  binary name; also names the buildx builder
#   IMAGE_REPO     := rondomondo/pdf-strip       repository under $(REGISTRY)
#   VERSION_ARG    := PDF_STRIP_VERSION          Dockerfile ARG that receives $(VERSION)
#   include ../docker.mk
#
# Optional, set before the include:
#   BUILDER            buildx builder name (default $(TOOL)-builder)
#   PLATFORMS          buildx platforms (default linux/amd64,linux/arm64)
#   INSTALL_ASSETS     "src:name" pairs copied onto the host by `make install` (default $(TOOL):$(TOOL))
#   INSTALL_LINKS      extra names symlinked to the first asset
#   INSTALL_POST       shell snippet run after the assets are installed
#   CLEAN_ALL_EXTRA    extra targets for clean-all
#
# The tool Makefile supplies docker-shell, example and any tool-specific targets.
# `make sync-skill` copies this file next to the skill directories so ../docker.mk still resolves there.
.DEFAULT_GOAL := help
MAKEFLAGS     += --no-print-directory
SHELL         := /bin/bash

# Colours
BOLD   := \033[1m
GREEN  := \033[32m
CYAN   := \033[36m
RED    := \033[31m
YELLOW := \033[33m
RESET  := \033[0m

# Image and build config
REGISTRY    ?= ghcr.io
REMOTE      := $(REGISTRY)/$(IMAGE_REPO)
INSTALL_TAG ?= latest
VERSION      = $(shell cat VERSION 2>/dev/null | tr -d '[:space:]')
PLATFORMS   ?= linux/amd64,linux/arm64
BUILDER     ?= $(TOOL)-builder
NO_CACHE    ?= 0
CACHE_FLAG   = $(if $(filter 1,$(NO_CACHE)),--no-cache,)
CACHE_REF   := $(REMOTE):buildcache
REGISTRY_CACHE = --cache-from type=registry,ref=$(CACHE_REF) --cache-to type=registry,ref=$(CACHE_REF),mode=max,image-manifest=true,oci-mediatypes=true
# release bumps the patch version first, so the candidate for the next release is NEXT_VERSION-rc.<RC>
NEXT_VERSION = $(shell awk -F. '{printf "%d.%d.%d", $$1, $$2, $$3+1}' VERSION 2>/dev/null)
RC          ?= 1
RC_VERSION   = $(NEXT_VERSION)-rc.$(RC)
# Pre-release versions (containing a hyphen) must never move :latest
LATEST_TAG   = $(if $(findstring -,$(VERSION)),,--tag $(REMOTE):latest)
CHECK_VERSIONS := ../scripts/check-image-versions.sh

# Install defaults
INSTALL_ASSETS ?= $(TOOL):$(TOOL)
INSTALL_LINKS  ?=
INSTALL_POST   ?= true
INSTALL_PRIMARY = $(word 2,$(subst :, ,$(firstword $(INSTALL_ASSETS))))
INSTALLED_NAMES = $(foreach a,$(INSTALL_ASSETS),$(word 2,$(subst :, ,$(a)))) $(INSTALL_LINKS)
CLEAN_ALL_EXTRA ?=

# Help
# Scans the Makefiles for targets annotated with ## comments and prints a
# formatted usage table, grouped by ##@ section headers.
.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} \
	  /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0,5) } \
	  /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' \
	  $(filter %/docker.mk docker.mk,$(MAKEFILE_LIST)) $(filter-out %/docker.mk docker.mk,$(MAKEFILE_LIST))

##@ Install

.PHONY: install
install: ## Install the tool onto this host; tries /usr/local/bin (direct then sudo), falls back to ~/.local/bin
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
	for pair in $(INSTALL_ASSETS); do \
	  $$SUDO install -m 755 "$${pair%%:*}" "$$IDIR/$${pair##*:}"; \
	  printf "$(GREEN)Installed$(RESET) $$IDIR/$${pair##*:}\n"; \
	done; \
	for link in $(INSTALL_LINKS); do \
	  $$SUDO ln -sf "$$IDIR/$(INSTALL_PRIMARY)" "$$IDIR/$$link"; \
	  printf "$(GREEN)Linked$(RESET)     $$IDIR/$$link -> $$IDIR/$(INSTALL_PRIMARY)\n"; \
	done; \
	$(INSTALL_POST)

.PHONY: uninstall
uninstall: ## Remove the tool from /usr/local/bin and ~/.local/bin
	@for name in $(INSTALLED_NAMES); do \
	  for dir in /usr/local/bin "$$HOME/.local/bin"; do \
	    if [ -f "$$dir/$$name" ] || [ -L "$$dir/$$name" ]; then \
	      if rm -f "$$dir/$$name" 2>/dev/null || sudo rm -f "$$dir/$$name"; then \
	        printf "$(GREEN)Removed$(RESET)   $$dir/$$name\n"; \
	      fi; \
	    fi; \
	  done; \
	done

.PHONY: docker-install
docker-install: ## Install from the published image: docker run --rm $(REMOTE):$(INSTALL_TAG) install | sh
	docker run --rm $(REMOTE):$(INSTALL_TAG) install | sh

##@ Build

.PHONY: build
build: bump builder-init ## Build single-arch image for local testing (loads into Docker daemon). NO_CACHE=1 to bust cache.
	docker buildx build --builder $(BUILDER) --load $(CACHE_FLAG) --build-arg $(VERSION_ARG)=$(VERSION) -t $(REMOTE):$(VERSION) -t $(REMOTE):latest .
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

.PHONY: check-versions
check-versions: ## Verify the image version is baked into every shipped file that names the image
	@bash $(CHECK_VERSIONS) $(notdir $(CURDIR))

.PHONY: bump
bump: ## Increment patch version in VERSION file
	@old=$(VERSION); \
	new=$$(awk -F. '{printf "%d.%d.%d", $$1, $$2, $$3+1}' VERSION); \
	echo "$$new" > VERSION; \
	printf "$(GREEN)Bumped$(RESET) $$old -> $$new\n"

.PHONY: push
push: check-versions builder-init ## Build multi-platform image and push to ghcr.io (see PLATFORMS). NO_CACHE=1 to bust cache.
	docker buildx build \
	  --builder $(BUILDER) \
	  $(CACHE_FLAG) \
	  $(REGISTRY_CACHE) \
	  --build-arg $(VERSION_ARG)=$(VERSION) \
	  --platform $(PLATFORMS) \
	  --tag $(REMOTE):$(VERSION) \
	  $(LATEST_TAG) \
	  --push \
	  .
	@printf "$(GREEN)Pushed$(RESET) $(REMOTE):$(VERSION) $(if $(LATEST_TAG),and $(REMOTE):latest )($(PLATFORMS))\n"

.PHONY: release
release: bump push ## Bump patch version, build multi-platform, and push to ghcr.io

.PHONY: release-rc
release-rc: ## One-off: push the next release as NEXT-rc.RC (RC=1 by default) without bumping VERSION or moving :latest
	$(MAKE) push VERSION=$(RC_VERSION)

##@ Info

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
clean-all: clean clean-builder $(CLEAN_ALL_EXTRA) ## Run all clean targets
