#!/usr/bin/env python3
"""Compare compressed payload sizes for different JSON serialisation strategies."""

import base64
import json
import sys
import zlib
from pathlib import Path


SCHEMA = ["words", "category", "color", "url", "description", "skill_level", "additional_sources", "group_item_id", "group_set_id"]

SHARE_KEYS = ["words", "category", "color", "group_item_id", "group_set_id"]

KEY_MAP = {
    "words": "w",
    "category": "c",
    "color": "o",
    "url": "u",
    "description": "d",
    "skill_level": "s",
    "additional_sources": "a",
    "group_item_id": "i",
    "group_set_id": "g",
    "game_set_id": "G",
    "group_sets": "gs",
    "game_sets": "gS",
    "theme": "t",
}


def encode(data: dict) -> tuple[str, int]:
    raw = json.dumps(data, separators=(",", ":")).encode()
    compressed = zlib.compress(raw, level=9)
    b64 = base64.urlsafe_b64encode(compressed).decode()
    return b64, len(b64)


def strip_group_item(item: dict, keys: list[str]) -> dict:
    return {k: item[k] for k in keys if k in item}


def flatten_group_item(item: dict) -> list:
    return [item.get(k) for k in SCHEMA]


def minify_keys(obj: object) -> object:
    if isinstance(obj, dict):
        return {KEY_MAP.get(k, k): minify_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [minify_keys(i) for i in obj]
    return obj


def stripped_game(data: dict, keys: list[str]) -> dict:
    result = {"game_sets": []}
    for gs in data["game_sets"]:
        new_gs = {"theme": gs["theme"], "game_set_id": gs["game_set_id"], "group_sets": []}
        for group_set in gs["group_sets"]:
            new_gs["group_sets"].append([strip_group_item(item, keys) for item in group_set])
        result["game_sets"].append(new_gs)
    return result


def flattened_game(data: dict) -> dict:
    result = {"schema": SCHEMA, "game_sets": []}
    for gs in data["game_sets"]:
        new_gs = {"theme": gs["theme"], "game_set_id": gs["game_set_id"], "group_sets": []}
        for group_set in gs["group_sets"]:
            new_gs["group_sets"].append([flatten_group_item(item) for item in group_set])
        result["game_sets"].append(new_gs)
    return result


def report(label: str, data: dict) -> int:
    raw = json.dumps(data, separators=(",", ":")).encode()
    b64, size = encode(data)
    print(f"  {label:<45} raw={len(raw):>6}B  b64={size:>5}B")
    return size


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("games/physics-chemistry-teens.json")
    data = json.loads(path.read_text())

    print(f"\nPayload size comparison for: {path.name}\n")

    baseline = report("1. Baseline (current)", data)
    stripped_share = report("2. Strip to share keys only", stripped_game(data, SHARE_KEYS))
    stripped_all = report("3. Strip non-essential (keep url/desc/skill)", stripped_game(data, SHARE_KEYS + ["url", "description", "skill_level"]))
    minified = report("4. Minify key names (full payload)", minify_keys(data))
    flat = report("5. Flatten to arrays (full schema)", flattened_game(data))
    flat_minified = report("6. Flatten + minify key names", minify_keys(flattened_game(data)))

    print(f"\n  Savings vs baseline:")
    for label, size in [
        ("2. Strip to share keys", stripped_share),
        ("3. Strip non-essential", stripped_all),
        ("4. Minify keys", minified),
        ("5. Flatten arrays", flat),
        ("6. Flatten + minify", flat_minified),
    ]:
        saving = baseline - size
        pct = saving / baseline * 100
        print(f"    {label:<40} -{saving:>4}B  ({pct:.1f}%)")


if __name__ == "__main__":
    main()
