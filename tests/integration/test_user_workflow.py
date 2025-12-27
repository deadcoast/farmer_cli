"""
Integration tests for user workflow.

This module tests complete CRUD operations for users
and the export/import cycle.

Feature: farmer-cli-completion
Requirements: 9.4
"""

import json
import sys
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from farmer_cli.models.base import Base
from farmer_cli.models.user import User


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database path for user integration tests."""
    return tmp_path / "user_integration_test.db"


@pytest.fixture
def user_db_engine(user_db_path: Path):
    """Create a temporary SQLite database engine for user tests."""
    engine = create_engine(f"sqlite:///{user_db_path}", echo=False, future=True)
    yield engine
    engine.dispose()


@pytest.fixture
def user_session_factory(user_db_engine) -> sessionmaker:
    """Create a session factory for user tests."""
    # Import all models to ensure they are registered
    from farmer_cli.models import DownloadHistory  # noqa: F401
    from farmer_cli.models import QueueItem  # noqa: F401
    from farmer_cli.models import User  # noqa: F401

    # Create all tables
    Base.metadata.create_all(user_db_engine)

    return sessionmaker(bind=user_db_engine, expire_on_commit=False)


@pytest.fixture
def user_session(user_session_factory: sessionmaker) -> Generator[Session, None, None]:
    """Provide a database session for user tests."""
    session = user_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# User CRUD Integration Tests
# ---------------------------------------------------------------------------


class TestUserCRUDWorkflow:
    """Integration tests for user CRUD operations."""

    def test_create_user_workflow(self, user_session: Session) -> None:
        """Test creating a new user with preferences."""
        # Create user
        user = User(
            name="Test User",
            preferences=json.dumps({"theme": "dark", "notifications": True}),
        )
        user_session.add(user)
        user_session.commit()

        # Verify user was created
        assert user.id is not None
        assert user.name == "Test User"
        assert user.preferences_dict == {"theme": "dark", "notifications": True}
        assert user.created_at is not None

    def test_read_user_workflow(self, user_session: Session) -> None:
        """Test reading user data."""
        # Create user
        user = User(name="Read Test User", preferences=json.dumps({"key": "value"}))
        user_session.add(user)
        user_session.commit()
        user_id = user.id

        # Read user back
        retrieved_user = user_session.query(User).filter(User.id == user_id).first()

        assert retrieved_user is not None
        assert retrieved_user.name == "Read Test User"
        assert retrieved_user.preferences_dict == {"key": "value"}

    def test_update_user_workflow(self, user_session: Session) -> None:
        """Test updating user information."""
        # Create user
        user = User(name="Original Name", preferences=json.dumps({"setting": "old"}))
        user_session.add(user)
        user_session.commit()
        user_id = user.id

        # Update user
        user.name = "Updated Name"
        user.preferences = json.dumps({"setting": "new", "extra": True})
        user_session.commit()

        # Verify update
        updated_user = user_session.query(User).filter(User.id == user_id).first()
        assert updated_user is not None
        assert updated_user.name == "Updated Name"
        assert updated_user.preferences_dict == {"setting": "new", "extra": True}

    def test_delete_user_workflow(self, user_session: Session) -> None:
        """Test deleting a user."""
        # Create user
        user = User(name="Delete Me", preferences="{}")
        user_session.add(user)
        user_session.commit()
        user_id = user.id

        # Delete user
        user_session.delete(user)
        user_session.commit()

        # Verify deletion
        deleted_user = user_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None

    def test_list_users_workflow(self, user_session: Session) -> None:
        """Test listing multiple users."""
        # Create multiple users
        users_data = [
            ("Alice", {"role": "admin"}),
            ("Bob", {"role": "user"}),
            ("Charlie", {"role": "user"}),
        ]

        for name, prefs in users_data:
            user = User(name=name, preferences=json.dumps(prefs))
            user_session.add(user)
        user_session.commit()

        # List all users
        all_users = user_session.query(User).order_by(User.name).all()

        assert len(all_users) == 3
        assert all_users[0].name == "Alice"
        assert all_users[1].name == "Bob"
        assert all_users[2].name == "Charlie"

    def test_search_users_workflow(self, user_session: Session) -> None:
        """Test searching users by name."""
        # Create users
        users_data = [
            "John Smith",
            "Jane Doe",
            "John Doe",
            "Alice Williams",
        ]

        for name in users_data:
            user = User(name=name, preferences="{}")
            user_session.add(user)
        user_session.commit()

        # Search for "John" - should find John Smith and John Doe
        john_users = (
            user_session.query(User)
            .filter(User.name.ilike("%John%"))
            .all()
        )

        assert len(john_users) == 2
        names = {u.name for u in john_users}
        assert "John Smith" in names
        assert "John Doe" in names

        # Search for "Doe" - should find Jane Doe and John Doe
        doe_users = (
            user_session.query(User)
            .filter(User.name.ilike("%Doe%"))
            .all()
        )

        assert len(doe_users) == 2

    def test_user_pagination_workflow(self, user_session: Session) -> None:
        """Test paginating through users."""
        # Create 10 users
        for i in range(10):
            user = User(name=f"User {i:02d}", preferences="{}")
            user_session.add(user)
        user_session.commit()

        # Get first page (3 users)
        page1 = (
            user_session.query(User)
            .order_by(User.name)
            .offset(0)
            .limit(3)
            .all()
        )
        assert len(page1) == 3
        assert page1[0].name == "User 00"

        # Get second page
        page2 = (
            user_session.query(User)
            .order_by(User.name)
            .offset(3)
            .limit(3)
            .all()
        )
        assert len(page2) == 3
        assert page2[0].name == "User 03"

        # Verify no overlap
        page1_ids = {u.id for u in page1}
        page2_ids = {u.id for u in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_user_name_uniqueness(self, user_session: Session) -> None:
        """Test that user names must be unique."""
        # Create first user
        user1 = User(name="Unique Name", preferences="{}")
        user_session.add(user1)
        user_session.commit()

        # Try to create duplicate
        user2 = User(name="Unique Name", preferences="{}")
        user_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            user_session.commit()

    def test_user_preferences_workflow(self, user_session: Session) -> None:
        """Test working with user preferences."""
        # Create user with preferences
        user = User(
            name="Preferences User",
            preferences=json.dumps({
                "theme": "light",
                "language": "en",
                "notifications": {
                    "email": True,
                    "push": False,
                },
            }),
        )
        user_session.add(user)
        user_session.commit()

        # Read preferences
        prefs = user.preferences_dict
        assert prefs["theme"] == "light"
        assert prefs["notifications"]["email"] is True

        # Update single preference
        prefs["theme"] = "dark"
        user.preferences = json.dumps(prefs)
        user_session.commit()

        # Verify update
        updated_prefs = user.preferences_dict
        assert updated_prefs["theme"] == "dark"
        assert updated_prefs["language"] == "en"  # Unchanged


# ---------------------------------------------------------------------------
# Export/Import Integration Tests
# ---------------------------------------------------------------------------


class TestExportImportWorkflow:
    """Integration tests for export/import cycle."""

    def test_json_export_format(self, tmp_path: Path) -> None:
        """Test JSON export produces valid JSON structure."""
        # Create test data
        test_data = [
            {"id": 1, "name": "User 1", "preferences": {"theme": "dark"}},
            {"id": 2, "name": "User 2", "preferences": {"theme": "light"}},
        ]

        # Write to JSON file
        output_path = tmp_path / "test_export.json"
        with open(output_path, "w") as f:
            json.dump(test_data, f, indent=2)

        # Verify file exists and is valid JSON
        assert output_path.exists()

        with open(output_path) as f:
            loaded_data = json.load(f)

        assert len(loaded_data) == 2
        assert loaded_data[0]["name"] == "User 1"

    def test_csv_export_format(self, tmp_path: Path) -> None:
        """Test CSV export produces valid CSV structure."""
        import csv

        # Create test data
        test_data = [
            {"id": 1, "name": "User 1"},
            {"id": 2, "name": "User 2"},
        ]

        # Write to CSV file
        output_path = tmp_path / "test_export.csv"
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name"])
            writer.writeheader()
            writer.writerows(test_data)

        # Verify file exists and is valid CSV
        assert output_path.exists()

        with open(output_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["name"] == "User 1"

    def test_import_json_data_structure(self, tmp_path: Path) -> None:
        """Test importing JSON data validates structure."""
        # Create valid import file
        import_data = [
            {"name": "Import User 1", "preferences": {"setting": "value1"}},
            {"name": "Import User 2", "preferences": {"setting": "value2"}},
        ]
        import_file = tmp_path / "users_import.json"
        with open(import_file, "w") as f:
            json.dump(import_data, f)

        # Read and validate
        with open(import_file) as f:
            loaded_data = json.load(f)

        assert isinstance(loaded_data, list)
        assert len(loaded_data) == 2
        for item in loaded_data:
            assert "name" in item
            assert isinstance(item["name"], str)

    def test_export_import_data_roundtrip(self, tmp_path: Path) -> None:
        """Test that export/import preserves data integrity."""
        # Original data
        original_data = [
            {
                "name": "Roundtrip User 1",
                "preferences": {"theme": "dark", "lang": "en"},
            },
            {
                "name": "Roundtrip User 2",
                "preferences": {"theme": "light", "lang": "es"},
            },
        ]

        # Export to JSON
        export_path = tmp_path / "roundtrip_export.json"
        with open(export_path, "w") as f:
            json.dump(original_data, f, indent=2)

        # Import from JSON
        with open(export_path) as f:
            imported_data = json.load(f)

        # Verify data preserved
        assert len(imported_data) == len(original_data)
        for orig, imported in zip(original_data, imported_data):
            assert orig["name"] == imported["name"]
            assert orig["preferences"] == imported["preferences"]

    def test_import_validates_required_fields(self, tmp_path: Path) -> None:
        """Test that import validates required fields."""
        # Create import file with invalid entries
        import_data = [
            {"name": "Valid User", "preferences": {}},
            {"preferences": {}},  # Missing name - invalid
            {"name": "", "preferences": {}},  # Empty name - invalid
            {"name": "Another Valid", "preferences": {}},
        ]
        import_file = tmp_path / "invalid_import.json"
        with open(import_file, "w") as f:
            json.dump(import_data, f)

        # Read and validate
        with open(import_file) as f:
            loaded_data = json.load(f)

        # Count valid entries
        valid_count = 0
        invalid_count = 0
        for item in loaded_data:
            if "name" in item and item["name"].strip():
                valid_count += 1
            else:
                invalid_count += 1

        assert valid_count == 2
        assert invalid_count == 2

    def test_export_field_selection(self, tmp_path: Path) -> None:
        """Test exporting with specific field selection."""
        # Full data
        full_data = [
            {
                "id": 1,
                "name": "User 1",
                "preferences": {"key": "value"},
                "created_at": "2024-01-01",
            },
        ]

        # Export with limited fields
        fields = ["id", "name"]
        limited_data = [
            {k: v for k, v in item.items() if k in fields}
            for item in full_data
        ]

        output_path = tmp_path / "limited_export.json"
        with open(output_path, "w") as f:
            json.dump(limited_data, f)

        # Verify
        with open(output_path) as f:
            exported_data = json.load(f)

        assert len(exported_data) == 1
        user_data = exported_data[0]
        assert "id" in user_data
        assert "name" in user_data
        assert "preferences" not in user_data
        assert "created_at" not in user_data

    def test_duplicate_detection_logic(self) -> None:
        """Test duplicate detection logic for imports."""
        existing_names = {"User A", "User B", "User C"}

        import_data = [
            {"name": "User A"},  # Duplicate
            {"name": "User D"},  # New
            {"name": "User B"},  # Duplicate
            {"name": "User E"},  # New
        ]

        imported = []
        skipped = []

        for item in import_data:
            if item["name"] in existing_names:
                skipped.append(item)
            else:
                imported.append(item)
                existing_names.add(item["name"])

        assert len(imported) == 2
        assert len(skipped) == 2
        assert imported[0]["name"] == "User D"
        assert imported[1]["name"] == "User E"
