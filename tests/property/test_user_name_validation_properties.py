"""
Property-based tests for user name validation.

Feature: farmer-cli-completion
Property 16: User Name Validation
Validates: Requirements 7.1

For any string provided as a user name, the validation SHALL correctly
accept non-empty strings ≤255 characters and reject empty strings or
those exceeding the limit.
"""

import string

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from farmer_cli.models.user import User


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid user names (non-empty, ≤255 characters)
valid_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " -_.",
    min_size=1,
    max_size=255,
).filter(lambda x: x.strip())  # Ensure non-empty after strip

# Strategy for generating names that are too long (>255 characters)
too_long_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=256,
    max_size=500,
)

# Strategy for generating empty or whitespace-only names
empty_name_strategy = st.one_of(
    st.just(""),
    st.text(alphabet=" \t\n\r", min_size=1, max_size=10),
)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestUserNameValidation:
    """
    Property 16: User Name Validation

    For any string provided as a user name, the validation SHALL correctly
    accept non-empty strings ≤255 characters and reject empty strings or
    those exceeding the limit.

    **Validates: Requirements 7.1**
    """

    @given(valid_name_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_valid_names_are_accepted(self, name: str):
        """
        Feature: farmer-cli-completion, Property 16: User Name Validation
        Validates: Requirements 7.1

        For any non-empty string ≤255 characters, the User model SHALL
        accept it as a valid name.
        """
        # Create a user with the valid name - should not raise
        user = User(name=name)

        # The name should be stored (possibly stripped)
        assert user.name is not None
        assert len(user.name) > 0
        assert len(user.name) <= 255

    @given(too_long_name_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_names_exceeding_255_chars_are_rejected(self, name: str):
        """
        Feature: farmer-cli-completion, Property 16: User Name Validation
        Validates: Requirements 7.1

        For any string exceeding 255 characters, the User model SHALL
        reject it with a ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            User(name=name)

        assert "255" in str(exc_info.value) or "exceed" in str(exc_info.value).lower()

    @given(empty_name_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_empty_names_are_rejected(self, name: str):
        """
        Feature: farmer-cli-completion, Property 16: User Name Validation
        Validates: Requirements 7.1

        For any empty or whitespace-only string, the User model SHALL
        reject it with a ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            User(name=name)

        assert "empty" in str(exc_info.value).lower()

    @given(valid_name_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_names_are_stripped(self, name: str):
        """
        Feature: farmer-cli-completion, Property 16: User Name Validation
        Validates: Requirements 7.1

        For any valid name with leading/trailing whitespace, the User model
        SHALL strip the whitespace.
        """
        # Add whitespace around the name
        padded_name = f"  {name}  "

        # Only test if padded name is still ≤255 chars
        if len(padded_name) <= 255:
            user = User(name=padded_name)
            # The name should be stripped
            assert user.name == name.strip()

    @given(st.text(min_size=1, max_size=255))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_validation_never_raises_unexpected_exception(self, name: str):
        """
        Feature: farmer-cli-completion, Property 16: User Name Validation
        Validates: Requirements 7.1

        For any input string, the validation SHALL either accept the name
        or raise a ValueError, never an unexpected exception type.
        """
        try:
            user = User(name=name)
            # If we get here, the name was accepted
            assert user.name is not None
        except ValueError:
            # Expected for invalid names
            pass
        except Exception as e:
            # Unexpected exception type
            pytest.fail(f"Unexpected exception type: {type(e).__name__}: {e}")

    @given(st.integers(min_value=1, max_value=255))
    @settings(max_examples=50)
    @pytest.mark.property
    def test_names_at_boundary_lengths_are_accepted(self, length: int):
        """
        Feature: farmer-cli-completion, Property 16: User Name Validation
        Validates: Requirements 7.1

        For any name with length between 1 and 255 characters, the User
        model SHALL accept it.
        """
        name = "a" * length
        user = User(name=name)
        assert len(user.name) == length

    @pytest.mark.property
    def test_name_at_exact_255_chars_is_accepted(self):
        """
        Feature: farmer-cli-completion, Property 16: User Name Validation
        Validates: Requirements 7.1

        A name with exactly 255 characters SHALL be accepted.
        """
        name = "a" * 255
        user = User(name=name)
        assert len(user.name) == 255

    @pytest.mark.property
    def test_name_at_256_chars_is_rejected(self):
        """
        Feature: farmer-cli-completion, Property 16: User Name Validation
        Validates: Requirements 7.1

        A name with exactly 256 characters SHALL be rejected.
        """
        name = "a" * 256
        with pytest.raises(ValueError):
            User(name=name)
