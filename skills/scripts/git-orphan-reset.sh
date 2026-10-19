#!/usr/bin/env bash
# =============================================================================
# git-orphan-reset.sh
#
# Wipes all commit history from a local git repo and pushes a single
# "chore: Initial commit" tagged at v0.1.0.  Safe to run multiple times
# (idempotent).
#
# Usage:
#   git-orphan-reset.sh [--no-verify] [/path/to/repo]
#
#   --no-verify  Skip pre-commit hooks on the orphan commit.
#   If no path is given the current working directory is used.
#
# What it does:
#   1. Validates the target is a git repo with a remote.
#   2. Checks that every tracked file is committed (no dirty state).
#   3. Checks that the local branch is fully pushed to its remote tracking
#      branch (no unpushed commits).
#   4. Asks one explicit yes/no confirmation question before destructive work.
#   5. Creates an orphan branch, stages all files, makes a single commit
#      tagged v0.1.0.
#   6. Force-pushes the orphan branch and the tag to origin.
#   7. Cleans up the temporary orphan branch.
#
# Idempotency:
#   - If the repo already has exactly one commit whose message starts with
#     "chore: Initial commit" AND the tag v0.1.0 already exists on origin, the
#     script reports success and exits 0 without touching anything.
#
# Requirements: git, awk, sed (standard POSIX tools only)
# =============================================================================

set -euo pipefail

# -- colour helpers ------------------------------------------------------------
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { printf "${CYAN}[INFO]${RESET}  %s\n" "$*"; }
success() { printf "${GREEN}[OK]${RESET}    %s\n" "$*"; }
warn()    { printf "${YELLOW}[WARN]${RESET}  %s\n" "$*"; }
die()     { printf "${RED}[ERROR]${RESET} %s\n" "$*" >&2; exit 1; }
banner()  { printf "\n${BOLD}%s${RESET}\n%s\n" "$1" "$(printf '%0.s-' $(seq 1 ${#1}))"; }

# -- helpers -------------------------------------------------------------------
require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

confirm() {
  # $1 = prompt  Returns 0 for yes, 1 for no
  local answer
  printf "\n${BOLD}${YELLOW}[!] CONFIRMATION REQUIRED${RESET}\n"
  printf "%s\n" "$1"
  printf "${BOLD}Type exactly 'yes' to proceed, anything else to abort: ${RESET}"
  read -r answer
  [[ "$answer" == "yes" ]]
}

