# scripts

**Maintenance helpers for the toolbox repo itself: scaffold a new tool, and tidy the GitHub Container Registry packages the Docker tools are published to.**

| Script | What it does |
|---|---|
| [scaffold-tool.sh](scaffold-tool.sh) | Bootstraps a new skill-aware tool (Makefile, SKILL.md, README.md, main script, and a Dockerfile for docker-type tools). Also behind `make new-tool` in the repo root. |
| [ghcr-pkg.sh](ghcr-pkg.sh) | Lists and deletes package versions on ghcr.io through the `gh` CLI. |
| [check-image-versions.sh](check-image-versions.sh) | Static check that every docker tool bakes its `VERSION` into each shipped file that names its own image (wrapper, install/uninstall scripts). Run it with `make check-versions`; `make docker-push` and `make docker-release` run it first. |
| [git-orphan-reset.sh](git-orphan-reset.sh) | Older copy of the history-reset tool. The maintained version, with its own README and SKILL.md, is in [../git-orphan-reset](../git-orphan-reset). |

> **Also available as an [Agent Skill](#claude-code-skill)** -- install it to scaffold tools and prune ghcr.io versions directly from Claude Code.

---

## Try it now

These are plain bash scripts (no Docker image), so they install from a clone:

```bash
# 1. Clone the toolbox repo
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/scripts

# 2. Install scaffold-tool and git-orphan-reset
make install
```

This copies `scaffold-tool.sh` and `git-orphan-reset.sh` to `/usr/local/bin` (else `sudo`, else `~/.local/bin`)
with extension-less symlinks, so they are callable as `scaffold-tool` and `git-orphan-reset`. `ghcr-pkg.sh` is
not installed; run it from the clone.

> To uninstall: `make uninstall` (from `toolbox/scripts/`)

Then:

```bash
scaffold-tool my-tool --type docker --description "Does a thing"
./ghcr-pkg.sh list -p screenshot
```

---

## scaffold-tool

```
scaffold-tool <name> [--type script|docker] [--description "..."]
                     [--toolbox-dir DIR] [--skills-dir DIR]
                     [--no-makefile-patch] [--dry-run]
```

| Option | Meaning |
|---|---|
| `<name>` | Lowercase kebab-case tool name (`my-tool`) |
| `--type script\|docker` | `script` (default) writes `<name>.sh`; `docker` writes a bare `<name>` wrapper plus a Dockerfile stub |
| `--description "..."` | One-line description used in SKILL.md and README.md |
| `--toolbox-dir DIR` | Toolbox root (default: the parent of the script) |
| `--skills-dir DIR` | agent-skills-toolbox `skills/` directory (default: `~/Code/agent-skills-toolbox/skills`) |
| `--no-makefile-patch` | Do not patch the root Makefile |
| `--dry-run` | Print what would be written without writing anything |

It creates `toolbox/<name>/` containing `Makefile`, `SKILL.md`, `README.md` and the main script, and mirrors those
into the skills directory. From the repo root the same thing is `make new-tool NAME=my-tool TYPE=docker DESC="..."`
(that target passes `--no-makefile-patch`, so add the new tool to `SCRIPT_TOOLS` or `DOCKER_TOOLS` in the root
Makefile yourself).

Try `scaffold-tool demo --dry-run` first to see what it would do.

## ghcr-pkg

```
ghcr-pkg.sh <command> [options]

Commands:
  list              List package versions (id, created, tags)
  delete            Delete package versions (all, or filtered)
  delete-package    Delete the entire package in one call

Options:
  -o OWNER   GitHub user/org that owns the package   (default: rondomondo)
  -p PACKAGE Package name                            (default: screenshot)
  -e VAR     Name of the env var holding the token   (default: GITHUB_TOKEN_PACKAGES)
  -t TYPE    Owner type: auto|user|org               (default: auto)
  -i ID      delete: a specific version ID (repeatable)
  -u         only untagged versions
  -d DAYS    only versions older than DAYS days
  -n         Dry run: show what would be deleted, change nothing
  -y         Skip the confirmation prompt
```

`GHCR_OWNER`, `GHCR_PACKAGE`, `GHCR_TOKEN_VAR` and `GHCR_OWNER_TYPE` override the defaults.

```bash
./ghcr-pkg.sh list -p pdf-strip
./ghcr-pkg.sh delete -p pdf-strip -n               # dry run, all versions
./ghcr-pkg.sh delete -p pdf-strip -u -d 30 -y      # untagged and older than 30 days, no prompt
./ghcr-pkg.sh delete -p pdf-strip -i 12345678 -y   # one version by ID
```

Deletion is permanent. Run with `-n` first. `delete-package` removes the whole package (GitHub can restore it
for 30 days). Without a TTY and without `-y` it refuses to delete.

**Requires:** `gh`, `jq`, and a *classic* personal access token in `$GITHUB_TOKEN_PACKAGES` (fine-grained tokens
cannot access Packages) with `read:packages` to list, plus `delete:packages` to delete.

---

## Makefile targets

```
make help           Show all targets
make install        Install git-orphan-reset and scaffold-tool to /usr/local/bin (else ~/.local/bin)
make uninstall      Remove both from /usr/local/bin and ~/.local/bin
make usage          Show git-orphan-reset usage
make scaffold-usage Show scaffold-tool usage
make sync-skill     Sync SKILL.md, README.md and git-orphan-reset.sh into SKILLS_DIR
```

`make sync-skill` currently defaults to `~/Code/agent-skills-toolbox/skills/git-orphan-reset/`, the same place
`../git-orphan-reset` syncs to. Pass `SKILLS_DIR=...` to keep the two apart.

---

## Claude Code skill

<details>
<summary>Install the skill for Claude Code</summary>

The skill in [SKILL.md](SKILL.md) tells Claude how to run `scaffold-tool` and `ghcr-pkg` safely (dry run first,
confirm before any deletion).

### Invoking the skill

> *"Scaffold a new docker tool called qr-cli"*
>
> *"List the untagged versions of the pdf-strip package on ghcr.io"*

### Installing the skill

```bash
mkdir -p .claude/skills/toolbox-scripts
cp scaffold-tool.sh ghcr-pkg.sh SKILL.md README.md .claude/skills/toolbox-scripts/
```

</details>

---

## Requirements

- `bash` 3.2+ (the macOS default is fine)
- `git`, `make`
- `gh` and `jq` (for `ghcr-pkg` only)
