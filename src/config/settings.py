"""
Settings module for Farmer CLI application.

This module handles configuration management using pydantic for validation
and python-dotenv for environment variable loading.
"""

from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings


# Load environment variables from .env file
load_dotenv()

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "src" / "config"


class Settings(BaseSettings):
    """Application settings with validation."""

    # Application info
    app_name: str = Field(default="Farmer CLI", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")

    # API Keys
    openweather_api_key: Optional[str] = Field(
        default=None, env="OPENWEATHER_API_KEY", description="OpenWeatherMap API key"
    )  # type: ignore

    # Database settings
    database_dir: Path = Field(default=DATA_DIR / "database", description="Database directory")
    database_file: str = Field(default="cli_app.db", description="Database filename")

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Path = Field(default=LOGS_DIR / "cli_app.log", description="Log file path")
    log_retention_days: int = Field(default=7, description="Log retention in days")

    # UI settings
    default_theme: str = Field(default="default", description="Default UI theme")
    terminal_width: int = Field(default=80, description="Default terminal width")

    # Performance settings
    ui_responsiveness_ms: int = Field(default=100, description="UI responsiveness target in ms")
    progress_refresh_rate: int = Field(default=10, description="Progress bar refresh rate")

    model_config = {"env_file": PROJECT_ROOT / ".env", "env_file_encoding": "utf-8", "case_sensitive": False}

    @field_validator("database_dir", "log_file", mode="before")
    @classmethod
    def ensure_path(cls, v: Any) -> Path:
        """Ensure paths are Path objects and create directories if needed."""
        if isinstance(v, str):
            v = Path(v)
        if isinstance(v, Path):
            if v.suffix:  # It's a file
                v.parent.mkdir(parents=True, exist_ok=True)
            else:  # It's a directory
                v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def database_path(self) -> Path:
        """Get full database path."""
        return self.database_dir / self.database_file

    def get_theme_config(self) -> Dict[str, Any]:
        """Get theme configuration."""
        from ..themes import THEMES

        return THEMES.get(self.default_theme, THEMES["default"])


# Create a singleton instance
settings = Settings()

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
settings.database_dir.mkdir(parents=True, exist_ok=True)
