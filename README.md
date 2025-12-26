# Farmer CLI

A modular CLI application with Rich UI for video downloading and system management.

## Features

- Beautiful terminal UI with Rich library
- Video downloading with yt-dlp integration
- User management system
- Interactive menus with keyboard shortcuts
- Multiple themes (default, dark, light, high contrast)
- Progress tracking and system monitoring
- Fuzzy search capabilities
- Export functionality (CSV, PDF)
- Weather checking integration
- File browser

## Installation

Requires Python 3.10+.

### From Source (uv recommended)

```bash
git clone https://github.com/deadcoast/farmer-cli.git
cd farmer-cli
uv sync
uv run farmer-cli
```

### Using pip

```bash
pip install farmer-cli
```

## Usage

Run the application:

```bash
farmer-cli
```

If you're using uv without installing the entrypoint, run:

```bash
uv run farmer-cli
```

### Keyboard Shortcuts

- `Ctrl+C`: Exit application
- `Ctrl+S`: Search menu
- `Ctrl+H`: Display help

### Menu Options

1. **Data Processing**: Advanced data processing and analysis tools
2. **User Management**: Manage users, preferences, and system configuration
3. **Configuration**: Customize themes, layouts, and display options
4. **System Tools**: File browser, weather checking, and monitoring

## Configuration

The application uses environment variables for sensitive data. Create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your API keys
```

### Required Environment Variables

- `OPENWEATHER_API_KEY`: For weather functionality

## Development

### Setup Development Environment

```bash
uv sync --extra dev
```

If you prefer pip:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements-dev.txt
pip install -e .
```

### Running Tests

```bash
uv run pytest
```

If you're using a pip/venv setup, run `pytest` directly.

### Code Style

This project uses:

- Ruff for formatting and linting
- isort for import sorting
- Black (optional, if you prefer black formatting)
- mypy and pyright for type checking

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
