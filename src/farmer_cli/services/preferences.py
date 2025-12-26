"""
Preferences service for Farmer CLI.

This module handles loading and saving user preferences.
"""

import json
import logging
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional

from exceptions import FileOperationError

from ..core.constants import PREFERENCES_FILE


logger = logging.getLogger(__name__)


class PreferencesService:
    """
    Service for managing user preferences.

    Handles loading, saving, and accessing user preferences
    stored in JSON format.
    """

    def __init__(self, preferences_file: Optional[Path] = None):
        """
        Initialize the preferences service.

        Args:
            preferences_file: Path to preferences file (defaults to PREFERENCES_FILE)
        """
        self.preferences_file = preferences_file or PREFERENCES_FILE
        self._cache: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """
        Load preferences from file.

        Returns:
            Dictionary of preferences
        """
        if self._cache is not None:
            return self._cache.copy()

        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                    return self._cache.copy()
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load preferences: {e}")

        # Return default preferences
        self._cache = self._get_defaults()
        return self._cache.copy()

    def save(self, preferences: Dict[str, Any]) -> None:
        """
        Save preferences to file.

        Args:
            preferences: Dictionary of preferences to save

        Raises:
            FileOperationError: If save fails
        """
        try:
            # Update cache
            self._cache = preferences.copy()

            # Ensure directory exists
            self.preferences_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(self.preferences_file, "w", encoding="utf-8") as f:
                json.dump(preferences, f, indent=4, sort_keys=True)

            logger.info("Preferences saved successfully")

        except IOError as e:
            error_msg = f"Failed to save preferences: {e}"
            logger.error(error_msg)
            raise FileOperationError(error_msg) from e

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a preference value.

        Args:
            key: Preference key
            default: Default value if key not found

        Returns:
            Preference value or default
        """
        preferences = self.load()
        return preferences.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a preference value.

        Args:
            key: Preference key
            value: Value to set
        """
        preferences = self.load()
        preferences[key] = value
        self.save(preferences)

    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple preferences.

        Args:
            updates: Dictionary of updates
        """
        preferences = self.load()
        preferences.update(updates)
        self.save(preferences)

    def reset(self) -> None:
        """Reset preferences to defaults."""
        self._cache = None
        defaults = self._get_defaults()
        self.save(defaults)

    def _get_defaults(self) -> Dict[str, Any]:
        """
        Get default preferences.

        Returns:
            Dictionary of default preferences
        """
        from ..core.constants import DEFAULT_THEME

        return {
            "theme": DEFAULT_THEME,
            "first_run": True,
            "check_updates": True,
            "show_tips": True,
            "export_format": "csv",
            "last_directory": str(Path.home()),
        }
