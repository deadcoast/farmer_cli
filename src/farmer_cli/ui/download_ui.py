"""
Download progress UI components for Farmer CLI.

This module provides UI components for displaying download progress,
queue status, and download history.

Feature: farmer-cli-completion
Requirements: 1.3, 4.2, 5.2
"""

from pathlib import Path
from typing import TYPE_CHECKING

from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich.progress import TimeRemainingColumn
from rich.progress import TransferSpeedColumn
from rich.table import Table

from .console import console


if TYPE_CHECKING:
    from ..models.download import QueueItem
    from ..services.download_manager import HistoryEntry


def create_download_progress() -> Progress:
    """
    Create a progress bar for download operations.

    Returns:
        Progress object configured for download display
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )


def create_multi_download_progress() -> Progress:
    """
    Create a progress display for multiple concurrent downloads.

    Returns:
        Progress object configured for multiple downloads
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.fields[title]}", justify="left"),
        BarColumn(bar_width=30),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TransferSpeedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console,
        expand=True,
    )


def display_download_queue(queue: list["QueueItem"]) -> None:
    """
    Display the download queue in a formatted table.

    Args:
        queue: List of QueueItem objects to display
    """
    if not queue:
        console.print("[yellow]Queue is empty[/yellow]")
        return

    table = Table(
        title="Download Queue",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Title", min_width=30, max_width=50)
    table.add_column("Status", width=12)
    table.add_column("Progress", width=10)
    table.add_column("Position", width=8)

    for i, item in enumerate(queue, 1):
        # Format status with color
        status = item.status.value
        status_style = _get_status_style(status)
        status_display = f"[{status_style}]{status}[/{status_style}]"

        # Format progress
        progress_display = f"{item.progress:.1f}%"

        # Format title (truncate if needed)
        title = item.title or item.url[:40]
        if len(title) > 50:
            title = title[:47] + "..."

        table.add_row(
            str(i),
            title,
            status_display,
            progress_display,
            str(item.position),
        )

    console.print(table)


def display_download_history(history: list["HistoryEntry"]) -> None:
    """
    Display download history in a formatted table.

    Args:
        history: List of HistoryEntry objects to display
    """
    if not history:
        console.print("[yellow]No download history[/yellow]")
        return

    table = Table(
        title="Download History",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Title", min_width=30, max_width=45)
    table.add_column("Date", width=16)
    table.add_column("Size", width=10)
    table.add_column("File", width=8)

    for i, entry in enumerate(history, 1):
        # Format title (truncate if needed)
        title = entry.title
        if len(title) > 45:
            title = title[:42] + "..."

        # Format date
        date_str = entry.downloaded_at.strftime("%Y-%m-%d %H:%M")

        # Format file size
        size_str = _format_filesize(entry.file_size)

        # Check file existence
        file_exists = Path(entry.file_path).exists() if entry.file_path else False
        file_status = "[green]✓[/green]" if file_exists else "[red]✗[/red]"

        table.add_row(
            str(i),
            title,
            date_str,
            size_str,
            file_status,
        )

    console.print(table)


def display_video_info_panel(
    title: str,
    uploader: str | None = None,
    duration: str | None = None,
    views: int | None = None,
    formats_count: int = 0,
) -> None:
    """
    Display video information in a formatted panel.

    Args:
        title: Video title
        uploader: Channel/uploader name
        duration: Formatted duration string
        views: View count
        formats_count: Number of available formats
    """
    from rich.panel import Panel

    info_lines = [f"[bold]{title}[/bold]"]

    if uploader:
        info_lines.append(f"Channel: {uploader}")
    if duration:
        info_lines.append(f"Duration: {duration}")
    if views:
        info_lines.append(f"Views: {views:,}")
    if formats_count:
        info_lines.append(f"Available formats: {formats_count}")

    panel = Panel(
        "\n".join(info_lines),
        title="Video Information",
        border_style="cyan",
    )
    console.print(panel)


def display_format_selection(
    video_formats: list,
    audio_formats: list,
) -> None:
    """
    Display available formats for selection.

    Args:
        video_formats: List of video format dictionaries
        audio_formats: List of audio format dictionaries
    """
    if video_formats:
        console.print("\n[bold cyan]Video Formats:[/bold cyan]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("#", width=4)
        table.add_column("Resolution", width=12)
        table.add_column("Format", width=8)
        table.add_column("Size", width=12)
        table.add_column("Codec", width=15)

        for i, fmt in enumerate(video_formats, 1):
            table.add_row(
                str(i),
                fmt.get("resolution", "N/A"),
                fmt.get("extension", "N/A"),
                fmt.get("filesize", "Unknown"),
                fmt.get("codec", "N/A"),
            )
        console.print(table)

    if audio_formats:
        console.print("\n[bold cyan]Audio Formats:[/bold cyan]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("#", width=4)
        table.add_column("Format", width=8)
        table.add_column("Bitrate", width=12)
        table.add_column("Size", width=12)

        offset = len(video_formats) if video_formats else 0
        for i, fmt in enumerate(audio_formats, offset + 1):
            table.add_row(
                str(i),
                fmt.get("extension", "N/A"),
                fmt.get("bitrate", "N/A"),
                fmt.get("filesize", "Unknown"),
            )
        console.print(table)


def display_batch_progress(
    current: int,
    total: int,
    current_title: str,
    successes: int,
    failures: int,
) -> None:
    """
    Display batch download progress.

    Args:
        current: Current video number
        total: Total videos
        current_title: Title of current video
        successes: Number of successful downloads
        failures: Number of failed downloads
    """
    console.print(
        f"\n[bold]Progress:[/bold] {current}/{total} "
        f"([green]{successes} ✓[/green] / [red]{failures} ✗[/red])"
    )
    console.print(f"[dim]Current: {current_title[:50]}...[/dim]")


def display_download_complete(
    file_path: str,
    file_size: int | None = None,
    duration: float | None = None,
) -> None:
    """
    Display download completion message.

    Args:
        file_path: Path to downloaded file
        file_size: Size of downloaded file in bytes
        duration: Download duration in seconds
    """
    console.print("\n[bold green]✓ Download Complete![/bold green]")
    console.print(f"  File: {file_path}")

    if file_size:
        console.print(f"  Size: {_format_filesize(file_size)}")

    if duration:
        if duration >= 60:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            console.print(f"  Time: {minutes}m {seconds}s")
        else:
            console.print(f"  Time: {duration:.1f}s")


def display_download_failed(
    error_message: str,
    url: str | None = None,
) -> None:
    """
    Display download failure message.

    Args:
        error_message: Error description
        url: URL that failed (optional)
    """
    console.print("\n[bold red]✗ Download Failed[/bold red]")
    console.print(f"  Error: {error_message}")
    if url:
        console.print(f"  URL: {url[:60]}...")


def _get_status_style(status: str) -> str:
    """Get Rich style for a download status."""
    status_styles = {
        "pending": "yellow",
        "downloading": "cyan",
        "completed": "green",
        "failed": "red",
        "paused": "magenta",
        "cancelled": "dim",
    }
    return status_styles.get(status.lower(), "white")


def _format_filesize(size: int | None) -> str:
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
