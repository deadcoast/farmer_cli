"""
Custom exception classes for the Farmer CLI application.

These exceptions provide more specific error handling and better
error messages for various failure scenarios.
"""

from typing import Any
from typing import Optional


class FarmerCLIError(Exception):
    """Base exception class for all Farmer CLI errors."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
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

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Any] = None) -> None:
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
