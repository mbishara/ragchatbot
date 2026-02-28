# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Build the project
```bash
git pull --rebase
uv run build
```

### Run tests
```bash
git pull --rebase
uv test
```

### Lint the code
```bash
git pull --rebase
uv lint
```

### Run a single test
```bash
git pull --rebase
uv test path/to/test_file.py::TestClassName::test_method_name
```

## Code Architecture

The project appears to be a Python-based application. Here's a high-level overview of its structure:

- **src/**: Main source code directory.
  - **api/**: Contains API endpoints and related logic.
  - **models/**: Data models and schemas.
  - **services/**: Business logic services.
  - **utils/**: Utility functions and helpers.

- **tests/**: Unit tests for the codebase.

- **requirements.txt**: Lists project dependencies.

## Development Notes

1. Use `uv` to manage all dependencies instead of `pip`.
2. Ensure that you are using the correct virtual environment (`/home/mb/Desktop/AI/claudecode_course/code/starting-ragchatbot-codebase/.venv`).

For more detailed information, please refer to the `README.md` file in the root directory.