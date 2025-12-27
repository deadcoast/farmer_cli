"""
Integration tests for download workflow.

This module tests the complete download flow from URL to file,
queue management workflow, and history tracking.

Feature: farmer-cli-completion
Requirements: 9.4
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from farmer_cli.models.base import Base
from farmer_cli.models.download import DownloadStatus
from farmer_cli.models.download import QueueItem
from farmer_cli.models.history import DownloadHistory
from farmer_cli.services.download_manager import DownloadManager
from farmer_cli.services.download_manager import HistoryEntry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def integration_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database path for integration tests."""
    return tmp_path / "integration_test.db"


@pytest.fixture
def integration_db_engine(integration_db_path: Path):
    """Create a temporary SQLite database engine for integration tests."""
    engine = create_engine(f"sqlite:///{integration_db_path}", echo=False, future=True)
    yield engine
    engine.dispose()


@pytest.fixture
def integration_session_factory(integration_db_engine) -> sessionmaker:
    """Create a session factory for integration tests."""
    # Import all models to ensure they are registered
    from farmer_cli.models import DownloadHistory  # noqa: F401
    from farmer_cli.models import QueueItem  # noqa: F401
    from farmer_cli.models import User  # noqa: F401

    # Create all tables
    Base.metadata.create_all(integration_db_engine)

    return sessionmaker(bind=integration_db_engine, expire_on_commit=False)


@pytest.fixture
def download_manager(
    integration_session_factory: sessionmaker, tmp_path: Path
) -> DownloadManager:
    """Provide a DownloadManager instance for integration tests."""
    return DownloadManager(
        session_factory=integration_session_factory,
        default_output_path=tmp_path / "downloads",
        max_concurrent=3,
    )


# ---------------------------------------------------------------------------
# Queue Management Integration Tests
# ---------------------------------------------------------------------------


class TestQueueManagementWorkflow:
    """Integration tests for download queue management workflow."""

    def test_add_multiple_items_to_queue(self, download_manager: DownloadManager) -> None:
        """Test adding multiple items to the queue maintains correct positions."""
        urls = [
            "https://www.youtube.com/watch?v=test1",
            "https://www.youtube.com/watch?v=test2",
            "https://www.youtube.com/watch?v=test3",
        ]

        # Add items to queue
        items = []
        for url in urls:
            item = download_manager.add_to_queue(url)
            items.append(item)

        # Verify queue order
        queue = download_manager.get_queue()
        assert len(queue) == 3

        # Verify positions are sequential
        for i, item in enumerate(queue):
            assert item.position == i + 1
            assert item.url == urls[i]
            assert item.status == DownloadStatus.PENDING

    def test_queue_reordering_workflow(self, download_manager: DownloadManager) -> None:
        """Test complete queue reordering workflow."""
        # Add items
        item1 = download_manager.add_to_queue("https://example.com/video1")
        item2 = download_manager.add_to_queue("https://example.com/video2")
        item3 = download_manager.add_to_queue("https://example.com/video3")

        # Verify initial order
        queue = download_manager.get_queue()
        assert queue[0].id == item1.id
        assert queue[1].id == item2.id
        assert queue[2].id == item3.id

        # Move item3 to first position
        result = download_manager.reorder_queue(item3.id, 0)
        assert result is True

        # Verify new order
        queue = download_manager.get_queue()
        assert queue[0].id == item3.id
        assert queue[1].id == item1.id
        assert queue[2].id == item2.id

    def test_pause_resume_workflow(self, download_manager: DownloadManager) -> None:
        """Test pause and resume workflow for downloads."""
        # Add item and start download
        item = download_manager.add_to_queue("https://example.com/video")
        download_manager.start_download(item.id)

        # Verify downloading status
        updated_item = download_manager.get_queue_item(item.id)
        assert updated_item is not None
        assert updated_item.status == DownloadStatus.DOWNLOADING

        # Pause download
        result = download_manager.pause_download(item.id)
        assert result is True

        # Verify paused status
        paused_item = download_manager.get_queue_item(item.id)
        assert paused_item is not None
        assert paused_item.status == DownloadStatus.PAUSED

        # Resume download
        result = download_manager.resume_download(item.id)
        assert result is True

        # Verify downloading status again
        resumed_item = download_manager.get_queue_item(item.id)
        assert resumed_item is not None
        assert resumed_item.status == DownloadStatus.DOWNLOADING

    def test_cancel_download_workflow(self, download_manager: DownloadManager) -> None:
        """Test cancelling a download removes it from active tracking."""
        # Add and start download
        item = download_manager.add_to_queue("https://example.com/video")
        download_manager.start_download(item.id)

        # Verify active count
        assert download_manager.get_active_download_count() == 1

        # Cancel download
        result = download_manager.cancel_download(item.id)
        assert result is True

        # Verify cancelled status and active count
        cancelled_item = download_manager.get_queue_item(item.id)
        assert cancelled_item is not None
        assert cancelled_item.status == DownloadStatus.CANCELLED
        assert download_manager.get_active_download_count() == 0

    def test_concurrent_download_limit(self, download_manager: DownloadManager) -> None:
        """Test that concurrent download limit is enforced."""
        # Set max concurrent to 2
        download_manager.set_max_concurrent(2)

        # Add 3 items
        item1 = download_manager.add_to_queue("https://example.com/video1")
        item2 = download_manager.add_to_queue("https://example.com/video2")
        item3 = download_manager.add_to_queue("https://example.com/video3")

        # Start first two downloads
        assert download_manager.start_download(item1.id) is True
        assert download_manager.start_download(item2.id) is True

        # Third should fail due to limit
        assert download_manager.can_start_download() is False
        assert download_manager.start_download(item3.id) is False

        # Complete one download
        download_manager.cancel_download(item1.id)

        # Now third should be able to start
        assert download_manager.can_start_download() is True


