"""
Logging configuration for Farmer CLI.

This module provides centralized logging configuration with:
- Console handler for user-friendly messages (WARNING and above)
- File handler with full stack traces (DEBUG and above)
- Configurable log levels

Feature: farmer-cli-completion
Requirements: 10.2, 10.3
"""

import logging
import sys
from pathlib import Path
from typing import Optional


# Default log directory
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_LOG_FILE = "cli_app.log"

# Log format strings
CONSOLE_FORMAT = "%(message)s"
FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
FILE_FORMAT_WITH_TRACE = (
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s\n"
    "%(exc_text)s"
)

# Valid log levels
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class UserFriendlyFormatter(logging.Formatter):
    """
    Custom formatter that produces user-friendly console messages.

    Strips technical details like stack traces and internal paths,
    keeping messages concise and actionable.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record for console output.

        Args:
            record: The log record to format

        Returns:
            Formatted message string
        """
        # Don't include exception info in console output
        record.exc_info = None
        record.exc_text = None
        return super().format(record)


class DetailedFileFormatter(logging.Formatter):
    """
    Custom formatter that includes full details for file logging.

    Includes timestamps, logger names, levels, messages, and full
    stack traces for debugging purposes.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with full details.

        Args:
            record: The log record to format

        Returns:
            Formatted message string with full details
        """
        # Format the basic message
        result = super().format(record)

        # Add exception info if present
        if record.exc_info:
            # Format exception with full traceback
            exc_text = self.formatException(record.exc_info)
            if exc_text:
                result = f"{result}\n{exc_text}"

        return result


