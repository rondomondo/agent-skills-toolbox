---
name: asciinema
description: >
    Record terminal sessions to .cast files using asciinema-rec, a convenience wrapper around
    asciinema (via uvx). Use this skill whenever the user wants to record a terminal session,
    capture a command demo, create a .cast file, or replay an existing recording. Trigger on
    "record terminal", "asciinema", "capture session", "record a demo", "record this command",
    "make a cast file", or any request to produce or replay a terminal recording.
---

# asciinema Skill

You are recording terminal sessions to `.cast` files using the `asciinema-rec` wrapper script,
which applies sensible defaults on top of `asciinema` (run via `uvx`).

---

## When to use this skill

- User wants to record an interactive terminal session
- User wants to capture a command or script run as a `.cast` file
- User wants to replay an existing `.cast` recording
- User asks to "record a demo", "make a cast", or "capture this command"

---

## Quickstart

```bash
# Record an interactive session
asciinema-rec session.cast

# Record a single command
asciinema-rec demo.cast bash -c 'ls -la'

# Replay a recording
asciinema-rec play session.cast
```

---

## Step 0 - Resolve environment and install tool

```bash
if [ "${IS_SANDBOX:-no}" = "yes" ] || [ "${IS_SANDBOX:-no}" = "1" ] || [ "${IS_SANDBOX:-no}" = "true" ]; then
    SKILL_DIR="/mnt/skills/user/asciinema"
    command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
    cp "$SKILL_DIR/asciinema-rec" /usr/local/bin/asciinema-rec
    chmod +x /usr/local/bin/asciinema-rec
else
    command -v asciinema-rec >/dev/null 2>&1 || {
        echo "ERROR: asciinema-rec not installed. Run: git clone https://github.com/rondomondo/toolbox.git && make -C toolbox/asciinema install" >&2
        exit 1
    }
fi
```

## Step 1 - Check for the tool

```bash
which asciinema-rec
```

If missing locally, install it from a clone of the toolbox repo (there is no Docker image for this tool):

```bash
make -C ~/Code/toolbox/asciinema install
```

---

## Step 2 - Determine what to record

Ask the user (or infer from context):

- **Interactive session**: just an output path (`session.cast`)
- **Single command**: output path + command (`demo.cast bash -c 'ls -la'`)
- **Replay**: `play` + path (`play session.cast`)

---

## Step 3 - Run asciinema-rec

### Interactive session recording

```bash
asciinema-rec <output.cast>
```

The wrapper will prompt the user to type `exit` or press `Ctrl+\` to stop. This needs a real terminal, so
an agent cannot drive it; prefer command recording below for anything non-interactive.

### Command recording

```bash
asciinema-rec <output.cast> <cmd> [args]
# or with -- separator
asciinema-rec <output.cast> -- <cmd> [args]
```

### Replay

```bash
asciinema-rec play <file.cast>
# replay at 2x speed
asciinema-rec play <file.cast> -s 2
```

---

## Step 4 - Confirm output

After recording, confirm the `.cast` file exists:

```bash
ls -lh <output.cast>
```

---

## Environment variables

| Variable | Default | Effect |
|---|---|---|
| `ASCIINEMA_IDLE_TIME` | unset | Clamp idle gaps to N seconds (`-i N`); not passed when unset or empty. Set e.g. `2.5` for tidy demos |
| `ASCIINEMA_YES` | unset | Non-empty passes `-y` (answer yes to prompts) |
| `ASCIINEMA_OVERWRITE` | unset | Non-empty passes `--overwrite`; the wrapper already always overwrites an existing output file |
| `DEBUG` | `false` | Enable verbose logging |

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Recording or playback completed successfully |
| 1 | Missing argument, dependency not found, or output file not written |

---

## Error handling

| Symptom | Likely cause | Fix |
|---|---|---|
| `uvx is required but not found in PATH` | `uv` not installed | Run `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `asciinema-rec not found` | Not installed | Run `make install` from `toolbox/asciinema/` |
| Output file not written after recording | Session ended before asciinema could save | Check for error output; re-run |
