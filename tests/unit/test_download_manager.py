"""
Unit tests for the download_manager module.

Tests cover:
- Queue manipulation methods (add, pause, resume, cancel, reorder)
- History management methods (add, get, check_duplicate, clear)
- Concurrent download tracking
- add_to_history() method
- get_history_count() method

Requirements: 9.1, 9.3
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from farmer_cli.exceptions import DatabaseError
from farmer_cli.exceptions import QueueError
from farmer_cli.models.download import DownloadStatus
from farmer_cli.models.download import QueueItem
from farmer_cli.models.history import DownloadHistory
from farmer_cli.services.download_manager import DownloadManager
from farmer_cli.services.download_manager import HistoryEntry


# ---------------------------------------------------------------------------
# HistoryEntry Tests
# ---------------------------------------------------------------------------


class TestHistoryEntry:
    """Tests for HistoryEntry dataclass."""

    def test_history_entry_creation(self):
        """Test creating a HistoryEntry."""
        entry = HistoryEntry(
            id="test-id",
            url="https://youtube.com/watch?v=test",
            title="Test Video",
            file_path="/downloads/test.mp4",
            file_size=1000000,
            downloaded_at=datetime.utcnow(),
            status="completed",
            file_exists=True,
        )
        assert entry.id == "test-id"
        assert entry.title == "Test Video"
        assert entry.status == "completed"

    def test_history_entry_from_model(self):
        """Test creating HistoryEntry from DownloadHistory model."""
        model = MagicMock(spec=DownloadHistory)
        model.id = "model-id"
        model.url = "https://example.com/video"
        model.title = "Model Video"
        model.file_path = "/path/to/video.mp4"
        model.file_size = 5000000
        model.downloaded_at = datetime(2023, 6, 15, 12, 0, 0)
        model.status = "completed"
        model.file_exists = True
        model.format_id = "22"
        model.duration = 300
        model.uploader = "Test Channel"

        entry = HistoryEntry.from_model(model)

        assert entry.id == "model-id"
        assert entry.url == "https://example.com/video"
        assert entry.title == "Model Video"
        assert entry.file_size == 5000000
        assert entry.format_id == "22"


# ---------------------------------------------------------------------------
# DownloadManager Initialization Tests
# ---------------------------------------------------------------------------


class TestDownloadManagerInit:
    """Tests for DownloadManager initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        session_factory = MagicMock()
        manager = DownloadManager(session_factory)

        assert manager._max_concurrent == DownloadManager.DEFAULT_CONCURRENT
        assert manager._default_output_path == Path.cwd() / "downloads"

    def test_init_with_custom_values(self, tmp_path):
        """Test initialization with custom values."""
        session_factory = MagicMock()
        manager = DownloadManager(
            session_factory,
            default_output_path=tmp_path,
            max_concurrent=5,
        )

        assert manager._max_concurrent == 5
        assert manager._default_output_path == tmp_path

    def test_init_clamps_max_concurrent_low(self):
        """Test that max_concurrent is clamped to minimum."""
        session_factory = MagicMock()
        manager = DownloadManager(session_factory, max_concurrent=0)

        assert manager._max_concurrent == DownloadManager.MIN_CONCURRENT

    def test_init_clamps_max_concurrent_high(self):
        """Test that max_concurrent is clamped to maximum."""
        session_factory = MagicMock()
        manager = DownloadManager(session_factory, max_concurrent=100)

        assert manager._max_concurrent == DownloadManager.MAX_CONCURRENT


# ---------------------------------------------------------------------------
# Queue Management Tests
# ---------------------------------------------------------------------------


