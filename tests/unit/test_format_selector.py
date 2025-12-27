"""
Unit tests for the format_selector module.

Tests cover:
- get_available_formats with various inputs
- get_best_format ranking logic
- Audio format filtering
- get_video_formats() method
- get_best_audio_format() method
- get_formats_by_resolution() method
- _filter_by_resolution() method
- _sort_formats() and _sort_audio_formats() methods
- set_default_format() and get_default_format()
- get_format_for_download() method

Requirements: 9.1, 9.3
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from farmer_cli.exceptions import FormatError
from farmer_cli.services.format_selector import FormatSelector
from farmer_cli.services.ytdlp_wrapper import VideoFormat


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_formats():
    """Create sample VideoFormat objects for testing."""
    return [
        VideoFormat(
            format_id="22",
            extension="mp4",
            resolution="720p",
            filesize=50000000,
            codec="h264",
            is_audio_only=False,
            quality=720,
            vcodec="h264",
            acodec="aac",
        ),
        VideoFormat(
            format_id="37",
            extension="mp4",
            resolution="1080p",
            filesize=100000000,
            codec="h264",
            is_audio_only=False,
            quality=1080,
            vcodec="h264",
            acodec="aac",
        ),
        VideoFormat(
            format_id="18",
            extension="mp4",
            resolution="360p",
            filesize=20000000,
            codec="h264",
            is_audio_only=False,
            quality=360,
            vcodec="h264",
            acodec="aac",
        ),
        VideoFormat(
            format_id="140",
            extension="m4a",
            resolution=None,
            filesize=5000000,
            codec="aac",
            is_audio_only=True,
            quality=128,
            acodec="aac",
            abr=128.0,
        ),
        VideoFormat(
            format_id="251",
            extension="webm",
            resolution=None,
            filesize=6000000,
            codec="opus",
            is_audio_only=True,
            quality=160,
            acodec="opus",
            abr=160.0,
        ),
    ]


@pytest.fixture
def mock_ytdlp_wrapper():
    """Create a mock YtdlpWrapper."""
    return MagicMock()


@pytest.fixture
def mock_preferences_service():
    """Create a mock PreferencesService."""
    mock = MagicMock()
    mock.get.return_value = None
    return mock


@pytest.fixture
def selector(mock_ytdlp_wrapper, mock_preferences_service):
    """Create a FormatSelector with mocked dependencies."""
    return FormatSelector(
        ytdlp_wrapper=mock_ytdlp_wrapper,
        preferences_service=mock_preferences_service,
    )


# ---------------------------------------------------------------------------
# Initialization Tests
# ---------------------------------------------------------------------------


class TestFormatSelectorInit:
    """Tests for FormatSelector initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        selector = FormatSelector()
        assert selector._ytdlp_wrapper is not None
        assert selector._preferences_service is None

    def test_init_with_custom_wrapper(self, mock_ytdlp_wrapper):
        """Test initialization with custom wrapper."""
        selector = FormatSelector(ytdlp_wrapper=mock_ytdlp_wrapper)
        assert selector._ytdlp_wrapper == mock_ytdlp_wrapper

    def test_init_with_preferences_service(self, mock_preferences_service):
        """Test initialization with preferences service."""
        selector = FormatSelector(preferences_service=mock_preferences_service)
        assert selector._preferences_service == mock_preferences_service

    def test_ytdlp_wrapper_property(self, selector, mock_ytdlp_wrapper):
        """Test ytdlp_wrapper property."""
        assert selector.ytdlp_wrapper == mock_ytdlp_wrapper


# ---------------------------------------------------------------------------
# get_available_formats Tests
# ---------------------------------------------------------------------------


