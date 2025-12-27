"""
Unit tests for the user_manager feature module.

Tests cover:
- add_user validation
- update_user logic
- delete_user with confirmation
- pagination logic
- search_users() method
- _validate_json helper

Requirements: 9.1, 9.3
"""

import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from farmer_cli.features.user_manager import UserManagementFeature


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def feature():
    """Create a UserManagementFeature instance."""
    return UserManagementFeature()


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock()
    return session


@pytest.fixture
def mock_user():
    """Create a mock User object."""
    user = MagicMock()
    user.id = 1
    user.name = "Test User"
    user.preferences = '{"theme": "dark"}'
    user.preferences_dict = {"theme": "dark"}
    return user


# ---------------------------------------------------------------------------
# UserManagementFeature Initialization Tests
# ---------------------------------------------------------------------------


class TestUserManagementFeatureInit:
    """Tests for UserManagementFeature initialization."""

    def test_init_sets_name(self, feature):
        """Test that name is set correctly."""
        assert feature.name == "User Management"

    def test_init_sets_description(self, feature):
        """Test that description is set correctly."""
        assert "Manage users" in feature.description

    def test_init_creates_menu_manager(self, feature):
        """Test that menu manager is created."""
        assert feature.menu_manager is not None


# ---------------------------------------------------------------------------
# _validate_json Tests
# ---------------------------------------------------------------------------


class TestValidateJson:
    """Tests for _validate_json method."""

    def test_valid_empty_object(self, feature):
        """Test validation of empty JSON object."""
        assert feature._validate_json("{}") is True

    def test_valid_object_with_data(self, feature):
        """Test validation of JSON object with data."""
        assert feature._validate_json('{"key": "value"}') is True

    def test_valid_array(self, feature):
        """Test validation of JSON array."""
        assert feature._validate_json('[1, 2, 3]') is True

    def test_valid_nested_object(self, feature):
        """Test validation of nested JSON object."""
        assert feature._validate_json('{"outer": {"inner": "value"}}') is True

    def test_invalid_json(self, feature):
        """Test validation of invalid JSON."""
        assert feature._validate_json("not json") is False

    def test_invalid_missing_quotes(self, feature):
        """Test validation of JSON with missing quotes."""
        assert feature._validate_json("{key: value}") is False

    def test_invalid_trailing_comma(self, feature):
        """Test validation of JSON with trailing comma."""
        assert feature._validate_json('{"key": "value",}') is False

    def test_valid_null(self, feature):
        """Test validation of JSON null."""
        assert feature._validate_json("null") is True

    def test_valid_boolean(self, feature):
        """Test validation of JSON boolean."""
        assert feature._validate_json("true") is True
        assert feature._validate_json("false") is True

    def test_valid_number(self, feature):
        """Test validation of JSON number."""
        assert feature._validate_json("123") is True
        assert feature._validate_json("3.14") is True


# ---------------------------------------------------------------------------
# add_user Tests
# ---------------------------------------------------------------------------


class TestAddUser:
    """Tests for add_user method."""

    def test_add_user_empty_name_raises(self, feature):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            feature.add_user("")

    def test_add_user_whitespace_name_raises(self, feature):
        """Test that whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            feature.add_user("   ")

    def test_add_user_long_name_raises(self, feature):
        """Test that name exceeding 255 chars raises ValueError."""
        long_name = "A" * 256
        with pytest.raises(ValueError, match="cannot exceed 255"):
            feature.add_user(long_name)

    def test_add_user_duplicate_raises(self, feature, mock_session, mock_user):
        """Test that duplicate name raises ValueError."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            with pytest.raises(ValueError, match="already exists"):
                feature.add_user("Test User")

    def test_add_user_success(self, feature, mock_session):
        """Test successful user creation."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = feature.add_user("New User", {"theme": "light"})

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_add_user_strips_name(self, feature, mock_session):
        """Test that name is stripped of whitespace."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            feature.add_user("  New User  ")

            # Verify the User was created with stripped name
            add_call = mock_session.add.call_args
            user_arg = add_call[0][0]
            assert user_arg.name == "New User"

    def test_add_user_default_preferences(self, feature, mock_session):
        """Test that default preferences is empty dict."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            feature.add_user("New User")

            add_call = mock_session.add.call_args
            user_arg = add_call[0][0]
            assert user_arg.preferences == "{}"


# ---------------------------------------------------------------------------
# update_user Tests
# ---------------------------------------------------------------------------


class TestUpdateUser:
    """Tests for update_user method."""

    def test_update_user_not_found_raises(self, feature, mock_session):
        """Test that updating non-existent user raises ValueError."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            with pytest.raises(ValueError, match="not found"):
                feature.update_user(999)

    def test_update_user_empty_name_raises(self, feature, mock_session, mock_user):
        """Test that empty name raises ValueError."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            with pytest.raises(ValueError, match="cannot be empty"):
                feature.update_user(1, name="   ")

    def test_update_user_long_name_raises(self, feature, mock_session, mock_user):
        """Test that name exceeding 255 chars raises ValueError."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            long_name = "A" * 256
            with pytest.raises(ValueError, match="cannot exceed 255"):
                feature.update_user(1, name=long_name)

    def test_update_user_duplicate_name_raises(self, feature, mock_session, mock_user):
        """Test that duplicate name raises ValueError."""
        existing_user = MagicMock()
        existing_user.id = 2
        existing_user.name = "Existing User"

        def filter_side_effect(*args, **kwargs):
            result = MagicMock()
            if "id" in kwargs:
                result.first.return_value = mock_user
            else:
                result.first.return_value = existing_user
            return result

        mock_session.query.return_value.filter_by.side_effect = filter_side_effect
        mock_session.query.return_value.filter.return_value.first.return_value = existing_user

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            with pytest.raises(ValueError, match="already exists"):
                feature.update_user(1, name="Existing User")

    def test_update_user_name_success(self, feature, mock_session, mock_user):
        """Test successful name update."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            feature.update_user(1, name="Updated Name")

            assert mock_user.name == "Updated Name"
            mock_session.commit.assert_called_once()

    def test_update_user_preferences_success(self, feature, mock_session, mock_user):
        """Test successful preferences update."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            feature.update_user(1, preferences={"theme": "light"})

            assert mock_user.preferences == '{"theme": "light"}'
            mock_session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# delete_user Tests
