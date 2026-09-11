---
name: pdf-strip
description: >
    Strip all metadata from PDF files using pdf-strip (Docker-backed, using pikepdf). Removes
    the /Info dictionary (Author, Title, Producer, CreationDate, etc.) and the XMP metadata
    stream. Use this skill whenever the user wants to remove PDF metadata, sanitise a PDF
    before sharing, check what metadata a PDF contains, or batch-process a directory of PDFs.
    Accepts local files, directories, and URLs pointing directly to PDF files.
    Trigger on "strip pdf metadata", "pdf-strip", "remove pdf metadata", "sanitise pdf",
    "clean pdf", "check pdf metadata", or any request to inspect or remove hidden data from
    PDF files, including when a URL to a PDF is provided.
---

# pdf-strip Skill

You are stripping metadata from PDF files. In the sandbox you call `strip.py` directly via
Python (no Docker). Outside the sandbox you use the `pdf-strip` wrapper script, which handles
Docker volume plumbing on top of a `pikepdf`-based Python stripper.

The skill accepts the following input types:

| Type            | Example                                      |
| --------------- | -------------------------------------------- |
| Single file     | `report.pdf`                                 |
| Multiple files  | `file1.pdf file2.pdf`                        |
| Directory       | `./my-docs/` or `/some/path/`                |
| URL (single PDF)| `https://example.com/report.pdf`             |

---

## Step 1 -- Detect the environment

```bash
echo "${IS_SANDBOX:-no}"
```

- `IS_SANDBOX=yes` -> use the **sandbox path** throughout (see _Sandbox path_ section).
- Otherwise -> use the **non-sandbox path** throughout (see _Non-sandbox path_ section).

---

## Step 2 -- Classify the input

Inspect the non-flag arguments:

- **Single argument starts with `http://` or `https://`** -> URL input. Go to _URL handling_, then
  proceed with the resolved local file via the appropriate sandbox or non-sandbox path.
- **Single argument is a directory path** (ends with `/`, or `test -d` is true) -> directory input.
- **More than one `.pdf` argument** -> multiple file input; treat each independently.
- **Otherwise** -> single file.

---

## URL handling

A URL pointing to a PDF file (ending in `.pdf` or clearly a direct PDF link):

1. Use the `web_fetch` tool to retrieve the binary content (do **not** use `curl` -- external
   domains may be blocked by the egress proxy).
2. Save the content to `/home/claude/<filename>.pdf` where `<filename>` is derived from the URL
   path (e.g. `https://example.com/docs/report.pdf` -> `/home/claude/report.pdf`).
3. Proceed with the saved local file following the appropriate sandbox or non-sandbox path
   (check or strip mode as requested).
4. Copy any `.stripped.pdf` output to `/mnt/user-data/outputs/` so the user can download it.

**Note**: Some domains or CDNs may block programmatic fetches or be unreachable from the sandbox
egress proxy. If `web_fetch` fails with a network or 403 error, inform the user and ask them to
download the file locally and provide the local path instead.

---

## Sandbox path

The sandbox has no Docker. Use Python + pikepdf directly via the bundled `strip.py` from the
skill directory.

### Step S1 -- Install pikepdf and locate strip.py

```bash
SKILL_DIR="/mnt/skills/user/pdf-strip"
STRIP_PY="$SKILL_DIR/strip.py"

if [ ! -f "$STRIP_PY" ]; then
  echo "ERROR: strip.py not found at $STRIP_PY" >&2
  exit 1
fi

pip install pikepdf --quiet
```

### Step S2 -- Determine what to do

Infer from context or ask:

- **Check mode**: inspect metadata, print findings, do not modify files.
- **Strip mode** (default): remove metadata and write `<base>.stripped.pdf` alongside the original.

### Step S3 -- Run strip.py

#### Check for metadata (no writes)

```bash
python "$STRIP_PY" --check <file.pdf>
```

For a directory, find all PDFs and check each:

```bash
find /path/to/dir -name "*.pdf" | while read -r f; do
  python "$STRIP_PY" --check "$f"
done
```

#### Strip metadata (default)

Single file -- write output alongside the original:

```bash
python "$STRIP_PY" <input.pdf> <input.stripped.pdf>
```

Multiple files:

```bash
for f in file1.pdf file2.pdf; do
  python "$STRIP_PY" "$f" "${f%.pdf}.stripped.pdf"
done
```

Directory:

