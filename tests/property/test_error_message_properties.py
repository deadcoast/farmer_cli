"""
Property-based tests for error message user-friendliness.

Feature: farmer-cli-completion
Property 9: Error Message User-Friendliness
Validates: Requirements 10.1

For any error displayed to the user, the message SHALL NOT contain stack traces,
internal paths, or technical jargon, and SHALL be under 200 characters.
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from farmer_cli.core.error_messages import (
    format_user_error,
    sanitize_error_message,
    is_user_friendly_message,
    MAX_MESSAGE_LENGTH,
    ERROR_TEMPLATES,
    UserFriendlyErrorHandler,
)


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating raw error messages with technical details
technical_error_strategy = st.one_of(
    # Stack traces
    st.just("Traceback (most recent call last):\n  File \"/usr/lib/python3.10/site.py\", line 73\n    raise ValueError"),
    # File paths
    st.just("Error in /home/user/project/src/module.py:42: invalid syntax"),
    # Memory addresses
    st.just("Object at 0x7f8b8c0d1e20 is not callable"),
    # Exception names
    st.just("ValueError: invalid literal for int() with base 10: 'abc'"),
    # Module paths
    st.just("farmer_cli.services.download_manager.DownloadError: failed"),
    # Combined technical details
    st.just("Traceback:\n  File \"/app/main.py\", line 10\nAttributeError: 'NoneType' object has no attribute 'foo'"),
)

# Strategy for generating simple error messages
simple_error_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=100,
).filter(lambda x: x.strip())

# Strategy for generating long error messages
long_error_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=250,
    max_size=500,
).filter(lambda x: x.strip())

# Strategy for network error messages
network_error_strategy = st.sampled_from([
    "Connection refused by server",
    "Connection timed out after 30 seconds",
    "DNS resolution failed for example.com",
    "SSL certificate verification failed",
    "Network is unreachable",
    "socket.timeout: The read operation timed out",
    "requests.exceptions.ConnectionError: Connection refused",
])

# Strategy for download error messages
download_error_strategy = st.sampled_from([
    "Video unavailable: This video is private",
    "Age-restricted content requires login",
    "Download interrupted at 50%",
    "Unsupported URL: example.com/video",
    "yt_dlp.utils.DownloadError: Video not found",
])


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestErrorMessageUserFriendliness:
    """
    Property 9: Error Message User-Friendliness

    For any error displayed to the user, the message SHALL NOT contain
    stack traces, internal paths, or technical jargon, and SHALL be
    under 200 characters.

    **Validates: Requirements 10.1**
    """

    @given(technical_error_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_sanitize_removes_stack_traces(self, error_msg: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any error message containing stack traces, sanitization SHALL
        remove them from the output.
        """
        result = sanitize_error_message(error_msg)

        assert "Traceback" not in result, f"Stack trace found in: {result}"
        assert "File \"" not in result, f"File reference found in: {result}"

    @given(technical_error_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_sanitize_removes_internal_paths(self, error_msg: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any error message containing internal paths, sanitization SHALL
        remove them from the output.
        """
        result = sanitize_error_message(error_msg)

        # Check for Unix paths
        assert ".py:" not in result or "line" not in result.lower(), \
            f"Internal path found in: {result}"
        # Check for Windows paths
        assert ":\\" not in result, f"Windows path found in: {result}"

    @given(technical_error_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_sanitize_removes_memory_addresses(self, error_msg: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any error message containing memory addresses, sanitization SHALL
        remove them from the output.
        """
        result = sanitize_error_message(error_msg)

        import re
        assert not re.search(r"0x[0-9a-fA-F]+", result), \
            f"Memory address found in: {result}"

    @given(long_error_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_sanitize_enforces_max_length(self, error_msg: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any error message, the sanitized output SHALL be under 200 characters.
        """
        result = sanitize_error_message(error_msg)

        assert len(result) <= MAX_MESSAGE_LENGTH, \
            f"Message too long ({len(result)} chars): {result[:50]}..."

    @given(simple_error_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_sanitize_preserves_meaningful_content(self, error_msg: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any simple error message, sanitization SHALL preserve the
        meaningful content (non-empty result).
        """
        result = sanitize_error_message(error_msg)

        assert result, "Sanitized message should not be empty"
        assert len(result) > 0, "Sanitized message should have content"

    @given(network_error_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_format_user_error_handles_network_errors(self, error_msg: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any network error, format_user_error SHALL return a user-friendly
        message without technical details.
        """
        result = format_user_error(error_msg, include_suggestions=False)

        assert is_user_friendly_message(result), \
            f"Message not user-friendly: {result}"
        assert len(result) <= MAX_MESSAGE_LENGTH, \
            f"Message too long: {len(result)} chars"

    @given(download_error_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_format_user_error_handles_download_errors(self, error_msg: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any download error, format_user_error SHALL return a user-friendly
        message without technical details.
        """
        result = format_user_error(error_msg, include_suggestions=False)

        assert is_user_friendly_message(result), \
            f"Message not user-friendly: {result}"
        assert len(result) <= MAX_MESSAGE_LENGTH, \
            f"Message too long: {len(result)} chars"

    @pytest.mark.property
    def test_all_templates_are_user_friendly(self):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For all error templates, the message SHALL be user-friendly.
        """
        for key, template in ERROR_TEMPLATES.items():
            assert is_user_friendly_message(template.message), \
                f"Template '{key}' message not user-friendly: {template.message}"
            assert len(template.message) <= MAX_MESSAGE_LENGTH, \
                f"Template '{key}' message too long: {len(template.message)} chars"

    @pytest.mark.property
    def test_all_templates_have_suggestions(self):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For all error templates, there SHALL be at least one suggestion.
        """
        for key, template in ERROR_TEMPLATES.items():
            assert len(template.suggestions) > 0, \
                f"Template '{key}' has no suggestions"

    @given(st.text(min_size=0, max_size=10))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_empty_or_short_input_handled_gracefully(self, error_msg: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any empty or very short input, sanitization SHALL return a
        valid user-friendly message.
        """
        result = sanitize_error_message(error_msg)

        assert result, "Result should not be empty"
        assert is_user_friendly_message(result), \
            f"Result not user-friendly: {result}"

    @given(st.sampled_from(list(ERROR_TEMPLATES.keys())))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_handler_returns_consistent_results(self, error_key: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any error key, the UserFriendlyErrorHandler SHALL return
        consistent, user-friendly results.
        """
        handler = UserFriendlyErrorHandler(include_suggestions=False)
        template = ERROR_TEMPLATES[error_key]

        # Create a mock error that would match this template
        result = handler.handle(template.message)

        assert is_user_friendly_message(result), \
            f"Handler result not user-friendly: {result}"

    @given(st.text(min_size=1, max_size=500).filter(lambda x: x.strip()))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_is_user_friendly_message_is_consistent(self, message: str):
        """
        Feature: farmer-cli-completion, Property 9: Error Message User-Friendliness
        Validates: Requirements 10.1

        For any message, is_user_friendly_message SHALL return a boolean
        and be consistent across multiple calls.
        """
        result1 = is_user_friendly_message(message)
        result2 = is_user_friendly_message(message)

        assert isinstance(result1, bool), "Result should be boolean"
        assert result1 == result2, "Results should be consistent"
