# =================================================================
# mermaid-render -- Makefilem(Docker image + mermaid-render wrapper)
# =================================================================
.DEFAULT_GOAL := help
MAKEFLAGS     += --no-print-directory
SHELL         := /bin/bash

# -- Colors ---------------------------------------------------
BOLD   := \033[1m
GREEN  := \033[32m
CYAN   := \033[36m
YELLOW := \033[33m
RESET  := \033[0m

# -- Paths ----------------------------------------------------
TOOL := mermaid-render

# -- Image & Build Config -------------------------------------
REGISTRY   ?= ghcr.io
IMAGE_REPO := rondomondo/mermaid-render
REMOTE     := $(REGISTRY)/$(IMAGE_REPO)
INSTALL_TAG ?= latest
VERSION     = $(shell cat VERSION 2>/dev/null | tr -d '[:space:]')
PLATFORMS  := linux/amd64,linux/arm64
#PLATFORMS  := linux/amd64
BUILDER    := mermaid-render-builder
NO_CACHE   ?= 0
CACHE_FLAG  = $(if $(filter 1,$(NO_CACHE)),--no-cache,)
CACHE_REF   := $(REMOTE):buildcache
REGISTRY_CACHE = --cache-from type=registry,ref=$(CACHE_REF) --cache-to type=registry,ref=$(CACHE_REF),mode=max,image-manifest=true,oci-mediatypes=true
RC_VERSION  = $(VERSION)-rc.1
# Pre-release versions (containing a hyphen) must never move :latest
LATEST_TAG  = $(if $(findstring -,$(VERSION)),,--tag $(REMOTE):latest)
IMAGE_SHELL ?= bash
DOCKER_EXTRA_ARGS ?= --env DEBUG=false --env USE_SHELL=$(IMAGE_SHELL)

# -- Test -----------------------------------------------------
TEST_INPUT     ?= examples/example1.md

# -- Help -----------------------------------------------------
.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} \
	  /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0,5) } \
	  /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)

##@ Install

.PHONY: install
install: ## Install mermaid-render; tries /usr/local/bin (direct then sudo), falls back to ~/.local/bin
	@if install -m 755 $(TOOL) /usr/local/bin/$(TOOL) 2>/dev/null; then \
	  IDIR=/usr/local/bin; \
	elif sudo install -m 755 $(TOOL) /usr/local/bin/$(TOOL) 2>/dev/null; then \
	  IDIR=/usr/local/bin; \
	else \
	  mkdir -p "$$HOME/.local/bin"; \
	  install -m 755 $(TOOL) "$$HOME/.local/bin/$(TOOL)"; \
	  IDIR="$$HOME/.local/bin"; \
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
	printf "$(GREEN)Installed$(RESET) $$IDIR/$(TOOL)\n"

.PHONY: docker-install
docker-install: ## Install from the published image: docker run --rm $(REMOTE):$(INSTALL_TAG) install | sh
	docker run --rm $(REMOTE):$(INSTALL_TAG) install | sh

.PHONY: uninstall
uninstall: ## Remove mermaid-render from /usr/local/bin and ~/.local/bin
	@for dir in /usr/local/bin "$$HOME/.local/bin"; do \
	  if [ -f "$$dir/$(TOOL)" ] || [ -L "$$dir/$(TOOL)" ]; then \
	    if rm -f "$$dir/$(TOOL)" 2>/dev/null || sudo rm -f "$$dir/$(TOOL)"; then \
	      printf "$(GREEN)Removed$(RESET)   $$dir/$(TOOL)\n"; \
	    fi; \
	  fi; \
	done

##@ mermaid-render

.PHONY: mermaid-render-usage
mermaid-render-usage: ## Show mermaid-render usage
	@bash $(SKILL_NAME)

.PHONY: test
test: ## Render TEST_INPUT as SVG and PNG to verify the full pipeline (override: TEST_INPUT=examples/foo.md)
	@printf "$(BOLD)$(CYAN)--- SVG render ---$(RESET)\n"
	@bash $(SKILL_NAME) $(TEST_INPUT) --scale 2 -f svg
	@printf "$(BOLD)$(CYAN)--- PNG render ---$(RESET)\n"
	@bash $(SKILL_NAME) $(TEST_INPUT) --scale 2 -f png --width 960 --height 640
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

##@ Build

.PHONY: build
build: bump builder-init ## Build single-arch image for local testing (loads into Docker daemon). NO_CACHE=1 to bust cache.
	docker buildx build --builder $(BUILDER) --load $(CACHE_FLAG) --build-arg MERMAID_RENDER_VERSION=$(VERSION) -t $(REMOTE):$(VERSION) -t $(REMOTE):latest .
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
	  --build-arg MERMAID_RENDER_VERSION=$(VERSION) \
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

.PHONY: size
size: ## Show local image sizes
	@docker images $(REMOTE) --format "table {{.Tag}}\t{{.Size}}\t{{.ID}}" | head -10

.PHONY: version
version: ## Print current version
	@echo $(VERSION)

.PHONY: inspect
inspect: ## Show manifest platforms for the remote :latest image
	docker buildx imagetools inspect $(REMOTE):latest

##@ Legacy

.PHONY: doctor
doctor: ## Show environment info useful for bug reports
	@printf "$(BOLD)$(SKILL_NAME) doctor$(RESET)\n\n"
	@printf "  Shell:         %s\n" "$$SHELL"
	@printf "  Wrapper:       "; ls -lh "$(SKILL_NAME)" 2>/dev/null || printf "$(RED)not found$(RESET)\n"
	@printf "  Docker:        "; docker --version 2>/dev/null || printf "$(RED)not found$(RESET)\n"
	@printf "  Docker running: "; docker info >/dev/null 2>&1 && printf "$(GREEN)yes$(RESET)\n" || printf "$(RED)no$(RESET)\n"
	@printf "  $(SKILL_NAME) image: "; docker image inspect $(REMOTE_IMAGE):latest --format '{{.RepoTags}} ({{.Id}})' 2>/dev/null || printf "not pulled\n"
	@echo ""

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
clean-all: clean clean-builder clean-output ## Run all clean targets
