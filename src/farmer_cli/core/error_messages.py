"""
User-friendly error message templates and utilities.

This module provides centralized error message handling with:
- User-friendly message templates for common errors
- Troubleshooting suggestions for network errors
- Error message sanitization to remove technical details

Feature: farmer-cli-completion
Requirements: 10.1, 10.4
"""

import re
from dataclasses import dataclass
from enum import Enum


# Maximum length for user-facing error messages
MAX_MESSAGE_LENGTH = 200


class ErrorCategory(Enum):
    """Categories of errors for message templating."""

    NETWORK = "network"
    DOWNLOAD = "download"
    FORMAT = "format"
    VALIDATION = "validation"
    DATABASE = "database"
    FILE = "file"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    PLAYLIST = "playlist"
    QUEUE = "queue"
    EXPORT = "export"
    UNKNOWN = "unknown"


@dataclass
class ErrorTemplate:
    """Template for user-friendly error messages."""

    message: str
    suggestions: list[str]
    category: ErrorCategory


# Error message templates for common errors
ERROR_TEMPLATES: dict[str, ErrorTemplate] = {
    # Network errors
    "connection_refused": ErrorTemplate(
        message="Unable to connect to the server. Please check your internet connection.",
        suggestions=[
            "Check if you're connected to the internet",
            "Try again in a few moments",
            "Check if the website is accessible in your browser",
        ],
        category=ErrorCategory.NETWORK,
    ),
    "connection_timeout": ErrorTemplate(
        message="Connection timed out. The server took too long to respond.",
        suggestions=[
            "Check your internet connection speed",
            "The server might be busy, try again later",
            "Try using a different network",
        ],
        category=ErrorCategory.NETWORK,
    ),
    "dns_resolution": ErrorTemplate(
        message="Could not resolve the server address. Please check the URL.",
        suggestions=[
            "Verify the URL is correct",
            "Check your DNS settings",
            "Try using a different DNS server",
        ],
        category=ErrorCategory.NETWORK,
    ),
    "ssl_error": ErrorTemplate(
        message="Secure connection failed. There may be a certificate issue.",
        suggestions=[
            "Check your system date and time are correct",
            "Try updating your system certificates",
            "The website's certificate may have expired",
        ],
        category=ErrorCategory.NETWORK,
    ),
    "network_unreachable": ErrorTemplate(
        message="Network is unreachable. Please check your connection.",
        suggestions=[
            "Verify your network connection is active",
            "Check if other websites are accessible",
            "Restart your network adapter or router",
        ],
        category=ErrorCategory.NETWORK,
    ),
    # Download errors
    "video_unavailable": ErrorTemplate(
        message="This video is not available. It may be private or deleted.",
        suggestions=[
            "Check if the video is still available on the platform",
            "The video may be region-restricted",
            "Try accessing the video in your browser first",
        ],
        category=ErrorCategory.DOWNLOAD,
    ),
    "age_restricted": ErrorTemplate(
        message="This video is age-restricted and requires authentication.",
        suggestions=[
            "Some platforms require login for age-restricted content",
            "Check if the video is available without restrictions",
        ],
        category=ErrorCategory.DOWNLOAD,
    ),
    "download_interrupted": ErrorTemplate(
        message="Download was interrupted. You can try resuming it.",
        suggestions=[
            "Check your internet connection",
            "Try resuming the download",
            "Ensure you have enough disk space",
        ],
        category=ErrorCategory.DOWNLOAD,
    ),
    "unsupported_url": ErrorTemplate(
        message="This URL is not supported. Please use a supported platform.",
        suggestions=[
            "Check if the URL is from a supported platform",
            "Verify the URL format is correct",
            "Try copying the URL directly from your browser",
        ],
        category=ErrorCategory.DOWNLOAD,
    ),
    # Format errors
    "format_unavailable": ErrorTemplate(
        message="The requested format is not available for this video.",
        suggestions=[
            "Try selecting a different format",
            "Use 'best' to automatically select the best available format",
            "List available formats first to see options",
        ],
        category=ErrorCategory.FORMAT,
    ),
    "invalid_format": ErrorTemplate(
        message="Invalid format specified. Please check the format ID.",
        suggestions=[
            "Use --format to specify a valid format ID",
            "List available formats to see valid options",
            "Use presets like 'best', '720p', or 'audio'",
        ],
        category=ErrorCategory.FORMAT,
    ),
    # Validation errors
    "invalid_url": ErrorTemplate(
        message="The provided URL is invalid. Please check and try again.",
        suggestions=[
            "Ensure the URL starts with http:// or https://",
            "Copy the URL directly from your browser",
            "Check for typos in the URL",
        ],
        category=ErrorCategory.VALIDATION,
    ),
    "invalid_path": ErrorTemplate(
        message="The specified path is invalid or inaccessible.",
        suggestions=[
            "Check if the directory exists",
            "Verify you have write permissions",
            "Try using an absolute path",
        ],
        category=ErrorCategory.VALIDATION,
    ),
    "empty_input": ErrorTemplate(
        message="Input cannot be empty. Please provide a value.",
        suggestions=[
            "Enter a valid value",
            "Check the required format for this field",
        ],
        category=ErrorCategory.VALIDATION,
    ),
    # Database errors
    "database_locked": ErrorTemplate(
        message="Database is currently locked. Please try again.",
        suggestions=[
            "Wait a moment and try again",
            "Close other instances of the application",
            "Check if another process is using the database",
        ],
        category=ErrorCategory.DATABASE,
    ),
    "database_corrupted": ErrorTemplate(
        message="Database appears to be corrupted. A backup may be needed.",
        suggestions=[
            "Try restoring from a backup",
            "Delete the database file to start fresh",
            "Contact support if the issue persists",
        ],
        category=ErrorCategory.DATABASE,
    ),
    # File errors
    "file_not_found": ErrorTemplate(
        message="The specified file was not found.",
        suggestions=[
            "Check if the file path is correct",
            "Verify the file hasn't been moved or deleted",
            "Use an absolute path to avoid confusion",
        ],
        category=ErrorCategory.FILE,
    ),
    "permission_denied": ErrorTemplate(
        message="Permission denied. Cannot access the file or directory.",
        suggestions=[
            "Check file/directory permissions",
            "Try running with appropriate permissions",
            "Choose a different location",
        ],
        category=ErrorCategory.FILE,
    ),
    "disk_full": ErrorTemplate(
        message="Not enough disk space to complete the operation.",
        suggestions=[
            "Free up disk space",
            "Choose a different download location",
            "Delete unnecessary files",
        ],
        category=ErrorCategory.FILE,
    ),
    # Playlist errors
    "playlist_empty": ErrorTemplate(
        message="The playlist is empty or contains no downloadable videos.",
        suggestions=[
            "Check if the playlist URL is correct",
            "The playlist may be private or empty",
            "Try accessing the playlist in your browser",
        ],
        category=ErrorCategory.PLAYLIST,
    ),
    "playlist_unavailable": ErrorTemplate(
        message="This playlist is not available or has been removed.",
        suggestions=[
            "Verify the playlist still exists",
            "Check if the playlist is public",
            "Try a different playlist URL",
        ],
        category=ErrorCategory.PLAYLIST,
    ),
    # Configuration errors
    "config_invalid": ErrorTemplate(
        message="Configuration is invalid. Using default settings.",
        suggestions=[
            "Check your configuration file for errors",
            "Reset to default configuration",
            "Verify all required settings are present",
        ],
        category=ErrorCategory.CONFIGURATION,
    ),
    # Export errors
    "export_failed": ErrorTemplate(
        message="Failed to export data. Please check the output path.",
        suggestions=[
            "Verify the output directory exists",
            "Check write permissions",
            "Try a different export location",
        ],
        category=ErrorCategory.EXPORT,
    ),
}


