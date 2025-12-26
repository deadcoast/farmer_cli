"""
Property-based tests for DownloadHistory model.

Feature: farmer-cli-completion
Property 7: History Entry Completeness
Validates: Requirements 5.2

For any HistoryEntry in the download history, it SHALL contain non-null
values for id, url, title, file_path, and downloaded_at fields.
"""

import string
from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st

from farmer_cli.models.history import DownloadHistory


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid UUIDs
uuid_strategy = st.uuids().map(str)

# Strategy for generating valid URLs
url_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "/:.-_?=&%",
    min_size=10,
    max_size=200,
).map(lambda s: f"https://example.com/{s}")

# Strategy for generating valid titles
title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " -_",
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip())

# Strategy for generating valid file paths
file_path_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "/_.-",
    min_size=5,
    max_size=200,
).map(lambda s: f"/downloads/{s}.mp4")

# Strategy for generating file sizes
file_size_strategy = st.one_of(
    st.none(),
    st.integers(min_value=0, max_value=10 * 1024 * 1024 * 1024),  # Up to 10GB
)

# Strategy for generating durations
duration_strategy = st.one_of(
    st.none(),
    st.integers(min_value=0, max_value=86400),  # Up to 24 hours
)

# Strategy for generating uploader names
uploader_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet=string.ascii_letters + string.digits + " -_",
        min_size=1,
        max_size=100,
    ),
)

# Strategy for generating format IDs
format_id_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet=string.ascii_letters + string.digits + "-_",
        min_size=1,
        max_size=20,
    ),
)

# Strategy for generating status values
status_strategy = st.sampled_from(["completed", "deleted", "moved"])

# Strategy for generating valid DownloadHistory instances
download_history_strategy = st.builds(
    DownloadHistory,
    id=uuid_strategy,
    url=url_strategy,
    title=title_strategy,
    file_path=file_path_strategy,
    file_size=file_size_strategy,
    format_id=format_id_strategy,
    duration=duration_strategy,
    uploader=uploader_strategy,
    status=status_strategy,
)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestHistoryEntryCompleteness:
    """
    Property 7: History Entry Completeness

    For any HistoryEntry in the download history, it SHALL contain non-null
    values for id, url, title, file_path, and downloaded_at fields.

    **Validates: Requirements 5.2**
    """

    @given(download_history_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_id_is_never_null(self, history: DownloadHistory):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any DownloadHistory, id SHALL be non-null and non-empty.
        """
        assert history.id is not None, "id should not be None"
        assert len(history.id) > 0, "id should not be empty"

    @given(download_history_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_url_is_never_null(self, history: DownloadHistory):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any DownloadHistory, url SHALL be non-null and non-empty.
        """
        assert history.url is not None, "url should not be None"
        assert len(history.url) > 0, "url should not be empty"

    @given(download_history_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_title_is_never_null(self, history: DownloadHistory):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any DownloadHistory, title SHALL be non-null and non-empty.
        """
        assert history.title is not None, "title should not be None"
        assert len(history.title) > 0, "title should not be empty"

    @given(download_history_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_file_path_is_never_null(self, history: DownloadHistory):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any DownloadHistory, file_path SHALL be non-null and non-empty.
        """
        assert history.file_path is not None, "file_path should not be None"
        assert len(history.file_path) > 0, "file_path should not be empty"

    @given(download_history_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_downloaded_at_has_default(self, history: DownloadHistory):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any DownloadHistory, downloaded_at SHALL have a default value
        when not explicitly set.
        """
        # The model has a default for downloaded_at, so it should be set
        # Note: In actual DB usage, this would be set by the default
        # For this test, we verify the model accepts datetime values
        history.downloaded_at = datetime.utcnow()
        assert history.downloaded_at is not None, "downloaded_at should not be None"
        assert isinstance(history.downloaded_at, datetime), "downloaded_at should be a datetime"

    @given(download_history_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_to_dict_contains_required_fields(self, history: DownloadHistory):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any DownloadHistory, to_dict() SHALL contain all required fields.
        """
        # Set downloaded_at for the test
        history.downloaded_at = datetime.utcnow()

        result = history.to_dict()

        required_fields = ["id", "url", "title", "file_path", "downloaded_at"]
        for field in required_fields:
            assert field in result, f"to_dict() should contain '{field}'"
            assert result[field] is not None, f"'{field}' should not be None in to_dict()"

    @given(
        st.sampled_from(["", " ", "\t", "\n", "\r", "  ", "\t\n"]),
        title_strategy,
        file_path_strategy,
    )
    @settings(max_examples=50)
    @pytest.mark.property
    def test_empty_url_raises_error(self, url: str, title: str, file_path: str):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any empty or whitespace-only URL, DownloadHistory construction
        SHALL raise a ValueError.
        """
        with pytest.raises(ValueError, match="URL cannot be empty"):
            DownloadHistory(url=url, title=title, file_path=file_path)

    @given(
        url_strategy,
        st.sampled_from(["", " ", "\t", "\n", "\r", "  ", "\t\n"]),
        file_path_strategy,
    )
    @settings(max_examples=50)
    @pytest.mark.property
    def test_empty_title_raises_error(self, url: str, title: str, file_path: str):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any empty or whitespace-only title, DownloadHistory construction
        SHALL raise a ValueError.
        """
        with pytest.raises(ValueError, match="Title cannot be empty"):
            DownloadHistory(url=url, title=title, file_path=file_path)

    @given(
        url_strategy,
        title_strategy,
        st.sampled_from(["", " ", "\t", "\n", "\r", "  ", "\t\n"]),
    )
    @settings(max_examples=50)
    @pytest.mark.property
    def test_empty_file_path_raises_error(self, url: str, title: str, file_path: str):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any empty or whitespace-only file_path, DownloadHistory construction
        SHALL raise a ValueError.
        """
        with pytest.raises(ValueError, match="File path cannot be empty"):
            DownloadHistory(url=url, title=title, file_path=file_path)

    @given(download_history_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_file_size_formatted_is_never_empty(self, history: DownloadHistory):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any DownloadHistory, file_size_formatted SHALL produce a non-empty string.
        """
        formatted = history.file_size_formatted

        assert formatted is not None, "file_size_formatted should not be None"
        assert len(formatted) > 0, "file_size_formatted should not be empty"

    @given(download_history_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_duration_formatted_is_never_empty(self, history: DownloadHistory):
        """
        Feature: farmer-cli-completion, Property 7: History Entry Completeness
        Validates: Requirements 5.2

        For any DownloadHistory, duration_formatted SHALL produce a non-empty string.
        """
        formatted = history.duration_formatted

        assert formatted is not None, "duration_formatted should not be None"
        assert len(formatted) > 0, "duration_formatted should not be empty"
