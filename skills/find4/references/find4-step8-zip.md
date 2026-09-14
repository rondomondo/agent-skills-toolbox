# Step 8 -- Zip output files

Bundle the deliverables into a single convenience zip at `output/<suggested_name>.zip`.
The zip name comes from `metadata.suggested_name` (strip the `.json` suffix).

⚠️ **Step 7.1 must be complete before this step.** The card widget HTML and screenshot are
generated in Step 7.1 and must exist before the zip is assembled.

Include:

- `output/games/<basename>/<basename>.json` (combined JSON)
- `output/games/<basename>/<slug>.json` for each split game set
- `output/games/<basename>/html/<slug>.html` for each game set (standalone HTML)
- `output/games/<basename>/html/<slug>.w.html` for each game set (widget HTML)
- `output/games/<basename>/screenshots/<slug>.html.png` for each game set (skip any that failed)
- `output/games/<basename>/html/${parent_stem}.card.html` (short-link card widget — generated in Step 7.1)
- `output/games/<basename>/screenshots/${parent_stem}.card.html.png` (card widget screenshot — generated in Step 7.1, skip if failed)

```bash
ZIPNAME=$(python3 -c "import json; d=json.load(open('output/tmp/find4_final.json')); print(d['metadata']['suggested_name'].replace('.json',''))")

# Stage files under a named subfolder so the zip extracts tidily into one directory.
ZIPSTAGE="output/tmp/zip_stage/${ZIPNAME}"
mkdir -p "$ZIPSTAGE"

# Combined JSON
cp "output/games/${ZIPNAME}/${ZIPNAME}.json" "$ZIPSTAGE/"

# Split JSONs + HTML + screenshots — iterate split files directly from games/
for split_json in "output/games/${ZIPNAME}/"*.json; do
  SLUG=$(basename "$split_json" .json)
  [ "$SLUG" = "$ZIPNAME" ] && continue  # skip combined
  cp "$split_json" "$ZIPSTAGE/"
  [ -f "output/games/${ZIPNAME}/html/${SLUG}.html" ]   && cp "output/games/${ZIPNAME}/html/${SLUG}.html"   "$ZIPSTAGE/"
  [ -f "output/games/${ZIPNAME}/html/${SLUG}.w.html" ] && cp "output/games/${ZIPNAME}/html/${SLUG}.w.html" "$ZIPSTAGE/"
  [ -f "output/games/${ZIPNAME}/screenshots/${SLUG}.html.png" ] && \
    cp "output/games/${ZIPNAME}/screenshots/${SLUG}.html.png" "$ZIPSTAGE/"
done

# Card widget (Step 7.1 outputs)
[ -f "output/games/${ZIPNAME}/html/${ZIPNAME}.card.html" ] && \
  cp "output/games/${ZIPNAME}/html/${ZIPNAME}.card.html" "$ZIPSTAGE/"
[ -f "output/games/${ZIPNAME}/screenshots/${ZIPNAME}.card.html.png" ] && \
  cp "output/games/${ZIPNAME}/screenshots/${ZIPNAME}.card.html.png" "$ZIPSTAGE/"

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
