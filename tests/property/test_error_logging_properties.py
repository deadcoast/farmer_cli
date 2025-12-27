"""
Property-based tests for error logging completeness.

Feature: farmer-cli-completion
Property 10: Error Logging Completeness
Validates: Requirements 10.2

For any error that occurs, the log file SHALL contain an entry with
timestamp, error type, message, and full stack trace.
"""

import logging
import re
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from farmer_cli.core.logging_config import (
    configure_logging,
    LoggingConfig,
    VALID_LOG_LEVELS,
)


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for log levels
log_level_strategy = st.sampled_from(VALID_LOG_LEVELS)

# Strategy for log messages
log_message_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=200,
).filter(lambda x: x.strip())

# Strategy for logger names
logger_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip() and x.isidentifier())

# Strategy for exception types
exception_type_strategy = st.sampled_from([
    ValueError,
    TypeError,
    RuntimeError,
    IOError,
    KeyError,
    AttributeError,
])


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def create_temp_log_config() -> tuple[LoggingConfig, Path]:
    """Create a logging config with a temporary log file."""
    temp_dir = Path(tempfile.mkdtemp())
    log_file = temp_dir / "test.log"

    # Reset singleton for testing
    LoggingConfig._instance = None
    LoggingConfig._initialized = False

    config = configure_logging(
        log_level="DEBUG",
        log_file=log_file,
        console_level="CRITICAL",  # Suppress console output during tests
    )

    return config, log_file


def read_log_file(log_file: Path) -> str:
    """Read the contents of a log file."""
    if log_file.exists():
        return log_file.read_text(encoding="utf-8")
    return ""


