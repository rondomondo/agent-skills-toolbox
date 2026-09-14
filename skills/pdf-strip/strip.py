#!/usr/bin/env -S uv run python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pikepdf"]
# ///
"""Strip or check document-level metadata from a PDF.

Removes both metadata stores:
  - the legacy /Info dictionary (Author, Title, Producer, CreationDate, ...)
  - the XMP packet at /Root/Metadata

Usage:
    strip.py [--check] INPUT.pdf [OUTPUT.pdf]

Modes:
    (default)  Strip metadata and write output.
               If OUTPUT is omitted, writes to stripped/<base>.stripped.pdf.
    --check    Report whether metadata is present; exit 1 if any found.
               OUTPUT is ignored in check mode.
"""
import sys
from pathlib import Path

import pikepdf


def check(in_path: Path) -> dict:
    """Return a dict of found metadata fields, empty if clean."""
    found = {}
    with pikepdf.open(in_path) as pdf:
        if pdf.docinfo:
            for k, v in pdf.docinfo.items():
                found[str(k)] = str(v)
        if "/Metadata" in pdf.Root:
            with pdf.open_metadata() as meta:
                for k, v in meta.items():
                    found[f"XMP:{k}"] = str(v)
    return found


def strip(in_path: Path, out_path: Path) -> None:
    with pikepdf.open(in_path) as pdf:
        try:
            del pdf.docinfo
        except (KeyError, AttributeError):
            pass

        if "/Metadata" in pdf.Root:
            del pdf.Root.Metadata

        pdf.save(out_path)


def main(argv: list[str]) -> int:
    args = argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__, file=sys.stderr)
        return 1 if not args else 0

    mode = "strip"
    if args[0] == "--check":
        mode = "check"
        args = args[1:]

    if not args:
        print("error: no input file specified", file=sys.stderr)
        return 1

    in_path = Path(args[0])
    if not in_path.is_file():
        print(f"error: input not found: {in_path}", file=sys.stderr)
        return 2

    if mode == "check":
        found = check(in_path)
        if found:
            print(f"HAS_METADATA: {in_path}")
            for k, v in found.items():
                print(f"  {k}: {v}")
            return 1
        print(f"CLEAN: {in_path}")
        return 0

    out_path = Path(args[1]) if len(args) > 1 else Path("stripped") / in_path.with_suffix(".stripped.pdf").name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    strip(in_path, out_path)
    print(f"wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
