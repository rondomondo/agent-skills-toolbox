---
name: mermaid-render
description: Use this skill whenever the user wants to render, export, or convert Mermaid diagrams -- including when they mention architecture diagrams, flowcharts, sequence diagrams, or any .md file containing charts, even if they don't say "mermaid" explicitly. Also trigger when the user asks to visualise a directory of docs, render diagrams from a URL or GitHub repo, or produce image outputs from diagram code.
---

# Mermaid Render Skill

You are rendering Mermaid diagrams from Markdown sources using either the `mermaid-render` script (Docker-backed, non-sandbox) or `mmdc` directly (sandbox).

## Reference material

The `references/` directory contains supporting material for diagram authoring:

- [references/mermaid-reference.md](references/mermaid-reference.md) - colour palette (classDefs) with 16 named colours in dark-text and white-text variants, a quick-reference table, and examples of how to apply classDefs to nodes in `flowchart` and `graph` diagrams.

Consult this file when generating or improving diagrams that use colour styling and when working with complex diagrams that could have many nodes.

---

## How the tool works

- `mermaid-render` wraps `ghcr.io/rondomondo/mermaid-render` (built on `minlag/mermaid-cli`) via Docker.
- It finds every ` ```mermaid ` fenced block in the input `.md` file.
- It renders each block to a numbered image file (e.g. `example1.md-1.svg`).
- It writes a companion `.md` file with `![diagram](./image-N.ext)` references replacing the code blocks.
- The original file is **never modified**.

## Input types

The skill accepts the following types of input:

| Type                   | Example                                       |
| ---------------------- | --------------------------------------------- |
| Single file            | `examples/example1.md`                        |
| Multiple files         | `examples/example1.md examples/example2.md`   |
| Local directory        | `./docs/` or `/some/path/`                    |
| URL (single file)      | `https://example.com/diagram.md`              |
| URL (GitHub directory) | `https://github.com/user/repo/tree/main/docs` |

**Multiple files:** When the user passes more than one `.md` file as arguments, treat each one as an independent single-file input and render them in sequence. Apply the same companion-file guard and read-only mount checks as in _Single file handling_. Report a combined summary at the end.

---

## Your task

When invoked with arguments like `/mermaid-render examples/example1.md -f png`, do the following:

### Step 1 -- Detect the environment

```bash
echo "${IS_SANDBOX:-no}"
```

- `IS_SANDBOX=yes` -> use the **mmdc sandbox render path** throughout (see _Sandbox render_ section).
- Otherwise -> use `mermaid-render ...` throughout (see _Non-sandbox_ section below).

**If `IS_SANDBOX=yes`, immediately resolve the Chromium path before any render attempt:**

```bash
CHROMIUM_DEFAULT="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if [ -x "$CHROMIUM_DEFAULT" ]; then
  CHROMIUM_PATH="$CHROMIUM_DEFAULT"
else
  CHROMIUM_PATH=$(find /opt/pw-browsers -name "chrome" | grep -v headless | head -1)
fi

if [ -z "$CHROMIUM_PATH" ]; then
  echo "ERROR: Chromium not found under /opt/pw-browsers" >&2
  exit 1
fi
```

Use `$CHROMIUM_PATH` (never the hardcoded default) in the puppeteer config written in the _Render command_ section.

### Step 1.5 -- vCPU check (sandbox, single-file only)

**This step applies only when `IS_SANDBOX=yes` AND the input is a single file.** Do not run it for directory or URL inputs -- `$INPUT_FILE` is not yet resolved at this stage for those paths. For directory/URL inputs, skip to Step 2 now and apply the vCPU check per-file inside the handling sections.

When the above conditions are met, check how many vCPUs are available and count how many mermaid blocks the input file contains:

````bash
VCPUS=$(nproc)
DIAGRAM_COUNT=$(grep -c '```mermaid' "$INPUT_FILE" 2>/dev/null || echo 0)
echo "vCPUs: $VCPUS  Diagrams: $DIAGRAM_COUNT"
````

**Decision rule -- split mode:**

If `VCPUS -le 1` AND `DIAGRAM_COUNT -gt 2`, use **split mode** (see _Sandbox split mode_ section below) instead of rendering the file directly. Otherwise render normally.

The threshold of 2 diagrams on a single vCPU is safe; 3+ causes Chromium renderer processes to stack up and compete for the one core, making renders slow and risking OOM on the 4 GB sandbox limit (no swap).

### Step 2 -- Classify the input

Inspect the non-flag arguments:

- **More than one `.md` argument** -> Multiple file input. Render each independently following _Single file handling_, then report a combined summary.
- **Single argument starts with `http://` or `https://`** -> URL input. Go to _URL handling_.
- **Single argument is a directory path** (ends with `/`, or `test -d` is true) -> Directory input. Go to _Directory handling_.
- **Otherwise** -> single file. Go to _Single file handling_.

