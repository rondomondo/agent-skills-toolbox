#!/usr/bin/env -S uv run python3
"""
add_ids.py - Post-processing step 2 for find4 skill.

Adds unique MD5-based IDs at three levels of the hierarchy:
  - game_set_id  : identifies a whole game set (theme + all its group_sets)
  - group_set_id : identifies one group_set (a round of 4 groups)
  - group_item_id: identifies one group (category + words + color + description)

IDs are content-addressed hex strings - the same content always produces the
same ID, making cross-file deduplication safe. A top-level id_registry is also
written so the frontend can resolve any ID instantly.

By default groups are output as full dicts and the "theme" field is preserved.
Pass --flatten to enable the compact representation: each group is converted to
a value array, the root-level "schema" key is written, and the redundant "theme"
field is dropped (it is reconstructable from the parent game_set.theme).

The schema order when --flatten is used:

  ["words","category","color","url","description","skill_level",
   "additional_sources","group_item_id","group_set_id"]

Reads JSON from stdin (default) or --game-set-json FILE.
Writes enriched JSON to stdout.

Usage:
    # from stdin (default - use in pipeline)
    cat output/tmp/find4_colored.json | python3 add_ids.py > output/tmp/find4_ids.json

    # from a file
    python3 add_ids.py --game-set-json output/tmp/find4_colored.json > output/tmp/find4_ids.json

    # with compact packed output
    cat output/tmp/find4_colored.json | python3 add_ids.py --flatten > output/tmp/find4_ids.json

    # full pipeline example
    cat raw.json | python3 fix_colors.py | python3 add_ids.py | python3 finalize_metadata.py --source stdin
"""

import argparse
import hashlib
import json
import sys
from typing import Any

GROUP_SCHEMA = [
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


def _pack_group(group: dict[str, Any]) -> list[Any]:
    """Convert a group object to a value array using GROUP_SCHEMA order."""
    return [group.get(k) for k in GROUP_SCHEMA]


def calculate_jsondata_ids(data: dict[str, Any], hex_length: int = 6, flatten: bool = False) -> dict[str, Any]:
    """
    Add unique IDs at game_set, group_set and group_item levels.

    Args:
        data: parsed game JSON with a top-level 'game_sets' key.
        hex_length: number of hex characters for each generated ID.
        flatten: when True, convert each group dict to a packed value array
            and write a root-level 'schema' key; also drops the redundant
            'theme' field from each group.

    Returns:
        Enriched data dict with IDs and id_registry stamped throughout.
    """
    id_registry: dict[str, list[str]] = {"group_set_ids": [], "game_set_ids": [], "group_item_ids": []}

    for game_set in data["game_sets"]:
        game_set_content: list[Any] = []

        for group_set in game_set["group_sets"]:
            group_set_hash_content = []

            for i, group in enumerate(group_set):
                if isinstance(group, list):
                    # already packed; reconstruct minimal dict for hashing
                    schema = data.get("schema", GROUP_SCHEMA)
                    group_dict = dict(zip(schema, group))
                else:
                    group_dict = group

                crucial_fields = [
                    group_dict["category"],
                    ",".join(sorted(group_dict["words"])),
                    group_dict["color"],
                    group_dict["description"],
                ]
                group_item_content = "|".join(crucial_fields)
                group_item_id = hashlib.md5(group_item_content.encode()).hexdigest()[:hex_length]
                group_dict["group_item_id"] = group_item_id

                if group_item_id not in id_registry["group_item_ids"]:
                    id_registry["group_item_ids"].append(group_item_id)

                group_set_hash_content.append(group_item_content)
                group_set[i] = group_dict

            group_set_content_str = "_".join(group_set_hash_content)
            group_set_id = hashlib.md5(group_set_content_str.encode()).hexdigest()[:hex_length]

            if group_set_id not in id_registry["group_set_ids"]:
                id_registry["group_set_ids"].append(group_set_id)

            for j, group_dict in enumerate(group_set):
                group_dict["group_set_id"] = group_set_id
                if flatten:
                    group_dict.pop("theme", None)
                    group_set[j] = _pack_group(group_dict)
                else:
                    group_set[j] = group_dict

            game_set_content.append(group_set_hash_content)

        game_set_hash = hashlib.md5((game_set["theme"] + "_" + str(game_set_content)).encode()).hexdigest()[
            :hex_length
        ]

        if game_set_hash not in id_registry["game_set_ids"]:
            id_registry["game_set_ids"].append(game_set_hash)

        game_set["game_set_id"] = game_set_hash

    if flatten:
        data["schema"] = GROUP_SCHEMA
    data["id_registry"] = id_registry
    return data


def main():
    parser = argparse.ArgumentParser(description="Add IDs to find4 game JSON")
    parser.add_argument("--game-set-json", metavar="FILE", help="Input JSON file (default: read from stdin)")
    parser.add_argument(
        "--hex-bytes", type=int, default=3, metavar="N", help="ID length in bytes (default: 3 -> 6 hex chars)"
    )
    parser.add_argument(
        "--flatten",
        action="store_true",
        default=False,
        help="Pack each group into a value array and write a root 'schema' key (reduces payload size)",
    )
    args = parser.parse_args()

    if args.hex_bytes < 1 or args.hex_bytes > 32:
        print("Error: --hex-bytes must be between 1 and 32", file=sys.stderr)
        sys.exit(1)
    hex_length = args.hex_bytes * 2

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
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(1)

    if "game_sets" not in data:
        print("Error: Input JSON missing 'game_sets' key", file=sys.stderr)
        sys.exit(1)

    result = calculate_jsondata_ids(data, hex_length, flatten=args.flatten)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
