# Design Document: Farmer CLI Completion

## Overview

This design document outlines the architecture and implementation approach for completing the Farmer CLI application. The primary focus is implementing the missing video downloading functionality using yt-dlp, enhancing existing features, and establishing comprehensive test coverage.

The design follows the existing modular architecture with clear separation between core logic, features, services, UI components, and utilities.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface                             │
│  (Click-based argument parsing + Interactive Rich UI)            │
├─────────────────────────────────────────────────────────────────┤
│                      Feature Layer                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │   Video      │ │    User      │ │   System     │             │
│  │  Downloader  │ │  Management  │ │    Tools     │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                      Service Layer                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │  Download    │ │  Preferences │ │   Export     │             │
│  │   Manager    │ │   Service    │ │   Service    │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                       Core Layer                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │   Database   │ │    Config    │ │   Logging    │             │
│  │   Manager    │ │   Settings   │ │   System     │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Module Organization

```
src/farmer_cli/
├── __init__.py
├── __main__.py              # Entry point with CLI argument handling
├── cli.py                   # NEW: Click-based CLI interface
├── core/
│   ├── app.py               # Main application coordinator
│   ├── constants.py         # Application constants
│   ├── database.py          # Database management
│   └── logging_config.py    # NEW: Logging configuration
├── models/
│   ├── base.py              # SQLAlchemy base
│   ├── user.py              # User model
│   ├── download.py          # NEW: Download/Queue models
│   └── history.py           # NEW: Download history model
├── features/
│   ├── base.py              # Base feature class
│   ├── video_downloader.py  # NEW: Video download feature
│   ├── user_manager.py      # Enhanced user management
│   ├── configuration.py     # Configuration feature
│   └── system_tools.py      # System tools feature
├── services/
│   ├── download_manager.py  # NEW: Download queue/history management
│   ├── format_selector.py   # NEW: Format selection service
│   ├── playlist_handler.py  # NEW: Playlist processing
│   ├── preferences.py       # Enhanced preferences service
│   ├── export.py            # Enhanced export service
│   └── ytdlp_wrapper.py     # NEW: yt-dlp integration wrapper
├── ui/
│   ├── console.py           # Rich console setup
│   ├── menu.py              # Menu system
│   ├── widgets.py           # UI widgets
│   ├── prompts.py           # Input prompts
│   └── download_ui.py       # NEW: Download progress UI
└── utils/
    ├── validators.py        # Input validators
    ├── filename_template.py # NEW: Filename templating
    └── url_utils.py         # NEW: URL validation utilities
```

## Components and Interfaces

### 1. CLI Interface (cli.py)

```python
import click
from typing import Optional

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output')
@click.pass_context
def cli(ctx: click.Context, version: bool, quiet: bool) -> None:
    """Farmer CLI - Video downloading and system management."""
    pass

@cli.command()
@click.argument('url')
@click.option('--format', '-f', help='Video format')
@click.option('--output', '-o', type=click.Path(), help='Output path')
def download(url: str, format: Optional[str], output: Optional[str]) -> None:
    """Download a video from URL."""
    pass
```

### 2. yt-dlp Wrapper Service (ytdlp_wrapper.py)

```python
from dataclasses import dataclass
from typing import List, Optional, Callable, Any
from enum import Enum

class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class VideoFormat:
    format_id: str
    extension: str
    resolution: Optional[str]
    filesize: Optional[int]
    codec: Optional[str]
    is_audio_only: bool

@dataclass
class VideoInfo:
    url: str
    title: str
    uploader: Optional[str]
    duration: Optional[int]
    formats: List[VideoFormat]
    playlist_index: Optional[int]
    playlist_title: Optional[str]

@dataclass
class DownloadProgress:
    status: DownloadStatus
    downloaded_bytes: int
    total_bytes: Optional[int]
    speed: Optional[float]
    eta: Optional[int]
    filename: str

class YtdlpWrapper:
    """Wrapper around yt-dlp for video downloading."""

    def extract_info(self, url: str) -> VideoInfo:
        """Extract video information without downloading."""
        pass

    def get_formats(self, url: str) -> List[VideoFormat]:
        """Get available formats for a video."""
        pass

    def download(
        self,
        url: str,
        output_path: str,
        format_id: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> str:
        """Download video and return the file path."""
        pass

    def extract_playlist(self, url: str) -> List[VideoInfo]:
        """Extract all videos from a playlist."""
        pass
```

