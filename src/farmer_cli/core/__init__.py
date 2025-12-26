"""
Core module for Farmer CLI application.

This module contains the core application logic, database management,
and fundamental constants used throughout the application.

Components:
    - app: Main application class and lifecycle management
    - database: Database initialization and session management
    - constants: Application-wide constants and configuration
"""

from .app import FarmerCLI
from .constants import APP_NAME
from .constants import APP_VERSION
from .constants import DEFAULT_THEME
from .constants import MENU_OPTIONS
from .database import DatabaseManager
from .database import get_session


__all__ = ["FarmerCLI", "DatabaseManager", "get_session", "APP_NAME", "APP_VERSION", "MENU_OPTIONS", "DEFAULT_THEME"]
