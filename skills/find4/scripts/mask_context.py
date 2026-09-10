#!/usr/bin/env -S uv run python3
"""
mask_context.py - Mask sensitive keys from a GitHub Actions context object for safe logging.

Reads a JSON context object (e.g. the github context) plus a context schema that describes
each key's type and whether it is sensitive. Any key marked sensitive in the schema is
replaced with a redacted placeholder so the masked output can be logged freely.

Usage:
    # From a file
    python3 mask_context.py --schema schema.json --input github_ctx.json

    # From stdin (e.g. injected by a workflow step)
    echo '${{ toJson(github) }}' | python3 mask_context.py --schema schema.json

    # Pretty-print to stdout (default); suppress with --quiet
    python3 mask_context.py --schema schema.json --input ctx.json --quiet
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REDACTED = "***"

SENSITIVE_KEYS: frozenset[str] = frozenset(
    [
        "token",
        "secret",
        "password",
        "key",
        "credential",
        "auth",
        "private",
        "access_key",
        "secret_key",
        "api_key",
        "client_secret",
        "pat",
    ]
)


class MaskError(Exception):
    pass


def _is_sensitive_key(key: str, schema: dict[str, Any] | None) -> bool:
    """Return True if the key should be redacted.

    Schema takes precedence: if the schema entry has a 'sensitive' field, use it.
    Otherwise fall back to substring matching against known sensitive key names.
    """
    if schema and key in schema:
        entry = schema[key]
        if isinstance(entry, dict) and "sensitive" in entry:
            return bool(entry["sensitive"])

    key_lower = key.lower()
    return any(s in key_lower for s in SENSITIVE_KEYS)


def mask_object(obj: Any, schema: dict[str, Any] | None, depth: int = 0) -> Any:
    """Recursively mask sensitive keys in a JSON-compatible object.

    Args:
        obj: The value to mask (dict, list, or scalar).
        schema: Optional flat key->descriptor map used for sensitivity decisions.
        depth: Current recursion depth (schema lookup is only applied at depth 0).

    Returns:
        A new object with sensitive values replaced by REDACTED.
    """
    if isinstance(obj, dict):
        return {
            k: (REDACTED if _is_sensitive_key(k, schema if depth == 0 else None) else mask_object(v, None, depth + 1))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [mask_object(item, None, depth + 1) for item in obj]
    return obj


def load_json(source: str | Path | None) -> Any:
    """Load JSON from a file path or stdin if source is None.

    Args:
        source: Path to a JSON file, or None to read from stdin.

    Returns:
        Parsed JSON value.

    Raises:
        MaskError: If the source cannot be read or contains invalid JSON.
    """
    try:
        if source is None:
            raw = sys.stdin.read()
        else:
            raw = Path(source).read_text(encoding="utf-8")
        return json.loads(raw)
    except FileNotFoundError as exc:
        raise MaskError(f"File not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise MaskError(f"Invalid JSON: {exc}") from exc


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mask sensitive keys in a GitHub Actions context object for safe logging",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--schema",
        metavar="FILE",
        help="JSON file describing context keys; each key maps to an object with optional 'sensitive' bool",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        help="JSON context file to mask (reads from stdin if omitted)",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write masked JSON to this file (prints to stdout if omitted)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout output when --output is given",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="JSON indentation spaces",
    )
    return parser.parse_args()


def main() -> None:
    try:
        args = parse_arguments()

        schema: dict[str, Any] | None = None
        if args.schema:
            schema = load_json(args.schema)
            if not isinstance(schema, dict):
                raise MaskError("Schema must be a JSON object")

        context = load_json(args.input)
        masked = mask_object(context, schema)
        output_str = json.dumps(masked, indent=args.indent, ensure_ascii=False)

        if args.output:
            Path(args.output).write_text(output_str + "\n", encoding="utf-8")
            if not args.quiet:
                print(output_str)
        else:
            print(output_str)

    except MaskError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
