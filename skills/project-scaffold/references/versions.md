# Version Pins

All version pins used across the Dockerfile and postCreate.sh are listed here.
When bumping a version, update **both** this file and every place marked below.

| Variable               | Current value | Used in                                      |
| ---------------------- | ------------- | -------------------------------------------- |
| `PYTHON_VERSION`       | `3.12`        | Dockerfile `ARG`, `.python-version`          |
| `NODE_VERSION`         | `v23.3.0`     | Dockerfile `ARG`, postCreate.sh base-image   |
| `FNM_VERSION`          | `1.37.1`      | Dockerfile `ARG`                             |
| `GIT_DELTA_VERSION`    | `0.18.2`      | Dockerfile `ARG`, postCreate.sh base-image   |
| `ZSH_IN_DOCKER_VERSION`| `1.2.1`       | Dockerfile `ARG`, postCreate.sh base-image   |
| `CLAUDE_CODE_VERSION`  | `2.1.111`     | Dockerfile `ARG`, postCreate.sh base-image   |

## How to bump a version

1. Update the value in the table above.
2. Update the matching `ARG` line at the top of `.devcontainer/Dockerfile`.
3. If using base-image + postCreate mode, update the matching `export` line in `.devcontainer/scripts/postCreate.sh`.
4. Rebuild: `docker build --no-cache .devcontainer/ -t <project>-dev`
