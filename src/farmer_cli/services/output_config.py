"""
Output configuration service for Farmer CLI.

This module provides functionality for managing download output settings,
including default download directory, filename templates, conflict resolution,
and subdirectory organization preferences.

Feature: farmer-cli-completion
Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ..utils.filename_template import FilenameTemplate


logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """Options for handling filename conflicts."""

    RENAME = "rename"  # Add suffix like (1), (2), etc.
    OVERWRITE = "overwrite"  # Replace existing file
    SKIP = "skip"  # Skip download if file exists


class SubdirectoryOrganization(Enum):
    """Options for organizing downloads into subdirectories."""

    NONE = "none"  # All files in download directory
    BY_CHANNEL = "by_channel"  # Organize by uploader/channel
    BY_PLAYLIST = "by_playlist"  # Organize by playlist name
    BY_DATE = "by_date"  # Organize by download date (YYYY-MM)


@dataclass
class DirectoryValidationResult:
    """Result of directory validation."""

    is_valid: bool
    exists: bool
    is_writable: bool
    error: str | None = None


@dataclass
class OutputSettings:
    """
    Data class for download output settings.

    Attributes:
        download_directory: Default directory for downloads
        filename_template: Template for generating filenames
        conflict_resolution: How to handle filename conflicts
        subdirectory_organization: How to organize files into subdirectories
    """

    download_directory: str
    filename_template: str
    conflict_resolution: ConflictResolution
    subdirectory_organization: SubdirectoryOrganization

    @classmethod
    def get_defaults(cls) -> "OutputSettings":
        """Get default output settings."""
        return cls(
            download_directory=str(Path.home() / "Downloads"),
            filename_template="%(title)s.%(ext)s",
            conflict_resolution=ConflictResolution.RENAME,
            subdirectory_organization=SubdirectoryOrganization.NONE,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary for persistence."""
        return {
            "download_directory": self.download_directory,
            "filename_template": self.filename_template,
            "conflict_resolution": self.conflict_resolution.value,
            "subdirectory_organization": self.subdirectory_organization.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutputSettings":
        """Create settings from dictionary."""
        defaults = cls.get_defaults()

        return cls(
            download_directory=data.get("download_directory", defaults.download_directory),
            filename_template=data.get("filename_template", defaults.filename_template),
            conflict_resolution=ConflictResolution(
                data.get("conflict_resolution", defaults.conflict_resolution.value)
            ),
            subdirectory_organization=SubdirectoryOrganization(
                data.get("subdirectory_organization", defaults.subdirectory_organization.value)
            ),
        )


class OutputConfigService:
    """
    Service for managing download output configuration.

    Handles validation and management of download output settings including
    directory validation, filename template management, and conflict resolution.
    """

    # Preference keys for storage
    PREF_KEY_DOWNLOAD_DIR = "download_directory"
    PREF_KEY_FILENAME_TEMPLATE = "filename_template"
    PREF_KEY_CONFLICT_RESOLUTION = "conflict_resolution"
    PREF_KEY_SUBDIRECTORY_ORG = "subdirectory_organization"

    def __init__(self, preferences_service: Any | None = None) -> None:
        """
        Initialize the output configuration service.

        Args:
            preferences_service: Optional PreferencesService instance for persistence
        """
        self._preferences_service = preferences_service
        self._filename_template = FilenameTemplate()

    def get_settings(self) -> OutputSettings:
        """
        Get current output settings.

        Returns:
            OutputSettings with current configuration
        """
        if self._preferences_service is None:
            return OutputSettings.get_defaults()

        prefs = self._preferences_service.load()
        return OutputSettings(
            download_directory=prefs.get(
                self.PREF_KEY_DOWNLOAD_DIR,
                str(Path.home() / "Downloads"),
            ),
            filename_template=prefs.get(
                self.PREF_KEY_FILENAME_TEMPLATE,
                "%(title)s.%(ext)s",
            ),
            conflict_resolution=ConflictResolution(
                prefs.get(self.PREF_KEY_CONFLICT_RESOLUTION, ConflictResolution.RENAME.value)
            ),
            subdirectory_organization=SubdirectoryOrganization(
                prefs.get(self.PREF_KEY_SUBDIRECTORY_ORG, SubdirectoryOrganization.NONE.value)
            ),
        )

    def save_settings(self, settings: OutputSettings) -> None:
        """
        Save output settings to preferences.

        Args:
            settings: OutputSettings to save
        """
        if self._preferences_service is None:
            logger.warning("No preferences service configured, settings not saved")
            return

        self._preferences_service.update({
            self.PREF_KEY_DOWNLOAD_DIR: settings.download_directory,
            self.PREF_KEY_FILENAME_TEMPLATE: settings.filename_template,
            self.PREF_KEY_CONFLICT_RESOLUTION: settings.conflict_resolution.value,
            self.PREF_KEY_SUBDIRECTORY_ORG: settings.subdirectory_organization.value,
        })
        logger.info("Output settings saved")

    def set_download_directory(self, directory: str | Path) -> DirectoryValidationResult:
        """
        Set the default download directory.

        Validates the directory and saves if valid.

        Args:
            directory: Path to the download directory

        Returns:
            DirectoryValidationResult indicating success or failure
        """
        validation = self.validate_directory(directory)

        if validation.is_valid:
            settings = self.get_settings()
            settings.download_directory = str(Path(directory).resolve())
            self.save_settings(settings)
            logger.info(f"Download directory set to: {settings.download_directory}")

        return validation

    def set_filename_template(self, template: str) -> tuple[bool, str | None]:
        """
        Set the filename template.

        Validates the template and saves if valid.

        Args:
            template: Filename template string

        Returns:
            Tuple of (success, error_message)
        """
        validation = self._filename_template.validate(template)

        if validation.is_valid:
            settings = self.get_settings()
            settings.filename_template = template
            self.save_settings(settings)
            logger.info(f"Filename template set to: {template}")
            return True, None

        return False, validation.error

    def set_conflict_resolution(self, resolution: ConflictResolution | str) -> None:
        """
        Set the conflict resolution preference.

        Args:
            resolution: ConflictResolution enum or string value
        """
        if isinstance(resolution, str):
            resolution = ConflictResolution(resolution)

        settings = self.get_settings()
        settings.conflict_resolution = resolution
        self.save_settings(settings)
        logger.info(f"Conflict resolution set to: {resolution.value}")

    def set_subdirectory_organization(self, organization: SubdirectoryOrganization | str) -> None:
        """
        Set the subdirectory organization preference.

        Args:
            organization: SubdirectoryOrganization enum or string value
        """
        if isinstance(organization, str):
            organization = SubdirectoryOrganization(organization)

        settings = self.get_settings()
        settings.subdirectory_organization = organization
        self.save_settings(settings)
        logger.info(f"Subdirectory organization set to: {organization.value}")

    @staticmethod
    def validate_directory(directory: str | Path) -> DirectoryValidationResult:
        """
        Validate that a directory path exists and is writable.

        Args:
            directory: Path to validate

        Returns:
            DirectoryValidationResult with validation details
        """
        try:
            path = Path(directory).resolve()

            # Check if path exists
            exists = path.exists()

            if not exists:
                return DirectoryValidationResult(
                    is_valid=False,
                    exists=False,
                    is_writable=False,
                    error=f"Directory does not exist: {path}",
                )

            # Check if it's a directory (not a file)
            if not path.is_dir():
                return DirectoryValidationResult(
                    is_valid=False,
                    exists=True,
                    is_writable=False,
                    error=f"Path is not a directory: {path}",
                )

            # Check if writable
            is_writable = os.access(path, os.W_OK)

            if not is_writable:
                return DirectoryValidationResult(
                    is_valid=False,
                    exists=True,
                    is_writable=False,
                    error=f"Directory is not writable: {path}",
                )

            return DirectoryValidationResult(
                is_valid=True,
                exists=True,
                is_writable=True,
                error=None,
            )

        except Exception as e:
            return DirectoryValidationResult(
                is_valid=False,
                exists=False,
                is_writable=False,
                error=f"Invalid path: {e}",
            )

    @staticmethod
    def ensure_directory(directory: str | Path) -> DirectoryValidationResult:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory: Path to ensure exists

        Returns:
            DirectoryValidationResult with validation details
        """
        try:
            path = Path(directory).resolve()

            # Create directory if it doesn't exist
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")

            # Validate the directory
            return OutputConfigService.validate_directory(path)

        except PermissionError:
            return DirectoryValidationResult(
                is_valid=False,
                exists=False,
                is_writable=False,
                error=f"Permission denied creating directory: {directory}",
            )
        except Exception as e:
            return DirectoryValidationResult(
                is_valid=False,
                exists=False,
                is_writable=False,
                error=f"Failed to create directory: {e}",
            )

    def get_output_path(
        self,
        video_info: dict[str, Any],
        custom_directory: str | Path | None = None,
    ) -> tuple[Path | None, str | None]:
        """
        Get the full output path for a video download.

        Combines the download directory, subdirectory organization,
        and filename template to generate the complete output path.

        Args:
            video_info: Video metadata dictionary
            custom_directory: Optional custom directory override

        Returns:
            Tuple of (output_path, error_message)
        """
        settings = self.get_settings()

        # Determine base directory
        base_dir = Path(custom_directory) if custom_directory else Path(settings.download_directory)

        # Apply subdirectory organization
        subdir = self._get_subdirectory(video_info, settings.subdirectory_organization)
        if subdir:
            base_dir = base_dir / subdir

        # Ensure directory exists
        validation = self.ensure_directory(base_dir)
        if not validation.is_valid:
            return None, validation.error

        # Generate filename
        template = FilenameTemplate(settings.filename_template)
        result = template.render(video_info)

        if not result.success:
            return None, result.error

        return base_dir / result.filename, None

    def _get_subdirectory(
        self,
        video_info: dict[str, Any],
        organization: SubdirectoryOrganization,
    ) -> str | None:
        """
        Get subdirectory name based on organization preference.

        Args:
            video_info: Video metadata dictionary
            organization: Subdirectory organization preference

        Returns:
            Subdirectory name or None
        """
        if organization == SubdirectoryOrganization.NONE:
            return None

        if organization == SubdirectoryOrganization.BY_CHANNEL:
            uploader = video_info.get("uploader") or video_info.get("channel")
            if uploader:
                return self._sanitize_dirname(uploader)
            return None

        if organization == SubdirectoryOrganization.BY_PLAYLIST:
            playlist = video_info.get("playlist")
            if playlist:
                return self._sanitize_dirname(playlist)
            return None

        if organization == SubdirectoryOrganization.BY_DATE:
            from datetime import datetime
            return datetime.now().strftime("%Y-%m")

        return None

    @staticmethod
    def _sanitize_dirname(name: str) -> str:
        """
        Sanitize a string for use as a directory name.

        Args:
            name: String to sanitize

        Returns:
            Sanitized directory name
        """
        import re

        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)

        # Replace multiple underscores/spaces with single ones
        sanitized = re.sub(r"[_\s]+", "_", sanitized)

        # Remove leading/trailing underscores and spaces
        sanitized = sanitized.strip("_ ")

        # Truncate if too long
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized or "Unknown"

    def resolve_conflict(
        self,
        file_path: Path,
        resolution: ConflictResolution | None = None,
    ) -> tuple[Path, bool]:
        """
        Resolve a filename conflict based on preference.

        Args:
            file_path: Path that may conflict with existing file
            resolution: Optional override for conflict resolution

        Returns:
            Tuple of (resolved_path, should_download)
            - resolved_path: The path to use for download
            - should_download: Whether to proceed with download
        """
        if resolution is None:
            settings = self.get_settings()
            resolution = settings.conflict_resolution

        # If file doesn't exist, no conflict
        if not file_path.exists():
            return file_path, True

        if resolution == ConflictResolution.SKIP:
            logger.info(f"Skipping download, file exists: {file_path}")
            return file_path, False

        if resolution == ConflictResolution.OVERWRITE:
            logger.info(f"Will overwrite existing file: {file_path}")
            return file_path, True

        # RENAME: Find a unique filename
        return self._get_unique_path(file_path), True

    @staticmethod
    def _get_unique_path(file_path: Path) -> Path:
        """
        Get a unique path by adding a numeric suffix.

        Args:
            file_path: Original file path

        Returns:
            Unique file path with numeric suffix if needed
        """
        if not file_path.exists():
            return file_path

        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent

        counter = 1
        while True:
            new_path = parent / f"{stem} ({counter}){suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

            # Safety limit
            if counter > 1000:
                raise ValueError(f"Too many files with similar names: {file_path}")

    def get_template_variables(self) -> dict[str, str]:
        """
        Get available template variables with descriptions.

        Returns:
            Dictionary mapping variable names to descriptions
        """
        return self._filename_template.get_variables()

    def validate_template(self, template: str) -> tuple[bool, str | None]:
        """
        Validate a filename template.

        Args:
            template: Template string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        result = self._filename_template.validate(template)
        return result.is_valid, result.error
