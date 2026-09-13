# URL fetch methods

Two methods are available. Check availability first:

```bash
if command -v wkhtmltopdf &>/dev/null && command -v pdftotext &>/dev/null; then
    USE_WKHTMLTOPDF=true
else
    USE_WKHTMLTOPDF=false
fi
```

## Method A: wkhtmltopdf + pdftotext (USE_WKHTMLTOPDF=true)

Use in sandbox and CI environments where both tools are installed.

```bash
xvfb-run wkhtmltopdf \
  --log-level none \
  --load-error-handling ignore \
  --load-media-error-handling ignore \
  "<URL>" /tmp/find4_source.pdf

pdftotext /tmp/find4_source.pdf - \
  | head -c 120000 \
  > output/tmp/find4_input.txt
```

After extraction, check for empty output. Some JS-heavy pages render as blank PDFs even when
wkhtmltopdf exits 0. If `find4_input.txt` is empty or under 100 bytes, fall back to Method B.

**Known limitation:** Wikimedia CDN rate-limits image requests (HTTP 429) -- text content is unaffected.

## Method B: WebFetch tool (USE_WKHTMLTOPDF=false)

Use on local/Mac where wkhtmltopdf is not available, or as fallback after a blank PDF.

Use the `WebFetch` tool to fetch the URL directly, then write the returned text to
`output/tmp/find4_input.txt`. Truncate to ~120,000 characters if needed.

## Failure handling

If both methods fail (empty output or non-zero exit), report the full error and stop.
