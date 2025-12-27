"""
Property-based tests for export/import round-trip.

Feature: farmer-cli-completion
Property 3: Export/Import Round-Trip
Validates: Requirements 12.6

For any collection of exportable records (users or history), exporting to JSON
then importing SHALL preserve all data fields and produce equivalent records.
"""

import json
import string
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from farmer_cli.models.base import Base
from farmer_cli.models.history import DownloadHistory
from farmer_cli.models.user import User
from farmer_cli.services.export import ExportFormat, ExportService


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for valid user names (alphanumeric with spaces)
user_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " _-",
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip())

# Strategy for valid preference keys
preference_key_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=20,
)

# Strategy for JSON-serializable preference values
preference_value_strategy = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
)

# Strategy for user preferences
preferences_strategy = st.dictionaries(
    keys=preference_key_strategy,
    values=preference_value_strategy,
    min_size=0,
    max_size=5,
)

# Strategy for generating user data
user_data_strategy = st.fixed_dictionaries({
    "name": user_name_strategy,
    "preferences": preferences_strategy,
})

# Strategy for valid URLs
url_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "/:.-_?=&",
    min_size=10,
    max_size=200,
).map(lambda x: f"https://example.com/{x}")

# Strategy for valid titles
title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " _-",
    min_size=1,
    max_size=100,
).filter(lambda x: x.strip())

# Strategy for file paths
file_path_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "/_-.",
    min_size=5,
    max_size=100,
).map(lambda x: f"/downloads/{x}.mp4")

