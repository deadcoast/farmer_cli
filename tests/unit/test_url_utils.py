"""
Unit tests for farmer_cli.utils.url_utils module.

Tests URL validation, platform detection, and video ID extraction.

Feature: farmer-cli-completion
Requirements: 9.1, 9.3
"""

import pytest


class TestIsValidUrl:
    """Tests for is_valid_url function."""

    def test_valid_https_url(self):
        """Test that valid HTTPS URL returns True."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("https://example.com")

        assert result.is_valid is True
        assert result.error is None

    def test_valid_http_url(self):
        """Test that valid HTTP URL returns True."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("http://example.com")

        assert result.is_valid is True

    def test_url_with_path(self):
        """Test that URL with path is valid."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("https://example.com/path/to/page")

        assert result.is_valid is True

    def test_url_with_query(self):
        """Test that URL with query string is valid."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("https://example.com?key=value")

        assert result.is_valid is True

    def test_url_with_port(self):
        """Test that URL with port is valid."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("https://example.com:8080")

        assert result.is_valid is True

    def test_localhost_url(self):
        """Test that localhost URL is valid."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("http://localhost:3000")

        assert result.is_valid is True

    def test_ip_address_url(self):
        """Test that IP address URL is valid."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("http://192.168.1.1")

        assert result.is_valid is True

    def test_empty_url(self):
        """Test that empty URL returns False."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("")

        assert result.is_valid is False
        assert "empty" in result.error.lower()

    def test_none_url(self):
        """Test that None URL returns False."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url(None)

        assert result.is_valid is False

    def test_invalid_format(self):
        """Test that invalid format returns False."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("not-a-url")

        assert result.is_valid is False
        assert "format" in result.error.lower()

    def test_javascript_scheme_rejected(self):
        """Test that javascript: scheme is rejected."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("javascript:alert('xss')")

        assert result.is_valid is False
        assert "scheme" in result.error.lower()

    def test_file_scheme_rejected(self):
        """Test that file: scheme is rejected."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("file:///etc/passwd")

        assert result.is_valid is False

    def test_data_scheme_rejected(self):
        """Test that data: scheme is rejected."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("data:text/html,<script>alert('xss')</script>")

        assert result.is_valid is False

    def test_whitespace_trimmed(self):
        """Test that whitespace is trimmed from URL."""
        from farmer_cli.utils.url_utils import is_valid_url

        result = is_valid_url("  https://example.com  ")

        assert result.is_valid is True


class TestIsSupportedPlatform:
    """Tests for is_supported_platform function."""

    def test_youtube_url(self):
        """Test that YouTube URL is supported."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("https://www.youtube.com/watch?v=abc123")

        assert result[0] is True
        assert result[1] == "youtube"

    def test_youtube_short_url(self):
        """Test that youtu.be URL is supported."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("https://youtu.be/abc123")

        assert result[0] is True
        assert result[1] == "youtube"

    def test_youtube_mobile_url(self):
        """Test that mobile YouTube URL is supported."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("https://m.youtube.com/watch?v=abc123")

        assert result[0] is True
        assert result[1] == "youtube"

    def test_vimeo_url(self):
        """Test that Vimeo URL is supported."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("https://vimeo.com/123456789")

        assert result[0] is True
        assert result[1] == "vimeo"

    def test_vimeo_player_url(self):
        """Test that Vimeo player URL is supported."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("https://player.vimeo.com/video/123456789")

        assert result[0] is True
        assert result[1] == "vimeo"

    def test_direct_mp4_url(self):
        """Test that direct MP4 URL is supported."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("https://example.com/video.mp4")

        assert result[0] is True
        assert result[1] == "direct"

    def test_direct_webm_url(self):
        """Test that direct WebM URL is supported."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("https://example.com/video.webm")

        assert result[0] is True
        assert result[1] == "direct"

    def test_unsupported_url(self):
        """Test that unsupported URL returns False."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("https://example.com/page")

        assert result[0] is False
        assert result[1] is None

    def test_invalid_url(self):
        """Test that invalid URL returns False."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("not-a-url")

        assert result[0] is False
        assert result[1] is None

    def test_url_with_port(self):
        """Test that URL with port is handled correctly."""
        from farmer_cli.utils.url_utils import is_supported_platform

        result = is_supported_platform("https://www.youtube.com:443/watch?v=abc123")

        assert result[0] is True
        assert result[1] == "youtube"


