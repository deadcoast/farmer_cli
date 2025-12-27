"""
Unit tests for the export.py service module.

Tests cover:
- CSV export formatting
- JSON export structure
- Field selection filtering
- PDF export (if implemented)
- export_history() method
- ExportResult and ImportResult dataclasses

Requirements: 9.1, 9.3
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from farmer_cli.exceptions import ExportError
from farmer_cli.exceptions import ValidationError
from farmer_cli.services.export import ExportFormat
from farmer_cli.services.export import ExportResult
from farmer_cli.services.export import ExportService
from farmer_cli.services.export import ImportResult


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def export_service():
    """Create an ExportService instance."""
    return ExportService()


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
    user.created_at = datetime(2024, 1, 15, 10, 30, 0)
    user.updated_at = datetime(2024, 1, 20, 14, 45, 0)
    return user


@pytest.fixture
def mock_history_entry():
    """Create a mock DownloadHistory object."""
    entry = MagicMock()
    entry.id = 1
    entry.url = "https://youtube.com/watch?v=test123"
    entry.title = "Test Video"
    entry.file_path = "/downloads/test_video.mp4"
    entry.file_size = 50_000_000
    entry.format_id = "22"
    entry.duration = 300
    entry.uploader = "Test Channel"
    entry.downloaded_at = datetime(2024, 1, 15, 10, 30, 0)
    entry.status = "completed"
    entry.file_exists = True
    entry.thumbnail_url = None
    entry.description = None
    return entry


# ---------------------------------------------------------------------------
# ExportResult Tests
# ---------------------------------------------------------------------------


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_file_size_formatted_bytes(self):
        """Test formatting bytes."""
        result = ExportResult(
            success=True,
            file_path=Path("/test.json"),
            file_size=500,
            record_count=10,
            format=ExportFormat.JSON,
            message="Success",
        )
        assert "B" in result.file_size_formatted

    def test_file_size_formatted_kb(self):
        """Test formatting kilobytes."""
        result = ExportResult(
            success=True,
            file_path=Path("/test.json"),
            file_size=2048,
            record_count=10,
            format=ExportFormat.JSON,
            message="Success",
        )
        assert "KB" in result.file_size_formatted

    def test_file_size_formatted_mb(self):
        """Test formatting megabytes."""
        result = ExportResult(
            success=True,
            file_path=Path("/test.json"),
            file_size=5 * 1024 * 1024,
            record_count=10,
            format=ExportFormat.JSON,
            message="Success",
        )
        assert "MB" in result.file_size_formatted

    def test_file_size_formatted_gb(self):
        """Test formatting gigabytes."""
        result = ExportResult(
            success=True,
            file_path=Path("/test.json"),
            file_size=2 * 1024 * 1024 * 1024,
            record_count=10,
            format=ExportFormat.JSON,
            message="Success",
        )
        assert "GB" in result.file_size_formatted


# ---------------------------------------------------------------------------
# ImportResult Tests
# ---------------------------------------------------------------------------


class TestImportResult:
    """Tests for ImportResult dataclass."""

    def test_import_result_success(self):
        """Test successful import result."""
        result = ImportResult(
            success=True,
            records_imported=10,
            records_skipped=2,
            errors=["Record 5: Duplicate"],
            message="Imported 10 records",
        )
        assert result.success is True
        assert result.records_imported == 10
        assert result.records_skipped == 2
        assert len(result.errors) == 1

    def test_import_result_failure(self):
        """Test failed import result."""
        result = ImportResult(
            success=False,
            records_imported=0,
            records_skipped=5,
            errors=["All records failed"],
            message="Import failed",
        )
        assert result.success is False
        assert result.records_imported == 0


# ---------------------------------------------------------------------------
# ExportFormat Tests
# ---------------------------------------------------------------------------


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_csv_format(self):
        """Test CSV format value."""
        assert ExportFormat.CSV.value == "csv"

    def test_json_format(self):
        """Test JSON format value."""
        assert ExportFormat.JSON.value == "json"

    def test_pdf_format(self):
        """Test PDF format value."""
        assert ExportFormat.PDF.value == "pdf"


# ---------------------------------------------------------------------------
# ExportService Initialization Tests
# ---------------------------------------------------------------------------


class TestExportServiceInit:
    """Tests for ExportService initialization."""

    def test_init_creates_logger(self, export_service):
        """Test that logger is created."""
        assert export_service._logger is not None

    def test_user_fields_defined(self, export_service):
        """Test that USER_FIELDS is defined."""
        assert len(export_service.USER_FIELDS) > 0
        assert "id" in export_service.USER_FIELDS
        assert "name" in export_service.USER_FIELDS

    def test_history_fields_defined(self, export_service):
        """Test that HISTORY_FIELDS is defined."""
        assert len(export_service.HISTORY_FIELDS) > 0
        assert "url" in export_service.HISTORY_FIELDS
        assert "title" in export_service.HISTORY_FIELDS


# ---------------------------------------------------------------------------
# _validate_fields Tests
# ---------------------------------------------------------------------------


class TestValidateFields:
    """Tests for _validate_fields method."""

    def test_valid_fields_pass(self, export_service):
        """Test that valid fields pass validation."""
        # Should not raise
        export_service._validate_fields(
            ["id", "name"],
            export_service.USER_FIELDS,
            "user",
        )

    def test_invalid_fields_raise(self, export_service):
        """Test that invalid fields raise ValidationError."""
        with pytest.raises(ValidationError, match="Invalid user fields"):
            export_service._validate_fields(
                ["id", "invalid_field"],
                export_service.USER_FIELDS,
                "user",
            )

    def test_empty_fields_pass(self, export_service):
        """Test that empty fields list passes."""
        # Should not raise
        export_service._validate_fields([], export_service.USER_FIELDS, "user")


# ---------------------------------------------------------------------------
# _user_to_dict Tests
# ---------------------------------------------------------------------------


class TestUserToDict:
    """Tests for _user_to_dict method."""

    def test_converts_all_fields(self, export_service, mock_user):
        """Test conversion with all fields."""
        result = export_service._user_to_dict(mock_user, export_service.USER_FIELDS)

        assert result["id"] == 1
        assert result["name"] == "Test User"
        assert result["preferences"] == {"theme": "dark"}

    def test_filters_fields(self, export_service, mock_user):
        """Test that only requested fields are included."""
        result = export_service._user_to_dict(mock_user, ["id", "name"])

        assert "id" in result
        assert "name" in result
        assert "preferences" not in result
        assert "created_at" not in result

    def test_formats_datetime(self, export_service, mock_user):
        """Test that datetime is formatted as ISO string."""
        result = export_service._user_to_dict(mock_user, ["created_at"])

        assert "created_at" in result
        assert "2024-01-15" in result["created_at"]


# ---------------------------------------------------------------------------
# _history_to_dict Tests
# ---------------------------------------------------------------------------


class TestHistoryToDict:
    """Tests for _history_to_dict method."""

    def test_converts_all_fields(self, export_service, mock_history_entry):
        """Test conversion with all fields."""
        result = export_service._history_to_dict(
            mock_history_entry, export_service.HISTORY_FIELDS
        )

        assert result["url"] == "https://youtube.com/watch?v=test123"
        assert result["title"] == "Test Video"
        assert result["file_size"] == 50_000_000

    def test_filters_fields(self, export_service, mock_history_entry):
        """Test that only requested fields are included."""
        result = export_service._history_to_dict(mock_history_entry, ["url", "title"])

        assert "url" in result
        assert "title" in result
        assert "file_path" not in result


# ---------------------------------------------------------------------------
# _export_to_json Tests
# ---------------------------------------------------------------------------


class TestExportToJson:
    """Tests for _export_to_json method."""

    def test_creates_valid_json(self, export_service, tmp_path):
        """Test that valid JSON is created."""
        data = [{"id": 1, "name": "Test"}]
        output_path = tmp_path / "test.json"

        export_service._export_to_json(data, output_path)

        assert output_path.exists()
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_creates_parent_directories(self, export_service, tmp_path):
        """Test that parent directories are created."""
        data = [{"id": 1}]
        output_path = tmp_path / "subdir" / "test.json"

        export_service._export_to_json(data, output_path)

        assert output_path.exists()

    def test_handles_unicode(self, export_service, tmp_path):
        """Test that unicode is handled correctly."""
        data = [{"name": "Tëst Üsér 日本語"}]
        output_path = tmp_path / "test.json"

        export_service._export_to_json(data, output_path)

        with open(output_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded[0]["name"] == "Tëst Üsér 日本語"

    def test_handles_datetime(self, export_service, tmp_path):
        """Test that datetime objects are serialized."""
        data = [{"date": datetime(2024, 1, 15)}]
        output_path = tmp_path / "test.json"

        # Should not raise
        export_service._export_to_json(data, output_path)

        assert output_path.exists()


# ---------------------------------------------------------------------------
# _export_to_csv Tests
# ---------------------------------------------------------------------------


class TestExportToCsv:
    """Tests for _export_to_csv method."""

    def test_creates_csv_with_header(self, export_service, tmp_path):
        """Test that CSV is created with header row."""
        data = [{"id": 1, "name": "Test"}]
        fields = ["id", "name"]
        output_path = tmp_path / "test.csv"

        export_service._export_to_csv(data, output_path, fields)

        assert output_path.exists()
        content = output_path.read_text()
        assert "id,name" in content
        assert "1,Test" in content

    def test_creates_parent_directories(self, export_service, tmp_path):
        """Test that parent directories are created."""
        data = [{"id": 1}]
        fields = ["id"]
        output_path = tmp_path / "subdir" / "test.csv"

        export_service._export_to_csv(data, output_path, fields)

        assert output_path.exists()

    def test_handles_empty_data(self, export_service, tmp_path):
        """Test that empty data creates header-only CSV."""
        data = []
        fields = ["id", "name"]
        output_path = tmp_path / "test.csv"

        export_service._export_to_csv(data, output_path, fields)

        content = output_path.read_text()
        assert "id,name" in content


# ---------------------------------------------------------------------------
# export_users Tests
# ---------------------------------------------------------------------------


class TestExportUsers:
    """Tests for export_users method."""

    def test_export_users_empty(self, export_service, mock_session, tmp_path):
        """Test exporting when no users exist."""
        mock_session.query.return_value.order_by.return_value.all.return_value = []

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service.export_users(
                output_path=tmp_path / "users.json",
                format=ExportFormat.JSON,
            )

            assert result.success is True
            assert result.record_count == 0
            assert "No users" in result.message

    def test_export_users_json(self, export_service, mock_session, mock_user, tmp_path):
        """Test exporting users to JSON."""
        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_user]

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            output_path = tmp_path / "users.json"
            result = export_service.export_users(
                output_path=output_path,
                format=ExportFormat.JSON,
            )

            assert result.success is True
            assert result.record_count == 1
            assert output_path.exists()

    def test_export_users_csv(self, export_service, mock_session, mock_user, tmp_path):
        """Test exporting users to CSV."""
        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_user]

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            output_path = tmp_path / "users.csv"
            result = export_service.export_users(
                output_path=output_path,
                format=ExportFormat.CSV,
            )

            assert result.success is True
            assert result.record_count == 1
            assert output_path.exists()

    def test_export_users_invalid_fields_raises(self, export_service, tmp_path):
        """Test that invalid fields raise ValidationError."""
        with pytest.raises(ValidationError):
            export_service.export_users(
                output_path=tmp_path / "users.json",
                format=ExportFormat.JSON,
                fields=["invalid_field"],
            )


# ---------------------------------------------------------------------------
# export_history Tests
# ---------------------------------------------------------------------------


class TestExportHistory:
    """Tests for export_history method."""

    def test_export_history_empty(self, export_service, mock_session, tmp_path):
        """Test exporting when no history exists."""
        mock_session.query.return_value.order_by.return_value.all.return_value = []

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service.export_history(
                output_path=tmp_path / "history.json",
                format=ExportFormat.JSON,
            )

            assert result.success is True
            assert result.record_count == 0
            assert "No download history" in result.message

    def test_export_history_json(self, export_service, mock_session, mock_history_entry, tmp_path):
        """Test exporting history to JSON."""
        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_history_entry]

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            output_path = tmp_path / "history.json"
            result = export_service.export_history(
                output_path=output_path,
                format=ExportFormat.JSON,
            )

            assert result.success is True
            assert result.record_count == 1
            assert output_path.exists()

    def test_export_history_csv(self, export_service, mock_session, mock_history_entry, tmp_path):
        """Test exporting history to CSV."""
        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_history_entry]

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            output_path = tmp_path / "history.csv"
            result = export_service.export_history(
                output_path=output_path,
                format=ExportFormat.CSV,
            )

            assert result.success is True
            assert result.record_count == 1
            assert output_path.exists()


# ---------------------------------------------------------------------------
# import_data Tests
# ---------------------------------------------------------------------------


class TestImportData:
    """Tests for import_data method."""

    def test_import_file_not_found_raises(self, export_service, tmp_path):
        """Test that missing file raises ExportError."""
        with pytest.raises(ExportError, match="not found"):
            export_service.import_data(tmp_path / "nonexistent.json")

    def test_import_non_json_raises(self, export_service, tmp_path):
        """Test that non-JSON file raises ExportError."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("id,name\n1,Test")

        with pytest.raises(ExportError, match="Only JSON"):
            export_service.import_data(csv_file)

    def test_import_invalid_json_raises(self, export_service, tmp_path):
        """Test that invalid JSON raises ExportError."""
        json_file = tmp_path / "data.json"
        json_file.write_text("not valid json")

        with pytest.raises(ExportError, match="Invalid JSON"):
            export_service.import_data(json_file)

    def test_import_non_array_raises(self, export_service, tmp_path):
        """Test that non-array JSON raises ValidationError."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')

        with pytest.raises(ValidationError, match="must be a JSON array"):
            export_service.import_data(json_file)

    def test_import_unknown_type_raises(self, export_service, tmp_path):
        """Test that unknown data type raises ValidationError."""
        json_file = tmp_path / "data.json"
        json_file.write_text("[]")

        with pytest.raises(ValidationError, match="Unknown data type"):
            export_service.import_data(json_file, data_type="unknown")


# ---------------------------------------------------------------------------
# _import_users Tests
# ---------------------------------------------------------------------------


class TestImportUsers:
    """Tests for _import_users method."""

    def test_import_users_empty_list(self, export_service, mock_session):
        """Test importing empty list."""
        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service._import_users([])

            assert result.success is True
            assert result.records_imported == 0
            assert result.records_skipped == 0

    def test_import_users_missing_name(self, export_service, mock_session):
        """Test that missing name is skipped."""
        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service._import_users([{"preferences": "{}"}])

            assert result.records_skipped == 1
            assert "Missing required field" in result.errors[0]

    def test_import_users_empty_name(self, export_service, mock_session):
        """Test that empty name is skipped."""
        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service._import_users([{"name": "   "}])

            assert result.records_skipped == 1
            assert "Empty name" in result.errors[0]

    def test_import_users_duplicate(self, export_service, mock_session, mock_user):
        """Test that duplicate users are skipped."""
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service._import_users([{"name": "Test User"}])

            assert result.records_skipped == 1
            assert "already exists" in result.errors[0]

    def test_import_users_success(self, export_service, mock_session):
        """Test successful user import."""
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service._import_users([{"name": "New User"}])

            assert result.records_imported == 1
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# _import_history Tests
# ---------------------------------------------------------------------------


class TestImportHistory:
    """Tests for _import_history method."""

    def test_import_history_empty_list(self, export_service, mock_session):
        """Test importing empty list."""
        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service._import_history([])

            assert result.success is True
            assert result.records_imported == 0

    def test_import_history_missing_fields(self, export_service, mock_session):
        """Test that missing required fields are skipped."""
        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service._import_history([{"url": "https://example.com"}])

            assert result.records_skipped == 1
            assert "Missing required fields" in result.errors[0]

    def test_import_history_duplicate_url(self, export_service, mock_session, mock_history_entry):
        """Test that duplicate URLs are skipped."""
        mock_session.query.return_value.filter.return_value.first.return_value = mock_history_entry

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service._import_history([
                {
                    "url": "https://youtube.com/watch?v=test123",
                    "title": "Test",
                    "file_path": "/path/to/file.mp4",
                }
            ])

            assert result.records_skipped == 1
            assert "already in history" in result.errors[0]

    def test_import_history_success(self, export_service, mock_session):
        """Test successful history import."""
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch("farmer_cli.services.export.get_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = export_service._import_history([
                {
                    "url": "https://youtube.com/watch?v=new123",
                    "title": "New Video",
                    "file_path": "/path/to/new.mp4",
                }
            ])

            assert result.records_imported == 1
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
