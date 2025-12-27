# Farmer CLI

A modular CLI application with Rich UI for video downloading and system management.

## Features

- Beautiful terminal UI with Rich library
- Video downloading with yt-dlp integration
  - Download from YouTube, Vimeo, and 1000+ supported sites
  - Format and quality selection
  - Playlist and batch downloads
  - Download queue management
  - Download history tracking
- User management system
- Interactive menus with keyboard shortcuts
- Multiple themes (default, dark, light, high contrast)
- Progress tracking and system monitoring
- Fuzzy search capabilities
- Export functionality (CSV, JSON, PDF)
- Weather checking integration
- File browser
- Command-line interface for scripting

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

### Interactive Mode

Run the application in interactive mode:

```bash
farmer-cli
```

If you're using uv without installing the entrypoint, run:

```bash
uv run farmer-cli
```

### Command-Line Interface

Farmer CLI supports direct command-line usage for scripting and automation:

```bash
# Download a video
farmer-cli download "https://www.youtube.com/watch?v=VIDEO_ID"

# Download with specific format
farmer-cli download "URL" --format 720p

# Download to a specific location
farmer-cli download "URL" --output ~/Videos

# Quiet mode for scripts
farmer-cli download "URL" --quiet

# Show version
farmer-cli --version

# Show help
farmer-cli --help
```

#### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--format` | `-f` | Video format (e.g., best, 1080p, 720p, 480p, audio) |
| `--output` | `-o` | Output directory path |
| `--quiet` | `-q` | Minimal output for scripts |
| `--version` | | Show version and exit |
| `--help` | | Show help and exit |

### Keyboard Shortcuts

- `Ctrl+C`: Exit application
- `Ctrl+S`: Search menu
- `Ctrl+H`: Display help

### Menu Options

1. **Video Downloader**: Download videos from various platforms
   - Download single videos with format selection
   - Download entire playlists or ranges
   - Manage download queue (pause, resume, cancel, reorder)
   - View and search download history
   - Configure download settings
2. **Data Processing**: Advanced data processing and analysis tools
3. **User Management**: Manage users, preferences, and system configuration
4. **Configuration**: Customize themes, layouts, and display options
5. **System Tools**: File browser, weather checking, log viewer, and monitoring

## Video Downloading

### Supported Platforms

Farmer CLI uses yt-dlp under the hood, supporting 1000+ sites including:

- YouTube (videos and playlists)
- Vimeo
- Twitter/X
- TikTok
- And many more...

### Download Queue

The download queue allows you to:

- Add multiple videos for sequential downloading
- Set maximum concurrent downloads (1-5)
- Pause and resume downloads
- Reorder queue items
- Queue persists across application restarts

### Download History

Track all your downloads with:

- Search and filter by title
- View file existence status
- Detect and warn about duplicates
- Export history to CSV, JSON, or PDF

### Output Configuration

Customize your downloads:

- Set default download directory
- Configure filename templates with variables (title, uploader, date, etc.)
- Organize downloads into subdirectories by channel/playlist
- Handle filename conflicts (rename, overwrite, skip)

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
