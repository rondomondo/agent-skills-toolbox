#!/usr/bin/env -S uv run python3
"""
finalize_metadata.py - Post-processing step 3 for find4 skill.

The final enrichment pass before a game file is saved to disk. It:
  1. Stamps metadata.modified_at with the current ISO timestamp.
  2. Records metadata.source_id so the origin of the file is traceable.
  3. Moves the top-level id_registry into metadata.id_registry (single
     location -- root key is removed).
  4. Generates metadata.id -- a URL-safe base64 hash of the entire
     payload -- giving each file a globally unique, stable fingerprint.

The --source argument should be the canonical identifier of the input:
a URL, a file path, or the literal string "stdin".

Reads JSON from stdin (default) or --game-set-json FILE.
Writes finalized JSON to stdout.

Usage:
    # from a URL source
    cat output/tmp/find4_ids.json | python3 finalize_metadata.py \\
        --source "https://example.com/article" > output/tmp/find4_final.json

    # from a local file source
    python3 finalize_metadata.py \\
        --game-set-json output/tmp/find4_ids.json \\
        --source "my-notes.txt" > output/tmp/find4_final.json

    # full pipeline (all three post-processing steps)
    cat raw.json \\
      | python3 fix_colors.py \\
      | python3 add_ids.py \\
      | python3 finalize_metadata.py --source "https://example.com" \\
      > games/my-game.json
"""

import argparse
import base64
import json
import sys
from datetime import datetime
from typing import Any

try:
    import mmh3

    def _hash128(data: bytes) -> int:
        return mmh3.hash128(data, signed=False)

except ImportError:
    # Fallback: use hashlib sha256 if mmh3 not available
    import hashlib

    def _hash128(data: bytes) -> int:
        h = hashlib.sha256(data).digest()[:16]
        return int.from_bytes(h, byteorder="big")


def generate_url_safe_hash(data: Any, length: int = 16) -> str:
    """Generate a URL-safe base64 hash from any data."""
    if not isinstance(data, (str, bytes)):
        data = json.dumps(data, sort_keys=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    hash_value = _hash128(data)
    hash_bytes = hash_value.to_bytes(16, byteorder="big")
    hash_b64 = base64.urlsafe_b64encode(hash_bytes).decode("ascii").rstrip("=")
    return hash_b64[:length]


def finalize_metadata(data: dict[str, Any], source_identifier: str) -> dict[str, Any]:
    """
    Stamp metadata with runtime info and promote id_registry into metadata.
    """
    import copy

    result = copy.deepcopy(data)

    if "metadata" not in result:
        raise RuntimeError("Input JSON is missing 'metadata' key")

    result["metadata"].update(
        {
            "modified_at": datetime.now().isoformat(),
            "source_id": source_identifier,
            "step": "finalize_metadata",
        }
    )
    result["metadata"].pop("promoted", None)

    # Move id_registry into metadata (single location -- remove from root)
    if id_registry := result.pop("id_registry", None):
        result["metadata"]["id_registry"] = id_registry

    # Add a top-level unique hash ID for the whole payload
    result["metadata"]["id"] = generate_url_safe_hash(result)

    return result


def main():
    parser = argparse.ArgumentParser(description="Finalize find4 game JSON metadata")
    parser.add_argument("--source", default="unknown", help="Source identifier (URL, filename, or 'stdin')")
    parser.add_argument("--game-set-json", metavar="FILE", help="Input JSON file (default: read from stdin)")
    args = parser.parse_args()

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

    try:
        result = finalize_metadata(data, args.source)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
