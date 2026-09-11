"""Print /qr skill examples with ANSI colour formatting.

Run directly:  python3 scripts/extract_skill_examples.py
Invoked by:   /qr examples
"""

# -- ANSI palette ------------------------------------------------------------
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
ITALIC = "\033[3m"

BLACK  = "\033[30m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
BLUE   = "\033[34m"
MAGENTA= "\033[35m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"

BG_BLACK   = "\033[40m"
BG_RED     = "\033[41m"
BG_GREEN   = "\033[42m"
BG_YELLOW  = "\033[43m"
BG_BLUE    = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN    = "\033[46m"
BG_WHITE   = "\033[47m"

# bright variants
BRIGHT_BLACK   = "\033[90m"
BRIGHT_RED     = "\033[91m"
BRIGHT_GREEN   = "\033[92m"
BRIGHT_YELLOW  = "\033[93m"
BRIGHT_BLUE    = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN    = "\033[96m"
BRIGHT_WHITE   = "\033[97m"

# -- Example data -------------------------------------------------------------
# Each group: { "title": str, "note": str|None, "examples": [(label, cmd)] }

GROUPS = [
    {
        "title": "Dot styles  (dotsOptions.type)",
        "note": "Six shapes for the QR module dots",
        "examples": [
            ("square (default)",  "/qr https://example.com square #2B4D00 on #D4F299"),
            ("rounded",           "/qr https://example.com rounded #2B4D00 on #D4F299"),
            ("circles / dots",    "/qr https://example.com circles #2B4D00 on #D4F299"),
            ("classy",            "/qr https://example.com classy #2B4D00 on #D4F299"),
            ("classy-rounded",    "/qr https://example.com classy rounded #2B4D00 on #D4F299"),
            ("extra-rounded",     "/qr https://example.com extra-rounded #2B4D00 on #D4F299"),
        ],
    },
    {
        "title": "Corner square styles  (cornersSquareOptions.type)",
        "note": "The three finder-pattern square shapes",
        "examples": [
            ("square corners",        "/qr https://example.com rounded #064E3B on #A7F3D0 square corners"),
            ("dot corners",           "/qr https://example.com rounded #064E3B on #A7F3D0 dot corners"),
            ("round corners",         "/qr https://example.com rounded #064E3B on #A7F3D0 round corners"),
        ],
    },
    {
        "title": "Corner dot styles  (cornersDotOptions.type)",
        "note": "The inner dot of each finder pattern",
        "examples": [
            ("square corner dots",    "/qr https://example.com rounded #5C3A00 on #FDE68A round corners square corner dots"),
            ("dot corner dots",       "/qr https://example.com rounded #5C3A00 on #FDE68A round corners dot corner dots"),
        ],
    },
    {
        "title": "Error correction levels  (qrOptions.errorCorrectionLevel)",
        "note": "Higher = more redundancy; use H when embedding a logo",
        "examples": [
            ("L  (~7% recovery)",     "/qr https://example.com rounded #3B3100 on #FFF3C4 low error correction"),
            ("M  (~15% recovery)",    "/qr https://example.com rounded #3B3100 on #FFF3C4 medium error correction"),
            ("Q  (~25%, default)",    "/qr https://example.com rounded #3B3100 on #FFF3C4 standard error correction"),
            ("H  (~30%, use w/ logo)","/qr https://example.com rounded #3B3100 on #FFF3C4 high error correction"),
        ],
    },
    {
        "title": "Output formats",
        "note": None,
        "examples": [
            ("PNG  (default)",        "/qr https://example.com rounded #993C1D on #FAECE7"),
            ("JPEG",                  "/qr https://example.com rounded #993C1D on #FAECE7 jpg"),
            ("WebP",                  "/qr https://example.com rounded #993C1D on #FAECE7 webp"),
            ("SVG  (vector)",         "/qr https://example.com rounded #993C1D on #FAECE7 svg"),
        ],
    },
    {
        "title": "Full flag form  (individual CLI flags)",
        "note": "All flags passed explicitly — useful for precise control",
        "examples": [
            (
                "600 px, extra-rounded, logo-ready",
                (
                    "/qr https://example.com extra-rounded #4A1B0C on #F5C4B3 "
                    "round corners dot corner dots high error correction 600px"
                ),
            ),
        ],
    },
    {
        "title": "JSON blob form  (--json)",
        "note": "Pass a raw JSON config for complex or logo-bearing codes",
        "examples": [
            (
                "Facebook with logo",
                (
                    "/qr https://facebook.com extra-rounded #185FA5 on #E6F1FB "
                    "round corners dot corner dots high error correction 600px "
                    "with logo https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg"
                ),
            ),
            (
                "Geo-check with avatar logo",
                (
                    "/qr https://browserleaks.com/geo extra-rounded #185FA5 on #E6F1FB "
                    "round corners dot corner dots standard error correction jpg 600px "
                    "with logo https://i.imgur.com/IKGBe9H.png"
                ),
            ),
        ],
    },
    {
        "title": "Pipe via HEREDOC  (Claude Code CLI)",
        "note": "Feed a /qr command straight to claude from the terminal",
        "examples": [
            (
                "geo check — extra-rounded blue, jpg output",
                "claude << 'EOF'\n  /qr https://browserleaks.com/geo extra-rounded #185FA5 on #E6F1FB as jpg\nEOF",
            ),
        ],
    },
]

