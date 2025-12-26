# Repository Guidelines

## Project Structure & Module Organization
- `src/farmer_cli/` is the main package. Key areas are `core/` (app lifecycle, database), `features/` (CLI feature modules), `services/` (business logic), `ui/` (Rich UI components), and `utils/` (shared helpers).
- `src/config/` holds default settings (`default_config.json`) and `settings.py`; `src/exceptions/` centralizes custom errors; `src/themes.py` defines theme presets.
- `data/` stores local artifacts such as `data/database/cli_app.db`; `preferences.json` is user preference state.
- `assets/` and `docs/` contain static assets and architecture/theming references (see `docs/ARCHITECTURE.md`).

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate`: create and activate a virtualenv.
- `pip install -r requirements-dev.txt`: install dev tooling (ruff, black, pytest, mypy, pyright).
- `pip install -e .`: editable install for the `farmer-cli` entrypoint.
- `farmer-cli` or `python -m farmer_cli`: run the CLI locally.
- `pytest`: run the test suite.

## Coding Style & Naming Conventions
- Python, 4-space indentation, line length 120 (see `pyproject.toml`).
- Format with `black .` and `isort .`; lint with `ruff check .` (ruff/black config in `pyproject.toml`).
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: pytest (see `requirements-dev.txt`).
- Add new tests under `tests/` using `test_*.py` and `test_*` function names.
- Optional coverage: `pytest --cov=farmer_cli` if you need a coverage report.

## Commit & Pull Request Guidelines
- Commit history favors `type: subject` messages (example: `refactor: restructure CLI application...`). Keep subjects short and imperative.
- PRs should include a concise description, testing notes, and linked issues when applicable.
- For UI/output changes, include a terminal screenshot or brief GIF.

## Configuration & Secrets
- Copy `env.example` to `.env` and set `OPENWEATHER_API_KEY` for weather features.
- Avoid committing personal secrets or local state changes unless the change is intended.
