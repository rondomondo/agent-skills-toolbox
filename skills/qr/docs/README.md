# qr-cli -- A docker based QR Code generator

Two ways to generate QR codes - pick whichever fits your flow:

**1. CLI tool** -- generate QR codes by piping flags or JSON straight into the included dockerised qr-cli app, get a JSON<br>
payload back with a base64 image and dataUri. No dependencies (node etc) are required on the host.

**2. AI agent skill (`/qr`)** -- generate QR codes, using plain English, which describes all the properties, look and<br>
feel that you want in the QR Code image.

```shell 
# skill example
/qr https://browserleaks.com/geo rounded, 'dead blue eyes' on 'creamed butter', low error correction WebP 450px with a border and margin of 30px 
```

The skill translates your description into the right flags and hands the image back inline.

---

Built on [qr-code-styling](https://github.com/oblakstudio/qr-code-styling) with a headless NodeJS runtime, [node-canvas](https://github.com/automattic/node-canvas), [Cairo](https://github.com/jferrettiboke/cairo), and [Sharp](https://sharp.pixelplumbing.com/).

Customise dot shapes, corner styles, colours, gradients, embedded logos, error correction levels, and output format (PNG, JPEG, WebP, SVG, dataUri).

Input accepts `--key=value` flags, a `--json='{...}'` blob, or piped JSON via stdin - and all three can be combined and merged at invocation time.

Output is always a consistent JSON object:

```json
{ "success": true, "meta": { ...format, dimensions, colours, timing... }, "image": { ...base64, dataUri, filename... } }
```

Errors use the same schema (`"success": false`) so [jq](https://jqlang.org/) pipelines never need to branch on output shape or config selection.

Runs as a non-root user in a multi-stage Debian image. Works as a Docker sidecar, local dev tool, or CI step.
  
---

## Quick start

**Option A -- Docker Hub (no clone needed):**

<table><tr>
<td>

```bash
# turn off annoying spam
export DOCKER_CLI_HINTS=false

docker pull rondomondo/qr-cli:latest
docker run --rm rondomondo/qr-cli:latest \
  --data="https://example.com" \
  --format=webp \
  --border=10 \
  --margin=20 \
  --dotsOptions.type=extra-rounded \
  --dotsOptions.color="#185FA5" \
  --backgroundOptions.color="#E6F1FB" 2> /dev/null \
  | jq -r '.image.base64' | base64 -d > qr.webp

file qr.webp
```

</td>
<td><img src="assets/images/default/300x300_185FA5_E6F1FB_default.webp" width="200"/></td>
</tr></table>


**Option B -- clone, build, and run the full example suite:**

```bash
git clone https://github.com/rondomondo/qr-cli.git && cd qr-cli
make build
make examples
make skill-examples
```

---

## Makefile targets

| Target | Description |
|---|---|
| `make build` | Build the Docker image (`rondomondo/qr-cli:latest`) |
| `make build-clean` | Build with `--no-cache` |
| `make usage` | Show the generator's `--help` output as pretty-printed JSON |
| `make shell` | Open an interactive bash shell inside the container |
| `make gen-examples` | Parse `EXAMPLES.md` and regenerate `scripts/run_examples.sh` |
| `make examples` | Regenerate `scripts/run_examples.sh` then run all examples |
| `make skill-examples` | Print the `/qr` skill example gallery (ANSI-coloured, ~30 examples) |
| `make skill-install` | Install the `/qr` skill into `~/.claude/skills/qr/` with Python fallback support |
| `make skill-zip` | Zip `.claude/skills/qr/` into `.claude/skills/qr.zip` |
| `make doctor` | Show environment info useful for bug reports |
| `make venv` | Create Python virtual environment (if absent) |
| `make py-install` | Install qr-cli in editable mode (Docker primary, Node fallback) |
| `make py-install-node` | Pre-install bundled Node deps for the Node backend fallback |
| `make py-test` | Run Python package tests |
| `make py-lint` | Lint `qr_cli/` with ruff |
| `make py-build` | Build sdist + wheel ready for upload |
| `make py-publish` | Upload release to PyPI |
| `make py-check-backend` | Report which backend qr-cli will use in this environment |
| `make demo` | Regenerate terminal demo GIF for `TAPE=<file>` (default: `demo.tape`) |
| `make demo-all` | Regenerate terminal demo GIFs for all `*.tape` files in `demo/` |
| `make clean` | Remove Docker image, build artefacts, caches, and temp files |

---

## Usage

### Basic -- URL to PNG

<details>
<summary>

```bash
docker run --rm rondomondo/qr-cli:latest --project="daveco" \
  --data="https://example.com"
```

</summary>

#### JSON result
```json
{
  "success": true,
  "meta": {
    "format": "png",
    "mimeType": "image/png",
    "width": 300,
    "height": 300,
    "type": "canvas",
    "data": "https://example.com",
    "project": "daveco",
    "sizeBytes": 1539,
    "durationMs": 147,
    "generatedAt": "2026-05-02T20:17:50.448Z",
    "errorCorrectionLevel": "Q",
    "dotsType": "square",
    "dotsColor": "#000000",
    "backgroundColor": "#ffffff",
    "hasImage": false,
    "margin": 0,
    "border": 0
  },
  "image": {
    "filename": "assets/images/daveco/300x300_000000_FFFFFF_daveco.png",
    "generated": "2026-05-02T20:17:50.448Z",
    "base64": "iVBORw0KGgoAAAANSUhEUgAAASwAAAEsCAYAAAB5fY51AAAABmJLR0...",
    "dataUri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAAEs..."
  }
}
```

</details>

### Specify image format

<details>
<summary>

```bash
docker run --rm rondomondo/qr-cli:latest \
  --data="https://example.com" \
  --format=svg
```

</summary>

Supported formats: `png` (default), `jpeg`, `webp`, `svg`

#### JSON result
```json
{
  "success": true,
  "meta": {
    "format": "svg",
    "mimeType": "image/svg+xml",
    "width": 300,
    "height": 300,
    "type": "svg",
    "data": "https://example.com",
    "sizeBytes": 23837,
    "durationMs": 143,
    "generatedAt": "2026-05-02T20:20:22.495Z",
    "errorCorrectionLevel": "Q",
    "dotsType": "square",
    "dotsColor": "#000000",
    "backgroundColor": "#ffffff",
    "hasImage": false,
    "margin": 0,
    "border": 0
  },
  "image": {
    "filename": "qr.svg",
    "generated": "2026-05-02T20:20:22.495Z",
    "base64": "PD94bWwgdmVyc2lvbj0iMS4wIiBzdGFuZGFsb25lPSJubyI/Pg0KPH...",
    "dataUri": "data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBz..."
  }
}
```

</details>

### Full styling via flags

<details>
<summary>

```bash
docker run --rm rondomondo/qr-cli:latest \
  --data="https://example.com" \
  --width=400 \
  --height=400 \
  --format=png \
  --border=20 \
  --margin=10 \
  --dotsOptions.type=rounded \
  --dotsOptions.color="#185FA5" \
  --backgroundOptions.color="#E6F1FB" \
  --cornersSquareOptions.type=extra-rounded \
  --cornersSquareOptions.color="#185FA5" \
  --qrOptions.errorCorrectionLevel=H
```

</summary>


#### JSON result
```json
{
  "success": true,
  "meta": {
    "format": "svg",
    "mimeType": "image/svg+xml",
    "width": 400,
    "height": 400,
    "type": "svg",
    "data": "https://example.com",
    "sizeBytes": 33606,
    "durationMs": 156,
    "generatedAt": "2026-05-02T20:21:20.076Z",
    "errorCorrectionLevel": "H",
    "dotsType": "rounded",
    "dotsColor": "#185FA5",
    "backgroundColor": "#E6F1FB",
    "hasImage": false,
    "margin": 10,
    "border": 20
  },
  "image": {
    "filename": "qr.svg",
    "generated": "2026-05-02T20:21:20.076Z",
    "base64": "PD94bWwgdmVyc2lvbj0iMS4wIiBzdGFuZGFsb25lPSJubyI/Pg0KPH...",
    "dataUri": "data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBz..."
  }
}
```

</details>

### Pass a full JSON config

<details>
<summary>

```bash
docker run --rm rondomondo/qr-cli:latest \
  --json='{
    "data": "https://example.com",
    "width": 600,
    "height": 600,
    "margin": 20,
    "format": "png",
    "project": "daveco",
    "border": 10,
    "dotsOptions": {
      "type": "extra-rounded",
      "color": "#185FA5"
    },
    "backgroundOptions": {
      "color": "#E6F1FB"
    },
    "cornersDotOptions": {
      "type": "dot",
      "color": "#185FA5"
    },
    "qrOptions": {
      "errorCorrectionLevel": "H"
    } 
  }'

```
</summary>

#### JSON result
```json
{
  "success": true,
  "meta": {
    "format": "png",
    "mimeType": "image/png",
    "width": 600,
    "height": 600,
    "type": "canvas",
    "data": "https://example.com",
    "project": "daveco",
    "sizeBytes": 38361,
    "durationMs": 217,
    "generatedAt": "2026-05-02T20:35:23.346Z",
    "errorCorrectionLevel": "H",
    "dotsType": "extra-rounded",
    "dotsColor": "#185FA5",
    "backgroundColor": "#E6F1FB",
    "hasImage": false,
    "margin": 20,
    "border": 10
  },
  "image": {
    "filename": "assets/images/daveco/600x600_185FA5_E6F1FB_daveco.png",
    "generated": "2026-05-02T20:35:23.346Z",
    "base64": "iVBORw0KGgoAAAANSUhEUgAAAlgAAAJYCAYAAAC+ZpjcAAAABmJLR0...",
    "dataUri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAlgAAAJY..."
  }
}```
</details>


### Pipe JSON via stdin

<details>
<summary>

```bash
echo '{
  "data": "https://example.com",
  "width": 300,
  "format": "png"
}' | docker run --rm -i rondomondo/qr-cli:latest
```

</summary>

#### JSON result
```json
{
  "success": true,
  "meta": {
    "format": "png",
    "mimeType": "image/png",
    "width": 300,
    "height": 300,
    "type": "canvas",
    "data": "https://example.com",
    "sizeBytes": 1539,
    "durationMs": 152,
    "generatedAt": "2026-05-02T20:40:14.125Z",
    "errorCorrectionLevel": "Q",
    "dotsType": "square",
    "dotsColor": "#000000",
    "backgroundColor": "#ffffff",
    "hasImage": false,
    "margin": 0,
    "border": 0
  },
  "image": {
    "filename": "qr.png",
    "generated": "2026-05-02T20:40:14.125Z",
    "base64": "iVBORw0KGgoAAAANSUhEUgAAASwAAAEsCAYAAAB5fY51AAAABmJLR0...",
    "dataUri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAAEs..."
  }
}
```

</details>

### Save the image to disk

Mount a local directory as `/output` and pass `--save-to` to write directly to it -- no base64 decode step needed:

```bash
mkdir -p output
docker run --rm \
  -v "$(pwd)/output:/output" \
  rondomondo/qr-cli:latest \
  --data="https://example.com" \
  --save-to=/output/qr.png
```

Or decode the base64 from JSON if you prefer the pipe approach:

```bash
docker run --rm rondomondo/qr-cli:latest --data="https://example.com" \
  | jq -r '.image.base64' \
  | base64 -d > qr.png
```

---

## Examples

A few examples below to give you a taste. [EXAMPLES.md](EXAMPLES.md) has the full set covering every dot style, corner style, error correction level, and output format. Run them all in one go:

```shell
make examples
```

### Full styling with logo (JSON blob)

<details>
<summary>

```bash
docker run --rm rondomondo/qr-cli:latest \
  --json='{
    "data": "https://facebook.com",
    "width": 600, "height": 600,
    "format": "png", "border": 10, "margin": 20,
    "image": "https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg",
    "imageOptions": { "crossOrigin": "anonymous", "margin": 10 },
    "qrOptions": { "errorCorrectionLevel": "H" },
    "dotsOptions": { "type": "extra-rounded", "color": "#185FA5" },
    "backgroundOptions": { "color": "#E6F1FB" },
    "cornersSquareOptions": { "type": "extra-rounded", "color": "#185FA5" },
    "cornersDotOptions": { "type": "dot", "color": "#185FA5" }
  }' \
  | jq -r '.image.base64' | base64 -d > qr.png
```

</summary>

<img src="assets/images/daveco/qr.all.logo.png" width="200"/><br><sub>Facebook logo, Sky haze palette</sub>

</details>

### Dot styles (CLI flags)

<details>
<summary>

```bash
docker run --rm rondomondo/qr-cli:latest \
  --data="https://example.com" --format=png \
  --border=10 --margin=10 \
  --dotsOptions.type=extra-rounded \
  --dotsOptions.color="#2B4D00" \
  --backgroundOptions.color="#D4F299" \
  | jq -r '.image.base64' | base64 -d > qr.png
```

</summary>

<img src="assets/images/daveco/dots-extra-rounded.png" width="130"/><br><sub>extra-rounded</sub><br>

</details>

### Corner styles (JSON blob)

<details>
<summary>

```bash
docker run --rm rondomondo/qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png",
    "border":10,"margin":10,
    "dotsOptions":{"color":"#064E3B","type":"rounded"},
    "cornersSquareOptions":{"color":"#064E3B","type":"extra-rounded"},
    "backgroundOptions":{"color":"#A7F3D0"}}' \
  | jq -r '.image.base64' | base64 -d > qr.png
```

</summary>

<img src="assets/images/daveco/corners-extra-rounded.png" width="130"/><br><sub>extra-rounded corners</sub><br>

</details>


See all skill equivalents for every example in `EXAMPLES.md`:

```bash
make skill-examples
```

---

## `/qr` skill

If you use something like [Claude Code](https://claude.ai/code), this repo ships a `/qr` skill
that lets you generate QR codes in plain English directly from the chat panel.

### Setup

The skill files live at `./.claude/skills/qr`. Run `make skill-install` to copy
them to `~/.claude/skills/qr/` -- Claude Code will pick them up automatically.
There is also a zipped version at `./.claude/skills/qr.zip` for convenience.

### Usage

```
/qr <url> [natural language options]
```

Colours, dot styles, sizes, and logos are all described in plain English:

```
/qr https://example.com
/qr https://example.com rounded royal blue on cream
/qr https://example.com extra-rounded midnight blue on ivory 500px
/qr https://example.com svg slate on white
/qr https://example.com extra-rounded #175EF0 on #E0E0E0 round corners dot corner dots high error correction 600px with logo https://example.com/logo.svg
```

### What the skill does

1. Parses your intent (colour names, style keywords, size, format, logo URL).
2. Resolves ~30K English colour names to hex via `colourmapper`.
3. Calls `scripts/qr-skill.sh`, which wraps the Docker image.
4. **Docker backend:** mounts `./output` into the container and passes `--save-to` so the
   image is written directly to disk -- no base64 decode on the host. Logo URLs are passed
   straight through (no pre-fetch needed when running locally).
   **Node backend (no Docker):** calls `python3 -m qr_cli --backend=node` with `--save-to`.
5. Saves the image to `output/{project}/{width}x{height}_{dots}_{bg}_{project}.{format}`.
6. Reports a summary with a clickable link and a fenced `open` command you can
   copy straight from the VS Code copy button:

```
open output/default/600x600_175ef0_e0e0e0_default.png
```

Raw flags also pass straight through, so you can mix natural language and
explicit options in the same command.

### `/qr` skill examples

Three examples picked from `make skill-examples` to show the natural-language shorthand:

<details>
<summary>

```
/qr https://example.com extra-rounded #2B4D00 on #D4F299
```

</summary>

<img src="assets/images/default/skill-extra-rounded-forest.png" width="160"/><br><sub>extra-rounded</sub><br>

</details>

<details>
<summary>

```
/qr https://example.com classy rounded #042C53 on #B5D4F4
```

</summary>

<img src="assets/images/default/skill-classy-rounded-chambray.png" width="160"/><br><sub>classy-rounded</sub><br>

</details>

<details>
<summary>

```
/qr https://example.com rounded #5C3A00 on #FDE68A round corners dot corner dots
```

</summary>

<img src="assets/images/default/skill-rounded-golden-harvest.png" width="160"/><br><sub>rounded corners dot-corners</sub><br>

</details>



### Skill quick-reference

| What you say | What it does |
|---|---|
| `rounded`, `circles`, `classy`, `extra-rounded` | Sets dot shape |
| `round corners`, `dot corners`, `square corners` | Sets corner square style |
| `dot corner dots` | Sets corner dot style |
| `L`, `M`, `Q`, `H`  error correction | Sets QR error correction level |
| `svg`, `jpg`, `webp`, `png` | Changes output format (default: `png`) |
| `400px` or `600x400` | Sets output dimensions |
| `with logo <url>` | Embeds a logo (bumps error correction to H automatically) |
| Any colour name or hex | Sets dot / background / corner colours |

### See all skill equivalents for the examples

Tip:
```bash
make skill-examples
```

This prints a `/qr` skill command (and its natural-language shorthand) for every
example in `EXAMPLES.md`.

---

## Helper scripts

| Script | Purpose |
|---|---|
| `scripts/extract_examples.py` | Parses `EXAMPLES.md`, extracts every `bash` fenced block, and writes `run_examples.sh` with `[N/total]` progress labels. Re-run via `make gen-examples` after editing `EXAMPLES.md`. |
| `.claude/skills/qr/scripts/extract_skill_examples.py` | Prints a formatted gallery of `/qr` skill examples with ANSI colour. Invoked by `make skill-examples` and by the skill itself when you type `/qr examples`. |

---

## Output schema

```jsonc
{
  "success": true,
  "meta": {
    "format": "png",                        // output format
    "mimeType": "image/png",
    "width": 300,
    "height": 300,
    "type": "canvas",                       // qr-code-styling render type
    "data": "https://...",                  // the encoded string
    "project": "daveco",                    // project name if supplied, else omitted
    "sizeBytes": 12345,                     // raw image buffer size in bytes
    "durationMs": 42,                       // time taken to generate in ms
    "generatedAt": "2024-01-01T00:00:00Z", // UTC ISO 8601 timestamp
    "errorCorrectionLevel": "Q",
    "dotsType": "rounded",
    "dotsColor": "#0255c7",
    "backgroundColor": "#fdfbd4",
    "hasImage": false,
    "margin": 10,
    "border": 20                            // pixels added around the QR code
  },
  "image": {
    "filename": "assets/images/daveco/300x300_0255C7_FDFBD4_daveco.png",    // assets/images/{project}/{width}x{height}_{dots}_{bg}_{project}.{format})
    "generated": "2024-01-01T00:00:00Z",   // UTC ISO 8601 timestamp (same as meta.generatedAt)
    "base64": "<base64 string>",
    "dataUri": "data:image/png;base64,<base64 string>"
  }
}
```

On error (written to both stdout and stderr so `jq` pipelines can catch it):
```json
{ "success": false, "error": "Missing required option: \"data\"" }
```

### Useful jq extractions

```bash
# Save to disk, decoding base64
docker run --rm rondomondo/qr-cli:latest --data="https://example.com" \
  | jq -r '.image.base64' | base64 -d > qr.png

# One-liner: generate and save using the suggested filename (requires --project)
OUT=$(docker run --rm rondomondo/qr-cli:latest --data="https://example.com" --project=myapp --format=png)
mkdir -p $(dirname $(echo $OUT | jq -r '.image.filename'))
echo $OUT | jq -r '.image.base64' | base64 -d > $(echo $OUT | jq -r '.image.filename')

# Check success before using
if echo $OUT | jq -e '.success' > /dev/null; then
  echo $OUT | jq -r '.image.base64' | base64 -d > qr.png
else
  echo $OUT | jq -r '.error'
fi

# Print generation time
echo $OUT | jq '.meta.durationMs'
```

---

## All supported options

These map 1:1 to the [qr-code-styling API](https://github.com/oblakstudio/qr-code-styling#api-documentation):

| Flag / JSON key | Type | Default | Description |
|---|---|---|---|
| `data` | string | **required** | The string/URL to encode |
| `width` | number | 300 | Canvas width in px |
| `height` | number | 300 | Canvas height in px |
| `format` | string | `png` | Output format: `png`, `jpeg`, `webp`, `svg` |
| `margin` | number | 0 | Margin around the QR in px |
| `border` | number | 0 | Pixels added around the QR code |
| `project` | string | -- | Namespaces the suggested output filename as `assets/images/{project}/{width}x{height}_{dots}_{bg}_{project}.{format}` |
| `image` | string | -- | URL of logo to embed in the centre |
| `dotsOptions.type` | string | `square` | `rounded`, `dots`, `classy`, `classy-rounded`, `square`, `extra-rounded` |
| `dotsOptions.color` | string | `#000000` | Dot colour |
| `backgroundOptions.color` | string | `#ffffff` | Background colour |
| `cornersSquareOptions.type` | string | -- | `dot`, `square`, `extra-rounded` |
| `cornersSquareOptions.color` | string | -- | Corner square colour |
| `cornersDotOptions.type` | string | -- | `dot`, `square` |
| `cornersDotOptions.color` | string | -- | Corner dot colour |
| `qrOptions.errorCorrectionLevel` | string | `Q` | `L`, `M`, `Q`, `H` |
| `imageOptions.margin` | number | 0 | Logo margin in px |
| `imageOptions.imageSize` | number | 0.4 | Logo size coefficient (0-1) |
| `imageOptions.hideBackgroundDots` | boolean | true | Hide dots behind logo |
| `imageOptions.crossOrigin` | string | -- | `anonymous` for cross-origin logos |

Gradient options (on `dotsOptions`, `backgroundOptions`, `cornersSquareOptions`, `cornersDotOptions`) must be supplied as JSON:

```json
{
  "dotsOptions": {
    "gradient": {
      "type": "linear",
      "rotation": 0,
      "colorStops": [
        { "offset": 0, "color": "#000000" },
        { "offset": 1, "color": "#0255c7" }
      ]
    }
  }
}
```
<!-- 
## Dependencies
docker
jq
make -->

