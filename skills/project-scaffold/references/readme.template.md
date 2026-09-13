# README.md Template

```markdown
# <PROJECT_NAME>

<!-- github badges here -->

## Getting Started

### Prerequisites
- [VS Code](https://code.visualstudio.com/) with the Dev Containers extension
- Docker Desktop

### Quick Start

1. Open in VS Code -> click **Reopen in Container** when prompted
2. Activate the virtual environment: `source .venv/bin/activate`
3. Run `make install` to install dependencies
4. Run `make test` to verify everything works

## Available Commands

Run `make help` to see all available commands.

## GitHub SSH

If you need to access private GitHub repos from inside the container:

```bash
make github-check
```
```
