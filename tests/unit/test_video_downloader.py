"""
Unit tests for the video_downloader feature module.

Tests cover:
- VideoDownloaderFeature initialization
- Helper methods (_format_filesize, _sanitize_filename)
- _get_default_output_path
- _get_playlist_selection logic
- _batch_progress_callback

Requirements: 9.1, 9.3
"""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from farmer_cli.features.video_downloader import VIDEO_DOWNLOADER_OPTIONS
from farmer_cli.features.video_downloader import VideoDownloaderFeature
from farmer_cli.services.ytdlp_wrapper import VideoFormat
from farmer_cli.services.ytdlp_wrapper import VideoInfo


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_preferences_service():
    """Create a mock preferences service."""
    service = MagicMock()
    service.get.return_value = None
    return service


@pytest.fixture
def mock_get_session():
    """Create a mock session factory."""
    return MagicMock()


@pytest.fixture
def feature(mock_preferences_service, mock_get_session):
    """Create a VideoDownloaderFeature with mocked dependencies."""
    with patch("farmer_cli.features.video_downloader.get_session", mock_get_session):
        return VideoDownloaderFeature(preferences_service=mock_preferences_service)


@pytest.fixture
def sample_video_formats():
    """Create sample video formats for testing."""
    return [
        VideoFormat(
            format_id="22",
            extension="mp4",
            resolution="1280x720",
            filesize=50_000_000,
            vcodec="avc1",
            acodec="mp4a",
        ),
        VideoFormat(
            format_id="18",
            extension="mp4",
            resolution="640x360",
            filesize=20_000_000,
            vcodec="avc1",
            acodec="mp4a",
        ),
        VideoFormat(
            format_id="140",
            extension="m4a",
            resolution=None,
            filesize=5_000_000,
            vcodec=None,
            acodec="mp4a",
            abr=128.0,
        ),
    ]


@pytest.fixture
def sample_video_info(sample_video_formats):
    """Create sample VideoInfo for testing."""
    return VideoInfo(
        url="https://youtube.com/watch?v=test123",
        title="Test Video Title",
        video_id="test123",
        uploader="Test Channel",
        duration=300,
        view_count=1000000,
        formats=sample_video_formats,
        webpage_url="https://youtube.com/watch?v=test123",
    )


# ---------------------------------------------------------------------------
# VideoDownloaderFeature Initialization Tests
# ---------------------------------------------------------------------------


class TestVideoDownloaderFeatureInit:
    """Tests for VideoDownloaderFeature initialization."""

    def test_init_with_defaults(self, mock_get_session):
        """Test initialization with default values."""
        with patch("farmer_cli.features.video_downloader.get_session", mock_get_session):
            feature = VideoDownloaderFeature()

        assert feature.name == "Video Downloader"
        assert feature.description == "Download videos from various platforms"

    def test_init_with_custom_preferences(self, mock_preferences_service, mock_get_session):
        """Test initialization with custom preferences service."""
        with patch("farmer_cli.features.video_downloader.get_session", mock_get_session):
            feature = VideoDownloaderFeature(preferences_service=mock_preferences_service)

        assert feature._preferences_service == mock_preferences_service

    def test_properties_return_services(self, feature):
        """Test that property accessors return service instances."""
        assert feature.ytdlp_wrapper is not None
        assert feature.format_selector is not None
        assert feature.playlist_handler is not None
        assert feature.download_manager is not None


# ---------------------------------------------------------------------------
# _get_default_output_path Tests
# ---------------------------------------------------------------------------


class TestGetDefaultOutputPath:
    """Tests for _get_default_output_path method."""

    def test_returns_preference_path(self, mock_preferences_service, mock_get_session):
        """Test that preference path is returned when set."""
        mock_preferences_service.get.return_value = "/custom/download/path"

        with patch("farmer_cli.features.video_downloader.get_session", mock_get_session):
            feature = VideoDownloaderFeature(preferences_service=mock_preferences_service)

        result = feature._get_default_output_path()

        assert result == Path("/custom/download/path")

    def test_returns_default_when_no_preference(self, mock_preferences_service, mock_get_session):
        """Test that default path is returned when no preference set."""
        mock_preferences_service.get.return_value = None

        with patch("farmer_cli.features.video_downloader.get_session", mock_get_session):
            feature = VideoDownloaderFeature(preferences_service=mock_preferences_service)

        result = feature._get_default_output_path()

        assert result == Path.home() / "Downloads" / "FarmerCLI"


# ---------------------------------------------------------------------------
# _format_filesize Tests
# ---------------------------------------------------------------------------


