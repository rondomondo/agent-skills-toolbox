# asciinema-rec

[asciinema-rec](asciinema-rec) is a convenience wrapper around [asciinema](https://asciinema.org/) (via [uvx](https://docs.astral.sh/uv/)) for recording terminal sessions to `.cast` files.

> **Also available as an [Agent Skill](#claude-code-skill)** -- install it to record terminal sessions directly from Claude Code with no terminal required. Use the `/asciinema` slash command or just describe what you want and your AI Agent will handle it.

## Try it now

This tool is a single bash script (no Docker image), so it installs from a clone:

```bash
# 1. Clone the toolbox repo
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/asciinema

# 2. Install the wrapper script
make install

# 3. Record an interactive session
asciinema-rec session.cast

# 4. Done -- session.cast is ready to replay
asciinema-rec play session.cast
```

No separate asciinema install needed; `asciinema-rec` runs it via `uvx` automatically.

---

## Why this exists

Recording terminal sessions with raw `asciinema` requires remembering a handful of flags every time, and the output path handling is inconsistent across environments:

- Without `-i`, long pauses bloat replay files and make recordings tedious to watch (`ASCIINEMA_IDLE_TIME` sets it).
- Without `-y`, asciinema prompts for confirmation, breaking scripted or CI use (`ASCIINEMA_YES` sets it).
- Without `--overwrite`, re-running the same recording command silently refuses to replace the file (always passed).
- Output paths are resolved relative to the shell's working directory, which differs between interactive use and scripts.
- Playing back recordings requires a separate `uvx asciinema play` incantation that's easy to forget.

`asciinema-rec` applies sensible defaults for all of these, resolves output paths to absolute paths, creates intermediate directories automatically, and wraps both recording and playback under a single command.

It is safe to run repeatedly -- existing `.cast` files are always overwritten.

---

## Requirements

- [`uv`](https://docs.astral.sh/uv/) (provides `uvx` to run asciinema without a global install)
- `bash` 3.2+ (the macOS default is fine)
- `make` (for Makefile targets)

Install `uv` with:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Installation

### Install `asciinema-rec` to `/usr/local/bin` (or `~/.local/bin`)

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
asciinema-rec                                Show this help
asciinema-rec -h | --help                    Show this help
asciinema-rec <output.cast>                  Record an interactive shell session
asciinema-rec <output.cast> <cmd> [args]     Record a command with arguments
asciinema-rec <output.cast> -- <cmd> [args]  Record a command (leading -- stripped)
asciinema-rec play <file.cast> [args]        Play back a recorded session
```

### Environment variables

The recording defaults can be overridden per-invocation via environment variables:

| Variable | Default | Effect |
|---|---|---|
| `ASCIINEMA_IDLE_TIME` | unset | Clamp idle gaps to N seconds (`-i N`), e.g. `2.5`. Not passed when unset or empty |
| `ASCIINEMA_YES` | unset | Any non-empty value passes `-y` (answer yes to prompts) |
| `ASCIINEMA_OVERWRITE` | unset | Any non-empty value passes `--overwrite` again (it is always passed already) |

`--overwrite` is hard-wired, so an existing `.cast` file is always replaced. The idle clamp and `-y` only apply
when you set their variables, for example `ASCIINEMA_IDLE_TIME=2.5 asciinema-rec session.cast`.

### Debug logging

Set `DEBUG=true` or `DEBUG=1` to enable verbose logging of invocation arguments:

```bash
DEBUG=true asciinema-rec session.cast
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Recording or playback completed successfully |
| 1 | Missing argument, dependency not found, or output file not written |

---

## Examples

```bash
# Interactive shell recording
asciinema-rec session.cast

# Record a single command
asciinema-rec demo.cast bash -c 'ls -la'

# Record a command using -- separator
asciinema-rec demo.cast -- python3 demo.py

# Play back a recording
asciinema-rec play session.cast

# Play back at 2x speed
asciinema-rec play session.cast -s 2

# Record with idle gaps clamped to 2.5s
ASCIINEMA_IDLE_TIME=2.5 asciinema-rec session.cast

# Upload a recording to asciinema.org
uvx asciinema upload session.cast
```

---

## How it works

| File | Role |
|---|---|
| `asciinema-rec` | Wrapper script. Resolves output paths, creates intermediate directories, invokes `uvx asciinema rec` with consistent flags, and reports success or failure. |
| `Makefile` | Developer workflow: install/uninstall the wrapper. |

### What the wrapper does on each invocation

1. Checks that `uvx` is available on `PATH`; exits with an error if not.
2. Resolves the output path to an absolute path and creates any missing parent directories.
3. Builds the `asciinema rec` flag set: `--overwrite` always, plus `-i` and `-y` when `ASCIINEMA_IDLE_TIME` / `ASCIINEMA_YES` are set.
4. For command recordings, joins the remaining arguments and passes them via `-c`.
5. For interactive recordings, prints a reminder to type `exit` or press `Ctrl+\` to stop.
6. Confirms the output file exists after recording completes.

---

## Makefile targets

```
make help         Show all targets
make install      Install asciinema-rec to /usr/local/bin (else ~/.local/bin)
make uninstall    Remove asciinema-rec from /usr/local/bin and ~/.local/bin
make usage        Show asciinema-rec usage
make sync-skill   Sync skill files to ~/Code/agent-skills-toolbox/skills/asciinema
```

---

## Claude Code skill

<details>
<summary>Install the <code>/asciinema</code> slash command for Claude Code</summary>

This repository ships a `/asciinema` slash command skill for [Claude Code](https://claude.ai/code)
that lets Claude record and replay terminal sessions -- no terminal required. Just describe what
you want and Claude will invoke the skill automatically.

### What it accepts

| Input | Example |
|---|---|
| Interactive session | `session.cast` |
| Command recording | `demo.cast bash -c 'ls -la'` |
| Replay | `play session.cast` |

### Invoking the skill

Use the slash command directly:

```
/asciinema session.cast
/asciinema demo.cast bash -c 'ls -la'
/asciinema play session.cast
```

Or just describe what you want in natural language -- Claude will invoke the skill automatically:

> *"Record a terminal session to demo.cast"*
>
> *"Capture running make test as a cast file"*
>
> *"Play back session.cast"*

### Installing the skill

#### Option A -- sync locally via `make`

```bash
# from inside the asciinema directory
make sync-skill
```

This syncs `asciinema-rec`, `SKILL.md`, and `README.md` to:

```
~/Code/agent-skills-toolbox/skills/asciinema/
```

Override the target directory with `SKILLS_DIR`:

```bash
make sync-skill SKILLS_DIR=/path/to/your/project/.claude/skills/asciinema
```

#### Option B -- copy manually

```bash
mkdir -p .claude/skills/asciinema
cp asciinema-rec SKILL.md README.md .claude/skills/asciinema/
```

</details>
