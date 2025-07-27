# Terminal Commands

## Terminal Commands Execution

### Command: `uv init --no-package --python 3.12 --app --author-from auto --no-cache`

**Description:** Initializes a new project named `chekibot_api` with Python 3.12, without a package, using the current user as the author, and without using the cache.

### Command: `uv sync`

**Description:** Synchronizes the project dependencies, creates a virtual environment, and installs the required packages.

### Command: `uv add fastapi[all] langchain`

**Description:** Adds the `fastapi` and `langchain` packages to the project, including all optional features for FastAPI. The `uv add` command is used to add dependencies to the project. All project dependencies and configuration are located in the `pyproject.toml` file

### Command: `mkdir -p src/{core,api,agent}`

**Description:** Creates the directory structure for the project, including the `core`, `api`, and `agent` modules under the `src` directory.
