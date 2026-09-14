# pdf-strip

Strips all metadata from PDF files. Removes both the legacy `/Info` dictionary (Author, Title, Producer, CreationDate, etc.) and the XMP metadata stream embedded in `/Root/Metadata`.

Running `pdf-strip <file>` strips metadata by default and writes `<base>.stripped.pdf` alongside the original. Use `--check` to inspect any found metadata without modifying.

> **Also available as an [Agent Skill](#claude-code-skill)** -- install it to strip PDF metadata directly from Claude Code with no terminal required. Use the `/pdf-strip` slash command or just describe what you want and your AI Agent will handle it.

<details>
<summary><b>Why strip PDF metadata anyway?</b>
</summary>
<br>
When you share a PDF, you may be sharing a lot more than you realise. PDF files carry hidden metadata embedded by the tools that created them. Its invisible to readers but trivially extracted by anyone who knows to look. None of it is obvious in the document 

**What gets embedded:**

- **Provenance** — `Author`, `Creator`, and XMP fields record who made the document and which software was used (`Adobe Acrobat 23.1`, `Microsoft Word 2019`). Tool version information is handy for attackers scoping known vulnerabilities.
- **Revision history** — `CreationDate`, `ModDate`, and XMP revision counts expose your drafting timeline — when work started, how many rounds it went through, and when it was finalised.
- **Contributors** — collaborative tools (Google Docs exports, Office 365) can silently embed every editor and reviewer who touched the file.
- **Internal paths** — some applications write the original save location into XMP (e.g. `\\fileserver\confidential\Q3-board-pack.docx`), leaking internal naming conventions, folder structures, and server names.
- **Organisation details** — `Company`, `Keywords`, subject classifications, and Dublin Core fields can surface internal project names, team structures, or sensitivity labels that were never intended for outside eyes.
- **macOS extended attributes** — Apple's Finder and Spotlight silently tag files with `xattr` blobs including `com.apple.quarantine` and `com.apple.metadata:kMDItemWhereFroms` (the URL a file was downloaded from). These travel with the file when shared and can reveal source systems or download origin.

Stripping this before sharing is good practice: it reduces unintentional disclosure, limits what can be inferred about your environment, and produces smaller files.

**Not sure what's hiding in a file?** Run `pdf-strip --check <file>` first — it prints everything embedded so you can see exactly what you'd be sharing.

</details>

<br>

---

## Browser version (Pyodide)

A browser-based version of this tool runs entirely client-side using
[Pyodide](https://pyodide.org) -- no installation, no server, no data leaves your machine.

**Try it:** [find4.org/pdfstrip](https://find4.org/pdfstrip/#)

[![pdfstrip screenshot](images/pdfstrip-screenshot.png)](https://find4.org/pdfstrip/#)

Upload or drop a file to check and strip it of metadata -- all in the browser.

The Pyodide port lives at [github.com/rondomondo/pyodide](https://github.com/rondomondo/pyodide).

---

## Quickstart

> 💡 Prerequisite: Have you a [`test PDF file`] with metadata to try?

```bash
docker run --rm ghcr.io/rondomondo/pdf-strip install
```

### Install from the ghcr.io image

Using the pre-built [`docker image`] available at [`ghcr.io/rondomondo/pdf-strip`] run these steps

```bash
setopt interactivecomments

# 1. Stream the pdf-strip wrapper script to disk and make it executable
docker run --rm ghcr.io/rondomondo/pdf-strip:latest install > pdf-strip && chmod +x pdf-strip

# 2. Install it system-wide
install -m 755 pdf-strip /usr/local/bin/pdf-strip

# 3. get a PDF with metadata to test with (if we don't already have one)
EXAMPLE_PDF=test/example.pdf
EXAMPLE_STRIPPED_PDF=test/example.stripped.pdf

! test -e "$EXAMPLE_PDF" && curl --silent -L --create-dirs -o "${EXAMPLE_PDF}" https://abcdef.ai/$EXAMPLE_PDF

# 4. run pdf-strip to strip this test PDF file (default behaviour)
pdf-strip "$EXAMPLE_PDF"

# 5. check the PDF file size before stripping
printf "$(wc -c < ${EXAMPLE_PDF}) bytes in ${EXAMPLE_PDF} before stripping" 

# 6. check the PDF file size after stripping - should be less
printf "$(wc -c < ${EXAMPLE_STRIPPED_PDF}) bytes in ${EXAMPLE_PDF} after stripping" 

```


### Install and use from the github repository
Clone the github project repository, build and install etc., it locally with these steps

```bash
setopt interactivecomments

# 1. Clone the toolbox repo which has the pdf-strip tool
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/pdf-strip

# 2. install the `pdf-strip` tool to /usr/local/bin
make install

# 3. run pdf-strip to strip this test PDF file (default behaviour)
EXAMPLE_PDF=test/example.pdf
EXAMPLE_STRIPPED_PDF=test/example.stripped.pdf

pdf-strip "$EXAMPLE_PDF"

# 4. check the PDF file size before stripping
printf "$(wc -c < ${EXAMPLE_PDF}) bytes in ${EXAMPLE_PDF} before stripping" 

# 5. check the PDF file size after stripping - should be less
printf "$(wc -c < ${EXAMPLE_STRIPPED_PDF}) bytes in ${EXAMPLE_PDF} after stripping" 

```

> 💡 Tip: Once the `pdf-strip` tool has been installed it will take care of pulling any docker images it needs.


## Usage

Here are a few examples of how to use this tool. 

```sh
pdf-strip example.pdf                              # strip metadata (default)
pdf-strip *.pdf                                    # strip multiple files
pdf-strip ./my-docs/                               # strip all PDFs in a directory (recursive)
pdf-strip --check example.pdf                      # check for metadata without stripping
pdf-strip --check ./my-docs/                       # check all PDFs in a directory
```

When using the Claude Code skill, you can also pass a URL directly and Claude will fetch the file for you:

```
/pdf-strip https://alertstack.io/pdf-strip/test/example.pdf
/pdf-strip --check https://alertstack.io/pdf-strip/test/example.pdf
```

Output is written alongside each original file as `<base>.stripped.pdf`. Originals are never modified.

---

## How it works

| File | Role |
|---|---|
| `strip.py` | Core Python script. Opens a PDF with pikepdf, deletes the `/Info` dict and the XMP `/Root/Metadata` stream, writes a clean copy. |
| `entrypoint.sh` | Container entrypoint. Handles `install` dispatch, then delegates to `strip.py` with the supplied arguments. |
| `install.sh` | Bundled inside the image. Run via `docker run ... install` to copy the `pdf-strip` wrapper script to your host. |
| `pdf-strip` | Host-side wrapper script. Handles Docker plumbing: validates inputs, copies files into a temp dir, runs the container, and copies results back next to each original. |
| `Dockerfile` | Builds a minimal `python:3.12-slim` image with pikepdf and bundles all scripts. |
| `Makefile` | Developer workflow: build/tag/push image, run strips, install wrapper. |


---

## pdf-strip wrapper usage

```
pdf-strip                           Show help
pdf-strip -h | --help               Show help
pdf-strip <file.pdf>                Strip one PDF (default)
pdf-strip <f1.pdf> <f2.pdf>        Strip multiple PDFs
pdf-strip <directory>               Strip every .pdf found recursively
pdf-strip --check <file.pdf>        Check for metadata, print findings
pdf-strip --check <directory>       Check every .pdf found recursively
pdf-strip -- [args...]              Pass args directly to the container entrypoint
```

When invoked via the Claude Code skill, a URL is also accepted as input -- Claude fetches the
file and then strips or checks it:

```
/pdf-strip https://alertstack.io/pdf-strip/test/example.pdf
/pdf-strip --check https://alertstack.io/pdf-strip/test/example.pdf
```

### Modes

| Flag | Behaviour |
|---|---|
| _(none)_ | Strip metadata and write `<base>.stripped.pdf` alongside each original |
| `--check` | Print any metadata found (or none); exit 1 if any found |

### Environment variables

| Variable | Values | Description |
|---|---|---|
| `PDF_STRIP_IMAGE` | image reference | Override the Docker image (default: `ghcr.io/rondomondo/pdf-strip:latest`) |
| `DEBUG` | `true`/`1`, `false`/`0` | Enable verbose logging in both the wrapper and the container entrypoint |

```sh
# strip metadata (default)
pdf-strip report.pdf

# check for metadata without stripping
pdf-strip --check report.pdf

# override image
PDF_STRIP_IMAGE=ghcr.io/rondomondo/pdf-strip:0.0.3 pdf-strip report.pdf
```

---

### Open an interactive shell

```sh
make docker-shell
# or
docker run --rm -it \
  -v "$(pwd):/data" \
  --entrypoint /bin/bash \
  ghcr.io/rondomondo/pdf-strip:latest
```

---

## Make targets

```
make help                Show all targets

# Build
make docker-build        Build the image locally
make docker-tag          Retag for REGISTRY (default ghcr.io)
make docker-push         Push versioned + :latest to REGISTRY
make docker-release      Build, tag, and push in one step
make docker-ensure       Pull image from ghcr.io if not present; fall back to local build

# Run
make docker-shell        Open an interactive shell in the container

# Install
make install             Install pdf-strip wrapper to /usr/local/bin
make uninstall           Remove pdf-strip from /usr/local/bin

# Cleanup
make clean               Remove local Docker images (calls docker-clean)
```

Override registry, directories or tag:

```sh
make docker-release REGISTRY=docker.io
make docker-build PDF_STRIP_IMAGE_TAG=0.0.4
make run DATA=/path/to/pdfs
```

---

## What gets removed

| Metadata store | Fields |
|---|---|
| `/Info` dictionary | Author, Title, Subject, Keywords, Creator, Producer, CreationDate, ModDate |
| `/Root/Metadata` XMP stream | Dublin Core, XMP, XMP Rights, PDF namespaces |


---

### Get a Test PDF file
<details open>
<summary>Get a PDF file with metadata to test with here</summary>
<br>

```bash
setopt interactivecomments

EXAMPLE_PDF=test/example.pdf

curl --silent -L --create-dirs -o "${EXAMPLE_PDF}" https://abcdef.ai/$EXAMPLE_PDF
```

</details> 


---

## Build locally

```bash
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/pdf-strip
make docker-build
```

---

## Requirements

- Docker (running locally)
- `bash` 4+
- `make` (for Makefile targets)
- [pikepdf](https://pikepdf.readthedocs.io/) (for pdf functionality)

---

## Claude Code skill

<details>
<summary>Install the <code>/pdf-strip</code> slash command for Claude Code</summary>

This repository ships a `/pdf-strip` slash command skill for [Claude Code](https://claude.ai/code)
that lets Claude strip PDF metadata directly -- no terminal required. Just describe what you want
and Claude will invoke the skill automatically.

### What it accepts

| Input | Example |
|---|---|
| Single file | `report.pdf` |
| Multiple files | `file1.pdf file2.pdf` |
| Directory | `./my-docs/` |
| URL | `https://example.com/report.pdf` |
| Check mode | `--check report.pdf` |

### Invoking the skill

Use the slash command directly:

```
/pdf-strip report.pdf
/pdf-strip --check report.pdf
/pdf-strip ./my-docs/
/pdf-strip https://example.com/report.pdf
```

Or just describe what you want in natural language -- Claude will invoke the skill automatically:

> *"Strip the metadata from this PDF before I share it"*
>
> *"Check what's hidden in report.pdf"*
>
> *"Clean all the PDFs in my-docs/"*
>
> *"Fetch this PDF from the URL and strip its metadata"*

### Installing the skill

#### Option A -- sync locally via `make`

```bash
# from inside the pdf-strip directory
make sync-skill
```

This syncs `pdf-strip`, `SKILL.md`, and `README.md` to:

```
~/Code/agent-skills-toolbox/skills/pdf-strip/
```

Override the target directory with `SKILLS_DIR`:

```bash
make sync-skill SKILLS_DIR=/path/to/your/project/.claude/skills/pdf-strip
```

#### Option B -- copy manually

```bash
mkdir -p .claude/skills/pdf-strip
cp pdf-strip SKILL.md README.md .claude/skills/pdf-strip/
```

</details>

[ghcr.io/rondomondo/pdf-strip]: https://ghcr.io/rondomondo/pdf-strip:latest

[`ghcr.io/rondomondo/pdf-strip`]: https://ghcr.io/rondomondo/pdf-strip:latest

[docker image]: https://ghcr.io/rondomondo/pdf-strip:latest

[`docker image`]: https://ghcr.io/rondomondo/pdf-strip:latest

[test PDF file]: #get-a-test-pdf-file

[`test PDF file`]: #get-a-test-pdf-file