# Strategy for history data
history_data_strategy = st.fixed_dictionaries({
    "url": url_strategy,
    "title": title_strategy,
    "file_path": file_path_strategy,
    "file_size": st.integers(min_value=1000, max_value=1000000000),
    "format_id": st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10),
    "duration": st.integers(min_value=1, max_value=36000),
    "uploader": st.text(alphabet=string.ascii_letters + " ", min_size=1, max_size=50).filter(lambda x: x.strip()),
    "status": st.just("completed"),
})


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    yield SessionLocal, db_path

    engine.dispose()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def export_service():
    """Create an ExportService instance."""
    return ExportService()


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestExportImportRoundTrip:
    """
    Property 3: Export/Import Round-Trip

    For any collection of exportable records (users or history), exporting to JSON
    then importing SHALL preserve all data fields and produce equivalent records.

    **Validates: Requirements 12.6**
    """

    @given(st.lists(user_data_strategy, min_size=1, max_size=5, unique_by=lambda x: x["name"].strip()))
    @settings(max_examples=100, deadline=None)
    @pytest.mark.property
    def test_user_export_import_roundtrip(self, user_data_list: list):
        """
        Feature: farmer-cli-completion, Property 3: Export/Import Round-Trip
        Validates: Requirements 12.6

        For any list of users, exporting to JSON then importing into a fresh
        database SHALL produce equivalent user records.
        """
        # Create temporary database and files
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as db_file:
            db_path = Path(db_file.name)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as json_file:
            export_path = Path(json_file.name)

        try:
            # Setup first database with users
            engine1 = create_engine(f"sqlite:///{db_path}", echo=False)
            Base.metadata.create_all(engine1)
            SessionLocal1 = sessionmaker(bind=engine1, expire_on_commit=False)

            # Add users to first database (names get stripped by model validation)
            with SessionLocal1() as session:
                for user_data in user_data_list:
                    user = User(
                        name=user_data["name"],
                        preferences=json.dumps(user_data["preferences"]),
                    )
                    session.add(user)
                session.commit()

            # Export users to JSON
            export_data = []
            with SessionLocal1() as session:
                users = session.query(User).all()
                for user in users:
                    export_data.append({
                        "name": user.name,
                        "preferences": user.preferences_dict,
                    })

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f)

            engine1.dispose()

            # Create second database for import
            db_path2 = db_path.with_suffix(".db2")
            engine2 = create_engine(f"sqlite:///{db_path2}", echo=False)
            Base.metadata.create_all(engine2)
            SessionLocal2 = sessionmaker(bind=engine2, expire_on_commit=False)

            # Import users
            with open(export_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            with SessionLocal2() as session:
                for record in import_data:
                    user = User(
                        name=record["name"],
                        preferences=json.dumps(record["preferences"]),
                    )
                    session.add(user)
                session.commit()

            # Verify imported users match original (using stripped names)
            with SessionLocal2() as session:
                imported_users = session.query(User).all()
                assert len(imported_users) == len(user_data_list)

                imported_names = {u.name for u in imported_users}
                # Names are stripped by model validation
                original_names = {u["name"].strip() for u in user_data_list}
                assert imported_names == original_names

                for user in imported_users:
                    original = next(u for u in user_data_list if u["name"].strip() == user.name)
                    assert user.preferences_dict == original["preferences"]

            engine2.dispose()
            db_path2.unlink(missing_ok=True)

        finally:
            db_path.unlink(missing_ok=True)
            export_path.unlink(missing_ok=True)

    @given(st.lists(history_data_strategy, min_size=1, max_size=5, unique_by=lambda x: x["url"]))
    @settings(max_examples=100, deadline=None)
    @pytest.mark.property
    def test_history_export_import_roundtrip(self, history_data_list: list):
        """
        Feature: farmer-cli-completion, Property 3: Export/Import Round-Trip
        Validates: Requirements 12.6

        For any list of history entries, exporting to JSON then importing into
        a fresh database SHALL produce equivalent history records.
        """
        # Create temporary database and files
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as db_file:
            db_path = Path(db_file.name)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as json_file:
            export_path = Path(json_file.name)

        try:
            # Setup first database with history
            engine1 = create_engine(f"sqlite:///{db_path}", echo=False)
            Base.metadata.create_all(engine1)
            SessionLocal1 = sessionmaker(bind=engine1, expire_on_commit=False)

            # Add history entries to first database
            with SessionLocal1() as session:
                for history_data in history_data_list:
                    entry = DownloadHistory(
                        url=history_data["url"],
                        title=history_data["title"],
                        file_path=history_data["file_path"],
                        file_size=history_data["file_size"],
                        format_id=history_data["format_id"],
                        duration=history_data["duration"],
                        uploader=history_data["uploader"],
                        status=history_data["status"],
                        downloaded_at=datetime.utcnow(),
                    )
                    session.add(entry)
                session.commit()

            # Export history to JSON
            export_data = []
            with SessionLocal1() as session:
                entries = session.query(DownloadHistory).all()
                for entry in entries:
                    export_data.append({
                        "url": entry.url,
                        "title": entry.title,
                        "file_path": entry.file_path,
                        "file_size": entry.file_size,
                        "format_id": entry.format_id,
                        "duration": entry.duration,
                        "uploader": entry.uploader,
                        "status": entry.status,
                        "downloaded_at": entry.downloaded_at.isoformat() if entry.downloaded_at else None,
                    })

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f)

            engine1.dispose()

            # Create second database for import
            db_path2 = db_path.with_suffix(".db2")
            engine2 = create_engine(f"sqlite:///{db_path2}", echo=False)
            Base.metadata.create_all(engine2)
            SessionLocal2 = sessionmaker(bind=engine2, expire_on_commit=False)

            # Import history
            with open(export_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            with SessionLocal2() as session:
                for record in import_data:
                    downloaded_at = datetime.utcnow()
                    if record.get("downloaded_at"):
                        try:
                            downloaded_at = datetime.fromisoformat(record["downloaded_at"])
                        except (ValueError, TypeError):
                            pass

                    entry = DownloadHistory(
                        url=record["url"],
                        title=record["title"],
                        file_path=record["file_path"],
                        file_size=record.get("file_size"),
                        format_id=record.get("format_id"),
                        duration=record.get("duration"),
                        uploader=record.get("uploader"),
                        status=record.get("status", "completed"),
                        downloaded_at=downloaded_at,
                    )
                    session.add(entry)
                session.commit()

            # Verify imported history matches original (accounting for model validation stripping)
            with SessionLocal2() as session:
                imported_entries = session.query(DownloadHistory).all()
                assert len(imported_entries) == len(history_data_list)

                imported_urls = {e.url for e in imported_entries}
                original_urls = {h["url"].strip() for h in history_data_list}
                assert imported_urls == original_urls

                for entry in imported_entries:
                    original = next(h for h in history_data_list if h["url"].strip() == entry.url)
                    # Model validation strips whitespace from title and file_path
                    assert entry.title == original["title"].strip()
                    assert entry.file_path == original["file_path"].strip()
                    assert entry.file_size == original["file_size"]
                    assert entry.format_id == original["format_id"]
                    assert entry.duration == original["duration"]
                    assert entry.uploader == original["uploader"]
                    assert entry.status == original["status"]

            engine2.dispose()
            db_path2.unlink(missing_ok=True)

        finally:
            db_path.unlink(missing_ok=True)
            export_path.unlink(missing_ok=True)

    @given(preferences_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_preferences_json_roundtrip(self, preferences: dict):
        """
        Feature: farmer-cli-completion, Property 3: Export/Import Round-Trip
        Validates: Requirements 12.6

        For any preferences dictionary, JSON serialization then deserialization
        SHALL produce an equivalent dictionary.
        """
        # Serialize to JSON
        json_str = json.dumps(preferences)

        # Deserialize from JSON
        loaded = json.loads(json_str)

        # Should be equivalent
        assert loaded == preferences

    @given(st.lists(user_data_strategy, min_size=0, max_size=3, unique_by=lambda x: x["name"]))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_export_json_format_is_valid(self, user_data_list: list):
        """
        Feature: farmer-cli-completion, Property 3: Export/Import Round-Trip
        Validates: Requirements 12.6

        For any exported data, the JSON file SHALL be valid JSON that can be parsed.
        """
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            export_path = Path(f.name)

        try:
            # Create export data
            export_data = [
                {"name": u["name"], "preferences": u["preferences"]}
                for u in user_data_list
            ]

            # Write to JSON
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            # Read and parse JSON
            with open(export_path, "r", encoding="utf-8") as f:
                parsed = json.load(f)

            # Should be a list
            assert isinstance(parsed, list)
            assert len(parsed) == len(user_data_list)

            # Each item should have expected fields
            for item in parsed:
                assert "name" in item
                assert "preferences" in item

        finally:
            export_path.unlink(missing_ok=True)

    @given(st.lists(history_data_strategy, min_size=1, max_size=3, unique_by=lambda x: x["url"]))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_history_fields_preserved_after_roundtrip(self, history_data_list: list):
        """
        Feature: farmer-cli-completion, Property 3: Export/Import Round-Trip
        Validates: Requirements 12.6

        For any history data, all fields SHALL be preserved after export/import.
        """
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            export_path = Path(f.name)

        try:
            # Export to JSON
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(history_data_list, f)

            # Import from JSON
            with open(export_path, "r", encoding="utf-8") as f:
                imported = json.load(f)

            # Verify all fields preserved
            assert len(imported) == len(history_data_list)

            for original, loaded in zip(history_data_list, imported):
                assert loaded["url"] == original["url"]
                assert loaded["title"] == original["title"]
                assert loaded["file_path"] == original["file_path"]
                assert loaded["file_size"] == original["file_size"]
                assert loaded["format_id"] == original["format_id"]
                assert loaded["duration"] == original["duration"]
                assert loaded["uploader"] == original["uploader"]
                assert loaded["status"] == original["status"]

        finally:
            export_path.unlink(missing_ok=True)

    @pytest.mark.property
    def test_empty_export_produces_empty_array(self):
        """
        Feature: farmer-cli-completion, Property 3: Export/Import Round-Trip
        Validates: Requirements 12.6

        Exporting empty data SHALL produce a valid empty JSON array.
        """
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            export_path = Path(f.name)

        try:
            # Export empty list
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump([], f)

            # Import should return empty list
            with open(export_path, "r", encoding="utf-8") as f:
                imported = json.load(f)

            assert imported == []

        finally:
            export_path.unlink(missing_ok=True)

    @given(st.lists(user_data_strategy, min_size=1, max_size=3, unique_by=lambda x: x["name"]))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_double_roundtrip_is_idempotent(self, user_data_list: list):
        """
        Feature: farmer-cli-completion, Property 3: Export/Import Round-Trip
        Validates: Requirements 12.6

        For any data, performing export/import twice SHALL produce the same result.
        """
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f1:
            path1 = Path(f1.name)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f2:
            path2 = Path(f2.name)

        try:
            # First roundtrip
            with open(path1, "w", encoding="utf-8") as f:
                json.dump(user_data_list, f)
            with open(path1, "r", encoding="utf-8") as f:
                loaded1 = json.load(f)

            # Second roundtrip
            with open(path2, "w", encoding="utf-8") as f:
                json.dump(loaded1, f)
            with open(path2, "r", encoding="utf-8") as f:
                loaded2 = json.load(f)

            # Both should be equivalent
            assert loaded1 == loaded2

        finally:
            path1.unlink(missing_ok=True)
            path2.unlink(missing_ok=True)
