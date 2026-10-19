# ============================================================
# filetree -- Makefile
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
SCRIPT        := filetree
INSTALL_FILES := filetree.sh
LINK_NOEXT    := 1

# -- Help -----------------------------------------------------
.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} \
	  /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0,5) } \
	  /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)

##@ Install

.PHONY: install
install: ## Install filetree; tries /usr/local/bin (direct then sudo), falls back to ~/.local/bin
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
uninstall: ## Remove filetree from /usr/local/bin and ~/.local/bin
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

##@ Usage

.PHONY: usage
usage: ## Show filetree usage
	@bash $(SCRIPT).sh --help