---

## Single file handling

1. Verify the file exists.
2. If the filename matches a companion pattern (contains `.svg.md`, `.png.md`, `.pdf.md`), stop and inform the user -- this is a rendered output file, not a source. Ask them to pass the original `.md` source instead.
3. If it is under a read-only mount (e.g. `/mnt/`), copy it to `/home/claude/` first.
4. Render it (see _Render command_ section).
5. Copy all output files (rendered images and companion `.md`) to `/mnt/user-data/outputs/` so the user can download them.
6. Report the output files.

---

## Directory handling

1. List all `.md` files up to two levels deep (the directory itself and one level of subdirectories):
    ```bash
    find /path/to/dir -maxdepth 2 -name "*.md" 2>/dev/null
    ```
2. Filter to only files that contain at least one mermaid block:
    ````bash
    find /path/to/dir -maxdepth 2 -name "*.md" | xargs grep -l '```mermaid' 2>/dev/null
    ````
3. Skip any file whose name matches a companion pattern (contains `.svg.md`, `.png.md`, `.pdf.md`) -- these are already-rendered outputs, not sources.
4. For each remaining file, render it following _Single file handling_ (including the output copy step).
5. After all files are rendered, copy any remaining output files not already in `/mnt/user-data/outputs/` there now.
6. Report a summary: how many files found, how many rendered, total diagrams. If files exist beyond one subdirectory level, note that they were skipped -- no silent omissions.

---

## URL handling

There are two sub-cases:

### A) Single file URL

A URL ending in `.md` (or clearly pointing to a single Markdown file):

1. Use the `web_fetch` tool to retrieve the content (do **not** use `curl` -- external domains may be blocked by the egress proxy).
2. Save the content to `/home/claude/<filename>.md` where `<filename>` is derived from the URL path.
3. Render it following _Single file handling_.

### B) GitHub directory URL

A URL of the form `https://github.com/user/repo/tree/<branch>/path/to/dir`:

1. Convert the GitHub tree URL to a GitHub API contents URL:
    - `https://github.com/user/repo/tree/main/docs`
    - -> `https://api.github.com/repos/user/repo/contents/docs?ref=main`
2. Use `web_fetch` to retrieve the directory listing JSON.
3. Validate the response before iterating: confirm it parses as a JSON array and contains at least one entry with `"type"` and `"name"` fields. If the response is HTML, a rate-limit message, or unparseable JSON, stop and report the raw response to the user rather than silently failing.
4. Parse the JSON to find all entries where `"type": "file"` and `"name"` ends in `.md`.
5. Skip companion files (name contains `.svg.md`, `.png.md`, `.pdf.md`).
6. For each `.md` file, use `web_fetch` on its `download_url` field to fetch the content.
7. Save each to `/home/claude/<filename>.md` and render it (including copying outputs to `/mnt/user-data/outputs/` per _Single file handling_).
8. Report a summary.

**Note**: `raw.githubusercontent.com` and `api.github.com` may be blocked by the sandbox egress proxy. If `web_fetch` fails with a network/403 error, inform the user that GitHub URLs are not reachable from the sandbox and ask them to download the file(s) locally and upload instead.

---

## Sandbox split mode

Use this path when `IS_SANDBOX=yes`, `VCPUS <= 1`, and `DIAGRAM_COUNT > 2`.

### Why

On a single-vCPU sandbox, `mmdc` spawns one headless Chromium renderer process per diagram block when rendering a multi-diagram file. With 3+ diagrams these processes all queue on the same core simultaneously, causing slow serialised execution with full Chromium RSS overhead resident for the entire duration. Splitting into one-diagram-per-file means each render gets a clean Chromium instance that starts, renders, and fully exits before the next one begins -- faster, lower peak RSS, and no risk of silent OOM.

### Split procedure

**1. Split the source file into per-diagram temp files:**

````python
import re, os

with open(INPUT_FILE) as f:
    content = f.read()

# Split on H1/H2 headings (or on mermaid block boundaries if no headings)
sections = re.split(r'\n(?=#{1,2} )', content.strip())
# Filter to only sections that contain a mermaid block
sections = [s for s in sections if '```mermaid' in s]

STEM = os.path.splitext(os.path.basename(INPUT_FILE))[0]
split_files = []
for i, section in enumerate(sections, 1):
    fname = f"/home/claude/{STEM}-split-{i:02d}.md"
    with open(fname, 'w') as f:
        f.write(section.strip() + '\n')
    split_files.append(fname)
````