class TestGetAvailableFormats:
    """Tests for get_available_formats method."""

    def test_get_available_formats_success(self, selector, mock_ytdlp_wrapper, sample_formats):
        """Test successful format retrieval."""
        mock_ytdlp_wrapper.get_formats.return_value = sample_formats

        formats = selector.get_available_formats("https://youtube.com/watch?v=test")

        assert len(formats) == 5
        mock_ytdlp_wrapper.get_formats.assert_called_once_with("https://youtube.com/watch?v=test")

    def test_get_available_formats_empty_url_raises(self, selector):
        """Test that empty URL raises FormatError."""
        with pytest.raises(FormatError, match="URL cannot be empty"):
            selector.get_available_formats("")

    def test_get_available_formats_whitespace_url_raises(self, selector):
        """Test that whitespace URL raises FormatError."""
        with pytest.raises(FormatError, match="URL cannot be empty"):
            selector.get_available_formats("   ")

    def test_get_available_formats_wrapper_error(self, selector, mock_ytdlp_wrapper):
        """Test handling of wrapper errors."""
        mock_ytdlp_wrapper.get_formats.side_effect = Exception("Network error")

        with pytest.raises(FormatError, match="Failed to get available formats"):
            selector.get_available_formats("https://youtube.com/watch?v=test")

    def test_get_available_formats_sorted_by_quality(self, selector, mock_ytdlp_wrapper, sample_formats):
        """Test that formats are sorted by quality."""
        mock_ytdlp_wrapper.get_formats.return_value = sample_formats

        formats = selector.get_available_formats("https://youtube.com/watch?v=test")

        # Video formats should be sorted by quality (highest first)
        video_formats = [f for f in formats if not f.is_audio_only]
        assert video_formats[0].quality >= video_formats[1].quality


# ---------------------------------------------------------------------------
# get_best_format Tests
# ---------------------------------------------------------------------------


class TestGetBestFormat:
    """Tests for get_best_format method."""

    def test_get_best_format_returns_highest_quality(self, selector, sample_formats):
        """Test that best format returns highest quality."""
        best = selector.get_best_format(sample_formats)

        assert best is not None
        assert best.resolution == "1080p"

    def test_get_best_format_empty_list(self, selector):
        """Test get_best_format with empty list."""
        best = selector.get_best_format([])

        assert best is None

    def test_get_best_format_with_max_resolution(self, selector, sample_formats):
        """Test get_best_format with max_resolution filter."""
        best = selector.get_best_format(sample_formats, max_resolution=720)

        assert best is not None
        assert int(best.resolution.rstrip("p")) <= 720

    def test_get_best_format_with_codec_preference(self, selector, sample_formats):
        """Test get_best_format with codec preference."""
        best = selector.get_best_format(sample_formats, prefer_codec="h264")

        assert best is not None
        assert "h264" in best.codec.lower()

    def test_get_best_format_excludes_audio_only(self, selector, sample_formats):
        """Test that get_best_format excludes audio-only by default."""
        best = selector.get_best_format(sample_formats)

        assert best is not None
        assert not best.is_audio_only

    def test_get_best_format_falls_back_to_any(self, selector):
        """Test fallback when no video formats available."""
        audio_only_formats = [
            VideoFormat(
                format_id="140",
                extension="m4a",
                is_audio_only=True,
                quality=128,
            ),
        ]

        best = selector.get_best_format(audio_only_formats)

        assert best is not None
        assert best.is_audio_only


# ---------------------------------------------------------------------------
# Audio Format Tests
# ---------------------------------------------------------------------------


class TestAudioFormats:
    """Tests for audio format methods."""

    def test_get_audio_formats(self, selector, sample_formats):
        """Test filtering audio-only formats."""
        audio_formats = selector.get_audio_formats(sample_formats)

        assert len(audio_formats) == 2
        assert all(f.is_audio_only for f in audio_formats)

    def test_get_audio_formats_empty_when_none(self, selector):
        """Test get_audio_formats when no audio formats exist."""
        video_only = [
            VideoFormat(format_id="22", extension="mp4", resolution="720p", is_audio_only=False),
        ]

        audio_formats = selector.get_audio_formats(video_only)

        assert len(audio_formats) == 0

    def test_get_audio_formats_sorted_by_bitrate(self, selector, sample_formats):
        """Test that audio formats are sorted by bitrate."""
        audio_formats = selector.get_audio_formats(sample_formats)

        # Higher bitrate should come first
        if len(audio_formats) >= 2:
            assert audio_formats[0].abr >= audio_formats[1].abr

    def test_get_best_audio_format(self, selector, sample_formats):
        """Test getting best audio format."""
        best_audio = selector.get_best_audio_format(sample_formats)

        assert best_audio is not None
        assert best_audio.is_audio_only
        # Should be the one with highest bitrate
        assert best_audio.abr == 160.0

    def test_get_best_audio_format_none_available(self, selector):
        """Test get_best_audio_format when no audio formats."""
        video_only = [
            VideoFormat(format_id="22", extension="mp4", resolution="720p", is_audio_only=False),
        ]

        best_audio = selector.get_best_audio_format(video_only)

        assert best_audio is None


