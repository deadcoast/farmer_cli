"""
Video downloader feature for Farmer CLI.

This module provides the video downloading functionality including
single video downloads, playlist handling, queue management, and
download history.

Feature: farmer-cli-completion
Requirements: 1.1, 2.1, 2.3, 3.1, 3.2, 3.5, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 5.6
"""

import logging
from pathlib import Path

from ..core.database import get_session
from ..exceptions import DownloadError
from ..exceptions import FormatError
from ..exceptions import PlaylistError
from ..services.download_manager import DownloadManager
from ..services.format_selector import FormatSelector
from ..services.playlist_handler import PlaylistHandler
from ..services.preferences import PreferencesService
from ..services.ytdlp_wrapper import DownloadProgress
from ..services.ytdlp_wrapper import DownloadStatus
from ..services.ytdlp_wrapper import VideoFormat
from ..services.ytdlp_wrapper import VideoInfo
from ..services.ytdlp_wrapper import YtdlpWrapper
from ..ui.console import console
from ..ui.menu import MenuManager
from ..ui.prompts import choice_prompt
from ..ui.prompts import confirm_prompt
from ..ui.prompts import int_prompt
from ..ui.prompts import text_prompt
from ..utils.url_utils import is_valid_url
from .base import BaseFeature


logger = logging.getLogger(__name__)


# Submenu options for video downloader
VIDEO_DOWNLOADER_OPTIONS = [
    ("1", "Download Single Video"),
    ("2", "Download Playlist"),
    ("3", "View Download Queue"),
    ("4", "View Download History"),
    ("5", "Settings"),
    ("0", "Return to Main Menu"),
]