class TestQueueManagement:
    """Tests for queue management methods."""

    @pytest.fixture
    def manager(self, db_session):
        """Create a DownloadManager with test database."""
        return DownloadManager(lambda: db_session)

    def test_add_to_queue_success(self, manager):
        """Test adding an item to the queue."""
        item = manager.add_to_queue(
            url="https://youtube.com/watch?v=test123",
            title="Test Video",
        )

        assert item is not None
        assert item.url == "https://youtube.com/watch?v=test123"
        assert item.title == "Test Video"
        assert item.status == DownloadStatus.PENDING
        assert item.position == 1

    def test_add_to_queue_empty_url_raises(self, manager):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            manager.add_to_queue(url="")

    def test_add_to_queue_whitespace_url_raises(self, manager):
        """Test that whitespace URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            manager.add_to_queue(url="   ")

    def test_add_to_queue_with_format(self, manager):
        """Test adding item with format ID."""
        item = manager.add_to_queue(
            url="https://youtube.com/watch?v=test",
            format_id="22",
        )

        assert item.format_id == "22"

    def test_add_to_queue_increments_position(self, manager):
        """Test that position increments for each item."""
        item1 = manager.add_to_queue(url="https://example.com/1")
        item2 = manager.add_to_queue(url="https://example.com/2")
        item3 = manager.add_to_queue(url="https://example.com/3")

        assert item1.position == 1
        assert item2.position == 2
        assert item3.position == 3

    def test_get_queue_returns_ordered_items(self, manager):
        """Test that get_queue returns items ordered by position."""
        manager.add_to_queue(url="https://example.com/1")
        manager.add_to_queue(url="https://example.com/2")
        manager.add_to_queue(url="https://example.com/3")

        queue = manager.get_queue()

        assert len(queue) == 3
        assert queue[0].position < queue[1].position < queue[2].position

    def test_get_queue_excludes_completed(self, manager, db_session):
        """Test that get_queue excludes completed items by default."""
        item = manager.add_to_queue(url="https://example.com/1")
        manager.add_to_queue(url="https://example.com/2")

        # Mark first item as completed
        db_item = db_session.query(QueueItem).filter(QueueItem.id == item.id).first()
        db_item.status = DownloadStatus.COMPLETED
        db_session.commit()

        queue = manager.get_queue(include_completed=False)

        assert len(queue) == 1

    def test_get_queue_includes_completed_when_requested(self, manager, db_session):
        """Test that get_queue includes completed items when requested."""
        item = manager.add_to_queue(url="https://example.com/1")
        manager.add_to_queue(url="https://example.com/2")

        # Mark first item as completed
        db_item = db_session.query(QueueItem).filter(QueueItem.id == item.id).first()
        db_item.status = DownloadStatus.COMPLETED
        db_session.commit()

        queue = manager.get_queue(include_completed=True)

        assert len(queue) == 2

    def test_get_queue_item_found(self, manager):
        """Test getting a specific queue item."""
        item = manager.add_to_queue(url="https://example.com/test")

        retrieved = manager.get_queue_item(item.id)

        assert retrieved is not None
        assert retrieved.id == item.id

    def test_get_queue_item_not_found(self, manager):
        """Test getting a non-existent queue item."""
        retrieved = manager.get_queue_item("non-existent-id")

        assert retrieved is None


# ---------------------------------------------------------------------------
# Pause/Resume/Cancel Tests
# ---------------------------------------------------------------------------


class TestPauseResumeCancel:
    """Tests for pause, resume, and cancel operations."""

    @pytest.fixture
    def manager(self, db_session):
        """Create a DownloadManager with test database."""
        return DownloadManager(lambda: db_session)

    def test_pause_download_success(self, manager, db_session):
        """Test pausing a downloading item."""
        item = manager.add_to_queue(url="https://example.com/test")

        # Set to downloading first
        db_item = db_session.query(QueueItem).filter(QueueItem.id == item.id).first()
        db_item.status = DownloadStatus.DOWNLOADING
        db_session.commit()

        result = manager.pause_download(item.id)

        assert result is True
        updated = manager.get_queue_item(item.id)
        assert updated.status == DownloadStatus.PAUSED

    def test_pause_download_not_found(self, manager):
        """Test pausing a non-existent item."""
        result = manager.pause_download("non-existent-id")

        assert result is False

    def test_pause_download_invalid_status(self, manager):
        """Test pausing an item that cannot be paused."""
        item = manager.add_to_queue(url="https://example.com/test")
        # Item is PENDING, cannot be paused

        result = manager.pause_download(item.id)

        assert result is False

    def test_resume_download_success(self, manager, db_session):
        """Test resuming a paused item."""
        item = manager.add_to_queue(url="https://example.com/test")

        # Set to paused first
        db_item = db_session.query(QueueItem).filter(QueueItem.id == item.id).first()
        db_item.status = DownloadStatus.PAUSED
        db_session.commit()

        result = manager.resume_download(item.id)

        assert result is True
        updated = manager.get_queue_item(item.id)
        assert updated.status == DownloadStatus.DOWNLOADING

    def test_resume_download_not_found(self, manager):
        """Test resuming a non-existent item."""
        result = manager.resume_download("non-existent-id")

        assert result is False

    def test_resume_download_invalid_status(self, manager, db_session):
        """Test resuming an item that cannot be resumed."""
        item = manager.add_to_queue(url="https://example.com/test")

        # Set to completed
        db_item = db_session.query(QueueItem).filter(QueueItem.id == item.id).first()
        db_item.status = DownloadStatus.COMPLETED
        db_session.commit()

        result = manager.resume_download(item.id)

        assert result is False

    def test_cancel_download_success(self, manager, db_session):
        """Test cancelling a download."""
        item = manager.add_to_queue(url="https://example.com/test")

        # Set to downloading
        db_item = db_session.query(QueueItem).filter(QueueItem.id == item.id).first()
        db_item.status = DownloadStatus.DOWNLOADING
        db_session.commit()

        result = manager.cancel_download(item.id)

        assert result is True
        updated = manager.get_queue_item(item.id)
        assert updated.status == DownloadStatus.CANCELLED

    def test_cancel_download_not_found(self, manager):
        """Test cancelling a non-existent item."""
        result = manager.cancel_download("non-existent-id")

        assert result is False

    def test_cancel_download_pending(self, manager):
        """Test cancelling a pending item."""
        item = manager.add_to_queue(url="https://example.com/test")

        result = manager.cancel_download(item.id)

        assert result is True
        updated = manager.get_queue_item(item.id)
        assert updated.status == DownloadStatus.CANCELLED


# ---------------------------------------------------------------------------
# Reorder Tests
# ---------------------------------------------------------------------------


class TestReorderQueue:
    """Tests for queue reordering."""

    @pytest.fixture
    def manager(self, db_session):
        """Create a DownloadManager with test database."""
        return DownloadManager(lambda: db_session)

    def test_reorder_queue_move_down(self, manager):
        """Test moving an item down in the queue."""
        item1 = manager.add_to_queue(url="https://example.com/1")
        manager.add_to_queue(url="https://example.com/2")
        manager.add_to_queue(url="https://example.com/3")

        result = manager.reorder_queue(item1.id, 2)

        assert result is True
        updated = manager.get_queue_item(item1.id)
        assert updated.position == 2

    def test_reorder_queue_move_up(self, manager):
        """Test moving an item up in the queue."""
        manager.add_to_queue(url="https://example.com/1")
        manager.add_to_queue(url="https://example.com/2")
        item3 = manager.add_to_queue(url="https://example.com/3")

        result = manager.reorder_queue(item3.id, 0)

        assert result is True
        updated = manager.get_queue_item(item3.id)
        assert updated.position == 0

    def test_reorder_queue_same_position(self, manager):
        """Test reordering to same position."""
        item = manager.add_to_queue(url="https://example.com/1")

        result = manager.reorder_queue(item.id, item.position)

        assert result is True

    def test_reorder_queue_not_found(self, manager):
        """Test reordering a non-existent item."""
        result = manager.reorder_queue("non-existent-id", 0)

        assert result is False

    def test_reorder_queue_negative_position_raises(self, manager):
        """Test that negative position raises ValueError."""
        item = manager.add_to_queue(url="https://example.com/1")

        with pytest.raises(ValueError, match="Position cannot be negative"):
            manager.reorder_queue(item.id, -1)

    def test_remove_from_queue_success(self, manager):
        """Test removing an item from the queue."""
        item = manager.add_to_queue(url="https://example.com/test")

        result = manager.remove_from_queue(item.id)

        assert result is True
        assert manager.get_queue_item(item.id) is None

    def test_remove_from_queue_not_found(self, manager):
        """Test removing a non-existent item."""
        result = manager.remove_from_queue("non-existent-id")

        assert result is False

    def test_remove_from_queue_updates_positions(self, manager):
        """Test that removing updates positions of subsequent items."""
        item1 = manager.add_to_queue(url="https://example.com/1")
        item2 = manager.add_to_queue(url="https://example.com/2")
        item3 = manager.add_to_queue(url="https://example.com/3")

        manager.remove_from_queue(item1.id)

        updated2 = manager.get_queue_item(item2.id)
        updated3 = manager.get_queue_item(item3.id)

        assert updated2.position == 1
        assert updated3.position == 2


# ---------------------------------------------------------------------------
# History Management Tests
# ---------------------------------------------------------------------------


class TestHistoryManagement:
    """Tests for history management methods."""

    @pytest.fixture
    def manager(self, db_session):
        """Create a DownloadManager with test database."""
        return DownloadManager(lambda: db_session)

    def test_add_to_history_success(self, manager):
        """Test adding an entry to history."""
        entry = manager.add_to_history(
            url="https://youtube.com/watch?v=test",
            title="Test Video",
            file_path="/downloads/test.mp4",
            file_size=1000000,
            format_id="22",
            duration=300,
            uploader="Test Channel",
        )

        assert entry is not None
        assert entry.url == "https://youtube.com/watch?v=test"
        assert entry.title == "Test Video"
        assert entry.file_size == 1000000
        assert entry.status == "completed"

    def test_add_to_history_minimal(self, manager):
        """Test adding history entry with minimal data."""
        entry = manager.add_to_history(
            url="https://example.com/video",
            title="Minimal Video",
            file_path="/downloads/minimal.mp4",
        )

        assert entry is not None
        assert entry.file_size is None
        assert entry.format_id is None

    def test_get_history_returns_entries(self, manager):
        """Test getting history entries."""
        manager.add_to_history(
            url="https://example.com/1",
            title="Video 1",
            file_path="/downloads/1.mp4",
        )
        manager.add_to_history(
            url="https://example.com/2",
            title="Video 2",
            file_path="/downloads/2.mp4",
        )

        history = manager.get_history()

        assert len(history) == 2

    def test_get_history_with_search(self, manager):
        """Test getting history with search filter."""
        manager.add_to_history(
            url="https://example.com/1",
            title="Python Tutorial",
            file_path="/downloads/1.mp4",
        )
        manager.add_to_history(
            url="https://example.com/2",
            title="JavaScript Guide",
            file_path="/downloads/2.mp4",
        )

        history = manager.get_history(search="Python")

        assert len(history) == 1
        assert "Python" in history[0].title

    def test_get_history_with_pagination(self, manager):
        """Test getting history with pagination."""
        for i in range(10):
            manager.add_to_history(
                url=f"https://example.com/{i}",
                title=f"Video {i}",
                file_path=f"/downloads/{i}.mp4",
            )

        page1 = manager.get_history(limit=5, offset=0)
        page2 = manager.get_history(limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) == 5

    def test_get_history_count(self, manager):
        """Test getting history count."""
        for i in range(5):
            manager.add_to_history(
                url=f"https://example.com/{i}",
                title=f"Video {i}",
                file_path=f"/downloads/{i}.mp4",
            )

        count = manager.get_history_count()

        assert count == 5

    def test_get_history_count_with_search(self, manager):
        """Test getting history count with search filter."""
        manager.add_to_history(
            url="https://example.com/1",
            title="Python Tutorial",
            file_path="/downloads/1.mp4",
        )
        manager.add_to_history(
            url="https://example.com/2",
            title="JavaScript Guide",
            file_path="/downloads/2.mp4",
        )
        manager.add_to_history(
            url="https://example.com/3",
            title="Python Advanced",
            file_path="/downloads/3.mp4",
        )

        count = manager.get_history_count(search="Python")

        assert count == 2

    def test_check_duplicate_found(self, manager):
        """Test checking for duplicate URL that exists."""
        manager.add_to_history(
            url="https://youtube.com/watch?v=test123",
            title="Test Video",
            file_path="/downloads/test.mp4",
        )

        duplicate = manager.check_duplicate("https://youtube.com/watch?v=test123")

        assert duplicate is not None
        assert duplicate.url == "https://youtube.com/watch?v=test123"

    def test_check_duplicate_not_found(self, manager):
        """Test checking for duplicate URL that doesn't exist."""
        duplicate = manager.check_duplicate("https://youtube.com/watch?v=nonexistent")

        assert duplicate is None

    def test_check_duplicate_empty_url(self, manager):
        """Test checking duplicate with empty URL."""
        duplicate = manager.check_duplicate("")

        assert duplicate is None

    def test_clear_history(self, manager):
        """Test clearing all history."""
        for i in range(5):
            manager.add_to_history(
                url=f"https://example.com/{i}",
                title=f"Video {i}",
                file_path=f"/downloads/{i}.mp4",
            )

        count = manager.clear_history()

        assert count == 5
        assert manager.get_history_count() == 0

    def test_remove_from_history_success(self, manager):
        """Test removing a specific history entry."""
        entry = manager.add_to_history(
            url="https://example.com/test",
            title="Test Video",
            file_path="/downloads/test.mp4",
        )

        result = manager.remove_from_history(entry.id)

        assert result is True
        assert manager.get_history_count() == 0

    def test_remove_from_history_not_found(self, manager):
        """Test removing a non-existent history entry."""
        result = manager.remove_from_history("non-existent-id")

        assert result is False


