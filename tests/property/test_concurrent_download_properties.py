"""
Property-based tests for concurrent download limit in DownloadManager.

Feature: farmer-cli-completion
Property 19: Concurrent Download Limit
Validates: Requirements 4.5

For any configured max_concurrent value between 1 and 5, the Download_Manager
SHALL never have more than that many simultaneous active downloads.
"""

import uuid
from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st

from farmer_cli.models.download import DownloadStatus
from farmer_cli.models.download import QueueItem
from farmer_cli.services.download_manager import DownloadManager


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid concurrent limits
concurrent_limit_strategy = st.integers(min_value=1, max_value=5)

# Strategy for generating invalid concurrent limits (too low)
invalid_low_concurrent_strategy = st.integers(min_value=-100, max_value=0)

# Strategy for generating invalid concurrent limits (too high)
invalid_high_concurrent_strategy = st.integers(min_value=6, max_value=100)

# Strategy for generating number of downloads to add
num_downloads_strategy = st.integers(min_value=1, max_value=10)


# ---------------------------------------------------------------------------
# Helper function to clean database
# ---------------------------------------------------------------------------

def clean_queue(session):
    """Clean all queue items from the database."""
    session.query(QueueItem).delete()
    session.commit()


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestConcurrentDownloadLimit:
    """
    Property 19: Concurrent Download Limit

    For any configured max_concurrent value between 1 and 5, the Download_Manager
    SHALL never have more than that many simultaneous active downloads.

    **Validates: Requirements 4.5**
    """

    @given(max_concurrent=concurrent_limit_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_set_max_concurrent_accepts_valid_values(
        self,
        db_session,
        max_concurrent: int,
    ):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        For any value between 1 and 5, set_max_concurrent SHALL accept it.
        """
        manager = DownloadManager(session_factory=lambda: db_session)

        # Should not raise
        manager.set_max_concurrent(max_concurrent)

        assert manager.max_concurrent == max_concurrent

    @given(max_concurrent=invalid_low_concurrent_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_set_max_concurrent_rejects_values_below_minimum(
        self,
        db_session,
        max_concurrent: int,
    ):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        For any value below 1, set_max_concurrent SHALL raise ValueError.
        """
        manager = DownloadManager(session_factory=lambda: db_session)

        with pytest.raises(ValueError, match="Concurrent downloads must be between"):
            manager.set_max_concurrent(max_concurrent)

    @given(max_concurrent=invalid_high_concurrent_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_set_max_concurrent_rejects_values_above_maximum(
        self,
        db_session,
        max_concurrent: int,
    ):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        For any value above 5, set_max_concurrent SHALL raise ValueError.
        """
        manager = DownloadManager(session_factory=lambda: db_session)

        with pytest.raises(ValueError, match="Concurrent downloads must be between"):
            manager.set_max_concurrent(max_concurrent)

    @given(
        max_concurrent=concurrent_limit_strategy,
        num_downloads=num_downloads_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_active_downloads_never_exceed_limit(
        self,
        db_session,
        max_concurrent: int,
        num_downloads: int,
    ):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        For any number of download attempts, active downloads SHALL never
        exceed the configured max_concurrent limit.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)
        manager.set_max_concurrent(max_concurrent)

        # Add multiple queue items
        item_ids = []
        for i in range(num_downloads):
            item = QueueItem(
                id=str(uuid.uuid4()),
                url=f"https://example.com/video{uuid.uuid4()}",
                output_path=f"/downloads/video{uuid.uuid4()}.mp4",
                status=DownloadStatus.PENDING,
                progress=0.0,
                position=i,
            )
            item.created_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            db_session.add(item)
            item_ids.append(item.id)

        db_session.commit()

        # Try to start all downloads
        started_count = 0
        for item_id in item_ids:
            if manager.start_download(item_id):
                started_count += 1

            # Verify we never exceed the limit
            active_count = manager.get_active_download_count()
            assert active_count <= max_concurrent, (
                f"Active downloads ({active_count}) should never exceed "
                f"max_concurrent ({max_concurrent})"
            )

        # Verify final state
        assert started_count <= max_concurrent, (
            f"Started downloads ({started_count}) should not exceed "
            f"max_concurrent ({max_concurrent})"
        )

    @given(max_concurrent=concurrent_limit_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_can_start_download_respects_limit(
        self,
        db_session,
        max_concurrent: int,
    ):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        can_start_download SHALL return False when at the concurrent limit.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)
        manager.set_max_concurrent(max_concurrent)

        # Add and start downloads up to the limit
        for i in range(max_concurrent):
            item = QueueItem(
                id=str(uuid.uuid4()),
                url=f"https://example.com/video{uuid.uuid4()}",
                output_path=f"/downloads/video{uuid.uuid4()}.mp4",
                status=DownloadStatus.PENDING,
                progress=0.0,
                position=i,
            )
            item.created_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            db_session.add(item)
            db_session.commit()

            assert manager.can_start_download(), (
                f"Should be able to start download {i + 1} of {max_concurrent}"
            )
            manager.start_download(item.id)

        # Now at the limit
        assert not manager.can_start_download(), (
            "Should not be able to start more downloads when at limit"
        )

    @given(max_concurrent=concurrent_limit_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_completing_download_allows_new_start(
        self,
        db_session,
        max_concurrent: int,
    ):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        After completing a download, can_start_download SHALL return True
        if previously at the limit.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)
        manager.set_max_concurrent(max_concurrent)

        # Add and start downloads up to the limit
        item_ids = []
        for i in range(max_concurrent):
            item = QueueItem(
                id=str(uuid.uuid4()),
                url=f"https://example.com/video{uuid.uuid4()}",
                title=f"Video {i}",
                output_path=f"/downloads/video{uuid.uuid4()}.mp4",
                status=DownloadStatus.PENDING,
                progress=0.0,
                position=i,
            )
            item.created_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            db_session.add(item)
            db_session.commit()
            manager.start_download(item.id)
            item_ids.append(item.id)

        # At the limit
        assert not manager.can_start_download()

        # Complete one download
        manager.complete_download(item_ids[0], "/downloads/video0.mp4", 1000)

        # Should now be able to start another
        assert manager.can_start_download(), (
            "Should be able to start download after completing one"
        )

    @given(max_concurrent=concurrent_limit_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_failing_download_allows_new_start(
        self,
        db_session,
        max_concurrent: int,
    ):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        After a download fails, can_start_download SHALL return True
        if previously at the limit.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)
        manager.set_max_concurrent(max_concurrent)

        # Add and start downloads up to the limit
        item_ids = []
        for i in range(max_concurrent):
            item = QueueItem(
                id=str(uuid.uuid4()),
                url=f"https://example.com/video{uuid.uuid4()}",
                output_path=f"/downloads/video{uuid.uuid4()}.mp4",
                status=DownloadStatus.PENDING,
                progress=0.0,
                position=i,
            )
            item.created_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            db_session.add(item)
            db_session.commit()
            manager.start_download(item.id)
            item_ids.append(item.id)

        # At the limit
        assert not manager.can_start_download()

        # Fail one download
        manager.fail_download(item_ids[0], "Test error")

        # Should now be able to start another
        assert manager.can_start_download(), (
            "Should be able to start download after one fails"
        )

    @given(max_concurrent=concurrent_limit_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_pausing_download_frees_slot(
        self,
        db_session,
        max_concurrent: int,
    ):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        After pausing a download, can_start_download SHALL return True
        if previously at the limit.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)
        manager.set_max_concurrent(max_concurrent)

        # Add and start downloads up to the limit
        item_ids = []
        for i in range(max_concurrent):
            item = QueueItem(
                id=str(uuid.uuid4()),
                url=f"https://example.com/video{uuid.uuid4()}",
                output_path=f"/downloads/video{uuid.uuid4()}.mp4",
                status=DownloadStatus.PENDING,
                progress=0.0,
                position=i,
            )
            item.created_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            db_session.add(item)
            db_session.commit()
            manager.start_download(item.id)
            item_ids.append(item.id)

        # At the limit
        assert not manager.can_start_download()

        # Pause one download
        manager.pause_download(item_ids[0])

        # Should now be able to start another
        assert manager.can_start_download(), (
            "Should be able to start download after pausing one"
        )

    @given(max_concurrent=concurrent_limit_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_initial_max_concurrent_is_valid(
        self,
        db_session,
        max_concurrent: int,
    ):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        DownloadManager initialized with valid max_concurrent SHALL use that value.
        """
        manager = DownloadManager(
            session_factory=lambda: db_session,
            max_concurrent=max_concurrent,
        )

        assert manager.max_concurrent == max_concurrent

    @pytest.mark.property
    def test_default_max_concurrent_is_valid(self, db_session):
        """
        Feature: farmer-cli-completion, Property 19: Concurrent Download Limit
        Validates: Requirements 4.5

        DownloadManager default max_concurrent SHALL be within valid range.
        """
        manager = DownloadManager(session_factory=lambda: db_session)

        assert 1 <= manager.max_concurrent <= 5