class TestFormatFilesize:
    """Tests for _format_filesize method."""

    def test_format_none(self, feature):
        """Test formatting None size."""
        assert feature._format_filesize(None) == "Unknown"

    def test_format_bytes(self, feature):
        """Test formatting bytes."""
        assert feature._format_filesize(500) == "500 B"

    def test_format_kilobytes(self, feature):
        """Test formatting kilobytes."""
        result = feature._format_filesize(2048)
        assert "KB" in result
        assert "2.0" in result

    def test_format_megabytes(self, feature):
        """Test formatting megabytes."""
        result = feature._format_filesize(5 * 1024 * 1024)
        assert "MB" in result
        assert "5.0" in result

    def test_format_gigabytes(self, feature):
        """Test formatting gigabytes."""
        result = feature._format_filesize(2 * 1024 * 1024 * 1024)
        assert "GB" in result
        assert "2.0" in result

    def test_format_boundary_kb(self, feature):
        """Test formatting at KB boundary."""
        result = feature._format_filesize(1024)
        assert "KB" in result

    def test_format_boundary_mb(self, feature):
        """Test formatting at MB boundary."""
        result = feature._format_filesize(1024 * 1024)
        assert "MB" in result

    def test_format_boundary_gb(self, feature):
        """Test formatting at GB boundary."""
        result = feature._format_filesize(1024 * 1024 * 1024)
        assert "GB" in result


# ---------------------------------------------------------------------------
# _sanitize_filename Tests
# ---------------------------------------------------------------------------


class TestSanitizeFilename:
    """Tests for _sanitize_filename method."""

    def test_sanitize_normal_name(self, feature):
        """Test sanitizing a normal filename."""
        result = feature._sanitize_filename("My Video Title")
        assert result == "My Video Title"

    def test_sanitize_removes_invalid_chars(self, feature):
        """Test that invalid characters are replaced."""
        result = feature._sanitize_filename('Video: "Test" <file>')
        assert ":" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_replaces_with_underscore(self, feature):
        """Test that invalid chars are replaced with underscore."""
        result = feature._sanitize_filename("Video:Test")
        assert result == "Video_Test"

    def test_sanitize_removes_backslash(self, feature):
        """Test that backslash is removed."""
        result = feature._sanitize_filename("Video\\Test")
        assert "\\" not in result

    def test_sanitize_removes_forward_slash(self, feature):
        """Test that forward slash is removed."""
        result = feature._sanitize_filename("Video/Test")
        assert "/" not in result

    def test_sanitize_removes_pipe(self, feature):
        """Test that pipe is removed."""
        result = feature._sanitize_filename("Video|Test")
        assert "|" not in result

    def test_sanitize_removes_question_mark(self, feature):
        """Test that question mark is removed."""
        result = feature._sanitize_filename("Video?Test")
        assert "?" not in result

    def test_sanitize_removes_asterisk(self, feature):
        """Test that asterisk is removed."""
        result = feature._sanitize_filename("Video*Test")
        assert "*" not in result

    def test_sanitize_truncates_long_names(self, feature):
        """Test that long names are truncated."""
        long_name = "A" * 200
        result = feature._sanitize_filename(long_name)
        assert len(result) <= 100

    def test_sanitize_strips_whitespace(self, feature):
        """Test that whitespace is stripped."""
        result = feature._sanitize_filename("  Video Title  ")
        assert result == "Video Title"

    def test_sanitize_multiple_invalid_chars(self, feature):
        """Test sanitizing multiple invalid characters."""
        result = feature._sanitize_filename('Test: "Video" | Part 1?')
        assert ":" not in result
        assert '"' not in result
        assert "|" not in result
        assert "?" not in result


# ---------------------------------------------------------------------------
# VIDEO_DOWNLOADER_OPTIONS Tests
# ---------------------------------------------------------------------------


class TestVideoDownloaderOptions:
    """Tests for VIDEO_DOWNLOADER_OPTIONS constant."""

    def test_options_count(self):
        """Test that correct number of options exist."""
        assert len(VIDEO_DOWNLOADER_OPTIONS) == 6

    def test_options_structure(self):
        """Test that options have correct structure."""
        for option in VIDEO_DOWNLOADER_OPTIONS:
            assert isinstance(option, tuple)
            assert len(option) == 2
            assert isinstance(option[0], str)
            assert isinstance(option[1], str)

    def test_options_include_return(self):
        """Test that return option exists."""
        keys = [opt[0] for opt in VIDEO_DOWNLOADER_OPTIONS]
        assert "0" in keys

    def test_options_include_download_single(self):
        """Test that download single video option exists."""
        labels = [opt[1] for opt in VIDEO_DOWNLOADER_OPTIONS]
        assert any("Single Video" in label for label in labels)

    def test_options_include_download_playlist(self):
        """Test that download playlist option exists."""
        labels = [opt[1] for opt in VIDEO_DOWNLOADER_OPTIONS]
        assert any("Playlist" in label for label in labels)