# ---------------------------------------------------------------------------
# Concurrent Download Tests
# ---------------------------------------------------------------------------


class TestConcurrentDownloads:
    """Tests for concurrent download management."""

    @pytest.fixture
    def manager(self, db_session):
        """Create a DownloadManager with test database."""
        return DownloadManager(lambda: db_session, max_concurrent=3)

    def test_max_concurrent_property(self, manager):
        """Test max_concurrent property."""
        assert manager.max_concurrent == 3

    def test_set_max_concurrent_valid(self, manager):
        """Test setting valid max_concurrent value."""
        manager.set_max_concurrent(5)

        assert manager.max_concurrent == 5

    def test_set_max_concurrent_too_low_raises(self, manager):
        """Test that setting max_concurrent below minimum raises."""
        with pytest.raises(ValueError):
            manager.set_max_concurrent(0)

    def test_set_max_concurrent_too_high_raises(self, manager):
        """Test that setting max_concurrent above maximum raises."""
        with pytest.raises(ValueError):
            manager.set_max_concurrent(10)

    def test_get_active_download_count_empty(self, manager):
        """Test active download count when empty."""
        assert manager.get_active_download_count() == 0

    def test_can_start_download_when_empty(self, manager):
        """Test can_start_download when no active downloads."""
        assert manager.can_start_download() is True

    def test_start_download_success(self, manager):
        """Test starting a download."""
        item = manager.add_to_queue(url="https://example.com/test")

        result = manager.start_download(item.id)

        assert result is True
        assert manager.get_active_download_count() == 1
        updated = manager.get_queue_item(item.id)
        assert updated.status == DownloadStatus.DOWNLOADING

    def test_start_download_not_found(self, manager):
        """Test starting a non-existent download."""
        result = manager.start_download("non-existent-id")

        assert result is False

    def test_start_download_at_limit(self, manager):
        """Test starting download when at concurrent limit."""
        # Add and start max_concurrent downloads
        for i in range(manager.max_concurrent):
            item = manager.add_to_queue(url=f"https://example.com/{i}")
            manager.start_download(item.id)

        # Try to start another
        new_item = manager.add_to_queue(url="https://example.com/extra")
        result = manager.start_download(new_item.id)

        assert result is False

    def test_complete_download_success(self, manager, tmp_path):
        """Test completing a download."""
        item = manager.add_to_queue(url="https://example.com/test", title="Test Video")
        manager.start_download(item.id)

        # Create a test file
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"test content")

        result = manager.complete_download(item.id, str(test_file), file_size=12)

        assert result is True
        updated = manager.get_queue_item(item.id)
        assert updated.status == DownloadStatus.COMPLETED
        assert manager.get_active_download_count() == 0

        # Check history was created
        history = manager.get_history()
        assert len(history) == 1
        assert history[0].url == "https://example.com/test"

    def test_complete_download_not_found(self, manager):
        """Test completing a non-existent download."""
        result = manager.complete_download("non-existent-id", "/path/to/file.mp4")

        assert result is False

    def test_fail_download_success(self, manager):
        """Test failing a download."""
        item = manager.add_to_queue(url="https://example.com/test")
        manager.start_download(item.id)

        result = manager.fail_download(item.id, "Network error")

        assert result is True
        updated = manager.get_queue_item(item.id)
        assert updated.status == DownloadStatus.FAILED
        assert updated.error_message == "Network error"
        assert manager.get_active_download_count() == 0

    def test_fail_download_not_found(self, manager):
        """Test failing a non-existent download."""
        result = manager.fail_download("non-existent-id", "Error")

        assert result is False

    def test_update_progress_success(self, manager):
        """Test updating download progress."""
        item = manager.add_to_queue(url="https://example.com/test")
        manager.start_download(item.id)

        result = manager.update_progress(item.id, 50.0)

        assert result is True
        updated = manager.get_queue_item(item.id)
        assert updated.progress == 50.0

    def test_update_progress_clamps_values(self, manager):
        """Test that progress is clamped to 0-100."""
        item = manager.add_to_queue(url="https://example.com/test")
        manager.start_download(item.id)

        manager.update_progress(item.id, 150.0)
        updated = manager.get_queue_item(item.id)
        assert updated.progress == 100.0

        manager.update_progress(item.id, -50.0)
        updated = manager.get_queue_item(item.id)
        assert updated.progress == 0.0

    def test_update_progress_not_found(self, manager):
        """Test updating progress for non-existent item."""
        result = manager.update_progress("non-existent-id", 50.0)

        assert result is False


