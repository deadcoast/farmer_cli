"""
Preferences service for Farmer CLI.

This module handles loading, saving, and validating user preferences.
"""

import json
import logging
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import TypeVar

from exceptions import FileOperationError
from exceptions import ValidationError

from ..core.constants import PREFERENCES_FILE


logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Preference Schema Definition
# ---------------------------------------------------------------------------

class PreferenceSchema:
    """
    Schema definition for a preference value.

    Defines the expected type, validation rules, and default value
    for a preference key.
    """

    def __init__(
        self,
        expected_type: type | tuple[type, ...],
        default: Any,
        validator: Optional[Callable[[Any], bool]] = None,
        description: str = "",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allowed_values: Optional[list] = None,
    ):
        """
        Initialize preference schema.

        Args:
            expected_type: Expected Python type(s) for the value
            default: Default value for this preference
            validator: Optional custom validation function
            description: Human-readable description
            min_value: Minimum value for numeric types
            max_value: Maximum value for numeric types
            allowed_values: List of allowed values (enum-like)
        """
        self.expected_type = expected_type
        self.default = default
        self.validator = validator
        self.description = description
        self.min_value = min_value
        self.max_value = max_value
        self.allowed_values = allowed_values

    def validate(self, value: Any) -> tuple[bool, str]:
        """
        Validate a value against this schema.

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Type check - handle bool/int distinction specially
        # In Python, bool is a subclass of int, so we need explicit checks
        if self.expected_type == int:
            # For int type, reject booleans explicitly
            if isinstance(value, bool):
                return False, f"Expected type int, got bool"
            if not isinstance(value, int):
                return False, f"Expected type int, got {type(value).__name__}"
        elif self.expected_type == bool:
            # For bool type, only accept actual booleans
            if not isinstance(value, bool):
                return False, f"Expected type bool, got {type(value).__name__}"
        elif not isinstance(value, self.expected_type):
            expected = (
                self.expected_type.__name__
                if isinstance(self.expected_type, type)
                else " or ".join(t.__name__ for t in self.expected_type)
            )
            return False, f"Expected type {expected}, got {type(value).__name__}"

        # Range check for numeric types (only for actual int/float, not bool)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if self.min_value is not None and value < self.min_value:
                return False, f"Value {value} is below minimum {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"Value {value} is above maximum {self.max_value}"

        # Allowed values check
        if self.allowed_values is not None and value not in self.allowed_values:
            return False, f"Value '{value}' not in allowed values: {self.allowed_values}"

        # Custom validator
        if self.validator is not None:
            try:
                if not self.validator(value):
                    return False, "Custom validation failed"
            except Exception as e:
                return False, f"Validation error: {e}"

        return True, ""


# ---------------------------------------------------------------------------
# Preference Schemas Registry
# ---------------------------------------------------------------------------

def _validate_path(path: str) -> bool:
    """Validate that a path string is reasonable."""
    if not isinstance(path, str):
        return False
    # Allow empty string (will be replaced with actual path at runtime)
    if path == "":
        return True
    # Basic validation - path should not be empty after strip
    return len(path.strip()) > 0


def _validate_filename_template(template: str) -> bool:
    """Validate filename template format."""
    if not template or not isinstance(template, str):
        return False
    # Must contain at least %(ext)s or .ext pattern
    return len(template.strip()) > 0


PREFERENCE_SCHEMAS: Dict[str, PreferenceSchema] = {
    "theme": PreferenceSchema(
        expected_type=str,
        default="default",
        description="UI theme name",
    ),
    "first_run": PreferenceSchema(
        expected_type=bool,
        default=True,
        description="Whether this is the first run",
    ),
    "check_updates": PreferenceSchema(
        expected_type=bool,
        default=True,
        description="Whether to check for updates",
    ),
    "show_tips": PreferenceSchema(
        expected_type=bool,
        default=True,
        description="Whether to show tips",
    ),
    "export_format": PreferenceSchema(
        expected_type=str,
        default="csv",
        allowed_values=["csv", "json", "pdf"],
        description="Default export format",
    ),
    "last_directory": PreferenceSchema(
        expected_type=str,
        default="",
        validator=_validate_path,
        description="Last used directory",
    ),
    "download_directory": PreferenceSchema(
        expected_type=str,
        default="",
        validator=_validate_path,
        description="Default download directory",
    ),
    "filename_template": PreferenceSchema(
        expected_type=str,
        default="%(title)s.%(ext)s",
        validator=_validate_filename_template,
        description="Filename template for downloads",
    ),
    "conflict_resolution": PreferenceSchema(
        expected_type=str,
        default="rename",
        allowed_values=["rename", "overwrite", "skip"],
        description="How to handle filename conflicts",
    ),
    "subdirectory_organization": PreferenceSchema(
        expected_type=str,
        default="none",
        allowed_values=["none", "channel", "playlist", "date"],
        description="How to organize downloads into subdirectories",
    ),
    "max_concurrent_downloads": PreferenceSchema(
        expected_type=int,
        default=3,
        min_value=1,
        max_value=5,
        description="Maximum concurrent downloads",
    ),
    "default_format": PreferenceSchema(
        expected_type=(str, type(None)),
        default=None,
        description="Default video format preference",
    ),
    "prefer_audio_only": PreferenceSchema(
        expected_type=bool,
        default=False,
        description="Whether to prefer audio-only downloads",
    ),
}


# ---------------------------------------------------------------------------
# Preferences Service
# ---------------------------------------------------------------------------

class PreferencesService:
    """
    Service for managing user preferences.

    Handles loading, saving, validating, and accessing user preferences
    stored in JSON format. Includes type checking, range validation,
    and corruption recovery.
    """

    def __init__(self, preferences_file: Optional[Path] = None):
        """
        Initialize the preferences service.

        Args:
            preferences_file: Path to preferences file (defaults to PREFERENCES_FILE)
        """
        self.preferences_file = preferences_file or PREFERENCES_FILE
        self._cache: Optional[Dict[str, Any]] = None
        self._corruption_detected = False

    def load(self) -> Dict[str, Any]:
        """
        Load preferences from file.

        Returns:
            Dictionary of preferences

        Note:
            If the file is corrupted, returns defaults and sets
            corruption_detected flag.
        """
        if self._cache is not None:
            return self._cache.copy()

        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():
                        # Empty file - treat as corruption
                        raise json.JSONDecodeError("Empty file", content, 0)
                    loaded = json.loads(content)

                    # Validate loaded data is a dict
                    if not isinstance(loaded, dict):
                        raise json.JSONDecodeError(
                            "Root element must be object", str(loaded), 0
                        )

                    self._cache = loaded
                    return self._cache.copy()

            except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to load preferences (corrupted): {e}")
                self._corruption_detected = True
                # Fall through to return defaults

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

    def set(self, key: str, value: Any, validate: bool = True) -> None:
        """
        Set a preference value.

        Args:
            key: Preference key
            value: Value to set
            validate: Whether to validate the value (default True)

        Raises:
            ValidationError: If validation is enabled and value is invalid
        """
        if validate:
            is_valid, error_msg = self.validate_preference(key, value)
            if not is_valid:
                raise ValidationError(f"Invalid preference value for '{key}': {error_msg}")

        preferences = self.load()
        preferences[key] = value
        self.save(preferences)

    def update(self, updates: Dict[str, Any], validate: bool = True) -> None:
        """
        Update multiple preferences.

        Args:
            updates: Dictionary of updates
            validate: Whether to validate values (default True)

        Raises:
            ValidationError: If validation is enabled and any value is invalid
        """
        if validate:
            errors = []
            for key, value in updates.items():
                is_valid, error_msg = self.validate_preference(key, value)
                if not is_valid:
                    errors.append(f"{key}: {error_msg}")
            if errors:
                raise ValidationError(
                    f"Invalid preference values: {'; '.join(errors)}"
                )

        preferences = self.load()
        preferences.update(updates)
        self.save(preferences)

    def reset(self) -> None:
        """Reset preferences to defaults."""
        self._cache = None
        self._corruption_detected = False
        defaults = self._get_defaults()
        self.save(defaults)

    def validate_preference(self, key: str, value: Any) -> tuple[bool, str]:
        """
        Validate a single preference value.

        Args:
            key: Preference key
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        schema = PREFERENCE_SCHEMAS.get(key)
        if schema is None:
            # Unknown keys are allowed but logged
            logger.debug(f"Unknown preference key: {key}")
            return True, ""

        return schema.validate(value)

    def validate_all(self, preferences: Dict[str, Any]) -> tuple[bool, Dict[str, str]]:
        """
        Validate all preferences in a dictionary.

        Args:
            preferences: Dictionary of preferences to validate

        Returns:
            Tuple of (all_valid, errors_dict)
            errors_dict maps invalid keys to error messages
        """
        errors: Dict[str, str] = {}
        for key, value in preferences.items():
            is_valid, error_msg = self.validate_preference(key, value)
            if not is_valid:
                errors[key] = error_msg

        return len(errors) == 0, errors

    def is_corruption_detected(self) -> bool:
        """
        Check if corruption was detected during load.

        Returns:
            True if corruption was detected
        """
        return self._corruption_detected

    def recover_from_corruption(self) -> Dict[str, Any]:
        """
        Recover from a corrupted preferences file.

        Resets to defaults, saves them, and clears the corruption flag.

        Returns:
            The default preferences that were restored
        """
        logger.warning("Recovering from corrupted preferences file")
        self._cache = None
        self._corruption_detected = False
        defaults = self._get_defaults()
        self.save(defaults)
        logger.info("Preferences reset to defaults after corruption recovery")
        return defaults

    def get_schema(self, key: str) -> Optional[PreferenceSchema]:
        """
        Get the schema for a preference key.

        Args:
            key: Preference key

        Returns:
            PreferenceSchema or None if key is unknown
        """
        return PREFERENCE_SCHEMAS.get(key)

    def get_all_schemas(self) -> Dict[str, PreferenceSchema]:
        """
        Get all preference schemas.

        Returns:
            Dictionary mapping keys to schemas
        """
        return PREFERENCE_SCHEMAS.copy()

    def _get_defaults(self) -> Dict[str, Any]:
        """
        Get default preferences.

        Returns:
            Dictionary of default preferences
        """
        from ..core.constants import DEFAULT_THEME

        defaults = {}
        for key, schema in PREFERENCE_SCHEMAS.items():
            defaults[key] = schema.default

        # Override with constants where applicable
        defaults["theme"] = DEFAULT_THEME
        defaults["last_directory"] = str(Path.home())
        defaults["download_directory"] = str(Path.home() / "Downloads")

        return defaults