# -- main ----------------------------------------------------------------------
main() {
  require_cmd git

  # -- parse flags ----------------------------------------------------------
  local no_verify=false
  local args=()
  for arg in "$@"; do
    case "$arg" in
      --no-verify) no_verify=true ;;
      *) args+=("$arg") ;;
    esac
  done
  set -- "${args[@]+"${args[@]}"}"

  # -- resolve target directory ---------------------------------------------
  local repo_path="${1:-.}"
  repo_path="$(cd "$repo_path" 2>/dev/null || die "Directory not found: $repo_path"; pwd)"

  banner "git-orphan-reset  ->  $repo_path"

  cd "$repo_path"

  # -- 1. is this actually a git repo? --------------------------------------
  git rev-parse --git-dir >/dev/null 2>&1 \
    || die "Not a git repository: $repo_path"
  success "Git repository confirmed"

  # -- 2. capture key state -------------------------------------------------
  local current_branch remote remote_url
  current_branch="$(git symbolic-ref --short HEAD 2>/dev/null \
    || die "HEAD is detached. Checkout a branch first.")"
  info "Current branch : $current_branch"

  remote="$(git remote 2>/dev/null | head -1)"
  [[ -n "$remote" ]] || die "No git remote configured. Add one first."
  info "Remote         : $remote"

  remote_url="$(git remote get-url "$remote" 2>/dev/null)"
  info "Remote URL     : $remote_url"

  # -- 3. idempotency check -------------------------------------------------
  local commit_count
  commit_count="$(git rev-list --count HEAD 2>/dev/null || echo 0)"

  local first_msg=""
  if [[ "$commit_count" -ge 1 ]]; then
    first_msg="$(git log --oneline | tail -1 | cut -d' ' -f2-)"
  fi

  local remote_tag_exists=false
  git fetch --tags --quiet 2>/dev/null || true
  if git tag -l "v0.1.0" | grep -q "v0.1.0"; then
    remote_tag_exists=true
  fi

  if [[ "$commit_count" -eq 1 \
        && "$first_msg" == "chore: Initial commit"* \
        && "$remote_tag_exists" == "true" ]]; then
    success "Repo is already in the target state (single 'chore: Initial commit', tag v0.1.0 exists)."
    success "Nothing to do -- exiting cleanly."
    exit 0
  fi

  # -- 4. check for uncommitted changes -------------------------------------
  local dirty=""
  dirty="$(git status --porcelain 2>/dev/null)"
  if [[ -n "$dirty" ]]; then
    warn "Uncommitted changes detected:"
    git status --short
    die "Commit or stash all changes before running this script."
  fi
  success "Working tree is clean"

  # -- 5. check for unpushed commits ----------------------------------------
  local tracking
  tracking="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"

  if [[ -z "$tracking" ]]; then
    warn "No upstream tracking branch set for '$current_branch'."
    warn "Skipping unpushed-commit check (no remote tracking branch)."
  else
    git fetch "$remote" --quiet 2>/dev/null || true

    local unpushed
    unpushed="$(git log "${tracking}..HEAD" --oneline 2>/dev/null || true)"
    if [[ -n "$unpushed" ]]; then
      warn "Unpushed commits found:"
      echo "$unpushed"
      die "Push all commits before orphaning. Run: git push $remote $current_branch"
    fi
    success "All commits are pushed to $tracking"
  fi

  # -- 6. summary before confirmation ---------------------------------------
  printf "\n${BOLD}Summary of what will happen:${RESET}\n"
  printf "  - All %s commit(s) on branch '%s' will be erased\n" "$commit_count" "$current_branch"
  printf "  - Current file tree will be preserved in a brand-new orphan commit\n"
  printf "  - Commit message  : 'chore: Initial commit'\n"
  printf "  - Version tag     : v0.1.0\n"
  printf "  - Force-pushed to : %s / %s\n" "$remote" "$current_branch"
  printf "  - This is IRREVERSIBLE once pushed (history is gone from remote)\n"
  printf "  - Remote URL      : %s\n\n" "$remote_url"

  # -- 7. THE confirmation question -----------------------------------------
  confirm "You are about to PERMANENTLY DELETE all git history for the repository
  '$repo_path' and push a single orphan 'chore: Initial commit' tagged v0.1.0
  to remote '$remote' ($remote_url).

  Are you absolutely sure you want to orphan this repository and erase all history?" \
    || { warn "Aborted by user. Nothing was changed."; exit 0; }

  # -- 8. destructive work begins -------------------------------------------
  banner "Executing orphan reset"

  local orphan_branch="__orphan_reset_tmp__"

  # Clean up any leftover orphan branch from a previous failed run
  if git show-ref --verify --quiet "refs/heads/$orphan_branch" 2>/dev/null; then
    info "Removing stale orphan branch from a previous run..."
    git branch -D "$orphan_branch"
  fi

  info "Creating orphan branch '$orphan_branch'..."
  git checkout --orphan "$orphan_branch"

  info "Staging all files..."
  git add -A

  info "Creating chore: Initial commit..."
  local commit_flags=(--allow-empty -m "chore: Initial commit")
  [[ "$no_verify" == true ]] && commit_flags+=(--no-verify)
  git commit "${commit_flags[@]}"

  # -- 9. remove old tag if it exists locally -------------------------------
  if git tag -l "v0.1.0" | grep -q "v0.1.0"; then
    info "Removing existing local tag v0.1.0..."
    git tag -d "v0.1.0"
  fi

  info "Tagging as v0.1.0..."
  git tag -a "v0.1.0" -m "Version 0.1.0 -- initial release"

  # -- 10. rename orphan -> current branch name ------------------------------
  info "Replacing branch '$current_branch' with orphan..."
  # Delete the old branch ref (we're currently on orphan_branch)
  git branch -D "$current_branch" 2>/dev/null || true
  git branch -m "$orphan_branch" "$current_branch"

  # -- 11. force-push branch + tag ------------------------------------------
  info "Force-pushing '$current_branch' to $remote..."
  git push --force "$remote" "$current_branch"

  info "Force-pushing tag v0.1.0 to $remote..."
  git push --force "$remote" "v0.1.0"

  # -- 12. re-set upstream tracking -----------------------------------------
  info "Setting upstream tracking branch..."
  git branch --set-upstream-to="$remote/$current_branch" "$current_branch" 2>/dev/null \
    || warn "Could not set upstream (remote may need a moment to reflect the push)."

  # -- 13. done -------------------------------------------------------------
  printf "\n"
  success "==================================================="
  success "Orphan reset complete!"
  success "  Branch : $current_branch"
  success "  Tag    : v0.1.0"
  success "  Remote : $remote_url"
  success "  Commits: $(git rev-list --count HEAD)"
  success "==================================================="
}

main "$@"
