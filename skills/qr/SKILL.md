---
name: qr
description: >
    Generate styled QR codes via the qr-cli Docker image (or Node fallback when Docker is
    unavailable). Use this skill whenever the user wants to generate, create, render, or style a
    QR code -- including /qr, "make a QR code", "QR this URL", "QR with logo", or "styled QR".
    Accepts natural-language colour names, dot/corner style keywords, logo embedding, and raw
    flags. Always saves to disk and reports the path.

# Invocation
argument-hint: '<url> [colour] [on <bg-colour>] [rounded|circles|classy|extra-rounded] [<size>px] [svg|png|jpg|webp] [with logo <url>] [save to <path>] [--backend=docker|node|auto]'
disable-model-invocation: false
user-invocable: true
---

# /qr — QR code generator skill

Generate styled QR codes via the `qr-cli` Docker image. Accepts natural language
descriptions, named colours (resolved via `colourmapper`), or raw flags/JSON.
Always saves the image to disk and reports where it landed.

## Skill location and dependencies

All paths below are relative to the skill root (the directory containing this SKILL.md file).
When installed, that is `~/.claude/skills/qr/`.

- Wrapper: `./scripts/qr-skill.sh`
- Docker image: `rondomondo/qr-cli:latest` (primary backend)
- Python/Node: `python3 -m qr_cli` (automatic fallback when Docker is unavailable)

### Backend selection

The wrapper selects a backend automatically (Docker first, Node fallback):

| Situation                       | Backend used                       |
| ------------------------------- | ---------------------------------- |
| Docker running (default)        | `docker run rondomondo/qr-cli`     |
| Docker unavailable (sandbox/CI) | `python3 -m qr_cli --backend=node` |
| `--backend=docker` forced       | Docker (errors if not running)     |
| `--backend=node` forced         | Python/Node always                 |
| `QR_BACKEND=node` env var       | Python/Node always                 |

### colourmapper (required for named colour resolution)

```bash
pip install -i https://pypi.org/simple/ colourmapper-dev
```

The wrapper calls `python3 -m colourmapper.cm <name>` and falls back gracefully
to the raw value if the package is not installed.

---

## Node backend bootstrap (sandboxed / no-Docker environments)

> **When does this apply?**
> In sandboxed environments (e.g. Claude's own execution sandbox, CI runners,
> airgapped machines) Docker is unavailable and `python3 -m qr_cli --install`
> also fails -- because the `canvas` npm package tries to compile itself and
> download Node.js C++ headers from `nodejs.org`, which is typically blocked.
>
> The bootstrap script solves this entirely without any network access beyond
> PyPI and the Ubuntu package mirror.

### What the bootstrap does

1. Installs `qr-cli` and `colourmapper-dev` from PyPI
2. Installs system libs (`libcairo2-dev`, `libpango1.0-dev`, `librsvg2-dev`,
   `libjpeg-dev`, `libgif-dev`) via apt -- these are the native dependencies
   for the `canvas` npm package
3. Compiles `canvas` using **system Node headers** at `/usr/include/node/`
   via `npm_config_nodedir=/usr` -- completely avoids the `nodejs.org` download