# ---------------------------------------------------------------------------
# History Tracking Integration Tests
# ---------------------------------------------------------------------------


class TestHistoryTrackingWorkflow:
    """Integration tests for download history tracking workflow."""

    def test_add_to_history_workflow(
        self, download_manager: DownloadManager, tmp_path: Path
    ) -> None:
        """Test adding completed downloads to history."""
        # Create a test file
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"fake video content")

        # Add to history
        entry = download_manager.add_to_history(
            url="https://www.youtube.com/watch?v=test123",
            title="Test Video Title",
            file_path=str(test_file),
            file_size=test_file.stat().st_size,
            duration=120,
            uploader="Test Channel",
        )

        # Verify entry was created
        assert entry.id is not None
        assert entry.url == "https://www.youtube.com/watch?v=test123"
        assert entry.title == "Test Video Title"
        assert entry.status == "completed"

    def test_duplicate_detection_workflow(
        self, download_manager: DownloadManager, tmp_path: Path
    ) -> None:
        """Test duplicate URL detection in history."""
        test_url = "https://www.youtube.com/watch?v=duplicate_test"
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"content")

        # Add first entry
        download_manager.add_to_history(
            url=test_url,
            title="First Download",
            file_path=str(test_file),
        )

        # Check for duplicate
        duplicate = download_manager.check_duplicate(test_url)
        assert duplicate is not None
        assert duplicate.url == test_url
        assert duplicate.title == "First Download"

        # Check non-existent URL
        no_duplicate = download_manager.check_duplicate("https://example.com/new")
        assert no_duplicate is None

    def test_history_search_workflow(
        self, download_manager: DownloadManager, tmp_path: Path
    ) -> None:
        """Test searching through download history."""
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"content")

        # Add multiple history entries
        download_manager.add_to_history(
            url="https://example.com/video1",
            title="Python Tutorial Part 1",
            file_path=str(test_file),
            uploader="CodeChannel",
        )
        download_manager.add_to_history(
            url="https://example.com/video2",
            title="JavaScript Basics",
            file_path=str(test_file),
            uploader="WebDev",
        )
        download_manager.add_to_history(
            url="https://example.com/video3",
            title="Python Tutorial Part 2",
            file_path=str(test_file),
            uploader="CodeChannel",
        )

        # Search by title
        results = download_manager.get_history(search="Python")
        assert len(results) == 2

        # Search by uploader
        results = download_manager.get_history(search="CodeChannel")
        assert len(results) == 2

        # Search with no results
        results = download_manager.get_history(search="Rust")
        assert len(results) == 0

    def test_history_pagination_workflow(
        self, download_manager: DownloadManager, tmp_path: Path
    ) -> None:
        """Test pagination of download history."""
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"content")

        # Add 10 history entries
        for i in range(10):
            download_manager.add_to_history(
                url=f"https://example.com/video{i}",
                title=f"Video {i}",
                file_path=str(test_file),
            )

        # Get first page
        page1 = download_manager.get_history(limit=3, offset=0)
        assert len(page1) == 3

        # Get second page
        page2 = download_manager.get_history(limit=3, offset=3)
        assert len(page2) == 3

        # Verify no overlap
        page1_ids = {e.id for e in page1}
        page2_ids = {e.id for e in page2}
        assert page1_ids.isdisjoint(page2_ids)

        # Get total count
        total = download_manager.get_history_count()
        assert total == 10

    def test_clear_history_workflow(
        self, download_manager: DownloadManager, tmp_path: Path
    ) -> None:
        """Test clearing download history."""
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"content")

        # Add entries
        for i in range(5):
            download_manager.add_to_history(
                url=f"https://example.com/video{i}",
                title=f"Video {i}",
                file_path=str(test_file),
            )

        # Verify entries exist
        assert download_manager.get_history_count() == 5

        # Clear history
        deleted_count = download_manager.clear_history()
        assert deleted_count == 5

        # Verify history is empty
        assert download_manager.get_history_count() == 0