class VideoDownloaderFeature(BaseFeature):
    """
    Video downloader feature implementation.

    Provides video downloading functionality including single video downloads,
    playlist handling, queue management, and download history.
    """

    def __init__(
        self,
        preferences_service: PreferencesService | None = None,
    ) -> None:
        """
        Initialize the video downloader feature.

        Args:
            preferences_service: Optional preferences service for settings persistence
        """
        super().__init__(
            name="Video Downloader",
            description="Download videos from various platforms",
        )
        self.menu_manager = MenuManager()
        self._preferences_service = preferences_service or PreferencesService()

        # Initialize services
        self._ytdlp_wrapper = YtdlpWrapper()
        self._format_selector = FormatSelector(
            ytdlp_wrapper=self._ytdlp_wrapper,
            preferences_service=self._preferences_service,
        )
        self._playlist_handler = PlaylistHandler(ytdlp_wrapper=self._ytdlp_wrapper)
        self._download_manager = DownloadManager(
            session_factory=get_session,
            default_output_path=self._get_default_output_path(),
        )

    def _get_default_output_path(self) -> Path:
        """Get the default output path from preferences or use default."""
        default_path = self._preferences_service.get("download_directory")
        if default_path:
            return Path(default_path)
        return Path.home() / "Downloads" / "FarmerCLI"

    @property
    def ytdlp_wrapper(self) -> YtdlpWrapper:
        """Get the yt-dlp wrapper instance."""
        return self._ytdlp_wrapper

    @property
    def format_selector(self) -> FormatSelector:
        """Get the format selector instance."""
        return self._format_selector

    @property
    def playlist_handler(self) -> PlaylistHandler:
        """Get the playlist handler instance."""
        return self._playlist_handler

    @property
    def download_manager(self) -> DownloadManager:
        """Get the download manager instance."""
        return self._download_manager

    def execute(self) -> None:
        """Execute the video downloader feature with submenu."""
        while True:
            choice = self.menu_manager.display_submenu(
                "Video Downloader",
                VIDEO_DOWNLOADER_OPTIONS,
            )

            if choice is None:
                break

            if choice == "1":
                self._download_single_video()
            elif choice == "2":
                self._download_playlist()
            elif choice == "3":
                self._view_download_queue()
            elif choice == "4":
                self._view_download_history()
            elif choice == "5":
                self._settings_menu()

    def _download_single_video(self) -> None:
        """Handle single video download workflow."""
        console.clear()
        console.print("[bold cyan]Download Single Video[/bold cyan]\n")

        # Get URL from user
        url = text_prompt(
            "Enter video URL",
            validator=is_valid_url,
            error_message="Please enter a valid URL",
        )

        if not url:
            return

        try:
            # Check if this is a playlist URL
            if self._playlist_handler.is_playlist(url):
                if confirm_prompt(
                    "This appears to be a playlist. Download as playlist instead?"
                ):
                    self._handle_playlist_download(url)
                    return

            # Check for duplicates
            duplicate = self._download_manager.check_duplicate(url)
            if duplicate:
                console.print(
                    "\n[yellow]⚠ This video was previously downloaded:[/yellow]"
                )
                console.print(f"  Title: {duplicate.title}")
                console.print(f"  Date: {duplicate.downloaded_at.strftime('%Y-%m-%d %H:%M')}")
                console.print(f"  File: {duplicate.file_path}")

                if duplicate.file_exists:
                    console.print("  [green]✓ File still exists[/green]")
                else:
                    console.print("  [red]✗ File no longer exists[/red]")

                if not confirm_prompt("Download anyway?"):
                    console.input("\nPress Enter to continue...")
                    return

            # Extract video info
            console.print("\n[dim]Fetching video information...[/dim]")
            video_info = self._ytdlp_wrapper.extract_info(url)

            # Display video info
            self._display_video_info(video_info)

            # Get format selection
            selected_format = self._select_format(video_info)
            if selected_format is None:
                console.input("\nPress Enter to continue...")
                return

            # Get output path
            output_path = self._get_output_path()

            # Start download with progress
            console.print("\n[bold green]Starting download...[/bold green]")
            self._download_with_progress(
                url=url,
                output_path=output_path,
                format_id=selected_format.format_id,
                video_info=video_info,
            )

        except DownloadError as e:
            console.print(f"\n[bold red]Download error: {e.message}[/bold red]")
            logger.error(f"Download error: {e}")
        except FormatError as e:
            console.print(f"\n[bold red]Format error: {e.message}[/bold red]")
            logger.error(f"Format error: {e}")
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
            logger.error(f"Unexpected error in single video download: {e}", exc_info=True)

        console.input("\nPress Enter to continue...")

    def _download_playlist(self) -> None:
        """Handle playlist download workflow."""
        console.clear()
        console.print("[bold cyan]Download Playlist[/bold cyan]\n")

        # Get URL from user
        url = text_prompt(
            "Enter playlist URL",
            validator=is_valid_url,
            error_message="Please enter a valid URL",
        )

        if not url:
            return

        try:
            self._handle_playlist_download(url)
        except PlaylistError as e:
            console.print(f"\n[bold red]Playlist error: {e.message}[/bold red]")
            logger.error(f"Playlist error: {e}")
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
            logger.error(f"Unexpected error in playlist download: {e}", exc_info=True)

        console.input("\nPress Enter to continue...")

    def _handle_playlist_download(self, url: str) -> None:
        """
        Handle the playlist download workflow.

        Args:
            url: Playlist URL
        """
        # Get playlist info first
        console.print("\n[dim]Fetching playlist information...[/dim]")
        playlist_info = self._playlist_handler.get_playlist_info(url)

        console.print(f"\n[bold]Playlist: {playlist_info['title']}[/bold]")
        if playlist_info.get("uploader"):
            console.print(f"Channel: {playlist_info['uploader']}")
        console.print(f"Videos: {playlist_info['count']}")

        # Enumerate videos
        console.print("\n[dim]Loading video list...[/dim]")
        videos = self._playlist_handler.enumerate_playlist(url)

        # Display video list
        self._display_playlist_videos(videos)

        # Get selection options
        selection = self._get_playlist_selection(len(videos))
        if selection is None:
            return

        start, end = selection

        # Get selected videos
        if start == 1 and end == len(videos):
            selected_videos = videos
        else:
            selected_videos = self._playlist_handler.get_range(videos, start, end)

        console.print(f"\n[green]Selected {len(selected_videos)} videos for download[/green]")

        # Get output path
        output_path = self._get_output_path()

        # Create subdirectory for playlist
        playlist_dir = output_path / self._sanitize_filename(playlist_info["title"])
        playlist_dir.mkdir(parents=True, exist_ok=True)

        # Queue videos for download
        if confirm_prompt("Add to download queue?"):
            for video in selected_videos:
                self._download_manager.add_to_queue(
                    url=video.webpage_url or video.url,
                    output_path=str(playlist_dir),
                    title=video.title,
                )
            console.print(
                f"\n[green]✓ Added {len(selected_videos)} videos to download queue[/green]"
            )
        else:
            # Download immediately
            console.print("\n[bold green]Starting batch download...[/bold green]")
            result = self._playlist_handler.download_batch(
                videos=selected_videos,
                output_dir=playlist_dir,
                progress_callback=self._batch_progress_callback,
            )

            # Display summary
            console.print(f"\n{result.summary()}")

            # Add successful downloads to history
            for file_path in result.successes:
                path = Path(file_path)
                if path.exists():
                    # Find matching video info
                    for video in selected_videos:
                        if video.title in path.name:
                            self._download_manager.add_to_history(
                                url=video.webpage_url or video.url,
                                title=video.title,
                                file_path=str(path),
                                file_size=path.stat().st_size,
                                duration=video.duration,
                                uploader=video.uploader,
                            )
                            break

    def _view_download_queue(self) -> None:
        """Display and manage the download queue."""
        from ..ui.download_ui import display_download_queue

        while True:
            console.clear()
            console.print("[bold cyan]Download Queue[/bold cyan]\n")

            queue = self._download_manager.get_queue(include_completed=False)

            if not queue:
                console.print("[yellow]Queue is empty[/yellow]")
                console.input("\nPress Enter to continue...")
                return

            # Display queue
            display_download_queue(queue)

            # Queue management options
            console.print("\n[bold]Options:[/bold]")
            console.print("  [1] Pause/Resume download")
            console.print("  [2] Cancel download")
            console.print("  [3] Reorder queue")
            console.print("  [4] Clear completed")
            console.print("  [0] Return")

            choice = text_prompt("Select option", default="0")

            if choice == "0":
                break
            elif choice == "1":
                self._pause_resume_download(queue)
            elif choice == "2":
                self._cancel_download(queue)
            elif choice == "3":
                self._reorder_queue(queue)
            elif choice == "4":
                count = self._download_manager.clear_completed()
                console.print(f"[green]Cleared {count} completed items[/green]")
                console.input("\nPress Enter to continue...")

    def _view_download_history(self) -> None:
        """Display and manage download history."""
        from ..ui.download_ui import display_download_history

        search_term = None

        while True:
            console.clear()
            console.print("[bold cyan]Download History[/bold cyan]\n")

            # Get history with optional search
            history = self._download_manager.get_history(search=search_term, limit=20)
            total_count = self._download_manager.get_history_count(search=search_term)

            if not history:
                if search_term:
                    console.print(f"[yellow]No results for '{search_term}'[/yellow]")
                else:
                    console.print("[yellow]No download history[/yellow]")
            else:
                display_download_history(history)
                console.print(f"\n[dim]Showing {len(history)} of {total_count} entries[/dim]")

            # History management options
            console.print("\n[bold]Options:[/bold]")
            console.print("  [1] Search history")
            console.print("  [2] Clear search")
            console.print("  [3] Remove entry")
            console.print("  [4] Clear all history")
            console.print("  [0] Return")

            choice = text_prompt("Select option", default="0")

            if choice == "0":
                break
            elif choice == "1":
                search_term = text_prompt("Enter search term")
            elif choice == "2":
                search_term = None
            elif choice == "3":
                if history:
                    entry_num = int_prompt(
                        "Enter entry number to remove",
                        min_value=1,
                        max_value=len(history),
                    )
                    entry = history[entry_num - 1]
                    if confirm_prompt(f"Remove '{entry.title}'?"):
                        self._download_manager.remove_from_history(entry.id)
                        console.print("[green]Entry removed[/green]")
            elif choice == "4":
                if confirm_prompt("Clear all download history?", default=False):
                    count = self._download_manager.clear_history()
                    console.print(f"[green]Cleared {count} entries[/green]")
                    console.input("\nPress Enter to continue...")

    def _settings_menu(self) -> None:
        """Display and manage download settings."""
        while True:
            console.clear()
            console.print("[bold cyan]Download Settings[/bold cyan]\n")

            # Display current settings
            current_path = self._get_default_output_path()
            default_format = self._format_selector.get_default_format() or "best"
            max_concurrent = self._download_manager.max_concurrent

            console.print("[bold]Current Settings:[/bold]")
            console.print(f"  Download directory: {current_path}")
            console.print(f"  Default format: {default_format}")
            console.print(f"  Max concurrent downloads: {max_concurrent}")

            console.print("\n[bold]Options:[/bold]")
            console.print("  [1] Change download directory")
            console.print("  [2] Set default format")
            console.print("  [3] Set max concurrent downloads")
            console.print("  [0] Return")

            choice = text_prompt("Select option", default="0")

            if choice == "0":
                break
            elif choice == "1":
                new_path = text_prompt(
                    "Enter download directory",
                    default=str(current_path),
                )
                if new_path:
                    path = Path(new_path).expanduser()
                    path.mkdir(parents=True, exist_ok=True)
                    self._preferences_service.set("download_directory", str(path))
                    console.print(f"[green]Download directory set to: {path}[/green]")
            elif choice == "2":
                format_choice = choice_prompt(
                    "Select default format",
                    choices=["best", "1080p", "720p", "480p", "360p", "audio"],
                    default=default_format,
                )
                self._format_selector.set_default_format(format_choice)
                console.print(f"[green]Default format set to: {format_choice}[/green]")
            elif choice == "3":
                new_max = int_prompt(
                    "Enter max concurrent downloads (1-5)",
                    default=max_concurrent,
                    min_value=1,
                    max_value=5,
                )
                self._download_manager.set_max_concurrent(new_max)
                console.print(f"[green]Max concurrent downloads set to: {new_max}[/green]")

            console.input("\nPress Enter to continue...")

    def _display_video_info(self, video_info: VideoInfo) -> None:
        """Display video information."""
        console.print(f"\n[bold]Title:[/bold] {video_info.title}")
        if video_info.uploader:
            console.print(f"[bold]Channel:[/bold] {video_info.uploader}")
        if video_info.duration:
            console.print(f"[bold]Duration:[/bold] {video_info.duration_formatted}")
        if video_info.view_count:
            console.print(f"[bold]Views:[/bold] {video_info.view_count:,}")

    def _select_format(self, video_info: VideoInfo) -> VideoFormat | None:
        """
        Let user select a format for download.

        Args:
            video_info: Video information with available formats

        Returns:
            Selected VideoFormat or None if cancelled
        """
        formats = video_info.formats
        if not formats:
            console.print("[yellow]No formats available[/yellow]")
            return None

        # Get video and audio formats
        video_formats = self._format_selector.get_video_formats(formats)
        audio_formats = self._format_selector.get_audio_formats(formats)

        console.print("\n[bold]Available Formats:[/bold]")

        # Display video formats
        if video_formats:
            console.print("\n[cyan]Video formats:[/cyan]")
            for i, fmt in enumerate(video_formats[:10], 1):
                size_str = self._format_filesize(fmt.filesize)
                console.print(
                    f"  [{i}] {fmt.resolution or 'N/A'} - {fmt.extension} - {size_str}"
                )

        # Display audio formats
        if audio_formats:
            console.print("\n[cyan]Audio only:[/cyan]")
            offset = len(video_formats[:10])
            for i, fmt in enumerate(audio_formats[:5], offset + 1):
                size_str = self._format_filesize(fmt.filesize)
                bitrate = f"{fmt.abr:.0f}kbps" if fmt.abr else "N/A"
                console.print(
                    f"  [{i}] {fmt.extension} - {bitrate} - {size_str}"
                )

        console.print("\n  [0] Cancel")
        console.print("  [b] Best quality (default)")

        # Get selection
        all_formats = video_formats[:10] + audio_formats[:5]
        choice = text_prompt("Select format", default="b")

        if choice == "0":
            return None
        if choice.lower() == "b":
            return self._format_selector.get_best_format(formats)

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(all_formats):
                return all_formats[idx]
        except ValueError:
            pass

        console.print("[yellow]Invalid selection, using best quality[/yellow]")
        return self._format_selector.get_best_format(formats)

    def _get_output_path(self) -> Path:
        """Get output path from user or use default."""
        default_path = self._get_default_output_path()

        if confirm_prompt(f"Save to {default_path}?", default=True):
            default_path.mkdir(parents=True, exist_ok=True)
            return default_path

        custom_path = text_prompt(
            "Enter output directory",
            default=str(default_path),
        )
        path = Path(custom_path).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _download_with_progress(
        self,
        url: str,
        output_path: Path,
        format_id: str | None,
        video_info: VideoInfo,
    ) -> None:
        """
        Download video with progress display.

        Args:
            url: Video URL
            output_path: Output directory
            format_id: Format ID to download
            video_info: Video information
        """
        from ..ui.download_ui import create_download_progress

        with create_download_progress() as progress:
            task_id = progress.add_task(
                f"[cyan]{video_info.title[:40]}...",
                total=100,
            )

            def progress_callback(prog: DownloadProgress) -> None:
                progress.update(
                    task_id,
                    completed=prog.percent,
                    description=f"[cyan]{video_info.title[:30]}... {prog.speed_formatted}",
                )

            try:
                file_path = self._ytdlp_wrapper.download(
                    url=url,
                    output_path=output_path,
                    format_id=format_id,
                    progress_callback=progress_callback,
                )

                progress.update(task_id, completed=100)

                # Add to history
                path = Path(file_path)
                self._download_manager.add_to_history(
                    url=url,
                    title=video_info.title,
                    file_path=file_path,
                    file_size=path.stat().st_size if path.exists() else None,
                    duration=video_info.duration,
                    uploader=video_info.uploader,
                )

                console.print("\n[bold green]✓ Download complete![/bold green]")
                console.print(f"  Saved to: {file_path}")

            except DownloadError as e:
                progress.update(task_id, description=f"[red]Failed: {e.message[:30]}...")
                raise

    def _display_playlist_videos(self, videos: list[VideoInfo]) -> None:
        """Display list of videos in a playlist."""
        console.print(f"\n[bold]Videos ({len(videos)} total):[/bold]")

        for i, video in enumerate(videos[:20], 1):
            duration = video.duration_formatted if video.duration else "N/A"
            console.print(f"  {i:3}. {video.title[:50]} [{duration}]")

        if len(videos) > 20:
            console.print(f"  ... and {len(videos) - 20} more")

    def _get_playlist_selection(self, total: int) -> tuple[int, int] | None:
        """
        Get user selection for playlist range.

        Args:
            total: Total number of videos

        Returns:
            Tuple of (start, end) or None if cancelled
        """
        console.print("\n[bold]Selection Options:[/bold]")
        console.print("  [1] Download all")
        console.print("  [2] Select range")
        console.print("  [0] Cancel")

        choice = text_prompt("Select option", default="1")

        if choice == "0":
            return None
        if choice == "1":
            return (1, total)
        if choice == "2":
            start = int_prompt("Start position", default=1, min_value=1, max_value=total)
            end = int_prompt("End position", default=total, min_value=start, max_value=total)
            return (start, end)

        return (1, total)

    def _batch_progress_callback(self, _url: str, current: int, total: int) -> None:
        """Callback for batch download progress."""
        console.print(f"  [{current}/{total}] Completed")

    def _pause_resume_download(self, queue: list) -> None:
        """Pause or resume a download."""
        entry_num = int_prompt(
            "Enter queue number",
            min_value=1,
            max_value=len(queue),
        )
        item = queue[entry_num - 1]

        if item.status == DownloadStatus.PAUSED:
            if self._download_manager.resume_download(item.id):
                console.print("[green]Download resumed[/green]")
        elif item.status == DownloadStatus.DOWNLOADING:
            if self._download_manager.pause_download(item.id):
                console.print("[green]Download paused[/green]")
        else:
            console.print("[yellow]Cannot pause/resume this item[/yellow]")

        console.input("\nPress Enter to continue...")

    def _cancel_download(self, queue: list) -> None:
        """Cancel a download."""
        entry_num = int_prompt(
            "Enter queue number to cancel",
            min_value=1,
            max_value=len(queue),
        )
        item = queue[entry_num - 1]

        if confirm_prompt(f"Cancel download of '{item.title or item.url[:30]}'?"):
            if self._download_manager.cancel_download(item.id):
                console.print("[green]Download cancelled[/green]")
            else:
                console.print("[yellow]Could not cancel download[/yellow]")

        console.input("\nPress Enter to continue...")

    def _reorder_queue(self, queue: list) -> None:
        """Reorder queue items."""
        entry_num = int_prompt(
            "Enter queue number to move",
            min_value=1,
            max_value=len(queue),
        )
        item = queue[entry_num - 1]

        new_pos = int_prompt(
            "Enter new position",
            min_value=1,
            max_value=len(queue),
        )

        if self._download_manager.reorder_queue(item.id, new_pos - 1):
            console.print("[green]Queue reordered[/green]")
        else:
            console.print("[yellow]Could not reorder queue[/yellow]")

        console.input("\nPress Enter to continue...")

    def _format_filesize(self, size: int | None) -> str:
        """Format file size for display."""
        if not size:
            return "Unknown"
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} B"

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        return name.strip()[:100]  # Limit length

    def cleanup(self) -> None:
        """Cleanup the video downloader feature."""
        # No specific cleanup needed
        pass
