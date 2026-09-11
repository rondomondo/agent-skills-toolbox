#!/usr/bin/env -S uv run python3
"""
generate_library_all.py - Build themes.json, library.json, and results/meta.json in one pass.

Step 1 (always): Scans a directory of Find4 game JSON files and writes
themes.json -- the compact index the Find4 Library panel loads on startup.
Deduplicates by game_set_id, keeping the most recently modified copy when the
same ID appears in more than one file.

Step 2 (default, skip with --themes-only): Reads themes.json and assembles
library.json -- a single document with full word data for every game set.
The output uses the same envelope as default.json (metadata + game_sets) so
the Find4 frontend can load it without changes.

Step 3 (opt-in, --create-meta): Reads the themes index and writes:
  - results/meta.json                              -- combined summary of all game sets
  - results/<slug>/<stem>.meta.json                -- one file per game set

Usage:
    # standard rebuild after adding a new game
    python3 generate_library_all.py \\
        --config-dir ./config --games-dir ./games --output-dir ./library \\
        --library-root . --force

    # themes.json only (skip library.json)
    python3 generate_library_all.py \\
        --games-dir ./games --output-dir ./library --themes-only --force

    # rebuild with randomised word order
    python3 generate_library_all.py \\
        --games-dir ./games --output-dir ./library --shuffle --force

    # also regenerate results/meta.json and per-game meta files
    python3 generate_library_all.py \\
        --games-dir ./games --output-dir ./library --library-root . \\
        --themes-only --create-meta --meta-dir results \\
        --meta-source-id stdin --meta-zip my-topic --force

    # dry-run: validate all game files without writing any output
    python3 generate_library_all.py --games-dir ./games --output-dir ./library 2>&1 | grep -E 'Error|OK'
"""

import argparse
import hashlib
import json
import os
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO
from datetime import timedelta


