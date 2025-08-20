# Farmer CLI

A powerful CLI application with Rich UI for video downloading and media management.

## Features

- 🎨 Beautiful terminal UI with Rich library
- 🎬 Video downloading with yt-dlp integration
- 👥 User management system
- 🎯 Interactive menus with keyboard shortcuts
- 🌈 Multiple themes (default, dark, light, high contrast)
- 📊 Progress tracking and system monitoring
- 🔍 Fuzzy search capabilities
- 📄 Export functionality (CSV, PDF)
- 🌤️ Weather checking integration
- 📁 File browser

## Installation

### From Source

```bash
git clone https://github.com/yourusername/farmer-cli.git
cd farmer-cli
pip install -e .
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
cp env.example .env
# Edit .env with your API keys
```

### Required Environment Variables

- `OPENWEATHER_API_KEY`: For weather functionality

## Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .
```

### Running Tests

```bash
pytest
```

### Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
