"""
Property-based tests for duplicate detection in DownloadManager.

Feature: farmer-cli-completion
Property 13: Duplicate Detection Accuracy
Validates: Requirements 5.3

For any URL that exists in the download history, the check_duplicate function
SHALL return the matching HistoryEntry.
"""

import string
import uuid
from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st

from farmer_cli.models.history import DownloadHistory
from farmer_cli.services.download_manager import DownloadManager
from farmer_cli.services.download_manager import HistoryEntry


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid URLs with unique suffix
url_strategy = st.uuids().map(lambda u: f"https://example.com/video/{u}")

# Strategy for generating valid titles
title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " -_",
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip())

# Strategy for generating valid file paths with unique suffix
file_path_strategy = st.uuids().map(lambda u: f"/downloads/{u}.mp4")

# Strategy for generating file sizes
file_size_strategy = st.one_of(
    st.none(),
    st.integers(min_value=1, max_value=10_000_000_000),
)

# Strategy for generating durations
duration_strategy = st.one_of(
    st.none(),
    st.integers(min_value=1, max_value=86400),
)

# Strategy for generating uploader names
uploader_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet=string.ascii_letters + string.digits + " -_",
        min_size=1,
        max_size=50,
    ).filter(lambda s: s.strip()),
)


# ---------------------------------------------------------------------------
# Helper function to clean database
# ---------------------------------------------------------------------------

