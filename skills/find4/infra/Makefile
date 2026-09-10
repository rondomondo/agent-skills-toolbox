STATE_BUCKET        := find4-terraform-state
LOCAL_STATE_BUCKET  := find4-terraform-state-local
REGION              := us-east-1
AWS_PROFILE         ?= daveadmin
AWS_PROFILE_DEPLOYER ?= daveadmin
AWS_PAGER           :=
LOCALSTACK_ENDPOINT := http://localhost:4566
FLOCI_DIR           ?= $(shell git rev-parse --show-toplevel 2>/dev/null)/floci
export AWS_PAGER

BOLD  := \033[1m
GREEN := \033[32m
CYAN  := \033[36m
RED   := \033[31m
RESET := \033[0m

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# State bucket setup

.PHONY: state-bucket
state-bucket: check-deps ## Create and configure the S3 remote state bucket (run once, needs admin credentials)
	@printf "$(CYAN)creating state bucket$(RESET) $(STATE_BUCKET)...\n"
	AWS_PROFILE=$(AWS_PROFILE) aws s3api create-bucket --bucket $(STATE_BUCKET) --region $(REGION)
	AWS_PROFILE=$(AWS_PROFILE) aws s3api put-bucket-versioning --bucket $(STATE_BUCKET) --versioning-configuration Status=Enabled
	AWS_PROFILE=$(AWS_PROFILE) aws s3api put-bucket-encryption --bucket $(STATE_BUCKET) --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
	@printf "$(GREEN)ok$(RESET)  state bucket ready\n"

# Guards

.PHONY: check-deps
check-deps:
	@command -v tofu >/dev/null 2>&1 || { printf "$(RED)error$(RESET)  opentofu not found - install from https://opentofu.org/docs/intro/install/\n"; exit 1; }
	@command -v aws >/dev/null 2>&1 || { printf "$(RED)error$(RESET)  aws cli not found - install from https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html\n"; exit 1; }

# Core tofu workflow

.PHONY: init
init: check-deps ## Initialise OpenTofu and connect to remote state
	AWS_PROFILE=$(AWS_PROFILE) tofu init

.PHONY: plan
plan: check-deps ## Show what tofu will create/change/destroy
	AWS_PROFILE=$(AWS_PROFILE) tofu plan

.PHONY: apply
apply: check-deps ## Apply the plan (prompts for confirmation)
	AWS_PROFILE=$(AWS_PROFILE) tofu apply

.PHONY: destroy
destroy: check-deps ## Destroy all managed resources (prompts for confirmation)
	AWS_PROFILE=$(AWS_PROFILE) tofu destroy

# Credential helpers

.PHONY: show-credentials
show-credentials: ## Print the deployer access key ID and secret (add both to GitHub secrets)
	@printf "\n$(BOLD)AWS_ACCESS_KEY_ID$(RESET)\n"
	@AWS_PROFILE=$(AWS_PROFILE) tofu output deployer_access_key_id
	@printf "\n$(BOLD)AWS_SECRET_ACCESS_KEY$(RESET)\n"
	@AWS_PROFILE=$(AWS_PROFILE) tofu output -raw deployer_secret_access_key
	@printf "\n"

.PHONY: show-url
show-url: ## Print the S3 and CloudFront URLs
	@printf "\n$(BOLD)S3$(RESET)\n"
	@AWS_PROFILE=$(AWS_PROFILE) tofu output website_url
	@printf "\n$(BOLD)CloudFront$(RESET)\n"
	@AWS_PROFILE=$(AWS_PROFILE) tofu output cloudfront_url
	@printf "\n"

# State surgery

.PHONY: state-rm-user
state-rm-user: check-deps ## Remove stale managed IAM user from state (run once after switching to data source)
	AWS_PROFILE=$(AWS_PROFILE) tofu state rm aws_iam_user.deployer

# Convenience

.PHONY: setup
setup: state-bucket init ## Bootstrap from scratch: create state bucket then init (needs admin credentials)
	@printf "\n$(GREEN)Ready.$(RESET) Run $(CYAN)make plan$(RESET) next.\n"

.PHONY: fmt
fmt: ## Format all .tf files
	AWS_PROFILE=$(AWS_PROFILE) tofu fmt

.PHONY: validate
validate: ## Validate configuration without connecting to AWS
	AWS_PROFILE=$(AWS_PROFILE) tofu validate

# LocalStack simulation targets
# Requires: docker compose up -d  (from /Users/davek/Code/floci/)
# Simulates: S3 + IAM only. CloudFront, ACM, Route53 need LocalStack Pro.

LOCAL_INFRA_SRC := /Users/davek/Code/floci
LOCAL_WD        := /tmp/find4-local-infra

.PHONY: check-localstack
check-localstack: ## Check LocalStack is running
	@curl -sf $(LOCALSTACK_ENDPOINT)/_localstack/health | grep -q '"s3"' \
		|| { printf "$(RED)error$(RESET)  LocalStack not running - cd $(LOCAL_INFRA_SRC) && docker compose up -d\n"; exit 1; }
	@printf "$(GREEN)ok$(RESET)  LocalStack is up\n"

.PHONY: local-state-bucket
local-state-bucket: check-localstack ## Create the local state bucket in LocalStack (run once per LocalStack restart)
	@printf "$(CYAN)creating$(RESET) local state bucket $(LOCAL_STATE_BUCKET)...\n"
	@AWS_ENDPOINT_URL=$(LOCALSTACK_ENDPOINT) \
	 AWS_ACCESS_KEY_ID=mock-key AWS_SECRET_ACCESS_KEY=mock-secret \
	 aws s3api create-bucket --bucket $(LOCAL_STATE_BUCKET) --region $(REGION) 2>/dev/null || true
	@printf "$(GREEN)ok$(RESET)  local state bucket ready\n"

.PHONY: local-init
local-init: check-deps check-localstack local-state-bucket ## Init tofu against LocalStack (copies sim files into a temp workspace)
	@printf "$(CYAN)preparing$(RESET) local workspace at $(LOCAL_WD)...\n"
	@rm -rf $(LOCAL_WD) && mkdir -p $(LOCAL_WD)
	@cp $(LOCAL_INFRA_SRC)/provider-local-override.tf $(LOCAL_WD)/
	@cp $(LOCAL_INFRA_SRC)/local-infra.tf $(LOCAL_WD)/
	@cp $(LOCAL_INFRA_SRC)/backend-local.tfvars $(LOCAL_WD)/
	@printf 'terraform {\n  required_version = ">= 1.6.0"\n  required_providers {\n    aws = { source = "hashicorp/aws", version = "~> 5.0" }\n  }\n  backend "s3" {}\n}\n' > $(LOCAL_WD)/versions.tf
	@cd $(LOCAL_WD) && \
	 AWS_ENDPOINT_URL=$(LOCALSTACK_ENDPOINT) \
	 AWS_ACCESS_KEY_ID=mock-key AWS_SECRET_ACCESS_KEY=mock-secret \
	 tofu init -backend-config=backend-local.tfvars -reconfigure
	@printf "$(GREEN)ok$(RESET)  local workspace ready at $(LOCAL_WD)\n"
	@printf "     Run $(CYAN)make local-plan$(RESET) next.\n"

.PHONY: local-plan
local-plan: check-localstack ## Plan against LocalStack
	@cd $(LOCAL_WD) && \
	 AWS_ENDPOINT_URL=$(LOCALSTACK_ENDPOINT) \
	 AWS_ACCESS_KEY_ID=mock-key AWS_SECRET_ACCESS_KEY=mock-secret \
	 tofu plan

.PHONY: local-apply
local-apply: check-localstack ## Apply against LocalStack
	@cd $(LOCAL_WD) && \
	 AWS_ENDPOINT_URL=$(LOCALSTACK_ENDPOINT) \
	 AWS_ACCESS_KEY_ID=mock-key AWS_SECRET_ACCESS_KEY=mock-secret \
	 tofu apply -auto-approve

.PHONY: local-destroy
local-destroy: check-localstack ## Destroy all local resources in LocalStack
	@cd $(LOCAL_WD) && \
	 AWS_ENDPOINT_URL=$(LOCALSTACK_ENDPOINT) \
	 AWS_ACCESS_KEY_ID=mock-key AWS_SECRET_ACCESS_KEY=mock-secret \
	 tofu destroy -auto-approve
	@printf "$(GREEN)ok$(RESET)  local resources destroyed\n"

.PHONY: local-show-credentials
local-show-credentials: ## Print the local deployer credentials from LocalStack state
	@printf "\n$(BOLD)AWS_ACCESS_KEY_ID$(RESET)\n"
	@cd $(LOCAL_WD) && \
	 AWS_ENDPOINT_URL=$(LOCALSTACK_ENDPOINT) \
	 AWS_ACCESS_KEY_ID=mock-key AWS_SECRET_ACCESS_KEY=mock-secret \
	 tofu output local_deployer_access_key_id
	@printf "\n$(BOLD)AWS_SECRET_ACCESS_KEY$(RESET)\n"
	@cd $(LOCAL_WD) && \
	 AWS_ENDPOINT_URL=$(LOCALSTACK_ENDPOINT) \
	 AWS_ACCESS_KEY_ID=mock-key AWS_SECRET_ACCESS_KEY=mock-secret \
	 tofu output -raw local_deployer_secret_access_key
	@printf "\n"

.PHONY: local-show-url
local-show-url: ## Print the local S3 website URL
	@cd $(LOCAL_WD) && \
	 AWS_ENDPOINT_URL=$(LOCALSTACK_ENDPOINT) \
	 AWS_ACCESS_KEY_ID=mock-key AWS_SECRET_ACCESS_KEY=mock-secret \
	 tofu output local_website_url

.PHONY: local-setup
local-setup: local-init local-apply ## Full local bootstrap: init + apply in one step
	@printf "\n$(GREEN)Local simulation ready.$(RESET)\n"
	@printf "  URL:  http://localhost:4566/find4-webapp/index.html\n"
	@printf "  Creds: $(CYAN)make local-show-credentials$(RESET)\n"
