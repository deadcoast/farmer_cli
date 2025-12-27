"""
Core module for Farmer CLI application.

This module contains the core application logic, database management,
logging configuration, and fundamental constants used throughout the application.

Components:
    - app: Main application class and lifecycle management
    - database: Database initialization and session management
    - constants: Application-wide constants and configuration
    - logging_config: Centralized logging configuration
    - error_messages: User-friendly error message handling
"""

from .app import FarmerCLI
from .constants import APP_NAME
from .constants import APP_VERSION
from .constants import DEFAULT_THEME
from .constants import MENU_OPTIONS
from .database import DatabaseManager
from .database import get_session
from .error_messages import ErrorCategory
from .error_messages import UserFriendlyErrorHandler
from .error_messages import format_user_error
from .error_messages import get_network_troubleshooting
from .error_messages import is_user_friendly_message
from .error_messages import sanitize_error_message
from .logging_config import LoggingConfig
from .logging_config import configure_logging
from .logging_config import get_logging_config


__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_THEME",
    "MENU_OPTIONS",
    "DatabaseManager",
    "FarmerCLI",
    "get_session",
    "LoggingConfig",
    "configure_logging",
    "get_logging_config",
    "ErrorCategory",
    "UserFriendlyErrorHandler",
    "format_user_error",
    "get_network_troubleshooting",
    "is_user_friendly_message",
    "sanitize_error_message",
]
