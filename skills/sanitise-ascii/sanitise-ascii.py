#!/usr/bin/env -S uv run python3
"""
sanitise-ascii -- Strip non-ASCII characters from text files

WHY THIS EXISTS
---------------
Text files passed through automated pipelines, shared via version control, or
fed into tools that expect plain ASCII often contain Unicode characters that
look fine on screen but cause silent failures:

  * Smart quotes (U+2018/2019/201C/201D) break shell one-liners embedded in
    code blocks and config snippets.
  * En/em dashes (U+2013/2014) confuse argument parsers when docs are piped
    into scripts.
  * Non-breaking spaces (U+00A0) and zero-width characters (U+200B) produce
    invisible diffs that make code-review noise and can break grep patterns.
  * BOMs and variation selectors (U+FEFF, U+FE0F) corrupt tooling that reads
    files byte-by-byte.
  * Copy-paste from word processors, browsers, Notion, or Confluence is a
    major source -- these apps aggressively apply typographic substitutions.

This tool auto-converts the most common offenders to ASCII equivalents and
flags anything it cannot fix so you can review it manually.  It is safe to run
repeatedly -- clean files are left untouched.

DEFAULT BEHAVIOUR
-----------------
Running with no mode flag (or with SANITISE_ACTION=check) performs a dry run:
files are never modified.  You must pass --fix (or SANITISE_ACTION=fix) to
allow writes.

USAGE
-----
    sanitise-ascii [files...]          # check only (default, no writes)
    sanitise-ascii --check [files]     # same as above, explicit
    sanitise-ascii --fix [files]       # auto-fix in place
    sanitise-ascii --dir <path>        # check all .txt/.md files under a directory
    sanitise-ascii --fix --dir <path>  # fix all .txt/.md files under a directory
    sanitise-ascii --allow-emoji ...   # treat emoji as acceptable (skip them)
    sanitise-ascii --quiet ...         # suppress OK lines

ENVIRONMENT
-----------
    SANITISE_ACTION=check  (default) check only, no writes
    SANITISE_ACTION=fix    allow in-place fixes (equivalent to --fix)

    --fix and --check always override SANITISE_ACTION.
    --fix and --check are mutually exclusive.

EXIT CODES
----------
    0  - all clean (or all auto-fixed successfully)
    1  - unfixable non-ASCII characters remain  (or any non-ASCII in check mode)
"""

import os
import re
import sys
import argparse
from pathlib import Path

# Box-drawing chars used as decorative dash runs in comment section dividers.
# U+2500 (─), U+2501 (━), U+254C (╌), U+254D (╍), U+2550 (═)
BOX_DASH_RE = re.compile(r"[\u2500\u2501\u254c\u254d\u2550]+")

# Any of these on a line means it is part of a tree diagram - leave it alone.
TREE_CHARS = frozenset("\u251c\u2514\u2502\u2510\u250c\u2518\u2524\u252c\u2534\u253c\u2550\u2560\u2563\u2566\u2569\u256c")

# Replacement map: non-ASCII -> ASCII equivalent
# Add entries here as new problem characters are discovered.
REPLACEMENTS: dict[str, str] = {
    # Dashes
    "\u2011": "-",       # non-breaking hyphen -
    "\u2013": "-",       # en dash         -
    "\u2014": "--",      # em dash         --
    "\u2012": "-",       # figure dash     -
    "\u2015": "--",      # horizontal bar  --
    "\u2500": "-",       # box horizontal bar  --
    # Quotes
    "\u2018": "'",       # left single     '
    "\u2019": "'",       # right single    '
    "\u201a": "'",       # low-9 single    '
    "\u201c": '"',       # left double     "
    "\u201d": '"',       # right double    "
    "\u201e": '"',       # low-9 double    "
    "\u2032": "'",       # prime           '
    "\u2033": '"',       # double prime    "

    # Spaces
    "\u00a0": " ",       # non-breaking space
    "\u202f": " ",       # narrow no-break space
    "\u2009": " ",       # thin space
    "\u200b": "",        # zero-width space (drop it)
    "\ufeff": "",        # BOM (drop it)

    # Punctuation
    "\u2026": "...",     # ellipsis        ...
    "\u2022": "-",       # bullet          -
    "\u00b7": "-",       # middle dot      -
    "\u2023": "-",       # triangular bullet -

    # Arrows
    "\u2192": "->",      # right arrow     ->
    "\u2190": "<-",      # left arrow      <-
    "\u2194": "<->",     # left-right      <->
    "\u21d2": "=>",      # double right    =>

    # Math / misc
    "\u00d7": "x",       # multiplication  x
    "\u00f7": "/",       # division        /
    "\u2260": "!=",      # not equal       !=
    "\u2264": "<=",      # less-or-equal   <=
    "\u2265": ">=",      # greater-or-eq   >=
    "\u00b1": "+/-",     # plus-minus      +/-
    "\u00b0": " deg",    # degree          deg
    "\u2212": "-",       # minus sign      -
    "\u2550": "=",       # dbl horizontal  =

    # Typography
    "\u00a7": "Sec.",    # section sign    (§)
    "\u00ae": "(R)",     # registered      (R)
    "\u00a9": "(C)",     # copyright       (C)
    "\u2122": "(TM)",    # trademark       (TM)

    # Symbols
    #"\u26a0": "[!]",     # warning sign    [!]
    "\u2713": "[x]",      # tick    [x]
    "\ufe0f": "",        # variation selector-16 (drop - invisible modifier)
}

