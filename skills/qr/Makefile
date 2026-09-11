BOLD   := \033[1m
RED    := \033[31m
GREEN  := \033[32m
CYAN   := \033[36m
YELLOW := \033[33m
RESET  := \033[0m

PROJECT  := qr
ZIP_DIR  := ../zipped/qr
ZIP_FILES := SKILL.md scripts docs resources assets

MAKEFLAGS += --no-print-directory

.DEFAULT_GOAL := help

.PHONY: help
help:  ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: zip-prep
zip-prep: ## Copy distributable files to ZIP_DIR (../zipped/qr) ready for zipping
	@printf "$(CYAN)Preparing zip staging dir:$(RESET) $(ZIP_DIR)\n"
	@/bin/rm -rf $(ZIP_DIR)
	@mkdir -p $(ZIP_DIR)
	@ok=0; fail=0; \
	for f in $(ZIP_FILES); do \
		if /bin/cp -R $$f $(ZIP_DIR)/ 2>/dev/null; then \
			printf "  $(GREEN)ok$(RESET)  $$f\n"; ok=$$((ok+1)); \
		else \
			printf "  $(RED)FAIL$(RESET)  $$f\n"; fail=$$((fail+1)); \
		fi \
	done; \
	printf "\n  $(BOLD)$$ok copied, $$fail failed$(RESET) -> $(ZIP_DIR)\n"; \
	[ $$fail -eq 0 ]

.PHONY: clean
clean: ## Remove zip staging directory
	@printf "$(CYAN)cleaning$(RESET) $(ZIP_DIR)...\n"
	@/bin/rm -rf $(ZIP_DIR)
	@printf "  $(GREEN)ok$(RESET)\n"