4. Installs `jsdom` (needed for `qr-code-styling`'s DOM rendering in Node)
5. Drops in `./scripts/index.js` (the patched version) which contains three
   fixes discovered through debugging (see patch notes below)

### Running the bootstrap

```bash
bash ./.claude/skills/qr/scripts/bootstrap_node_backend.sh
```

The script is **idempotent** -- safe to re-run after `qr-cli` upgrades or
reinstalls. It checks what's already in place and only does what's needed.

A smoke test runs at the end to confirm everything works.

### Patch notes (why index.js is patched)

Three bugs exist in the upstream `qr-cli` Node backend that only manifest in
sandboxed environments. The patched `./scripts/index.js` fixes all three:

**Patch 1 — JSDOM network hang**
`qr-code-styling` calls `new jsdom("", { resources: "usable" })` internally.
The `resources: "usable"` option tells jsdom to fetch external resources over
the network, which hangs indefinitely when the network is restricted.
Fix: subclass JSDOM to strip the `resources` key before calling `super()`.

**Patch 2 — canvas + jsdom wiring**
The original index.js used a partial `global.document` shim that only stubbed
`createElement`, not `createElementNS`. `qr-code-styling` needs a full SVG DOM.
Fix: pass `jsdom: JSDOM` and `nodeCanvas: { createCanvas, loadImage }` directly
to the `QRCodeStyling` constructor (which supports this natively).

**Patch 3 — stdin blocking**
When `python3 -m qr_cli` runs Node via `subprocess` with captured stdout,
stdin is not a TTY. The original index.js unconditionally called
`fs.readFileSync("/dev/stdin")` which blocks forever waiting for input.
Fix: only attempt the stdin read when `--data` and `--json` flags are absent.

---

## Auto-bootstrap in execution flow

**Claude should auto-bootstrap before the first Node backend attempt**, rather
than waiting for it to fail. The execution steps below include this check.

Detection: the Node backend needs bootstrapping if the compiled canvas binary is missing:

```bash
python3 -c "
import importlib.util, os, sys
spec = importlib.util.find_spec('qr_cli')
if not spec: sys.exit(1)
canvas = os.path.join(os.path.dirname(spec.origin), 'node/node_modules/canvas/build/Release/canvas.node')
sys.exit(0 if os.path.exists(canvas) else 1)
" 2>/dev/null
```

This is a fast file-existence check (no network, no QR generation). On macOS use `otool -L` to
inspect the binary if needed; `ldd` is Linux-only.

In practice: **if Docker is not available, run the bootstrap first, then generate.**

---

## How to invoke

When the user types `/qr <anything>`, parse their intent and call the wrapper.
Never ask clarifying questions for reasonable defaults -- just pick them and say so.

### Examples mode

If the user types `/qr examples`, `/qr show examples`, `/qr show me the examples`,
or any phrase asking to see skill examples, run:

```bash
python3 ./scripts/extract_skill_examples.py
```

Print the output verbatim (it includes ANSI colour codes that the terminal renders).
Do not call the wrapper or generate any QR code. Sample images are in `./assets/`; extended
docs are at `./docs/EXAMPLES.md` and `./docs/README.md`.

### Help mode

If the user types `/qr help`, `/qr --help`, or `/qr -h`, print this reference
directly without calling the wrapper:

```
/qr <url> [options]

QUICK EXAMPLES
  /qr https://example.com
  /qr https://example.com rounded royal blue on cream
  /qr https://example.com extra-rounded midnight blue on ivory 500px
  /qr https://example.com svg slate on white
  /qr https://example.com with logo https://example.com/logo.svg

COLOURS       Any English name: "royal blue", "burnt orange", "cream", "slate",
              "ivory", "charcoal", "goldenrod", "dusty rose" -- ~30K names work.
              Hex also accepted: "#0255c7", "fff"

DOT STYLES    rounded, circles, classy, classy-round, extra-rounded, square
CORNER STYLES round corners, dot corners, square corners
FORMATS       png (default), svg, jpg, webp
SIZE          e.g. 400px, 600x400
QUALITY       use --qrOptions.errorCorrectionLevel=H when adding a logo
SAVE PATH     save to /my/path/qr.png

FLAGS (raw passthrough also works)
  --data=        URL or string to encode (required)
  --format=      png | jpg | webp | svg
  --width=       pixels (default 300)
  --height=      pixels (default 300)
  --border=      pixel border (default 10)
  --margin=      quiet zone (default 0)
  --project=     namespaces output as assets/images/<name>/qr.<ext>
  --image=       <url|path> logo URL to embed in centre
                            (URLs are pre-fetched to a local temp file before
                            generation to avoid sandbox network restrictions)
  --dotsOptions.type=
  --cornersSquareOptions.type=
  --qrOptions.errorCorrectionLevel=  L | M | Q | H
```

### Colour resolution

Pass any colour the user names using `--dots-color=`, `--bg-color=`,
`--corners-color=`, `--corner-dot-color=`. The wrapper resolves them to hex via
`colourmapper` (30K named colours -- "royal blue", "cream", "burnt orange",
"slate", etc. all work). You can also pass hex directly.

If the user says "dark" / "light" without specifying a colour, default to
`--dots-color="#000000"` / `--bg-color="#ffffff"`.

### Dot style shortcuts (map natural language to --dotsOptions.type)

| User says              | Flag value       |
| ---------------------- | ---------------- |
| round / rounded        | `rounded`        |
| circle / circles       | `dots`           |
| classy                 | `classy`         |
| classy round / elegant | `classy-rounded` |
| extra round / bubbly   | `extra-rounded`  |
| square (default)       | `square`         |

### Corner style shortcuts (--cornersSquareOptions.type)

| User says      | Flag value      |
| -------------- | --------------- |
| round corners  | `extra-rounded` |
| dot corners    | `dot`           |
| square corners | `square`        |

### Error correction shortcuts (--qrOptions.errorCorrectionLevel)

| User says                  | Level |
| -------------------------- | ----- |
| low / small / fast         | `L`   |
| medium / normal            | `M`   |
| standard / default (omit)  | `Q`   |
| high / logo / image / best | `H`   |

### Format shortcuts

| User says     | --format |
| ------------- | -------- |
| svg / vector  | `svg`    |
| jpg / jpeg    | `jpg`    |
| webp          | `webp`   |
| png (default) | `png`    |

## Wrapper flags reference

```
--data=<url>                  (required) string/URL to encode
--format=<png|jpg|webp|svg>   output format (default: png)
--width=<px>                  width in pixels (default: 300)
--height=<px>                 height in pixels (default: 300)
--border=<px>                 pixel border around QR (default: 10)
--margin=<px>                 quiet zone (default 0)
--project=<name>              namespaces output as assets/images/<name>/qr.<ext>
--dotsOptions.type=<style>    dot shape (see table above)
--dotsOptions.color=<hex>     dot colour (use --dots-color= for name resolution)
--backgroundOptions.color=<hex>  background (use --bg-color= for name resolution)
--cornersSquareOptions.type=<style>
--cornersSquareOptions.color=<hex>   (use --corners-color= for name resolution)
--cornersDotOptions.type=<style>
--cornersDotOptions.color=<hex>      (use --corner-dot-color= for name resolution)
--qrOptions.errorCorrectionLevel=<L|M|Q|H>
--image=<url>                 logo URL to embed in centre
--imageOptions.margin=<px>    logo margin (default: 10)
--imageOptions.crossOrigin=anonymous   required for external logos
--save-to=<path>              override save path
--no-save                     skip writing to disk
--image-tag=<tag>             override docker image tag
--backend=<docker|node|auto>  force backend (default: auto -- Docker if available, else Node)
```

## Execution steps

1. Parse the user's request (natural language, flags, or JSON blob).

2. **Check backend availability:**
    - Try `docker info` -- if Docker is available, proceed to step 3 with Docker.
    - If Docker is unavailable, check if the Node backend is bootstrapped with:

        ```bash
        # canvas will exist if we have been bootstrapped
        python3 -c "
        import importlib.util, os, sys
        spec = importlib.util.find_spec('qr_cli')
        if not spec: sys.exit(1)
        canvas = os.path.join(os.path.dirname(spec.origin), 'node/node_modules/canvas/build/Release/canvas.node')
        sys.exit(0 if os.path.exists(canvas) else 1)
        " 2>/dev/null
        ```

    - If that fails or times out, **run bootstrap first**:

    Before running the bootstrap, emit a message to the user:
    "⚙️ One-time setup in progress — compiling the QR rendering engine against system
    libraries (no Docker in this environment). This takes ~30–40 seconds and only happens once.
    Hang tight…"

    Then run the bootstrap.
    `bash
    bash ./.claude/skills/qr/scripts/bootstrap_node_backend.sh
    `
    - After bootstrap, use `python3 -m qr_cli --backend=node` directly (not
      qr-skill.sh) because qr-skill.sh's base64 decode step is incompatible
      with the Node backend's save-to handling. See note below.

2b. **If a logo image URL is supplied (`--image=<url>`):**
    - **Docker backend:** pass the URL through unchanged. Docker runs locally and has
      unrestricted network access, so the container fetches it directly. No pre-fetch needed.
    - **Node backend (no Docker / sandbox):** use the `web_fetch` tool to download the image
      to a temp local path `/tmp/qr_logo_<random_suffix>.<ext>` (infer extension from URL or
      Content-Type), then replace `--image=<url>` with the bare local path.
      If the fetch fails (network blocked, 4xx/5xx), warn the user and continue without the
      logo rather than aborting. Clean up the temp file after generation completes.
    - Bump error correction to `H` if not already set (logo occludes part of the code).

3. Resolve colour names using the wrapper's `--dots-color=` / `--bg-color=` etc.

4. Set sensible defaults for anything not specified:
    - format: `png`, width/height: `300`, border: `10`, margin: `10`
    - dots style: `rounded` (nicer default than `square`)
    - error correction: omit (library default `Q`) unless a logo is present, then use `H`
    - project: `default` if the user does not name one

5. Build the structured save path before calling:
    - **Docker backend:** images are written into `./output/` on the host (the wrapper mounts
      it as `/output` inside the container). Pass `--save-to` as a path relative to `output/`,
      e.g. `output/{project}/{width}x{height}_{dotscolor}_{bgcolor}_{project}.{format}`.
      The wrapper translates this to `/output/...` for the container automatically.
    - **Node backend:** pass `--save-to` directly; the wrapper saves there.
    - Pattern: `output/{project}/{width}x{height}_{dotscolor}_{bgcolor}_{project}.{format}`
    - Strip the leading `#` from hex colours in the filename (e.g. `0504aa` not `#0504aa`).
      Use the raw colour name if hex is not yet known.
    - Example: `output/default/300x300_royalblue_cream_default.png`

6. **Run the appropriate command:**

    **Docker available** — use qr-skill.sh (volume mount handled inside the wrapper):

    ```bash
    bash ./.claude/skills/qr/scripts/qr-skill.sh \
      --data="<url>" \
      --save-to="output/default/300x300_000000_ffffff_default.png" \
      [other args...]
    ```

    The wrapper mounts `./output` as `/output` in the container, rewrites `--save-to` to
    `/output/default/300x300_000000_ffffff_default.png`, and the file lands at
    `./output/default/300x300_000000_ffffff_default.png` on the host.

    **Node backend (no Docker)** — qr-skill.sh also handles this path correctly now:

    ```bash
    bash ./.claude/skills/qr/scripts/qr-skill.sh --backend=node \
      --data="<url>" \
      --format=png \
      --dotsOptions.type=rounded \
      --save-to="output/default/300x300_000000_ffffff_default.png"
    ```

7. Parse the JSON result.

8. Report back clearly:
    - Saved to: `<path>` (use `_skill.saved_to` if present, else the path you passed)
    - Format / size / dimensions
    - Colours used (with resolved names if colourmapper matched)
    - Generation time
    - Backend used (Docker or Node)
    - Any error from `.error`

## Example invocations

```bash
SKILL=./.claude/skills/qr/scripts/qr-skill.sh

# Docker: minimal (image saved to ./output/default/qr.png via volume mount)
bash "$SKILL" \
  --data="https://example.com" \
  --save-to="output/default/300x300_000000_ffffff_default.png"

# Docker: natural colour names, rounded style
bash "$SKILL" \
  --data="https://example.com" \
  --dotsOptions.type=rounded \
  --dots-color="royal blue" \
  --bg-color="cream" \
  --save-to="output/default/300x300_royalblue_cream_default.png" \
  --border=10 --margin=10

# Docker: with a logo -- URL passed straight through, no pre-fetch needed
bash "$SKILL" \
  --data="https://example.com" \
  --dotsOptions.type=extra-rounded \
  --dots-color="midnight blue" \
  --bg-color="ivory" \
  --cornersSquareOptions.type=extra-rounded \
  --corners-color="midnight blue" \
  --qrOptions.errorCorrectionLevel=H \
  --image="https://example.com/logo.svg" \
  --imageOptions.crossOrigin=anonymous \
  --imageOptions.margin=10 \
  --format=png --width=500 --height=500 \
  --save-to="output/default/500x500_midnightblue_ivory_default.png"

# Node (no Docker): via qr-skill.sh with --backend=node
bash "$SKILL" --backend=node \
  --data="https://example.com" \
  --format=webp \
  --dotsOptions.type=rounded \
  --border=10 \
  --save-to="output/default/300x300_000000_ffffff_default.webp"

# Node (no Docker): bootstrap first if needed, then generate
bash ./.claude/skills/qr/scripts/bootstrap_node_backend.sh
bash "$SKILL" --backend=node \
  --data="https://example.com" \
  --format=png \
  --save-to="output/default/300x300_000000_ffffff_default.png"
```

## What to report after generation

Render the saved path as a clickable markdown link using a **relative path** from
the repo root (`./`). VS Code renders relative markdown links as
clickable; `file://` URIs are NOT clickable in the VS Code markdown renderer.

```
QR code generated and saved.

  Saved to:    [output/default/300x300_0504aa_ffffc2_default.png](output/default/300x300_0504aa_ffffc2_default.png)
  Format:      PNG  (300x300 px, 14.2 KB)
  Dots:        rounded  #0504aa  (royal blue)
  Background:  #ffffc2  (cream)
  Backend:     Docker  (or "Node (python3 -m qr_cli)" when fallback was used)
  Generated:   42 ms
```

If the Node fallback was used (Docker unavailable), say so clearly.

Always append a fenced code block after the summary so the user can copy the
`open` command directly from the VS Code copy button:

````
```
open output/default/300x300_0504aa_ffffc2_default.png
```
````

Use `_skill.saved_to` from the JSON result as the path (set by the wrapper for
both Docker and Node backends when `--save-to` is provided).

Rules for the link:

- Use the relative path as both the link text and the href.
- Format: `[<relative_path>](<relative_path>)`
- Never use `file://` URIs -- they are not clickable in VS Code.

If an error occurs, show the `.error` field from the JSON and suggest a fix based on the
common causes below:

| Symptom                                    | Likely cause                      | Fix                                                                        |
| ------------------------------------------ | --------------------------------- | -------------------------------------------------------------------------- |
| `Cannot connect to the Docker daemon`      | Docker not running                | Start Docker Desktop, or use `--backend=node`                              |
| `canvas.node: no such file or directory`   | Node backend not bootstrapped     | Run `bootstrap_node_backend.sh`                                            |
| `colour not found` / unexpected hex result | Colour name too obscure           | Try a simpler name or pass hex directly                                    |
| `canvas` compile error during bootstrap    | Missing system libs               | Check apt output; re-run bootstrap                                         |
| Hangs indefinitely on Node backend         | jsdom network access blocked      | Ensure patched `index.js` is in place                                      |
| `format not supported`                     | Backend/format mismatch           | SVG requires Docker; use `--format=png` for Node                           |
| fetch failed for logo URL                  | Network sandbox blocks the domain | Claude pre-fetches via web_fetch tool; if that also fails, logo is skipped |

## Colour name tips

- Any English colour name works: "burnt orange", "slate", "cream", "cobalt",
  "sage green", "dusty rose", "charcoal", "goldenrod", etc.
- Crayola names work too: "Alien Armpit", "Absolute Zero"
- Hex always works: "#0255c7", "0255c7", "#fff"
- The colourmapper will find the nearest match for approximate names
- The `cm` tool can be used to look up colours
