"""
Farmer CLI - A powerful CLI application with Rich UI for video downloading.

This package provides a modular, maintainable command-line interface application
with features including user management, weather checking, file browsing, and more.

Modules:
    - core: Core application logic and initialization
    - models: Database models and ORM definitions
    - ui: User interface components and layouts
    - features: Individual feature implementations
    - services: Business logic and external service integrations
    - utils: Utility functions and helpers

Example:
    To run the application:

    $ python -m farmer_cli

    Or after installation:

    $ farmer-cli
"""

__version__ = "0.2.0"
__author__ = "Farmer CLI Team"
__email__ = "support@farmercli.com"

# Import key components for easier access
from .core.app import FarmerCLI
from .core.database import DatabaseManager
from .ui.console import console


__all__ = ["DatabaseManager", "FarmerCLI", "__author__", "__email__", "__version__", "console"]