# ---------------------------------------------------------------------------
# Complete Download Flow Integration Tests
# ---------------------------------------------------------------------------


class TestCompleteDownloadFlow:
    """Integration tests for complete download flow from URL to file."""

    def test_queue_to_history_flow(
        self, download_manager: DownloadManager, tmp_path: Path
    ) -> None:
        """Test complete flow from queue to history."""
        test_url = "https://www.youtube.com/watch?v=complete_flow"
        test_file = tmp_path / "downloads" / "video.mp4"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_bytes(b"video content")

        # Step 1: Add to queue
        queue_item = download_manager.add_to_queue(
            url=test_url,
            title="Complete Flow Test",
        )
        assert queue_item.status == DownloadStatus.PENDING

        # Step 2: Start download
        started = download_manager.start_download(queue_item.id)
        assert started is True

        # Step 3: Complete download (simulated)
        completed = download_manager.complete_download(
            item_id=queue_item.id,
            file_path=str(test_file),
            file_size=test_file.stat().st_size,
        )
        assert completed is True

        # Step 4: Verify in history
        history = download_manager.get_history(search="Complete Flow")
        assert len(history) == 1
        assert history[0].url == test_url

        # Step 5: Verify duplicate detection works
        duplicate = download_manager.check_duplicate(test_url)
        assert duplicate is not None

    def test_failed_download_flow(self, download_manager: DownloadManager) -> None:
        """Test flow when download fails."""
        # Add to queue
        queue_item = download_manager.add_to_queue(
            url="https://example.com/failing_video",
            title="Failing Video",
        )

        # Start download
        download_manager.start_download(queue_item.id)

        # Fail download
        failed = download_manager.fail_download(
            item_id=queue_item.id,
            error_message="Network error: Connection refused",
        )
        assert failed is True

        # Verify status
        failed_item = download_manager.get_queue_item(queue_item.id)
        assert failed_item is not None
        assert failed_item.status == DownloadStatus.FAILED
        assert "Network error" in (failed_item.error_message or "")

    def test_queue_persistence_across_operations(
        self, download_manager: DownloadManager
    ) -> None:
        """Test that queue state persists correctly across operations."""
        # Add items
        item1 = download_manager.add_to_queue("https://example.com/v1", title="Video 1")
        item2 = download_manager.add_to_queue("https://example.com/v2", title="Video 2")

        # Perform various operations
        download_manager.start_download(item1.id)
        download_manager.pause_download(item1.id)

        # Get fresh queue
        queue = download_manager.get_queue()

        # Verify state persisted
        item1_fresh = next((i for i in queue if i.id == item1.id), None)
        item2_fresh = next((i for i in queue if i.id == item2.id), None)

        assert item1_fresh is not None
        assert item1_fresh.status == DownloadStatus.PAUSED
        assert item2_fresh is not None
        assert item2_fresh.status == DownloadStatus.PENDING

    def test_remove_from_queue_updates_positions(
        self, download_manager: DownloadManager
    ) -> None:
        """Test that removing items updates positions correctly."""
        # Add 4 items
        items = []
        for i in range(4):
            item = download_manager.add_to_queue(f"https://example.com/v{i}")
            items.append(item)

        # Remove second item
        download_manager.remove_from_queue(items[1].id)

        # Get queue
        queue = download_manager.get_queue()
        assert len(queue) == 3

        # Verify positions are sequential
        positions = [item.position for item in queue]
        assert positions == sorted(positions)
        assert len(set(positions)) == len(positions)  # No duplicates
