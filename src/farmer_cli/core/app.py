"""
Main application class for Farmer CLI.

This module contains the core application logic, including the main loop,
menu navigation, and coordination of all features.
"""

import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from config.settings import settings
from exceptions import DatabaseError
from exceptions import FarmerCLIError
from themes import THEMES

from ..features import ConfigurationFeature
from ..features import DataProcessingFeature
from ..features import SystemToolsFeature
from ..features import UserManagementFeature
from ..features import VideoDownloaderFeature
from ..services.preferences import PreferencesService
from ..ui.console import console
from ..ui.menu import MenuManager
from .constants import APP_NAME
from .constants import APP_VERSION
from .constants import MENU_ACTIONS
from .database import get_database_manager


logger = logging.getLogger(__name__)


class FarmerCLI:
    """
    Main application class that coordinates all features and manages the application lifecycle.
    """

    def __init__(self):
        """Initialize the Farmer CLI application."""
        self.running = False
        self.current_theme = settings.default_theme
        self.preferences_service = PreferencesService()
        self.menu_manager = MenuManager()

        # Initialize features
        self.features: Dict[str, Any] = {
            "video_downloader": VideoDownloaderFeature(
                preferences_service=self.preferences_service
            ),
            "data_processing": DataProcessingFeature(),
            "user_management": UserManagementFeature(),
            "configuration": ConfigurationFeature(self),
            "system_tools": SystemToolsFeature(),
        }

        # Database manager
        self.db_manager = get_database_manager()

    def initialize(self) -> None:
        """
        Initialize the application.

        This includes database setup, integrity validation, loading preferences,
        and any other initialization tasks.

        Raises:
            DatabaseError: If database initialization fails
        """
        try:
            # Initialize database
            self.db_manager.initialize()
            console.print("[bold green]Database initialized successfully.[/bold green]")

            # Validate database integrity on startup
            is_valid, issues = self.db_manager.validate_integrity()
            if not is_valid:
                console.print(
                    "[bold yellow]Database integrity issues detected:[/bold yellow]"
                )
                for issue in issues:
                    console.print(f"  [yellow]• {issue}[/yellow]")

                # Attempt automatic repair
                console.print("[bold cyan]Attempting automatic repair...[/bold cyan]")
                if self.db_manager.repair_database():
                    console.print(
                        "[bold green]Database repair successful.[/bold green]"
                    )
                else:
                    console.print(
                        "[bold yellow]Some issues could not be repaired. "
                        "Consider restoring from backup.[/bold yellow]"
                    )
            else:
                logger.info("Database integrity validation passed")

            # Load preferences
            preferences = self.preferences_service.load()
            self.current_theme = preferences.get("theme", settings.default_theme)

            # Apply theme
            self._apply_theme(self.current_theme)

            logger.info(f"{APP_NAME} v{APP_VERSION} initialized successfully")

        except DatabaseError:
            raise
        except Exception as e:
            error_msg = f"Application initialization failed: {e}"
            logger.error(error_msg)
            raise FarmerCLIError(error_msg) from e

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the main application loop.

        Args:
            args: Command line arguments

        Returns:
            Exit code (0 for success)
        """
        try:
            # Initialize application
            self.initialize()

            self.running = True

            # Main application loop
            while self.running:
                # Display main menu and get choice (includes clearing and greeting)
                choice = self.menu_manager.display_main_menu(self.current_theme)

                if choice is None:
                    continue

                # Handle menu selection
                self._handle_menu_choice(choice)

            # Clean exit
            console.print("\n[bold green]Thank you for using Farmer CLI![/bold green]")
            console.print("Exiting the application. Goodbye!", style="bold red")
            return 0

        except KeyboardInterrupt:
            raise  # Let __main__ handle this
        except DatabaseError as e:
            console.print(f"\n[bold red]Database error: {e}[/bold red]")
            logger.error(f"Database error: {e}")
            return 1
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return 1

    def _display_greeting(self) -> None:
        """Display the welcome greeting."""
        from ..ui.welcome import display_welcome_screen

        display_welcome_screen(theme=self.current_theme, app_name=APP_NAME, version=APP_VERSION)
        console.input()  # Wait for user to press Enter

    def _handle_menu_choice(self, choice: str) -> None:
        """
        Handle menu selection.

        Args:
            choice: Menu choice string
        """
        action = MENU_ACTIONS.get(choice)

        if action == "exit":
            if self._confirm_exit():
                self.running = False
        elif action in self.features:
            try:
                self.features[action].execute()
            except Exception as e:
                console.print(f"[bold red]Error in {action}: {e}[/bold red]")
                logger.error(f"Error executing {action}: {e}", exc_info=True)
                console.input("\nPress Enter to continue...")

    def _confirm_exit(self) -> bool:
        """
        Confirm if user wants to exit.

        Returns:
            True if user confirms exit
        """
        from ..ui.prompts import confirm_prompt

        return confirm_prompt("Are you sure you want to exit?")

    def _apply_theme(self, theme_name: str) -> None:
        """
        Apply a theme to the application.

        Args:
            theme_name: Name of the theme to apply
        """
        if theme_name in THEMES:
            self.current_theme = theme_name
            # Theme is applied when rendering UI components
        else:
            logger.warning(f"Unknown theme: {theme_name}, using default")
            self.current_theme = "default"

    def change_theme(self, theme_name: str) -> None:
        """
        Change the application theme.

        Args:
            theme_name: Name of the new theme
        """
        self._apply_theme(theme_name)

        # Save preference
        preferences = self.preferences_service.load()
        preferences["theme"] = theme_name
        self.preferences_service.save(preferences)

        logger.info(f"Theme changed to: {theme_name}")
