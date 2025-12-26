"""
Validators for Farmer CLI.

This module provides validation functions for various input types.
"""

import json
import re
from pathlib import Path
from typing import Any


def validate_json(value: str) -> bool:
    """
    Validate if a string is valid JSON.

    Args:
        value: String to validate

    Returns:
        True if valid JSON
    """
    try:
        json.loads(value)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_path(path: str, must_exist: bool = False, must_be_dir: bool = False) -> bool:
    """
    Validate a file system path.

    Args:
        path: Path to validate
        must_exist: Whether the path must exist
        must_be_dir: Whether the path must be a directory

    Returns:
        True if valid path
    """
    try:
        p = Path(path)

        if must_exist and not p.exists():
            return False

        return not must_be_dir or not p.exists() or p.is_dir()
    except (ValueError, OSError):
        return False


def validate_positive_int(value: Any) -> bool:
    """
    Validate if a value is a positive integer.

    Args:
        value: Value to validate

    Returns:
        True if positive integer
    """
    try:
        num = int(value)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_port(port: Any) -> bool:
    """
    Validate if a value is a valid port number.

    Args:
        port: Port number to validate

    Returns:
        True if valid port (1-65535)
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid URL format
    """
    pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))


def validate_version(version: str) -> bool:
    """
    Validate semantic version format.

    Args:
        version: Version string to validate

    Returns:
        True if valid semantic version (e.g., 1.2.3)
    """
    pattern = r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9\-\.]+)?(?:\+[a-zA-Z0-9\-\.]+)?$"
    return bool(re.match(pattern, version))


def validate_non_empty(value: Any) -> bool:
    """
    Validate that a value is not empty.

    Args:
        value: Value to validate

    Returns:
        True if not empty
    """
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return len(value) > 0 if hasattr(value, "__len__") else True


def validate_choice(value: Any, choices: list) -> bool:
    """
    Validate that a value is in a list of choices.

    Args:
        value: Value to validate
        choices: List of valid choices

    Returns:
        True if value in choices
    """
    return value in choices


def validate_range(value: Any, min_val: float | None = None, max_val: float | None = None) -> bool:
    """
    Validate that a numeric value is within a range.

    Args:
        value: Value to validate
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)

    Returns:
        True if value in range
    """
    try:
        num = float(value)

        if min_val is not None and num < min_val:
            return False

        return max_val is None or num <= max_val
    except (ValueError, TypeError):
        return False