DEFAULT_SCHEMA = [
    "words",
    "category",
    "color",
    "url",
    "description",
    "skill_level",
    "additional_sources",
    "group_item_id",
    "group_set_id",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()[:19]



def hydrate_game_set(game_set: dict[str, Any], schema: list[str]) -> dict[str, Any]:
    """Expand packed group value arrays to dicts (shallow copy of game_set).

    Args:
        game_set: raw game set dict, whose group_sets may contain packed lists.
        schema: ordered field names used to unpack each packed group list.

    Returns:
        A new dict with group_sets fully expanded to dicts.
    """
    game_set = dict(game_set)
    game_set["group_sets"] = [
        [dict(zip(schema, g)) if isinstance(g, list) else g for g in gs]
        for gs in game_set.get("group_sets", [])
    ]
    return game_set

def ff_hash(config_file: str) -> str:
    """Compute a stable FNV-1a 32-bit hash of config_file, prefixed ff-.

    Port of the JavaScript ffHash function in find4.js.

    Args:
        config_file: the config file path string to hash.

    Returns:
        String of the form 'ff-xxxxxxxx' (8 lowercase hex digits).
    """
    h = 0x811C9DC5
    for ch in config_file:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"ff-{h:08x}"


def content_hash(data: Any) -> str:
    """Return a SHA-256 hex digest of the JSON-serialised data.

    Args:
        data: any JSON-serialisable value.

    Returns:
        Lowercase hex string of the SHA-256 digest.
    """
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def metadata_fingerprint(metadata: dict[str, Any]) -> str:
    """Return a 16-char fingerprint of a metadata dict.

    Args:
        metadata: the metadata dict to fingerprint.

    Returns:
        First 16 hex chars of the SHA-256 digest.
    """
    return content_hash(metadata)[:16]


@dataclass
class GameSetVersion:
    """Tracks versions of a game set for deduplication."""

    game_set_id: str
    games_file: str
    modified_time: datetime
    file_content_hash: str
    theme: str

    def __lt__(self, other: "GameSetVersion") -> bool:
        return self.modified_time < other.modified_time


class ThemeIndexerError(Exception):
    pass


class ConfigurationError(ThemeIndexerError):
    pass


class ValidationError(ThemeIndexerError):
    pass


class ThemeIndexer:
    """Indexes and validates game themes from Find4 JSON configuration files.

    Deduplicates by game_set_id, keeping the most recently modified version.
    """

    def __init__(
        self,
        games_dir: str = "games",
        shuffle_enabled: bool = False,
        hex_length: int = 12,
        filter_pattern: str | None = None,
        invert_match: bool = False,
        short_code_base: str | None = None,
    ):
        self.games_dir = Path(games_dir)
        self.known_ids: set[str] = set()
        self.duplicate_ids: dict[str, list[GameSetVersion]] = defaultdict(list)
        self.validation_errors: list[str] = []
        self.processed_files: set[str] = set()
        self.shuffle_enabled = shuffle_enabled
        self.hex_length = hex_length
        self._filter_re = re.compile(filter_pattern, re.IGNORECASE) if filter_pattern else None
        self._invert_match = invert_match
        self._short_code_base = short_code_base

    def validate_game_set(self, game_set: dict[str, Any], file_path: str) -> bool:
        """Validate structural correctness of a game set dict.

        Args:
            game_set: the game set to validate.
            file_path: used only for error messages.

        Returns:
            True if valid, False otherwise (errors appended to self.validation_errors).
        """
        errors = []

        for field in ("theme", "game_set_id", "group_sets"):
            if field not in game_set:
                errors.append(f"Missing required field '{field}'")

        if "game_set_id" in game_set:
            gid = game_set["game_set_id"]
            if not (isinstance(gid, str) and len(gid) == self.hex_length and all(c in "0123456789abcdef" for c in gid)):
                errors.append(f"Invalid game_set_id format: {gid}")

        if "group_sets" in game_set:
            if not isinstance(game_set["group_sets"], list):
                errors.append("group_sets must be a list")
            else:
                for i, group_set in enumerate(game_set["group_sets"]):
                    if not isinstance(group_set, list):
                        errors.append(f"group_set {i} must be a list")
                    else:
                        for j, group in enumerate(group_set):
                            if not isinstance(group, dict):
                                errors.append(f"group {j} in group_set {i} must be a dict")
                            else:
                                for field in ("words", "category", "skill_level"):
                                    if field not in group:
                                        errors.append(f"Missing '{field}' in group {j} of group_set {i}")

        if errors:
            for error in errors:
                self.validation_errors.append(f"{file_path}: {error}")
            return False
        return True

    def calculate_content_hash(self, game_set: dict[str, Any]) -> str:
        """Return a stable hash for a game set based on theme and group_sets content.

        Args:
            game_set: the game set dict.

        Returns:
            SHA-256 hex digest string.
        """
        content_dict = {
            "theme": game_set.get("theme", ""),
            "group_sets": game_set.get("group_sets", []),
        }
        return content_hash(content_dict)

    def shuffle_game_set(self, game_set: dict[str, Any]) -> dict[str, Any]:
        """Shuffle group_sets, groups within sets, and words within groups.

        Args:
            game_set: the game set to shuffle.

        Returns:
            Original dict if shuffling is disabled; otherwise a shallow copy with shuffled data.
        """
        if not self.shuffle_enabled:
            return game_set
        shuffled = game_set.copy()
        if "group_sets" in shuffled:
            random.shuffle(shuffled["group_sets"])
            for group_set in shuffled["group_sets"]:
                random.shuffle(group_set)
                for group in group_set:
                    if "words" in group:
                        random.shuffle(group["words"])
        return shuffled

    def _game_set_matches_filter(self, game_set: dict[str, Any]) -> bool:
        """Return True when this game set should be included given the active filter.

        Searches theme, category, and description (case-insensitively) across all
        groups in all group_sets. With --invert-match the result is negated.

        Args:
            game_set: hydrated game set dict.

        Returns:
            True if the game set passes the filter (or no filter is active).
        """
        if self._filter_re is None:
            return True

        candidates: list[str] = [game_set.get("theme", "")]
        for group_set in game_set.get("group_sets", []):
            for group in group_set:
                for field in ("category", "description"):
                    value = group.get(field)
                    if isinstance(value, str):
                        candidates.append(value)

        matched = any(self._filter_re.search(c) for c in candidates)
        return not matched if self._invert_match else matched

    def create_theme_index(self) -> list[dict[str, Any]]:
        """Scan games_dir and build a list of theme index entries.

        Returns:
            List of theme entry dicts sorted alphabetically by theme.

        Raises:
            ConfigurationError: if games_dir does not exist.
        """
        if not self.games_dir.exists():
            raise ConfigurationError(f"Config directory '{self.games_dir}' not found")

        theme_entries: dict[str, dict[str, Any]] = {}

        for json_file in self.games_dir.glob("*.json"):
            if json_file.name == "themes.json":
                continue
            try:
                self.processed_files.add(str(json_file))
                file_stat = json_file.stat()
                modified_time = datetime.fromtimestamp(file_stat.st_mtime)

                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)

                if "game_sets" not in data:
                    continue

                schema = data.get("schema", DEFAULT_SCHEMA)
                for game_set in data["game_sets"]:
                    game_set = hydrate_game_set(game_set, schema)
                    if not self.validate_game_set(game_set, str(json_file)):
                        continue

                    if not self._game_set_matches_filter(game_set):
                        continue

                    if self.shuffle_enabled:
                        game_set = self.shuffle_game_set(game_set)

                    game_set_id = game_set["game_set_id"]
                    gs_hash = self.calculate_content_hash(game_set)

                    version = GameSetVersion(
                        game_set_id=game_set_id,
                        games_file=str(json_file.relative_to(self.games_dir)),
                        modified_time=modified_time,
                        file_content_hash=gs_hash,
                        theme=game_set["theme"],
                    )
                    self.duplicate_ids[game_set_id].append(version)

                    word_count = 0
                    categories: set[str] = set()
                    skill_levels: set[str] = set()
                    colors: set[str] = set()

                    for group_set in game_set["group_sets"]:
                        for group in group_set:
                            word_count += len(group.get("words", []))
                            categories.add(group.get("category", ""))
                            skill_levels.add(group.get("skill_level", ""))
                            colors.add(group.get("color", ""))

                    split_info = data.get("metadata", {}).get("split_info", {})
                    if split_info.get("role") == "split":
                        parent_stem = Path(split_info.get("parent_file", "")).stem
                        split_slug = split_info.get("slug", "")
                        config_file = f"library/{parent_stem}/{split_slug}.json"
                    else:
                        config_file = f"games/{json_file.relative_to(self.games_dir)}"

                    short_path = f"games/{str(json_file.relative_to(self.games_dir))}" 
                    short_link = ff_hash(short_path) 
                    print(f"short_link: {short_link} short_path: {short_path} config_file: {config_file}", file=sys.stderr)
                    entry = {
                        "game_set_id": game_set_id,
                        "theme": game_set["theme"],
                        "short_path": short_path,
                        "short_link": short_link,
                        "games_file": str(json_file.relative_to(self.games_dir)),
                        "config_file": config_file,
                        "last_modified": modified_time.isoformat(),
                        "content_hash": gs_hash,
                        "total_words": word_count,
                        "categories": sorted(list(categories)),
                        "skill_levels": sorted(list(skill_levels)),
                        "colors": sorted(list(colors)),
                        "group_sets_count": len(game_set["group_sets"]),
                        "total_groups": sum(len(gs) for gs in game_set["group_sets"]),
                        "versions_found": 1,
                        "is_latest": True,
                        "metadata": {
                            "generated_at": data.get("metadata", {}).get("generated_at", ""),
                            "source": data.get("metadata", {}).get("source", ""),
                            "suggested_name": data.get("metadata", {}).get("suggested_name", ""),
                        },
                    }

                    if game_set_id in theme_entries:
                        entry["versions_found"] = theme_entries[game_set_id]["versions_found"] + 1
                        if modified_time > datetime.fromisoformat(theme_entries[game_set_id]["last_modified"]):
                            theme_entries[game_set_id]["is_latest"] = False
                            theme_entries[game_set_id] = entry
                    else:
                        theme_entries[game_set_id] = entry

            except json.JSONDecodeError as e:
                self.validation_errors.append(f"Error reading {json_file}: Invalid JSON - {e}")
            except Exception as e:
                self.validation_errors.append(f"Error processing {json_file}: {e}")

        return sorted(theme_entries.values(), key=lambda x: x["theme"])

    def print_validation_report(self, out: TextIO | None = None) -> None:
        """Print a validation and deduplication summary.

        Args:
            out: output stream; defaults to sys.stdout.
        """
        if out is None:
            out = sys.stdout
        print("\nValidation Report:", file=out)
        print("-" * 80, file=out)
        if self.validation_errors:
            print("Errors found:", file=out)
            for error in self.validation_errors:
                print(f"  - {error}", file=out)
        else:
            print("No validation errors found.", file=out)

        print("\nDuplicate Analysis:", file=out)
        for game_set_id, versions in self.duplicate_ids.items():
            if len(versions) > 1:
                print(f"\n  Game Set ID: {game_set_id}", file=out)
                versions.sort()
                for v in versions:
                    print(f"  - {v.games_file} ({v.modified_time.isoformat()}) [{v.file_content_hash[:8]}]", file=out)
                if len(set(v.file_content_hash for v in versions)) > 1:
                    print("  WARNING: Content differs between versions!", file=out)

        print(f"\nProcessed {len(self.processed_files)} files", file=out)
        print(f"Found {len(self.duplicate_ids)} unique game sets", file=out)


