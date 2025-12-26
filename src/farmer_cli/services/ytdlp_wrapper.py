"""
yt-dlp wrapper service for video downloading.

This module provides a wrapper around yt-dlp for extracting video information
and downloading videos from various platforms.

Feature: farmer-cli-completion
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.4, 3.1
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Callable
from typing import ClassVar

import yt_dlp

from ..exceptions import DownloadError


class DownloadStatus(Enum):
    """Status of a download operation."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class VideoFormat:
    """
    Represents a video format option.

    Attributes:
        format_id: Unique identifier for the format
        extension: File extension (e.g., mp4, webm)
        resolution: Video resolution (e.g., 1080p, 720p) or None for audio
        filesize: Estimated file size in bytes, or None if unknown
        codec: Video/audio codec information
        is_audio_only: Whether this format contains only audio
        quality: Quality ranking for sorting (higher is better)
        fps: Frames per second for video formats
        vcodec: Video codec name
        acodec: Audio codec name
        abr: Audio bitrate in kbps
        vbr: Video bitrate in kbps
    """

    format_id: str
    extension: str
    resolution: str | None = None
    filesize: int | None = None
    codec: str | None = None
    is_audio_only: bool = False
    quality: int = 0
    fps: int | None = None
    vcodec: str | None = None
    acodec: str | None = None
    abr: float | None = None
    vbr: float | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.format_id or not self.format_id.strip():
            raise ValueError("format_id cannot be empty")
        if not self.extension or not self.extension.strip():
            raise ValueError("extension cannot be empty")

    @property
    def display_name(self) -> str:
        """Get a human-readable display name for the format."""
        parts = []
        if self.resolution:
            parts.append(self.resolution)
        if self.fps:
            parts.append(f"{self.fps}fps")
        if self.extension:
            parts.append(self.extension.upper())
        if self.is_audio_only:
            parts.append("(audio only)")
        if self.filesize:
            size_mb = self.filesize / (1024 * 1024)
            parts.append(f"~{size_mb:.1f}MB")
        return " - ".join(parts) if parts else self.format_id

    @classmethod
    def from_ytdlp_format(cls, fmt: dict[str, Any]) -> "VideoFormat":
        """
        Create a VideoFormat from a yt-dlp format dictionary.

        Args:
            fmt: Format dictionary from yt-dlp

        Returns:
            VideoFormat instance
        """
        format_id = fmt.get("format_id", "unknown")
        extension = fmt.get("ext", "unknown")

        # Determine resolution
        height = fmt.get("height")
        width = fmt.get("width")
        resolution = None
        if height:
            resolution = f"{height}p"
        elif width:
            resolution = f"{width}w"

        # Get filesize (try multiple fields)
        filesize = fmt.get("filesize") or fmt.get("filesize_approx")

        # Determine codec info
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")
        codec = None
        if vcodec and vcodec != "none":
            codec = vcodec
        elif acodec and acodec != "none":
            codec = acodec

        # Determine if audio only
        is_audio_only = (vcodec == "none" or not vcodec) and acodec and acodec != "none"

        # Calculate quality score for sorting
        quality = 0
        if height:
            quality = height
        if fmt.get("tbr"):
            quality = max(quality, int(fmt.get("tbr", 0)))

        return cls(
            format_id=format_id,
            extension=extension,
            resolution=resolution,
            filesize=filesize,
            codec=codec,
            is_audio_only=is_audio_only,
            quality=quality,
            fps=fmt.get("fps"),
            vcodec=vcodec if vcodec != "none" else None,
            acodec=acodec if acodec != "none" else None,
            abr=fmt.get("abr"),
            vbr=fmt.get("vbr"),
        )


