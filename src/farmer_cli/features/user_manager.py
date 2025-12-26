"""
User management feature for Farmer CLI.

This module provides user management functionality including
adding, listing, and exporting users.
"""

import json
import logging

from ..core.constants import USER_MANAGEMENT_OPTIONS
from ..core.database import get_session
from ..models.user import User
from ..ui.console import console
from ..ui.menu import MenuManager
from ..ui.prompts import confirm_prompt
from ..ui.prompts import text_prompt
from ..ui.widgets import create_table
from .base import BaseFeature
from .export import export_users_to_csv


logger = logging.getLogger(__name__)


class UserManagementFeature(BaseFeature):
    """
    User management feature implementation.

    Provides CRUD operations for users and related functionality.
    """

    def __init__(self):
        """Initialize the user management feature."""
        super().__init__(name="User Management", description="Manage users, preferences, and system configuration")
        self.menu_manager = MenuManager()

    def execute(self) -> None:
        """Execute the user management feature."""
        while True:
            choice = self.menu_manager.display_submenu("User Management", USER_MANAGEMENT_OPTIONS)

            if choice is None:
                break

            if choice == "1":
                self._add_user()
            elif choice == "2":
                self._list_users()
            elif choice == "3":
                self._export_users()

    def _add_user(self) -> None:
        """Add a new user."""
        try:
            # Get user input
            name = text_prompt(
                "Enter user name", validator=lambda x: bool(x.strip()), error_message="Name cannot be empty"
            )

            # Get preferences
            prefs_input = text_prompt(
                "Enter user preferences (JSON format)",
                default="{}",
                validator=self._validate_json,
                error_message="Invalid JSON format",
            )

            # Create user
            with get_session() as session:
                if session.query(User).filter_by(name=name).first():
                    console.print(f"[bold red]User '{name}' already exists![/bold red]")
                    console.input("Press Enter to continue...")
                    return

                # Create new user
                user = User(name=name, preferences=prefs_input)
                session.add(user)
                session.commit()

                console.print(f"[bold green]✓ User '{name}' added successfully![/bold green]")
                logger.info(f"Added user: {name}")

        except Exception as e:
            console.print(f"[bold red]Failed to add user: {e}[/bold red]")
            logger.error(f"Error adding user: {e}")

        console.input("Press Enter to continue...")

    def _list_users(self) -> None:
        """List all users."""
        console.clear()

        try:
            with get_session() as session:
                if users := session.query(User).order_by(User.name).all():
                    # Prepare data for table
                    columns = [
                        ("ID", {"style": "dim", "width": 6}),
                        ("Name", {"style": "bold cyan", "min_width": 20}),
                        ("Preferences", {"style": "dim", "max_width": 40}),
                        ("Created", {"style": "dim"}),
                    ]

                    rows = []
                    for user in users:
                        # Format preferences for display
                        prefs = user.preferences_dict
                        prefs_str = json.dumps(prefs, indent=None)
                        if len(prefs_str) > 40:
                            prefs_str = f"{prefs_str[:37]}..."

                        # Format date
                        created = user.created_at.strftime("%Y-%m-%d %H:%M")

                        rows.append([str(user.id), user.name, prefs_str, created])

                    table = create_table(f"Users ({len(users)} total)", columns, rows)  # type: ignore

                    console.print(table)

                else:
                    console.print("[bold yellow]No users found.[/bold yellow]")
        except Exception as e:
            console.print(f"[bold red]Failed to list users: {e}[/bold red]")
            logger.error(f"Error listing users: {e}")

        console.input("\nPress Enter to continue...")

    def _export_users(self) -> None:
        """Export users to CSV."""
        try:
            if confirm_prompt("Export all users to CSV?"):
                export_users_to_csv()
                console.input("Press Enter to continue...")
        except Exception as e:
            console.print(f"[bold red]Export failed: {e}[/bold red]")
            logger.error(f"Error exporting users: {e}")
            console.input("Press Enter to continue...")

    def _validate_json(self, value: str) -> bool:
        """
        Validate JSON string.

        Args:
            value: String to validate

        Returns:
            True if valid JSON
        """
        try:
            json.loads(value)
            return True
        except json.JSONDecodeError:
            return False

    def cleanup(self) -> None:
        """Cleanup the user management feature."""
        # No specific cleanup needed for user management
        pass