def print_theme_summary(entries: list[dict[str, Any]], out: TextIO | None = None) -> None:
    """Print a tabular summary of theme index entries.

    Args:
        entries: list of theme entry dicts from create_theme_index().
        out: output stream; defaults to sys.stdout.
    """
    if out is None:
        out = sys.stdout
    print("\nTheme Index Summary:", file=out)
    print("-" * 120, file=out)
    print(f"{'Theme':<30} {'Game Set ID':<15} {'Words':<8} {'Groups':<8} {'Vers':<7} {'File'}", file=out)
    print("-" * 120, file=out)
    for entry in entries:
        print(
            f"{entry['theme'][:30]:<30} "
            f"{entry['game_set_id']:<15} "
            f"{entry['total_words']:<8} "
            f"{entry['total_groups']:<8} "
            f"{entry['versions_found']:<4}[{'v' if entry['is_latest'] else 'x':<1}] "
            f"{entry['games_file']}",
            file=out,
        )
    print("-" * 120, file=out)


def load_json(path: Path) -> Any:
    """Load and return JSON from a file.

    Args:
        path: path to the JSON file.

    Returns:
        Parsed JSON value.
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_config_path(entry: dict[str, Any], library_root: Path) -> Path | None:
    """Resolve the full filesystem path for a theme entry's config_file.

    Falls back to walking library/ subdirectories when config_file does not
    exist directly -- this handles split files generated by game_split.py.

    Args:
        entry: a theme index entry from themes.json.
        library_root: root directory for resolving relative config_file paths.

    Returns:
        Resolved Path if found, None otherwise.
    """
    raw = entry.get("config_file", "")
    if not raw:
        return None
    candidate = library_root / raw
    if candidate.exists():
        return candidate
    games_file = entry.get("games_file", "")
    games_stem = Path(games_file).stem if games_file else ""
    if games_stem:
        library_dir = library_root / "library"
        if library_dir.exists():
            for subdir in library_dir.iterdir():
                if not subdir.is_dir():
                    continue
                for json_file in subdir.glob("*.json"):
                    try:
                        doc = load_json(json_file)
                        gid = entry.get("game_set_id", "")
                        if any(gs.get("game_set_id") == gid for gs in doc.get("game_sets", [])):
                            return json_file
                    except Exception:
                        continue
    return None


def build_full_library(
    themes_path: Path,
    library_root: Path,
    trigger: str,
    themes_data: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble library.json from a themes.json index.

    Args:
        themes_path: path to themes.json produced in step 1 (used as source label in metadata).
        library_root: root directory for resolving config_file paths.
        trigger: free-text label identifying who or what triggered this build.
        themes_data: in-memory themes list; when provided, themes_path is not read from disk.

    Returns:
        Dict with 'metadata' and 'game_sets' keys, suitable for JSON output.
    """
    themes: list[dict[str, Any]] = themes_data if themes_data is not None else load_json(themes_path)

    game_sets: list[dict[str, Any]] = []
    source_hashes: dict[str, str] = {}
    missing: list[str] = []

    for entry in themes:
        game_set_id = entry.get("game_set_id", "unknown")
        config_path = resolve_config_path(entry, library_root)

        if config_path is None:
            print(f"  SKIP {game_set_id}: config_file not found ({entry.get('config_file')})", file=sys.stderr)
            missing.append(game_set_id)
            continue

        try:
            game_doc = load_json(config_path)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  ERROR {game_set_id}: {config_path} - {exc}", file=sys.stderr)
            missing.append(game_set_id)
            continue

        matched: dict[str, Any] | None = None
        for gs in game_doc.get("game_sets", []):
            if gs.get("game_set_id") == game_set_id:
                matched = gs
                break

        if matched is None:
            if len(game_doc.get("game_sets", [])) == 1:
                matched = game_doc["game_sets"][0]
            else:
                print(f"  SKIP {game_set_id}: no matching game_set in {config_path}", file=sys.stderr)
                missing.append(game_set_id)
                continue

        source_hashes[game_set_id] = entry.get("content_hash", content_hash(matched))
        game_sets.append(matched)
        print(f"  OK   {game_set_id}: {entry.get('theme', '')}", file=sys.stderr)

    if missing:
        print(f"\nWarning: {len(missing)} game set(s) could not be resolved: {missing}", file=sys.stderr)

    all_game_sets_content = [
        {"game_set_id": gs.get("game_set_id"), "group_sets": gs.get("group_sets")} for gs in game_sets
    ]
    library_content_hash = content_hash(all_game_sets_content)

    now_iso = now()
    meta: dict[str, Any] = {
        "generated_at": now_iso,
        "library_version": now_iso,
        "trigger": trigger,
        "source": str(themes_path),
        "game_set_count": len(game_sets),
        "missing_count": len(missing),
        "source_hashes": source_hashes,
        "content_hash": library_content_hash,
    }
    meta["metadata_fingerprint"] = metadata_fingerprint(meta)

    return {"metadata": meta, "game_sets": game_sets}


