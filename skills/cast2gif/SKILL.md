---
name: cast2gif
description: >
    Convert asciinema .cast recording files into GIF animations using cast2gif (Docker-backed,
    wrapping agg). Use this skill whenever the user wants to convert a terminal recording to a
    GIF, produce an animated GIF from a .cast file, or batch-convert a directory of recordings.
    Trigger on "cast to gif", "cast2gif", "convert cast", "make a gif from", "terminal gif",
    "animated gif from recording", or any request to turn .cast files into GIF images.
---

# cast2gif Skill

You are converting asciinema `.cast` recording files into GIF animations using the `cast2gif`
wrapper script, which handles all Docker volume plumbing on top of `agg` (asciinema GIF generator).

---

## When to use this skill

- User wants to convert a `.cast` file to a `.gif`
- User wants to batch-convert a directory of `.cast` files
- User asks to "make a GIF from a recording" or "turn my cast file into an animation"

---

## Quickstart

```bash
# Single file
cast2gif demo.cast

# Directory of cast files
cast2gif recordings/

# Multiple files
cast2gif m0.cast m1.cast m2.cast
```

---

## Step 0 - Resolve environment and install tool

```bash
if [ "${IS_SANDBOX:-no}" = "yes" ] || [ "${IS_SANDBOX:-no}" = "1" ] || [ "${IS_SANDBOX:-no}" = "true" ]; then
    SKILL_DIR="/mnt/skills/user/cast2gif"
    cp "$SKILL_DIR/cast2gif" /usr/local/bin/cast2gif
    chmod +x /usr/local/bin/cast2gif
else
    command -v cast2gif >/dev/null 2>&1 || {
        echo "ERROR: cast2gif not installed. Run: docker run --rm ghcr.io/rondomondo/cast2gif:latest install | sh" >&2
        exit 1
    }
fi
```

## Step 1 - Check for the tool and Docker

```bash
which cast2gif
docker info >/dev/null 2>&1 || echo "ERROR: Docker is not running"
```

If `cast2gif` is missing locally, install it from the published image (or `make install` from
`toolbox/cast2gif/` in a clone):

```bash
docker run --rm ghcr.io/rondomondo/cast2gif:latest install | sh
```

---

## Step 2 - Determine inputs

Ask the user (or infer from context):

- **Single file**: path to a `.cast` file
- **Directory**: path to a directory containing `.cast` files
- **Multiple files**: space-separated list of `.cast` file paths
- **Explicit output**: `input.cast output.gif`

---

## Step 3 - Run cast2gif

### Single file

```bash
cast2gif <input.cast>
# output: <input>.gif alongside the input file
```

### Explicit output name

```bash
cast2gif <input.cast> <output.gif>
```

### Directory

```bash
cast2gif <directory>/
# converts every .cast file found beneath the directory (recursive)
```

### Multiple files

```bash
cast2gif file1.cast file2.cast file3.cast
```

### Pass-through to agg directly

```bash
cast2gif -- --help
cast2gif -- --theme monokai input.cast output.gif
```

Always use `--` for agg flags. If a flag is passed without it, the wrapper stops and prompts on
`/dev/tty` (continue or convert to pass-through), which will hang a non-interactive session.

---

## Step 4 - Confirm output

After converting, confirm the `.gif` file exists:

```bash
ls -lh <output>.gif
file <output>.gif
```

---

## Default agg options applied by the wrapper

| Option | Default | Notes |
|---|---|---|
| `--rows` | 32 | Terminal height in rows |
| `--cols` | 110 | Terminal width in columns |
| `--font-size` | 24 | Font size in pixels |
| `--line-height` | 1.6 | Line height multiplier |

To override, use pass-through mode: `cast2gif -- --font-size 18 input.cast output.gif`. Pass-through
drops all of the defaults above, so repeat any you still want (e.g. `--rows 32 --cols 110`).

---

## Environment variables

| Variable | Values | Description |
|---|---|---|
| `DEBUG` | `true`/`1`, `false`/`0` | Enable verbose logging |

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All conversions completed successfully |
| 1 | Input not found, Docker error, or conversion failed |

---

## Error handling

| Symptom | Likely cause | Fix |
|---|---|---|
| `cast2gif not found` | Not installed | Run `make install` from `toolbox/cast2gif/` |
| `Docker not running` | Docker Desktop stopped | Start Docker Desktop |
| `No .cast files found` | Directory has no `.cast` beneath it | Check the path; the search is recursive |
| `Pull failed` | No network or auth | Run `make build` to build locally |
| Output GIF missing | Conversion error | Check stderr for agg error output |