```bash
find /path/to/dir -name "*.pdf" | while read -r f; do
  python "$STRIP_PY" "$f" "${f%.pdf}.stripped.pdf"
done
```

### Step S4 -- Copy outputs

After stripping, copy all `.stripped.pdf` output files to `/mnt/user-data/outputs/` so the user
can download them. The output paths are whatever you passed as the second argument to `strip.py`
in Step S3, so collect and copy those explicitly:

```bash
mkdir -p /mnt/user-data/outputs/
for f in <list of .stripped.pdf paths from S3>; do
  cp "$f" /mnt/user-data/outputs/
done
```

### Step S5 -- Report

After `--check`, summarise what was found (see _Reporting_ section).
After stripping, confirm each `.stripped.pdf` exists and is accessible.

---

## Non-sandbox path

The non-sandbox environment uses the `pdf-strip` wrapper script which runs pikepdf inside a
Docker container (`ghcr.io/rondomondo/pdf-strip:latest`).

### Step N1 -- Check for the tool and Docker

Locate `pdf-strip` -- prefer a copy bundled with this skill, fall back to the system install:

```bash
if [[ -x "./pdf-strip" ]]; then
  PDF_STRIP="./pdf-strip"
elif command -v pdf-strip &>/dev/null; then
  PDF_STRIP="pdf-strip"
else
  echo "ERROR: pdf-strip not found. Install it via: make install" >&2
  exit 1
fi

docker info >/dev/null 2>&1 || { echo "ERROR: Docker is not running" >&2; exit 1; }
```

### Step N2 -- Determine what to do

Infer from context or ask:

- **Check mode** (`--check`): inspect metadata, print findings, do not modify files.
- **Strip mode** (default): remove metadata and write `<base>.stripped.pdf` alongside the original.

### Step N3 -- Run pdf-strip

#### Check for metadata (no writes)

```bash
"$PDF_STRIP" --check <file.pdf>
"$PDF_STRIP" --check <directory>
```

#### Strip metadata (default)

```bash
"$PDF_STRIP" <file.pdf>
"$PDF_STRIP" <file1.pdf> <file2.pdf>
"$PDF_STRIP" <directory>
```

Output is written as `<base>.stripped.pdf` alongside each original. Originals are never modified.

### Step N4 -- Report

After `--check`, summarise what was found (see _Reporting_ section).
After stripping, confirm each `.stripped.pdf` exists:

```bash
ls -lh <base>.stripped.pdf
```

---

## Reporting

### After --check

Summarise what was found per file:

- `/Info` fields: Author, Title, Subject, Keywords, Creator, Producer, CreationDate, ModDate
- XMP stream: Dublin Core, XMP, XMP Rights, PDF namespaces
- Report `CLEAN` or `HAS_METADATA` per file

### After stripping

Confirm each output file exists and report its size. If the stripped file is larger than the
original (rare but possible with some pikepdf versions), flag it for the user.

---

## Environment variables

| Variable          | Values             | Description                                                       |
|-------------------|--------------------|-------------------------------------------------------------------|
| `PDF_STRIP_IMAGE` | image reference    | Override the Docker image (default: `ghcr.io/rondomondo/pdf-strip:latest`) |
| `DEBUG`           | `true`/`1`, `false`/`0` | Enable verbose logging                                      |

---

## Exit codes

| Code | Meaning                                          |
|------|--------------------------------------------------|
| 0    | All clean or all stripped successfully           |
| 1    | Metadata found (check mode), or error during strip |

---

## Error handling

| Symptom                          | Likely cause                  | Fix                                                                          |
|----------------------------------|-------------------------------|------------------------------------------------------------------------------|
| `pdf-strip not found`            | Not installed                 | Run `make install` from `toolbox/pdf-strip/`                                 |
| `Docker not running`             | Docker Desktop stopped        | Start Docker Desktop                                                         |
| `Pull failed`                    | No network or auth            | Run `make docker-build` to build locally                                     |
| `strip.py not found`             | Skill not mounted             | Check `/mnt/skills/user/pdf-strip/` is present in the sandbox                |
| `pikepdf not installed`          | pip install failed            | Run `pip install pikepdf` manually                                           |
| Stripped file missing            | Conversion error              | Check stderr for pikepdf error output                                        |
| `web_fetch` fails with 403/error | Domain blocked by egress proxy| Inform user; ask them to download the file locally and provide the local path |
| URL fetches non-PDF content      | Wrong URL or redirect to HTML | Report raw response; ask user to verify the URL points directly to a PDF     |
