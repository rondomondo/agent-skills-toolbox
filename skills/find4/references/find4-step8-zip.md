# Step 8 -- Zip output files

Bundle the deliverables into a single convenience zip at `output/<suggested_name>.zip`.
The zip name comes from `metadata.suggested_name` (strip the `.json` suffix).

⚠️ **Step 7.1 must be complete before this step.** The card widget HTML and screenshot are
generated in Step 7.1 and must exist before the zip is assembled.

Include:

- `output/games/<output_filename>` (combined JSON)
- `output/games/<basename>/<slug>.json` for each game set (split files)
- `output/games/html/<slug>.html` for each game set (standalone HTML)
- `output/games/screenshots/<slug>.html.png` for each game set (skip any that failed)
- `output/games/html/${COMBINED_BASENAME}.card.html` (short-link card widget — generated in Step 7.1)
- `output/games/screenshots/${COMBINED_BASENAME}.card.html.png` (card widget screenshot — generated in Step 7.1, skip if failed)

```bash
ZIPNAME=$(python3 -c "import json; d=json.load(open('output/tmp/find4_final.json')); print(d['metadata']['suggested_name'].replace('.json',''))")

# Stage files under a named subfolder so the zip extracts tidily into one directory.
ZIPSTAGE="output/tmp/zip_stage/${ZIPNAME}"
mkdir -p "$ZIPSTAGE"

cp "output/games/<output_filename>" "$ZIPSTAGE/"
while IFS= read -r SPLIT_JSON; do
  SLUG=$(basename "$SPLIT_JSON" .json)
  cp "$SPLIT_JSON" "$ZIPSTAGE/"
  [ -f "output/games/html/${SLUG}.html" ] && cp "output/games/html/${SLUG}.html" "$ZIPSTAGE/"
  [ -f "output/games/screenshots/${SLUG}.html.png" ] && \
    cp "output/games/screenshots/${SLUG}.html.png" "$ZIPSTAGE/"
done < output/tmp/split_paths.txt

# Card widget (Step 7.1 outputs) — COMBINED_BASENAME is the combined JSON basename, e.g. envoy-redis-core-concepts
COMBINED_BASENAME=$(python3 -c "import json; m=json.load(open('output/tmp/find4_final.json'))['metadata']; print(m['suggested_name'].replace('.json',''))")
[ -f "output/games/html/${COMBINED_BASENAME}.card.html" ] && \
  cp "output/games/html/${COMBINED_BASENAME}.card.html" "$ZIPSTAGE/"
[ -f "output/games/screenshots/${COMBINED_BASENAME}.card.html.png" ] && \
  cp "output/games/screenshots/${COMBINED_BASENAME}.card.html.png" "$ZIPSTAGE/"

# cd into the staging parent so the zip path is just <ZIPNAME>/...
(cd "output/tmp/zip_stage" && zip -r "../../${ZIPNAME}.zip" "${ZIPNAME}/") 2>/dev/null || true
echo "Zip: output/${ZIPNAME}.zip"
```

Files are staged under `output/tmp/zip_stage/<ZIPNAME>/` before zipping so that extraction always produces a single tidy folder named after the game.
This step is **non-critical** -- if it fails, log a warning and continue.

In sandbox: copy the zip to outputs and include it in `present_files`:

```bash
cp output/${ZIPNAME}.zip /mnt/user-data/outputs/${ZIPNAME}.zip
```