### 3. Download Manager Service (download_manager.py)

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum

@dataclass
class QueueItem:
    id: str
    url: str
    title: Optional[str]
    format_id: Optional[str]
    output_path: str
    status: DownloadStatus
    progress: float
    position: int
    created_at: datetime
    error_message: Optional[str]

@dataclass
class HistoryEntry:
    id: str
    url: str
    title: str
    file_path: str
    file_size: int
    downloaded_at: datetime
    status: str
    file_exists: bool

class DownloadManager:
    """Manages download queue and history."""

    def add_to_queue(self, url: str, format_id: Optional[str] = None) -> QueueItem:
        """Add a download to the queue."""
        pass

    def get_queue(self) -> List[QueueItem]:
        """Get all items in the queue."""
        pass

    def pause_download(self, item_id: str) -> bool:
        """Pause a download."""
        pass

    def resume_download(self, item_id: str) -> bool:
        """Resume a paused download."""
        pass

    def cancel_download(self, item_id: str) -> bool:
        """Cancel a download."""
        pass

    def reorder_queue(self, item_id: str, new_position: int) -> bool:
        """Move an item to a new position in the queue."""
        pass

    def get_history(
        self,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[HistoryEntry]:
        """Get download history with optional search."""
        pass

    def check_duplicate(self, url: str) -> Optional[HistoryEntry]:
        """Check if URL was previously downloaded."""
        pass

    def set_max_concurrent(self, count: int) -> None:
        """Set maximum concurrent downloads (1-5)."""
        pass
```

### 4. Format Selector Service (format_selector.py)

```python
from typing import List, Optional

class FormatSelector:
    """Handles format selection and preferences."""

    def get_available_formats(self, url: str) -> List[VideoFormat]:
        """Get all available formats for a video."""
        pass

    def get_best_format(self, formats: List[VideoFormat]) -> VideoFormat:
        """Select the best quality format."""
        pass

    def get_audio_formats(self, formats: List[VideoFormat]) -> List[VideoFormat]:
        """Filter to audio-only formats."""
        pass

    def set_default_format(self, format_preference: str) -> None:
        """Set default format preference."""
        pass

    def get_default_format(self) -> Optional[str]:
        """Get saved default format preference."""
        pass
```

### 5. Playlist Handler Service (playlist_handler.py)

```python
from typing import List, Optional, Tuple

class PlaylistHandler:
    """Handles playlist enumeration and batch downloads."""

    def enumerate_playlist(self, url: str) -> List[VideoInfo]:
        """Get all videos in a playlist."""
        pass

    def get_range(
        self,
        videos: List[VideoInfo],
        start: int,
        end: int
    ) -> List[VideoInfo]:
        """Get a range of videos from the playlist."""
        pass

    def download_batch(
        self,
        videos: List[VideoInfo],
        output_dir: str,
        format_id: Optional[str] = None,
        max_concurrent: int = 3
    ) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Download multiple videos, returns (successes, failures)."""
        pass
```

### 6. Filename Template Utility (filename_template.py)

```python
from typing import Dict, Any

class FilenameTemplate:
    """Handles filename templating with variables."""

    VARIABLES = {
        'title': 'Video title',
        'uploader': 'Channel/uploader name',
        'upload_date': 'Upload date (YYYYMMDD)',
        'id': 'Video ID',
        'ext': 'File extension',
        'playlist': 'Playlist name',
        'playlist_index': 'Position in playlist'
    }

    def __init__(self, template: str = "%(title)s.%(ext)s"):
        self.template = template

    def render(self, video_info: Dict[str, Any]) -> str:
        """Render filename from template and video info."""
        pass

    def validate(self, template: str) -> bool:
        """Validate a template string."""
        pass
```

### 7. Enhanced User Manager

```python
from typing import List, Optional

class UserManagementFeature(BaseFeature):
    """Enhanced user management with full CRUD operations."""

    def add_user(self, name: str, preferences: dict) -> User:
        """Add a new user."""
        pass

    def update_user(self, user_id: int, name: Optional[str], preferences: Optional[dict]) -> User:
        """Update an existing user."""
        pass

    def delete_user(self, user_id: int, confirm: bool = True) -> bool:
        """Delete a user with confirmation."""
        pass

    def list_users(self, page: int = 1, page_size: int = 10) -> List[User]:
        """List users with pagination."""
        pass

    def search_users(self, query: str) -> List[User]:
        """Search users by name."""
        pass
```

### 8. Enhanced Export Service

```python
from typing import List, Optional
from enum import Enum
from pathlib import Path

class ExportFormat(Enum):
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"

class ExportService:
    """Enhanced export service with multiple formats."""

    def export_users(
        self,
        format: ExportFormat,
        output_path: Path,
        fields: Optional[List[str]] = None
    ) -> Path:
        """Export users to specified format."""
        pass

    def export_history(
        self,
        format: ExportFormat,
        output_path: Path,
        fields: Optional[List[str]] = None
    ) -> Path:
        """Export download history to specified format."""
        pass

    def import_data(self, file_path: Path) -> int:
        """Import data from file, returns count of imported records."""
        pass
```

## Data Models

### Download Model (models/download.py)

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from .base import Base
import enum

class DownloadStatus(enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class QueueItem(Base):
    __tablename__ = "download_queue"

    id = Column(String(36), primary_key=True)  # UUID
    url = Column(String(2048), nullable=False)
    title = Column(String(500))
    format_id = Column(String(50))
    output_path = Column(String(1024), nullable=False)
    status = Column(Enum(DownloadStatus), default=DownloadStatus.PENDING)
    progress = Column(Float, default=0.0)
    position = Column(Integer, nullable=False)
    error_message = Column(String(1000))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

class DownloadHistory(Base):
    __tablename__ = "download_history"

    id = Column(String(36), primary_key=True)  # UUID
    url = Column(String(2048), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer)
    format_id = Column(String(50))
    duration = Column(Integer)
    uploader = Column(String(255))
    downloaded_at = Column(DateTime, nullable=False)
    status = Column(String(50), default="completed")
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: User Serialization Round-Trip

*For any* valid User object, serializing to JSON then deserializing SHALL produce an equivalent User object with identical name and preferences.

**Validates: Requirements 7.6**

### Property 2: Preferences Round-Trip

*For any* valid preferences dictionary, saving to file then loading SHALL produce an equivalent dictionary with all key-value pairs preserved.

**Validates: Requirements 8.6**

### Property 3: Export/Import Round-Trip

*For any* collection of exportable records (users or history), exporting to JSON then importing SHALL preserve all data fields and produce equivalent records.

**Validates: Requirements 12.6**

### Property 4: Queue Persistence Round-Trip

*For any* download queue state, persisting to database then loading on restart SHALL restore the exact queue with all items, positions, and statuses preserved.

**Validates: Requirements 4.4**

### Property 5: Database Consistency Invariant

*For any* sequence of database operations (add, update, delete), the database SHALL remain in a consistent state with no orphaned records, valid foreign keys, and all constraints satisfied.

**Validates: Requirements 11.6**

### Property 6: Format Information Completeness

*For any* VideoFormat object returned by the Format_Selector, it SHALL contain non-null values for format_id, extension, and is_audio_only fields.

**Validates: Requirements 2.2**

### Property 7: History Entry Completeness

*For any* HistoryEntry in the download history, it SHALL contain non-null values for id, url, title, file_path, and downloaded_at fields.

**Validates: Requirements 5.2**

### Property 8: Queue Item Completeness

*For any* QueueItem in the download queue, it SHALL contain non-null values for id, url, output_path, status, progress, position, and created_at fields.

**Validates: Requirements 4.2**

### Property 9: Error Message User-Friendliness

*For any* error displayed to the user, the message SHALL NOT contain stack traces, internal paths, or technical jargon, and SHALL be under 200 characters.

**Validates: Requirements 10.1**

### Property 10: Error Logging Completeness

*For any* error that occurs, the log file SHALL contain an entry with timestamp, error type, message, and full stack trace.

**Validates: Requirements 10.2**

### Property 11: Database Rollback on Failure

*For any* database operation that raises an exception, the database state SHALL be unchanged from before the operation began.

**Validates: Requirements 11.2**

### Property 12: Invalid URL Error Handling

*For any* invalid or unsupported URL provided to the Video_Downloader, it SHALL return an error result (not raise an unhandled exception) with a descriptive message.

**Validates: Requirements 1.2**

### Property 13: Duplicate Detection Accuracy

*For any* URL that exists in the download history, the check_duplicate function SHALL return the matching HistoryEntry.

**Validates: Requirements 5.3**

### Property 14: Filename Template Rendering

*For any* valid filename template and video metadata dictionary, the rendered filename SHALL contain no invalid filesystem characters and SHALL be non-empty.

**Validates: Requirements 6.2**

### Property 15: Directory Validation

*For any* path provided as output directory, the validation function SHALL correctly identify whether the path exists and is writable.

**Validates: Requirements 6.5**

### Property 16: User Name Validation

*For any* string provided as a user name, the validation SHALL correctly accept non-empty strings ≤255 characters and reject empty strings or those exceeding the limit.

**Validates: Requirements 7.1**

### Property 17: Preference Value Validation

*For any* preference key-value pair, the validation SHALL correctly accept values of the expected type and reject invalid types or out-of-range values.

**Validates: Requirements 8.4**

### Property 18: CLI Invalid Argument Handling

*For any* invalid combination of CLI arguments, the application SHALL exit with a non-zero code and display usage help.

**Validates: Requirements 13.6**

### Property 19: Concurrent Download Limit

*For any* configured max_concurrent value between 1 and 5, the Download_Manager SHALL never have more than that many simultaneous active downloads.

**Validates: Requirements 4.5**

### Property 20: Batch Failure Isolation

*For any* batch download where some items fail, the successful downloads SHALL complete and be recorded in history, independent of the failures.

**Validates: Requirements 3.4**

## Error Handling

### Exception Hierarchy

```python
class FarmerCLIError(Exception):
    """Base exception for all Farmer CLI errors."""
    pass

class DownloadError(FarmerCLIError):
    """Errors during video download."""
    pass

class FormatError(FarmerCLIError):
    """Errors related to format selection."""
    pass

class PlaylistError(FarmerCLIError):
    """Errors processing playlists."""
    pass

class QueueError(FarmerCLIError):
    """Errors in queue management."""
    pass

class ValidationError(FarmerCLIError):
    """Input validation errors."""
    pass

class ExportError(FarmerCLIError):
    """Errors during data export."""
    pass
```

### Error Handling Strategy

1. **External API Errors**: Wrap all yt-dlp calls in try-except, convert to DownloadError with user-friendly messages
2. **Network Errors**: Catch requests exceptions, provide troubleshooting suggestions
3. **Database Errors**: Use transactions, rollback on failure, log full details
4. **Validation Errors**: Return structured error responses, never raise to UI
5. **File System Errors**: Check permissions before operations, provide clear messages

### Logging Configuration

```python
import logging
from pathlib import Path

def configure_logging(log_level: str = "INFO", log_file: Path = None):
    """Configure application logging."""

    # Console handler - user-friendly messages only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter('%(message)s'))

    # File handler - full details including stack traces
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s'
    ))

    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=[console_handler, file_handler]
    )
```

## Testing Strategy

### Testing Framework

- **Framework**: pytest with pytest-cov for coverage
- **Property Testing**: Hypothesis for property-based tests
- **Mocking**: pytest-mock for external dependencies

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_ytdlp_wrapper.py
│   ├── test_download_manager.py
│   ├── test_format_selector.py
│   ├── test_playlist_handler.py
│   ├── test_filename_template.py
│   ├── test_user_manager.py
│   ├── test_preferences.py
│   ├── test_export.py
│   └── test_validators.py
├── property/
│   ├── test_roundtrip_properties.py
│   ├── test_invariant_properties.py
│   └── test_validation_properties.py
└── integration/
    ├── test_download_workflow.py
    ├── test_user_workflow.py
    └── test_cli_interface.py
```

### Property Test Configuration

- Minimum 100 iterations per property test
- Use Hypothesis strategies for generating test data
- Tag each test with design document property reference

### Example Property Test

```python
from hypothesis import given, strategies as st
import json

@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.one_of(st.text(), st.integers(), st.booleans()),
    min_size=1,
    max_size=10
))
def test_preferences_roundtrip(preferences: dict):
    """
    Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
    Validates: Requirements 8.6
    """
    service = PreferencesService(Path("/tmp/test_prefs.json"))
    service.save(preferences)
    loaded = service.load()
    assert loaded == preferences
```

### Coverage Requirements

- Minimum 80% overall code coverage
- 100% coverage for core services (download_manager, preferences, export)
- All error paths must have test coverage
