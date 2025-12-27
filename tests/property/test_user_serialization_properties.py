"""
Property-based tests for user serialization round-trip.

Feature: farmer-cli-completion
Property 1: User Serialization Round-Trip
Validates: Requirements 7.6

For any valid User object, serializing to JSON then deserializing SHALL
produce an equivalent User object with identical name and preferences.
"""

import json
import string

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from farmer_cli.models.user import User


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid user names
valid_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " -_.",
    min_size=1,
    max_size=100,
).filter(lambda x: x.strip())

# Strategy for generating valid preference values
preference_value_strategy = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none(),
)

# Strategy for generating valid preference keys
preference_key_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=30,
)

# Strategy for generating valid preferences dictionaries
preferences_strategy = st.dictionaries(
    keys=preference_key_strategy,
    values=preference_value_strategy,
    min_size=0,
    max_size=10,
)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def serialize_user(user: User) -> dict:
    """
    Serialize a User object to a dictionary.

    Args:
        user: User object to serialize

    Returns:
        Dictionary representation of the user
    """
    return {
        "name": user.name,
        "preferences": user.preferences_dict,
    }


def deserialize_user(data: dict) -> User:
    """
    Deserialize a dictionary to a User object.

    Args:
        data: Dictionary containing user data

    Returns:
        User object
    """
    return User(
        name=data["name"],
        preferences=json.dumps(data["preferences"]),
    )


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestUserSerializationRoundTrip:
    """
    Property 1: User Serialization Round-Trip

    For any valid User object, serializing to JSON then deserializing SHALL
    produce an equivalent User object with identical name and preferences.

    **Validates: Requirements 7.6**
    """

    @given(valid_name_strategy, preferences_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_user_roundtrip_preserves_name(self, name: str, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 1: User Serialization Round-Trip
        Validates: Requirements 7.6

        For any valid User, serializing then deserializing SHALL preserve
        the user's name.
        """
        # Create original user
        original = User(name=name, preferences=json.dumps(preferences))

        # Serialize to dict
        serialized = serialize_user(original)

        # Deserialize back to User
        restored = deserialize_user(serialized)

        # Name should be identical
        assert restored.name == original.name

    @given(valid_name_strategy, preferences_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_user_roundtrip_preserves_preferences(self, name: str, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 1: User Serialization Round-Trip
        Validates: Requirements 7.6

        For any valid User, serializing then deserializing SHALL preserve
        the user's preferences.
        """
        # Create original user
        original = User(name=name, preferences=json.dumps(preferences))

        # Serialize to dict
        serialized = serialize_user(original)

        # Deserialize back to User
        restored = deserialize_user(serialized)

        # Preferences should be equivalent
        assert restored.preferences_dict == original.preferences_dict

    @given(valid_name_strategy, preferences_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_user_json_roundtrip(self, name: str, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 1: User Serialization Round-Trip
        Validates: Requirements 7.6

        For any valid User, converting to JSON string and back SHALL
        produce an equivalent User.
        """
        # Create original user
        original = User(name=name, preferences=json.dumps(preferences))

        # Serialize to JSON string
        json_str = json.dumps(serialize_user(original))

        # Deserialize from JSON string
        data = json.loads(json_str)
        restored = deserialize_user(data)

        # Should be equivalent
        assert restored.name == original.name
        assert restored.preferences_dict == original.preferences_dict

    @given(valid_name_strategy, preferences_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_double_roundtrip_is_idempotent(self, name: str, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 1: User Serialization Round-Trip
        Validates: Requirements 7.6

        For any valid User, performing the roundtrip twice SHALL produce
        the same result as performing it once.
        """
        # Create original user
        original = User(name=name, preferences=json.dumps(preferences))

        # First roundtrip
        serialized1 = serialize_user(original)
        restored1 = deserialize_user(serialized1)

        # Second roundtrip
        serialized2 = serialize_user(restored1)
        restored2 = deserialize_user(serialized2)

        # Both restored users should be equivalent
        assert restored1.name == restored2.name
        assert restored1.preferences_dict == restored2.preferences_dict

    @given(valid_name_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_empty_preferences_roundtrip(self, name: str):
        """
        Feature: farmer-cli-completion, Property 1: User Serialization Round-Trip
        Validates: Requirements 7.6

        For any valid User with empty preferences, serializing then
        deserializing SHALL preserve the empty preferences.
        """
        # Create user with empty preferences
        original = User(name=name, preferences="{}")

        # Serialize and deserialize
        serialized = serialize_user(original)
        restored = deserialize_user(serialized)

        # Preferences should be empty dict
        assert restored.preferences_dict == {}
        assert restored.name == original.name

    @given(valid_name_strategy, st.lists(
        st.tuples(preference_key_strategy, preference_value_strategy),
        min_size=1,
        max_size=5,
    ))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_preferences_dict_setter_roundtrip(self, name: str, pref_items: list):
        """
        Feature: farmer-cli-completion, Property 1: User Serialization Round-Trip
        Validates: Requirements 7.6

        For any valid preferences set via preferences_dict setter,
        the getter SHALL return equivalent values.
        """
        # Create user
        user = User(name=name)

        # Set preferences via dict setter
        prefs = dict(pref_items)
        user.preferences_dict = prefs

        # Get preferences via dict getter
        retrieved = user.preferences_dict

        # Should be equivalent
        assert retrieved == prefs

    @given(valid_name_strategy, preference_key_strategy, preference_value_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_single_preference_roundtrip(self, name: str, key: str, value):
        """
        Feature: farmer-cli-completion, Property 1: User Serialization Round-Trip
        Validates: Requirements 7.6

        For any single preference set via set_preference(), get_preference()
        SHALL return the same value.
        """
        # Create user
        user = User(name=name)

        # Set single preference
        user.set_preference(key, value)

        # Get single preference
        retrieved = user.get_preference(key)

        # Should be equivalent
        assert retrieved == value

    @given(valid_name_strategy, preferences_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_serialization_produces_valid_json(self, name: str, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 1: User Serialization Round-Trip
        Validates: Requirements 7.6

        For any valid User, serialization SHALL produce valid JSON.
        """
        # Create user
        user = User(name=name, preferences=json.dumps(preferences))

        # Serialize
        serialized = serialize_user(user)

        # Should be JSON-serializable without error
        json_str = json.dumps(serialized)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Should be parseable back
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "name" in parsed
        assert "preferences" in parsed