# ---------------------------------------------------------------------------
# Video Format Tests
# ---------------------------------------------------------------------------


class TestVideoFormats:
    """Tests for video format methods."""

    def test_get_video_formats(self, selector, sample_formats):
        """Test filtering video formats."""
        video_formats = selector.get_video_formats(sample_formats)

        assert len(video_formats) == 3
        assert all(not f.is_audio_only for f in video_formats)

    def test_get_video_formats_sorted_by_quality(self, selector, sample_formats):
        """Test that video formats are sorted by quality."""
        video_formats = selector.get_video_formats(sample_formats)

        # Higher quality should come first
        assert video_formats[0].quality >= video_formats[1].quality

    def test_get_formats_by_resolution(self, selector, sample_formats):
        """Test getting formats by specific resolution."""
        formats_720 = selector.get_formats_by_resolution(sample_formats, 720)

        assert len(formats_720) == 1
        assert formats_720[0].resolution == "720p"

    def test_get_formats_by_resolution_no_match(self, selector, sample_formats):
        """Test get_formats_by_resolution with no matching formats."""
        formats_4k = selector.get_formats_by_resolution(sample_formats, 2160)

        assert len(formats_4k) == 0

    def test_get_formats_by_resolution_excludes_audio(self, selector, sample_formats):
        """Test that get_formats_by_resolution excludes audio-only."""
        formats = selector.get_formats_by_resolution(sample_formats, 720)

        assert all(not f.is_audio_only for f in formats)


# ---------------------------------------------------------------------------
# Filter and Sort Tests
# ---------------------------------------------------------------------------


class TestFilterAndSort:
    """Tests for internal filter and sort methods."""

    def test_filter_by_resolution(self, selector, sample_formats):
        """Test _filter_by_resolution method."""
        filtered = selector._filter_by_resolution(sample_formats, max_resolution=720)

        assert len(filtered) == 2  # 720p and 360p
        for fmt in filtered:
            height = int(fmt.resolution.rstrip("p"))
            assert height <= 720

    def test_filter_by_resolution_excludes_audio(self, selector, sample_formats):
        """Test that _filter_by_resolution excludes audio-only."""
        filtered = selector._filter_by_resolution(sample_formats, max_resolution=1080)

        assert all(not f.is_audio_only for f in filtered)

    def test_sort_formats_by_quality(self, selector):
        """Test _sort_formats sorts by quality."""
        formats = [
            VideoFormat(format_id="1", extension="mp4", quality=360),
            VideoFormat(format_id="2", extension="mp4", quality=1080),
            VideoFormat(format_id="3", extension="mp4", quality=720),
        ]

        sorted_formats = selector._sort_formats(formats)

        assert sorted_formats[0].quality == 1080
        assert sorted_formats[1].quality == 720
        assert sorted_formats[2].quality == 360

    def test_sort_formats_prefers_mp4(self, selector):
        """Test _sort_formats prefers mp4 extension."""
        formats = [
            VideoFormat(format_id="1", extension="webm", quality=720),
            VideoFormat(format_id="2", extension="mp4", quality=720),
            VideoFormat(format_id="3", extension="mkv", quality=720),
        ]

        sorted_formats = selector._sort_formats(formats)

        assert sorted_formats[0].extension == "mp4"

    def test_sort_formats_prefers_combined_streams(self, selector):
        """Test _sort_formats prefers formats with both video and audio."""
        formats = [
            VideoFormat(format_id="1", extension="mp4", quality=720, vcodec="h264", acodec=None),
            VideoFormat(format_id="2", extension="mp4", quality=720, vcodec="h264", acodec="aac"),
        ]

        sorted_formats = selector._sort_formats(formats)

        assert sorted_formats[0].acodec == "aac"

    def test_sort_audio_formats_by_bitrate(self, selector):
        """Test _sort_audio_formats sorts by bitrate."""
        formats = [
            VideoFormat(format_id="1", extension="m4a", is_audio_only=True, abr=64.0),
            VideoFormat(format_id="2", extension="m4a", is_audio_only=True, abr=256.0),
            VideoFormat(format_id="3", extension="m4a", is_audio_only=True, abr=128.0),
        ]

        sorted_formats = selector._sort_audio_formats(formats)

        assert sorted_formats[0].abr == 256.0
        assert sorted_formats[1].abr == 128.0
        assert sorted_formats[2].abr == 64.0

    def test_sort_audio_formats_prefers_m4a(self, selector):
        """Test _sort_audio_formats prefers m4a extension."""
        formats = [
            VideoFormat(format_id="1", extension="opus", is_audio_only=True, abr=128.0),
            VideoFormat(format_id="2", extension="m4a", is_audio_only=True, abr=128.0),
        ]

        sorted_formats = selector._sort_audio_formats(formats)

        assert sorted_formats[0].extension == "m4a"


