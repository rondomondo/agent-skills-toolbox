#!/usr/bin/env -S uv run python3
"""
validate.py - Validates a find4 game JSON file against the expected structure.

Two validation modes:

  Default (structural):
    - root has a game_sets list with at least one entry
    - each game_set has theme and group_sets
    - each group_set has exactly 4 groups
    - each group has words (list of 4 strings), category, color,
      description, and skill_level
    - color is from the valid palette (red, blue, green, yellow,
      orange, indigo, purple, teal)
    - skill_level is one of: Beginner, Intermediate, Advanced, Expert
    - all 4 colors within a group_set are distinct

  Strict (--strict, for fully post-processed files):
    - all default checks, plus:
    - game_set_id present and valid hex ID
    - group_item_id and group_set_id present on every group
    - root has a metadata block; id_registry is inside metadata

  Fix mode (--fix):
    - Runs the full post-processing pipeline inline to repair fixable issues:
      - Wraps bare group_sets into proper game_sets structure
      - Adds missing IDs (game_set_id, group_set_id, group_item_id)
      - Adds missing id_registry
      - Adds minimal metadata block if absent
    - Outputs fixed JSON to stdout (or --output FILE)
    - Non-fixable errors (bad words count, invalid skill_level, etc.) still fail

Files using the packed schema format (groups as value arrays with a root
"schema" key) are automatically hydrated to full objects before validation
and re-packed before output.

Exits 0 on success, 1 on any validation error.
Errors are written to stderr; the OK summary goes to stdout.

Reads JSON from stdin (default) or --game-set-json FILE.

Usage:
    # validate a finished game file (strict -- all IDs and metadata required)
    python3 validate.py --game-set-json config/default.json --strict

    # validate raw LLM output before post-processing
    cat output/tmp/find4_raw.json | python3 validate.py

    # automatically fix a bad file
    python3 validate.py --game-set-json games/bad.json --fix > games/fixed.json

    # fix and overwrite the original file
    python3 validate.py --game-set-json games/bad.json -i

    # validate every file in the games directory
    for f in games/*.json; do python3 validate.py --game-set-json "$f" --strict; done

    # validate/fix with shorter IDs
    python3 validate.py --game-set-json games/foo.json --hex-bytes 3 --fix
"""

import argparse
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from typing import Any

COLOR_PALETTE = {"red", "blue", "green", "yellow", "orange", "indigo", "purple", "teal"}
COLOR_PALETTE_ORDERED = ["red", "blue", "green", "yellow", "orange", "indigo", "purple", "teal"]
VALID_SKILL_LEVELS = {"Beginner", "Intermediate", "Advanced", "Expert"}
HEX_CHARS = set("0123456789abcdef")

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


# ---------------------------------------------------------------------------
# Schema hydration / packing
# ---------------------------------------------------------------------------