# Patterns to detect error types from exception messages
ERROR_PATTERNS: list[tuple[str, str]] = [
    (r"connection refused", "connection_refused"),
    (r"timed? ?out", "connection_timeout"),
    (r"name or service not known|dns|resolve", "dns_resolution"),
    (r"ssl|certificate|cert", "ssl_error"),
    (r"network.*(unreachable|down)", "network_unreachable"),
    (r"video.*(unavailable|not found|private|deleted)", "video_unavailable"),
    (r"age.*(restrict|gate)", "age_restricted"),
    (r"(download|transfer).*(interrupt|abort|cancel)", "download_interrupted"),
    (r"unsupported.*(url|site|platform)", "unsupported_url"),
    (r"format.*(unavailable|not found)", "format_unavailable"),
    (r"invalid.*format", "invalid_format"),
    (r"invalid.*(url|link)", "invalid_url"),
    (r"invalid.*(path|directory)", "invalid_path"),
    (r"(empty|blank|missing).*input", "empty_input"),
    (r"database.*lock", "database_locked"),
    (r"database.*(corrupt|damage)", "database_corrupted"),
    (r"(file|path).*not found", "file_not_found"),
    (r"permission.*denied|access.*denied", "permission_denied"),
    (r"(disk|space).*(full|insufficient)", "disk_full"),
    (r"playlist.*(empty|no videos)", "playlist_empty"),
    (r"playlist.*(unavailable|not found)", "playlist_unavailable"),
    (r"config.*(invalid|error|corrupt)", "config_invalid"),
    (r"export.*fail", "export_failed"),
]


