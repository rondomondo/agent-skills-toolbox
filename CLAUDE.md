# Project

This CLAUDE.md applies to all projects and directories (including subdirectories) that contain this file,
unless a path is excluded by `.claudeignore`.

## Precedence

- Explicit instructions in the current chat override this file.
- "Scope" governs everything else: when a rule below says a project "must" have something, that applies
  when creating a project. In an existing project, flag anything missing in the final summary; do not add
  it unless asked.

## Context exclusions

If a `.claudeignore` file exists in the project root, it lists glob patterns for paths Claude must not read
or summarise (dependencies, build output, secrets, large data files). Treat it as authoritative.

`.claudeignore` is advisory: it works because this file asks for it, and it does not block tool reads.
Secrets must also be protected with `permissions.deny` read rules in `.claude/settings.json`.

## Memory

Project-level memories are stored under `~/.claude/projects/` and loaded automatically. Global preferences
and cross-project rules live in `~/.claude/`. When a task references prior decisions or past context,
check those memory files before asking the user to re-explain.

## Writing style

- ASCII only in source, comments, docs and commit messages. Data output may contain UTF-8 (see JSON below).
- Never use em dashes, en dashes, or `--` as a dash substitute. Use commas, colons, semicolons,
  parentheses, or separate sentences.
- British spelling: `realise` not `realize`, `colour` not `color`.
- Docstrings describe what a function does. Inline comments explain only why (hidden constraints,
  non-obvious invariants), never what.

## Code style

- `ruff` for linting and formatting, `line-length = 119`
- `mypy` with `strict = false` and `ignore_missing_imports = true`
- Python 3.12+ with full type annotations
- Import order: standard lib, third-party, local
- Naming: `snake_case` for functions and variables, `PascalCase` for classes
- Pydantic v2 for data validation and schemas
- FastAPI for HTTP endpoints
- `pathlib.Path` throughout; never raw string paths
- `copy.deepcopy` before mutating shared data structures
- All file I/O uses `encoding='utf-8'`; JSON output uses `ensure_ascii=False`
- Magic numbers are named constants (`ALL_CAPS`)

## Naming and public API

- Never prefix your own function, method, attribute, or variable names with `_` or `__`. Use descriptive
  names instead.
- Exempt: Python-defined dunders (`__init__`, `__repr__`, `__eq__`, `__name__`, `__all__`, `__init__.py`),
  framework-required names, and a bare `_` for unused values (`for _ in range(n)`).
- A module's public API is what it lists in `__all__`. Everything else is internal. Any module imported by
  other modules must define `__all__`; standalone scripts need not.
- "Public" elsewhere in this file means listed in `__all__`.

## Type hints

- All public function signatures have full type hints
- Modern syntax: `str | None`, `list[str]`, `dict[str, Any]`; never `Optional[str]` or `List[str]`
- Bare generics are not allowed in signatures: `dict[str, Any]`, not `dict`
- `from __future__ import annotations` is not used; import from `typing` only for constructs unavailable as
  builtins (e.g. `Any`, `Union` in complex cases)
- Buffer parameters are typed `BytesIO | bytes | str | Path` as appropriate, not `Optional[bytes]`

## Async

- Prefer `async`/`await` for I/O-bound work (network calls, file reads in hot paths)
- Use `httpx` (async-capable), not `requests`, for HTTP calls
- Async entry points use `asyncio.run(main())`; never call `asyncio.get_event_loop()` directly
- Synchronous CLI scripts that do minimal I/O are acceptable without async

## Logging

- Library and API code uses the `logging` module, never `print`, for diagnostics
- CLI scripts may use `print(..., file=sys.stderr)` for errors and warnings, and `print()` for output data
- Do not configure logging inside library modules; leave that to the caller or entry point
- Levels: `DEBUG` for trace and detail, `INFO` for progress, `WARNING` for recoverable issues, `ERROR` for
  failures

## Error handling

- Catch specific exceptions; never bare `except:`, and never `except Exception:` without re-raising or
  logging
- Validate inputs early; fail fast with a clear message before doing any work
- CLI scripts exit 0 on success and 1 on failure, via `sys.exit(1)`, not `raise SystemExit`
- Optional third-party dependencies are imported inside `try/except ImportError` with a fallback or a clear
  error message

## CLI scripts

- Use `argparse` with grouped arguments and sensible defaults. Use `typer` only if the project already
  depends on it.
- Validate all arguments in `main()` before any processing begins
- Scripts designed for pipeline composition read from stdin, write data to stdout, and send errors to stderr
- Entry point guard: `if __name__ == "__main__":` then `main()`, or `asyncio.run(main())` if `main` is async
- Helper functions called only from `main()` get plain names (`parse_args`, `run`, `load_config`)
- Always support `-h` as a short alias for `--help`. For `argparse`, keep `add_help=True` (the default) and
  set `formatter_class`. For `typer`, pass `context_settings={"help_option_names": ["-h", "--help"]}` to the
  `Typer()` constructor.

## Standalone scripts (uv shebang)

Scripts intended to run directly with `uv run` use the inline script metadata shebang:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "some-package>=1.0.0",
# ]
# ///
```

Always use this form for any script that carries its own dependency list. Never use a bare
`#!/usr/bin/env python3` shebang on such scripts.

