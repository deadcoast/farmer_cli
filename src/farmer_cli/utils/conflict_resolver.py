"""
Filename conflict resolution utilities for Farmer CLI.

This module provides functionality for detecting and resolving filename
conflicts during downloads.

Feature: farmer-cli-completion
Requirements: 6.3
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """Options for handling filename conflicts."""

    RENAME = "rename"  # Add suffix like (1), (2), etc.
    OVERWRITE = "overwrite"  # Replace existing file
    SKIP = "skip"  # Skip download if file exists


@dataclass
class ConflictResult:
    """
    Result of conflict resolution.

    Attributes:
        resolved_path: The path to use for the file
        should_proceed: Whether to proceed with the operation
        action_taken: Description of the action taken
        original_path: The original path that had a conflict
    """

    resolved_path: Path
    should_proceed: bool
    action_taken: str
    original_path: Path


def detect_conflict(file_path: str | Path) -> bool:
    """
    Detect if a file already exists at the given path.

    Args:
        file_path: Path to check for existing file

    Returns:
        True if file exists (conflict detected), False otherwise
    """
    return Path(file_path).exists()


def resolve_conflict(
    file_path: str | Path,
    resolution: ConflictResolution = ConflictResolution.RENAME,
) -> ConflictResult:
    """
    Resolve a filename conflict based on the specified resolution strategy.

    Args:
        file_path: Path that may conflict with existing file
        resolution: How to handle the conflict

    Returns:
        ConflictResult with the resolved path and action details
    """
    path = Path(file_path)
    original_path = path

    # If file doesn't exist, no conflict to resolve
    if not path.exists():
        return ConflictResult(
            resolved_path=path,
            should_proceed=True,
            action_taken="no_conflict",
            original_path=original_path,
        )

    if resolution == ConflictResolution.SKIP:
        logger.info(f"Skipping, file exists: {path}")
        return ConflictResult(
            resolved_path=path,
            should_proceed=False,
            action_taken="skipped",
            original_path=original_path,
        )

    if resolution == ConflictResolution.OVERWRITE:
        logger.info(f"Will overwrite existing file: {path}")
        return ConflictResult(
            resolved_path=path,
            should_proceed=True,
            action_taken="overwrite",
            original_path=original_path,
        )

    # RENAME: Find a unique filename
    unique_path = get_unique_path(path)
    logger.info(f"Renamed to avoid conflict: {path} -> {unique_path}")
    return ConflictResult(
        resolved_path=unique_path,
        should_proceed=True,
        action_taken="renamed",
        original_path=original_path,
    )


def get_unique_path(file_path: str | Path, max_attempts: int = 1000) -> Path:
    """
    Get a unique path by adding a numeric suffix.

    Generates paths like "filename (1).ext", "filename (2).ext", etc.
    until a non-existing path is found.

    Args:
        file_path: Original file path
        max_attempts: Maximum number of suffixes to try

    Returns:
        Unique file path with numeric suffix if needed

    Raises:
        ValueError: If unable to find unique path within max_attempts
    """
    path = Path(file_path)

    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    for counter in range(1, max_attempts + 1):
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path

    raise ValueError(f"Unable to find unique filename after {max_attempts} attempts: {file_path}")


def get_conflict_options() -> list[tuple[str, ConflictResolution, str]]:
    """
    Get available conflict resolution options for UI display.

    Returns:
        List of tuples (display_name, enum_value, description)
    """
    return [
        (
            "Rename",
            ConflictResolution.RENAME,
            "Add a number suffix to create a unique filename",
        ),
        (
            "Overwrite",
            ConflictResolution.OVERWRITE,
            "Replace the existing file with the new download",
        ),
        (
            "Skip",
            ConflictResolution.SKIP,
            "Skip this download and keep the existing file",
        ),
    ]


def suggest_resolution(file_path: str | Path) -> ConflictResolution:
    """
    Suggest a conflict resolution based on file characteristics.

    Args:
        file_path: Path to the conflicting file

    Returns:
        Suggested ConflictResolution
    """
    path = Path(file_path)

    if not path.exists():
        return ConflictResolution.RENAME  # Default, though no conflict

    # If file is very small (likely incomplete), suggest overwrite
    try:
        if path.stat().st_size < 1024:  # Less than 1KB
            return ConflictResolution.OVERWRITE
    except OSError:
        pass

    # Default to rename to preserve existing files
    return ConflictResolution.RENAME


class ConflictResolver:
    """
    Class for managing conflict resolution with configurable defaults.

    This class provides a stateful interface for conflict resolution,
    allowing configuration of default behavior and batch operations.
    """

    def __init__(
        self,
        default_resolution: ConflictResolution = ConflictResolution.RENAME,
        remember_choice: bool = False,
    ) -> None:
        """
        Initialize the conflict resolver.

        Args:
            default_resolution: Default resolution strategy
            remember_choice: Whether to remember user choices for batch operations
        """
        self._default_resolution = default_resolution
        self._remember_choice = remember_choice
        self._remembered_choice: ConflictResolution | None = None

    @property
    def default_resolution(self) -> ConflictResolution:
        """Get the default resolution strategy."""
        return self._default_resolution

    @default_resolution.setter
    def default_resolution(self, value: ConflictResolution) -> None:
        """Set the default resolution strategy."""
        self._default_resolution = value

    def resolve(
        self,
        file_path: str | Path,
        resolution: ConflictResolution | None = None,
    ) -> ConflictResult:
        """
        Resolve a conflict using the specified or default resolution.

        Args:
            file_path: Path that may conflict
            resolution: Optional override for resolution strategy

        Returns:
            ConflictResult with resolution details
        """
        # Use remembered choice if available and remember_choice is enabled
        if resolution is None and self._remember_choice and self._remembered_choice:
            resolution = self._remembered_choice

        # Fall back to default
        if resolution is None:
            resolution = self._default_resolution

        return resolve_conflict(file_path, resolution)

    def remember(self, resolution: ConflictResolution) -> None:
        """
        Remember a resolution choice for future conflicts.

        Args:
            resolution: Resolution to remember
        """
        self._remembered_choice = resolution

    def clear_remembered(self) -> None:
        """Clear any remembered resolution choice."""
        self._remembered_choice = None

    def has_conflict(self, file_path: str | Path) -> bool:
        """
        Check if a file path has a conflict.

        Args:
            file_path: Path to check

        Returns:
            True if conflict exists
        """
        return detect_conflict(file_path)

    def resolve_batch(
        self,
        file_paths: list[str | Path],
        resolution: ConflictResolution | None = None,
    ) -> list[ConflictResult]:
        """
        Resolve conflicts for multiple files.

        Args:
            file_paths: List of paths to resolve
            resolution: Optional resolution strategy for all files

        Returns:
            List of ConflictResult for each file
        """
        return [self.resolve(path, resolution) for path in file_paths]
