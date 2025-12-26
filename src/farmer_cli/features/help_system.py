"""
Help system for Farmer CLI.

This module provides help documentation and search functionality.
"""

from typing import Dict

from ..core.constants import APP_NAME
from ..core.constants import APP_VERSION
from ..ui.console import console
from ..ui.prompts import text_prompt
from .base import BaseFeature


# Help content database
HELP_CONTENT: Dict[str, str] = {
    "overview": f"{APP_NAME} is a powerful CLI application with Rich UI for various tasks.",
    "navigation": "Use number keys to select menu options. Press 0 to go back.",
    "login": "User management allows you to create and manage user accounts.",
    "theme": "Change themes from Configuration menu. Available: default, dark, light, high_contrast.",
    "exit": "Select Exit or press Ctrl+C. You'll be asked to confirm.",
    "search": "Press Ctrl+S for fuzzy search through menu options.",
    "help": "Press Ctrl+H or type 'help' at any menu for assistance.",
    "weather": "Check weather by entering any city name. Requires API key in .env file.",
    "files": "Browse files and directories with detailed information.",
    "export": "Export data to CSV or help documentation to PDF.",
    "feedback": "Submit feedback through System Tools menu.",
    "shortcuts": "Ctrl+C: Exit, Ctrl+S: Search, Ctrl+H: Help",
    "preferences": "Your preferences are saved automatically.",
    "database": "All data is stored in a local SQLite database.",
    "configuration": "Configure the app through the Configuration menu.",
}


class HelpSystem(BaseFeature):
    """
    Help system implementation.

    Provides comprehensive help and documentation features.
    """

    def __init__(self):
        """Initialize the help system."""
        super().__init__(name="Help System", description="Comprehensive help and documentation")

    def execute(self) -> None:
        """Execute the help system."""
        display_full_help()


def display_full_help() -> None:
    """Display comprehensive help information."""
    console.clear()

    help_text = f"""
[bold magenta]Help - {APP_NAME} v{APP_VERSION}[/bold magenta]

[bold cyan]Overview[/bold cyan]
{HELP_CONTENT["overview"]}

[bold cyan]Navigation[/bold cyan]
{HELP_CONTENT["navigation"]}

[bold cyan]Main Features[/bold cyan]

[bold]1. Data Processing[/bold]
- Display code snippets with syntax highlighting
- View system information
- Create data tables
- Simulate progress bars

[bold]2. User Management[/bold]
- Add new users with preferences
- List all users
- Export user data to CSV
- Store preferences in JSON format

[bold]3. Configuration[/bold]
- {HELP_CONTENT["theme"]}
- Display current date/time
- Search help documentation

[bold]4. System Tools[/bold]
- {HELP_CONTENT["files"]}
- {HELP_CONTENT["weather"]}
- {HELP_CONTENT["export"]}
- {HELP_CONTENT["feedback"]}

[bold cyan]Keyboard Shortcuts[/bold cyan]
{HELP_CONTENT["shortcuts"]}

[bold cyan]Tips[/bold cyan]
- {HELP_CONTENT["preferences"]}
- {HELP_CONTENT["database"]}
- {HELP_CONTENT["configuration"]}

[bold cyan]Support[/bold cyan]
For assistance, contact: support@farmercli.com
"""

    console.print(help_text.strip())
    console.input("\nPress Enter to return...")


def display_quick_help() -> None:
    """Display quick help for menu navigation."""
    console.clear()
    console.print("[bold magenta]Quick Help - Menu Navigation[/bold magenta]\n")

    quick_help = """
• Use [bold]number keys[/bold] to select menu options
• Press [bold]0[/bold] to return to previous menu
• Type [bold]help[/bold] for detailed assistance
• Press [bold]Ctrl+C[/bold] to exit (with confirmation)
• Press [bold]Ctrl+S[/bold] to search menu options
• Press [bold]Ctrl+H[/bold] to display this help

[dim]All changes are saved automatically.[/dim]
"""

    console.print(quick_help.strip())


def searchable_help() -> None:
    """Search through help documentation."""
    console.clear()
    console.print("[bold magenta]Search Help Documentation[/bold magenta]\n")

    query = text_prompt("Enter keyword to search in help").lower()

    if results := {
        topic: content for topic, content in HELP_CONTENT.items() if query in topic.lower() or query in content.lower()
    }:
        console.print(f"\n[bold green]Found {len(results)} help topics:[/bold green]\n")

        for topic, content in results.items():
            console.print(f"[bold cyan]{topic.replace('_', ' ').title()}[/bold cyan]")
            console.print(f"{content}\n")

    else:
        console.print(f"\n[bold yellow]No help topics found for '{query}'[/bold yellow]")
    console.input("Press Enter to return...")