class LoggingConfig:
    """
    Centralized logging configuration manager.

    Provides methods to configure, update, and manage logging
    throughout the application lifecycle.
    """

    _instance: Optional["LoggingConfig"] = None
    _initialized: bool = False

    def __new__(cls) -> "LoggingConfig":
        """Singleton pattern to ensure single configuration instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the logging configuration."""
        if LoggingConfig._initialized:
            return

        self._log_level = logging.INFO
        self._log_file: Optional[Path] = None
        self._console_handler: Optional[logging.Handler] = None
        self._file_handler: Optional[logging.Handler] = None
        self._root_logger = logging.getLogger()

        LoggingConfig._initialized = True

    def configure(
        self,
        log_level: str = "INFO",
        log_file: Optional[Path] = None,
        log_dir: Optional[Path] = None,
        console_level: str = "WARNING",
    ) -> None:
        """
        Configure the logging system.

        Args:
            log_level: Overall log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional, uses default if not provided)
            log_dir: Directory for log files (optional, uses default if not provided)
            console_level: Log level for console output (default: WARNING)

        Raises:
            ValueError: If invalid log level is provided
        """
        # Validate log level
        log_level_upper = log_level.upper()
        if log_level_upper not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid log level: {log_level}. "
                f"Valid levels: {', '.join(VALID_LOG_LEVELS)}"
            )

        console_level_upper = console_level.upper()
        if console_level_upper not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid console log level: {console_level}. "
                f"Valid levels: {', '.join(VALID_LOG_LEVELS)}"
            )

        # Set log level
        self._log_level = getattr(logging, log_level_upper)
        console_log_level = getattr(logging, console_level_upper)

        # Determine log file path
        if log_file:
            self._log_file = log_file
        else:
            log_directory = log_dir or DEFAULT_LOG_DIR
            log_directory.mkdir(parents=True, exist_ok=True)
            self._log_file = log_directory / DEFAULT_LOG_FILE

        # Clear existing handlers
        self._clear_handlers()

        # Configure root logger
        self._root_logger.setLevel(self._log_level)

        # Set up console handler (user-friendly messages)
        self._setup_console_handler(console_log_level)

        # Set up file handler (detailed logging)
        self._setup_file_handler()

    def _clear_handlers(self) -> None:
        """Remove existing handlers from the root logger."""
        for handler in self._root_logger.handlers[:]:
            handler.close()
            self._root_logger.removeHandler(handler)

        self._console_handler = None
        self._file_handler = None

    def _setup_console_handler(self, level: int) -> None:
        """
        Set up the console handler for user-friendly output.

        Args:
            level: Logging level for console output
        """
        self._console_handler = logging.StreamHandler(sys.stderr)
        self._console_handler.setLevel(level)
        self._console_handler.setFormatter(UserFriendlyFormatter(CONSOLE_FORMAT))
        self._root_logger.addHandler(self._console_handler)

    def _setup_file_handler(self) -> None:
        """Set up the file handler for detailed logging."""
        if not self._log_file:
            return

        # Ensure log directory exists
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

        self._file_handler = logging.FileHandler(
            self._log_file,
            mode="a",
            encoding="utf-8",
        )
        self._file_handler.setLevel(logging.DEBUG)  # Capture all levels
        self._file_handler.setFormatter(DetailedFileFormatter(FILE_FORMAT))
        self._root_logger.addHandler(self._file_handler)

    def set_level(self, level: str) -> None:
        """
        Update the logging level.

        Args:
            level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Raises:
            ValueError: If invalid log level is provided
        """
        level_upper = level.upper()
        if level_upper not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid log level: {level}. "
                f"Valid levels: {', '.join(VALID_LOG_LEVELS)}"
            )

        self._log_level = getattr(logging, level_upper)
        self._root_logger.setLevel(self._log_level)

    def set_console_level(self, level: str) -> None:
        """
        Update the console handler log level.

        Args:
            level: New console log level

        Raises:
            ValueError: If invalid log level is provided
        """
        level_upper = level.upper()
        if level_upper not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid log level: {level}. "
                f"Valid levels: {', '.join(VALID_LOG_LEVELS)}"
            )

        if self._console_handler:
            self._console_handler.setLevel(getattr(logging, level_upper))

    def get_log_file_path(self) -> Optional[Path]:
        """
        Get the current log file path.

        Returns:
            Path to the log file, or None if not configured
        """
        return self._log_file

    def get_recent_logs(
        self,
        count: int = 50,
        level_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Read recent log entries from the log file.

        Args:
            count: Maximum number of entries to return
            level_filter: Optional filter by log level

        Returns:
            List of log entry dictionaries with timestamp, level, and message
        """
        if not self._log_file or not self._log_file.exists():
            return []

        entries = []
        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Parse log entries (simple parsing based on format)
            for line in lines[-count * 2:]:  # Read extra lines for multi-line entries
                line = line.strip()
                if not line:
                    continue

                # Try to parse the log line
                entry = self._parse_log_line(line)
                if entry:
                    # Apply level filter if specified
                    if level_filter:
                        if entry["level"].upper() == level_filter.upper():
                            entries.append(entry)
                    else:
                        entries.append(entry)

            # Return only the requested count
            return entries[-count:]

        except Exception:
            return []

    def _parse_log_line(self, line: str) -> Optional[dict]:
        """
        Parse a log line into a structured dictionary.

        Args:
            line: Raw log line string

        Returns:
            Dictionary with timestamp, level, logger, and message, or None
        """
        # Expected format: "2025-08-20 03:12:48,294 - __main__ - INFO - Message"
        try:
            parts = line.split(" - ", 3)
            if len(parts) >= 4:
                return {
                    "timestamp": parts[0],
                    "logger": parts[1],
                    "level": parts[2],
                    "message": parts[3],
                }
            elif len(parts) == 3:
                # Might be continuation of previous entry
                return None
        except Exception:
            pass
        return None

    def clear_log_file(self) -> bool:
        """
        Clear the log file contents.

        Returns:
            True if successful, False otherwise
        """
        if not self._log_file:
            return False

        try:
            # Close file handler temporarily
            if self._file_handler:
                self._file_handler.close()
                self._root_logger.removeHandler(self._file_handler)

            # Clear the file
            with open(self._log_file, "w", encoding="utf-8") as f:
                f.write("")

            # Re-setup file handler
            self._setup_file_handler()
            return True

        except Exception:
            return False


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    log_dir: Optional[Path] = None,
    console_level: str = "WARNING",
) -> LoggingConfig:
    """
    Configure application logging.

    This is the main entry point for setting up logging. It configures:
    - Console handler for user-friendly messages (WARNING and above by default)
    - File handler with full stack traces (DEBUG and above)

    Args:
        log_level: Overall log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_dir: Directory for log files (optional)
        console_level: Log level for console output (default: WARNING)

    Returns:
        The LoggingConfig instance

    Example:
        >>> configure_logging(log_level="DEBUG", console_level="INFO")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("This will appear in the log file")
        >>> logger.warning("This will appear in console and log file")
    """
    config = LoggingConfig()
    config.configure(
        log_level=log_level,
        log_file=log_file,
        log_dir=log_dir,
        console_level=console_level,
    )
    return config


def get_logging_config() -> LoggingConfig:
    """
    Get the current logging configuration instance.

    Returns:
        The LoggingConfig singleton instance
    """
    return LoggingConfig()