@dataclass
class VideoInfo:
    """
    Represents information about a video.

    Attributes:
        url: Original URL of the video
        title: Video title
        uploader: Channel or uploader name
        duration: Video duration in seconds
        formats: List of available formats
        video_id: Platform-specific video ID
        description: Video description
        thumbnail: URL to thumbnail image
        upload_date: Upload date in YYYYMMDD format
        view_count: Number of views
        like_count: Number of likes
        playlist_index: Position in playlist (1-indexed)
        playlist_title: Title of the playlist
        playlist_count: Total videos in playlist
        webpage_url: Canonical URL for the video
        extractor: Name of the extractor used
    """

    url: str
    title: str
    uploader: str | None = None
    duration: int | None = None
    formats: list[VideoFormat] = field(default_factory=list)
    video_id: str | None = None
    description: str | None = None
    thumbnail: str | None = None
    upload_date: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    playlist_index: int | None = None
    playlist_title: str | None = None
    playlist_count: int | None = None
    webpage_url: str | None = None
    extractor: str | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.url:
            raise ValueError("url cannot be empty")
        if not self.title:
            raise ValueError("title cannot be empty")

    @property
    def duration_formatted(self) -> str:
        """Get duration in HH:MM:SS format."""
        if not self.duration:
            return "Unknown"
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @classmethod
    def from_ytdlp_info(cls, info: dict[str, Any]) -> "VideoInfo":
        """
        Create a VideoInfo from a yt-dlp info dictionary.

        Args:
            info: Info dictionary from yt-dlp extract_info

        Returns:
            VideoInfo instance
        """
        # Extract formats
        formats = []
        for fmt in info.get("formats", []):
            try:
                formats.append(VideoFormat.from_ytdlp_format(fmt))
            except (ValueError, KeyError):
                # Skip invalid formats
                continue

        return cls(
            url=info.get("original_url") or info.get("webpage_url") or info.get("url", ""),
            title=info.get("title", "Unknown Title"),
            uploader=info.get("uploader") or info.get("channel"),
            duration=info.get("duration"),
            formats=formats,
            video_id=info.get("id"),
            description=info.get("description"),
            thumbnail=info.get("thumbnail"),
            upload_date=info.get("upload_date"),
            view_count=info.get("view_count"),
            like_count=info.get("like_count"),
            playlist_index=info.get("playlist_index"),
            playlist_title=info.get("playlist_title"),
            playlist_count=info.get("playlist_count"),
            webpage_url=info.get("webpage_url"),
            extractor=info.get("extractor"),
        )


@dataclass
class DownloadProgress:
    """
    Represents the progress of a download operation.

    Attributes:
        status: Current download status
        downloaded_bytes: Number of bytes downloaded
        total_bytes: Total file size in bytes (if known)
        speed: Download speed in bytes per second
        eta: Estimated time remaining in seconds
        filename: Name of the file being downloaded
        percent: Download percentage (0-100)
        elapsed: Time elapsed in seconds
    """

    status: DownloadStatus
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed: float | None = None
    eta: int | None = None
    filename: str = ""
    percent: float = 0.0
    elapsed: float | None = None

    @property
    def speed_formatted(self) -> str:
        """Get speed in human-readable format."""
        if not self.speed:
            return "Unknown"
        if self.speed >= 1024 * 1024:
            return f"{self.speed / (1024 * 1024):.1f} MB/s"
        if self.speed >= 1024:
            return f"{self.speed / 1024:.1f} KB/s"
        return f"{self.speed:.0f} B/s"

    @property
    def eta_formatted(self) -> str:
        """Get ETA in human-readable format."""
        if not self.eta:
            return "Unknown"
        if self.eta >= 3600:
            hours, remainder = divmod(self.eta, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}h {minutes}m {seconds}s"
        if self.eta >= 60:
            minutes, seconds = divmod(self.eta, 60)
            return f"{minutes}m {seconds}s"
        return f"{self.eta}s"

    @classmethod
    def from_ytdlp_progress(cls, d: dict[str, Any]) -> "DownloadProgress":
        """
        Create a DownloadProgress from a yt-dlp progress dictionary.

        Args:
            d: Progress dictionary from yt-dlp hook

        Returns:
            DownloadProgress instance
        """
        status_map = {
            "downloading": DownloadStatus.DOWNLOADING,
            "finished": DownloadStatus.COMPLETED,
            "error": DownloadStatus.FAILED,
        }
        status = status_map.get(d.get("status", ""), DownloadStatus.PENDING)

        downloaded = d.get("downloaded_bytes", 0) or 0
        total = d.get("total_bytes") or d.get("total_bytes_estimate")

        percent = 0.0
        if total and total > 0:
            percent = (downloaded / total) * 100

        return cls(
            status=status,
            downloaded_bytes=downloaded,
            total_bytes=total,
            speed=d.get("speed"),
            eta=d.get("eta"),
            filename=d.get("filename", ""),
            percent=percent,
            elapsed=d.get("elapsed"),
        )