def clean_history(session):
    """Clean all history entries from the database."""
    session.query(DownloadHistory).delete()
    session.commit()


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestDuplicateDetectionAccuracy:
    """
    Property 13: Duplicate Detection Accuracy

    For any URL that exists in the download history, the check_duplicate function
    SHALL return the matching HistoryEntry.

    **Validates: Requirements 5.3**
    """

    @given(
        url=url_strategy,
        title=title_strategy,
        file_path=file_path_strategy,
        file_size=file_size_strategy,
        duration=duration_strategy,
        uploader=uploader_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_check_duplicate_returns_entry_for_existing_url(
        self,
        db_session,
        url: str,
        title: str,
        file_path: str,
        file_size: int | None,
        duration: int | None,
        uploader: str | None,
    ):
        """
        Feature: farmer-cli-completion, Property 13: Duplicate Detection Accuracy
        Validates: Requirements 5.3

        For any URL added to history, check_duplicate SHALL return a matching entry.
        """
        # Clean database before each iteration
        clean_history(db_session)

        # Create a download manager with the test session
        manager = DownloadManager(session_factory=lambda: db_session)

        # Add entry to history
        history_entry = DownloadHistory(
            id=str(uuid.uuid4()),
            url=url,
            title=title,
            file_path=file_path,
            file_size=file_size,
            duration=duration,
            uploader=uploader,
            downloaded_at=datetime.utcnow(),
            status="completed",
        )
        db_session.add(history_entry)
        db_session.commit()

        # Check for duplicate
        result = manager.check_duplicate(url)

        # Verify result
        assert result is not None, f"check_duplicate should find entry for URL: {url}"
        assert result.url == url, "Returned entry should have matching URL"
        # Note: title may be stripped by the model validator
        assert result.title == title.strip() if title else title, "Returned entry should have matching title"
        assert result.file_path == file_path, "Returned entry should have matching file_path"

    @given(
        url=url_strategy,
        other_url=url_strategy,
        title=title_strategy,
        file_path=file_path_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_check_duplicate_returns_none_for_nonexistent_url(
        self,
        db_session,
        url: str,
        other_url: str,
        title: str,
        file_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 13: Duplicate Detection Accuracy
        Validates: Requirements 5.3

        For any URL NOT in history, check_duplicate SHALL return None.
        """
        # Skip if URLs happen to be the same
        if url == other_url:
            return

        # Clean database before each iteration
        clean_history(db_session)

        # Create a download manager with the test session
        manager = DownloadManager(session_factory=lambda: db_session)

        # Add a different URL to history
        history_entry = DownloadHistory(
            id=str(uuid.uuid4()),
            url=other_url,
            title=title,
            file_path=file_path,
            downloaded_at=datetime.utcnow(),
            status="completed",
        )
        db_session.add(history_entry)
        db_session.commit()

        # Check for the URL that was NOT added
        result = manager.check_duplicate(url)

        # Verify result is None
        assert result is None, f"check_duplicate should return None for non-existent URL: {url}"

    @given(url=url_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_check_duplicate_returns_none_for_empty_history(
        self,
        db_session,
        url: str,
    ):
        """
        Feature: farmer-cli-completion, Property 13: Duplicate Detection Accuracy
        Validates: Requirements 5.3

        For any URL when history is empty, check_duplicate SHALL return None.
        """
        # Clean database before each iteration
        clean_history(db_session)

        # Create a download manager with the test session
        manager = DownloadManager(session_factory=lambda: db_session)

        # Check for duplicate with empty history
        result = manager.check_duplicate(url)

        # Verify result is None
        assert result is None, "check_duplicate should return None when history is empty"

    @given(
        url=url_strategy,
        title=title_strategy,
        file_path=file_path_strategy,
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_check_duplicate_returns_most_recent_entry(
        self,
        db_session,
        url: str,
        title: str,
        file_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 13: Duplicate Detection Accuracy
        Validates: Requirements 5.3

        For any URL with multiple history entries, check_duplicate SHALL return
        the most recent entry.
        """
        # Clean database before each iteration
        clean_history(db_session)

        # Create a download manager with the test session
        manager = DownloadManager(session_factory=lambda: db_session)

        # Add multiple entries for the same URL
        older_entry = DownloadHistory(
            id=str(uuid.uuid4()),
            url=url,
            title="Older Title",
            file_path="/old/path.mp4",
            downloaded_at=datetime(2023, 1, 1, 12, 0, 0),
            status="completed",
        )
        db_session.add(older_entry)

        newer_entry = DownloadHistory(
            id=str(uuid.uuid4()),
            url=url,
            title=title,
            file_path=file_path,
            downloaded_at=datetime(2024, 1, 1, 12, 0, 0),
            status="completed",
        )
        db_session.add(newer_entry)
        db_session.commit()

        # Check for duplicate
        result = manager.check_duplicate(url)

        # Verify result is the newer entry
        assert result is not None, "check_duplicate should find entry"
        assert result.title == title, "Should return the most recent entry"
        assert result.file_path == file_path, "Should return the most recent entry"

    @pytest.mark.property
    def test_check_duplicate_handles_empty_url(self, db_session):
        """
        Feature: farmer-cli-completion, Property 13: Duplicate Detection Accuracy
        Validates: Requirements 5.3

        For empty or whitespace-only URLs, check_duplicate SHALL return None.
        """
        manager = DownloadManager(session_factory=lambda: db_session)

        # Test empty string
        assert manager.check_duplicate("") is None
        assert manager.check_duplicate("   ") is None
        assert manager.check_duplicate("\t\n") is None

    @given(
        url=url_strategy,
        title=title_strategy,
        file_path=file_path_strategy,
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_check_duplicate_result_is_history_entry(
        self,
        db_session,
        url: str,
        title: str,
        file_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 13: Duplicate Detection Accuracy
        Validates: Requirements 5.3

        For any matching URL, check_duplicate SHALL return a HistoryEntry instance.
        """
        # Clean database before each iteration
        clean_history(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)

        # Add entry to history
        history_entry = DownloadHistory(
            id=str(uuid.uuid4()),
            url=url,
            title=title,
            file_path=file_path,
            downloaded_at=datetime.utcnow(),
            status="completed",
        )
        db_session.add(history_entry)
        db_session.commit()

        # Check for duplicate
        result = manager.check_duplicate(url)

        # Verify result type
        assert isinstance(result, HistoryEntry), "Result should be a HistoryEntry instance"
        assert hasattr(result, "id"), "HistoryEntry should have id attribute"
        assert hasattr(result, "url"), "HistoryEntry should have url attribute"
        assert hasattr(result, "title"), "HistoryEntry should have title attribute"
        assert hasattr(result, "file_path"), "HistoryEntry should have file_path attribute"
        assert hasattr(result, "downloaded_at"), "HistoryEntry should have downloaded_at attribute"
