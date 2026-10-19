import os
import shlex
import shutil
import socket
import subprocess
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

WRAPPER = Path(__file__).resolve().parent.parent / "vhs-rec"
BASH = "/bin/bash" if Path("/bin/bash").exists() else "bash"
SOCKET_PARENT = "/tmp"

# The fake docker copies the tape it is asked to render and creates the requested output file, which is all the
# wrapper checks, so no container is needed.
FAKE_DOCKER = """#!/bin/bash
prev=""
for arg in "$@"; do
  case "$arg" in
    *.tape) cp "$arg" "$CAPTURE_TAPE" ;;
  esac
  if [ "$prev" = "-o" ]; then
    : > "$arg"
  fi
  prev="$arg"
done
exit 0
"""


@dataclass
class Result:
    """Outcome of one wrapper invocation."""

    proc: subprocess.CompletedProcess[str]
    cwd: Path
    capture: Path

    @property
    def tape(self) -> str:
        """Return the tape text that vhs would have been asked to render."""
        return self.capture.read_text(encoding="utf-8")


@pytest.fixture
def sock_home() -> Iterator[Path]:
    """Provide a HOME containing a unix socket, since the wrapper refuses to start without a docker socket."""
    home = Path(tempfile.mkdtemp(dir=SOCKET_PARENT))
    sock_path = home / ".docker" / "run" / "docker.sock"
    sock_path.parent.mkdir(parents=True)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
    yield home
    server.close()
    shutil.rmtree(home, ignore_errors=True)


