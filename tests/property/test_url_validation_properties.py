"""
Property-based tests for URL validation utilities.

Feature: farmer-cli-completion
Property 12: Invalid URL Error Handling
Validates: Requirements 1.2

For any invalid or unsupported URL provided to the Video_Downloader,
it SHALL return an error result (not raise an unhandled exception)
with a descriptive message.
"""

import string

import pytest
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st


# Import the module under test
from farmer_cli.utils.url_utils import extract_video_id
from farmer_cli.utils.url_utils import is_supported_platform
from farmer_cli.utils.url_utils import is_valid_url


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating invalid URLs
invalid_url_strategy = st.one_of(
    st.just(""),  # Empty string
    st.just("   "),  # Whitespace only
    st.text(min_size=1, max_size=50).filter(lambda x: "://" not in x),  # No scheme
    st.sampled_from([
        "javascript:alert('xss')",
        "data:text/html,<script>alert('xss')</script>",
        "file:///etc/passwd",
        "vbscript:msgbox('xss')",
        "ftp://example.com/video.mp4",
        "http://",
        "https://",
        "://missing-scheme.com",
        "http:///no-domain",
    ]),
)

# Strategy for generating random strings that are unlikely to be valid URLs
random_string_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " !@#$%^&*()[]{}",
    min_size=1,
    max_size=100,
).filter(lambda x: not x.startswith("http://") and not x.startswith("https://"))

# Strategy for generating unsupported but valid URLs
# Note: Direct video URLs (.mp4, .webm, etc.) ARE supported, so we exclude them
unsupported_url_strategy = st.sampled_from([
    "https://example.com/page",
    "https://randomsite.org/watch?v=123",
    "https://notsupported.net/video/456",
    "https://unknown-platform.io/content/789",
    "https://somesite.com/stream",
])


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestInvalidUrlErrorHandling:
    """
    Property 12: Invalid URL Error Handling

    For any invalid or unsupported URL provided to the Video_Downloader,
    it SHALL return an error result (not raise an unhandled exception)
    with a descriptive message.

    **Validates: Requirements 1.2**
    """

    @given(invalid_url_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_invalid_urls_return_error_result_not_exception(self, url: str):
        """
        Feature: farmer-cli-completion, Property 12: Invalid URL Error Handling
        Validates: Requirements 1.2

        For any invalid URL, is_valid_url SHALL return an error result
        (not raise an unhandled exception) with a descriptive message.
        """
        # This should never raise an exception
        result = is_valid_url(url)

        # Result should be a tuple-like with is_valid and error
        assert hasattr(result, "is_valid"), "Result must have is_valid attribute"
        assert hasattr(result, "error"), "Result must have error attribute"

        # For invalid URLs, is_valid should be False
        assert result.is_valid is False, f"Invalid URL '{url}' should not be valid"

        # Error message should be descriptive (non-empty string)
        assert result.error is not None, "Error message should not be None for invalid URL"
        assert isinstance(result.error, str), "Error message should be a string"
        assert len(result.error) > 0, "Error message should not be empty"

    @given(random_string_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_random_strings_return_error_result_not_exception(self, text: str):
        """
        Feature: farmer-cli-completion, Property 12: Invalid URL Error Handling
        Validates: Requirements 1.2

        For any random string that is not a valid URL, is_valid_url SHALL
        return an error result (not raise an unhandled exception).
        """
        # This should never raise an exception
        result = is_valid_url(text)

        # Result should always have the expected structure
        assert hasattr(result, "is_valid"), "Result must have is_valid attribute"
        assert hasattr(result, "error"), "Result must have error attribute"

        # If invalid, error should be descriptive
        if not result.is_valid:
            assert result.error is not None, "Error message should not be None"
            assert len(result.error) > 0, "Error message should not be empty"

    @given(unsupported_url_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_unsupported_platform_urls_handled_gracefully(self, url: str):
        """
        Feature: farmer-cli-completion, Property 12: Invalid URL Error Handling
        Validates: Requirements 1.2

        For any URL from an unsupported platform, is_supported_platform SHALL
        return (False, None) without raising an exception.
        """
        # This should never raise an exception
        is_supported, platform = is_supported_platform(url)

        # Should return a tuple
        assert isinstance(is_supported, bool), "is_supported should be a boolean"

        # For unsupported platforms, should return False
        assert is_supported is False, f"URL '{url}' should not be from a supported platform"
        assert platform is None, "Platform should be None for unsupported URLs"

    @given(invalid_url_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_extract_video_id_returns_error_for_invalid_urls(self, url: str):
        """
        Feature: farmer-cli-completion, Property 12: Invalid URL Error Handling
        Validates: Requirements 1.2

        For any invalid URL, extract_video_id SHALL return an error result
        (not raise an unhandled exception) with a descriptive message.
        """
        # This should never raise an exception
        result = extract_video_id(url)

        # Result should have expected structure
        assert hasattr(result, "success"), "Result must have success attribute"
        assert hasattr(result, "error"), "Result must have error attribute"
        assert hasattr(result, "platform"), "Result must have platform attribute"
        assert hasattr(result, "video_id"), "Result must have video_id attribute"

        # For invalid URLs, success should be False
        assert result.success is False, f"Invalid URL '{url}' should not succeed"

        # Error message should be descriptive
        assert result.error is not None, "Error message should not be None"
        assert isinstance(result.error, str), "Error message should be a string"
        assert len(result.error) > 0, "Error message should not be empty"

    @given(st.none() | st.integers() | st.floats() | st.lists(st.text()))
    @settings(max_examples=50)
    @pytest.mark.property
    def test_non_string_inputs_handled_gracefully(self, value):
        """
        Feature: farmer-cli-completion, Property 12: Invalid URL Error Handling
        Validates: Requirements 1.2

        For any non-string input, is_valid_url SHALL return an error result
        (not raise an unhandled exception).
        """
        # This should never raise an exception
        result = is_valid_url(value)

        # Result should have expected structure
        assert hasattr(result, "is_valid"), "Result must have is_valid attribute"
        assert hasattr(result, "error"), "Result must have error attribute"

        # Non-string inputs should be invalid
        assert result.is_valid is False, "Non-string input should not be valid"
        assert result.error is not None, "Error message should not be None"