def _hydrate_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    If groups are packed value arrays, expand them to dicts using root schema.
    Returns a deep copy with all groups as dicts. No-op if already objects.
    """
    schema = data.get("schema", DEFAULT_SCHEMA)
    data = copy.deepcopy(data)
    for game_set in data.get("game_sets", []):
        for group_set in game_set.get("group_sets", []):
            for i, group in enumerate(group_set):
                if isinstance(group, list):
                    group_set[i] = dict(zip(schema, group))
    return data


def _pack_group(group: dict[str, Any], schema: list[str]) -> list[Any]:
    return [group.get(k) for k in schema]


def _pack_data(data: dict[str, Any]) -> dict[str, Any]:
    """Convert all group dicts to packed value arrays. Writes root schema key."""
    schema = data.get("schema", DEFAULT_SCHEMA)
    data["schema"] = schema
    for game_set in data.get("game_sets", []):
        for group_set in game_set.get("group_sets", []):
            for i, group in enumerate(group_set):
                if isinstance(group, dict):
                    group_set[i] = _pack_group(group, schema)
    return data


def _is_packed(data: dict[str, Any]) -> bool:
    """True if any group in the data is a packed list (not a dict)."""
    for game_set in data.get("game_sets", []):
        for group_set in game_set.get("group_sets", []):
            for group in group_set:
                if isinstance(group, list):
                    return True
    return False


# ---------------------------------------------------------------------------
# Fixable issue types -- used to decide what --fix can repair
# ---------------------------------------------------------------------------

FIXABLE = {
    "missing_game_sets_wrapper",  # bare group_sets at root, not in game_sets
    "missing_metadata",  # no metadata block
    "missing_id_registry",  # no id_registry
    "duplicate_id_registry",  # id_registry at both root and metadata
    "missing_game_set_id",  # game_set lacks game_set_id
    "missing_group_item_id",  # group lacks group_item_id
    "missing_group_set_id",  # group lacks group_set_id
}


class Issue:
    def __init__(self, path: str, message: str, tag: str | None = None):
        self.path = path
        self.message = message
        self.tag = tag

    def is_fixable(self) -> bool:
        return self.tag in FIXABLE

    def __str__(self) -> str:
        fix_hint = " [fixable with --fix]" if self.is_fixable() else ""
        return f"{self.path}: {self.message}{fix_hint}"


# ---------------------------------------------------------------------------
# Structural detection helpers
# ---------------------------------------------------------------------------


def _is_valid_hex_id(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and set(value) <= HEX_CHARS


def _detect_bare_group_sets(data: Any) -> bool:
    return isinstance(data, dict) and "group_sets" in data and "game_sets" not in data


# ---------------------------------------------------------------------------
# Validators (operate on hydrated dicts)
# ---------------------------------------------------------------------------


def validate_group(group: Any, path: str, strict: bool = False, hex_length: int = 6) -> list[Issue]:
    issues = []
    if not isinstance(group, dict):
        issues.append(Issue(path, f"must be an object, got {type(group).__name__}"))
        return issues

    for field in ("words", "category", "color", "description", "skill_level"):
        if field not in group:
            issues.append(Issue(path, f"missing required field '{field}'"))

    if "words" in group:
        if not isinstance(group["words"], list) or len(group["words"]) != 4:
            issues.append(Issue(path, "words: must be a list of exactly 4 items"))
        elif not all(isinstance(w, str) for w in group["words"]):
            issues.append(Issue(path, "words: all items must be strings"))

    if "color" in group and group["color"] not in COLOR_PALETTE:
        issues.append(Issue(path, f"color: '{group['color']}' not in palette {sorted(COLOR_PALETTE)}"))

    if "skill_level" in group and group["skill_level"] not in VALID_SKILL_LEVELS:
        issues.append(Issue(path, f"skill_level: '{group['skill_level']}' not in {sorted(VALID_SKILL_LEVELS)}"))

    if strict or "group_item_id" in group:
        if "group_item_id" not in group:
            issues.append(Issue(path, "missing 'group_item_id' (run add_ids.py)", "missing_group_item_id"))
        elif not _is_valid_hex_id(group["group_item_id"], hex_length):
            issues.append(
                Issue(
                    path, f"group_item_id: invalid format '{group['group_item_id']}' (expected {hex_length} hex chars)"
                )
            )

    if strict or "group_set_id" in group:
        if "group_set_id" not in group:
            issues.append(Issue(path, "missing 'group_set_id' (run add_ids.py)", "missing_group_set_id"))
        elif not _is_valid_hex_id(group["group_set_id"], hex_length):
            issues.append(
                Issue(
                    path, f"group_set_id: invalid format '{group['group_set_id']}' (expected {hex_length} hex chars)"
                )
            )

    return issues


def validate_group_set(group_set: Any, path: str, strict: bool = False, hex_length: int = 6) -> list[Issue]:
    issues = []
    if not isinstance(group_set, list):
        issues.append(Issue(path, f"must be a list, got {type(group_set).__name__}"))
        return issues
    if len(group_set) != 4:
        issues.append(Issue(path, f"must contain exactly 4 groups, got {len(group_set)}"))

    colors_seen = []
    for i, group in enumerate(group_set):
        issues.extend(validate_group(group, f"{path}[{i}]", strict, hex_length))
        if isinstance(group, dict) and "color" in group:
            colors_seen.append(group["color"])

    if len(colors_seen) == 4 and len(set(colors_seen)) != 4:
        issues.append(Issue(path, f"colors must all be distinct, got {colors_seen}"))

    return issues


def validate_game_set(game_set: Any, path: str, strict: bool = False, hex_length: int = 6) -> list[Issue]:
    issues = []
    if not isinstance(game_set, dict):
        issues.append(Issue(path, f"must be an object, got {type(game_set).__name__}"))
        return issues

    for field in ("theme", "group_sets"):
        if field not in game_set:
            issues.append(Issue(path, f"missing required field '{field}'"))

    if "game_set_id" not in game_set:
        if strict:
            issues.append(Issue(path, "missing 'game_set_id' (run add_ids.py)", "missing_game_set_id"))
    else:
        if not _is_valid_hex_id(game_set["game_set_id"], hex_length):
            issues.append(
                Issue(
                    path, f"game_set_id: invalid format '{game_set['game_set_id']}' (expected {hex_length} hex chars)"
                )
            )

    if "group_sets" in game_set:
        if not isinstance(game_set["group_sets"], list):
            issues.append(Issue(path, "group_sets: must be a list"))
        else:
            for i, group_set in enumerate(game_set["group_sets"]):
                issues.extend(validate_group_set(group_set, f"{path}.group_sets[{i}]", strict, hex_length))

    return issues


def validate(data: Any, strict: bool = False, hex_length: int = 6) -> tuple[list[Issue], list[str]]:
    """
    Hydrates packed groups before validating. Returns (issues, suggestions).
    """
    issues: list[Issue] = []
    suggestions: list[str] = []

    if not isinstance(data, dict):
        issues.append(Issue("root", f"must be an object, got {type(data).__name__}"))
        return issues, suggestions

    # Work on hydrated copy so validators always see dicts
    hydrated = _hydrate_data(data)

    if _detect_bare_group_sets(hydrated):
        issues.append(
            Issue(
                "root",
                "has 'group_sets' at root level instead of inside 'game_sets' list -- "
                "this looks like a legacy or incorrectly structured file",
                "missing_game_sets_wrapper",
            )
        )
        suggestions.append("Wrap root group_sets inside a game_sets list with a theme")
        for i, group_set in enumerate(hydrated.get("group_sets", [])):
            if isinstance(group_set, list):
                issues.extend(validate_group_set(group_set, f"group_sets[{i}]", strict, hex_length))
            else:
                issues.extend(validate_group(group_set, f"group_sets[{i}]", strict, hex_length))
    elif "game_sets" not in hydrated:
        issues.append(Issue("root", "missing required field 'game_sets'"))
    else:
        if not isinstance(hydrated["game_sets"], list):
            issues.append(Issue("root.game_sets", "must be a list"))
        elif len(hydrated["game_sets"]) == 0:
            issues.append(Issue("root.game_sets", "must contain at least one game set"))
        else:
            for i, game_set in enumerate(hydrated["game_sets"]):
                issues.extend(validate_game_set(game_set, f"game_sets[{i}]", strict, hex_length))

    # metadata check
    if "metadata" not in hydrated:
        tag = "missing_metadata"
        issues.append(Issue("root", "missing 'metadata' block -- file has not been through finalize_metadata.py", tag))
        suggestions.append("Add minimal metadata block with generated_at, source, and id")

    # id_registry check -- must be in metadata (post-finalize) or root (mid-pipeline)
    metadata = hydrated.get("metadata", {})
    has_registry = "id_registry" in metadata or "id_registry" in hydrated
    if not has_registry and not _detect_bare_group_sets(hydrated):
        if strict or "game_sets" in hydrated:
            issues.append(
                Issue(
                    "root", "missing 'id_registry' (run add_ids.py then finalize_metadata.py)", "missing_id_registry"
                )
            )
            suggestions.append("Regenerate id_registry from content hashes via add_ids.py")

    if "id_registry" in hydrated and "id_registry" in metadata:
        issues.append(
            Issue(
                "root",
                "id_registry exists at both root and metadata -- root copy will be dropped",
                "duplicate_id_registry",
            )
        )

    return issues, suggestions


# ---------------------------------------------------------------------------
# Fix logic
# ---------------------------------------------------------------------------


def _md5_hex(content: str, length: int = 6) -> str:
    return hashlib.md5(content.encode()).hexdigest()[:length]


def _add_ids(data: dict[str, Any], hex_length: int = 6) -> dict[str, Any]:
    """Add group_item_id, group_set_id, game_set_id, and rebuild id_registry."""
    from add_ids import GROUP_SCHEMA as SCHEMA

    id_registry: dict[str, list[str]] = {"group_set_ids": [], "game_set_ids": [], "group_item_ids": []}

    for game_set in data["game_sets"]:
        game_set_hash_parts = []

        for group_set in game_set["group_sets"]:
            group_set_hash_parts_inner = []

            for i, group in enumerate(group_set):
                group_dict = group if isinstance(group, dict) else dict(zip(data.get("schema", SCHEMA), group))
                crucial = [
                    group_dict.get("category", ""),
                    ",".join(sorted(group_dict.get("words", []))),
                    group_dict.get("color", ""),
                    group_dict.get("description", ""),
                ]
                group_item_content = "|".join(crucial)
                group_item_id = _md5_hex(group_item_content, hex_length)
                group_dict["group_item_id"] = group_item_id
                group_dict.pop("theme", None)
                if group_item_id not in id_registry["group_item_ids"]:
                    id_registry["group_item_ids"].append(group_item_id)
                group_set_hash_parts_inner.append(group_item_content)
                group_set[i] = group_dict

            group_set_content_str = "_".join(group_set_hash_parts_inner)
            group_set_id = _md5_hex(group_set_content_str, hex_length)
            if group_set_id not in id_registry["group_set_ids"]:
                id_registry["group_set_ids"].append(group_set_id)
            for group_dict in group_set:
                group_dict["group_set_id"] = group_set_id

            game_set_hash_parts.append(group_set_hash_parts_inner)

        game_set_hash = _md5_hex(game_set.get("theme", "") + "_" + str(game_set_hash_parts), hex_length)
        if game_set_hash not in id_registry["game_set_ids"]:
            id_registry["game_set_ids"].append(game_set_hash)
        game_set["game_set_id"] = game_set_hash

    data["id_registry"] = id_registry
    return data


def _wrap_bare_structure(data: dict[str, Any]) -> dict[str, Any]:
    theme = data.get("theme", "Unknown Theme")
    game_set_id = data.get("game_set_id")
    game_set: dict[str, Any] = {"theme": theme, "group_sets": data["group_sets"]}
    if game_set_id:
        game_set["game_set_id"] = game_set_id
    skip = {"theme", "group_sets", "game_set_id", "metadata", "id_registry", "schema"}
    new_data: dict[str, Any] = {k: v for k, v in data.items() if k not in skip}
    new_data["game_sets"] = [game_set]
    for k in ("metadata", "id_registry", "schema"):
        if k in data:
            new_data[k] = data[k]
    return new_data


_PLACEHOLDER_SOURCE_IDS = {"unknown", "validate_fix", "", None}


def _is_realistic_source_id(value: Any) -> bool:
    """Return True if value looks like a real origin (URL, filename path) rather than a placeholder."""
    if not isinstance(value, str) or value in _PLACEHOLDER_SOURCE_IDS:
        return False
    return "/" in value or value.startswith("http") or "." in value


def _add_metadata(data: dict[str, Any], source: str = "unknown") -> dict[str, Any]:
    """Add or update the metadata block on data.

    Args:
        data: hydrated game data dict, mutated in place.
        source: caller-supplied source identifier; ignored when the existing
            source_id already looks realistic.

    Returns:
        The mutated data dict.
    """
    now = datetime.now(timezone.utc).isoformat()

    if "metadata" not in data:
        data["metadata"] = {
            "generated_at": now,
            "source": source,
        }

    meta = data["metadata"]

    # Promote an existing modified_at to created_at before overwriting it
    if "modified_at" in meta:
        meta.setdefault("created_at", meta["modified_at"])

    meta["modified_at"] = now

    # Preserve a realistic existing source_id rather than clobbering it
    if not _is_realistic_source_id(meta.get("source_id")):
        meta["source_id"] = source

    meta["step"] = "validate_fix"

    if id_registry := data.pop("id_registry", None):
        meta["id_registry"] = id_registry
        meta["promoted"] = True

    fingerprint_data = json.dumps(data, sort_keys=True).encode()
    meta["id"] = hashlib.sha256(fingerprint_data).hexdigest()[:22]
    return data


def apply_fix(data: dict[str, Any], source: str = "unknown", hex_length: int = 6) -> tuple[dict[str, Any], list[str]]:
    data = copy.deepcopy(data)
    # Hydrate before fixing so all logic works on plain dicts
    data = _hydrate_data(data)
    actions: list[str] = []

    if _detect_bare_group_sets(data):
        data = _wrap_bare_structure(data)
        actions.append("Wrapped root-level group_sets into game_sets list")

    if "id_registry" in data and "id_registry" in data.get("metadata", {}):
        data.pop("id_registry")
        actions.append("Dropped duplicate root-level id_registry (metadata copy retained)")

    data = _add_ids(data, hex_length)
    actions.append(f"Generated/regenerated IDs ({hex_length}-char hex)")

    data = _add_metadata(data, source)
    actions.append("Added/updated metadata block")

    return data, actions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Validate a find4 game JSON file against the expected structure")
    parser.add_argument("--game-set-json", metavar="FILE", help="Input JSON file (default: read from stdin)")
    parser.add_argument("--strict", action="store_true", help="Also require IDs and metadata (fully finalized file)")
    parser.add_argument(
        "--fix", action="store_true", help="Apply fixes for all fixable issues and write corrected JSON to stdout"
    )
    parser.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="Write fixed JSON back to --game-set-json (implies --fix; requires --game-set-json)",
    )
    parser.add_argument(
        "--source", default="unknown", help="Source identifier written into metadata when --fix is used"
    )
    parser.add_argument(
        "--output", metavar="FILE", help="Write fixed JSON to FILE instead of stdout (only with --fix)"
    )
    parser.add_argument(
        "--hex-bytes", type=int, default=3, metavar="N", help="ID length in bytes (default: 3 -> 6 hex chars)"
    )
    args = parser.parse_args()

    if args.hex_bytes < 1 or args.hex_bytes > 32:
        print("Error: --hex-bytes must be between 1 and 32", file=sys.stderr)
        sys.exit(1)
    hex_length = args.hex_bytes * 2

    if args.in_place and not args.game_set_json:
        print("Error: --in-place requires --game-set-json", file=sys.stderr)
        sys.exit(1)

    if args.in_place:
        args.fix = True

    source = args.source
    if source == "unknown" and args.game_set_json:
        source = args.game_set_json

    try:
        if args.game_set_json:
            with open(args.game_set_json, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.load(sys.stdin)
    except FileNotFoundError:
        print(f"Error: File not found: {args.game_set_json}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON -- {e}", file=sys.stderr)
        sys.exit(1)

    issues, suggestions = validate(data, strict=args.strict, hex_length=hex_length)

    fixable = [i for i in issues if i.is_fixable()]
    unfixable = [i for i in issues if not i.is_fixable()]

    if not issues:
        source_label = args.game_set_json or "stdin"
        mode = " (strict)" if args.strict else ""
        packed_note = " [packed schema]" if _is_packed(data) else ""
        print(f"  ok: {source_label} is valid{mode}{packed_note}")
        hydrated = _hydrate_data(data)
        game_sets = hydrated.get("game_sets", [])
        total_groups = sum(len(gs) for game_set in game_sets for gs in game_set.get("group_sets", []))
        print(f"  {len(game_sets)} game set(s), {total_groups} group(s)")
        return

    print(f"INVALID: {len(issues)} issue(s) found\n", file=sys.stderr)
    for issue in issues:
        prefix = "  [fixable]" if issue.is_fixable() else "  [error]  "
        print(f"{prefix} {issue}", file=sys.stderr)

    if suggestions:
        print("\nSuggested fixes:", file=sys.stderr)
        for s in suggestions:
            print(f"  - {s}", file=sys.stderr)

    if fixable and not args.fix:
        print(f"\n  {len(fixable)} issue(s) can be auto-fixed -- rerun with --fix to apply.", file=sys.stderr)
        sys.exit(1)

    if unfixable:
        if args.fix:
            print(f"\nCannot fix: {len(unfixable)} unfixable error(s) must be corrected manually.", file=sys.stderr)
        sys.exit(1)

    if args.fix:
        fixed_data, actions = apply_fix(data, source=source, hex_length=hex_length)
        post_issues, _ = validate(fixed_data, strict=args.strict, hex_length=hex_length)
        remaining_unfixable = [i for i in post_issues if not i.is_fixable()]

        print("\nFix applied:", file=sys.stderr)
        for action in actions:
            print(f"  [x] {action}", file=sys.stderr)

        if remaining_unfixable:
            print("\nRemaining errors after fix:", file=sys.stderr)
            for issue in remaining_unfixable:
                print(f"  - {issue}", file=sys.stderr)
            sys.exit(1)

        fixed_json = json.dumps(fixed_data, indent=2, ensure_ascii=False) + "\n"
        if args.in_place:
            with open(args.game_set_json, "w", encoding="utf-8") as f:
                f.write(fixed_json)
            print(f"\nFixed JSON written in place: {args.game_set_json}", file=sys.stderr)
        elif args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(fixed_json)
            print(f"\nFixed JSON written to: {args.output}", file=sys.stderr)
        else:
            print(fixed_json, end="")


if __name__ == "__main__":
    main()
