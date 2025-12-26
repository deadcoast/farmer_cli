"""
Cleanup utilities for Farmer CLI.

This module provides cleanup handlers for graceful application shutdown.
"""

import logging
from datetime import datetime
from typing import Callable
from typing import List

from ..core.database import get_database_manager
from ..services.preferences import PreferencesService
from ..ui.console import console


logger = logging.getLogger(__name__)

# List of cleanup handlers
_cleanup_handlers: List[Callable[[], None]] = []


def register_cleanup(handler: Callable[[], None]) -> None:
    """
    Register a cleanup handler.

    Args:
        handler: Function to call during cleanup
    """
    _cleanup_handlers.append(handler)


def _run_cleanup_handler(handler: Callable[[], None]) -> None:
    try:
        handler()
    except Exception as e:
        logger.error(f"Cleanup handler failed: {e}")


def cleanup_handler() -> None:
    """
    Main cleanup handler called on application exit.

    This function is registered with atexit and performs
    all necessary cleanup operations.
    """
    console.print("\n[bold red]Cleaning up before exit...[/bold red]")

    try:
        # Save exit timestamp to preferences
        try:
            prefs_service = PreferencesService()
            preferences = prefs_service.load()
            preferences["last_exit"] = datetime.now().isoformat()
            prefs_service.save(preferences)
        except Exception as e:
            logger.error(f"Failed to save exit timestamp: {e}")

        # Close database connections
        try:
            db_manager = get_database_manager()
            db_manager.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Failed to close database: {e}")

        # Run registered cleanup handlers
        for handler in _cleanup_handlers:
            _run_cleanup_handler(handler)

        logger.info("Application exited gracefully")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def cleanup_temp_files() -> None:
    """Clean up temporary files created during the session."""
    from pathlib import Path

    from ..core.constants import HTML_TEMP_FILE

    temp_files = [Path(HTML_TEMP_FILE), Path("temp_export.csv"), Path(".tmp_feedback.txt")]

    for temp_file in temp_files:
        if temp_file.exists():
            try:
                temp_file.unlink()
                logger.debug(f"Removed temporary file: {temp_file}")
            except OSError as e:
                logger.warning(f"Failed to remove {temp_file}: {e}")


# Register default cleanup handlers
register_cleanup(cleanup_temp_files)