REPLACEMENTS_EXTEND: dict[str, str] = {
    "\u2705": "✅",       # Green tick - allow
    "\u274C": "❌"        # Red Check - allow
}

#REPLACEMENTS.update(REPLACEMENTS_EXTEND)

# Characters we explicitly allow when --allow-emoji is set
EMOJI_RANGES: list[tuple[int, int]] = [
    (0x2600, 0x27BF),   # Misc symbols / dingbats (includes checkmarks, warning signs)
    (0x1F300, 0x1FAFF), # Emoji block
]


def fix_comment_box_dashes(text: str) -> tuple[str, int]:
    """Replace box-drawing dash runs on comment lines with plain hyphens.

    Targets lines whose first non-whitespace character is '#' and that do not
    contain tree-drawing characters (which indicate a file-tree diagram).

    Args:
        text: the full file contents.

    Returns:
        A tuple of (fixed_text, count) where count is the number of
        substitutions made.
    """
    count = 0
    lines = text.splitlines(keepends=True)
    result: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#") and not TREE_CHARS.intersection(line):
            new_line, n = BOX_DASH_RE.subn(lambda m: "-" * len(m.group()), line)
            count += n
            result.append(new_line)
        else:
            result.append(line)
    return "".join(result), count


def is_emoji(ch: str) -> bool:
    """Return True if the character falls within a known emoji codepoint range.

    Args:
        ch: a single character to test.

    Returns:
        True if ch is in any of the EMOJI_RANGES.
    """
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in EMOJI_RANGES)