# ---------------------------------------------------------------------------
# _batch_progress_callback Tests
# ---------------------------------------------------------------------------


class TestBatchProgressCallback:
    """Tests for _batch_progress_callback method."""

    def test_callback_prints_progress(self, feature, capsys):
        """Test that callback prints progress."""
        with patch("farmer_cli.features.video_downloader.console") as mock_console:
            feature._batch_progress_callback("https://example.com", 1, 5)
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "[1/5]" in call_args

    def test_callback_with_different_values(self, feature):
        """Test callback with various progress values."""
        with patch("farmer_cli.features.video_downloader.console") as mock_console:
            feature._batch_progress_callback("https://example.com", 3, 10)
            call_args = mock_console.print.call_args[0][0]
            assert "[3/10]" in call_args


# ---------------------------------------------------------------------------
# _display_video_info Tests
# ---------------------------------------------------------------------------


class TestDisplayVideoInfo:
    """Tests for _display_video_info method."""

    def test_displays_title(self, feature, sample_video_info):
        """Test that title is displayed."""
        with patch("farmer_cli.features.video_downloader.console") as mock_console:
            feature._display_video_info(sample_video_info)

            # Check that print was called with title
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("Test Video Title" in call for call in calls)

    def test_displays_uploader(self, feature, sample_video_info):
        """Test that uploader is displayed."""
        with patch("farmer_cli.features.video_downloader.console") as mock_console:
            feature._display_video_info(sample_video_info)

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("Test Channel" in call for call in calls)

    def test_displays_view_count(self, feature, sample_video_info):
        """Test that view count is displayed."""
        with patch("farmer_cli.features.video_downloader.console") as mock_console:
            feature._display_video_info(sample_video_info)

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("1,000,000" in call for call in calls)


# ---------------------------------------------------------------------------
# _display_playlist_videos Tests
# ---------------------------------------------------------------------------


class TestDisplayPlaylistVideos:
    """Tests for _display_playlist_videos method."""

    def test_displays_video_count(self, feature):
        """Test that video count is displayed."""
        videos = [
            VideoInfo(
                url=f"https://youtube.com/watch?v=vid{i}",
                title=f"Video {i}",
                video_id=f"vid{i}",
            )
            for i in range(5)
        ]

        with patch("farmer_cli.features.video_downloader.console") as mock_console:
            feature._display_playlist_videos(videos)

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("5 total" in call for call in calls)

    def test_truncates_long_list(self, feature):
        """Test that long lists show truncation message."""
        videos = [
            VideoInfo(
                url=f"https://youtube.com/watch?v=vid{i}",
                title=f"Video {i}",
                video_id=f"vid{i}",
            )
            for i in range(30)
        ]

        with patch("farmer_cli.features.video_downloader.console") as mock_console:
            feature._display_playlist_videos(videos)

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("more" in call for call in calls)


# ---------------------------------------------------------------------------
# Service Property Tests
# ---------------------------------------------------------------------------


class TestServiceProperties:
    """Tests for service property accessors."""

    def test_ytdlp_wrapper_property(self, feature):
        """Test ytdlp_wrapper property returns wrapper."""
        wrapper = feature.ytdlp_wrapper
        assert wrapper is not None
        assert wrapper == feature._ytdlp_wrapper

    def test_format_selector_property(self, feature):
        """Test format_selector property returns selector."""
        selector = feature.format_selector
        assert selector is not None
        assert selector == feature._format_selector

    def test_playlist_handler_property(self, feature):
        """Test playlist_handler property returns handler."""
        handler = feature.playlist_handler
        assert handler is not None
        assert handler == feature._playlist_handler

    def test_download_manager_property(self, feature):
        """Test download_manager property returns manager."""
        manager = feature.download_manager
        assert manager is not None
        assert manager == feature._download_manager


# ---------------------------------------------------------------------------
# cleanup Tests
# ---------------------------------------------------------------------------


class TestCleanup:
    """Tests for cleanup method."""

    def test_cleanup_does_not_raise(self, feature):
        """Test that cleanup completes without error."""
        # Should not raise any exceptions
        feature.cleanup()
