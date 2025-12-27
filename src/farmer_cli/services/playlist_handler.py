"""
Playlist handler service for processing and downloading video playlists.

This module provides the PlaylistHandler class for enumerating playlist videos
and managing batch downloads with concurrent execution.

Feature: farmer-cli-completion
Requirements: 3.1, 3.3, 3.4, 3.5, 3.6
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Callable

from ..exceptions import DownloadError
from ..exceptions import PlaylistError
from .ytdlp_wrapper import VideoInfo
from .ytdlp_wrapper import YtdlpWrapper


logger = logging.getLogger(__name__)


@dataclass
class BatchDownloadResult:
    """
    Result of a batch download operation.

    Attributes:
        successes: List of successfully downloaded file paths
        failures: List of tuples (url, error_message) for failed downloads
        total: Total number of videos attempted
        success_count: Number of successful downloads
        failure_count: Number of failed downloads
    """

    successes: list[str] = field(default_factory=list)
    failures: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Get total number of videos attempted."""
        return len(self.successes) + len(self.failures)

    @property
    def success_count(self) -> int:
        """Get number of successful downloads."""
        return len(self.successes)

    @property
    def failure_count(self) -> int:
        """Get number of failed downloads."""
        return len(self.failures)

    def summary(self) -> str:
        """Generate a summary report of the batch download."""
        lines = [
            "Batch Download Summary",
            "=" * 40,
            f"Total videos: {self.total}",
            f"Successful: {self.success_count}",
            f"Failed: {self.failure_count}",
        ]

        if self.failures:
            lines.append("")
            lines.append("Failed downloads:")
            for url, error in self.failures:
                # Truncate URL for display
                display_url = url[:50] + "..." if len(url) > 50 else url
                lines.append(f"  - {display_url}: {error}")

        return "\n".join(lines)