# ---------------------------------------------------------------------------
# Queue State and Restoration Tests
# ---------------------------------------------------------------------------


class TestQueueStateAndRestoration:
    """Tests for queue state and restoration."""

    @pytest.fixture
    def manager(self, db_session):
        """Create a DownloadManager with test database."""
        return DownloadManager(lambda: db_session)

    def test_restore_queue_empty(self, manager):
        """Test restoring an empty queue."""
        items = manager.restore_queue()

        assert items == []

    def test_restore_queue_resets_downloading(self, manager, db_session):
        """Test that restore_queue resets DOWNLOADING items to PENDING."""
        item = manager.add_to_queue(url="https://example.com/test")

        # Set to downloading (simulating interrupted download)
        db_item = db_session.query(QueueItem).filter(QueueItem.id == item.id).first()
        db_item.status = DownloadStatus.DOWNLOADING
        db_session.commit()

        items = manager.restore_queue()

        assert len(items) == 1
        assert items[0].status == DownloadStatus.PENDING

    def test_restore_queue_excludes_completed(self, manager, db_session):
        """Test that restore_queue excludes completed items."""
        item1 = manager.add_to_queue(url="https://example.com/1")
        manager.add_to_queue(url="https://example.com/2")

        # Mark first as completed
        db_item = db_session.query(QueueItem).filter(QueueItem.id == item1.id).first()
        db_item.status = DownloadStatus.COMPLETED
        db_session.commit()

        items = manager.restore_queue()

        assert len(items) == 1

    def test_get_queue_state(self, manager):
        """Test getting queue state."""
        manager.add_to_queue(url="https://example.com/1")
        manager.add_to_queue(url="https://example.com/2")

        state = manager.get_queue_state()

        assert state["total_items"] == 2
        assert state["status_counts"]["pending"] == 2
        assert state["active_downloads"] == 0
        assert state["can_start_more"] is True

    def test_retry_failed_success(self, manager, db_session):
        """Test retrying a failed download."""
        item = manager.add_to_queue(url="https://example.com/test")

        # Set to failed
        db_item = db_session.query(QueueItem).filter(QueueItem.id == item.id).first()
        db_item.status = DownloadStatus.FAILED
        db_item.error_message = "Previous error"
        db_session.commit()

        result = manager.retry_failed(item.id)

        assert result is True
        updated = manager.get_queue_item(item.id)
        assert updated.status == DownloadStatus.PENDING
        assert updated.error_message is None
        assert updated.progress == 0.0

    def test_retry_failed_not_failed_status(self, manager):
        """Test retrying an item that isn't failed."""
        item = manager.add_to_queue(url="https://example.com/test")

        result = manager.retry_failed(item.id)

        assert result is False

    def test_retry_failed_not_found(self, manager):
        """Test retrying a non-existent item."""
        result = manager.retry_failed("non-existent-id")

        assert result is False

    def test_clear_completed(self, manager, db_session):
        """Test clearing completed items."""
        item1 = manager.add_to_queue(url="https://example.com/1")
        item2 = manager.add_to_queue(url="https://example.com/2")
        manager.add_to_queue(url="https://example.com/3")

        # Mark some as completed/cancelled
        db_item1 = db_session.query(QueueItem).filter(QueueItem.id == item1.id).first()
        db_item1.status = DownloadStatus.COMPLETED
        db_item2 = db_session.query(QueueItem).filter(QueueItem.id == item2.id).first()
        db_item2.status = DownloadStatus.CANCELLED
        db_session.commit()

        count = manager.clear_completed()

        assert count == 2
        queue = manager.get_queue(include_completed=True)
        assert len(queue) == 1

    def test_set_on_download_complete_callback(self, manager):
        """Test setting download complete callback."""
        callback = MagicMock()
        manager.set_on_download_complete_callback(callback)

        assert manager._on_download_complete == callback