class TestExtractVideoId:
    """Tests for extract_video_id function."""

    def test_youtube_watch_url(self):
        """Test extracting ID from YouTube watch URL."""
        from farmer_cli.utils.url_utils import extract_video_id

        result = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert result.success is True
        assert result.platform == "youtube"
        assert result.video_id == "dQw4w9WgXcQ"
        assert result.error is None

    def test_youtube_short_url(self):
        """Test extracting ID from youtu.be URL."""
        from farmer_cli.utils.url_utils import extract_video_id

        result = extract_video_id("https://youtu.be/dQw4w9WgXcQ")

        assert result.success is True
        assert result.platform == "youtube"
        assert result.video_id == "dQw4w9WgXcQ"

    def test_youtube_embed_url(self):
        """Test extracting ID from YouTube embed URL."""
        from farmer_cli.utils.url_utils import extract_video_id

        result = extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")

        assert result.success is True
        assert result.platform == "youtube"
        assert result.video_id == "dQw4w9WgXcQ"

    def test_vimeo_url(self):
        """Test extracting ID from Vimeo URL."""
        from farmer_cli.utils.url_utils import extract_video_id

        result = extract_video_id("https://vimeo.com/123456789")

        assert result.success is True
        assert result.platform == "vimeo"
        assert result.video_id == "123456789"

    def test_vimeo_video_url(self):
        """Test extracting ID from Vimeo video URL."""
        from farmer_cli.utils.url_utils import extract_video_id

        result = extract_video_id("https://vimeo.com/video/123456789")

        assert result.success is True
        assert result.platform == "vimeo"
        assert result.video_id == "123456789"

    def test_direct_url(self):
        """Test extracting ID from direct video URL."""
        from farmer_cli.utils.url_utils import extract_video_id

        result = extract_video_id("https://example.com/videos/my_video.mp4")

        assert result.success is True
        assert result.platform == "direct"
        assert result.video_id == "my_video"

    def test_invalid_url(self):
        """Test that invalid URL returns error."""
        from farmer_cli.utils.url_utils import extract_video_id

        result = extract_video_id("not-a-url")

        assert result.success is False
        assert result.platform is None
        assert result.video_id is None
        assert result.error is not None

    def test_unsupported_platform(self):
        """Test that unsupported platform returns error."""
        from farmer_cli.utils.url_utils import extract_video_id

        result = extract_video_id("https://example.com/page")

        assert result.success is False
        assert "not from a supported platform" in result.error

    def test_empty_url(self):
        """Test that empty URL returns error."""
        from farmer_cli.utils.url_utils import extract_video_id

        result = extract_video_id("")

        assert result.success is False
        assert result.error is not None


class TestGetSupportedPlatforms:
    """Tests for get_supported_platforms function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        from farmer_cli.utils.url_utils import get_supported_platforms

        result = get_supported_platforms()

        assert isinstance(result, list)

    def test_includes_youtube(self):
        """Test that YouTube is in supported platforms."""
        from farmer_cli.utils.url_utils import get_supported_platforms

        result = get_supported_platforms()

        assert "youtube" in result

    def test_includes_vimeo(self):
        """Test that Vimeo is in supported platforms."""
        from farmer_cli.utils.url_utils import get_supported_platforms

        result = get_supported_platforms()

        assert "vimeo" in result

    def test_includes_direct(self):
        """Test that direct is in supported platforms."""
        from farmer_cli.utils.url_utils import get_supported_platforms

        result = get_supported_platforms()

        assert "direct" in result


class TestGetPlatformDomains:
    """Tests for get_platform_domains function."""

    def test_youtube_domains(self):
        """Test that YouTube domains are returned."""
        from farmer_cli.utils.url_utils import get_platform_domains

        result = get_platform_domains("youtube")

        assert "youtube.com" in result
        assert "youtu.be" in result

    def test_vimeo_domains(self):
        """Test that Vimeo domains are returned."""
        from farmer_cli.utils.url_utils import get_platform_domains

        result = get_platform_domains("vimeo")

        assert "vimeo.com" in result

    def test_direct_domains_empty(self):
        """Test that direct platform has no specific domains."""
        from farmer_cli.utils.url_utils import get_platform_domains

        result = get_platform_domains("direct")

        assert result == []

    def test_unknown_platform(self):
        """Test that unknown platform returns empty list."""
        from farmer_cli.utils.url_utils import get_platform_domains

        result = get_platform_domains("unknown_platform")

        assert result == []


class TestVideoIdResult:
    """Tests for VideoIdResult named tuple."""

    def test_video_id_result_fields(self):
        """Test that VideoIdResult has correct fields."""
        from farmer_cli.utils.url_utils import VideoIdResult

        result = VideoIdResult(
            platform="youtube",
            video_id="abc123",
            success=True,
            error=None,
        )

        assert result.platform == "youtube"
        assert result.video_id == "abc123"
        assert result.success is True
        assert result.error is None


class TestUrlValidationResult:
    """Tests for UrlValidationResult named tuple."""

    def test_url_validation_result_fields(self):
        """Test that UrlValidationResult has correct fields."""
        from farmer_cli.utils.url_utils import UrlValidationResult

        result = UrlValidationResult(is_valid=True, error=None)

        assert result.is_valid is True
        assert result.error is None

    def test_url_validation_result_with_error(self):
        """Test UrlValidationResult with error."""
        from farmer_cli.utils.url_utils import UrlValidationResult

        result = UrlValidationResult(is_valid=False, error="Invalid URL")

        assert result.is_valid is False
        assert result.error == "Invalid URL"
