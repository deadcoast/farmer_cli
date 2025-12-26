"""
Property-based tests for VideoFormat data class.

Feature: farmer-cli-completion
Property 6: Format Information Completeness
Validates: Requirements 2.2

For any VideoFormat object returned by the Format_Selector,
it SHALL contain non-null values for format_id, extension,
and is_audio_only fields.
"""

import string

import pytest
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st

from farmer_cli.services.ytdlp_wrapper import VideoFormat


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid format IDs
format_id_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_",
    min_size=1,
    max_size=20,
)

# Strategy for generating valid extensions
extension_strategy = st.sampled_from([
    "mp4", "webm", "mkv", "avi", "mov", "flv", "m4v", "m4a", "mp3", "ogg", "opus", "wav"
])

# Strategy for generating resolutions
resolution_strategy = st.one_of(
    st.none(),
    st.sampled_from(["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"]),
)

# Strategy for generating file sizes
filesize_strategy = st.one_of(
    st.none(),
    st.integers(min_value=1, max_value=10 * 1024 * 1024 * 1024),  # Up to 10GB
)

# Strategy for generating codec names
codec_strategy = st.one_of(
    st.none(),
    st.sampled_from(["h264", "h265", "vp9", "av1", "aac", "opus", "mp3", "vorbis"]),
)

# Strategy for generating valid VideoFormat instances
video_format_strategy = st.builds(
    VideoFormat,
    format_id=format_id_strategy,
    extension=extension_strategy,
    resolution=resolution_strategy,
    filesize=filesize_strategy,
    codec=codec_strategy,
    is_audio_only=st.booleans(),
    quality=st.integers(min_value=0, max_value=4320),
    fps=st.one_of(st.none(), st.integers(min_value=1, max_value=120)),
    vcodec=st.one_of(st.none(), st.sampled_from(["h264", "h265", "vp9", "av1"])),
    acodec=st.one_of(st.none(), st.sampled_from(["aac", "opus", "mp3", "vorbis"])),
    abr=st.one_of(st.none(), st.floats(min_value=32, max_value=320)),
    vbr=st.one_of(st.none(), st.floats(min_value=100, max_value=50000)),
)

