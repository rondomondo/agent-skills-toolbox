# cast2gif

[cast2gif](cast2gif) is a utility script wrapper used to interact with the
[ghcr.io/rondomondo/cast2gif](https://ghcr.io/rondomondo/cast2gif) Docker image,
which in turn incorporates [agg](https://github.com/asciinema/agg)
(asciinema GIF generator).

> **Also available as an [Agent Skill](#claude-code-skill)** -- install it to convert terminal recordings directly from Claude Code with no terminal required. Use the `/cast2gif` slash command or just describe what you want and your AI Agent will handle it.

## Try it now

Install the lightweight `cast2gif` wrapper, which calls Docker for you:

```bash
docker run --rm ghcr.io/rondomondo/cast2gif install | sh
```

Then from any directory:

```bash
cast2gif demo.cast    # -> demo.gif
file demo.gif
```

> To uninstall: `docker run --rm ghcr.io/rondomondo/cast2gif uninstall | sh`

The installer is a self-contained `sh` script streamed from the image. It installs `cast2gif` to
`/usr/local/bin` if that is writable, otherwise retries with `sudo`, and finally falls back to
`~/.local/bin` (adding it to `PATH` in your `~/.zshrc`, `~/.bashrc` or fish config if needed).
Running it again is safe. The installed wrapper defaults to the image tag it shipped with.

## No install needed - just Docker

```bash
docker run --rm -v "$PWD:/data" ghcr.io/rondomondo/cast2gif:latest demo.cast demo.gif
```

## What it does

It converts [asciinema](https://asciinema.org/) `.cast` recording files into
GIF animations. Running agg directly as a container requires manually wiring up
Docker volume mounts so the container can read your cast file and write output
back to the host.

This wrapper handles all of that automatically: it resolves absolute paths,
mounts the right directory, and derives the output filename for you, so you can
pass a single `.cast` file, multiple `.cast` files, or a directory full of
`.cast` files and get GIF files generated for all of them.

Note: calling with `--` passes everything through directly to the agg app.

---

## Install from the github repository

```bash
# 1. Clone the toolbox repo
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/cast2gif

# 2. Install the wrapper script
make install

# 3. Convert an example recording
cast2gif demo.cast

# 4. Done -- demo.gif should now exist
file demo.gif
```

No Docker pull needed upfront; `cast2gif` pulls `ghcr.io/rondomondo/cast2gif:latest`
automatically on first run.

---

## Installation

From the cloned repository:

### Install `cast2gif` (`/usr/local/bin`, else `sudo`, else `~/.local/bin`)

```bash
make install
```

### Uninstall

```bash
make uninstall
```

---

## Usage

```
cast2gif                         Show help
cast2gif -h | --help             Show help only
cast2gif <input.cast>            Convert one cast file -> <input>.gif
cast2gif <input.cast> <out.gif>  Convert one cast file with explicit output name
cast2gif <directory>             Convert every .cast file found beneath a directory (recursive)
cast2gif <cast1> <cast2> ...     Convert multiple cast files
cast2gif -- [args...]            Pass args directly to agg (e.g. --help)
```

### Examples

```bash
# Single file
cast2gif demo.cast

# Explicit output name
cast2gif session.cast output/my-recording.gif

# Whole directory
cast2gif recordings/

# Multiple files
cast2gif m0.cast m1.cast m2.cast

# Pass args directly to agg (passthrough mode)
cast2gif -- --help
```

---

## Default agg options

The wrapper applies these agg options by default. Edit `AGG_OPTIONS` in the
script to tune them.

| Option          | Default | Notes                     |
|-----------------|---------|---------------------------|
| `--rows`        | 32      | Terminal height in rows   |
| `--cols`        | 110     | Terminal width in columns |
| `--font-size`   | 24      | Font size in pixels       |
| `--line-height` | 1.6     | Line height multiplier    |

Run `cast2gif -- --help` for the full list of agg options, including `--theme`, `--speed`,
`--idle-time-limit`, `--fps-cap`, and frame selection. Pass-through mode drops all of the defaults
above, so repeat any you still want.

---

## What's in the image

Built on `ghcr.io/asciinema/agg:latest` with:

| Category | Included |
|---|---|
| Converter | agg (asciinema GIF generator) |
| Shell | bash |
| Wrapper | cast2gif, install.sh, uninstall.sh, a sample `/demo.cast` |
| Extras | zsh, git, make, curl, wget and a few other debugging tools (used by `make docker-shell`) |

---

## Docker targets

```bash
make build                     # Bump VERSION, build a single-arch image for local testing
make push                      # Build multi-platform (see PLATFORMS) and push :VERSION and :latest
make release                   # Bump patch version, then push
make release-rc                # Push VERSION-rc.1 without bumping VERSION or moving :latest
make retag FROM=latest TAG=v0.1.1   # Re-tag an existing remote image
make docker-shell              # Drop into a shell in the container
make inspect                   # Show the platforms in the remote :latest manifest
make example                   # Print cut-and-paste usage examples
make clean                     # Remove local image tags (clean-builder removes the buildx builder)
```

Options:

```bash
make push NO_CACHE=1           # bust the build cache
make push REGISTRY=docker.io   # push somewhere else
```

`make push` and `make release` publish to the registry and need `docker login` first.

The base image `ghcr.io/asciinema/agg` is amd64-only, so `PLATFORMS` defaults to `linux/amd64` here.

---

## Requirements

- Docker (running locally)
- `bash` 3.2+
- `make` (for Makefile targets)
- `asciinema` (to record `.cast` files)

---

## Claude Code skill

<details>
<summary>Install the <code>/cast2gif</code> slash command for Claude Code</summary>

This repository ships a `/cast2gif` slash command skill for [Claude Code](https://claude.ai/code)
that lets Claude convert terminal recordings to GIFs -- no terminal required. Just describe what
you want and Claude will invoke the skill automatically.

### What it accepts

| Input | Example |
|---|---|
| Single file | `demo.cast` |
| Directory | `recordings/` |
| Multiple files | `m0.cast m1.cast m2.cast` |

### Invoking the skill

Use the slash command directly:

```
/cast2gif demo.cast
/cast2gif recordings/
/cast2gif m0.cast m1.cast
```

Or just describe what you want in natural language -- Claude will invoke the skill automatically:

> *"Convert demo.cast to a GIF"*
>
> *"Turn all the cast files in recordings/ into animated GIFs"*

### Installing the skill

#### Option A -- sync locally via `make`

```bash
# from inside the cast2gif directory
make sync-skill
```

This syncs `cast2gif`, `SKILL.md`, and `README.md` to:

```
~/Code/agent-skills-toolbox/skills/cast2gif/
```

Override the target directory with `SKILLS_DIR`:

```bash
make sync-skill SKILLS_DIR=/path/to/your/project/.claude/skills/cast2gif
```

#### Option B -- copy manually

```bash
mkdir -p .claude/skills/cast2gif
cp cast2gif SKILL.md README.md .claude/skills/cast2gif/
```

</details>