If the file has no headings at all, split purely on mermaid block boundaries instead -- extract each ` ```mermaid ... ``` ` block (plus any title comment above it) into its own file.

**2. Render each split file serially** using the standard sandbox render command (see _Render command_ section). Render one, wait for it to complete and Chromium to exit, then render the next. Never render two split files concurrently.

**3. Collect outputs** -- after all splits are rendered, gather all output images. `mmdc` names them `<stem>-split-NN-1.<ext>` (one diagram per split file = always index 1).

**Note:** Step 4 (Recombine) below produces the companion `.md` for split mode. For standard sandbox renders (non-split), the companion `.md` is generated separately -- see _Standard sandbox companion `.md`_ in the _Output location_ section.

**4. Recombine** -- produce a single companion Markdown file that references all rendered images in order:

```python
STEM = os.path.splitext(os.path.basename(INPUT_FILE))[0]
output_md = f"/home/claude/{STEM}-rendered.md"
lines = [f"# {STEM} -- rendered diagrams\n"]
for img_path in sorted(output_images):   # output_images = list of rendered file paths
    title = os.path.basename(img_path)
    lines.append(f"![{title}](./{os.path.basename(img_path)})\n")
with open(output_md, 'w') as f:
    f.writelines(lines)
```

Copy all rendered images **and** the companion `.md` to `/mnt/user-data/outputs/`.

**5. Clean up** -- remove the temporary split `.md` files from `/home/claude/` after recombination.

**6. Report** -- tell the user:

- That split mode was used and why (single vCPU, N diagrams)
- How many split files were rendered
- The name of the combined companion Markdown
- Any individual render failures (show stderr per diagram)

---

## Render command

### Sandbox (IS_SANDBOX=yes)

Write the puppeteer config once per session using `$CHROMIUM_PATH` resolved in Step 1, then reuse:

```bash
cat > /tmp/puppeteer-config.json << EOF
{
  "executablePath": "$CHROMIUM_PATH",
  "args": ["--no-sandbox", "--disable-setuid-sandbox"]
}
EOF

mmdc -i "$INPUT_FILE" -o "$OUTPUT_FILE" --puppeteerConfigFile /tmp/puppeteer-config.json
```

### Non-sandbox (Docker)

Locate `mermaid-render` -- prefer a copy bundled with this skill, fall back to the system install:

```bash
if [[ -x "./mermaid-render" ]]; then
  MERMAID_RENDER="./mermaid-render"
elif [[ -x "$(dirname "$0")/mermaid-render" ]]; then
  MERMAID_RENDER="$(dirname "$0")/mermaid-render"
elif command -v mermaid-render &>/dev/null; then
  MERMAID_RENDER="mermaid-render"
else
  echo "ERROR: mermaid-render not found. Install it via: make install" >&2
  exit 1
fi

"$MERMAID_RENDER" "$INPUT_FILE" [options]
```

**`-d` / `--dir` flag:** The wrapper mounts `$PWD` at `/data` inside the Docker container. If the input file is outside `$PWD` (e.g. an absolute path in `/home/user/docs/`), pass `-d /home/user/docs` so the correct directory is mounted and the file is reachable. Without it, Docker will not be able to see the file and the render will fail with a file-not-found error inside the container.

### Flag mapping (wrapper flags -> mmdc flags)

| mermaid-render flag | mmdc equivalent                                                                           |
| ------------------- | ----------------------------------------------------------------------------------------- |
| `-f` / `--format`   | `--outputFormat` (jpg/gif/webp: renders PNG intermediate, then `convert` to final format) |
| `-t` / `--theme`    | `--theme`                                                                                 |
| `-b` / `--bg`       | `--backgroundColor`                                                                       |
| `-w` / `--width`    | `--width`                                                                                 |
| `-H` / `--height`   | `--height`                                                                                |
| `-s` / `--scale`    | `--scale`                                                                                 |

---

## Options reference

| Flag | Long form  | Description                                                                                                                                |
| ---- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `-f` | `--format` | Output format: `svg` (default), `png`, `pdf`, `jpg`, `gif`, `webp` — jpg/gif/webp render via PNG intermediate then ImageMagick `convert`   |
| `-t` | `--theme`  | Theme: `default`, `dark`, `forest`, `neutral`                                                                                              |
| `-b` | `--bg`     | Background colour: `white`, `transparent`, `'#rrggbb'`                                                                                     |
| `-w` | `--width`  | Canvas width in pixels                                                                                                                     |
| `-H` | `--height` | Canvas height in pixels                                                                                                                    |
| `-s` | `--scale`  | Pixel density / scale factor (use 2-3 for retina PNG)                                                                                      |
| `-d` | `--dir`    | Override the host directory mounted into Docker (non-sandbox only -- use when the input file is outside `$PWD`, e.g. `-d /home/user/docs`) |
| `-h` | `--help`   | Print built-in help                                                                                                                        |