def get_error_template(error_key: str) -> ErrorTemplate | None:
    """
    Get an error template by key.

    Args:
        error_key: The error template key

    Returns:
        ErrorTemplate if found, None otherwise
    """
    return ERROR_TEMPLATES.get(error_key)


def detect_error_type(error_message: str) -> str | None:
    """
    Detect the error type from an error message using pattern matching.

    Args:
        error_message: The raw error message

    Returns:
        Error template key if detected, None otherwise
    """
    message_lower = error_message.lower()

    for pattern, error_key in ERROR_PATTERNS:
        if re.search(pattern, message_lower):
            return error_key

    return None


def sanitize_error_message(message: str) -> str:
    """
    Sanitize an error message to remove technical details.

    Removes:
    - Stack traces
    - Internal file paths
    - Technical jargon
    - Excessive length

    Args:
        message: The raw error message

    Returns:
        Sanitized, user-friendly message
    """
    if not message:
        return "An unexpected error occurred."

    # Remove stack trace patterns (both full and abbreviated forms)
    message = re.sub(r"Traceback \(most recent call last\):.*", "", message, flags=re.DOTALL)
    message = re.sub(r"^Traceback:.*", "", message, flags=re.MULTILINE | re.DOTALL)
    message = re.sub(r"\nTraceback:.*", "", message, flags=re.DOTALL)
    message = re.sub(r"File \"[^\"]+\", line \d+.*", "", message, flags=re.MULTILINE)

    # Remove internal paths (Unix and Windows)
    message = re.sub(r"/[a-zA-Z0-9_/.-]+\.py(:\d+)?", "", message)
    message = re.sub(r"[A-Z]:\\[a-zA-Z0-9_\\.-]+\.py(:\d+)?", "", message)

    # Remove common technical prefixes
    message = re.sub(r"^(Error|Exception|Warning|Traceback):\s*", "", message, flags=re.IGNORECASE)
    message = re.sub(r"^\w+Error:\s*", "", message)
    message = re.sub(r"^\w+Exception:\s*", "", message)

    # Remove memory addresses
    message = re.sub(r"0x[0-9a-fA-F]+", "", message)

    # Remove module paths
    message = re.sub(r"\b[a-z_]+\.[a-z_]+\.[a-z_]+\b", "", message)

    # Clean up whitespace
    message = re.sub(r"\s+", " ", message).strip()

    # Truncate if too long
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH - 3] + "..."

    # Ensure message ends with proper punctuation
    if message and message[-1] not in ".!?":
        message += "."

    return message if message else "An unexpected error occurred."


