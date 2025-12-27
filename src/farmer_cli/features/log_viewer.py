"""
Log viewer feature for Farmer CLI.

This module provides a UI for viewing recent log entries with
filtering by log level.

Feature: farmer-cli-completion
Requirements: 10.6
"""

from typing import Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..core.logging_config import VALID_LOG_LEVELS, get_logging_config
from ..ui.console import console
from .base import BaseFeature


# Log level colors for display
LEVEL_COLORS = {
    "DEBUG": "dim",
    "INFO": "blue",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold red",
}


class LogViewerFeature(BaseFeature):
    """
    Log viewer feature implementation.

    Provides functionality to view and filter recent log entries.
    """

    def __init__(self):
        """Initialize the log viewer feature."""
        super().__init__(
            name="Log Viewer",
            description="View recent application log entries",
        )
        self._default_count = 50

    def execute(self) -> None:
        """Execute the log viewer feature."""
        while True:
            choice = self._show_menu()

            if choice is None or choice == "0":
                break

            if choice == "1":
                self._view_all_logs()
            elif choice == "2":
                self._view_filtered_logs()
            elif choice == "3":
                self._view_log_file_path()
            elif choice == "4":
                self._clear_logs()

    def _show_menu(self) -> Optional[str]:
        """
        Show the log viewer menu.

        Returns:
            Selected menu option or None
        """
        options = [
            ("1", "View Recent Logs"),
            ("2", "Filter by Level"),
            ("3", "Show Log File Path"),
            ("4", "Clear Log File"),
            ("0", "Return to Main Menu"),
        ]

        console.print()
        console.print(Panel("[bold]Log Viewer[/bold]", expand=False))

        for key, label in options:
            console.print(f"  [{key}] {label}")

        console.print()
        choice = console.input("[bold cyan]Select option:[/bold cyan] ").strip()

        return choice if choice in ["0", "1", "2", "3", "4"] else None

    def _view_all_logs(self, count: int = 50) -> None:
        """
        View all recent log entries.

        Args:
            count: Number of entries to display
        """
        config = get_logging_config()
        entries = config.get_recent_logs(count=count)

        if not entries:
            console.print("[yellow]No log entries found.[/yellow]")
            console.input("\nPress Enter to continue...")
            return

        self._display_log_entries(entries, title="Recent Log Entries")
        console.input("\nPress Enter to continue...")

    def _view_filtered_logs(self) -> None:
        """View log entries filtered by level."""
        # Let user select a log level
        level_options = [(level, level) for level in VALID_LOG_LEVELS]
        level_options.append(("ALL", "All Levels"))

        console.print()
        console.print("[bold]Select log level to filter:[/bold]")
        for i, (level, label) in enumerate(level_options, 1):
            color = LEVEL_COLORS.get(level, "white")
            console.print(f"  [{i}] [{color}]{label}[/{color}]")

        console.print()
        choice = console.input("[bold cyan]Select level:[/bold cyan] ").strip()

        try:
            index = int(choice) - 1
            if 0 <= index < len(level_options):
                selected_level = level_options[index][0]
            else:
                console.print("[red]Invalid selection.[/red]")
                console.input("\nPress Enter to continue...")
                return
        except ValueError:
            console.print("[red]Invalid selection.[/red]")
            console.input("\nPress Enter to continue...")
            return

        # Get filtered logs
        config = get_logging_config()

        if selected_level == "ALL":
            entries = config.get_recent_logs(count=self._default_count)
            title = "All Log Entries"
        else:
            entries = config.get_recent_logs(
                count=self._default_count,
                level_filter=selected_level
   )
            title = f"Log Entries - {selected_level}"

        if not entries:
            console.print(f"[yellow]No {selected_level} log entries found.[/yellow]")
            console.input("\nPress Enter to continue...")
            return

        self._display_log_entries(entries, title=title)
        console.input("\nPress Enter to continue...")

    def _view_log_file_path(self) -> None:
        """Display the current log file path."""
        config = get_logging_config()
        log_path = config.get_log_file_path()

        if log_path:
            console.print()
            console.print(Panel(
                f"[bold]Log File Location:[/bold]\n{log_path}",
                title="Log File",
                expand=False,
            ))

            # Show file size if exists
            if log_path.exists():
                size = log_path.stat().st_size
                size_str = self._format_file_size(size)
                console.print(f"[dim]File size: {size_str}[/dim]")
        else:
            console.print("[yellow]Log file path not configured.[/yellow]")

        console.input("\nPress Enter to continue...")

    def _clear_logs(self) -> None:
        """Clear the log file with confirmation."""
        console.print()
        confirm = console.input(
            "[bold yellow]Are you sure you want to clear the log file? (y/N):[/bold yellow] "
        ).strip().lower()

        if confirm != "y":
            console.print("[dim]Operation cancelled.[/dim]")
            console.input("\nPress Enter to continue...")
            return

        config = get_logging_config()
        success = config.clear_log_file()

        if success:
            console.print("[green]Log file cleared successfully.[/green]")
        else:
            console.print("[red]Failed to clear log file.[/red]")

        console.input("\nPress Enter to continue...")

    def _display_log_entries(
        self,
        entries: list[dict],
        title: str = "Log Entries",
    ) -> None:
        """
        Display log entries in a formatted table.

        Args:
            entries: List of log entry dictionaries
            title: Title for the display
        """
        table = Table(title=title, show_header=True, header_style="bold")
        table.add_column("Time", style="dim", width=20)
        table.add_column("Level", width=10)
        table.add_column("Message", overflow="fold")

        for entry in entries:
            timestamp = entry.get("timestamp", "")
            level = entry.get("level", "")
            message = entry.get("message", "")

            # Truncate timestamp to just time portion if too long
            if len(timestamp) > 20:
                timestamp = timestamp.split(" ")[-1] if " " in timestamp else timestamp[:20]

            # Color the level
            level_color = LEVEL_COLORS.get(level.upper(), "white")
            level_text = Text(level, style=level_color)

            # Truncate message if too long
            if len(message) > 100:
                message = message[:97] + "..."

            table.add_row(timestamp, level_text, message)

        console.print()
        console.print(table)
        console.print(f"\n[dim]Showing {len(entries)} entries[/dim]")

    def _format_file_size(self, size: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def cleanup(self) -> None:
        """Cleanup the feature."""
        pass


def view_logs() -> None:
    """
    Convenience function to view logs.

    Can be called directly from other parts of the application.
    """
    feature = LogViewerFeature()
    feature.execute()
