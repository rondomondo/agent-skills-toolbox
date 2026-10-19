import shlex
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "vhs-demo.py"


def run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    """Run vhs-demo and capture its output."""
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=False, capture_output=True, text=True)


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        (
            ["url2pdf", "https://en.wikipedia.org/wiki/Special:Random"],
            (
                "vhs-rec demo -o docs/url2pdf.gif --install screenshot --snippet -- "
                "url2pdf https://en.wikipedia.org/wiki/Special:Random"
            ),
        ),
        (["pdf-strip", "--check", "a.pdf"], "vhs-rec demo -o docs/pdf-strip.gif --install pdf-strip --snippet -- "),
        (["git", "log", "--oneline", "-5"], "vhs-rec demo -o docs/git-log.gif --snippet -- git log --oneline -5"),
        (["docker", "ps", "--help"], "vhs-rec demo -o docs/docker-ps-help.gif --snippet -- docker ps --help"),
        (["git", "-h"], "vhs-rec demo -o docs/git-help.gif --snippet -- git -h"),
    ],
)
def test_single_command_line(command: list[str], expected: str) -> None:
    result = run_demo(*command)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(expected)
    assert result.stdout.count("\n") == 1


def test_command_flags_are_not_taken_as_vhs_demo_flags() -> None:
    result = run_demo("url2pdf", "https://example.com", "--paper-format", "Letter", "--help")
    assert result.returncode == 0, result.stderr
    assert shlex.split(result.stdout)[-5:] == ["url2pdf", "https://example.com", "--paper-format", "Letter", "--help"]


def test_arguments_with_spaces_and_quotes_survive_a_shell() -> None:
    words = ["git", "commit", "-m", 'it\'s a "test" & more']
    line = shlex.split(run_demo(*words).stdout)
    assert line[line.index("--") + 1 :] == words


def test_options_and_head() -> None:
    result = run_demo("-d", "img", "--install", "ghcr.io/me/tool", "--env", "A=1", "--head", "5", "tool", "--help")
    assert result.stdout.strip() == (
        "vhs-rec demo -o img/tool-help.gif --install ghcr.io/me/tool --env A=1 --snippet -x 'tool --help | head -n 5'"
    )


def test_catalog_has_one_runnable_line_per_tool() -> None:
    result = run_demo("--catalog")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert len(lines) >= 12
    for line in lines:
        words = shlex.split(line)
        assert words[:2] == ["vhs-rec", "demo"]
        assert "--snippet" in words
    outputs = [shlex.split(line)[3] for line in lines]
    assert "docs/url2pdf-help.gif" in outputs
    assert "docs/regctl-help.gif" in outputs


@pytest.mark.parametrize(
    "args",
    [[], ["--catalog", "ls"], ["--head", "0", "ls"]],
)
def test_bad_usage_fails_with_message(args: list[str]) -> None:
    result = run_demo(*args)
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith("vhs-demo:")


def test_unknown_tool_warns_but_still_prints() -> None:
    result = run_demo("url2pfd", "https://example.com")
    assert result.returncode == 0
    assert "not a known toolbox tool" in result.stderr
    assert result.stdout.startswith("vhs-rec demo -o docs/url2pfd.gif --snippet")
