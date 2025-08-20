"""Custom exceptions for the Farmer CLI application."""

from .cli_exceptions import APIError
from .cli_exceptions import AuthenticationError
from .cli_exceptions import ConfigurationError
from .cli_exceptions import DatabaseError
from .cli_exceptions import FarmerCLIError
from .cli_exceptions import FileOperationError
from .cli_exceptions import NetworkError
from .cli_exceptions import ValidationError


__all__ = [
    "FarmerCLIError",
    "ConfigurationError",
    "DatabaseError",
    "NetworkError",
    "ValidationError",
    "FileOperationError",
    "AuthenticationError",
    "APIError",
]