class PlaylistHandler:
    """
    Handles playlist enumeration and batch downloads.

    This class provides methods for extracting videos from playlists,
    selecting ranges of videos, and downloading multiple videos concurrently.

    Attributes:
        ytdlp_wrapper: YtdlpWrapper instance for video operations
    """

    DEFAULT_MAX_CONCURRENT = 3
    MIN_CONCURRENT = 1
    MAX_CONCURRENT = 5

    def __init__(self, ytdlp_wrapper: YtdlpWrapper | None = None) -> None:
        """
        Initialize the playlist handler.

        Args:
            ytdlp_wrapper: Optional YtdlpWrapper instance (creates one if not provided)
        """
        self._ytdlp_wrapper = ytdlp_wrapper or YtdlpWrapper()

    @property
    def ytdlp_wrapper(self) -> YtdlpWrapper:
        """Get the yt-dlp wrapper instance."""
        return self._ytdlp_wrapper

    def enumerate_playlist(self, url: str) -> list[VideoInfo]:
        """
        Get all videos in a playlist.

        Extracts video information for all entries in a playlist URL.
        Handles pagination for large playlists automatically.

        Args:
            url: The playlist URL to enumerate

        Returns:
            List of VideoInfo objects for each video in the playlist

        Raises:
            PlaylistError: If the URL is invalid or playlist extraction fails
        """
        if not url or not url.strip():
            raise PlaylistError("URL cannot be empty", playlist_url=url)

        url = url.strip()

        try:
            videos = self._ytdlp_wrapper.extract_playlist(url)

            if not videos:
                raise PlaylistError(
                    "Playlist is empty or could not be accessed.",
                    playlist_url=url,
                )

            logger.info(f"Enumerated {len(videos)} videos from playlist: {url[:50]}...")
            return videos

        except DownloadError as e:
            raise PlaylistError(
                f"Failed to enumerate playlist: {e.message}",
                playlist_url=url,
                details=e.details,
            ) from e

        except Exception as e:
            raise PlaylistError(
                f"Unexpected error while enumerating playlist: {e}",
                playlist_url=url,
                details=str(e),
            ) from e

    def get_range(
        self,
        videos: list[VideoInfo],
        start: int,
        end: int,
    ) -> list[VideoInfo]:
        """
        Get a range of videos from a playlist.

        Extracts a subset of videos from the playlist based on 1-indexed
        start and end positions (inclusive).

        Args:
            videos: List of VideoInfo objects from enumerate_playlist
            start: Start position (1-indexed, inclusive)
            end: End position (1-indexed, inclusive)

        Returns:
            List of VideoInfo objects in the specified range

        Raises:
            ValueError: If start or end are invalid
            PlaylistError: If the range is invalid for the playlist
        """
        if not videos:
            raise PlaylistError("Video list is empty")

        # Validate range parameters
        if start < 1:
            raise ValueError("Start position must be at least 1")
        if end < start:
            raise ValueError("End position must be greater than or equal to start")

        # Convert to 0-indexed for slicing
        start_idx = start - 1
        end_idx = end  # end is inclusive, so we use end (not end-1) for slice

        # Clamp to valid range
        total_videos = len(videos)
        if start_idx >= total_videos:
            raise PlaylistError(
                f"Start position {start} exceeds playlist length ({total_videos})",
            )

        # Clamp end to playlist length
        end_idx = min(end_idx, total_videos)

        selected = videos[start_idx:end_idx]
        logger.info(f"Selected {len(selected)} videos (positions {start}-{min(end, total_videos)})")
        return selected

    def download_batch(
        self,
        videos: list[VideoInfo],
        output_dir: str | Path,
        format_id: str | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> BatchDownloadResult:
        """
        Download multiple videos concurrently.

        Downloads a list of videos with configurable concurrency. Tracks
        successes and failures separately, ensuring that individual failures
        do not affect other downloads.

        Args:
            videos: List of VideoInfo objects to download
            output_dir: Directory to save downloaded files
            format_id: Optional format ID for all downloads
            max_concurrent: Maximum concurrent downloads (1-5)
            progress_callback: Optional callback(url, current, total) for progress

        Returns:
            BatchDownloadResult with successes and failures

        Raises:
            PlaylistError: If output_dir is invalid
        """
        if not videos:
            return BatchDownloadResult()

        # Validate and clamp max_concurrent
        max_concurrent = max(self.MIN_CONCURRENT, min(max_concurrent, self.MAX_CONCURRENT))

        # Validate output directory
        output_path = Path(output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise PlaylistError(
                f"Cannot create output directory: {e}",
                details=str(e),
            ) from e

        result = BatchDownloadResult()
        total = len(videos)

        logger.info(f"Starting batch download of {total} videos with {max_concurrent} concurrent downloads")

        def download_single(video: VideoInfo, index: int) -> tuple[bool, str, str | None]:
            """
            Download a single video.

            Returns:
                Tuple of (success, url, file_path_or_error)
            """
            url = video.webpage_url or video.url
            try:
                file_path = self._ytdlp_wrapper.download(
                    url=url,
                    output_path=output_path,
                    format_id=format_id,
                )
                logger.info(f"Downloaded ({index + 1}/{total}): {video.title[:50]}...")
                return (True, url, file_path)
            except DownloadError as e:
                logger.warning(f"Failed ({index + 1}/{total}): {video.title[:50]}... - {e.message}")
                return (False, url, e.message)
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Failed ({index + 1}/{total}): {video.title[:50]}... - {error_msg}")
                return (False, url, error_msg)

        # Use ThreadPoolExecutor for concurrent downloads
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all download tasks
            future_to_video = {
                executor.submit(download_single, video, idx): video
                for idx, video in enumerate(videos)
            }

            # Process completed downloads
            completed = 0
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                completed += 1

                try:
                    success, url, result_data = future.result()

                    if success:
                        result.successes.append(result_data)
                    else:
                        result.failures.append((url, result_data))

                except Exception as e:
                    # Handle unexpected exceptions from the future
                    url = video.webpage_url or video.url
                    result.failures.append((url, str(e)))
                    logger.error(f"Unexpected error downloading {url}: {e}")

                # Call progress callback if provided
                if progress_callback:
                    try:
                        progress_callback(video.url, completed, total)
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")

        logger.info(f"Batch download complete: {result.success_count} succeeded, {result.failure_count} failed")
        return result

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

        return self._ytdlp_wrapper.is_playlist(url)

    def get_playlist_info(self, url: str) -> dict:
        """
        Get basic playlist information without extracting all videos.

        Args:
            url: The playlist URL

        Returns:
            Dictionary with playlist metadata (title, count, uploader, etc.)

        Raises:
            PlaylistError: If the URL is invalid or not a playlist
        """
        if not url or not url.strip():
            raise PlaylistError("URL cannot be empty", playlist_url=url)

        try:
            return self._ytdlp_wrapper.get_playlist_info(url)
        except DownloadError as e:
            raise PlaylistError(
                f"Failed to get playlist info: {e.message}",
                playlist_url=url,
                details=e.details,
            ) from e

    def download_playlist(
        self,
        url: str,
        output_dir: str | Path,
        format_id: str | None = None,
        start: int | None = None,
        end: int | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> BatchDownloadResult:
        """
        Download a playlist with optional range selection.

        Convenience method that combines enumerate_playlist, get_range,
        and download_batch into a single operation.

        Args:
            url: The playlist URL
            output_dir: Directory to save downloaded files
            format_id: Optional format ID for all downloads
            start: Optional start position (1-indexed, inclusive)
            end: Optional end position (1-indexed, inclusive)
            max_concurrent: Maximum concurrent downloads (1-5)
            progress_callback: Optional callback(url, current, total) for progress

        Returns:
            BatchDownloadResult with successes and failures

        Raises:
            PlaylistError: If playlist extraction or download fails
        """
        # Enumerate playlist
        videos = self.enumerate_playlist(url)

        # Apply range if specified
        if start is not None or end is not None:
            start = start or 1
            end = end or len(videos)
            videos = self.get_range(videos, start, end)

        # Download batch
        return self.download_batch(
            videos=videos,
            output_dir=output_dir,
            format_id=format_id,
            max_concurrent=max_concurrent,
            progress_callback=progress_callback,
        )