# Strategy for generating yt-dlp format dictionaries
ytdlp_format_dict_strategy = st.fixed_dictionaries({
    "format_id": format_id_strategy,
    "ext": extension_strategy,
}, optional={
    "height": st.integers(min_value=144, max_value=4320),
    "width": st.integers(min_value=256, max_value=7680),
    "filesize": st.integers(min_value=1, max_value=10 * 1024 * 1024 * 1024),
    "filesize_approx": st.integers(min_value=1, max_value=10 * 1024 * 1024 * 1024),
    "vcodec": st.sampled_from(["h264", "h265", "vp9", "av1", "none"]),
    "acodec": st.sampled_from(["aac", "opus", "mp3", "vorbis", "none"]),
    "fps": st.integers(min_value=1, max_value=120),
    "tbr": st.floats(min_value=100, max_value=50000),
    "abr": st.floats(min_value=32, max_value=320),
    "vbr": st.floats(min_value=100, max_value=50000),
})


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestVideoFormatCompleteness:
    """
    Property 6: Format Information Completeness

    For any VideoFormat object returned by the Format_Selector,
    it SHALL contain non-null values for format_id, extension,
    and is_audio_only fields.

    **Validates: Requirements 2.2**
    """

    @given(video_format_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_format_id_is_never_null(self, video_format: VideoFormat):
        """
        Feature: farmer-cli-completion, Property 6: Format Information Completeness
        Validates: Requirements 2.2

        For any VideoFormat, format_id SHALL be non-null and non-empty.
        """
        assert video_format.format_id is not None, "format_id should not be None"
        assert len(video_format.format_id) > 0, "format_id should not be empty"

    @given(video_format_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_extension_is_never_null(self, video_format: VideoFormat):
        """
        Feature: farmer-cli-completion, Property 6: Format Information Completeness
        Validates: Requirements 2.2

        For any VideoFormat, extension SHALL be non-null and non-empty.
        """
        assert video_format.extension is not None, "extension should not be None"
        assert len(video_format.extension) > 0, "extension should not be empty"

    @given(video_format_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_is_audio_only_is_never_null(self, video_format: VideoFormat):
        """
        Feature: farmer-cli-completion, Property 6: Format Information Completeness
        Validates: Requirements 2.2

        For any VideoFormat, is_audio_only SHALL be a boolean (never None).
        """
        assert video_format.is_audio_only is not None, "is_audio_only should not be None"
        assert isinstance(video_format.is_audio_only, bool), "is_audio_only should be a boolean"

    @given(ytdlp_format_dict_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_from_ytdlp_format_preserves_required_fields(self, fmt_dict: dict):
        """
        Feature: farmer-cli-completion, Property 6: Format Information Completeness
        Validates: Requirements 2.2

        For any yt-dlp format dictionary with required fields,
        from_ytdlp_format SHALL produce a VideoFormat with non-null
        format_id, extension, and is_audio_only.
        """
        video_format = VideoFormat.from_ytdlp_format(fmt_dict)

        assert video_format.format_id is not None, "format_id should not be None"
        assert len(video_format.format_id) > 0, "format_id should not be empty"
        assert video_format.extension is not None, "extension should not be None"
        assert len(video_format.extension) > 0, "extension should not be empty"
        assert video_format.is_audio_only is not None, "is_audio_only should not be None"
        assert isinstance(video_format.is_audio_only, bool), "is_audio_only should be a boolean"

    @given(video_format_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_display_name_is_never_empty(self, video_format: VideoFormat):
        """
        Feature: farmer-cli-completion, Property 6: Format Information Completeness
        Validates: Requirements 2.2

        For any VideoFormat, display_name SHALL produce a non-empty string.
        """
        display_name = video_format.display_name

        assert display_name is not None, "display_name should not be None"
        assert len(display_name) > 0, "display_name should not be empty"

    @given(st.sampled_from(["", " ", "\t", "\n", "\r", "  ", "\t\n"]), extension_strategy)
    @settings(max_examples=50)
    @pytest.mark.property
    def test_empty_format_id_raises_error(self, format_id: str, extension: str):
        """
        Feature: farmer-cli-completion, Property 6: Format Information Completeness
        Validates: Requirements 2.2

        For any empty or whitespace-only format_id, VideoFormat construction
        SHALL raise a ValueError.
        """
        with pytest.raises(ValueError, match="format_id cannot be empty"):
            VideoFormat(format_id=format_id, extension=extension)

    @given(format_id_strategy, st.sampled_from(["", " ", "\t", "\n", "\r", "  ", "\t\n"]))
    @settings(max_examples=50)
    @pytest.mark.property
    def test_empty_extension_raises_error(self, format_id: str, extension: str):
        """
        Feature: farmer-cli-completion, Property 6: Format Information Completeness
        Validates: Requirements 2.2

        For any empty or whitespace-only extension, VideoFormat construction
        SHALL raise a ValueError.
        """
        with pytest.raises(ValueError, match="extension cannot be empty"):
            VideoFormat(format_id=format_id, extension=extension)

    @given(ytdlp_format_dict_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_from_ytdlp_format_never_raises_unhandled_exception(self, fmt_dict: dict):
        """
        Feature: farmer-cli-completion, Property 6: Format Information Completeness
        Validates: Requirements 2.2

        For any yt-dlp format dictionary, from_ytdlp_format SHALL never
        raise an unhandled exception.
        """
        # This should never raise an exception for valid input dicts
        video_format = VideoFormat.from_ytdlp_format(fmt_dict)

        # Result should be a valid VideoFormat
        assert isinstance(video_format, VideoFormat)