def format_user_error(
    error: Exception | str,
    include_suggestions: bool = True,
) -> str:
    """
    Format an error into a user-friendly message.

    Args:
        error: The exception or error message
        include_suggestions: Whether to include troubleshooting suggestions

    Returns:
        Formatted user-friendly error message
    """
    # Get the error message
    if isinstance(error, Exception):
        raw_message = str(error)
    else:
        raw_message = error

    # Try to detect error type and get template
    error_key = detect_error_type(raw_message)

    if error_key and error_key in ERROR_TEMPLATES:
        template = ERROR_TEMPLATES[error_key]
        result = template.message

        if include_suggestions and template.suggestions:
            suggestions_text = "\n".join(f"  • {s}" for s in template.suggestions[:3])
            result = f"{result}\n\nSuggestions:\n{suggestions_text}"

        return result

    # Fall back to sanitized message
    return sanitize_error_message(raw_message)


def get_network_troubleshooting() -> str:
    """
    Get general network troubleshooting suggestions.

    Returns:
        Formatted troubleshooting text
    """
    suggestions = [
        "Check your internet connection",
        "Try accessing the URL in your browser",
        "Check if a firewall or proxy is blocking the connection",
        "Try again in a few moments",
        "Restart your network connection",
    ]

    return "Network Troubleshooting:\n" + "\n".join(f"  • {s}" for s in suggestions)


def is_user_friendly_message(message: str) -> bool:
    """
    Check if a message is user-friendly.

    A user-friendly message:
    - Does not contain stack traces
    - Does not contain internal paths
    - Does not contain technical jargon
    - Is under 200 characters

    Args:
        message: The message to check

    Returns:
        True if the message is user-friendly
    """
    if not message:
        return False

    # Check length
    if len(message) > MAX_MESSAGE_LENGTH:
        return False

    # Check for stack traces
    if "Traceback" in message or "File \"" in message:
        return False

    # Check for internal paths
    if re.search(r"/[a-zA-Z0-9_/.-]+\.py(:\d+)?", message):
        return False
    if re.search(r"[A-Z]:\\[a-zA-Z0-9_\\.-]+\.py(:\d+)?", message):
        return False

    # Check for memory addresses
    if re.search(r"0x[0-9a-fA-F]+", message):
        return False

    # Check for common technical patterns
    technical_patterns = [
        r"\w+Error:",
        r"\w+Exception:",
        r"at line \d+",
        r"in module",
        r"__\w+__",
    ]

    for pattern in technical_patterns:
        if re.search(pattern, message):
            return False

    return True


class UserFriendlyErrorHandler:
    """
    Handler for converting exceptions to user-friendly messages.

    This class provides a consistent interface for error handling
    throughout the application.
    """

    def __init__(self, include_suggestions: bool = True):
        """
        Initialize the error handler.

        Args:
            include_suggestions: Whether to include troubleshooting suggestions
        """
        self.include_suggestions = include_suggestions

    def handle(self, error: Exception | str) -> str:
        """
        Handle an error and return a user-friendly message.

        Args:
            error: The exception or error message

        Returns:
            User-friendly error message
        """
        return format_user_error(error, self.include_suggestions)

    def get_category(self, error: Exception | str) -> ErrorCategory:
        """
        Get the category of an error.

        Args:
            error: The exception or error message

        Returns:
            ErrorCategory enum value
        """
        raw_message = str(error) if isinstance(error, Exception) else error
        error_key = detect_error_type(raw_message)

        if error_key and error_key in ERROR_TEMPLATES:
            return ERROR_TEMPLATES[error_key].category

        return ErrorCategory.UNKNOWN

    def get_suggestions(self, error: Exception | str) -> list[str]:
        """
        Get troubleshooting suggestions for an error.

        Args:
            error: The exception or error message

        Returns:
            List of suggestion strings
        """
        raw_message = str(error) if isinstance(error, Exception) else error
        error_key = detect_error_type(raw_message)

        if error_key and error_key in ERROR_TEMPLATES:
            return ERROR_TEMPLATES[error_key].suggestions

        return []