# -- Rendering helpers --------------------------------------------------------

WIDTH = 78  # terminal column target


def hr(char="-", colour=DIM):
    return f"{colour}{char * WIDTH}{RESET}"


def section_header(title: str, idx: int) -> str:
    num   = f"{BOLD}{BRIGHT_CYAN}{idx}{RESET}"
    arrow = f"{BRIGHT_BLACK}›{RESET}"
    label = f"{BOLD}{WHITE}{title}{RESET}"
    return f"  {num} {arrow} {label}"


def render_label(label: str) -> str:
    return f"    {BRIGHT_BLACK}▸{RESET} {YELLOW}{label}{RESET}"


def render_cmd(cmd: str, is_heredoc: bool = False) -> str:
    lines = cmd.splitlines()
    out = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            out.append(f"      {DIM}{line}{RESET}")
        elif is_heredoc and stripped in ("EOF",):
            out.append(f"      {BRIGHT_GREEN}{stripped}{RESET}")
        elif is_heredoc and stripped.startswith("claude"):
            out.append(f"      {BOLD}{BRIGHT_GREEN}{line}{RESET}")
        else:
            # colour-highlight the /qr command part
            if stripped.startswith("/qr"):
                parts = line.split(" ", 1)
                cmd_part  = f"{BOLD}{BRIGHT_GREEN}{parts[0]}{RESET}"
                rest_part = f"{GREEN}{parts[1] if len(parts) > 1 else ''}{RESET}"
                indent    = " " * (len(line) - len(line.lstrip()))
                out.append(f"      {indent}{cmd_part} {rest_part}")
            else:
                out.append(f"      {GREEN}{line}{RESET}")
    return "\n".join(out)


# -- Main ----------------------------------------------------------------------

def main():
    total = sum(len(g["examples"]) for g in GROUPS)

    print()
    print(hr("═", BRIGHT_CYAN))
    print(
        f"  {BOLD}{BRIGHT_CYAN}/qr{RESET}"
        f"  {BOLD}{WHITE}skill — example gallery{RESET}"
        f"  {DIM}({total} examples across {len(GROUPS)} categories){RESET}"
    )
    print(hr("═", BRIGHT_CYAN))
    print()

    for i, group in enumerate(GROUPS, 1):
        print(section_header(group["title"], i))
        if group["note"]:
            print(f"    {DIM}{ITALIC}{group['note']}{RESET}")
        print()

        is_heredoc = "HEREDOC" in group["title"]
        for label, cmd in group["examples"]:
            print(render_label(label))
            print(render_cmd(cmd, is_heredoc=is_heredoc))
            print()

        if i < len(GROUPS):
            print(hr())
            print()

    print(hr("═", BRIGHT_CYAN))
    print(
        f"  {DIM}Tip: any English colour name works — "
        f"\"royal blue\", \"burnt orange\", \"cream\", \"slate\" …{RESET}"
    )
    print(
        f"  {DIM}Hex also accepted: #0255c7, fff — "
        f"~30 000 names via colourmapper{RESET}"
    )
    print(hr("═", BRIGHT_CYAN))
    print()


if __name__ == "__main__":
    main()
