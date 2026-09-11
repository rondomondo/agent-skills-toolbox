# Step 9 — Push output to GitHub

**Skip this step entirely if any of `GITHUB_TOKEN`, `GITHUB_REPO`, or `GITHUB_BRANCH` are unset.** Warn the user and continue — the zip is still available for manual download.

This step pushes a `results/` tree into `skills/find4/results/` in the target repo on a unique scratch branch, then dispatches the GitHub Actions workflow to publish the games to S3. Each run gets its own branch (`find4-drop-<timestamp>-<random>`), so parallel skill runs never collide. The workflow merges scratch -> `find4-prod` -> `main` sequentially (serialised via a concurrency group) and deletes the scratch branch on completion.

`results/` mirrors `output/games/`, `output/library/`, `output/tmp/zip_stage/`, and `logs/`, plus any loose files directly under `output/tmp/` -- but never the `output/tmp/gh-push` clone itself. See 9.3 for why that distinction matters.

## 9.1 -- Collect credentials

```bash
# These must be set before running -- prompt the user if missing
: "${GITHUB_TOKEN:?GITHUB_TOKEN is not set -- skipping GitHub push}"
: "${GITHUB_REPO:?GITHUB_REPO is not set (format: owner/repo)}"

# Generate a unique scratch branch name for this run
RAND6=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 6; true)
GITHUB_BRANCH="find4-drop-$(date +%Y%m%d-%H%M%S)-${RAND6}"
echo "GITHUB_BRANCH=${GITHUB_BRANCH}" >> "$RUNDIR/.find4_env"
echo "Drop branch: ${GITHUB_BRANCH}"
```

## 9.2 -- Sparse clone and create the scratch branch

Clone only the `skills/find4/results/` subtree. The scratch branch is always new -- clone from the default branch then check out a fresh branch.

```bash
CLONE_DIR="$RUNDIR/output/tmp/gh-push"
rm -rf "$CLONE_DIR"

git clone \
  --depth 1 \
  --filter=blob:none \
  --sparse \
  "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git" \
  "$CLONE_DIR"

cd "$CLONE_DIR"
git sparse-checkout set skills/find4/results
git checkout -b "$GITHUB_BRANCH"
```

## 9.3 -- Copy output into the clone (append -- do not wipe existing files)

