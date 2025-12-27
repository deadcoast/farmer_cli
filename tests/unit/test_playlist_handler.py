"""
Unit tests for the playlist_handler module.

Tests cover:
- enumerate_playlist with mocked responses
- get_range boundary conditions
- batch download result aggregation
- download_playlist() convenience method

Requirements: 9.1, 9.3
"""

from unittest.mock import MagicMock

import pytest

from farmer_cli.exceptions import DownloadError
from farmer_cli.exceptions import PlaylistError
from farmer_cli.services.playlist_handler import BatchDownloadResult
from farmer_cli.services.playlist_handler import PlaylistHandler
from farmer_cli.services.ytdlp_wrapper import VideoInfo


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_videos():
    """Create sample VideoInfo objects for testing."""
    return [
        VideoInfo(
            url="https://youtube.com/watch?v=vid1",
            title="Video 1",
            video_id="vid1",
            playlist_index=1,
            webpage_url="https://youtube.com/watch?v=vid1",
        ),
        VideoInfo(
            url="https://youtube.com/watch?v=vid2",
            title="Video 2",
            video_id="vid2",
            playlist_index=2,
            webpage_url="https://youtube.com/watch?v=vid2",
        ),
        VideoInfo(
            url="https://youtube.com/watch?v=vid3",
            title="Video 3",
            video_id="vid3",
            playlist_index=3,
            webpage_url="https://youtube.com/watch?v=vid3",
        ),
        VideoInfo(
            url="https://youtube.com/watch?v=vid4",
            title="Video 4",
            video_id="vid4",
            playlist_index=4,
            webpage_url="https://youtube.com/watch?v=vid4",
        ),
        VideoInfo(
            url="https://youtube.com/watch?v=vid5",
            title="Video 5",
            video_id="vid5",
            playlist_index=5,
            webpage_url="https://youtube.com/watch?v=vid5",
        ),
    ]


@pytest.fixture
def mock_ytdlp_wrapper():
    """Create a mock YtdlpWrapper."""
    return MagicMock()


@pytest.fixture
def handler(mock_ytdlp_wrapper):
    """Create a PlaylistHandler with mocked wrapper."""
    return PlaylistHandler(ytdlp_wrapper=mock_ytdlp_wrapper)


# ---------------------------------------------------------------------------
# BatchDownloadResult Tests
# ---------------------------------------------------------------------------


class TestBatchDownloadResult:
    """Tests for BatchDownloadResult dataclass."""

    def test_empty_result(self):
        """Test empty BatchDownloadResult."""
        result = BatchDownloadResult()

        assert result.total == 0
        assert result.success_count == 0
        assert result.failure_count == 0

    def test_result_with_successes(self):
        """Test BatchDownloadResult with successes."""
        result = BatchDownloadResult(
            successes=["/path/to/video1.mp4", "/path/to/video2.mp4"],
        )

        assert result.total == 2
        assert result.success_count == 2
        assert result.failure_count == 0

    def test_result_with_failures(self):
        """Test BatchDownloadResult with failures."""
        result = BatchDownloadResult(
            failures=[
                ("https://example.com/1", "Network error"),
                ("https://example.com/2", "Video unavailable"),
            ],
        )

        assert result.total == 2
        assert result.success_count == 0
        assert result.failure_count == 2

    def test_result_mixed(self):
        """Test BatchDownloadResult with both successes and failures."""
        result = BatchDownloadResult(
            successes=["/path/to/video1.mp4"],
            failures=[("https://example.com/2", "Error")],
        )

        assert result.total == 2
        assert result.success_count == 1
        assert result.failure_count == 1

    def test_summary_no_failures(self):
        """Test summary with no failures."""
        result = BatchDownloadResult(
            successes=["/path/to/video1.mp4", "/path/to/video2.mp4"],
        )

        summary = result.summary()

        assert "Total videos: 2" in summary
        assert "Successful: 2" in summary
        assert "Failed: 0" in summary
        assert "Failed downloads:" not in summary

    def test_summary_with_failures(self):
        """Test summary with failures."""
        result = BatchDownloadResult(
            successes=["/path/to/video1.mp4"],
            failures=[("https://example.com/2", "Network error")],
        )

        summary = result.summary()

        assert "Total videos: 2" in summary
        assert "Successful: 1" in summary
        assert "Failed: 1" in summary
        assert "Failed downloads:" in summary
        assert "Network error" in summary

    def test_summary_truncates_long_urls(self):
        """Test that summary truncates long URLs."""
        long_url = "https://example.com/" + "a" * 100
        result = BatchDownloadResult(
            failures=[(long_url, "Error")],
        )

        summary = result.summary()

        assert "..." in summary


# ---------------------------------------------------------------------------
# PlaylistHandler Initialization Tests
# ---------------------------------------------------------------------------


