---
name: git-orphan-reset
description: >
    Wipe all commit history from a local git repository and replace it with a single
    "chore: Initial commit" tagged at v0.1.0, then force-push to origin. Use this skill
    whenever the user wants to reset git history, clean a repo's commit log, start fresh
    with a single commit, or squash all history into one commit. Trigger on "reset git history",
    "wipe commits", "orphan reset", "squash all history", "start fresh commit", or any request
    to replace a repo's full commit history with a single initial commit.
    WARNING: This is a destructive, irreversible operation. Always confirm with the user before
    running. Never run on shared branches without explicit user confirmation.
---

# git-orphan-reset Skill

You are resetting a git repository's commit history using `git-orphan-reset`, which creates
an orphan branch, stages all files into a single commit tagged `v0.1.0`, and force-pushes to
origin. This operation is **irreversible** -- always confirm before running.

---

## When to use this skill

- User wants to wipe all commit history and start fresh with a single commit
- User wants to squash all history before open-sourcing or sharing a repo
- User asks to "reset git history" or "orphan reset" a repository

---

## IMPORTANT: Confirm before running

This script:
- **Destroys all commit history**
- **Force-pushes to origin** (overwrites remote history)
- Is **idempotent** only if already in the target state

Always ask the user to confirm the target repo path and that they understand history will be lost.

---

## Quickstart

```bash
# Reset the current repo
git-orphan-reset

# Reset a specific repo
git-orphan-reset /path/to/repo

# Skip pre-commit hooks
git-orphan-reset --no-verify /path/to/repo
```

---

## Step 0 - Resolve environment and install tool

```bash
if [ "${IS_SANDBOX:-no}" = "yes" ] || [ "${IS_SANDBOX:-no}" = "1" ] || [ "${IS_SANDBOX:-no}" = "true" ]; then
    SKILL_DIR="/mnt/skills/user/git-orphan-reset"
    cp "$SKILL_DIR/git-orphan-reset.sh" /usr/local/bin/git-orphan-reset.sh
    chmod +x /usr/local/bin/git-orphan-reset.sh
    ln -sf /usr/local/bin/git-orphan-reset.sh /usr/local/bin/git-orphan-reset
else
    command -v git-orphan-reset >/dev/null 2>&1 || {
        echo "ERROR: git-orphan-reset not installed. Run: make -C ~/Code/toolbox/git-orphan-reset install" >&2
        exit 1
    }
fi
```

## Step 1 - Check for the tool

```bash
which git-orphan-reset
```

If missing locally (there is no Docker image for this tool, install from a clone of the toolbox repo):

```bash
make -C ~/Code/toolbox/git-orphan-reset install
```

---

## Step 2 - Confirm with the user

Before running, verify:

1. The target repository path
2. That the user understands **all commit history will be permanently destroyed**
3. That the user wants to force-push to the remote

Show the user what will happen:

```bash
cd <repo-path>
git log --oneline | head -5
git remote -v
```

---

## Step 3 - Pre-flight checks (the script runs these automatically)

The script validates:
- Target is a git repo with a remote configured
- All tracked files are committed (no dirty state)
- Local branch is fully pushed (no unpushed commits); skipped when the branch has no upstream
- Asks for confirmation: the user must type `yes` at the prompt, anything else aborts with exit 0 and no changes

The prompt reads from stdin, so the user has to answer it themselves. Do not pipe `yes` into the script on
their behalf; ask them to run it (in Claude Code: `! git-orphan-reset /path/to/repo`).

If already in target state (one commit + v0.1.0 tag, tags fetched first), exits 0 without changes.

---

## Step 4 - Run git-orphan-reset

```bash
# Current directory
git-orphan-reset

# Specific path
git-orphan-reset /path/to/repo

# Skip pre-commit hooks if needed
git-orphan-reset --no-verify /path/to/repo
```

---

## What the script does

1. Validates the target is a git repo with a remote
2. Checks no dirty state and no unpushed commits
3. Asks the user to type `yes` to confirm
4. Creates an orphan branch, stages all files, makes a single "chore: Initial commit" commit tagged `v0.1.0`
5. Force-pushes the orphan branch and tag to origin
6. Cleans up the temporary orphan branch

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Reset completed (or repo already in target state) |
| 1 | Validation failed or push error (a declined confirmation exits 0 with nothing changed) |

---

## Error handling

| Symptom | Likely cause | Fix |
|---|---|---|
| `git-orphan-reset not found` | Not installed | Run `make install` from `toolbox/git-orphan-reset/` |
| `dirty state` error | Uncommitted changes | Commit or stash all changes first |
| `unpushed commits` error | Local ahead of remote | Push first, then run the reset |
| Push rejected | Remote is protected | Check branch protection rules |