# ---------------------------------------------------------------------------


class TestDeleteUser:
    """Tests for delete_user method."""

    def test_delete_user_not_found_raises(self, feature, mock_session):
        """Test that deleting non-existent user raises ValueError."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            with pytest.raises(ValueError, match="not found"):
                feature.delete_user(999)

    def test_delete_user_success(self, feature, mock_session, mock_user):
        """Test successful user deletion."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = feature.delete_user(1, confirm=False)

            assert result is True
            mock_session.delete.assert_called_once_with(mock_user)
            mock_session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# list_users Tests (Pagination)
# ---------------------------------------------------------------------------


class TestListUsers:
    """Tests for list_users method and pagination logic."""

    def test_list_users_empty(self, feature, mock_session):
        """Test listing when no users exist."""
        mock_session.query.return_value.count.return_value = 0
        mock_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            users, total, pages = feature.list_users()

            assert users == []
            assert total == 0
            assert pages == 1

    def test_list_users_single_page(self, feature, mock_session, mock_user):
        """Test listing with single page of results."""
        mock_session.query.return_value.count.return_value = 5
        mock_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_user] * 5

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            users, total, pages = feature.list_users(page_size=10)

            assert len(users) == 5
            assert total == 5
            assert pages == 1

    def test_list_users_multiple_pages(self, feature, mock_session, mock_user):
        """Test listing with multiple pages."""
        mock_session.query.return_value.count.return_value = 25
        mock_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_user] * 10

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            users, total, pages = feature.list_users(page=1, page_size=10)

            assert total == 25
            assert pages == 3

    def test_list_users_page_clamping_high(self, feature, mock_session, mock_user):
        """Test that page number is clamped to max."""
        mock_session.query.return_value.count.return_value = 25
        mock_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_user] * 5

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Request page 100 when only 3 pages exist
            users, total, pages = feature.list_users(page=100, page_size=10)

            assert pages == 3
            # Should return last page

    def test_list_users_page_clamping_low(self, feature, mock_session, mock_user):
        """Test that page number is clamped to min."""
        mock_session.query.return_value.count.return_value = 25
        mock_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_user] * 10

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Request page 0 or negative
            users, total, pages = feature.list_users(page=0, page_size=10)

            # Should return first page
            assert pages == 3


# ---------------------------------------------------------------------------
# search_users Tests
# ---------------------------------------------------------------------------


class TestSearchUsers:
    """Tests for search_users method."""

    def test_search_empty_query_returns_empty(self, feature):
        """Test that empty query returns empty list."""
        result = feature.search_users("")
        assert result == []

    def test_search_whitespace_query_returns_empty(self, feature):
        """Test that whitespace query returns empty list."""
        result = feature.search_users("   ")
        assert result == []

    def test_search_no_results(self, feature, mock_session):
        """Test search with no matching results."""
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = feature.search_users("nonexistent")

            assert result == []

    def test_search_with_results(self, feature, mock_session, mock_user):
        """Test search with matching results."""
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_user]

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = feature.search_users("Test")

            assert len(result) == 1
            assert result[0] == mock_user


# ---------------------------------------------------------------------------
# get_user Tests
# ---------------------------------------------------------------------------


class TestGetUser:
    """Tests for get_user method."""

    def test_get_user_found(self, feature, mock_session, mock_user):
        """Test getting existing user."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = feature.get_user(1)

            assert result == mock_user

    def test_get_user_not_found(self, feature, mock_session):
        """Test getting non-existent user."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("farmer_cli.features.user_manager.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = feature.get_user(999)

            assert result is None


# ---------------------------------------------------------------------------
# cleanup Tests
# ---------------------------------------------------------------------------


class TestCleanup:
    """Tests for cleanup method."""

    def test_cleanup_does_not_raise(self, feature):
        """Test that cleanup completes without error."""
        feature.cleanup()
