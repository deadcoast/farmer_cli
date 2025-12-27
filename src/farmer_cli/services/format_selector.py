"""
Format selector service for video format selection and preferences.

This module provides the FormatSelector class for handling video format
selection, quality ranking, and format preference persistence.

Feature: farmer-cli-completion
Requirements: 2.1, 2.4, 2.5, 2.6
"""

import logging
from typing import TYPE_CHECKING
from typing import ClassVar

from ..exceptions import FormatError
from .ytdlp_wrapper import VideoFormat
from .ytdlp_wrapper import YtdlpWrapper


if TYPE_CHECKING:
    from .preferences import PreferencesService


logger = logging.getLogger(__name__)


# Preference keys for format settings
PREF_DEFAULT_FORMAT = "default_format"
PREF_DEFAULT_QUALITY = "default_quality"
PREF_PREFER_AUDIO_ONLY = "prefer_audio_only"


class FormatSelector:
    """
    Handles format selection and preferences for video downloads.

    This class provides methods for retrieving available formats,
    selecting the best format based on quality criteria, filtering
    audio-only formats, and persisting format preferences.

    Attributes:
        ytdlp_wrapper: YtdlpWrapper instance for format extraction
        preferences_service: Optional PreferencesService for persistence
    """

    # Quality presets for easy selection
    QUALITY_PRESETS: ClassVar[dict[str, int | str | None]] = {
        "best": None,  # Best available
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360,
        "audio": "audio_only",
    }

    # Extension preference order (higher = better)
    EXTENSION_PRIORITY: ClassVar[dict[str, int]] = {
        "mp4": 4,
        "webm": 3,
        "mkv": 2,
        "m4a": 3,  # For audio
        "mp3": 2,  # For audio
        "opus": 1,  # For audio
    }

    def __init__(
        self,
        ytdlp_wrapper: YtdlpWrapper | None = None,
        preferences_service: "PreferencesService | None" = None,
    ) -> None:
        """
        Initialize the format selector.

        Args:
            ytdlp_wrapper: YtdlpWrapper instance (creates new one if not provided)
            preferences_service: PreferencesService for persisting preferences
        """
        self._ytdlp_wrapper = ytdlp_wrapper or YtdlpWrapper()
        self._preferences_service = preferences_service

    @property
    def ytdlp_wrapper(self) -> YtdlpWrapper:
        """Get the yt-dlp wrapper instance."""
        return self._ytdlp_wrapper

    def get_available_formats(self, url: str) -> list[VideoFormat]:
        """
        Get all available formats for a video URL.

        Retrieves format information from the video URL and returns
        a sorted list of available formats with the highest quality first.

        Args:
            url: The video URL to get formats for

        Returns:
            List of VideoFormat objects sorted by quality (highest first)

        Raises:
            FormatError: If format extraction fails
        """
        if not url or not url.strip():
            raise FormatError("URL cannot be empty")

        try:
            formats = self._ytdlp_wrapper.get_formats(url)
            return self._sort_formats(formats)
        except Exception as e:
            error_msg = f"Failed to get available formats: {e}"
            logger.error(error_msg)
            raise FormatError(error_msg, details=str(e)) from e

    def get_best_format(
        self,
        formats: list[VideoFormat],
        max_resolution: int | None = None,
        prefer_codec: str | None = None,
    ) -> VideoFormat | None:
        """
        Select the best quality format from a list of formats.

        Applies quality ranking to select the optimal format based on
        resolution, codec preference, and file extension.

        Args:
            formats: List of VideoFormat objects to choose from
            max_resolution: Maximum resolution height (e.g., 1080 for 1080p)
            prefer_codec: Preferred codec (e.g., "h264", "vp9")

        Returns:
            Best VideoFormat or None if no formats available
        """
        if not formats:
            return None

        # Filter out audio-only formats for video selection
        video_formats = [f for f in formats if not f.is_audio_only]

        if not video_formats:
            # Fall back to any format if no video formats
            video_formats = formats

        # Apply resolution filter if specified
        if max_resolution:
            filtered = self._filter_by_resolution(video_formats, max_resolution)
            if filtered:
                video_formats = filtered

        # Apply codec preference if specified
        if prefer_codec:
            codec_filtered = [
                f for f in video_formats
                if f.codec and prefer_codec.lower() in f.codec.lower()
            ]
            if codec_filtered:
                video_formats = codec_filtered

        # Sort by quality and return the best
        sorted_formats = self._sort_formats(video_formats)
        return sorted_formats[0] if sorted_formats else None

    def get_audio_formats(self, formats: list[VideoFormat]) -> list[VideoFormat]:
        """
        Filter to audio-only formats from a list of formats.

        Args:
            formats: List of VideoFormat objects to filter

        Returns:
            List of audio-only VideoFormat objects sorted by quality
        """
        audio_formats = [f for f in formats if f.is_audio_only]
        return self._sort_audio_formats(audio_formats)

    def get_video_formats(self, formats: list[VideoFormat]) -> list[VideoFormat]:
        """
        Filter to video formats (with video track) from a list of formats.

        Args:
            formats: List of VideoFormat objects to filter

        Returns:
            List of video VideoFormat objects sorted by quality
        """
        video_formats = [f for f in formats if not f.is_audio_only]
        return self._sort_formats(video_formats)

    def get_best_audio_format(self, formats: list[VideoFormat]) -> VideoFormat | None:
        """
        Get the best audio-only format from a list of formats.

        Args:
            formats: List of VideoFormat objects

        Returns:
            Best audio-only VideoFormat or None if no audio formats
        """
        audio_formats = self.get_audio_formats(formats)
        return audio_formats[0] if audio_formats else None

    def get_formats_by_resolution(
        self,
        formats: list[VideoFormat],
        resolution: int,
    ) -> list[VideoFormat]:
        """
        Get formats matching a specific resolution.

        Args:
            formats: List of VideoFormat objects
            resolution: Target resolution height (e.g., 1080, 720)

        Returns:
            List of formats matching the resolution
        """
        matching = []
        for fmt in formats:
            if fmt.is_audio_only:
                continue
            if fmt.resolution:
                try:
                    height = int(fmt.resolution.rstrip("pw"))
                    if height == resolution:
                        matching.append(fmt)
                except ValueError:
                    continue
        return self._sort_formats(matching)

    def _filter_by_resolution(
        self,
        formats: list[VideoFormat],
        max_resolution: int,
    ) -> list[VideoFormat]:
        """
        Filter formats by maximum resolution.

        Args:
            formats: List of formats to filter
            max_resolution: Maximum resolution height

        Returns:
            Filtered list of formats
        """
        filtered = []
        for fmt in formats:
            if fmt.is_audio_only:
                continue
            if fmt.resolution:
                try:
                    height = int(fmt.resolution.rstrip("pw"))
                    if height <= max_resolution:
                        filtered.append(fmt)
                except ValueError:
                    continue
        return filtered

    def _sort_formats(self, formats: list[VideoFormat]) -> list[VideoFormat]:
        """
        Sort formats by quality (highest first).

        Sorting criteria (in order of priority):
        1. Quality score (resolution height or bitrate)
        2. Preferred extensions (mp4 > webm > others)
        3. Has both video and audio

        Args:
            formats: List of formats to sort

        Returns:
            Sorted list of formats
        """
        def sort_key(fmt: VideoFormat) -> tuple[int, int, int]:
            # Higher quality first (negative for descending)
            quality = -fmt.quality if fmt.quality else 0

            # Preferred extensions
            ext_prio = -self.EXTENSION_PRIORITY.get(fmt.extension, 0)

            # Prefer formats with both video and audio codecs
            has_both = 0
            if fmt.vcodec and fmt.acodec:
                has_both = -1

            return (quality, ext_prio, has_both)

        return sorted(formats, key=sort_key)

    def _sort_audio_formats(self, formats: list[VideoFormat]) -> list[VideoFormat]:
        """
        Sort audio formats by quality (highest first).

        Sorting criteria:
        1. Audio bitrate (higher is better)
        2. Preferred audio extensions

        Args:
            formats: List of audio formats to sort

        Returns:
            Sorted list of audio formats
        """
        def sort_key(fmt: VideoFormat) -> tuple[float, int]:
            # Higher bitrate first (negative for descending)
            bitrate = -(fmt.abr or 0)

            # Preferred extensions for audio
            ext_prio = -self.EXTENSION_PRIORITY.get(fmt.extension, 0)

            return (bitrate, ext_prio)

        return sorted(formats, key=sort_key)

    def set_default_format(self, format_preference: str) -> None:
        """
        Set default format preference.

        Saves the format preference to persistent storage for use
        in future downloads.

        Args:
            format_preference: Format preference string (e.g., "best", "1080p", "720p", "audio")

        Raises:
            FormatError: If preferences service is not available
            ValueError: If format_preference is invalid
        """
        if not self._preferences_service:
            raise FormatError("Preferences service not available")

        # Validate the format preference
        if format_preference not in self.QUALITY_PRESETS:
            valid_presets = ", ".join(self.QUALITY_PRESETS.keys())
            raise ValueError(
                f"Invalid format preference '{format_preference}'. "
                f"Valid options: {valid_presets}"
            )

        self._preferences_service.set(PREF_DEFAULT_FORMAT, format_preference)
        logger.info(f"Set default format preference to: {format_preference}")

    def get_default_format(self) -> str | None:
        """
        Get saved default format preference.

        Returns:
            Format preference string or None if not set
        """
        if not self._preferences_service:
            return None

        return self._preferences_service.get(PREF_DEFAULT_FORMAT)

    def set_prefer_audio_only(self, prefer_audio: bool) -> None:
        """
        Set preference for audio-only downloads.

        Args:
            prefer_audio: Whether to prefer audio-only formats

        Raises:
            FormatError: If preferences service is not available
        """
        if not self._preferences_service:
            raise FormatError("Preferences service not available")

        self._preferences_service.set(PREF_PREFER_AUDIO_ONLY, prefer_audio)
        logger.info(f"Set prefer audio only to: {prefer_audio}")

    def get_prefer_audio_only(self) -> bool:
        """
        Get preference for audio-only downloads.

        Returns:
            True if audio-only is preferred, False otherwise
        """
        if not self._preferences_service:
            return False

        return self._preferences_service.get(PREF_PREFER_AUDIO_ONLY, False)

    def get_format_for_download(
        self,
        url: str,
        format_id: str | None = None,
    ) -> VideoFormat | None:
        """
        Get the format to use for downloading a video.

        This method considers the explicitly provided format_id,
        saved preferences, and falls back to best quality.

        Args:
            url: The video URL
            format_id: Explicit format ID to use (overrides preferences)

        Returns:
            VideoFormat to use for download, or None if no formats available

        Raises:
            FormatError: If format extraction fails
        """
        formats = self.get_available_formats(url)

        if not formats:
            return None

        # If explicit format_id provided, find it
        if format_id:
            for fmt in formats:
                if fmt.format_id == format_id:
                    return fmt
            # Format not found, log warning and fall through to default
            logger.warning(f"Requested format '{format_id}' not found, using default")

        # Check saved preferences
        default_format = self.get_default_format()
        prefer_audio = self.get_prefer_audio_only()

        if prefer_audio:
            return self.get_best_audio_format(formats)

        if default_format:
            preset = self.QUALITY_PRESETS.get(default_format)
            if preset == "audio_only":
                return self.get_best_audio_format(formats)
            elif isinstance(preset, int):
                # Resolution preset
                return self.get_best_format(formats, max_resolution=preset)

        # Default to best quality
        return self.get_best_format(formats)

    def format_display_list(self, formats: list[VideoFormat]) -> list[dict]:
        """
        Create a display-friendly list of formats.

        Args:
            formats: List of VideoFormat objects

        Returns:
            List of dictionaries with display information
        """
        return [
            {
                "format_id": fmt.format_id,
                "display_name": fmt.display_name,
                "resolution": fmt.resolution or "N/A",
                "extension": fmt.extension,
                "filesize": self._format_filesize(fmt.filesize),
                "codec": fmt.codec or "N/A",
                "is_audio_only": fmt.is_audio_only,
            }
            for fmt in formats
        ]

    def _format_filesize(self, size: int | None) -> str:
        """
        Format file size for display.

        Args:
            size: File size in bytes

        Returns:
            Human-readable file size string
        """
        if not size:
            return "Unknown"

        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} B"
