#!/usr/bin/env bash
# git-orphan-reset.sh: Clears git history, creates a single "chore: Initial commit", and force-pushes to remote.

set -euo pipefail

# Colors
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { printf "${CYAN}[INFO]${RESET}  %s\n" "$*"; }
success() { printf "${GREEN}[OK]${RESET}    %s\n" "$*"; }
warn()    { printf "${YELLOW}[WARN]${RESET}  %s\n" "$*"; }
die()     { printf "${RED}[ERROR]${RESET} %s\n" "$*" >&2; exit 1; }
banner()  { printf "\n${BOLD}%s${RESET}\n%s\n" "$1" "$(printf '%0.s-' $(seq 1 ${#1}))"; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

confirm() {
  local answer
  printf "\n${BOLD}${YELLOW}[!] CONFIRMATION REQUIRED${RESET}\n%s\n" "$1"
  printf "${BOLD}Type 'yes' to proceed: ${RESET}"
  read -r answer
  [[ "$answer" == "yes" ]]
}

main() {
  require_cmd git

  # Options
  local no_verify=false
  local args=()
  for arg in "$@"; do
    case "$arg" in
      --no-verify) no_verify=true ;;
      *) args+=("$arg") ;;
    esac
  done
  set -- "${args[@]+"${args[@]}"}"

  # Target repo
  local repo_path="${1:-.}"
  repo_path="$(cd "$repo_path" 2>/dev/null || die "Directory not found: $repo_path"; pwd)"
  banner "git-orphan-reset -> $repo_path"
  cd "$repo_path"

  # Validation
  git rev-parse --git-dir >/dev/null 2>&1 || die "Not a git repository: $repo_path"
  success "Git repository confirmed"

  local current_branch remote remote_url
  current_branch="$(git symbolic-ref --short HEAD 2>/dev/null || die "HEAD is detached. Checkout a branch first.")"
  info "Current branch : $current_branch"

  remote="$(git remote 2>/dev/null | head -1)"
  [[ -n "$remote" ]] || die "No git remote configured."
  info "Remote         : $remote"

  remote_url="$(git remote get-url "$remote" 2>/dev/null)"
  info "Remote URL     : $remote_url"

  # Idempotency check
  local commit_count
  commit_count="$(git rev-list --count HEAD 2>/dev/null || echo 0)"

  local first_msg=""
  [[ "$commit_count" -ge 1 ]] && first_msg="$(git log --oneline | tail -1 | cut -d' ' -f2-)"

  local remote_tag_exists=false
  git fetch --tags --quiet 2>/dev/null || true
  git tag -l "v0.1.0" | grep -q "v0.1.0" && remote_tag_exists=true

  if [[ "$commit_count" -eq 1 && "$first_msg" == "chore: Initial commit"* && "$remote_tag_exists" == "true" ]]; then
    success "Repo is already reset (1 commit, tag v0.1.0 present). Nothing to do."
    exit 0
  fi

  # Check clean working tree
  if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    warn "Uncommitted changes detected:"
    git status --short
    die "Commit or stash all changes first."
  fi
  success "Working tree clean"

  # Check unpushed commits
  local tracking
  tracking="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"

  if [[ -n "$tracking" ]]; then
    git fetch "$remote" --quiet 2>/dev/null || true
    local unpushed
    unpushed="$(git log "${tracking}..HEAD" --oneline 2>/dev/null || true)"
    if [[ -n "$unpushed" ]]; then
      warn "Unpushed commits found:"
      echo "$unpushed"
      die "Push commits before resetting: git push $remote $current_branch"
    fi
    success "All commits pushed to $tracking"
  fi

  # User confirmation
  printf "\n${BOLD}Summary:${RESET}\n"
  printf "  - Erase %s commit(s) on '%s'\n" "$commit_count" "$current_branch"
  printf "  - Create initial commit tagged v0.1.0\n"
  printf "  - Force-push to %s / %s (%s)\n\n" "$remote" "$current_branch" "$remote_url"

  confirm "Permanently erase git history for '$repo_path' and push single commit to '$remote'?" \
    || { warn "Aborted by user."; exit 0; }

  # Reset execution
  banner "Executing orphan reset"
  local orphan_branch="__orphan_reset_tmp__"

  git show-ref --verify --quiet "refs/heads/$orphan_branch" 2>/dev/null && git branch -D "$orphan_branch"

  info "Creating orphan branch..."
  git checkout --orphan "$orphan_branch"

  info "Staging files & creating commit..."
  git add -A
  local commit_flags=(--allow-empty -m "chore: Initial commit")
  [[ "$no_verify" == true ]] && commit_flags+=(--no-verify)
  git commit "${commit_flags[@]}"

  info "Setting tag v0.1.0..."
  git tag -l "v0.1.0" | grep -q "v0.1.0" && git tag -d "v0.1.0"
  git tag -a "v0.1.0" -m "Version 0.1.0 -- initial release"

  info "Swapping branch to '$current_branch'..."
  git branch -D "$current_branch" 2>/dev/null || true
  git branch -m "$orphan_branch" "$current_branch"

  info "Pushing to remote..."
  git push --force "$remote" "$current_branch"
  git push --force "$remote" "v0.1.0"

  info "Updating upstream tracking..."
  git branch --set-upstream-to="$remote/$current_branch" "$current_branch" 2>/dev/null || true

  printf "\n"
  success "Orphan reset complete!"
  success "  Branch : $current_branch"
  success "  Tag    : v0.1.0"
  success "  Commits: $(git rev-list --count HEAD)"
}

main "$@"