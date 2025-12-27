"""
User management feature for Farmer CLI.

This module provides user management functionality including
adding, listing, updating, deleting, searching, and exporting users.
"""

import json
import logging
from typing import List
from typing import Tuple

from ..core.constants import DEFAULT_PAGE_SIZE
from ..core.constants import USER_MANAGEMENT_OPTIONS
from ..core.database import get_session
from ..models.user import User
from ..ui.console import console
from ..ui.menu import MenuManager
from ..ui.prompts import confirm_prompt
from ..ui.prompts import int_prompt
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
                self._update_user()
            elif choice == "4":
                self._delete_user()
            elif choice == "5":
                self._search_users()
            elif choice == "6":
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

    def _list_users(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> None:
        """
        List all users with pagination.

        Args:
            page: Current page number (1-indexed)
            page_size: Number of users per page
        """
        console.clear()

        try:
            with get_session() as session:
                # Get total count
                total_count = session.query(User).count()

                if total_count == 0:
                    console.print("[bold yellow]No users found.[/bold yellow]")
                    console.input("\nPress Enter to continue...")
                    return

                # Calculate pagination
                total_pages = (total_count + page_size - 1) // page_size
                page = max(1, min(page, total_pages))
                offset = (page - 1) * page_size

                # Query users with pagination
                users = session.query(User).order_by(User.name).offset(offset).limit(page_size).all()

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

                table = create_table(
                    f"Users (Page {page}/{total_pages}, {total_count} total)",
                    columns,
                    rows,
                )

                console.print(table)

                # Show pagination controls
                console.print(f"\n[dim]Page {page} of {total_pages}[/dim]")
                if total_pages > 1:
                    nav_msg = "[dim]Enter page number, 'n' for next, 'p' for previous, "
                    nav_msg += "or press Enter to return[/dim]"
                    console.print(nav_msg)
                    nav = text_prompt("Navigation", default="")

                    if nav.lower() == "n" and page < total_pages:
                        self._list_users(page + 1, page_size)
                        return
                    elif nav.lower() == "p" and page > 1:
                        self._list_users(page - 1, page_size)
                        return
                    elif nav.isdigit():
                        new_page = int(nav)
                        if 1 <= new_page <= total_pages:
                            self._list_users(new_page, page_size)
                            return
                else:
                    console.input("\nPress Enter to continue...")

        except Exception as e:
            console.print(f"[bold red]Failed to list users: {e}[/bold red]")
            logger.error(f"Error listing users: {e}")
            console.input("\nPress Enter to continue...")

    def _update_user(self) -> None:
        """Update an existing user."""
        try:
            # Get user ID
            user_id = int_prompt("Enter user ID to update", min_value=1)

            with get_session() as session:
                user = session.query(User).filter_by(id=user_id).first()

                if not user:
                    console.print(f"[bold red]User with ID {user_id} not found![/bold red]")
                    console.input("Press Enter to continue...")
                    return

                console.print(f"\n[bold]Current user: {user.name}[/bold]")
                console.print(f"[dim]Current preferences: {user.preferences}[/dim]\n")

                # Get new name (optional)
                new_name = text_prompt(
                    "Enter new name (leave empty to keep current)",
                    default="",
                )

                # Get new preferences (optional)
                new_prefs = text_prompt(
                    "Enter new preferences JSON (leave empty to keep current)",
                    default="",
                    validator=lambda x: x == "" or self._validate_json(x),
                    error_message="Invalid JSON format",
                )

                # Check if any changes were made
                if not new_name and not new_prefs:
                    console.print("[bold yellow]No changes made.[/bold yellow]")
                    console.input("Press Enter to continue...")
                    return

                # Update user
                if new_name:
                    # Check for name uniqueness
                    existing = session.query(User).filter(User.name == new_name, User.id != user_id).first()
                    if existing:
                        console.print(f"[bold red]User '{new_name}' already exists![/bold red]")
                        console.input("Press Enter to continue...")
                        return
                    user.name = new_name

                if new_prefs:
                    user.preferences = new_prefs

                session.commit()

                console.print("[bold green]✓ User updated successfully![/bold green]")
                logger.info(f"Updated user ID {user_id}")

        except ValueError:
            console.print("[bold red]Invalid user ID![/bold red]")
        except Exception as e:
            console.print(f"[bold red]Failed to update user: {e}[/bold red]")
            logger.error(f"Error updating user: {e}")

        console.input("Press Enter to continue...")

    def _delete_user(self) -> None:
        """Delete a user with confirmation."""
        try:
            # Get user ID
            user_id = int_prompt("Enter user ID to delete", min_value=1)

            with get_session() as session:
                user = session.query(User).filter_by(id=user_id).first()

                if not user:
                    console.print(f"[bold red]User with ID {user_id} not found![/bold red]")
                    console.input("Press Enter to continue...")
                    return

                console.print(f"\n[bold]User to delete: {user.name}[/bold]")
                console.print(f"[dim]Preferences: {user.preferences}[/dim]")
                console.print(f"[dim]Created: {user.created_at}[/dim]\n")

                # Confirm deletion
                if confirm_prompt(f"Are you sure you want to delete user '{user.name}'?", default=False):
                    user_name = user.name
                    session.delete(user)
                    session.commit()

                    console.print(f"[bold green]✓ User '{user_name}' deleted successfully![/bold green]")
                    logger.info(f"Deleted user: {user_name} (ID: {user_id})")
                else:
                    console.print("[bold yellow]Deletion cancelled.[/bold yellow]")

        except ValueError:
            console.print("[bold red]Invalid user ID![/bold red]")
        except Exception as e:
            console.print(f"[bold red]Failed to delete user: {e}[/bold red]")
            logger.error(f"Error deleting user: {e}")

        console.input("Press Enter to continue...")

    def _search_users(self) -> None:
        """Search users by name."""
        console.clear()

        try:
            # Get search query
            query = text_prompt(
                "Enter search query (name)",
                validator=lambda x: bool(x.strip()),
                error_message="Search query cannot be empty",
            )

            with get_session() as session:
                # Search users by name (case-insensitive)
                users = session.query(User).filter(User.name.ilike(f"%{query}%")).order_by(User.name).all()

                if not users:
                    console.print(f"[bold yellow]No users found matching '{query}'.[/bold yellow]")
                    console.input("\nPress Enter to continue...")
                    return

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

                table = create_table(f"Search Results for '{query}' ({len(users)} found)", columns, rows)

                console.print(table)

        except Exception as e:
            console.print(f"[bold red]Failed to search users: {e}[/bold red]")
            logger.error(f"Error searching users: {e}")

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

    # Public API methods for programmatic access

    def add_user(self, name: str, preferences: dict | None = None) -> User:
        """
        Add a new user programmatically.

        Args:
            name: User name
            preferences: Optional preferences dictionary

        Returns:
            Created User object

        Raises:
            ValueError: If name is invalid or already exists
        """
        if not name or not name.strip():
            raise ValueError("User name cannot be empty")

        name = name.strip()
        if len(name) > 255:
            raise ValueError("User name cannot exceed 255 characters")

        prefs_json = json.dumps(preferences or {})

        with get_session() as session:
            if session.query(User).filter_by(name=name).first():
                raise ValueError(f"User '{name}' already exists")

            user = User(name=name, preferences=prefs_json)
            session.add(user)
            session.commit()
            session.refresh(user)

            logger.info(f"Added user: {name}")
            return user

    def update_user(
        self, user_id: int, name: str | None = None, preferences: dict | None = None
    ) -> User:
        """
        Update an existing user.

        Args:
            user_id: ID of the user to update
            name: New name (optional)
            preferences: New preferences dictionary (optional)

        Returns:
            Updated User object

        Raises:
            ValueError: If user not found or name already exists
        """
        with get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            if name is not None:
                name = name.strip()
                if not name:
                    raise ValueError("User name cannot be empty")
                if len(name) > 255:
                    raise ValueError("User name cannot exceed 255 characters")

                # Check for name uniqueness
                existing = session.query(User).filter(User.name == name, User.id != user_id).first()
                if existing:
                    raise ValueError(f"User '{name}' already exists")

                user.name = name

            if preferences is not None:
                user.preferences = json.dumps(preferences)

            session.commit()
            session.refresh(user)

            logger.info(f"Updated user ID {user_id}")
            return user

    def delete_user(self, user_id: int, confirm: bool = True) -> bool:
        """
        Delete a user.

        Args:
            user_id: ID of the user to delete
            confirm: Whether to require confirmation (for programmatic use, set to False)

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If user not found
        """
        with get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            user_name = user.name
            session.delete(user)
            session.commit()

            logger.info(f"Deleted user: {user_name} (ID: {user_id})")
            return True

    def list_users(
        self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE
    ) -> Tuple[List[User], int, int]:
        """
        List users with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of users per page

        Returns:
            Tuple of (users list, total count, total pages)
        """
        with get_session() as session:
            total_count = session.query(User).count()
            total_pages = max(1, (total_count + page_size - 1) // page_size)
            page = max(1, min(page, total_pages))
            offset = (page - 1) * page_size

            users = session.query(User).order_by(User.name).offset(offset).limit(page_size).all()

            return users, total_count, total_pages

    def search_users(self, query: str) -> List[User]:
        """
        Search users by name.

        Args:
            query: Search query string

        Returns:
            List of matching User objects
        """
        if not query or not query.strip():
            return []

        with get_session() as session:
            users = session.query(User).filter(User.name.ilike(f"%{query}%")).order_by(User.name).all()
            return users

    def get_user(self, user_id: int) -> User | None:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        with get_session() as session:
            return session.query(User).filter_by(id=user_id).first()

    def cleanup(self) -> None:
        """Cleanup the user management feature."""
        # No specific cleanup needed for user management
        pass
