"""
System tools feature for Farmer CLI.

This module provides system-related tools including file browsing,
weather checking, export functionality, and feedback submission.
"""

from ..core.constants import SYSTEM_TOOLS_OPTIONS
from ..services.feedback import submit_feedback
from ..ui.console import console
from ..ui.menu import MenuManager
from .base import BaseFeature
from .export import export_help_to_pdf
from .file_browser import browse_files
from .weather import check_weather


class SystemToolsFeature(BaseFeature):
    """
    System tools feature implementation.

    Provides various system utilities and tools.
    """

    def __init__(self):
        """Initialize the system tools feature."""
        super().__init__(name="System Tools", description="File browser, weather checking, and monitoring")
        self.menu_manager = MenuManager()

    def execute(self) -> None:
        """Execute the system tools feature."""
        while True:
            choice = self.menu_manager.display_submenu("System Tools", SYSTEM_TOOLS_OPTIONS)

            if choice is None:
                break

            if choice == "1":
                browse_files()
            elif choice == "2":
                check_weather()
            elif choice == "3":
                self._export_help()
            elif choice == "4":
                submit_feedback()

    def _export_help(self) -> None:
        """Export help to PDF with error handling."""
        try:
            export_help_to_pdf()
            console.input("\nPress Enter to continue...")
        except Exception as e:
            console.print(f"[bold red]Export failed: {e}[/bold red]")
            console.input("\nPress Enter to continue...")
