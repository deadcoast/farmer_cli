---
description: Python best practices and patterns for Farmer CLI
globs: src/**/*.py,tests/**/*.py,setup.py
alwaysApply: false
---
# Repository Guidelines

## Python Best Practices

### Project Structure

- Use src-layout with `src/farmer_cli/`
- Place tests in `tests/` (add when tests are introduced)
- Keep configuration in `src/config/` and via environment variables
- Use `pyproject.toml` for package metadata and dependencies; uv uses `uv.toml` + `uv.lock`
- Place static files in `assets/`
- Use `data/` for local application data (database, exports, logs)

## Code Style

- Prefer `ruff format .` for formatting
- Use `ruff check .` for linting and `isort .` for import sorting
- Follow PEP 8 naming conventions:
  - snake_case for functions and variables
  - PascalCase for classes
  - UPPER_CASE for constants
- Maximum line length of 120 characters
- Use relative imports for internal package modules (e.g., `from ..config.settings import Settings`)

## Type Hints

- Use type hints for all function parameters and returns
- Use `Type | None` for optionals (Python >=3.10)
- Use `TypeVar` for generic types
- Define custom types in `types.py` or within the module
- Use `Protocol` for duck typing

## Error Handling

- Create custom exception classes in `exceptions/` directory
- Use proper try-except blocks
- Implement proper logging
- Return proper error responses
- Handle edge cases properly
- Use proper error messages
- Map external library errors to custom exceptions

## Documentation

- Use Numpy-style docstrings (ruff pydocstyle)
- Keep README.md updated
- Use proper inline comments
- Document environment setup
- Include project architecture documentation in `docs/`

## Development Workflow

- Use uv-managed virtual environments (`.venv`)
- Use proper Git workflow
- Implement proper logging
- Use pytest for testing
- Use coverage reporting

## Dependencies

- Use `pyproject.toml` as the source of truth for dependencies/metadata
- Keep `requirements*.txt` in sync for compatibility with pip workflows
- Keep `uv.toml` minimal and `uv.lock` checked in for repeatable installs
- Optional dependencies live in `[project.optional-dependencies]`

## Application-Specific Patterns

- Use Rich + prompt_toolkit for terminal UI components
- Use Pydantic settings for configuration and validation
- Use SQLAlchemy for database access and pathlib for file operations
- Implement proper progress tracking for long-running operations

## Project Structure & Module Organization
- `src/farmer_cli/` is the main package. Key areas are `core/` (app lifecycle, database), `features/` (CLI feature modules), `services/` (business logic), `ui/` (Rich UI components), and `utils/` (shared helpers).
- `src/config/` holds default settings (`default_config.json`) and `settings.py`; `src/exceptions/` centralizes custom errors; `src/themes.py` defines theme presets.
- `data/` stores local artifacts such as `data/database/cli_app.db`; `preferences.json` is user preference state.
- `assets/` and `docs/` contain static assets and architecture/theming references (see `docs/ARCHITECTURE.md`).

## Build, Test, and Development Commands
- `uv sync --extra dev`: install runtime + dev dependencies into `.venv`.
- `uv run farmer-cli` or `uv run python -m farmer_cli`: run the CLI locally.
- `uv run pytest`: run the test suite.

## Coding Style & Naming Conventions
- Python, 4-space indentation, line length 120 (see `pyproject.toml`).
- Format with `ruff format .`; lint with `ruff check .`; sort imports with `isort .`.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: pytest (see `requirements-test.txt`).
- Add new tests under `tests/` using `test_*.py` and `test_*` function names.
- Optional coverage: `pytest --cov=farmer_cli`.

## Commit & Pull Request Guidelines
- Commit history favors `type: subject` messages (example: `refactor: restructure CLI application...`). Keep subjects short and imperative.
- PRs should include a concise description, testing notes, and linked issues when applicable.
- For UI/output changes, include a terminal screenshot or brief GIF.

## Configuration & Secrets
- Copy `.env.example` to `.env` and set `OPENWEATHER_API_KEY` for weather features.
- Avoid committing personal secrets or local state changes unless the change is intended.