class TestPlaylistHandlerInit:
    """Tests for PlaylistHandler initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        handler = PlaylistHandler()

        assert handler._ytdlp_wrapper is not None

    def test_init_with_custom_wrapper(self, mock_ytdlp_wrapper):
        """Test initialization with custom wrapper."""
        handler = PlaylistHandler(ytdlp_wrapper=mock_ytdlp_wrapper)

        assert handler._ytdlp_wrapper == mock_ytdlp_wrapper

    def test_ytdlp_wrapper_property(self, handler, mock_ytdlp_wrapper):
        """Test ytdlp_wrapper property."""
        assert handler.ytdlp_wrapper == mock_ytdlp_wrapper


# ---------------------------------------------------------------------------
# enumerate_playlist Tests
# ---------------------------------------------------------------------------


class TestEnumeratePlaylist:
    """Tests for enumerate_playlist method."""

    def test_enumerate_playlist_success(self, handler, mock_ytdlp_wrapper, sample_videos):
        """Test successful playlist enumeration."""
        mock_ytdlp_wrapper.extract_playlist.return_value = sample_videos

        videos = handler.enumerate_playlist("https://youtube.com/playlist?list=test")

        assert len(videos) == 5
        mock_ytdlp_wrapper.extract_playlist.assert_called_once()

    def test_enumerate_playlist_empty_url_raises(self, handler):
        """Test that empty URL raises PlaylistError."""
        with pytest.raises(PlaylistError, match="URL cannot be empty"):
            handler.enumerate_playlist("")

    def test_enumerate_playlist_whitespace_url_raises(self, handler):
        """Test that whitespace URL raises PlaylistError."""
        with pytest.raises(PlaylistError, match="URL cannot be empty"):
            handler.enumerate_playlist("   ")

    def test_enumerate_playlist_empty_result_raises(self, handler, mock_ytdlp_wrapper):
        """Test that empty playlist raises PlaylistError."""
        mock_ytdlp_wrapper.extract_playlist.return_value = []

        with pytest.raises(PlaylistError, match="Playlist is empty"):
            handler.enumerate_playlist("https://youtube.com/playlist?list=empty")

    def test_enumerate_playlist_download_error(self, handler, mock_ytdlp_wrapper):
        """Test handling of DownloadError."""
        mock_ytdlp_wrapper.extract_playlist.side_effect = DownloadError(
            "Video unavailable",
            url="https://youtube.com/playlist?list=test",
        )

        with pytest.raises(PlaylistError, match="Failed to enumerate playlist"):
            handler.enumerate_playlist("https://youtube.com/playlist?list=test")

    def test_enumerate_playlist_unexpected_error(self, handler, mock_ytdlp_wrapper):
        """Test handling of unexpected errors."""
        mock_ytdlp_wrapper.extract_playlist.side_effect = Exception("Unexpected error")

        with pytest.raises(PlaylistError, match="Unexpected error"):
            handler.enumerate_playlist("https://youtube.com/playlist?list=test")


# ---------------------------------------------------------------------------
# get_range Tests
# ---------------------------------------------------------------------------


class TestGetRange:
    """Tests for get_range method."""

    def test_get_range_full_range(self, handler, sample_videos):
        """Test getting full range of videos."""
        selected = handler.get_range(sample_videos, start=1, end=5)

        assert len(selected) == 5

    def test_get_range_partial(self, handler, sample_videos):
        """Test getting partial range."""
        selected = handler.get_range(sample_videos, start=2, end=4)

        assert len(selected) == 3
        assert selected[0].video_id == "vid2"
        assert selected[-1].video_id == "vid4"

    def test_get_range_single_video(self, handler, sample_videos):
        """Test getting single video."""
        selected = handler.get_range(sample_videos, start=3, end=3)

        assert len(selected) == 1
        assert selected[0].video_id == "vid3"

    def test_get_range_first_video(self, handler, sample_videos):
        """Test getting first video."""
        selected = handler.get_range(sample_videos, start=1, end=1)

        assert len(selected) == 1
        assert selected[0].video_id == "vid1"

    def test_get_range_last_video(self, handler, sample_videos):
        """Test getting last video."""
        selected = handler.get_range(sample_videos, start=5, end=5)

        assert len(selected) == 1
        assert selected[0].video_id == "vid5"

    def test_get_range_clamps_end(self, handler, sample_videos):
        """Test that end is clamped to playlist length."""
        selected = handler.get_range(sample_videos, start=3, end=100)

        assert len(selected) == 3  # Videos 3, 4, 5

    def test_get_range_empty_list_raises(self, handler):
        """Test that empty video list raises PlaylistError."""
        with pytest.raises(PlaylistError, match="Video list is empty"):
            handler.get_range([], start=1, end=5)

    def test_get_range_start_less_than_one_raises(self, handler, sample_videos):
        """Test that start < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Start position must be at least 1"):
            handler.get_range(sample_videos, start=0, end=5)

    def test_get_range_end_less_than_start_raises(self, handler, sample_videos):
        """Test that end < start raises ValueError."""
        with pytest.raises(ValueError, match="End position must be greater than or equal to start"):
            handler.get_range(sample_videos, start=5, end=3)

    def test_get_range_start_exceeds_length_raises(self, handler, sample_videos):
        """Test that start > playlist length raises PlaylistError."""
        with pytest.raises(PlaylistError, match="Start position .* exceeds playlist length"):
            handler.get_range(sample_videos, start=10, end=15)


