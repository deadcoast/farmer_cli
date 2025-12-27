"""
Directory validation utilities for Farmer CLI.

This module provides functionality for validating and managing directories
for download operations.

Feature: farmer-cli-completion
Requirements: 6.5, 6.6
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class DirectoryValidationResult:
    """
    Result of directory validation.

    Attributes:
        is_valid: Whether the directory is valid for use
        exists: Whether the directory exists
        is_writable: Whether the directory is writable
        error: Error message if validation failed
    """

    is_valid: bool
    exists: bool
    is_writable: bool
    error: str | None = None


def validate_directory(directory: str | Path) -> DirectoryValidationResult:
    """
    Validate that a directory path exists and is writable.

    This function checks:
    1. The path is valid and can be resolved
    2. The path exists
    3. The path is a directory (not a file)
    4. The directory is writable

    Args:
        directory: Path to validate

    Returns:
        DirectoryValidationResult with validation details

    Examples:
        >>> result = validate_directory("/tmp")
        >>> result.is_valid
        True
        >>> result = validate_directory("/nonexistent/path")
        >>> result.is_valid
        False
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

    except OSError as e:
        return DirectoryValidationResult(
            is_valid=False,
            exists=False,
            is_writable=False,
            error=f"OS error validating path: {e}",
        )
    except Exception as e:
        return DirectoryValidationResult(
            is_valid=False,
            exists=False,
            is_writable=False,
            error=f"Invalid path: {e}",
        )


def ensure_directory(directory: str | Path) -> DirectoryValidationResult:
    """
    Ensure a directory exists, creating it if necessary.

    This function will:
    1. Create the directory and any parent directories if they don't exist
    2. Validate the directory after creation

    Args:
        directory: Path to ensure exists

    Returns:
        DirectoryValidationResult with validation details

    Examples:
        >>> result = ensure_directory("/tmp/test_dir")
        >>> result.is_valid
        True
    """
    try:
        path = Path(directory).resolve()

        # Create directory if it doesn't exist
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")

        # Validate the directory
        return validate_directory(path)

    except PermissionError:
        return DirectoryValidationResult(
            is_valid=False,
            exists=False,
            is_writable=False,
            error=f"Permission denied creating directory: {directory}",
        )
    except OSError as e:
        return DirectoryValidationResult(
            is_valid=False,
            exists=False,
            is_writable=False,
            error=f"OS error creating directory: {e}",
        )
    except Exception as e:
        return DirectoryValidationResult(
            is_valid=False,
            exists=False,
            is_writable=False,
            error=f"Failed to create directory: {e}",
        )


def is_path_writable(path: str | Path) -> bool:
    """
    Check if a path is writable.

    For existing paths, checks write permission.
    For non-existing paths, checks if parent directory is writable.

    Args:
        path: Path to check

    Returns:
        True if path is writable, False otherwise
    """
    try:
        resolved = Path(path).resolve()

        if resolved.exists():
            return os.access(resolved, os.W_OK)

        # Check parent directory
        parent = resolved.parent
        while not parent.exists() and parent != parent.parent:
            parent = parent.parent

        return os.access(parent, os.W_OK) if parent.exists() else False

    except Exception:
        return False


def get_available_space(directory: str | Path) -> int | None:
    """
    Get available disk space in bytes for a directory.

    Args:
        directory: Path to check

    Returns:
        Available space in bytes, or None if unable to determine
    """
    try:
        path = Path(directory).resolve()

        # Find existing parent if directory doesn't exist
        while not path.exists() and path != path.parent:
            path = path.parent

        if not path.exists():
            return None

        stat = os.statvfs(path)
        return stat.f_bavail * stat.f_frsize

    except (OSError, AttributeError):
        # statvfs not available on Windows, use shutil
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            return free
        except Exception:
            return None


def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path by resolving it and expanding user home.

    Args:
        path: Path to normalize

    Returns:
        Normalized Path object
    """
    return Path(path).expanduser().resolve()


def is_subdirectory(child: str | Path, parent: str | Path) -> bool:
    """
    Check if a path is a subdirectory of another path.

    Args:
        child: Potential child path
        parent: Potential parent path

    Returns:
        True if child is a subdirectory of parent
    """
    try:
        child_path = normalize_path(child)
        parent_path = normalize_path(parent)
        return parent_path in child_path.parents or child_path == parent_path
    except Exception:
        return False