@pytest.fixture
def run_wrapper(tmp_path: Path, sock_home: Path):
    """Return a callable that runs the wrapper in a scratch directory with a fake docker on PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "docker"
    fake.write_text(FAKE_DOCKER, encoding="utf-8")
    fake.chmod(0o755)
    work = tmp_path / "work"
    work.mkdir()
    capture = tmp_path / "captured.tape"

    def run(*args: str) -> Result:
        env = {
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "HOME": str(sock_home),
            "CAPTURE_TAPE": str(capture),
        }
        proc = subprocess.run(
            [BASH, str(WRAPPER), *args], check=False, cwd=work, env=env, capture_output=True, text=True
        )
        return Result(proc, work, capture)

    return run


def test_one_shot_writes_output_and_commands_in_order(run_wrapper) -> None:
    result = run_wrapper("-x", "echo one", "-x", "echo two")
    assert result.proc.returncode == 0, result.proc.stderr
    assert (result.cwd / "demo.gif").exists()
    tape = result.tape
    assert tape.startswith("Output demo.gif\n")
    assert tape.index("Type 'echo one'") < tape.index("Type 'echo two'")
    assert 'Set Theme "Catppuccin Mocha"' in tape
    assert "Wait+Screen" not in tape


def test_one_shot_starts_in_host_directory_off_screen(run_wrapper) -> None:
    tape = run_wrapper("-x", "ls").tape
    hide, show = tape.index("Hide"), tape.index("Show")
    assert hide < tape.index('cd "$HOST_PWD"') < show < tape.index("Type 'ls'")


def test_with_installs_tool_off_screen_and_waits(run_wrapper) -> None:
    result = run_wrapper("--with", "pdf-strip", "-x", "pdf-strip --check a.pdf")
    tape = result.tape
    assert "docker run --rm ghcr.io/rondomondo/pdf-strip install | sh" in tape
    assert tape.index("Hide") < tape.index("pdf-strip install") < tape.index("Wait+Screen") < tape.index("Show")
    assert tape.index("Show") < tape.index("Type 'pdf-strip --check a.pdf'")


def test_setup_command_is_hidden(run_wrapper) -> None:
    tape = run_wrapper("-s", "export FOO=1", "-x", "echo $FOO").tape
    assert tape.index("Hide") < tape.index("export FOO=1") < tape.index("Show") < tape.index("echo $FOO")


def test_options_are_applied(run_wrapper) -> None:
    result = run_wrapper(
        "-x", "ls", "-o", "out/rec.gif", "--theme", "Dracula", "--width", "800", "--height", "400", "--wait", "1.5"
    )
    assert result.proc.returncode == 0, result.proc.stderr
    assert (result.cwd / "out" / "rec.gif").exists()
    tape = result.tape
    assert "Output out/rec.gif" in tape
    assert 'Set Theme "Dracula"' in tape
    assert "Set Width 800" in tape
    assert "Set Height 400" in tape
    assert "Sleep 1.5s" in tape


def test_quote_style_avoids_quotes_in_command(run_wrapper) -> None:
    tape = run_wrapper("-x", "echo 'hi'", "-x", "echo \"a\" 'b'").tape
    assert "Type \"echo 'hi'\"" in tape
    assert "Type `echo \"a\" 'b'`" in tape


def test_command_with_all_quote_styles_is_rejected(run_wrapper) -> None:
    result = run_wrapper("-x", "echo ' \" `")
    assert result.proc.returncode == 1
    assert "cannot quote" in result.proc.stderr


def test_newline_in_command_is_rejected(run_wrapper) -> None:
    result = run_wrapper("-x", "echo a\necho b")
    assert result.proc.returncode == 1
    assert "cannot quote" in result.proc.stderr


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["-o", "x.gif"], "needs a command"),
        (["-x", "ls", "--width", "wide"], "whole numbers"),
        (["-x", "ls", "--height", "-5"], "whole numbers"),
        (["-x", "ls", "--wait", "soon"], "seconds"),
        (["-x", "ls", "--with", "../evil"], "tool name"),
        (["-x", "ls", "--theme", 'a"b'], "double quotes"),
        (["-x", "ls", "--output", ""], "must not be empty"),
        (["-x"], "requires a value"),
        (["-x", "ls", "--env", "NOEQUALS"], "KEY=VALUE"),
        (["-x", "ls", "--env", "1BAD=x"], "KEY=VALUE"),
        (["-x", "ls", "--install", "Bad Name"], "tool name"),
        (["-x", "ls", "--install", "x/$(evil)"], "tool name"),
        (["-x", "ls", "--timeout", "soon"], "whole number"),
        (["demo", "-o", "x.gif"], "needs a command"),
        (["-x", "ls", "stray.tape"], "unexpected argument"),
    ],
)
def test_validation_errors_exit_one_with_message(run_wrapper, args: list[str], message: str) -> None:
    result = run_wrapper(*args)
    assert result.proc.returncode == 1
    assert message in result.proc.stderr
    assert not (result.cwd / "demo.gif").exists()


def test_demo_quotes_arguments_and_runs_follow_ups_after(run_wrapper) -> None:
    result = run_wrapper(
        "demo", "--then", "ls -l pdfs", "--env", "LOG_LEVEL=ERROR", "--install", "ghcr.io/acme/tool", "--",
        "tool", "--title", "two words", "it's", "https://example.com/a?b=1",
    )  # fmt: skip
    assert result.proc.returncode == 0, result.proc.stderr
    tape = result.tape
    assert "Type \"tool --title 'two words' 'it'\\''s' 'https://example.com/a?b=1'\"" in tape
    assert tape.index('Type "tool') < tape.index("Type 'ls -l pdfs'")
    assert "export LOG_LEVEL=ERROR" in tape
    assert "docker run --rm ghcr.io/acme/tool install | sh" in tape
    assert tape.count("Wait+Line") == 2


def test_snippet_command_reproduces_the_same_recording(run_wrapper) -> None:
    first = run_wrapper(
        "demo", "-o", "docs/a.gif", "--install", "pdf-strip", "--then", "ls -l", "--keep-tape", "--snippet", "--",
        "pdf-strip", "--check", "my file.pdf",
    )  # fmt: skip
    assert first.proc.returncode == 0, first.proc.stderr
    assert first.proc.stdout.startswith("![a demo](docs/a.gif)\n")
    block = first.proc.stdout.split("```bash\n")[1].split("\n```")[0]
    assert "--snippet" not in block
    assert "--keep-tape" not in block
    words = shlex.split(block.replace("\\\n", " "))
    assert words[0] == "vhs-rec"
    second = run_wrapper(*words[1:])
    assert second.proc.returncode == 0, second.proc.stderr
    assert second.tape == first.tape


def test_progress_goes_to_stderr_so_stdout_is_only_the_snippet(run_wrapper) -> None:
    result = run_wrapper("-x", "ls", "--snippet")
    assert "Wrote demo.gif" in result.proc.stderr
    assert "Wrote" not in result.proc.stdout


def test_temp_tape_is_removed_after_run(run_wrapper) -> None:
    result = run_wrapper("-x", "ls")
    assert result.proc.returncode == 0
    assert sorted(p.name for p in result.cwd.iterdir()) == ["demo.gif"]


def test_temp_tape_is_removed_after_failure(run_wrapper) -> None:
    result = run_wrapper("-x", "echo ' \" `")
    assert result.proc.returncode == 1
    assert list(result.cwd.iterdir()) == []


def test_keep_tape_saves_next_to_output(run_wrapper) -> None:
    result = run_wrapper("-x", "ls", "-o", "rec.gif", "--keep-tape")
    assert result.proc.returncode == 0, result.proc.stderr
    kept = result.cwd / "rec.tape"
    assert kept.read_text(encoding="utf-8") == result.tape


def test_keep_tape_refuses_to_overwrite(run_wrapper) -> None:
    first = run_wrapper("-x", "ls", "--keep-tape")
    assert first.proc.returncode == 0
    (first.cwd / "demo.gif").unlink()
    second = run_wrapper("-x", "pwd", "--keep-tape")
    assert second.proc.returncode == 1
    assert "already exists" in second.proc.stderr
    assert "Type 'ls'" in (first.cwd / "demo.tape").read_text(encoding="utf-8")


def test_existing_tape_mode_still_rewrites_output_line(run_wrapper, tmp_path: Path) -> None:
    work = tmp_path / "work"
    (work / "in.tape").write_text("Output old.gif\nType 'x'\n", encoding="utf-8")
    result = run_wrapper("in.tape", "new.gif")
    assert result.proc.returncode == 0, result.proc.stderr
    assert result.tape.startswith("Output new.gif\n")
    assert (work / "new.gif").exists()


def test_help_documents_one_shot_flags(run_wrapper) -> None:
    result = run_wrapper("-h")
    assert result.proc.returncode == 0
    for flag in ("--exec", "--setup", "--with", "--output", "--keep-tape"):
        assert flag in result.proc.stdout