def build_meta(
    themes: list[dict[str, Any]],
    meta_dir: Path,
    base_url: str,
    source_id: str,
    zip_name: str,
    force: bool,
    dry_run: bool,
    progress: TextIO,
) -> dict[str, Any]:
    """Build results/meta.json and per-game results/<slug>/<stem>.meta.json from themes entries.

    Args:
        themes: list of theme index entries from themes.json.
        meta_dir: root output directory (e.g. results/).
        base_url: base URL for constructing short_url and path_url (e.g. https://find4.org).
        source_id: free-text source label written into meta.json (e.g. 'stdin' or a URL).
        zip_name: zip name written into meta.json.
        force: overwrite existing files when True.
        dry_run: skip all writes when True.
        progress: output stream for progress messages.

    Returns:
        The assembled meta dict written to results/meta.json.

    Raises:
        ConfigurationError: if any output file already exists and force is False.
    """
    base_url = base_url.rstrip("/")
    games: list[dict[str, Any]] = []

    for entry in themes:
        game_set_id = entry.get("game_set_id", "")
        theme = entry.get("theme", "")
        short_link = entry.get("short_link", "")
        short_path = entry.get("short_path", "")
        games_file = entry.get("games_file", "")
        suggested_name = Path(entry.get("metadata", {}).get("suggested_name", "")).stem

        short_url = f"{base_url}/?{short_link}" if short_link else ""
        path_url = f"{base_url}/?config={short_path}" if short_path else ""

        game_entry: dict[str, Any] = {
            "game_set_id": game_set_id,
            "theme": theme,
            "short_link": short_link,
            "short_url": short_url,
            "short_path": short_path,
            "path_url": path_url,
        }
        games.append(game_entry)

        if not suggested_name or not games_file:
            print(f"  SKIP individual meta for {game_set_id}: missing suggested_name or games_file", file=progress)
            continue

        stem = Path(games_file).stem
        individual_dir = meta_dir / suggested_name
        individual_file = individual_dir / f"{stem}.meta.json"

        if not dry_run:
            individual_dir.mkdir(parents=True, exist_ok=True)
            if individual_file.exists() and not force:
                raise ConfigurationError(f"Output file {individual_file} already exists. Use --force to overwrite.")
            with open(individual_file, "w", encoding="utf-8") as fh:
                json.dump(game_entry, fh, indent=2, ensure_ascii=False)
            print(f"  wrote {individual_file}", file=progress)
        else:
            print(f"  [dry-run] would write {individual_file}", file=progress)

    meta_doc: dict[str, Any] = {
        "source_id": source_id,
        "zip": zip_name,
        "games": games,
    }

    meta_file = meta_dir / "meta.json"
    if not dry_run:
        meta_dir.mkdir(parents=True, exist_ok=True)
        if meta_file.exists() and not force:
            raise ConfigurationError(f"Output file {meta_file} already exists. Use --force to overwrite.")
        with open(meta_file, "w", encoding="utf-8") as fh:
            json.dump(meta_doc, fh, indent=2, ensure_ascii=False)
        print(f"\nmeta.json written to {meta_file} ({len(games)} game set(s))", file=progress)
    else:
        print(f"\n[dry-run] would write {meta_file} ({len(games)} game set(s))", file=progress)

    return meta_doc


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find4 Library Generator -- build themes.json and library.json from a directory of game files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config-dir", default="config", help="Directory to read/write config files (themes.json, library.json)")
    parser.add_argument("--games-dir", default="games", help="Directory containing the JSON game files")
    parser.add_argument("--output-dir", default=None, help="Override output directory (defaults to --config-dir)")
    parser.add_argument("--library-dir", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--library-root", default=".", help="Root directory for resolving config_file paths in step 2")
    parser.add_argument("--themes-only", action="store_true", help="Stop after writing themes.json; skip library.json")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output files")
    parser.add_argument("--shuffle", action="store_true", help="Shuffle word order within groups")
    parser.add_argument("--trigger", default="manual", help="Label for who triggered this build (stored in library.json metadata)")
    parser.add_argument(
        "--filter",
        dest="filter_pattern",
        default=None,
        metavar="REGEX",
        help="Only include game sets whose theme, category, or description match this regex (case-insensitive)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes"),
        help="Validate and display results without writing any output files (also set via DRY_RUN env var)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print library.json to stdout instead of writing it to disk; all other output goes to stderr",
    )
    parser.add_argument(
        "-v",
        "--invert-match",
        action="store_true",
        help="Invert the --filter: exclude game sets that match instead of including them",
    )
    parser.add_argument(
        "--no-short-link",
        dest="short_link",
        action="store_false",
        default=True,
        help="Omit the short_link field from theme entries",
    )
    parser.add_argument(
        "--hex-bytes",
        type=int,
        default=3,
        metavar="N",
        help="Length of hex ID strings in bytes (default: 3 = 6 hex chars; use 6 for 12-char IDs)",
    )
    parser.add_argument(
        "--create-meta",
        action="store_true",
        help="Step 3: build results/meta.json and per-game results/<slug>/<stem>.meta.json from themes.json",
    )
    parser.add_argument(
        "--meta-dir",
        default="results",
        metavar="DIR",
        help="Output directory for --create-meta (default: results)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("FIND4_BASE_URL", "https://find4.org"),
        metavar="URL",
        help="Base URL for short_url and path_url construction (also read from FIND4_BASE_URL env var)",
    )
    parser.add_argument(
        "--meta-source-id",
        default="",
        metavar="TEXT",
        help="Free-text source label written into meta.json source_id field",
    )
    parser.add_argument(
        "--meta-zip",
        default="",
        metavar="NAME",
        help="Zip name written into meta.json zip field",
    )
    return parser.parse_args()


