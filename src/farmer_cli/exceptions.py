"""
Custom exception classes for the Farmer CLI application.

These exceptions provide more specific error handling and better
error messages for various failure scenarios in the video downloading
and management features.
"""

from typing import Any


class FarmerCLIError(Exception):
    """Base exception class for all Farmer CLI errors."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        """
        Initialize the exception.

        Args:
            message: The error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ConfigurationError(FarmerCLIError):
    """Raised when there's a configuration-related error."""

    pass


class DatabaseError(FarmerCLIError):
    """Raised when there's a database-related error."""

    pass


class NetworkError(FarmerCLIError):
    """Raised when there's a network-related error."""

    pass


class ValidationError(FarmerCLIError):
    """Raised when input validation fails."""

    pass


class FileOperationError(FarmerCLIError):
    """Raised when file operations fail."""

    pass


class AuthenticationError(FarmerCLIError):
    """Raised when authentication fails."""

    pass


class APIError(FarmerCLIError):
    """Raised when API calls fail."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: Any | None = None,
    ) -> None:
        """
        Initialize API error.

        Args:
            message: The error message
            status_code: HTTP status code if applicable
            response_data: Response data from the API
        """
        super().__init__(message, details={"status_code": status_code, "response": response_data})
        self.status_code = status_code
        self.response_data = response_data


class DownloadError(FarmerCLIError):
    """Raised when video download operations fail."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        details: Any | None = None,
    ) -> None:
        """
        Initialize download error.

        Args:
            message: The error message
            url: The URL that failed to download
            details: Additional error details
        """
        super().__init__(message, details=details)
        self.url = url


class FormatError(FarmerCLIError):
    """Raised when format selection or processing fails."""

    def __init__(
        self,
        message: str,
        format_id: str | None = None,
        details: Any | None = None,
    ) -> None:
        """
        Initialize format error.

        Args:
            message: The error message
            format_id: The format ID that caused the error
            details: Additional error details
        """
        super().__init__(message, details=details)
        self.format_id = format_id


class PlaylistError(FarmerCLIError):
    """Raised when playlist processing fails."""

    def __init__(
        self,
        message: str,
        playlist_url: str | None = None,
        details: Any | None = None,
    ) -> None:
        """
        Initialize playlist error.

        Args:
            message: The error message
            playlist_url: The playlist URL that caused the error
            details: Additional error details
        """
        super().__init__(message, details=details)
        self.playlist_url = playlist_url


class QueueError(FarmerCLIError):
    """Raised when download queue operations fail."""

    pass


class ExportError(FarmerCLIError):
    """Raised when data export operations fail."""

    pass