def sanitise(text: str, allow_emoji: bool = False) -> tuple[str, list[tuple[int, str, str]], list[tuple[int, str, int, str]]]:
    """Apply REPLACEMENTS to text and report what remains unfixable.

    Returns:
        A tuple of (fixed_text, fixes_made, remaining_nonascii) where:
            fixes_made is a list of (lineno, original_char, replacement) tuples;
            remaining_nonascii is a list of (lineno, char, codepoint, context) tuples.
    """
    fixes_made: list[tuple[int, str, str]] = []

    text, box_count = fix_comment_box_dashes(text)
    if box_count:
        fixes_made.extend([(0, "\u2500", "-")] * box_count)

    for char, replacement in REPLACEMENTS.items():
        if char not in text:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            count = line.count(char)
            for _ in range(count):
                fixes_made.append((lineno, char, replacement))
        text = text.replace(char, replacement)

    remaining: list[tuple[int, str, int, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for ch in line:
            if ord(ch) > 127:
                if allow_emoji and is_emoji(ch):
                    continue
                ctx = line.strip()[:60]
                remaining.append((lineno, ch, ord(ch), ctx))

    return text, fixes_made, remaining


def process_file(path: Path, check_only: bool = False, allow_emoji: bool = False, quiet: bool = False) -> bool:
    """Process a single file, applying or reporting non-ASCII characters.

    Args:
        path: the file to process.
        check_only: when True, report issues but do not write changes.
        allow_emoji: when True, emoji codepoints are silently allowed.
        quiet: when True, suppress OK messages for clean files.

    Returns:
        True if the file is clean after processing (no unfixable characters remain).
    """
    if path.resolve() == SELF_PATH:
        print(f"  SKIP  {path}: refusing to modify self", file=sys.stderr)
        return True

    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"  ERROR: {path} is not valid UTF-8 - skipping", file=sys.stderr)
        return False

    fixed, fixes_made, remaining = sanitise(original, allow_emoji=allow_emoji)

    if not fixes_made and not remaining:
        if not quiet:
            print(f"  OK    {path}", file=sys.stderr)
        return True

    if fixes_made and not quiet:
        by_line: dict[int, list[tuple[str, str]]] = {}
        for lineno, ch, rep in fixes_made:
            by_line.setdefault(lineno, []).append((ch, rep))
        for lineno in sorted(by_line):
            summary: dict[tuple[str, str], int] = {}
            for ch, rep in by_line[lineno]:
                key = (ch, rep)
                summary[key] = summary.get(key, 0) + 1
            fix_strs = [
                f"U+{ord(ch):04X} ({ch!r}) -> {rep!r} x{count}"
                for (ch, rep), count in summary.items()
            ]
            loc = f":{lineno}" if lineno else ""
            print(f"  FIX   {path}{loc}: {', '.join(fix_strs)}", file=sys.stderr)

    if remaining:
        for lineno, ch, cp, ctx in remaining:
            print(f"  WARN  {path}:{lineno}: U+{cp:04X} ({ch!r}) not in fix map | ...{ctx}...", file=sys.stderr)

    if not check_only and fixes_made:
        path.write_text(fixed, encoding="utf-8")

    return len(remaining) == 0


TEXT_GLOBS = ("*.md", "*.txt", "*.rst", "*.yaml", "*.yml", "*.json", "*.jsonl", "*.toml", "*.sh", "*.py", "*akefile")


SELF_PATH = Path(__file__).resolve()


def find_text_files(directory: Path) -> list[Path]:
    """Return all common text files under directory, sorted by path."""
    seen: set[Path] = set()
    results: list[Path] = []
    for pattern in TEXT_GLOBS:
        for p in directory.rglob(pattern):
            if p.resolve() == SELF_PATH:
                continue
            if p not in seen:
                seen.add(p)
                results.append(p)
    return sorted(results)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sanitise non-ASCII characters from text files.",
        epilog=(
            "Default mode is check (no writes). Use --fix or SANITISE_ACTION=fix to allow changes. "
            "--check and --fix are mutually exclusive."
        ),
    )
    parser.add_argument("files", nargs="*", help="files to process")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--check", action="store_true",
        help="check only - do not modify files; exits 1 if any non-ASCII found (default)",
    )
    mode_group.add_argument(
        "--fix", action="store_true",
        help="auto-fix in place; replaces known non-ASCII chars with ASCII equivalents",
    )

    parser.add_argument(
        "--dir", metavar="PATH", type=Path,
        help=f"process all common text files under this directory recursively ({', '.join(TEXT_GLOBS)})",
    )
    parser.add_argument(
        "--allow-emoji", action="store_true",
        help="allow emoji characters - do not flag them",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="suppress OK messages",
    )
    args = parser.parse_args()

    # Resolve mode: --fix / --check flags override SANITISE_ACTION; default is check.
    env_action = os.environ.get("SANITISE_ACTION", "check").lower()
    if env_action not in ("check", "fix"):
        print(
            f"ERROR: SANITISE_ACTION={env_action!r} is invalid; expected 'check' or 'fix'",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.fix:
        check_only = False
    elif args.check:
        check_only = True
    else:
        check_only = env_action != "fix"

    paths: list[Path] = []

    if args.dir:
        paths = find_text_files(args.dir)
        if not paths:
            globs = ", ".join(TEXT_GLOBS)
            print(f"No text files ({globs}) found under {args.dir}", file=sys.stderr)
            sys.exit(0)
    elif args.files:
        paths = [Path(f) for f in args.files]
    else:
        parser.print_help()
        sys.exit(0)

    mode = "CHECK" if check_only else "FIX"
    print(f"sanitise-ascii [{mode}] - {len(paths)} file(s)", file=sys.stderr)

    all_clean = True
    for path in paths:
        ok = process_file(
            path,
            check_only=check_only,
            allow_emoji=args.allow_emoji,
            quiet=args.quiet,
        )
        if not ok:
            all_clean = False

    if all_clean:
        print("All clean.", file=sys.stderr)
        sys.exit(0)
    else:
        if check_only:
            print("Non-ASCII characters found. Run with --fix to auto-fix.", file=sys.stderr)
        else:
            print("Some characters could not be auto-fixed - review WARNs above.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
