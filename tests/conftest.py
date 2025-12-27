"""
Shared pytest fixtures for Farmer CLI tests.

This module provides common fixtures for database, temp files, and mock services
used across unit, property, and integration tests.
"""

import gc
import json
import os
import sys
from pathlib import Path
from typing import Any
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Database Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database path."""
    return tmp_path / "test_cli_app.db"


@pytest.fixture
def db_engine(temp_db_path: Path):
    """Create a temporary SQLite database engine."""
    engine = create_engine(
        f"sqlite:///{temp_db_path}",
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    try:
        yield engine
    finally:
        # Explicitly close all connections before dispose
        engine.dispose(close=True)


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Provide a database session with automatic cleanup."""
    from farmer_cli.models.base import Base

    # Import all models to ensure they are registered
    from farmer_cli.models import DownloadHistory  # noqa: F401
    from farmer_cli.models import QueueItem  # noqa: F401
    from farmer_cli.models import User  # noqa: F401

    # Create all tables
    Base.metadata.create_all(db_engine)

    # Use scoped_session for proper cleanup
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    ScopedSession = scoped_session(session_factory)
    session = ScopedSession()

    try:
        yield session
    finally:
        session.rollback()
        session.expunge_all()
        ScopedSession.remove()  # Properly remove scoped session
        gc.collect()  # Force garbage collection to close any lingering connections


@pytest.fixture
def database_manager(temp_db_path: Path):
    """Provide a DatabaseManager instance with a temporary database."""
    from farmer_cli.core.database import DatabaseManager

    manager = DatabaseManager(database_path=temp_db_path)
    manager.initialize()
    yield manager
    manager.close()


# ---------------------------------------------------------------------------
# Temporary File Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def temp_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary file path."""
    file_path = tmp_path / "test_file.txt"
    yield file_path
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def temp_json_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary JSON file path."""
    file_path = tmp_path / "test_data.json"
    yield file_path
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def temp_preferences_file(tmp_path: Path) -> Path:
    """Provide a temporary preferences file path."""
    return tmp_path / "preferences.json"


# ---------------------------------------------------------------------------
# Service Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def preferences_service(temp_preferences_file: Path):
    """Provide a PreferencesService instance with a temporary file."""
    from farmer_cli.services.preferences import PreferencesService

    return PreferencesService(preferences_file=temp_preferences_file)


# ---------------------------------------------------------------------------
# Sample Data Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Provide sample user data for testing."""
    return {
        "name": "Test User",
        "preferences": json.dumps({"theme": "dark", "notifications": True}),
    }


@pytest.fixture
def sample_preferences() -> dict[str, Any]:
    """Provide sample preferences data for testing."""
    return {
        "theme": "dark",
        "first_run": False,
        "check_updates": True,
        "show_tips": True,
        "export_format": "json",
        "last_directory": "/tmp",
    }


@pytest.fixture
def sample_video_info() -> dict[str, Any]:
    """Provide sample video information for testing."""
    return {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Test Video Title",
        "uploader": "Test Channel",
        "duration": 212,
        "upload_date": "20230101",
        "id": "dQw4w9WgXcQ",
        "ext": "mp4",
    }


@pytest.fixture
def sample_playlist_info() -> dict[str, Any]:
    """Provide sample playlist information for testing."""
    return {
        "url": "https://www.youtube.com/playlist?list=PLtest123",
        "title": "Test Playlist",
        "uploader": "Test Channel",
        "playlist_count": 5,
    }


# ---------------------------------------------------------------------------
# URL Test Data Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_youtube_urls() -> list[str]:
    """Provide valid YouTube URLs for testing."""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/v/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
    ]


@pytest.fixture
def valid_vimeo_urls() -> list[str]:
    """Provide valid Vimeo URLs for testing."""
    return [
        "https://vimeo.com/123456789",
        "https://www.vimeo.com/123456789",
        "https://player.vimeo.com/video/123456789",
    ]


@pytest.fixture
def invalid_urls() -> list[str]:
    """Provide invalid URLs for testing."""
    return [
        "",
        "not-a-url",
        "http://",
        "ftp://example.com/video",
        "javascript:alert('xss')",
        "file:///etc/passwd",
    ]


# ---------------------------------------------------------------------------
# Filename Template Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def filename_template_variables() -> dict[str, str]:
    """Provide sample variables for filename template testing."""
    return {
        "title": "Test Video Title",
        "uploader": "Test Channel",
        "upload_date": "20230101",
        "id": "abc123",
        "ext": "mp4",
        "playlist": "Test Playlist",
        "playlist_index": "01",
    }


# ---------------------------------------------------------------------------
# Environment Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def clean_env():
    """Provide a clean environment without test-affecting variables."""
    original_env = os.environ.copy()
    # Remove any variables that might affect tests
    for key in list(os.environ.keys()):
        if key.startswith("FARMER_"):
            del os.environ[key]
    yield
    os.environ.clear()
    os.environ.update(original_env)
