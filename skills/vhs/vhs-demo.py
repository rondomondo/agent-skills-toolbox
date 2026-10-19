#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the vhs-rec command that records any command as a GIF.

    vhs-demo url2pdf https://en.wikipedia.org/wiki/Special:Random

prints

    vhs-rec demo -o docs/url2pdf.gif --install screenshot --snippet -- url2pdf https://en.wikipedia.org/wiki/Special:Random

Paste the line to record it, or pipe a batch to a shell: vhs-demo --catalog | sh
"""

import argparse
import re
import shlex
import sys
from pathlib import Path

DEFAULT_DIR = "docs"
DEFAULT_HEAD = 20
HELP_WORDS = frozenset({"-h", "--help", "help"})
SUBCOMMAND = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")

# Off screen steps that put a tool inside the recording container. Anything not listed is assumed to be in the
# vhs-rec image already (git, docker, make, curl and so on).
SCREENSHOT = ["--install", "screenshot"]
SANITISE_URL = "https://raw.githubusercontent.com/rondomondo/toolbox/main/sanitise-ascii/sanitise-ascii.py"
REGCTL_URL = (
    "https://github.com/regclient/regclient/releases/latest/download/regctl-linux-$(dpkg --print-architecture)"
)


def fetch_setup(name: str, url: str) -> list[str]:
    """Return the vhs-rec setup flags that download a single file tool into ~/.local/bin.

    sudo is avoided on purpose: it flushes keystrokes typed ahead, which swallows the wait marker that vhs-rec types
    straight after a setup command.
    """
    target = f"~/.local/bin/{name}"
    command = (
        f"command -v {name} >/dev/null 2>&1 || "
        f"{{ mkdir -p ~/.local/bin && curl -fsSL -o {target} {url} && chmod +x {target}; }} >/dev/null 2>&1; "
        'export PATH="$HOME/.local/bin:$PATH"'
    )
    return ["--setup", command]


TOOLS: dict[str, list[str]] = {
    "url2pdf": SCREENSHOT,
    "url2image": SCREENSHOT,
    "pdf-strip": ["--install", "pdf-strip"],
    "mermaid-render": ["--install", "mermaid-render"],
    "sanitise-ascii": fetch_setup("sanitise-ascii", SANITISE_URL),
    "regctl": fetch_setup("regctl", REGCTL_URL),
}

# Present in the vhs-rec image, so no note is printed for them.
IN_IMAGE = frozenset(
    {
        "git",
        "docker",
        "make",
        "curl",
        "wget",
        "ls",
        "cat",
        "echo",
        "uv",
        "go",
        "python3",
        "ssh",
    }
)

# git opens a man page for --help, which needs a pager, so it gets -h.
CATALOG = [
    "sanitise-ascii --help",
    "pdf-strip --help",
    "mermaid-render --help",
    "url2image --help",
    "url2pdf --help",
    "regctl --help",
    "docker --help",
    "docker ps --help",
    "docker run --help",
    "git -h",
    "git log -h",
    "git status -h",
    "git diff -h",
]


def slug_for(words: list[str]) -> str:
    """Derive a file stem from a command: tool, one subcommand, and 'help' when asking for help.

    Args:
        words: the command and its arguments.

    Returns:
        A lower case stem such as 'git-log' or 'docker-ps-help'.
    """
    parts = [Path(words[0]).name]
    if len(words) > 1 and SUBCOMMAND.match(words[1]) and words[1] not in HELP_WORDS:
        parts.append(words[1])
    if HELP_WORDS.intersection(words[1:]):
        parts.append("help")
    return re.sub(r"[^a-z0-9]+", "-", "-".join(parts).lower()).strip("-")


def build_line(
    words: list[str],
    out_dir: str = DEFAULT_DIR,
    output: str | None = None,
    installs: list[str] | None = None,
    envs: list[str] | None = None,
    thens: list[str] | None = None,
    head: int | None = None,
) -> str:
    """Build the full vhs-rec command line for one command.

    Args:
        words: the command and its arguments.
        out_dir: directory for the GIF when output is not given.
        output: explicit GIF path.
        installs: toolbox names or images to install off screen; replaces the built-in choice for the tool.
        envs: KEY=VALUE variables to export off screen.
        thens: extra commands to show after the main one.
        head: when set, show the command piped through head -n so long output keeps its first lines on screen.

    Returns:
        One shell line starting with 'vhs-rec demo'.
    """
    path = output or f"{out_dir.rstrip('/')}/{slug_for(words)}.gif"
    args = ["vhs-rec", "demo", "-o", path]
    if installs:
        for target in installs:
            args += ["--install", target]
    else:
        args += TOOLS.get(Path(words[0]).name, [])
    for env in envs or []:
        args += ["--env", env]
    for extra in thens or []:
        args += ["--then", extra]
    args.append("--snippet")
    if head:
        args += ["-x", f"{shlex.join(words)} | head -n {head}"]
    else:
        args += ["--", *words]
    return shlex.join(args)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="vhs-demo",
        description="Print the vhs-rec command that records any command as a GIF with a README snippet.",
        epilog="Options go before the command: vhs-demo --head 20 docker --help",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="the command to record, with its arguments",
    )
    parser.add_argument(
        "--catalog",
        action="store_true",
        help="print a line for the help of every built-in tool",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="show the tools that vhs-demo knows how to install",
    )
    parser.add_argument("-o", "--output", help="GIF path (default: docs/<tool>.gif)")
    parser.add_argument(
        "-d",
        "--dir",
        default=DEFAULT_DIR,
        help="directory for GIFs (default: %(default)s)",
    )
    parser.add_argument("--head", type=int, metavar="N", help="show the command piped through head -n N")
    parser.add_argument(
        "--install",
        action="append",
        help="toolbox name or image to install, repeatable",
    )
    parser.add_argument(
        "--env",
        action="append",
        metavar="KEY=VALUE",
        help="variable to export, repeatable",
    )
    parser.add_argument(
        "--then",
        action="append",
        metavar="CMD",
        help="extra command to show afterwards, repeatable",
    )
    return parser.parse_args(argv)


def main() -> None:
    """Entry point."""
    args = parse_args(sys.argv[1:])
    words = args.command[1:] if args.command[:1] == ["--"] else args.command
    if args.list:
        for name, flags in TOOLS.items():
            print(f"{name:16} {shlex.join(flags)}")
        return
    if args.catalog:
        if words or args.output:
            print("vhs-demo: --catalog takes no command or --output", file=sys.stderr)
            sys.exit(1)
        for entry in CATALOG:
            print(build_line(shlex.split(entry), args.dir, head=DEFAULT_HEAD))
        return
    if not words:
        print(
            "vhs-demo: give a command to record, e.g. vhs-demo url2pdf https://example.com",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.head is not None and args.head < 1:
        print("vhs-demo: --head must be at least 1", file=sys.stderr)
        sys.exit(1)
    name = Path(words[0]).name
    if name not in TOOLS and name not in IN_IMAGE and not args.install:
        print(
            f"vhs-demo: note: '{name}' is not a known toolbox tool, assuming the vhs-rec image has it",
            file=sys.stderr,
        )
    print(build_line(words, args.dir, args.output, args.install, args.env, args.then, args.head))


if __name__ == "__main__":
    main()