## Defaults

- Format: `svg`
- Scale: `2` (or `3` when format is `jpg`, `gif`, or `webp`, for a high-quality PNG intermediate)
- Background: theme default (use `transparent` for dark-mode embedding)

---

## Output location

Output file naming differs between the two render paths. Use the correct pattern when reporting results to the user.

### Sandbox path (mmdc)

For input `examples/example1.md` rendered as SVG, `mmdc` writes numbered images alongside the source file:

- `examples/example1.md-1.svg`
- `examples/example1.md-2.svg`
- ... (one per diagram block)

#### Standard sandbox companion `.md`

After `mmdc` finishes (non-split path), generate a companion `.md` file to match the non-sandbox output:

```python
import os, glob

STEM = os.path.basename(INPUT_FILE)          # e.g. "example1.md"
OUT_DIR = os.path.dirname(os.path.abspath(INPUT_FILE))
EXT = FORMAT if FORMAT else "svg"            # format passed by user, default svg

# Collect rendered images in order
images = sorted(glob.glob(os.path.join(OUT_DIR, f"{STEM}-*.{EXT}")))

companion = os.path.join(OUT_DIR, f"{STEM}.{EXT}.md")
with open(companion, "w") as f:
    for img in images:
        name = os.path.basename(img)
        f.write(f"![{name}](./{name})\n\n")
```

The companion file is named `example1.md.svg.md` (or `.png.md`, `.pdf.md` etc.) and lives alongside the rendered images. Include it in the files copied to `/mnt/user-data/outputs/` and report it to the user.

### Non-sandbox path (mermaid-render wrapper)

The Docker wrapper writes output into a `data/` subdirectory relative to the working directory, using the format stem:

- `data/example.svg-1.svg`, `data/example.svg-2.svg`, ...
- `data/example.svg.md` (companion Markdown with `![diagram](./example.svg-N.svg)` references)

---

## Previewing diagrams

Always share these tips with the user after a successful render:

- **VS Code**: Install the [Mermaid Preview](https://marketplace.visualstudio.com/items?itemName=vstirbu.vscode-mermaid-preview) extension to preview diagrams directly in the editor.
- **GitHub**: Mermaid rendering is built into GitHub -- ` ```mermaid ` fenced blocks render automatically when viewed in a repository.

---

## Error handling

| Symptom                                                    | Likely cause                     | Fix                                                                                               |
| ---------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------- |
| `Chromium not found under /opt/pw-browsers`                | Chromium version path changed    | Auto-detect ran and found nothing -- check `/opt/pw-browsers` manually; report to user            |
| `Chrome won't launch` / puppeteer crash                    | Missing sandbox flags            | Ensure `--no-sandbox` and `--disable-setuid-sandbox` are in the puppeteer config args             |
| File renders 0 diagrams                                    | Companion file passed directly   | Check filename for `.svg.md` / `.png.md` / `.pdf.md` -- pass the source `.md` instead             |
| Directory scan finds no files                              | Only nested >1 level deep        | Files beyond one subdirectory are skipped by design -- user must pass paths explicitly            |
| `web_fetch` returns HTML or unparseable JSON on GitHub URL | API rate limit or redirect       | Show raw response to user; ask them to download and upload the file directly                      |
| `web_fetch` fails with 403/network error on GitHub URL     | Domain blocked by egress proxy   | Inform user; ask them to upload the file directly                                                 |
| `mermaid-render` not found (non-sandbox)                   | Not installed or not in PATH     | Run `make install` from the toolbox dir, or ensure `./mermaid-render` is present in the skill dir |
| Docker not running (non-sandbox)                           | Docker Desktop stopped           | Tell user to start Docker Desktop                                                                 |
| File not found                                             | Wrong path or working directory  | Report the exact path tried; suggest `pwd` to check working directory                             |
| PNG looks low-res                                          | Scale factor not set             | Use `--scale 2` or `--scale 3` for retina-quality PNG output                                      |
| PDF output missing content                                 | PDF requires specific mmdc flags | Ensure `-f pdf` is passed; PDF support depends on mmdc version                                    |
| Renders very slow / Chromium processes stacking up         | Multi-diagram file on 1 vCPU     | Check `nproc`; if 1 vCPU and >2 diagrams, use sandbox split mode (see _Sandbox split mode_)       |
| Split mode produces wrong diagram count                    | File has no H1/H2 headings       | Fall back to mermaid-block-boundary splitting; each fenced block becomes its own split file       |

Always show raw stderr from the render so the user can see which diagrams succeeded (✅) or failed (❌).
