# agent-skills-toolbox

**Skills for AI coding agents.**

A collection of skills that give AI coding agents structured workflows and tool integrations, packaged for use with Claude Code.

---

## Contents

| Skill | What it does |
|-------|-------------|
| [asciinema](#asciinema) | Records terminal sessions to .cast files via the asciinema-rec wrapper (uvx), and replays existing recordings |
| [cast2gif](#cast2gif) | Converts asciinema .cast recordings to animated GIFs (Docker-backed, wrapping agg), singly or in batches |
| [filetree](#filetree) | Generates ASCII file trees from a directory for READMEs and documentation |
| [git-orphan-reset](#git-orphan-reset) | Replaces a repo's full commit history with a single tagged initial commit and force-pushes. Destructive; always confirms first |
| [inspect-sandbox](#inspect-sandbox) | Inspects a Linux container or AI sandbox and reports filesystem, security context, network, runtimes, and processes as a self-contained HTML viewer plus a multi-page A4 PDF |
| [mermaid-render](#mermaid-render) | Renders Mermaid diagrams from a Markdown file, directory, or URL to SVG, PNG, PDF, JPG, GIF, or WebP |
| [pdf-strip](#pdf-strip) | Strips the /Info dictionary and XMP metadata from PDFs (Docker-backed, pikepdf); accepts files, directories, and URLs |
| [qr](#qr) | Generates styled QR codes via Docker or Node fallback; accepts natural-language colour names, dot styles, and logo embedding |
| [sanitise-ascii](#sanitise-ascii) | Detects and auto-fixes non-ASCII characters (smart quotes, dashes, non-breaking spaces, BOMs, and more) and flags anything it cannot fix for manual review |
| [shell-install-pattern](#shell-install-pattern) | Audits and fixes install/uninstall scripts and Makefiles: install dir priority, cross-file consistency, and a safe PATH guard |
| [toolbox-scripts](#toolbox-scripts) | Maintains this repo: scaffolds new skill-aware tools (scaffold-tool) and lists or deletes ghcr.io package versions (ghcr-pkg) |
| [vhs](#vhs) | Records terminal GIF animations from .tape scripts (Docker-backed, wrapping VHS by Charmbracelet) |

---

## Quick Start

**Install as a Claude Code plugin (all 12 skills):**

```bash
/plugin install agent-skills-toolbox --marketplace rondomondo/agent-skills-toolbox
```

**Install a skill to your user profile (global):**

```bash
make skill-install name=inspect-sandbox
```

**Install to the current project only:**

```bash
make skill-install-local name=inspect-sandbox
```

**Install all skills into the current project:**

```bash
make install-all-skills
```

---

## Skills

### asciinema

Records terminal sessions to `.cast` files using `asciinema-rec`, a convenience wrapper around asciinema (run via `uvx`), and replays existing recordings.

**Triggers when:** you ask to record a terminal session, capture a command demo, make a `.cast` file, or replay a recording.

```bash
asciinema-rec session.cast                    # record an interactive session
asciinema-rec demo.cast bash -c 'ls -la'      # record a single command
asciinema-rec play session.cast               # replay a recording
```

Pairs with [cast2gif](#cast2gif) to turn recordings into GIFs.

See [skills/asciinema/SKILL.md](skills/asciinema/SKILL.md) for the full workflow.

---

### cast2gif

Converts asciinema `.cast` recordings to animated GIFs. A Docker-backed wrapper handles the volume plumbing on top of `agg`.

**Triggers when:** you ask to convert a recording to a GIF, make an animated GIF from a `.cast` file, or batch-convert a directory of recordings.

```bash
cast2gif demo.cast                  # single file
cast2gif recordings/                # directory of cast files
cast2gif m0.cast m1.cast m2.cast    # several files
```

See [skills/cast2gif/SKILL.md](skills/cast2gif/SKILL.md) for the full workflow, or [skills/cast2gif/README.md](skills/cast2gif/README.md) for the tool reference.

---

### filetree

Generates ASCII file trees from a directory for READMEs, documentation, or explaining project structure. A pure-bash wrapper around `find`.

**Triggers when:** you ask for a file tree, directory tree, or project layout, or want a tree added to a README.

```bash
filetree .                                # current directory
filetree --style ascii .                  # ASCII instead of unicode box characters
filetree --exclude-dirs dist:build src/   # skip extra directories
```

See [skills/filetree/SKILL.md](skills/filetree/SKILL.md) for the full workflow.

---

### git-orphan-reset

Replaces a repository's full commit history with a single `chore: Initial commit` tagged `v0.1.0`, then force-pushes to origin.

**Destructive and irreversible.** The skill always asks you to confirm the target repo and that you accept losing history before it runs anything.

**Triggers when:** you ask to reset git history, wipe commits, squash all history, or start fresh with one commit.

```bash
git-orphan-reset                         # current repo
git-orphan-reset /path/to/repo           # a specific repo
git-orphan-reset --no-verify /path/to/repo   # skip pre-commit hooks
```

See [skills/git-orphan-reset/SKILL.md](skills/git-orphan-reset/SKILL.md) for the full workflow.

---

### inspect-sandbox

Automated environment inspection that parses system state into a self-contained HTML viewer with collapsible sections, category filters, and rendered Mermaid diagrams. When running inside an AI sandbox (such as the Claude web UI), the full output is packaged into a downloadable zip that the user can run locally with a single command. A multi-page landscape A4 PDF of all text sections is also rendered via Playwright and presented inline in the chat client as well as in the download bundle.

> **Try it now:** just say one of these to your agent:
> - *Inspect this sandbox and show me what's available*
> - *What tools, runtimes, and network access do I have in here?*
> - *Run /inspect-sandbox and give me a full environment report*

#### Why inspect the sandbox?

When you build skills or agents that run inside an AI sandbox (Claude's web UI, a CI runner, or a cloud container) you are working inside an environment you did not configure and cannot easily observe. That gap can cause real problems:

**The slow-burn discover-as-you-fail loop.** Skills break at runtime because a tool isn't installed, a capability is blocked, the network is restricted, or a write path doesn't exist. You fix one thing, redeploy, and hit the next issue. Rinse and repeat. Each iteration costs minutes or hours. `inspect-sandbox` collapses this loop into a single upfront inspection and read.

**Things you didn't know you needed to know.** You only discover that `mmdc` needs a real display server, that `pip` is replaced by `uv`, that `/tmp` is a `tmpfs` with a 512 MB cap, or that outbound DNS is filtered when your skill fails silently at silly o'clock. The inspection surfaces all of it before you get too deep in despair.

**Concrete constraints, not assumptions.** How much disk can I write? Which Linux capabilities do I have? Is `ptrace` blocked? Is there a proxy? Does `sudo` work? Is seccomp enabled? These answers are rarely documented in detail, if at all; they depend on how the specific sandbox was configured. The generated report gives you the actual reality.

**What the report covers:**

| Section | What you learn |
|---|---|
| Filesystem & mounts | Where you can write, overlay/rclone mounts, tmpfs limits, symlink layout |
| Security context | uid/gid, Linux capabilities (decoded), seccomp mode, AppArmor/SELinux, namespace isolation |
| Network | Interfaces, routing, DNS, iptables rules, proxy variables, custom CA certs |
| Processes | Process tree, CPU/RAM, open file descriptors, listening ports |
| Runtime environment | Installed languages and versions, package managers, OS/kernel/CPU info |
| Skill tool availability | Presence of runtimes, PDF tools, OCR, media tools, browsers, shell utilities |

See [skills/inspect-sandbox/README.md](skills/inspect-sandbox/README.md) for full documentation.

---

### mermaid-render

Renders Mermaid diagrams from Markdown files to SVG, PNG, PDF, JPG, GIF, or WebP. Supports a named colour palette (16 classDef colours) for consistent diagram styling.

**Triggers when:** you type `/mermaid-render`, or ask to render, generate, export, or convert Mermaid diagrams or charts from a `.md` file, local directory, or URL.

**Input sources:**

| Type | Example |
|------|---------|
| Single file | `examples/example1.md` |
| Multiple files | `examples/example1.md examples/example2.md` |
| Local directory | `./docs/` |
| URL (single file) | `https://example.com/diagram.md` |
| URL (GitHub directory) | `https://github.com/user/repo/tree/main/docs` |

**Backends:**

| Environment | Backend |
|-------------|---------|
| Outside sandbox | `mermaid-render` script (Docker-backed via `ghcr.io/rondomondo/mermaid-render`) |
| Inside sandbox | `mmdc` with bundled Chromium; auto-detects Chromium path; uses split mode on single-vCPU sandboxes with 3+ diagrams |

**Output:**

- Numbered image files alongside the source (e.g. `example1.md-1.svg`)
- A companion `.md` with `![diagram](./image-N.ext)` references replacing fenced blocks
- The original file is never modified

**Formats:** `svg` (default), `png`, `pdf`, `jpg`, `gif`, `webp`

See [skills/mermaid-render/SKILL.md](skills/mermaid-render/SKILL.md) for the full workflow.

---

### pdf-strip

Strips all metadata from PDFs: the `/Info` dictionary (Author, Title, Producer, CreationDate, and so on) and the XMP metadata stream. Docker-backed using `pikepdf` outside a sandbox; inside a sandbox it calls `strip.py` directly.

**Triggers when:** you ask to strip or remove PDF metadata, sanitise or clean a PDF before sharing, check what metadata a PDF contains, or batch-process a directory of PDFs.

**Input sources:**

| Type | Example |
|------|---------|
| Single file | `report.pdf` |
| Multiple files | `file1.pdf file2.pdf` |
| Directory | `./my-docs/` |
| URL (single PDF) | `https://example.com/report.pdf` |

See [skills/pdf-strip/SKILL.md](skills/pdf-strip/SKILL.md) for the full workflow, or [skills/pdf-strip/README.md](skills/pdf-strip/README.md) for the tool reference.

---

### qr

Generates styled QR codes via the `rondomondo/qr-cli` Docker image, with automatic fallback to a Python/Node implementation when Docker is unavailable.

**Triggers when:** you type `/qr`, or ask to generate, create, render, or style a QR code.

**Features:**

- Natural-language colour names resolved via `colourmapper`
- Dot and corner style keywords: `rounded`, `circles`, `classy`, `extra-rounded`
- Logo embedding
- Output formats: SVG, PNG, JPG, WEBP
- Always saves to disk and reports the path

**Example invocations:**

```
/qr https://example.com blue on white rounded
/qr https://example.com with logo ./logo.png save to ./out.png
```

See [skills/qr/SKILL.md](skills/qr/SKILL.md) for the full workflow.

---

### sanitise-ascii

Detects and auto-fixes non-ASCII characters (smart quotes, en/em dashes, curly apostrophes, non-breaking spaces, BOMs, and more) before they cause silent failures in pipelines, CI, or tools that expect plain ASCII. Flags anything it cannot fix for manual review.

**Triggers when:** you type `/sanitise-ascii`, or ask to sanitise/sanitize, check for non-ASCII, clean before push, strip unicode, or prepare files for Remote Agent use or GitHub.

**Two deliverables:**

| File | Purpose |
|------|---------|
| `sanitise-ascii.py` | Standalone script, run manually or from CI |
| `pre-commit-sanitise-ascii` | Git hook (in `.githooks/`), checks staged files automatically on every commit |

**Usage:**

```bash
sanitise-ascii README.md              # check a single file (no writes)
sanitise-ascii --fix README.md        # auto-fix in place
sanitise-ascii --fix --dir ./skills   # fix all supported files under a directory
```

**Safe by default:** check mode never writes. Pass `--fix` to allow modifications.

See [skills/sanitise-ascii/README.md](skills/sanitise-ascii/README.md) for the full reference.

---

### shell-install-pattern

Audits and rewrites the install/uninstall strategy for a shell-based CLI tool distributed via `docker run ... install | sh` or a Makefile.

**Triggers when:** you ask to review, improve, or align install scripts or Makefiles, or mention install best practice, install dir, PATH guard, or rc file injection.

**What it enforces:**

- Install directory priority: `/usr/local/bin`, then `sudo`, then `~/.local/bin` (`~/bin` is dropped)
- Cross-file consistency between `install.sh`, `uninstall.sh`, and the Makefile, including every display string
- A POSIX-safe PATH guard that detects the user's shell, writes the export line to the right rc file (`~/.zshrc`, `~/.bashrc`, fish config), and avoids duplicate writes

See [skills/shell-install-pattern/SKILL.md](skills/shell-install-pattern/SKILL.md) for the full workflow.

---

### toolbox-scripts

Maintenance helpers for this repo itself. Two tools:

- **scaffold-tool** bootstraps a new skill-aware tool (Makefile, SKILL.md, README.md, main script, and a Dockerfile for docker-type tools). Also behind `make new-tool`.
- **ghcr-pkg** lists and deletes package versions on ghcr.io. Deletion is permanent, so the skill always does a dry run (`-n`) and confirms with you first.

**Triggers when:** you ask to create a new tool in the toolbox, scaffold a tool, list ghcr.io image versions, or prune untagged or old container images.

```bash
scaffold-tool my-tool --type docker --description "Does a thing"
```

The skill lives in `skills/scripts/` and is named `toolbox-scripts`.

See [skills/scripts/SKILL.md](skills/scripts/SKILL.md) for the full workflow, or [skills/scripts/README.md](skills/scripts/README.md) for the tool reference.

---

### vhs

Records terminal GIF animations from `.tape` script files using `vhs-rec`, a Docker-backed wrapper around VHS by Charmbracelet. It handles the volume plumbing and rewrites `Output` lines.

**Triggers when:** you ask to record a terminal GIF, convert a `.tape` file to a GIF, or batch-convert a directory of `.tape` files.

```bash
vhs-rec demo.tape                         # single tape file
vhs-rec test/                             # directory of tape files
vhs-rec -- validate test/demo.tape        # pass arguments straight to vhs
```

See [skills/vhs/SKILL.md](skills/vhs/SKILL.md) for the full workflow, or [skills/vhs/README.md](skills/vhs/README.md) for the tool reference.

---

## Makefile Reference

```bash
# Install a skill
make skill-install name=inspect-sandbox        # global (~/.claude/skills/)
make skill-install-local name=inspect-sandbox  # project-local (.claude/skills/)

# Install all skills into the current project
make install-all-skills

# Run a skill's own Makefile targets
make skill name=inspect-sandbox target=help
make skill name=inspect-sandbox target=report

# Package a skill as a zip
make skill-zip src=./skills/inspect-sandbox dst=./skills/inspect-sandbox/inspect-sandbox.zip

# Check every skill has a Makefile and SKILL.md
make ok

# Regenerate plugin.json and marketplace.json
make plugin-generate

# Show current plugin config
make plugin-show
```

---

## Contributing

Skills should be **specific** (actionable steps, not vague advice), **verifiable** (clear exit criteria), and **minimal** (only what's needed to guide the agent).

Each skill lives in its own directory under `skills/` with a `SKILL.md` as the entry point.

---

## License

MIT
