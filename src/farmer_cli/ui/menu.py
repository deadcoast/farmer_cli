"""
Menu system for Farmer CLI.

This module provides the menu display and navigation functionality
for the application.
"""

from typing import List
from typing import Optional
from typing import Tuple

from rich.align import Align
from rich.prompt import Prompt

from themes import DOUBLE_LINE
from themes import THEMES

from ..core.constants import FRAME_WIDTH
from ..core.constants import MENU_OPTIONS
from .console import console
from .widgets import create_frame


class MenuManager:
    """
    Manages menu display and navigation.

    This class handles the rendering of menus and processing of user input
    for menu navigation throughout the application.
    """

    def __init__(self):
        """Initialize the menu manager."""
        self.menu_stack: List[str] = []

    def display_main_menu(self, theme: str = "default") -> Optional[str]:
        """
        Display the main menu and get user choice.

        Args:
            theme: Theme name to use for styling

        Returns:
            User's menu choice or None if invalid
        """
        # Clear console for fresh display
        console.clear()

        # Display greeting
        from ..core.constants import APP_NAME
        from ..core.constants import APP_VERSION
        from ..ui.widgets import display_greeting

        display_greeting(APP_NAME, APP_VERSION)
        # Create menu content
        title = "=== Main Menu ==="
        options = [f"[{i + 1}] {option}" for i, option in enumerate(MENU_OPTIONS[:-1])]
        options.append("[0] Exit")

        menu_content = title + "\n" + "\n".join(options)

        # Get theme styling
        theme_config = THEMES.get(theme, THEMES["default"])

        # Create framed menu with theme
        frame = create_frame(
            menu_content,
            width=FRAME_WIDTH,
            border_style=theme_config["border_style"],
            border_chars=theme_config.get("border_chars", DOUBLE_LINE),
            title="Main Menu",
            theme=theme,
        )

        # Print the centered frame
        console.print("\n")
        console.print(Align.center(frame))
        console.print("\n")

        # Get user input
        choice = Prompt.ask("Enter your choice or type 'help' for assistance", console=console)

        # Handle help
        if choice.lower() == "help":
            self._display_help()
            return None

        # Validate choice
        valid_choices = [str(i) for i in range(len(MENU_OPTIONS))]
        if choice in valid_choices:
            return choice
        console.print("[bold red]Invalid choice. Please try again.[/bold red]")
        console.input("Press Enter to continue...")
        return None

    def display_submenu(self, title: str, options: List[Tuple[str, str]], theme: str = "default") -> Optional[str]:
        """
        Display a submenu and get user choice.

        Args:
            title: Submenu title
            options: List of (key, description) tuples
            theme: Theme name to use for styling

        Returns:
            User's choice or None if returning to main menu
        """
        console.clear()
        console.print(f"[bold magenta]{title}[/bold magenta]")

        # Display options
        for key, description in options:
            if key == "0":
                console.print(f"\n{key}. {description}")
            else:
                console.print(f"{key}. {description}")

        # Get valid choices
        valid_choices = [opt[0] for opt in options]

        # Get user input
        choice = Prompt.ask("\nEnter your choice", choices=valid_choices, default="0", console=console)

        return choice if choice != "0" else None

    def _display_help(self) -> None:
        """Display help for menu navigation."""
        from ..features.help_system import display_quick_help

        display_quick_help()
        console.input("\nPress Enter to return to the menu...")

    def push_menu(self, menu_name: str) -> None:
        """
        Push a menu onto the navigation stack.

        Args:
            menu_name: Name of the menu to push
        """
        self.menu_stack.append(menu_name)

    def pop_menu(self) -> Optional[str]:
        """
        Pop a menu from the navigation stack.

        Returns:
            Previous menu name or None if stack is empty
        """
        return self.menu_stack.pop() if self.menu_stack else None

    def clear_stack(self) -> None:
        """Clear the menu navigation stack."""
        self.menu_stack.clear()