# ---------------------------------------------------------------------------
# Preference Tests
# ---------------------------------------------------------------------------


class TestPreferences:
    """Tests for format preference methods."""

    def test_set_default_format_valid(self, selector, mock_preferences_service):
        """Test setting valid default format."""
        selector.set_default_format("1080p")

        mock_preferences_service.set.assert_called_once()

    def test_set_default_format_invalid_raises(self, selector):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid format preference"):
            selector.set_default_format("invalid_format")

    def test_set_default_format_no_service_raises(self):
        """Test that missing preferences service raises FormatError."""
        selector = FormatSelector(preferences_service=None)

        with pytest.raises(FormatError, match="Preferences service not available"):
            selector.set_default_format("1080p")

    def test_get_default_format(self, selector, mock_preferences_service):
        """Test getting default format."""
        mock_preferences_service.get.return_value = "720p"

        result = selector.get_default_format()

        assert result == "720p"

    def test_get_default_format_no_service(self):
        """Test get_default_format without preferences service."""
        selector = FormatSelector(preferences_service=None)

        result = selector.get_default_format()

        assert result is None

    def test_set_prefer_audio_only(self, selector, mock_preferences_service):
        """Test setting audio-only preference."""
        selector.set_prefer_audio_only(True)

        mock_preferences_service.set.assert_called_once()

    def test_set_prefer_audio_only_no_service_raises(self):
        """Test that missing preferences service raises FormatError."""
        selector = FormatSelector(preferences_service=None)

        with pytest.raises(FormatError, match="Preferences service not available"):
            selector.set_prefer_audio_only(True)

    def test_get_prefer_audio_only(self, selector, mock_preferences_service):
        """Test getting audio-only preference."""
        mock_preferences_service.get.return_value = True

        result = selector.get_prefer_audio_only()

        assert result is True

    def test_get_prefer_audio_only_default(self, selector, mock_preferences_service):
        """Test get_prefer_audio_only default value."""
        mock_preferences_service.get.return_value = False

        result = selector.get_prefer_audio_only()

        assert result is False

    def test_get_prefer_audio_only_no_service(self):
        """Test get_prefer_audio_only without preferences service."""
        selector = FormatSelector(preferences_service=None)

        result = selector.get_prefer_audio_only()

        assert result is False


# ---------------------------------------------------------------------------
# get_format_for_download Tests
# ---------------------------------------------------------------------------