## Section comments

Use plain section headings without decorator lines:

```python
# Section title
```

Not:

```python
# ---------------------------------------------------------------------------
# Section title
# ---------------------------------------------------------------------------
```

The dashes cause rendering problems in some editors and CI log viewers.

## Docstrings: Google style

All public functions have Google-style docstrings.

```python
def build_redirect_kwargs(url: str, overwrite: bool = False) -> dict[str, Any]:
    """Build put_object kwargs for a redirect object

    Optional longer description when intent is non-obvious.

    Args:
        url: the redirect destination URL.
        overwrite: when True, silently replace an existing key.

    Returns:
        A dict suitable for passing to put_object as extra kwargs.

    Raises:
        ValueError: If url uses an unsupported scheme.
    """
```

Rules:

- First line is a short imperative summary with no trailing period
- `Args:`, `Returns:`, `Raises:` sections only when present
- Parameter descriptions start lowercase
- Omit obvious sections (no `Returns:` on a `None`-returning function)

## Running tests

Use `pytest` exclusively. Run the full suite with:

```bash
uv run pytest
```

Test location and `pythonpath` are configured in `pyproject.toml`. Check that file for the canonical pytest
root and path configuration before adjusting test commands.

## Tests

- Write a test only when it would fail if the behaviour it protects broke. If you cannot name that failure,
  do not write it.
- New behaviour in the public API gets tests that meet the rule above. Boundary cases count when they are
  real inputs, not invented ones.
- Bug fix: one regression test that fails before the fix and passes after. Confirm the "fails before" part
  by running it.
- Do not test: getters and setters, type annotations, constructors that only assign fields, framework or
  stdlib behaviour, or internal (non-`__all__`) functions directly. Go through the public API.
- Do not mock what you own. Mock only network, clock, filesystem outside `tmp_path`, and other processes.
- No assertions that restate the implementation (e.g. asserting a mock was called with the exact args the
  code just passed).
- Prefer extending an existing parametrised test over adding a new test function.
- Never add tests purely to raise coverage. Coverage is a signal, not a target.
- If a test needs more setup than the code under test, say so and ask before writing it.

## Virtual environment

The project uses `uv` for dependency management and virtual environments:

```bash
uv sync
uv sync --extra dev   # include dev and test dependencies
```

Run a one-off command inside the project environment without activating it:

```bash
uv run <command>
```

Add or remove dependencies with `uv add` and `uv remove`; never edit `pyproject.toml` dependency lists by
hand. Do not use `pip`, `pip install`, `python -m venv`, or `virtualenv`.

## Git hooks

New projects get a `.githooks/` directory at the root with a `commit-msg` hook that enforces Conventional
Commits (https://www.conventionalcommits.org/en/v1.0.0/).

The hook must:

- Reject commits whose subject line does not match `<type>[optional scope]: <description>`
- Accept these types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`,
  `revert`
- Print a clear error message showing the expected format when it rejects a commit

Wire the hooks directory in the Makefile so `make install` (or equivalent setup target) runs:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/commit-msg
```

## README

New projects get a `README.md` at the top level describing the actual project, not a template or
placeholder. At minimum it covers:

- What the project does and why it exists
- How to install and run it locally (using `uv`)
- How to run the tests

When a change alters behaviour described in the README, update the README in the same commit.

## .gitignore

New projects get a `.gitignore` at the top level that excludes at minimum:

- `.venv/`
- `__pycache__/` and `*.pyc`
- `*.egg-info/`
- `dist/` and `build/`
- `.coverage` and `htmlcov/`
- `.env` and `*.local`
- `node_modules/` (if applicable)

## Makefiles

Before running any management or build command manually, check the root `Makefile` and, for skill-specific
work, `skills/<name>/Makefile`. Common tasks (installing skills, zipping, plugin generation) are already
captured there. Run `make help` for a summary of available targets.

When a task requires editing a Makefile, consolidate the targets you touch: shared values as variables at
the top, and merge or remove targets that duplicate the one you are changing. Flag other duplicate or unused
targets in the summary rather than removing them.

## Verification

- Before saying "done", run each of these separately, so one failure does not hide the others:

  ```bash
  uv run ruff check .
  uv run ruff format --check .
  uv run mypy .
  uv run pytest
  ```

  Report the actual output of each, not a summary of what you expect.
- If you did not run something, say so explicitly. Never claim "should work" or "tests pass" without having
  run them.
- For behaviour changes, exercise the real code path (run the CLI, hit the endpoint) at least once, not just
  unit tests.
- Re-read your own diff (`git diff`) before finishing. Remove debug prints, dead code, and unrelated edits.
- If a check fails, fix the cause. Do not skip, xfail, loosen assertions, or delete a test to get green.
- If you cannot verify something (needs credentials, hardware, prod), list it under "Unverified" in your
  final message.

## Scope

- Do what was asked. Surface adjacent problems in the summary; do not fix them unprompted.
- Do not add abstractions, config options, or error handling for cases that cannot happen.
- Final message: what changed, what was run and its result, what is unverified, and any flagged items.
  Nothing else.