def cleanup_logging():
    """Clean up logging configuration after tests."""
    # Remove all handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    # Reset singleton
    LoggingConfig._instance = None
    LoggingConfig._initialized = False


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestErrorLoggingCompleteness:
    """
    Property 10: Error Logging Completeness

    For any error that occurs, the log file SHALL contain an entry with
    timestamp, error type, message, and full stack trace.

    **Validates: Requirements 10.2**
    """

    def setup_method(self):
        """Set up test fixtures."""
        cleanup_logging()

    def teardown_method(self):
        """Clean up after tests."""
        cleanup_logging()

    @given(log_message_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_log_entries_contain_timestamp(self, message: str):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        For any logged message, the log file SHALL contain a timestamp.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger("test_timestamp")
            logger.error(message)

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            log_content = read_log_file(log_file)

            # Check for timestamp pattern (YYYY-MM-DD HH:MM:SS,mmm)
            timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}"
            assert re.search(timestamp_pattern, log_content), \
                f"No timestamp found in log: {log_content[:200]}"
        finally:
            cleanup_logging()

    @given(log_message_strategy, logger_name_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_log_entries_contain_logger_name(self, message: str, logger_name: str):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        For any logged message, the log file SHALL contain the logger name.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger(logger_name)
            logger.error(message)

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            log_content = read_log_file(log_file)

            assert logger_name in log_content, \
                f"Logger name '{logger_name}' not found in log: {log_content[:200]}"
        finally:
            cleanup_logging()

    @given(log_level_strategy, log_message_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_log_entries_contain_level(self, level: str, message: str):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        For any logged message, the log file SHALL contain the log level.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger("test_level")
            log_method = getattr(logger, level.lower())
            log_method(message)

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            log_content = read_log_file(log_file)

            assert level in log_content, \
                f"Log level '{level}' not found in log: {log_content[:200]}"
        finally:
            cleanup_logging()

    @given(log_message_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_log_entries_contain_message(self, message: str):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        For any logged message, the log file SHALL contain the message content.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger("test_message")
            logger.error(message)

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            log_content = read_log_file(log_file)

            assert message in log_content, \
                f"Message '{message[:50]}...' not found in log: {log_content[:200]}"
        finally:
            cleanup_logging()

    @given(exception_type_strategy, log_message_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_exceptions_include_stack_trace(self, exc_type: type, message: str):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        For any exception logged with exc_info, the log file SHALL contain
        the full stack trace.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger("test_exception")

            try:
                raise exc_type(message)
            except exc_type:
                logger.error("An error occurred", exc_info=True)

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            log_content = read_log_file(log_file)

            # Check for exception type name
            assert exc_type.__name__ in log_content, \
                f"Exception type '{exc_type.__name__}' not found in log"

            # Check for traceback indicator
            assert "Traceback" in log_content or "File" in log_content, \
                f"No stack trace found in log: {log_content[:500]}"
        finally:
            cleanup_logging()

    @given(exception_type_strategy, log_message_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_exceptions_include_error_message(self, exc_type: type, message: str):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        For any exception logged, the log file SHALL contain the error message.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger("test_exc_message")

            try:
                raise exc_type(message)
            except exc_type:
                logger.error("An error occurred", exc_info=True)

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            log_content = read_log_file(log_file)

            # The exception message should appear in the traceback
            assert message in log_content, \
                f"Exception message '{message[:50]}...' not found in log"
        finally:
            cleanup_logging()

    @pytest.mark.property
    def test_log_format_is_parseable(self):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        Log entries SHALL follow a consistent, parseable format.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger("test_format")
            logger.error("Test message for format validation")

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            log_content = read_log_file(log_file)

            # Expected format: "YYYY-MM-DD HH:MM:SS,mmm - logger - LEVEL - message"
            pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - \w+ - \w+ - .+"
            assert re.search(pattern, log_content), \
                f"Log format doesn't match expected pattern: {log_content[:200]}"
        finally:
            cleanup_logging()

    @given(st.lists(log_message_strategy, min_size=1, max_size=5))
    @settings(max_examples=50)
    @pytest.mark.property
    def test_multiple_log_entries_are_preserved(self, messages: list[str]):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        For any sequence of log messages, all entries SHALL be preserved
        in the log file.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger("test_multiple")

            for msg in messages:
                logger.error(msg)

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            log_content = read_log_file(log_file)

            for msg in messages:
                assert msg in log_content, \
                    f"Message '{msg[:30]}...' not found in log"
        finally:
            cleanup_logging()

    @given(log_level_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_log_level_configuration_is_respected(self, level: str):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        The configured log level SHALL be respected for filtering messages.
        """
        config, log_file = create_temp_log_config()

        try:
            # Set the log level
            config.set_level(level)

            logger = logging.getLogger("test_level_config")

            # Log at all levels
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")
            logger.critical("critical message")

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            log_content = read_log_file(log_file)

            # Messages at or above the configured level should appear
            level_order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            level_index = level_order.index(level)

            for i, lvl in enumerate(level_order):
                msg = f"{lvl.lower()} message"
                if i >= level_index:
                    assert msg in log_content, \
                        f"Message at level {lvl} should appear when level is {level}"
        finally:
            cleanup_logging()

    @pytest.mark.property
    def test_get_recent_logs_returns_valid_structure(self):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        get_recent_logs() SHALL return a list of dictionaries with
        timestamp, level, logger, and message fields.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger("test_recent")
            logger.error("Test error message")
            logger.warning("Test warning message")

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            entries = config.get_recent_logs(count=10)

            assert isinstance(entries, list), "Should return a list"

            for entry in entries:
                assert isinstance(entry, dict), "Each entry should be a dict"
                assert "timestamp" in entry, "Entry should have timestamp"
                assert "level" in entry, "Entry should have level"
                assert "message" in entry, "Entry should have message"
        finally:
            cleanup_logging()

    @given(log_level_strategy)
    @settings(max_examples=50)
    @pytest.mark.property
    def test_get_recent_logs_respects_level_filter(self, filter_level: str):
        """
        Feature: farmer-cli-completion, Property 10: Error Logging Completeness
        Validates: Requirements 10.2

        get_recent_logs() with level_filter SHALL only return entries
        at the specified level.
        """
        config, log_file = create_temp_log_config()

        try:
            logger = logging.getLogger("test_filter")

            # Log at all levels
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")
            logger.critical("critical message")

            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()

            entries = config.get_recent_logs(count=10, level_filter=filter_level)

            for entry in entries:
                assert entry["level"].upper() == filter_level.upper(), \
                    f"Entry level {entry['level']} doesn't match filter {filter_level}"
        finally:
            cleanup_logging()
