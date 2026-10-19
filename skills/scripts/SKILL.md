---
name: toolbox-scripts
description: >
    Maintain the toolbox repo itself: scaffold a new skill-aware tool (script or docker type) with
    scaffold-tool, and list or delete package versions on ghcr.io with ghcr-pkg. Use this skill
    whenever the user wants to create a new tool in toolbox, bootstrap a Makefile/SKILL.md/README.md
    for a new tool, list ghcr.io image versions, or prune untagged or old container images.
    Trigger on "new tool", "scaffold a tool", "scaffold-tool", "make new-tool", "ghcr-pkg",
    "list ghcr versions", "delete untagged images", "prune container registry".
    WARNING: ghcr-pkg delete is permanent. Always dry run (-n) and confirm with the user first.
---

# toolbox-scripts Skill

You are maintaining the toolbox repo with two helper scripts in `scripts/`: `scaffold-tool`, which creates
a new tool directory, and `ghcr-pkg.sh`, which lists and deletes GitHub Container Registry package versions.

The history-reset tool that also used to live here has its own skill: see `git-orphan-reset`.

---

## When to use this skill

- User wants to add a new tool to the toolbox
- User wants the standard Makefile, SKILL.md and README.md for a new tool
- User wants to see, or clean up, versions of a ghcr.io package

---

## Step 0 - Resolve environment and install

```bash
command -v scaffold-tool >/dev/null 2>&1 || make -C ~/Code/toolbox/scripts install
```

`make install` puts `scaffold-tool` (and `git-orphan-reset`) on the PATH. `ghcr-pkg.sh` is not installed;
run it as `~/Code/toolbox/scripts/ghcr-pkg.sh`.

---

## scaffold-tool

### Step 1 - Gather inputs

- **name** (required): lowercase kebab-case, e.g. `qr-cli`
- **type**: `script` (default, writes `<name>.sh`) or `docker` (bare `<name>` wrapper plus a Dockerfile stub)
- **description**: one line, used in SKILL.md and README.md

### Step 2 - Dry run, then create

```bash
scaffold-tool <name> --type <script|docker> --description "<one line>" --dry-run
scaffold-tool <name> --type <script|docker> --description "<one line>"
```

From the toolbox root the equivalent is `make new-tool NAME=<name> TYPE=<script|docker> DESC="<one line>"`.
Useful options: `--toolbox-dir DIR`, `--skills-dir DIR` (default `~/Code/agent-skills-toolbox/skills`),
`--no-makefile-patch`. `make new-tool` always passes `--no-makefile-patch`.

### Step 3 - Follow up

The script creates `toolbox/<name>/` with `Makefile`, `SKILL.md`, `README.md` and the main script, and mirrors
them into the skills directory. Then:

1. Implement the main script.
2. Fill in the TODO sections of SKILL.md and README.md.
3. Add the tool to `SCRIPT_TOOLS` or `DOCKER_TOOLS` in the root Makefile (it is not patched by `make new-tool`).
4. Run `make sync-skill` from the new tool directory.

---

## ghcr-pkg

Requires `gh`, `jq`, and a **classic** personal access token in `$GITHUB_TOKEN_PACKAGES` (fine-grained tokens
cannot access Packages) with `read:packages`, plus `delete:packages` to delete.

### Listing is safe

```bash
~/Code/toolbox/scripts/ghcr-pkg.sh list -p <package>
~/Code/toolbox/scripts/ghcr-pkg.sh list -p <package> -u -d 30   # untagged and older than 30 days
```

Defaults: owner `rondomondo` (`-o`), package `screenshot` (`-p`), token variable `GITHUB_TOKEN_PACKAGES` (`-e`).
`GHCR_OWNER`, `GHCR_PACKAGE`, `GHCR_TOKEN_VAR` and `GHCR_OWNER_TYPE` override them.

### Deleting is permanent -- confirm first

Before any `delete` or `delete-package`:

1. Show the user the package and what matches, using `-n` (dry run, changes nothing).
2. Get explicit confirmation of the package name and the filter.
3. Only then run without `-n`. The script prompts `[y/N]` on a TTY and refuses to delete without a TTY unless
   `-y` is given; add `-y` only when the user has confirmed.

```bash
ghcr-pkg.sh delete -p <package> -u -d 30 -n    # dry run
ghcr-pkg.sh delete -p <package> -u -d 30 -y    # after confirmation
ghcr-pkg.sh delete -p <package> -i <version-id> -y
ghcr-pkg.sh delete-package -p <package> -n     # whole package (restorable for 30 days)
```

If GitHub refuses to delete the last remaining version, the script suggests `delete-package`.

---

## Environment variables

| Variable | Used by | Description |
|---|---|---|
| `GITHUB_TOKEN_PACKAGES` | ghcr-pkg | Classic PAT; the variable name can be changed with `-e` or `GHCR_TOKEN_VAR` |
| `GHCR_OWNER`, `GHCR_PACKAGE`, `GHCR_OWNER_TYPE` | ghcr-pkg | Default owner, package, and `auto`/`user`/`org` |

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (including a dry run, or nothing matched) |
| 1 | Bad arguments, missing dependency or token, user declined, or one or more deletions failed |

---

## Error handling

| Symptom | Likely cause | Fix |
|---|---|---|
| `scaffold-tool: command not found` | Not installed | `make install` from `toolbox/scripts/` |
| `Tool name must be lowercase kebab-case` | Bad name | Use e.g. `my-tool` |
| `'gh' not found in PATH` / `'jq' not found in PATH` | Missing dependency | Install `gh` and `jq` |
| `env var GITHUB_TOKEN_PACKAGES is empty or unset` | No token | Export a classic PAT with the needed scopes |
| `cannot resolve owner` | Wrong `-o` or token | Check the owner name and token |
| `not a TTY and -y not given; refusing to delete` | Non-interactive delete | Confirm with the user, then add `-y` |
