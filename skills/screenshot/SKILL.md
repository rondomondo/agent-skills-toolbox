---
name: screenshot
description: >
    Capture full-page screenshots and PDFs of web pages or local HTML files using url2image and url2pdf
    (Docker-backed Playwright/Chromium, nothing to install on the host except Docker). Handles lazy-loaded
    content, cookie banners and popups, single-element capture by CSS selector, device emulation
    (iPhone, Pixel, iPad), webp/jpeg conversion, and logged-in pages via Playwright storage state. Use this
    skill whenever the user wants to screenshot a URL, save a page as PDF, see how a page looks on mobile,
    grab one element of a page, or turn local HTML into an image or PDF, even if they do not name the tool.
    Trigger on "screenshot", "capture this page", "save as pdf", "url2pdf", "url2image", "print this page to
    pdf", "iPhone screenshot", "element screenshot", "page behind a login", or any URL paired with a request
    for an image or PDF of it.
---

# screenshot Skill

You are capturing a web page as an image or PDF. The default route is the `url2image` and `url2pdf` wrappers,
which run `ghcr.io/rondomondo/screenshot` in Docker. Output is written to `./screenshots/` and `./pdfs/`
relative to the current directory.

## Step 1: Preflight

```bash
command -v url2image url2pdf; docker info >/dev/null 2>&1 && echo docker-ok
```

- Docker not running: stop and tell the user. Nothing here works without it.
- Wrappers missing but Docker fine: use the zero-install form (see _Docker directly_), or offer the installer.
  Do **not** run the installer without asking, because it writes to `/usr/local/bin` (possibly via sudo):
  `docker run --rm ghcr.io/rondomondo/screenshot:latest install | sh`

## Step 2: Route the request

| User wants | Command |
| --- | --- |
| PNG of a whole page | `url2image <url>` |
| Smaller format | `url2image <url> --convert webp` (or jpeg, gif) |
| Mobile or tablet view | `url2image <url> --device "iPhone 15"` (a safe default when no model is named; for any other model check the exact name with `devices` first) |
| Which devices exist | `url2image devices` (long list; pipe through `grep -i`); one descriptor: `url2image device-info "iPhone 15"` |
| One element only | `url2image element --selector '<css>' <url>` |
| PDF | `url2pdf <url> [--paper-format Letter]` |
| PDF without sidebars or TOC | `url2pdf <url> --hide '<css>'` (repeatable) |
| Local HTML file | put it in `./html/`, then `url2image page.html` (relative path) |
| Page behind a login | see _Authenticated pages_ |
| Lazy or slow content | `--wait-for-timeout 5000` or `--wait-for "some text"` |
| Viewport only | `--no-scroll` |

Full flag list: `references/options.md`, or run `url2image help` / `url2pdf help` (always current).

## Step 3: Run, then verify

1. Run the command. Progress goes to stderr; a non-zero exit means failure.
2. Confirm the capture exists and is plausible: `ls -lt screenshots pdfs | head`. The name is derived from the URL
   or file basename. A file of a few hundred bytes is almost always an error page or a blank render.
3. Look at the result, because a zero exit code only means Chromium finished, not that the page was usable.
   Read the PNG for images. A PDF cannot be Read directly on a host without poppler, so render page 1 to an
   image first: `sips -s format png pdfs/<name>.pdf --out /tmp/p1.png` on macOS, or
   `pdftoppm -png -r 60 -f 1 -l 1 pdfs/<name>.pdf /tmp/p1` elsewhere, then Read that PNG. For the page count and
   paper size use `grep -a -o '/Count [0-9]*'` and `grep -a -m1 -o 'MediaBox *\[[^]]*\]'` on the PDF. You are checking for a
   blank page, a cookie wall, a clipped layout or an unexpected paper size.
4. Report the full path, size and, for PDFs, the page count. If the output is wrong, go to
   `references/troubleshooting.md` before retrying.
5. CJK text renders as empty boxes: the container has no CJK fonts. That is a tool limitation, not a site
   problem, so say so rather than retrying.

## Rules that are easy to get wrong

- `-s` means `--selector` for `url2image element` but `--storage-state` for plain `url2image` and `url2pdf`.
  Use the long forms.
- `element` is image-only. There is no `url2pdf element`. For "a PDF of just this element", say so and offer the
  PNG, or `url2pdf --hide` on everything else (selectors depend on the site's markup, so check them against the
  page source). Do not wrap a PNG in HTML to fake it unless asked: the PDF text is then not selectable.
- `--device` overrides viewport, scale factor and user agent; do not combine it with `--viewport-size`.
- `--convert` is ignored for PDFs. `--device-scale-factor` is screenshot-only.
- Popup dismissal is on by default, but off for `element`; add `--dismiss-popups` if a banner is in the way.
- Local files must live in `./html/` and be passed as a path relative to it, not an absolute path.
- Pin a version with `IMAGE_TAG=<version> url2pdf ...`. Pre-release tags never move `:latest`.
- Diagnose with `LOG_LEVEL=INFO` or `DEBUG=1` (DEBUG prints the underlying `docker run` command).

## Authenticated pages

Use `--storage-state <file>`, a Playwright storageState JSON (cookies and localStorage). The wrapper mounts it
read-only into the container. That file holds live credentials: only use one the user points you to, never
create or print one, and do not copy it into the repo. See `references/auth-and-mcp.md`.

## Docker directly

```bash
docker run --rm -v "$(pwd)/screenshots:/screenshots" ghcr.io/rondomondo/screenshot:latest screenshot <url>
docker run --rm -v "$(pwd)/pdfs:/pdfs" ghcr.io/rondomondo/screenshot:latest pdf <url>
```

## Working inside this repo

Developing the tool itself, `make screenshot TARGET=<url>` and `make pdf TARGET=<url>` run `ssc.py` against a
local MCP server (started and stopped automatically; needs `uv`). `make test` runs the unit tests. Building
and releasing (`make build`, `make release`, which pushes to ghcr.io) are maintainer actions: ask first.
`make help` lists everything.
