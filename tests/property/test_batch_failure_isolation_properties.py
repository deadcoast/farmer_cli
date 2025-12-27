"""
Property-based tests for batch failure isolation in PlaylistHandler.

Feature: farmer-cli-completion
Property 20: Batch Failure Isolation
Validates: Requirements 3.4

For any batch download where some items fail, the successful downloads SHALL
complete and be recorded, independent of the failures.
"""

import string
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st

from farmer_cli.exceptions import DownloadError
from farmer_cli.services.playlist_handler import BatchDownloadResult
from farmer_cli.services.playlist_handler import PlaylistHandler
from farmer_cli.services.ytdlp_wrapper import VideoInfo


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid video titles
title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " -_",
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip())

# Strategy for generating valid URLs
url_strategy = st.uuids().map(lambda u: f"https://example.com/video/{u}")

# Strategy for generating video IDs
video_id_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=8,
    max_size=16,
)


def create_video_info(url: str, title: str, video_id: str | None = None) -> VideoInfo:
    """Create a VideoInfo object for testing."""
    return VideoInfo(
        url=url,
        title=title,
        video_id=video_id or str(uuid.uuid4())[:11],
        webpage_url=url,
    )


# Strategy for generating a list of VideoInfo objects
@st.composite
def video_list_strategy(draw, min_size: int = 2, max_size: int = 10):
    """Generate a list of VideoInfo objects."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    videos = []
    for i in range(size):
        url = draw(url_strategy)
        title = draw(title_strategy)
        video_id = draw(video_id_strategy)
        videos.append(create_video_info(url, title, video_id))
    return videos


# Strategy for generating failure indices
@st.composite
def failure_indices_strategy(draw, max_videos: int):
    """Generate a set of indices that should fail."""
    if max_videos <= 1:
        return set()
    # Generate between 1 and max_videos-1 failures (at least one success)
    num_failures = draw(st.integers(min_value=1, max_value=max(1, max_videos - 1)))
    indices = draw(
        st.lists(
            st.integers(min_value=0, max_value=max_videos - 1),
            min_size=num_failures,
            max_size=num_failures,
            unique=True,
        )
    )
    return set(indices)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestBatchFailureIsolation:
    """
    Property 20: Batch Failure Isolation

    For any batch download where some items fail, the successful downloads SHALL
    complete and be recorded in history, independent of the failures.

    **Validates: Requirements 3.4**
    """

    @given(
        videos=video_list_strategy(min_size=2, max_size=8),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_successful_downloads_complete_despite_failures(
        self,
        tmp_path: Path,
        videos: list[VideoInfo],
    ):
        """
        Feature: farmer-cli-completion, Property 20: Batch Failure Isolation
        Validates: Requirements 3.4

        For any batch with mixed success/failure, successful downloads SHALL complete.
        """
        # Determine which videos should fail (at least one success, at least one failure)
        num_videos = len(videos)
        if num_videos < 2:
            return  # Need at least 2 videos for this test

        # Make first half fail, second half succeed
        failure_indices = set(range(num_videos // 2))
        success_indices = set(range(num_videos // 2, num_videos))

        # Create mock wrapper
        mock_wrapper = MagicMock()

        def mock_download(url: str, output_path: Any, format_id: str | None = None) -> str:
            # Find which video this URL belongs to
            for idx, video in enumerate(videos):
                if video.url == url or video.webpage_url == url:
                    if idx in failure_indices:
                        raise DownloadError(f"Simulated failure for video {idx}", url=url)
                    return str(output_path / f"video_{idx}.mp4")
            raise DownloadError("Unknown URL", url=url)

        mock_wrapper.download.side_effect = mock_download

        # Create handler with mock
        handler = PlaylistHandler(ytdlp_wrapper=mock_wrapper)

        # Execute batch download
        result = handler.download_batch(
            videos=videos,
            output_dir=tmp_path,
            max_concurrent=2,
        )

        # Verify results
        assert result.success_count == len(success_indices), (
            f"Expected {len(success_indices)} successes, got {result.success_count}"
        )
        assert result.failure_count == len(failure_indices), (
            f"Expected {len(failure_indices)} failures, got {result.failure_count}"
        )
        assert result.total == num_videos, (
            f"Total should be {num_videos}, got {result.total}"
        )

    @given(
        videos=video_list_strategy(min_size=3, max_size=6),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_failures_do_not_affect_other_downloads(
        self,
        tmp_path: Path,
        videos: list[VideoInfo],
    ):
        """
        Feature: farmer-cli-completion, Property 20: Batch Failure Isolation
        Validates: Requirements 3.4

        Individual failures SHALL NOT prevent other downloads from completing.
        """
        num_videos = len(videos)
        if num_videos < 3:
            return

        # Only the middle video fails
        failure_index = num_videos // 2

        mock_wrapper = MagicMock()
        downloaded_urls = []

        def mock_download(url: str, output_path: Any, format_id: str | None = None) -> str:
            for idx, video in enumerate(videos):
                if video.url == url or video.webpage_url == url:
                    if idx == failure_index:
                        raise DownloadError(f"Simulated failure", url=url)
                    downloaded_urls.append(url)
                    return str(output_path / f"video_{idx}.mp4")
            raise DownloadError("Unknown URL", url=url)

        mock_wrapper.download.side_effect = mock_download

        handler = PlaylistHandler(ytdlp_wrapper=mock_wrapper)

        result = handler.download_batch(
            videos=videos,
            output_dir=tmp_path,
            max_concurrent=1,  # Sequential to ensure order
        )

        # All videos except the failing one should succeed
        expected_successes = num_videos - 1
        assert result.success_count == expected_successes, (
            f"Expected {expected_successes} successes, got {result.success_count}"
        )
        assert result.failure_count == 1, (
            f"Expected 1 failure, got {result.failure_count}"
        )

    @given(
        videos=video_list_strategy(min_size=2, max_size=5),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_batch_result_contains_all_outcomes(
        self,
        tmp_path: Path,
        videos: list[VideoInfo],
    ):
        """
        Feature: farmer-cli-completion, Property 20: Batch Failure Isolation
        Validates: Requirements 3.4

        BatchDownloadResult SHALL contain entries for all attempted downloads.
        """
        num_videos = len(videos)

        # Alternate success/failure
        failure_indices = set(range(0, num_videos, 2))

        mock_wrapper = MagicMock()

        def mock_download(url: str, output_path: Any, format_id: str | None = None) -> str:
            for idx, video in enumerate(videos):
                if video.url == url or video.webpage_url == url:
                    if idx in failure_indices:
                        raise DownloadError(f"Simulated failure", url=url)
                    return str(output_path / f"video_{idx}.mp4")
            raise DownloadError("Unknown URL", url=url)

        mock_wrapper.download.side_effect = mock_download

        handler = PlaylistHandler(ytdlp_wrapper=mock_wrapper)

        result = handler.download_batch(
            videos=videos,
            output_dir=tmp_path,
            max_concurrent=2,
        )

        # Total outcomes should equal total videos
        assert result.total == num_videos, (
            f"Total outcomes ({result.total}) should equal total videos ({num_videos})"
        )
        assert result.success_count + result.failure_count == num_videos, (
            "Sum of successes and failures should equal total videos"
        )

    @given(
        videos=video_list_strategy(min_size=2, max_size=5),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_failure_urls_are_recorded(
        self,
        tmp_path: Path,
        videos: list[VideoInfo],
    ):
        """
        Feature: farmer-cli-completion, Property 20: Batch Failure Isolation
        Validates: Requirements 3.4

        Failed download URLs SHALL be recorded in the failures list.
        """
        num_videos = len(videos)
        if num_videos < 2:
            return

        # First video fails
        failure_index = 0
        expected_failure_url = videos[failure_index].webpage_url or videos[failure_index].url

        mock_wrapper = MagicMock()

        def mock_download(url: str, output_path: Any, format_id: str | None = None) -> str:
            for idx, video in enumerate(videos):
                if video.url == url or video.webpage_url == url:
                    if idx == failure_index:
                        raise DownloadError("Simulated failure", url=url)
                    return str(output_path / f"video_{idx}.mp4")
            raise DownloadError("Unknown URL", url=url)

        mock_wrapper.download.side_effect = mock_download

        handler = PlaylistHandler(ytdlp_wrapper=mock_wrapper)

        result = handler.download_batch(
            videos=videos,
            output_dir=tmp_path,
            max_concurrent=1,
        )

        # Check that the failure URL is recorded
        failure_urls = [url for url, _ in result.failures]
        assert expected_failure_url in failure_urls, (
            f"Expected failure URL {expected_failure_url} not found in failures"
        )

    @given(
        videos=video_list_strategy(min_size=2, max_size=5),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_success_paths_are_recorded(
        self,
        tmp_path: Path,
        videos: list[VideoInfo],
    ):
        """
        Feature: farmer-cli-completion, Property 20: Batch Failure Isolation
        Validates: Requirements 3.4

        Successful download file paths SHALL be recorded in the successes list.
        """
        num_videos = len(videos)
        if num_videos < 2:
            return

        # Last video fails, others succeed
        failure_index = num_videos - 1

        mock_wrapper = MagicMock()

        def mock_download(url: str, output_path: Any, format_id: str | None = None) -> str:
            for idx, video in enumerate(videos):
                if video.url == url or video.webpage_url == url:
                    if idx == failure_index:
                        raise DownloadError("Simulated failure", url=url)
                    return str(output_path / f"video_{idx}.mp4")
            raise DownloadError("Unknown URL", url=url)

        mock_wrapper.download.side_effect = mock_download

        handler = PlaylistHandler(ytdlp_wrapper=mock_wrapper)

        result = handler.download_batch(
            videos=videos,
            output_dir=tmp_path,
            max_concurrent=1,
        )

        # Check that success paths are recorded
        assert len(result.successes) == num_videos - 1, (
            f"Expected {num_videos - 1} successes, got {len(result.successes)}"
        )
        for path in result.successes:
            assert path.endswith(".mp4"), f"Success path should end with .mp4: {path}"

    @pytest.mark.property
    def test_empty_batch_returns_empty_result(self, tmp_path: Path):
        """
        Feature: farmer-cli-completion, Property 20: Batch Failure Isolation
        Validates: Requirements 3.4

        Empty batch SHALL return empty result without errors.
        """
        handler = PlaylistHandler()

        result = handler.download_batch(
            videos=[],
            output_dir=tmp_path,
            max_concurrent=2,
        )

        assert result.total == 0
        assert result.success_count == 0
        assert result.failure_count == 0
        assert len(result.successes) == 0
        assert len(result.failures) == 0

    @given(
        videos=video_list_strategy(min_size=2, max_size=4),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_summary_report_includes_failures(
        self,
        tmp_path: Path,
        videos: list[VideoInfo],
    ):
        """
        Feature: farmer-cli-completion, Property 20: Batch Failure Isolation
        Validates: Requirements 3.4

        Summary report SHALL include information about failed downloads.
        """
        num_videos = len(videos)
        if num_videos < 2:
            return

        # First video fails
        failure_index = 0

        mock_wrapper = MagicMock()

        def mock_download(url: str, output_path: Any, format_id: str | None = None) -> str:
            for idx, video in enumerate(videos):
                if video.url == url or video.webpage_url == url:
                    if idx == failure_index:
                        raise DownloadError("Test error message", url=url)
                    return str(output_path / f"video_{idx}.mp4")
            raise DownloadError("Unknown URL", url=url)

        mock_wrapper.download.side_effect = mock_download

        handler = PlaylistHandler(ytdlp_wrapper=mock_wrapper)

        result = handler.download_batch(
            videos=videos,
            output_dir=tmp_path,
            max_concurrent=1,
        )

        summary = result.summary()

        # Verify summary contains key information
        assert "Batch Download Summary" in summary
        assert f"Total videos: {num_videos}" in summary
        assert f"Successful: {num_videos - 1}" in summary
        assert "Failed: 1" in summary
        assert "Failed downloads:" in summary