# ---------------------------------------------------------------------------
# download_batch Tests
# ---------------------------------------------------------------------------


class TestDownloadBatch:
    """Tests for download_batch method."""

    def test_download_batch_empty_list(self, handler):
        """Test download_batch with empty list."""
        result = handler.download_batch([], output_dir="/tmp/downloads")

        assert result.total == 0
        assert result.success_count == 0
        assert result.failure_count == 0

    def test_download_batch_all_success(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_batch with all successful downloads."""
        mock_ytdlp_wrapper.download.side_effect = [
            str(tmp_path / f"video{i}.mp4") for i in range(len(sample_videos))
        ]

        result = handler.download_batch(sample_videos, output_dir=tmp_path)

        assert result.success_count == 5
        assert result.failure_count == 0

    def test_download_batch_all_failures(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_batch with all failed downloads."""
        mock_ytdlp_wrapper.download.side_effect = DownloadError("Network error")

        result = handler.download_batch(sample_videos, output_dir=tmp_path)

        assert result.success_count == 0
        assert result.failure_count == 5

    def test_download_batch_mixed_results(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_batch with mixed success/failure."""
        def mock_download(url, output_path, format_id=None):
            if "vid1" in url or "vid3" in url:
                return str(tmp_path / "video.mp4")
            raise DownloadError("Failed")

        mock_ytdlp_wrapper.download.side_effect = mock_download

        result = handler.download_batch(sample_videos, output_dir=tmp_path)

        assert result.success_count == 2
        assert result.failure_count == 3

    def test_download_batch_clamps_max_concurrent(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test that max_concurrent is clamped to valid range."""
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")

        # Should not raise even with invalid values
        result = handler.download_batch(sample_videos, output_dir=tmp_path, max_concurrent=0)
        assert result.success_count == 5

        result = handler.download_batch(sample_videos, output_dir=tmp_path, max_concurrent=100)
        assert result.success_count == 5

    def test_download_batch_with_format_id(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_batch passes format_id to wrapper."""
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")

        handler.download_batch(sample_videos, output_dir=tmp_path, format_id="22")

        # Check that format_id was passed
        for call in mock_ytdlp_wrapper.download.call_args_list:
            assert call.kwargs.get("format_id") == "22"

    def test_download_batch_creates_output_dir(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test that download_batch creates output directory."""
        new_dir = tmp_path / "new_downloads"
        mock_ytdlp_wrapper.download.return_value = str(new_dir / "video.mp4")

        handler.download_batch(sample_videos[:1], output_dir=new_dir)

        assert new_dir.exists()

    def test_download_batch_invalid_output_dir_raises(self, handler, sample_videos):
        """Test that invalid output directory raises PlaylistError."""
        # Use a path that can't be created (e.g., inside a file)
        with pytest.raises(PlaylistError, match="Cannot create output directory"):
            handler.download_batch(sample_videos, output_dir="/dev/null/invalid")

    def test_download_batch_with_progress_callback(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_batch calls progress callback."""
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")
        progress_calls = []

        def progress_callback(url, current, total):
            progress_calls.append((url, current, total))

        handler.download_batch(
            sample_videos,
            output_dir=tmp_path,
            progress_callback=progress_callback,
        )

        assert len(progress_calls) == 5
        # All calls should have total=5
        assert all(call[2] == 5 for call in progress_calls)

    def test_download_batch_handles_callback_error(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test that callback errors don't stop downloads."""
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")

        def bad_callback(url, current, total):
            raise Exception("Callback error")

        # Should not raise
        result = handler.download_batch(
            sample_videos,
            output_dir=tmp_path,
            progress_callback=bad_callback,
        )

        assert result.success_count == 5


# ---------------------------------------------------------------------------
# is_playlist and get_playlist_info Tests
# ---------------------------------------------------------------------------


class TestPlaylistInfo:
    """Tests for is_playlist and get_playlist_info methods."""

    def test_is_playlist_true(self, handler, mock_ytdlp_wrapper):
        """Test is_playlist returns True for playlist URL."""
        mock_ytdlp_wrapper.is_playlist.return_value = True

        result = handler.is_playlist("https://youtube.com/playlist?list=test")

        assert result is True

    def test_is_playlist_false(self, handler, mock_ytdlp_wrapper):
        """Test is_playlist returns False for non-playlist URL."""
        mock_ytdlp_wrapper.is_playlist.return_value = False

        result = handler.is_playlist("https://youtube.com/watch?v=test")

        assert result is False

    def test_is_playlist_empty_url(self, handler):
        """Test is_playlist with empty URL."""
        result = handler.is_playlist("")

        assert result is False

    def test_is_playlist_whitespace_url(self, handler):
        """Test is_playlist with whitespace URL."""
        result = handler.is_playlist("   ")

        assert result is False

    def test_get_playlist_info_success(self, handler, mock_ytdlp_wrapper):
        """Test successful get_playlist_info."""
        mock_ytdlp_wrapper.get_playlist_info.return_value = {
            "title": "Test Playlist",
            "uploader": "Test Channel",
            "count": 10,
        }

        info = handler.get_playlist_info("https://youtube.com/playlist?list=test")

        assert info["title"] == "Test Playlist"
        assert info["count"] == 10

    def test_get_playlist_info_empty_url_raises(self, handler):
        """Test that empty URL raises PlaylistError."""
        with pytest.raises(PlaylistError, match="URL cannot be empty"):
            handler.get_playlist_info("")

    def test_get_playlist_info_download_error(self, handler, mock_ytdlp_wrapper):
        """Test handling of DownloadError."""
        mock_ytdlp_wrapper.get_playlist_info.side_effect = DownloadError(
            "Not a playlist",
            url="https://youtube.com/watch?v=test",
        )

        with pytest.raises(PlaylistError, match="Failed to get playlist info"):
            handler.get_playlist_info("https://youtube.com/watch?v=test")


# ---------------------------------------------------------------------------
# download_playlist Tests
# ---------------------------------------------------------------------------


class TestDownloadPlaylist:
    """Tests for download_playlist convenience method."""

    def test_download_playlist_full(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_playlist downloads all videos."""
        mock_ytdlp_wrapper.extract_playlist.return_value = sample_videos
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")

        result = handler.download_playlist(
            url="https://youtube.com/playlist?list=test",
            output_dir=tmp_path,
        )

        assert result.success_count == 5

    def test_download_playlist_with_range(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_playlist with range selection."""
        mock_ytdlp_wrapper.extract_playlist.return_value = sample_videos
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")

        result = handler.download_playlist(
            url="https://youtube.com/playlist?list=test",
            output_dir=tmp_path,
            start=2,
            end=4,
        )

        assert result.success_count == 3

    def test_download_playlist_with_start_only(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_playlist with only start specified."""
        mock_ytdlp_wrapper.extract_playlist.return_value = sample_videos
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")

        result = handler.download_playlist(
            url="https://youtube.com/playlist?list=test",
            output_dir=tmp_path,
            start=3,
        )

        assert result.success_count == 3  # Videos 3, 4, 5

    def test_download_playlist_with_end_only(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_playlist with only end specified."""
        mock_ytdlp_wrapper.extract_playlist.return_value = sample_videos
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")

        result = handler.download_playlist(
            url="https://youtube.com/playlist?list=test",
            output_dir=tmp_path,
            end=2,
        )

        assert result.success_count == 2  # Videos 1, 2

    def test_download_playlist_with_format(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_playlist passes format_id."""
        mock_ytdlp_wrapper.extract_playlist.return_value = sample_videos
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")

        handler.download_playlist(
            url="https://youtube.com/playlist?list=test",
            output_dir=tmp_path,
            format_id="22",
        )

        # Verify format_id was passed
        for call in mock_ytdlp_wrapper.download.call_args_list:
            assert call.kwargs.get("format_id") == "22"

    def test_download_playlist_with_progress_callback(self, handler, mock_ytdlp_wrapper, sample_videos, tmp_path):
        """Test download_playlist with progress callback."""
        mock_ytdlp_wrapper.extract_playlist.return_value = sample_videos
        mock_ytdlp_wrapper.download.return_value = str(tmp_path / "video.mp4")
        progress_calls = []

        def progress_callback(url, current, total):
            progress_calls.append((url, current, total))

        handler.download_playlist(
            url="https://youtube.com/playlist?list=test",
            output_dir=tmp_path,
            progress_callback=progress_callback,
        )

        assert len(progress_calls) == 5

    def test_download_playlist_enumeration_error(self, handler, mock_ytdlp_wrapper, tmp_path):
        """Test download_playlist handles enumeration errors."""
        mock_ytdlp_wrapper.extract_playlist.side_effect = DownloadError("Playlist unavailable")

        with pytest.raises(PlaylistError):
            handler.download_playlist(
                url="https://youtube.com/playlist?list=test",
                output_dir=tmp_path,
            )