class TestGetFormatForDownload:
    """Tests for get_format_for_download method."""

    def test_get_format_for_download_explicit_format(self, selector, mock_ytdlp_wrapper, sample_formats):
        """Test get_format_for_download with explicit format_id."""
        mock_ytdlp_wrapper.get_formats.return_value = sample_formats

        result = selector.get_format_for_download(
            "https://youtube.com/watch?v=test",
            format_id="22",
        )

        assert result is not None
        assert result.format_id == "22"

    def test_get_format_for_download_format_not_found(self, selector, mock_ytdlp_wrapper, sample_formats):
        """Test get_format_for_download when format_id not found."""
        mock_ytdlp_wrapper.get_formats.return_value = sample_formats

        result = selector.get_format_for_download(
            "https://youtube.com/watch?v=test",
            format_id="nonexistent",
        )

        # Should fall back to best format
        assert result is not None

    def test_get_format_for_download_uses_preference(self, selector, mock_ytdlp_wrapper, mock_preferences_service, sample_formats):
        """Test get_format_for_download uses saved preference."""
        mock_ytdlp_wrapper.get_formats.return_value = sample_formats
        mock_preferences_service.get.side_effect = lambda key, default=None: {
            "default_format": "720p",
            "prefer_audio_only": False,
        }.get(key, default)

        result = selector.get_format_for_download("https://youtube.com/watch?v=test")

        assert result is not None
        # Should respect 720p preference
        assert int(result.resolution.rstrip("p")) <= 720

    def test_get_format_for_download_audio_preference(self, selector, mock_ytdlp_wrapper, mock_preferences_service, sample_formats):
        """Test get_format_for_download with audio preference."""
        mock_ytdlp_wrapper.get_formats.return_value = sample_formats
        mock_preferences_service.get.side_effect = lambda key, default=None: {
            "default_format": None,
            "prefer_audio_only": True,
        }.get(key, default)

        result = selector.get_format_for_download("https://youtube.com/watch?v=test")

        assert result is not None
        assert result.is_audio_only

    def test_get_format_for_download_audio_preset(self, selector, mock_ytdlp_wrapper, mock_preferences_service, sample_formats):
        """Test get_format_for_download with audio preset."""
        mock_ytdlp_wrapper.get_formats.return_value = sample_formats
        mock_preferences_service.get.side_effect = lambda key, default=None: {
            "default_format": "audio",
            "prefer_audio_only": False,
        }.get(key, default)

        result = selector.get_format_for_download("https://youtube.com/watch?v=test")

        assert result is not None
        assert result.is_audio_only

    def test_get_format_for_download_no_formats(self, selector, mock_ytdlp_wrapper):
        """Test get_format_for_download when no formats available."""
        mock_ytdlp_wrapper.get_formats.return_value = []

        result = selector.get_format_for_download("https://youtube.com/watch?v=test")

        assert result is None

    def test_get_format_for_download_default_best(self, selector, mock_ytdlp_wrapper, mock_preferences_service, sample_formats):
        """Test get_format_for_download defaults to best quality."""
        mock_ytdlp_wrapper.get_formats.return_value = sample_formats
        mock_preferences_service.get.return_value = None

        result = selector.get_format_for_download("https://youtube.com/watch?v=test")

        assert result is not None
        # Should be highest quality video format
        assert result.resolution == "1080p"


# ---------------------------------------------------------------------------
# Display Formatting Tests
# ---------------------------------------------------------------------------


class TestDisplayFormatting:
    """Tests for display formatting methods."""

    def test_format_display_list(self, selector, sample_formats):
        """Test format_display_list creates proper display data."""
        display_list = selector.format_display_list(sample_formats)

        assert len(display_list) == 5
        assert all("format_id" in item for item in display_list)
        assert all("display_name" in item for item in display_list)
        assert all("resolution" in item for item in display_list)

    def test_format_display_list_handles_none_values(self, selector):
        """Test format_display_list handles None values."""
        formats = [
            VideoFormat(
                format_id="test",
                extension="mp4",
                resolution=None,
                filesize=None,
                codec=None,
            ),
        ]

        display_list = selector.format_display_list(formats)

        assert display_list[0]["resolution"] == "N/A"
        assert display_list[0]["codec"] == "N/A"
        assert display_list[0]["filesize"] == "Unknown"

    def test_format_filesize_gb(self, selector):
        """Test _format_filesize with GB size."""
        result = selector._format_filesize(2 * 1024 * 1024 * 1024)

        assert "GB" in result

    def test_format_filesize_mb(self, selector):
        """Test _format_filesize with MB size."""
        result = selector._format_filesize(50 * 1024 * 1024)

        assert "MB" in result

    def test_format_filesize_kb(self, selector):
        """Test _format_filesize with KB size."""
        result = selector._format_filesize(500 * 1024)

        assert "KB" in result

    def test_format_filesize_bytes(self, selector):
        """Test _format_filesize with bytes."""
        result = selector._format_filesize(500)

        assert "B" in result

    def test_format_filesize_none(self, selector):
        """Test _format_filesize with None."""
        result = selector._format_filesize(None)

        assert result == "Unknown"
