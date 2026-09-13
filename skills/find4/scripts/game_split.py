#!/usr/bin/env -S uv run python3
"""Split a combined Find4 game JSON into per-theme files in a named subdirectory."""

import argparse
import copy
import json
import logging
from posixpath import basename
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def make_slug(theme: str) -> str:
    """Convert a theme string to a URL-safe slug.

    Args:
        theme: the game set theme string.

    Returns:
        A lowercase hyphenated slug safe for use as a filename or directory name.
    """
    slug = theme.lower().replace("&", "and")
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug


def _collect_ids(gs: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    """Collect all IDs referenced within a single game_set.

    Args:
        gs: a single game_set dict.

    Returns:
        Tuple of (game_set_ids, group_set_ids, group_item_ids) as sets.
    """
    game_set_ids: set[str] = set()
    group_set_ids: set[str] = set()
    group_item_ids: set[str] = set()

    gid = gs.get("game_set_id")
    if gid:
        game_set_ids.add(gid)

    for group_set in gs.get("group_sets", []):
        for item in group_set:
            gsid = item.get("group_set_id")
            if gsid:
                group_set_ids.add(gsid)
            giid = item.get("group_item_id")
            if giid:
                group_item_ids.add(giid)

    return game_set_ids, group_set_ids, group_item_ids


def _prune_id_registry(registry: dict[str, list[str]], game_set_ids: set[str], group_set_ids: set[str], group_item_ids: set[str]) -> dict[str, list[str]]:
    """Return a copy of id_registry containing only IDs present in this split.

    Args:
        registry: the original id_registry dict.
        game_set_ids: set of game_set_id values in this split.
        group_set_ids: set of group_set_id values in this split.
        group_item_ids: set of group_item_id values in this split.

    Returns:
        Filtered id_registry dict.
    """
    return {
        "game_set_ids": [i for i in registry.get("game_set_ids", []) if i in game_set_ids],
        "group_set_ids": [i for i in registry.get("group_set_ids", []) if i in group_set_ids],
        "group_item_ids": [i for i in registry.get("group_item_ids", []) if i in group_item_ids],
    }


def _rel(path: Path | None, skill_root: Path | None) -> str | None:
    """Return path relative to skill_root when possible, otherwise absolute string."""
    if path is None:
        return None
    if skill_root is not None:
        try:
            return str(path.relative_to(skill_root))
        except ValueError:
            pass
    return str(path)


def mark_combined(data: dict[str, Any], source_path: Path | None, skill_root: Path | None = None) -> dict[str, Any]:
    """Return a copy of data with metadata updated to mark it as the combined master.

    Args:
        data: the combined game JSON.
        source_path: path to the combined JSON file, or None if from stdin.
        skill_root: when provided, file paths in split_info are made relative to this directory.

    Returns:
        Updated copy with split_info added to metadata.
    """
    result = copy.deepcopy(data)
    result.setdefault("metadata", {})["split_info"] = {
        "role": "combined",
        "split_at": datetime.now(timezone.utc).isoformat(),
        "source_file": _rel(source_path, skill_root),
    }
    return result


def split_game(
    data: dict[str, Any],
    output_dir: Path,
    source_path: Path | None = None,
    dry_run: bool = False,
    skill_root: Path | None = None,
) -> list[Path]:
    """Split a combined game JSON into one file per game_set.

    Args:
        data: parsed combined game JSON.
        output_dir: directory in which to write the split files.
        source_path: path to the source combined JSON, used to record provenance.
        dry_run: when True, log what would be written without touching the filesystem.
        skill_root: when provided, file paths in split_info are made relative to this directory.

    Returns:
        List of paths that were (or would be) written.

    Raises:
        ValueError: if the JSON has no game_sets key or it is empty.
    """
    game_sets = data.get("game_sets")
    if not game_sets:
        raise ValueError("No game_sets found in input JSON")

    parent_id = data.get("metadata", {}).get("id")
    registry = data.get("metadata", {}).get("id_registry", {})
    split_at = datetime.now(timezone.utc).isoformat()

    written: list[Path] = []
    for gs in game_sets:
        theme = gs.get("theme", "unnamed")
        slug = make_slug(theme)
        dest = output_dir / f"{slug}.json"

        game_set_ids, group_set_ids, group_item_ids = _collect_ids(gs)
        pruned_registry = _prune_id_registry(registry, game_set_ids, group_set_ids, group_item_ids)

        single = copy.deepcopy(data)
        single["game_sets"] = [gs]
        single.setdefault("metadata", {})["id_registry"] = pruned_registry
        single["metadata"]["split_info"] = {
            "role": "split",
            "split_at": split_at,
            "parent_id": parent_id,
            "parent_file": _rel(source_path, skill_root),
            "theme": theme,
            "slug": slug,
        }

        if dry_run:
            logger.info("dry-run: would write %s (%d group_sets)", dest, len(gs.get("group_sets", [])))
        else:
            dest.write_text(json.dumps(single, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info("wrote %s", dest)

        written.append(dest)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split a combined Find4 game JSON into per-theme files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        metavar="FILE",
        help="combined game JSON file; omit to read from stdin",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        metavar="DIR",
        help="directory to write split files into; defaults to games/<basename> beside the input file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes"),
        help="log what would be written without creating any files (also set via DRY_RUN env var)",
    )
    parser.add_argument(
        "--mark-combined",
        action="store_true",
        help="rewrite the input file with combined/master split_info metadata",
    )
    parser.add_argument(
        "--skill-root",
        type=Path,
        metavar="DIR",
        help="skill root directory; when set, source_file and parent_file in split_info are relative to this path",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="output format for written paths",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )

    source_path: Path | None = None
    if args.input is not None:
        if not args.input.is_file():
            print(f"Error: {args.input} does not exist or is not a file", file=sys.stderr)
            sys.exit(1)
        with open(args.input, encoding="utf-8") as f:
            try:
                data: dict[str, Any] = json.load(f)
            except json.JSONDecodeError as exc:
                print(f"Error: invalid JSON in {args.input}: {exc}", file=sys.stderr)
                sys.exit(1)
        source_path = args.input.resolve()
        basename = args.input.stem
        default_parent = args.input.parent
    else:
        try:
            data = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON on stdin: {exc}", file=sys.stderr)
            sys.exit(1)
        basename = "game"
        default_parent = Path("games")

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = default_parent / basename

    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("output directory: %s", output_dir)

    skill_root: Path | None = args.skill_root.resolve() if args.skill_root else None

    if args.mark_combined and source_path and not args.dry_run:
        marked = mark_combined(data, source_path, skill_root=skill_root)
        source_path.write_text(json.dumps(marked, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("marked %s as combined", source_path)

    try:
        written = split_game(data, output_dir, source_path=source_path, dry_run=args.dry_run, skill_root=skill_root)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        game_sets = data.get("game_sets", [])
        total_group_sets = sum(len(gs.get("group_sets", [])) for gs in game_sets)
        total_items = sum(
            len(item.get("words", [])) for gs in game_sets for group_set in gs.get("group_sets", []) for item in group_set
        )
        result: dict[str, Any] = {
            "source": str(args.input) if args.input is not None else "stdin",
            "slug": basename if args.input is not None else "stdin",
            "stats": {
                "game_sets": len(game_sets),
                "group_sets": total_group_sets,
                "items": total_items,
                "themes": [gs.get("theme", "unnamed") for gs in game_sets],
            },
            "splitfilenames": [str(p) for p in written],
        }
        print(json.dumps(result, ensure_ascii=False))
    else:
        for path in written:
            print(path)


if __name__ == "__main__":
    main()
