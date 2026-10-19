# ============================================================
# sanitise-ascii -- Makefile
# ============================================================
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
SANITISE      := sanitise-ascii
INSTALL_FILES := sanitise-ascii.py
LINK_NOEXT    := 1
SRCDIR        ?= .

# -- Help -----------------------------------------------------
.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} \
	  /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0,5) } \
	  /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)

##@ Install

.PHONY: install
install: ## Install sanitise-ascii; tries /usr/local/bin (direct then sudo), falls back to ~/.local/bin
	@USE_SUDO=0; \
	if install -m 755 /dev/null /usr/local/bin/.install_probe 2>/dev/null; then \
	  rm -f /usr/local/bin/.install_probe; \
	  IDIR=/usr/local/bin; \
	elif sudo install -m 755 /dev/null /usr/local/bin/.install_probe 2>/dev/null; then \
	  sudo rm -f /usr/local/bin/.install_probe; \
	  IDIR=/usr/local/bin; \
	  USE_SUDO=1; \
	else \
	  mkdir -p "$$HOME/.local/bin"; \
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
	for f in $(INSTALL_FILES); do \
	  base=$$(basename $$f); \
	  if [ "$$USE_SUDO" = "1" ]; then sudo install -m 755 $$f "$$IDIR/$$base"; else install -m 755 $$f "$$IDIR/$$base"; fi; \
	  printf "$(GREEN)Installed$(RESET) $$IDIR/$$base\n"; \
	  if [ "$(LINK_NOEXT)" = "1" ] && [ "$${base%.*}" != "$$base" ]; then \
	    if [ "$$USE_SUDO" = "1" ]; then sudo ln -sf "$$IDIR/$$base" "$$IDIR/$${base%.*}"; else ln -sf "$$IDIR/$$base" "$$IDIR/$${base%.*}"; fi; \
	    printf "$(GREEN)Linked$(RESET)    $$IDIR/$${base%.*} -> $$base\n"; \
	  fi; \
	done

.PHONY: uninstall
uninstall: ## Remove sanitise-ascii from /usr/local/bin and ~/.local/bin
	@for dir in /usr/local/bin "$$HOME/.local/bin"; do \
	  for f in $(INSTALL_FILES); do \
	    base=$$(basename $$f); \
	    for name in $$base $${base%.*}; do \
	      if [ -f "$$dir/$$name" ] || [ -L "$$dir/$$name" ]; then \
	        if rm -f "$$dir/$$name" 2>/dev/null || sudo rm -f "$$dir/$$name"; then \
	          printf "$(GREEN)Removed$(RESET)   $$dir/$$name\n"; \
	        fi; \
	      fi; \
	    done; \
	  done; \
	done

##@ Sanitise

# Invokes sanitise-ascii with --help, printing the full usage text that
# describes flags, supported file types, and exit codes.
.PHONY: usage
usage: ## Show sanitise-ascii usage
	@uv run python3 $(SANITISE).py --help

# Runs sanitise-ascii in check (dry-run) mode across all common text files
# in the repo root, reporting non-ASCII characters without modifying any files.
# Exits 1 if any non-ASCII characters are found.
.PHONY: check
check: ## Run sanitise-ascii --check on all text files in the repo root (default - no writes)
	@uv run python3 $(SANITISE).py --check --dir $(SRCDIR)

# Runs sanitise-ascii in fix mode, replacing known non-ASCII characters with
# ASCII equivalents in place. Characters not in the fix map are reported as
# WARNs and left for manual review; exits 1 if any remain after fixing.
.PHONY: fix
fix: ## Auto-fix non-ASCII in all text files in the repo root
	@uv run python3 $(SANITISE).py --fix --dir $(SRCDIR)