def main() -> None:
    try:
        args = parse_arguments()

        if args.hex_bytes < 1 or args.hex_bytes > 32:
            raise ConfigurationError("--hex-bytes must be between 1 and 32")
        hex_length = args.hex_bytes * 2

        if args.filter_pattern:
            try:
                re.compile(args.filter_pattern)
            except re.error as e:
                raise ConfigurationError(f"Invalid --filter regex: {e}") from e

        if args.invert_match and not args.filter_pattern:
            raise ConfigurationError("-v / --invert-match requires --filter")

        games_dir = args.library_dir if args.library_dir is not None else args.games_dir
        output_dir = Path(args.output_dir if args.output_dir is not None else args.config_dir)
        themes_file = output_dir / "themes.json"

        if not args.dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
            if themes_file.exists() and not args.force:
                raise ConfigurationError(f"Output file {themes_file} already exists. Use --force to overwrite.")

        out_to_stdout = args.stdout

        # Step 1: build themes index
        short_code_base = str(output_dir) if args.short_link else None
        indexer = ThemeIndexer(games_dir, args.shuffle, hex_length, args.filter_pattern, args.invert_match, short_code_base)
        entries = indexer.create_theme_index()

        progress = sys.stderr if out_to_stdout else sys.stdout
        indexer.print_validation_report(out=progress)
        print_theme_summary(entries, out=progress)

        if args.dry_run:
            print(f"\n[dry-run] {len(entries)} game set(s) would be written to {themes_file}", file=progress)
        else:
            with open(themes_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
            print(f"\nTheme index saved to {themes_file}", file=progress)

        # Step 3: build results/meta.json and per-game meta files
        if args.create_meta:
            meta_dir = Path(args.meta_dir)
            print(f"\nBuilding meta files in {meta_dir} ...", file=progress)
            build_meta(
                themes=entries,
                meta_dir=meta_dir,
                base_url=args.base_url,
                source_id=args.meta_source_id,
                zip_name=args.meta_zip,
                force=args.force,
                dry_run=args.dry_run,
                progress=progress,
            )

        if args.themes_only:
            return

        # Step 2: build full library.json
        library_file = output_dir / "library.json"
        if not args.dry_run and not out_to_stdout and library_file.exists() and not args.force:
            raise ConfigurationError(f"Output file {library_file} already exists. Use --force to overwrite.")

        progress = sys.stderr if out_to_stdout else sys.stdout
        print(f"\nBuilding library.json from {themes_file} ...", file=progress)
        library = build_full_library(
            themes_path=themes_file,
            library_root=Path(args.library_root),
            trigger=args.trigger,
            themes_data=entries if (args.dry_run or out_to_stdout) else None,
        )

        meta = library["metadata"]
        if args.dry_run:
            print(f"\n[dry-run] library.json would contain {meta['game_set_count']} game set(s)", file=progress)
        elif out_to_stdout:
            json.dump(library, sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
        else:
            with open(library_file, "w", encoding="utf-8") as f:
                json.dump(library, f, indent=2, ensure_ascii=False)
            print(f"\nDone.", file=progress)

        print(f"  game_sets : {meta['game_set_count']}", file=progress)
        print(f"  missing   : {meta['missing_count']}", file=progress)
        print(f"  hash      : {meta['content_hash'][:16]}...", file=progress)
        print(f"  fingerprint: {meta['metadata_fingerprint']}", file=progress)
        if not args.dry_run and not out_to_stdout:
            print(f"  output    : {library_file}", file=progress)

    except ThemeIndexerError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)



if __name__ == "__main__":
    main()
