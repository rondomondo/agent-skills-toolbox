# Common Reference

## Makefile Template

See [`references/makefile.template.md`](makefile.template.md) for the full Makefile.

Key points:
- `.DEFAULT_GOAL := help` -- `make help` is always first and default
- `.PHONY` declared for all non-file targets
- `##` comments after each target are parsed by the help formatter
- Guards: `check-sys-deps` and `check-venv` must be called before install/build targets
- Include `github-check` target only if the user provides an SSH key

---

## .gitignore Template

See [`references/gitignore.template.md`](gitignore.template.md) for the full `.gitignore`.

Covers: secrets/credentials, OS/editor files, Python venv, build output, test caches, logs, Claude caches.

---

## pyproject.toml Template

See [`references/pyproject.template.toml`](pyproject.template.toml) for the full `pyproject.toml`.

Replace all `<PLACEHOLDER>` values with project-specific values. Uses `setuptools` as the build backend.

---

## README.md Template

See [`references/readme.template.md`](readme.template.md) for the full `README.md`.

Replace `<PROJECT_NAME>` and remove the GitHub SSH section if no SSH key was configured.

---

## .githooks/commit-msg

See [`references/commit-msg.template.sh`](commit-msg.template.sh) for the full hook script.

Copy verbatim to `.githooks/commit-msg` and make executable (`chmod +x .githooks/commit-msg`).

---

## .devcontainer/scripts/postStartCommand.sh

```bash
# <PROJECT_NAME> - postStartCommand
echo "Add any postStartCommand dependencies here"
```

---

## Version Pins

See [`references/versions.md`](versions.md) for all pinned versions (Python, Node, Claude Code, etc.)
and instructions on how to bump them consistently across Dockerfile and postCreate.sh.
