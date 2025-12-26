"""
Configuration feature for Farmer CLI.

This module provides configuration management functionality including
theme selection, time display, and help search.
"""

from datetime import datetime
from time import sleep

from themes import THEMES

from ..core.constants import CONFIGURATION_OPTIONS
from ..ui.console import console
from ..ui.menu import MenuManager
from ..ui.prompts import choice_prompt
from .base import BaseFeature
from .help_system import searchable_help


class ConfigurationFeature(BaseFeature):
    """
    Configuration feature implementation.

    Provides various configuration and customization options.
    """

    def __init__(self, app=None):
        """
        Initialize the configuration feature.

        Args:
            app: Reference to main application (for theme changes)
        """
        super().__init__(name="Configuration", description="Customize themes, layouts, and display options")
        self.menu_manager = MenuManager()
        self.app = app

    def execute(self) -> None:
        """Execute the configuration feature."""
        while True:
            choice = self.menu_manager.display_submenu("Configuration Menu", CONFIGURATION_OPTIONS)

            if choice is None:
                break

            if choice == "1":
                self._select_theme()
            elif choice == "2":
                self._theme_showcase()
            elif choice == "3":
                self._display_current_time()
            elif choice == "4":
                searchable_help()

    def _select_theme(self) -> None:
        """Allow user to select a UI theme."""
        console.clear()
        console.print("[bold magenta]Select a Theme[/bold magenta]\n")

        # Display available themes with descriptions
        theme_list = list(THEMES.keys())
        for idx, theme_key in enumerate(theme_list, 1):
            theme_data = THEMES[theme_key]
            name = theme_data.get("name", theme_key.replace('_', ' ').title())
            description = theme_data.get("description", "")
            console.print(f"\n{idx}. [bold]{name}[/bold]")
            if description:
                console.print(f"   [dim]{description}[/dim]")

        # Get user choice
        choices = [str(i) for i in range(1, len(theme_list) + 1)]
        choice = choice_prompt("\nEnter theme number", choices=choices, default="1")

        # Apply theme
        selected_theme = theme_list[int(choice) - 1]

        if self.app:
            self.app.change_theme(selected_theme)

        console.print(f"\n[bold green]✓ Theme changed to {selected_theme.replace('_', ' ').title()}![/bold green]")
        sleep(2)

    def _display_current_time(self) -> None:
        """Display the current date and time."""
        console.clear()

        now = datetime.now()

        # Format different time representations
        formats = [
            ("Standard", now.strftime("%Y-%m-%d %H:%M:%S")),
            ("Long Date", now.strftime("%A, %B %d, %Y")),
            ("12-hour", now.strftime("%I:%M:%S %p")),
            ("ISO 8601", now.isoformat()),
            ("Unix Timestamp", str(int(now.timestamp()))),
        ]

        console.print("[bold cyan]Current Date and Time[/bold cyan]\n")

        for label, formatted in formats:
            console.print(f"[bold yellow]{label}:[/bold yellow] {formatted}")

        console.print(f"\n[dim]Timezone: {now.astimezone().tzname()}[/dim]")

        console.input("\nPress Enter to return to the menu...")

    def _theme_showcase(self) -> None:
        """Launch the theme showcase."""
        from .theme_showcase import ThemeShowcaseFeature

        showcase = ThemeShowcaseFeature()
        showcase.execute()

    def cleanup(self) -> None:
        """Cleanup the configuration feature."""
        # No specific cleanup needed for configuration
        pass
