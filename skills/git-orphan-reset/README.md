# git-orphan-reset

**Wipe all commit history from a local git repository and replace it with a single "chore: Initial commit" tagged at v0.1.0, then force-push to origin.**

[git-orphan-reset.sh](git-orphan-reset.sh) is a bash script that safely resets a repos history
to a single orphan commit. It validates pre-conditions, asks for explicit confirmation, and is
idempotent.  Re-running it on an already-reset repo is a no-op.

> **Also available as an [Agent Skill](#claude-code-skill)** -- install it to reset git history directly from Claude Code. Use the `/git-orphan-reset` slash command or just describe what you want and your AI Agent will handle it.

> **WARNING:** This is a destructive, irreversible operation. All commit history will be permanently destroyed. The remote will be force-pushed.

---

## Try it now

This tool is a single bash script (no Docker image), so it installs from a clone:

```bash
# 1. Clone the toolbox repo
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/git-orphan-reset

# 2. Install git-orphan-reset to /usr/local/bin
make install
```

This copies `git-orphan-reset.sh` to `/usr/local/bin` (else `sudo`, else `~/.local/bin`) and creates an
extension-less symlink so the tool is callable as `git-orphan-reset` on PATH.

> To uninstall: `make uninstall` (from `toolbox/git-orphan-reset/`)

Then, from inside a repo that has a remote:

```bash
# Reset the current repo
git-orphan-reset

# Reset a specific repo path
git-orphan-reset /path/to/repo

# Skip pre-commit hooks
git-orphan-reset --no-verify /path/to/repo
```

---

## Usage

```
git-orphan-reset [--no-verify] [/path/to/repo]

  --no-verify  Skip pre-commit hooks on the orphan commit.
  If no path is given the current working directory is used.
```

---

## What it does

1. Validates the target is a git repo with a remote configured
2. Checks that every tracked file is committed (no dirty state)
3. Checks that the local branch is fully pushed to its upstream (skipped when no upstream is set)
4. Asks for confirmation before any destructive work: you must type `yes` at the prompt (anything else aborts, exit 0, nothing changed)
5. Creates an orphan branch, stages all files, makes a single commit tagged `v0.1.0`
6. Force-pushes the orphan branch and the tag to origin
7. Cleans up the temporary orphan branch

### Idempotency

If the repo already has exactly one commit whose message starts with `chore: Initial commit`
AND the tag `v0.1.0` already exists (tags are fetched first), the script reports success and exits 0 without
touching anything.

---

## Examples

```bash
# Reset current repo
git-orphan-reset

# Reset a specific repo
git-orphan-reset ~/Code/myproject

# Skip pre-commit hooks
git-orphan-reset --no-verify ~/Code/myproject
```

---

## How it works

| File | Role |
|---|---|
| `git-orphan-reset.sh` | Main script. Validates, confirms, creates orphan commit, force-pushes. |
| `Makefile` | Developer workflow: install/uninstall the script. |

---

## Makefile targets

```
make help         Show all targets
make install      Install git-orphan-reset to /usr/local/bin (else ~/.local/bin)
make uninstall    Remove git-orphan-reset from /usr/local/bin and ~/.local/bin
make usage        Show git-orphan-reset usage
make sync-skill   Sync skill files to ~/Code/agent-skills-toolbox/skills/git-orphan-reset
```

---

## Claude Code skill

<details>
<summary>Install the <code>/git-orphan-reset</code> slash command for Claude Code</summary>

This repository ships a `/git-orphan-reset` slash command skill for [Claude Code](https://claude.ai/code)
that lets Claude reset git history -- no terminal required. Just describe what you want and
Claude will invoke the skill automatically (and always confirm before running).

### What it accepts

| Input | Example |
|---|---|
| Current directory | _(no argument)_ |
| Specific path | `/path/to/repo` |
| Skip hooks | `--no-verify /path/to/repo` |

### Invoking the skill

Use the slash command directly:

```
/git-orphan-reset
/git-orphan-reset /path/to/repo
```

Or just describe what you want in natural language -- Claude will invoke the skill automatically:

> *"Reset the git history of this repo to a single commit"*
>
> *"Wipe all commits and start fresh at v0.1.0"*

Claude will always confirm with you before running the destructive operation.

### Installing the skill

#### Option A -- sync locally via `make`

```bash
# from inside the git-orphan-reset directory
make sync-skill
```

This syncs `git-orphan-reset.sh`, `SKILL.md`, and `README.md` to:

```
~/Code/agent-skills-toolbox/skills/git-orphan-reset/
```

Override the target directory with `SKILLS_DIR`:

```bash
make sync-skill SKILLS_DIR=/path/to/your/project/.claude/skills/git-orphan-reset
```

#### Option B -- copy manually

```bash
mkdir -p .claude/skills/git-orphan-reset
cp git-orphan-reset.sh SKILL.md README.md .claude/skills/git-orphan-reset/
```

</details>


### Integration as a Custom Git Subcommand

Because the script follows the naming convention `git-<command>`, Git will automatically detect it as a subcommand if it exists in your system `$PATH`.

You can execute it directly through Git without any extra configuration:

```bash
git orphan-reset
```

---

## Requirements

- `bash` 3.2+ (the macOS default is fine)
- `git` with a configured remote
- `make` (for Makefile targets)