**Only copy the actual deliverables -- never the whole `output/` tree.**
`output/tmp/` is scratch space, and `output/tmp/gh-push` is *this very clone*
(`$CLONE_DIR` is created under `$RUNDIR/output/tmp/`). A blanket
`cp -rn "$RUNDIR/output/." "$DEST/"` therefore copies the clone into itself
mid-operation -- it embeds a nested `.git` (git logs an "adding embedded git
repository" warning) and drags every scratch file into the pushed repo.

This run preserves a fuller audit trail than just `games/`/`library/`, but stays
safe by listing every source explicitly and pulling only **files** (never
directories) out of `output/tmp/` itself -- that one rule is what excludes
`output/tmp/gh-push` (a directory) automatically, with no special-case needed:

```bash
DEST="$CLONE_DIR/skills/find4/results"
mkdir -p "$DEST/output/games" "$DEST/output/library" \
         "$DEST/output/tmp/zip_stage" "$DEST/output/tmp" \
         "$DEST/logs"

# cp -rn: copy recursively, no-clobber (never overwrites existing files).
# rsync is NOT available in the sandbox -- do not use it.
[ -d "$RUNDIR/output/games" ]         && cp -rn "$RUNDIR/output/games/."         "$DEST/output/games/"
[ -d "$RUNDIR/output/library" ]       && cp -rn "$RUNDIR/output/library/."       "$DEST/output/library/"
[ -d "$RUNDIR/output/tmp/zip_stage" ] && cp -rn "$RUNDIR/output/tmp/zip_stage/." "$DEST/output/tmp/zip_stage/"
[ -d "$RUNDIR/output/logs" ]          && cp -rn "$RUNDIR/output/logs/."          "$DEST/logs/"

# Flat files only, directly under output/tmp/ -- explicitly NOT recursive,
# so subdirectories (gh-push/, zip_stage/ already handled above) are skipped.
find "$RUNDIR/output/tmp" -maxdepth 1 -type f -exec cp -n {} "$DEST/output/tmp/" \;
```

`output/logs/` is not currently created or written to anywhere else in SKILL.md -- the `mkdir -p` and copy guard above are scaffolding for when logging is added; until then this line is a safe no-op.

## 9.3b -- Write meta.json payload

Write `results/meta.json` into the clone. The publish workflow reads this file and injects its
fields into the success email, so the email shows short links, game titles, and source info
without needing them as workflow inputs.

Build it from `output/library/themes.json` (already written by Step 7) and
`output/tmp/find4_final.json` (written by Step 5). Both are available by the time Step 9 runs.
Fall back gracefully if either file is absent.

```bash
THEMES_JSON="$RUNDIR/output/library/themes.json"
FINAL_JSON="$RUNDIR/output/tmp/find4_final.json"
META_JSON="$DEST/meta.json"

python3 - <<'PYEOF'
import json, os
from pathlib import Path

themes_path = Path(os.environ["THEMES_JSON"])
final_path  = Path(os.environ["FINAL_JSON"])
meta_path   = Path(os.environ["META_JSON"])

source_id = ""
zip_name  = ""
if final_path.exists():
    final = json.loads(final_path.read_text(encoding="utf-8"))
    meta  = final.get("metadata", {})
    source_id = meta.get("source_id", meta.get("source", ""))
    suggested  = meta.get("suggested_name", "")
    zip_name   = suggested.replace(".json", "") if suggested else ""

new_games = []
if themes_path.exists():
    themes = json.loads(themes_path.read_text(encoding="utf-8"))
    for entry in themes:
        short_link = entry.get("short_link", "")
        short_path = entry.get("short_path", "")
        new_games.append({
            "game_set_id": entry.get("game_set_id", ""),
            "theme":       entry.get("theme", ""),
            "short_link":  short_link,
            "short_url":   f"https://find4.org/?{short_link}" if short_link else "",
            "short_path":  short_path,
            "path_url":    f"https://find4.org/?config={short_path}" if short_path else "",
        })

# Merge with any existing meta.json in the clone, deduplicating by game_set_id.
# Each run appends its new games rather than replacing the whole file, so the
# email history accumulates across drops.
existing_games = []
if meta_path.exists():
    try:
        existing = json.loads(meta_path.read_text(encoding="utf-8"))
        existing_games = existing.get("games", [])
    except (json.JSONDecodeError, KeyError):
        pass

new_ids = {g["game_set_id"] for g in new_games}
merged_games = [g for g in existing_games if g["game_set_id"] not in new_ids] + new_games

payload = {
    "source_id": source_id,
    "zip":       zip_name,
    "games":     merged_games,
}
meta_path.parent.mkdir(parents=True, exist_ok=True)
meta_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"meta.json written: {len(new_games)} new game set(s), {len(merged_games)} total, source={source_id!r}")
PYEOF
```

## 9.4 -- Commit, push, and dispatch workflow

```bash
cd "$CLONE_DIR"

git config user.email "find4-skill@abcdef.ai"
git config user.name "Find4 Skill"

git add skills/find4/results/

if git diff --cached --quiet; then
  echo "No new files to push -- everything already present in remote."
  cd "$RUNDIR"
else
  git commit -m "feat(find4): add results ${ZIPNAME} [${GITHUB_BRANCH}]"
  git push origin "$GITHUB_BRANCH"
  echo "Pushed to ${GITHUB_REPO}@${GITHUB_BRANCH}"
  cd "$RUNDIR"

  # Dispatch the publish workflow -- it will merge scratch -> find4-prod -> main
  # and delete the scratch branch on completion.
  # Prefer gh CLI; fall back to the REST API (curl) when gh is not available.
  if command -v gh >/dev/null 2>&1; then
    GH_TOKEN="$GITHUB_TOKEN" gh workflow run publish-find4-games-workflow-call.yaml \
      --repo "$GITHUB_REPO" \
      --ref "$GITHUB_BRANCH" \
      --field "source_branch=${GITHUB_BRANCH}" \
      --field "branch_prod=find4-prod"
    echo "Workflow dispatched. Track at: https://github.com/${GITHUB_REPO}/actions"
  elif command -v curl >/dev/null 2>&1; then
    curl -s -o /dev/null -w "%{http_code}" -X POST \
      -H "Authorization: Bearer ${GITHUB_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/publish-find4-games-workflow-call.yaml/dispatches" \
      -d "{\"ref\":\"${GITHUB_BRANCH}\",\"inputs\":{\"source_branch\":\"${GITHUB_BRANCH}\",\"branch_prod\":\"find4-prod\"}}" \
    | grep -q "^204$" \
      && echo "Workflow dispatched via API. Track at: https://github.com/${GITHUB_REPO}/actions" \
      || echo "WARNING: workflow dispatch returned unexpected status -- check token permissions"
  else
    echo "WARNING: neither gh nor curl available -- trigger the workflow manually:"
    echo "  gh workflow run publish-find4-games-workflow-call.yaml \\"
    echo "    --repo ${GITHUB_REPO} --ref ${GITHUB_BRANCH} \\"
    echo "    --field source_branch=${GITHUB_BRANCH} --field branch_prod=find4-prod"
  fi
fi
```

## Step 9 checklist

- [ ] `GITHUB_TOKEN` and `GITHUB_REPO` are set (or step skipped with warning)
- [ ] `GITHUB_BRANCH` generated as `find4-drop-<timestamp>-<random>` -- unique per run
- [ ] Sparse clone targets `skills/find4/results/` only -- scratch branch created fresh from default
- [ ] `output/games/`, `output/library/`, `output/tmp/zip_stage/`, and `output/logs/` (if present) are copied recursively into `results/`
- [ ] Only top-level **files** (not subdirectories) are copied out of `output/tmp/` itself -- this is what excludes `output/tmp/gh-push` (the clone) automatically
- [ ] `cp -rn` used -- never overwrites existing files (`rsync` not available in sandbox)
- [ ] `results/meta.json` written from `output/library/themes.json` before commit (section 9.3b) -- includes `games[]` with `theme`, `short_url`, `path_url` per game set
- [ ] Workflow dispatched: `gh workflow run` if available, else `curl` REST API POST to `/dispatches` with `source_branch` and `branch_prod` inputs
- [ ] "No new files" case handled gracefully (no empty commit, no dispatch)
