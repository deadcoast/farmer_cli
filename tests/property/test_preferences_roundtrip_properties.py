"""
Property-based tests for preferences round-trip.

Feature: farmer-cli-completion
Property 2: Preferences Round-Trip
Validates: Requirements 8.6

For any valid preferences dictionary, saving to file then loading SHALL
produce an equivalent dictionary with all key-value pairs preserved.
"""

import tempfile
import string
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from farmer_cli.services.preferences import PreferencesService


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for valid preference keys (alphanumeric with underscores)
preference_key_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=30,
)

# Strategy for JSON-serializable preference values
preference_value_strategy = st.one_of(
    st.text(min_size=0, max_size=100),
    st.integers(min_value=-1000000, max_value=1000000),
    st.booleans(),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.none(),
)

# Strategy for valid preferences dictionaries
preferences_dict_strategy = st.dictionaries(
    keys=preference_key_strategy,
    values=preference_value_strategy,
    min_size=0,
    max_size=20,
)

# Strategy for nested preferences (one level deep)
nested_value_strategy = st.one_of(
    preference_value_strategy,
    st.dictionaries(
        keys=preference_key_strategy,
        values=preference_value_strategy,
        min_size=0,
        max_size=5,
    ),
    st.lists(preference_value_strategy, min_size=0, max_size=5),
)

nested_preferences_strategy = st.dictionaries(
    keys=preference_key_strategy,
    values=nested_value_strategy,
    min_size=0,
    max_size=10,
)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestPreferencesRoundTrip:
    """
    Property 2: Preferences Round-Trip

    For any valid preferences dictionary, saving to file then loading SHALL
    produce an equivalent dictionary with all key-value pairs preserved.

    **Validates: Requirements 8.6**
    """

    @given(preferences_dict_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_save_then_load_preserves_preferences(self, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
        Validates: Requirements 8.6

        For any valid preferences dictionary, saving then loading SHALL
        produce an equivalent dictionary.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            service = PreferencesService(temp_path)

            # Save preferences
            service.save(preferences)

            # Clear cache to force reload from file
            service._cache = None

            # Load preferences
            loaded = service.load()

            # Should be equivalent
            assert loaded == preferences
        finally:
            temp_path.unlink(missing_ok=True)

    @given(preferences_dict_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_double_roundtrip_is_idempotent(self, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
        Validates: Requirements 8.6

        For any valid preferences, performing save/load twice SHALL produce
        the same result as performing it once.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            service = PreferencesService(temp_path)

            # First roundtrip
            service.save(preferences)
            service._cache = None
            loaded1 = service.load()

            # Second roundtrip
            service.save(loaded1)
            service._cache = None
            loaded2 = service.load()

            # Both should be equivalent
            assert loaded1 == loaded2
        finally:
            temp_path.unlink(missing_ok=True)

    @given(preference_key_strategy, preference_value_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_set_then_get_preserves_value(self, key: str, value):
        """
        Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
        Validates: Requirements 8.6

        For any key-value pair, set() then get() SHALL return the same value.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            service = PreferencesService(temp_path)

            # Set value (without validation for arbitrary keys)
            service.set(key, value, validate=False)

            # Clear cache to force reload
            service._cache = None

            # Get value
            retrieved = service.get(key)

            # Should be equivalent
            assert retrieved == value
        finally:
            temp_path.unlink(missing_ok=True)

    @given(preferences_dict_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_update_preserves_all_values(self, updates: dict):
        """
        Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
        Validates: Requirements 8.6

        For any updates dictionary, update() SHALL preserve all values.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            service = PreferencesService(temp_path)

            # Start with empty preferences
            service.save({})

            # Update with new values (without validation)
            service.update(updates, validate=False)

            # Clear cache
            service._cache = None

            # Load and verify
            loaded = service.load()

            # All updates should be present
            for key, value in updates.items():
                assert key in loaded
                assert loaded[key] == value
        finally:
            temp_path.unlink(missing_ok=True)

    @given(nested_preferences_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_nested_preferences_roundtrip(self, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
        Validates: Requirements 8.6

        For any nested preferences (dicts and lists), roundtrip SHALL
        preserve the structure.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            service = PreferencesService(temp_path)

            # Save nested preferences
            service.save(preferences)

            # Clear cache
            service._cache = None

            # Load and verify
            loaded = service.load()

            assert loaded == preferences
        finally:
            temp_path.unlink(missing_ok=True)

    @given(preferences_dict_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_cache_consistency(self, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
        Validates: Requirements 8.6

        After saving, the cache SHALL be consistent with the file.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            service = PreferencesService(temp_path)

            # Save preferences
            service.save(preferences)

            # Load from cache (should not read file)
            cached = service.load()

            # Clear cache and load from file
            service._cache = None
            from_file = service.load()

            # Both should be equivalent
            assert cached == from_file == preferences
        finally:
            temp_path.unlink(missing_ok=True)

    @pytest.mark.property
    def test_reset_restores_defaults(self):
        """
        Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
        Validates: Requirements 8.6

        reset() SHALL restore default preferences and persist them.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            service = PreferencesService(temp_path)

            # Save custom preferences
            service.save({"custom_key": "custom_value"})

            # Reset to defaults
            service.reset()

            # Clear cache and reload
            service._cache = None
            loaded = service.load()

            # Should have default keys
            assert "theme" in loaded
            assert "custom_key" not in loaded
        finally:
            temp_path.unlink(missing_ok=True)

    @given(st.lists(
        st.tuples(preference_key_strategy, preference_value_strategy),
        min_size=1,
        max_size=10,
    ))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_multiple_sets_preserve_all_values(self, key_value_pairs: list):
        """
        Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
        Validates: Requirements 8.6

        Multiple set() calls SHALL preserve all values.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            service = PreferencesService(temp_path)

            # Set multiple values
            expected = {}
            for key, value in key_value_pairs:
                service.set(key, value, validate=False)
                expected[key] = value

            # Clear cache and reload
            service._cache = None
            loaded = service.load()

            # All values should be present
            for key, value in expected.items():
                assert key in loaded
                assert loaded[key] == value
        finally:
            temp_path.unlink(missing_ok=True)

    @given(preferences_dict_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_file_not_exists_returns_defaults(self, _: dict):
        """
        Feature: farmer-cli-completion, Property 2: Preferences Round-Trip
        Validates: Requirements 8.6

        When file doesn't exist, load() SHALL return defaults.
        """
        # Use a path that doesn't exist
        temp_path = Path(tempfile.gettempdir()) / "nonexistent_prefs_12345.json"

        try:
            # Ensure file doesn't exist
            temp_path.unlink(missing_ok=True)

            service = PreferencesService(temp_path)
            loaded = service.load()

            # Should have default keys
            assert "theme" in loaded
            assert isinstance(loaded, dict)
        finally:
            temp_path.unlink(missing_ok=True)
