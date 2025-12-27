"""
Property-based tests for preference value validation.

Feature: farmer-cli-completion
Property 17: Preference Value Validation
Validates: Requirements 8.4

For any preference key-value pair, the validation SHALL correctly accept
values of the expected type and reject invalid types or out-of-range values.
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from farmer_cli.services.preferences import (
    PreferencesService,
    PreferenceSchema,
    PREFERENCE_SCHEMAS,
)


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for valid string values
valid_string_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

# Strategy for valid boolean values
valid_bool_strategy = st.booleans()

# Strategy for valid integer values (general)
valid_int_strategy = st.integers(min_value=-1000, max_value=1000)

# Strategy for invalid types (wrong type for any preference)
invalid_type_for_string = st.one_of(
    st.integers(),
    st.lists(st.integers(), max_size=3),
    st.dictionaries(st.text(max_size=5), st.integers(), max_size=3),
)

invalid_type_for_bool = st.one_of(
    st.text(min_size=1, max_size=10),
    st.integers(),
    st.lists(st.integers(), max_size=3),
)

invalid_type_for_int = st.one_of(
    st.text(min_size=1, max_size=10),
    st.booleans(),
    st.lists(st.integers(), max_size=3),
)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestPreferenceValueValidation:
    """
    Property 17: Preference Value Validation

    For any preference key-value pair, the validation SHALL correctly accept
    values of the expected type and reject invalid types or out-of-range values.

    **Validates: Requirements 8.4**
    """

    @given(valid_string_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_string_preferences_accept_valid_strings(self, value: str):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any valid string, string-type preferences SHALL accept it.
        """
        service = PreferencesService()

        # Test theme preference (string type, no restrictions)
        is_valid, error_msg = service.validate_preference("theme", value)
        assert is_valid, f"Valid string '{value}' rejected for theme: {error_msg}"

    @given(valid_bool_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_boolean_preferences_accept_valid_booleans(self, value: bool):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any boolean value, boolean-type preferences SHALL accept it.
        """
        service = PreferencesService()

        # Test boolean preferences
        for key in ["first_run", "check_updates", "show_tips", "prefer_audio_only"]:
            is_valid, error_msg = service.validate_preference(key, value)
            assert is_valid, f"Valid bool {value} rejected for {key}: {error_msg}"

    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_max_concurrent_downloads_accepts_valid_range(self, value: int):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any integer in range [1, 5], max_concurrent_downloads SHALL accept it.
        """
        service = PreferencesService()

        is_valid, error_msg = service.validate_preference(
            "max_concurrent_downloads", value
        )
        assert is_valid, f"Valid int {value} rejected: {error_msg}"

    @given(st.integers().filter(lambda x: x < 1 or x > 5))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_max_concurrent_downloads_rejects_out_of_range(self, value: int):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any integer outside range [1, 5], max_concurrent_downloads SHALL reject it.
        """
        service = PreferencesService()

        is_valid, error_msg = service.validate_preference(
            "max_concurrent_downloads", value
        )
        assert not is_valid, f"Out-of-range int {value} was accepted"
        assert error_msg, "Error message should be provided"

    @given(st.sampled_from(["csv", "json", "pdf"]))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_export_format_accepts_allowed_values(self, value: str):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any value in allowed list, export_format SHALL accept it.
        """
        service = PreferencesService()

        is_valid, error_msg = service.validate_preference("export_format", value)
        assert is_valid, f"Allowed value '{value}' rejected: {error_msg}"

    @given(st.text(min_size=1, max_size=20).filter(
        lambda x: x not in ["csv", "json", "pdf"]
    ))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_export_format_rejects_disallowed_values(self, value: str):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any value not in allowed list, export_format SHALL reject it.
        """
        service = PreferencesService()

        is_valid, error_msg = service.validate_preference("export_format", value)
        assert not is_valid, f"Disallowed value '{value}' was accepted"
        assert "not in allowed values" in error_msg

    @given(st.sampled_from(["rename", "overwrite", "skip"]))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_conflict_resolution_accepts_allowed_values(self, value: str):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any value in allowed list, conflict_resolution SHALL accept it.
        """
        service = PreferencesService()

        is_valid, error_msg = service.validate_preference("conflict_resolution", value)
        assert is_valid, f"Allowed value '{value}' rejected: {error_msg}"

    @given(st.sampled_from(["none", "channel", "playlist", "date"]))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_subdirectory_organization_accepts_allowed_values(self, value: str):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any value in allowed list, subdirectory_organization SHALL accept it.
        """
        service = PreferencesService()

        is_valid, error_msg = service.validate_preference(
            "subdirectory_organization", value
        )
        assert is_valid, f"Allowed value '{value}' rejected: {error_msg}"

    @given(invalid_type_for_bool)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_boolean_preferences_reject_wrong_types(self, value):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any non-boolean value, boolean-type preferences SHALL reject it.
        """
        service = PreferencesService()

        for key in ["first_run", "check_updates", "show_tips", "prefer_audio_only"]:
            is_valid, error_msg = service.validate_preference(key, value)
            assert not is_valid, f"Wrong type {type(value)} accepted for {key}"
            assert "Expected type" in error_msg

    @given(invalid_type_for_int)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_integer_preferences_reject_wrong_types(self, value):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any non-integer value, integer-type preferences SHALL reject it.
        """
        service = PreferencesService()

        is_valid, error_msg = service.validate_preference(
            "max_concurrent_downloads", value
        )
        assert not is_valid, f"Wrong type {type(value)} accepted"
        assert "Expected type" in error_msg

    @given(invalid_type_for_string)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_string_preferences_reject_wrong_types(self, value):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any non-string value, string-type preferences SHALL reject it.
        """
        service = PreferencesService()

        is_valid, error_msg = service.validate_preference("theme", value)
        assert not is_valid, f"Wrong type {type(value)} accepted for theme"
        assert "Expected type" in error_msg

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_unknown_keys_are_accepted(self, key: str):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For any unknown preference key, validation SHALL accept any value
        (to allow extensibility).
        """
        assume(key not in PREFERENCE_SCHEMAS)

        service = PreferencesService()

        # Unknown keys should be accepted with any value
        is_valid, error_msg = service.validate_preference(key, "any_value")
        assert is_valid, f"Unknown key '{key}' was rejected"

    @pytest.mark.property
    def test_all_schemas_have_valid_defaults(self):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        For all defined preference schemas, the default value SHALL pass validation.
        """
        service = PreferencesService()

        for key, schema in PREFERENCE_SCHEMAS.items():
            is_valid, error_msg = service.validate_preference(key, schema.default)
            assert is_valid, (
                f"Default value {schema.default} for '{key}' failed validation: "
                f"{error_msg}"
            )

    @pytest.mark.property
    def test_validate_all_returns_correct_structure(self):
        """
        Feature: farmer-cli-completion, Property 17: Preference Value Validation
        Validates: Requirements 8.4

        validate_all() SHALL return a tuple of (bool, dict) with correct structure.
        """
        service = PreferencesService()

        # Valid preferences
        valid_prefs = {"theme": "dark", "first_run": False}
        all_valid, errors = service.validate_all(valid_prefs)
        assert isinstance(all_valid, bool)
        assert isinstance(errors, dict)
        assert all_valid is True
        assert len(errors) == 0

        # Invalid preferences
        invalid_prefs = {"theme": 123, "max_concurrent_downloads": 100}
        all_valid, errors = service.validate_all(invalid_prefs)
        assert all_valid is False
        assert len(errors) == 2
        assert "theme" in errors
        assert "max_concurrent_downloads" in errors