class YtdlpWrapper:
    """
    Wrapper around yt-dlp for video downloading and information extraction.

    This class provides a clean interface to yt-dlp functionality with proper
    error handling and type-safe return values.

    Attributes:
        default_opts: Default yt-dlp options used for all operations
    """

    # Supported platforms for validation
    SUPPORTED_PLATFORMS: ClassVar[list[str]] = [
        "youtube",
        "vimeo",
        "dailymotion",
        "twitch",
        "twitter",
        "facebook",
        "instagram",
        "tiktok",
        "soundcloud",
        "bandcamp",
        "generic",  # For direct video URLs
    ]

    def __init__(self, quiet: bool = True, no_warnings: bool = True) -> None:
        """
        Initialize the yt-dlp wrapper.

        Args:
            quiet: Suppress yt-dlp console output
            no_warnings: Suppress yt-dlp warnings
        """
        self.default_opts: dict[str, Any] = {
            "quiet": quiet,
            "no_warnings": no_warnings,
            "extract_flat": False,
            "ignoreerrors": False,
        }

    def _get_ydl_opts(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get yt-dlp options merged with defaults.

        Args:
            **kwargs: Additional options to merge

        Returns:
            Merged options dictionary
        """
        opts = self.default_opts.copy()
        opts.update(kwargs)
        return opts

    def extract_info(self, url: str, download: bool = False) -> VideoInfo:
        """
        Extract video information from a URL without downloading.

        This method wraps yt-dlp's extract_info with proper error handling
        and converts the result to a VideoInfo dataclass.

        Args:
            url: The video URL to extract information from
            download: Whether to download the video (default False)

        Returns:
            VideoInfo object containing video metadata and available formats

        Raises:
            DownloadError: If the URL is invalid, unsupported, or extraction fails
        """
        if not url or not url.strip():
            raise DownloadError("URL cannot be empty", url=url)

        opts = self._get_ydl_opts()

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=download)

                if info is None:
                    raise DownloadError(
                        "Failed to extract video information. The URL may be invalid or unsupported.",
                        url=url,
                    )

                return VideoInfo.from_ytdlp_info(info)

        except yt_dlp.utils.DownloadError as e:
            # Handle yt-dlp specific download errors
            error_msg = str(e)

            # Provide user-friendly error messages
            if "Video unavailable" in error_msg:
                raise DownloadError(
                    "Video is unavailable. It may be private, deleted, or region-restricted.",
                    url=url,
                    details=error_msg,
                ) from e
            if "Unsupported URL" in error_msg:
                raise DownloadError(
                    "This URL is not supported. Please check if the URL is correct.",
                    url=url,
                    details=error_msg,
                ) from e
            if "Unable to extract" in error_msg:
                raise DownloadError(
                    "Unable to extract video information. The page structure may have changed.",
                    url=url,
                    details=error_msg,
                ) from e

            raise DownloadError(
                f"Failed to extract video information: {error_msg}",
                url=url,
                details=error_msg,
            ) from e

        except yt_dlp.utils.ExtractorError as e:
            raise DownloadError(
                f"Extractor error: {e}",
                url=url,
                details=str(e),
            ) from e

        except Exception as e:
            # Handle network errors and other unexpected exceptions
            error_msg = str(e)

            if "getaddrinfo failed" in error_msg or "Name or service not known" in error_msg:
                raise DownloadError(
                    "Network error: Unable to connect. Please check your internet connection.",
                    url=url,
                    details=error_msg,
                ) from e
            if "Connection refused" in error_msg:
                raise DownloadError(
                    "Connection refused. The server may be down or blocking requests.",
                    url=url,
                    details=error_msg,
                ) from e
            if "timed out" in error_msg.lower():
                raise DownloadError(
                    "Connection timed out. Please try again later.",
                    url=url,
                    details=error_msg,
                ) from e

            raise DownloadError(
                f"Unexpected error while extracting video information: {error_msg}",
                url=url,
                details=error_msg,
            ) from e

    def get_formats(self, url: str) -> list[VideoFormat]:
        """
        Get available formats for a video URL.

        This method extracts video information and returns a sorted list
        of available formats, with the highest quality formats first.

        Args:
            url: The video URL to get formats for

        Returns:
            List of VideoFormat objects sorted by quality (highest first)

        Raises:
            DownloadError: If the URL is invalid or format extraction fails
        """
        video_info = self.extract_info(url, download=False)
        return self._sort_formats(video_info.formats)

    def get_audio_formats(self, url: str) -> list[VideoFormat]:
        """
        Get available audio-only formats for a video URL.

        Args:
            url: The video URL to get audio formats for

        Returns:
            List of audio-only VideoFormat objects sorted by quality

        Raises:
            DownloadError: If the URL is invalid or format extraction fails
        """
        formats = self.get_formats(url)
        return [f for f in formats if f.is_audio_only]

    def get_video_formats(self, url: str) -> list[VideoFormat]:
        """
        Get available video formats (with video track) for a URL.

        Args:
            url: The video URL to get video formats for

        Returns:
            List of video VideoFormat objects sorted by quality

        Raises:
            DownloadError: If the URL is invalid or format extraction fails
        """
        formats = self.get_formats(url)
        return [f for f in formats if not f.is_audio_only]

    def _sort_formats(self, formats: list[VideoFormat]) -> list[VideoFormat]:
        """
        Sort formats by quality (highest first).

        Sorting criteria (in order of priority):
        1. Quality score (resolution height or bitrate)
        2. Video formats before audio-only
        3. Preferred extensions (mp4 > webm > others)

        Args:
            formats: List of formats to sort

        Returns:
            Sorted list of formats
        """
        # Extension preference order
        ext_priority = {"mp4": 3, "webm": 2, "mkv": 1}

        def sort_key(fmt: VideoFormat) -> tuple[int, int, int]:
            # Higher quality first (negative for descending)
            quality = -fmt.quality if fmt.quality else 0
            # Video formats before audio-only
            is_video = 0 if not fmt.is_audio_only else 1
            # Preferred extensions
            ext_prio = -ext_priority.get(fmt.extension, 0)
            return (quality, is_video, ext_prio)

        return sorted(formats, key=sort_key)

    def get_best_format(self, url: str, audio_only: bool = False) -> VideoFormat | None:
        """
        Get the best quality format for a video URL.

        Args:
            url: The video URL
            audio_only: If True, return best audio-only format

        Returns:
            Best VideoFormat or None if no formats available

        Raises:
            DownloadError: If the URL is invalid or format extraction fails
        """
        if audio_only:
            formats = self.get_audio_formats(url)
        else:
            formats = self.get_video_formats(url)

        return formats[0] if formats else None

    def filter_formats_by_resolution(
        self,
        formats: list[VideoFormat],
        max_resolution: int | None = None,
        min_resolution: int | None = None,
    ) -> list[VideoFormat]:
        """
        Filter formats by resolution range.

        Args:
            formats: List of formats to filter
            max_resolution: Maximum resolution height (e.g., 1080 for 1080p)
            min_resolution: Minimum resolution height (e.g., 720 for 720p)

        Returns:
            Filtered list of formats
        """
        result = []
        for fmt in formats:
            if fmt.is_audio_only:
                continue

            # Extract height from resolution string (e.g., "1080p" -> 1080)
            if fmt.resolution:
                try:
                    height = int(fmt.resolution.rstrip("pw"))
                except ValueError:
                    continue

                if max_resolution and height > max_resolution:
                    continue
                if min_resolution and height < min_resolution:
                    continue

                result.append(fmt)

        return result

    def download(
        self,
        url: str,
        output_path: str | Path,
        format_id: str | None = None,
        progress_callback: Callable[[DownloadProgress], None] | None = None,
    ) -> str:
        """
        Download a video from URL to the specified path.

        This method downloads a video with optional format selection and
        progress tracking. It supports resuming interrupted downloads and
        verifies file integrity after completion.

        Args:
            url: The video URL to download
            output_path: Directory or file path for the downloaded video
            format_id: Specific format ID to download (None for best quality)
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the downloaded file

        Raises:
            DownloadError: If download fails or file integrity check fails
        """
        if not url or not url.strip():
            raise DownloadError("URL cannot be empty", url=url)

        output_path = Path(output_path)

        # Determine output template
        if output_path.is_dir() or str(output_path).endswith("/"):
            output_path.mkdir(parents=True, exist_ok=True)
            outtmpl = str(output_path / "%(title)s.%(ext)s")
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            outtmpl = str(output_path)

        # Build yt-dlp options
        opts = self._get_ydl_opts(
            outtmpl=outtmpl,
            # Resume partial downloads
            continuedl=True,
            # Don't overwrite existing files
            nooverwrites=False,
            # Retry on errors
            retries=3,
            fragment_retries=3,
        )

        # Set format selection
        if format_id:
            opts["format"] = format_id
        else:
            # Best video+audio, fallback to best available
            opts["format"] = "bestvideo+bestaudio/best"

        # Track the downloaded filename
        downloaded_file: str | None = None

        # Progress hook
        def progress_hook(d: dict[str, Any]) -> None:
            nonlocal downloaded_file

            if d.get("status") == "finished":
                downloaded_file = d.get("filename")

            if progress_callback:
                progress = DownloadProgress.from_ytdlp_progress(d)
                progress_callback(progress)

        opts["progress_hooks"] = [progress_hook]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            if not downloaded_file:
                # Try to find the file based on the template
                # This handles cases where the hook didn't capture the filename
                video_info = self.extract_info(url, download=False)
                expected_file = output_path / f"{video_info.title}.mp4"
                if expected_file.exists():
                    downloaded_file = str(expected_file)

            if downloaded_file and Path(downloaded_file).exists():
                # Verify file integrity (basic check - file exists and has content)
                file_size = Path(downloaded_file).stat().st_size
                if file_size == 0:
                    raise DownloadError(
                        "Downloaded file is empty. The download may have failed.",
                        url=url,
                    )
                return downloaded_file

            raise DownloadError(
                "Download completed but file not found.",
                url=url,
            )

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)

            if "Video unavailable" in error_msg:
                raise DownloadError(
                    "Video is unavailable. It may be private, deleted, or region-restricted.",
                    url=url,
                    details=error_msg,
                ) from e
            if "HTTP Error 403" in error_msg:
                raise DownloadError(
                    "Access denied. The video may require authentication.",
                    url=url,
                    details=error_msg,
                ) from e
            if "HTTP Error 429" in error_msg:
                raise DownloadError(
                    "Too many requests. Please wait before trying again.",
                    url=url,
                    details=error_msg,
                ) from e

            raise DownloadError(
                f"Download failed: {error_msg}",
                url=url,
                details=error_msg,
            ) from e

        except KeyboardInterrupt as e:
            # Handle user cancellation gracefully
            raise DownloadError(
                "Download cancelled by user.",
                url=url,
            ) from e

        except Exception as e:
            error_msg = str(e)

            if "No space left" in error_msg:
                raise DownloadError(
                    "Not enough disk space to complete the download.",
                    url=url,
                    details=error_msg,
                ) from e
            if "Permission denied" in error_msg:
                raise DownloadError(
                    "Permission denied. Cannot write to the output directory.",
                    url=url,
                    details=error_msg,
                ) from e

            raise DownloadError(
                f"Unexpected error during download: {error_msg}",
                url=url,
                details=error_msg,
            ) from e

    def download_with_format(
        self,
        url: str,
        output_path: str | Path,
        video_format: VideoFormat,
        progress_callback: Callable[[DownloadProgress], None] | None = None,
    ) -> str:
        """
        Download a video using a specific VideoFormat object.

        Args:
            url: The video URL to download
            output_path: Directory or file path for the downloaded video
            video_format: VideoFormat object specifying the format to download
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the downloaded file

        Raises:
            DownloadError: If download fails
        """
        return self.download(
            url=url,
            output_path=output_path,
            format_id=video_format.format_id,
            progress_callback=progress_callback,
        )

    def extract_playlist(self, url: str) -> list[VideoInfo]:
        """
        Extract all video entries from a playlist URL.

        This method handles pagination for large playlists and returns
        a list of VideoInfo objects for each video in the playlist.

        Args:
            url: The playlist URL to extract

        Returns:
            List of VideoInfo objects for each video in the playlist

        Raises:
            DownloadError: If the URL is invalid or playlist extraction fails
        """
        if not url or not url.strip():
            raise DownloadError("URL cannot be empty", url=url)

        # Use extract_flat to get playlist entries without full extraction
        opts = self._get_ydl_opts(
            extract_flat="in_playlist",
            ignoreerrors=True,  # Continue on individual video errors
        )

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    raise DownloadError(
                        "Failed to extract playlist information.",
                        url=url,
                    )

                # Check if this is actually a playlist
                if info.get("_type") != "playlist" and "entries" not in info:
                    # Single video, not a playlist
                    return [VideoInfo.from_ytdlp_info(info)]

                entries = info.get("entries", [])
                if not entries:
                    raise DownloadError(
                        "Playlist is empty or could not be accessed.",
                        url=url,
                    )

                videos = []
                playlist_title = info.get("title", "Unknown Playlist")
                playlist_count = len(entries)

                for idx, entry in enumerate(entries, start=1):
                    if entry is None:
                        # Skip unavailable videos
                        continue

                    try:
                        # Create VideoInfo from flat entry
                        video_info = VideoInfo(
                            url=entry.get("url") or entry.get("webpage_url", ""),
                            title=entry.get("title", f"Video {idx}"),
                            uploader=entry.get("uploader") or entry.get("channel"),
                            duration=entry.get("duration"),
                            video_id=entry.get("id"),
                            thumbnail=entry.get("thumbnail"),
                            playlist_index=idx,
                            playlist_title=playlist_title,
                            playlist_count=playlist_count,
                            webpage_url=entry.get("webpage_url"),
                            extractor=entry.get("extractor") or entry.get("ie_key"),
                        )
                        videos.append(video_info)
                    except (ValueError, KeyError):
                        # Skip entries that can't be converted
                        continue

                return videos

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)

            if "Playlist unavailable" in error_msg:
                raise DownloadError(
                    "Playlist is unavailable. It may be private or deleted.",
                    url=url,
                    details=error_msg,
                ) from e

            raise DownloadError(
                f"Failed to extract playlist: {error_msg}",
                url=url,
                details=error_msg,
            ) from e

        except Exception as e:
            raise DownloadError(
                f"Unexpected error while extracting playlist: {e}",
                url=url,
                details=str(e),
            ) from e

    def is_playlist(self, url: str) -> bool:
        """
        Check if a URL is a playlist.

        Args:
            url: The URL to check

        Returns:
            True if the URL is a playlist, False otherwise
        """
        if not url or not url.strip():
            return False

        # Quick check based on URL patterns
        playlist_patterns = [
            "playlist?list=",
            "/playlist/",
            "&list=",
            "/sets/",  # SoundCloud
            "/album/",  # Bandcamp, Spotify
        ]

        url_lower = url.lower()
        for pattern in playlist_patterns:
            if pattern in url_lower:
                return True

        # For ambiguous URLs, try extraction
        try:
            opts = self._get_ydl_opts(
                extract_flat="in_playlist",
                ignoreerrors=True,
            )

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return info.get("_type") == "playlist" or "entries" in info
        except Exception:
            pass

        return False

    def get_playlist_info(self, url: str) -> dict[str, Any]:
        """
        Get basic playlist information without extracting all videos.

        Args:
            url: The playlist URL

        Returns:
            Dictionary with playlist metadata (title, count, uploader, etc.)

        Raises:
            DownloadError: If the URL is invalid or not a playlist
        """
        if not url or not url.strip():
            raise DownloadError("URL cannot be empty", url=url)

        opts = self._get_ydl_opts(
            extract_flat="in_playlist",
            playlistend=1,  # Only get first entry for speed
        )

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    raise DownloadError(
                        "Failed to extract playlist information.",
                        url=url,
                    )

                if info.get("_type") != "playlist" and "entries" not in info:
                    raise DownloadError(
                        "URL is not a playlist.",
                        url=url,
                    )

                return {
                    "title": info.get("title", "Unknown Playlist"),
                    "uploader": info.get("uploader") or info.get("channel"),
                    "count": info.get("playlist_count") or len(info.get("entries", [])),
                    "description": info.get("description"),
                    "thumbnail": info.get("thumbnail"),
                    "webpage_url": info.get("webpage_url"),
                }

        except yt_dlp.utils.DownloadError as e:
            raise DownloadError(
                f"Failed to get playlist info: {e}",
                url=url,
                details=str(e),
            ) from e

        except Exception as e:
            raise DownloadError(
                f"Unexpected error: {e}",
                url=url,
                details=str(e),
            ) from e
