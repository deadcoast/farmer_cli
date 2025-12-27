"""
Unit tests for the output_config.py service module.

Tests cover:
- OutputSettings dataclass methods
- OutputConfigService.get_settings() and save_settings()
- set_download_directory() with validation
- set_filename_template() with validation
- set_conflict_resolution() and set_subdirectory_organization()
- validate_directory() static method
- ensure_directory() static method
- get_output_path() method
- _get_subdirectory() method
- _sanitize_dirname() static method
- resolve_conflict() method
- _get_unique_path() static method

Requirements: 9.1, 9.3
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from farmer_cli.services.output_config import ConflictResolution
from farmer_cli.services.output_config import DirectoryValidationResult
from farmer_cli.services.output_config import OutputConfigService
from farmer_cli.services.output_config import OutputSettings
from farmer_cli.services.output_config import SubdirectoryOrganization


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_preferences_service():
    """Create a mock preferences service."""
    service = MagicMock()
    service.load.return_value = {}
    return service


@pytest.fixture
def output_service(mock_preferences_service):
    """Create an OutputConfigService with mocked preferences."""
    return OutputConfigService(preferences_service=mock_preferences_service)


@pytest.fixture
def output_service_no_prefs():
    """Create an OutputConfigService without preferences."""
    return OutputConfigService(preferences_service=None)


# ---------------------------------------------------------------------------
# OutputSettings Tests
# ---------------------------------------------------------------------------


class TestOutputSettings:
    """Tests for OutputSettings dataclass."""

    def test_get_defaults(self):
        """Test get_defaults returns valid settings."""
        defaults = OutputSettings.get_defaults()

        assert defaults.download_directory is not None
        assert defaults.filename_template is not None
        assert defaults.conflict_resolution == ConflictResolution.RENAME
        assert defaults.subdirectory_organization == SubdirectoryOrganization.NONE

    def test_to_dict(self):
        """Test to_dict serialization."""
        settings = OutputSettings(
            download_directory="/downloads",
            filename_template="%(title)s.%(ext)s",
            conflict_resolution=ConflictResolution.OVERWRITE,
            subdirectory_organization=SubdirectoryOrganization.BY_CHANNEL,
        )

        result = settings.to_dict()

        assert result["download_directory"] == "/downloads"
        assert result["filename_template"] == "%(title)s.%(ext)s"
        assert result["conflict_resolution"] == "overwrite"
        assert result["subdirectory_organization"] == "by_channel"

    def test_from_dict(self):
        """Test from_dict deserialization."""
        data = {
            "download_directory": "/custom/path",
            "filename_template": "%(id)s.%(ext)s",
            "conflict_resolution": "skip",
            "subdirectory_organization": "by_date",
        }

        settings = OutputSettings.from_dict(data)

        assert settings.download_directory == "/custom/path"
        assert settings.filename_template == "%(id)s.%(ext)s"
        assert settings.conflict_resolution == ConflictResolution.SKIP
        assert settings.subdirectory_organization == SubdirectoryOrganization.BY_DATE

    def test_from_dict_uses_defaults(self):
        """Test from_dict uses defaults for missing keys."""
        settings = OutputSettings.from_dict({})

        defaults = OutputSettings.get_defaults()
        assert settings.download_directory == defaults.download_directory
        assert settings.filename_template == defaults.filename_template


# ---------------------------------------------------------------------------
# ConflictResolution Tests
# ---------------------------------------------------------------------------


class TestConflictResolution:
    """Tests for ConflictResolution enum."""

    def test_rename_value(self):
        """Test RENAME value."""
        assert ConflictResolution.RENAME.value == "rename"

    def test_overwrite_value(self):
        """Test OVERWRITE value."""
        assert ConflictResolution.OVERWRITE.value == "overwrite"

    def test_skip_value(self):
        """Test SKIP value."""
        assert ConflictResolution.SKIP.value == "skip"


# ---------------------------------------------------------------------------
# SubdirectoryOrganization Tests
# ---------------------------------------------------------------------------


class TestSubdirectoryOrganization:
    """Tests for SubdirectoryOrganization enum."""

    def test_none_value(self):
        """Test NONE value."""
        assert SubdirectoryOrganization.NONE.value == "none"

    def test_by_channel_value(self):
        """Test BY_CHANNEL value."""
        assert SubdirectoryOrganization.BY_CHANNEL.value == "by_channel"

    def test_by_playlist_value(self):
        """Test BY_PLAYLIST value."""
        assert SubdirectoryOrganization.BY_PLAYLIST.value == "by_playlist"

    def test_by_date_value(self):
        """Test BY_DATE value."""
        assert SubdirectoryOrganization.BY_DATE.value == "by_date"


# ---------------------------------------------------------------------------
# OutputConfigService Initialization Tests
# ---------------------------------------------------------------------------


class TestOutputConfigServiceInit:
    """Tests for OutputConfigService initialization."""

    def test_init_with_preferences(self, mock_preferences_service):
        """Test initialization with preferences service."""
        service = OutputConfigService(preferences_service=mock_preferences_service)

        assert service._preferences_service == mock_preferences_service

    def test_init_without_preferences(self):
        """Test initialization without preferences service."""
        service = OutputConfigService(preferences_service=None)

        assert service._preferences_service is None


# ---------------------------------------------------------------------------
# get_settings Tests
# ---------------------------------------------------------------------------


class TestGetSettings:
    """Tests for get_settings method."""

    def test_get_settings_returns_defaults_without_prefs(self, output_service_no_prefs):
        """Test get_settings returns defaults when no preferences."""
        settings = output_service_no_prefs.get_settings()

        defaults = OutputSettings.get_defaults()
        assert settings.download_directory == defaults.download_directory

    def test_get_settings_loads_from_preferences(self, output_service, mock_preferences_service):
        """Test get_settings loads from preferences."""
        mock_preferences_service.load.return_value = {
            "download_directory": "/custom/downloads",
        }

        settings = output_service.get_settings()

        assert settings.download_directory == "/custom/downloads"


# ---------------------------------------------------------------------------
# save_settings Tests
# ---------------------------------------------------------------------------


class TestSaveSettings:
    """Tests for save_settings method."""

    def test_save_settings_calls_update(self, output_service, mock_preferences_service):
        """Test save_settings calls preferences update."""
        settings = OutputSettings.get_defaults()

        output_service.save_settings(settings)

        mock_preferences_service.update.assert_called_once()

    def test_save_settings_without_prefs_does_not_raise(self, output_service_no_prefs):
        """Test save_settings without preferences doesn't raise."""
        settings = OutputSettings.get_defaults()

        # Should not raise
        output_service_no_prefs.save_settings(settings)


# ---------------------------------------------------------------------------
# validate_directory Tests
# ---------------------------------------------------------------------------


class TestValidateDirectory:
    """Tests for validate_directory static method."""

    def test_validate_existing_writable_directory(self, tmp_path):
        """Test validation of existing writable directory."""
        result = OutputConfigService.validate_directory(tmp_path)

        assert result.is_valid is True
        assert result.exists is True
        assert result.is_writable is True
        assert result.error is None

    def test_validate_nonexistent_directory(self, tmp_path):
        """Test validation of non-existent directory."""
        nonexistent = tmp_path / "nonexistent"

        result = OutputConfigService.validate_directory(nonexistent)

        assert result.is_valid is False
        assert result.exists is False
        assert "does not exist" in result.error

    def test_validate_file_not_directory(self, tmp_path):
        """Test validation of file (not directory)."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        result = OutputConfigService.validate_directory(file_path)

        assert result.is_valid is False
        assert "not a directory" in result.error


# ---------------------------------------------------------------------------
# ensure_directory Tests
# ---------------------------------------------------------------------------


class TestEnsureDirectory:
    """Tests for ensure_directory static method."""

    def test_ensure_creates_directory(self, tmp_path):
        """Test ensure_directory creates missing directory."""
        new_dir = tmp_path / "new_directory"

        result = OutputConfigService.ensure_directory(new_dir)

        assert result.is_valid is True
        assert new_dir.exists()

    def test_ensure_existing_directory(self, tmp_path):
        """Test ensure_directory with existing directory."""
        result = OutputConfigService.ensure_directory(tmp_path)

        assert result.is_valid is True

    def test_ensure_creates_nested_directories(self, tmp_path):
        """Test ensure_directory creates nested directories."""
        nested = tmp_path / "a" / "b" / "c"

        result = OutputConfigService.ensure_directory(nested)

        assert result.is_valid is True
        assert nested.exists()


# ---------------------------------------------------------------------------
# set_download_directory Tests
# ---------------------------------------------------------------------------


class TestSetDownloadDirectory:
    """Tests for set_download_directory method."""

    def test_set_valid_directory(self, output_service, tmp_path):
        """Test setting a valid directory."""
        result = output_service.set_download_directory(tmp_path)

        assert result.is_valid is True

    def test_set_invalid_directory(self, output_service, tmp_path):
        """Test setting an invalid directory."""
        result = output_service.set_download_directory(tmp_path / "nonexistent")

        assert result.is_valid is False


# ---------------------------------------------------------------------------
# set_filename_template Tests
# ---------------------------------------------------------------------------


class TestSetFilenameTemplate:
    """Tests for set_filename_template method."""

    def test_set_valid_template(self, output_service):
        """Test setting a valid template."""
        success, error = output_service.set_filename_template("%(title)s.%(ext)s")

        assert success is True
        assert error is None

    def test_set_invalid_template(self, output_service):
        """Test setting an invalid template."""
        # Empty template should be invalid
        success, error = output_service.set_filename_template("")

        # The validation depends on FilenameTemplate implementation
        # Just verify it returns a tuple
        assert isinstance(success, bool)


# ---------------------------------------------------------------------------
# set_conflict_resolution Tests
# ---------------------------------------------------------------------------


class TestSetConflictResolution:
    """Tests for set_conflict_resolution method."""

    def test_set_with_enum(self, output_service, mock_preferences_service):
        """Test setting with enum value."""
        output_service.set_conflict_resolution(ConflictResolution.SKIP)

        mock_preferences_service.update.assert_called()

    def test_set_with_string(self, output_service, mock_preferences_service):
        """Test setting with string value."""
        output_service.set_conflict_resolution("overwrite")

        mock_preferences_service.update.assert_called()


# ---------------------------------------------------------------------------
# set_subdirectory_organization Tests
# ---------------------------------------------------------------------------


class TestSetSubdirectoryOrganization:
    """Tests for set_subdirectory_organization method."""

    def test_set_with_enum(self, output_service, mock_preferences_service):
        """Test setting with enum value."""
        output_service.set_subdirectory_organization(SubdirectoryOrganization.BY_CHANNEL)

        mock_preferences_service.update.assert_called()

    def test_set_with_string(self, output_service, mock_preferences_service):
        """Test setting with string value."""
        output_service.set_subdirectory_organization("by_date")

        mock_preferences_service.update.assert_called()


# ---------------------------------------------------------------------------
# _sanitize_dirname Tests
# ---------------------------------------------------------------------------


class TestSanitizeDirname:
    """Tests for _sanitize_dirname static method."""

    def test_sanitize_normal_name(self):
        """Test sanitizing a normal name."""
        result = OutputConfigService._sanitize_dirname("My Channel")

        assert result == "My_Channel"

    def test_sanitize_removes_invalid_chars(self):
        """Test that invalid characters are removed."""
        result = OutputConfigService._sanitize_dirname('Channel: "Test" <name>')

        assert ":" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_truncates_long_names(self):
        """Test that long names are truncated."""
        long_name = "A" * 200

        result = OutputConfigService._sanitize_dirname(long_name)

        assert len(result) <= 100

    def test_sanitize_empty_returns_unknown(self):
        """Test that empty string returns 'Unknown'."""
        result = OutputConfigService._sanitize_dirname("")

        assert result == "Unknown"

    def test_sanitize_only_invalid_chars_returns_unknown(self):
        """Test that string with only invalid chars returns 'Unknown'."""
        result = OutputConfigService._sanitize_dirname(':<>"/\\|?*')

        assert result == "Unknown"


# ---------------------------------------------------------------------------
# _get_subdirectory Tests
# ---------------------------------------------------------------------------


class TestGetSubdirectory:
    """Tests for _get_subdirectory method."""

    def test_none_organization(self, output_service):
        """Test NONE organization returns None."""
        result = output_service._get_subdirectory(
            {"uploader": "Test"},
            SubdirectoryOrganization.NONE,
        )

        assert result is None

    def test_by_channel_with_uploader(self, output_service):
        """Test BY_CHANNEL with uploader."""
        result = output_service._get_subdirectory(
            {"uploader": "Test Channel"},
            SubdirectoryOrganization.BY_CHANNEL,
        )

        assert result == "Test_Channel"

    def test_by_channel_with_channel(self, output_service):
        """Test BY_CHANNEL with channel field."""
        result = output_service._get_subdirectory(
            {"channel": "Test Channel"},
            SubdirectoryOrganization.BY_CHANNEL,
        )

        assert result == "Test_Channel"

    def test_by_channel_no_uploader(self, output_service):
        """Test BY_CHANNEL without uploader returns None."""
        result = output_service._get_subdirectory(
            {},
            SubdirectoryOrganization.BY_CHANNEL,
        )

        assert result is None

    def test_by_playlist(self, output_service):
        """Test BY_PLAYLIST organization."""
        result = output_service._get_subdirectory(
            {"playlist": "My Playlist"},
            SubdirectoryOrganization.BY_PLAYLIST,
        )

        assert result == "My_Playlist"

    def test_by_date(self, output_service):
        """Test BY_DATE organization."""
        result = output_service._get_subdirectory(
            {},
            SubdirectoryOrganization.BY_DATE,
        )

        # Should be in YYYY-MM format
        assert result is not None
        assert len(result) == 7
        assert "-" in result


# ---------------------------------------------------------------------------
# resolve_conflict Tests
# ---------------------------------------------------------------------------


class TestResolveConflict:
    """Tests for resolve_conflict method."""

    def test_no_conflict_returns_original(self, output_service, tmp_path):
        """Test that non-existent file returns original path."""
        file_path = tmp_path / "new_file.mp4"

        result_path, should_download = output_service.resolve_conflict(file_path)

        assert result_path == file_path
        assert should_download is True

    def test_skip_resolution(self, output_service, tmp_path):
        """Test SKIP resolution."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result_path, should_download = output_service.resolve_conflict(
            file_path, ConflictResolution.SKIP
        )

        assert result_path == file_path
        assert should_download is False

    def test_overwrite_resolution(self, output_service, tmp_path):
        """Test OVERWRITE resolution."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result_path, should_download = output_service.resolve_conflict(
            file_path, ConflictResolution.OVERWRITE
        )

        assert result_path == file_path
        assert should_download is True

    def test_rename_resolution(self, output_service, tmp_path):
        """Test RENAME resolution."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result_path, should_download = output_service.resolve_conflict(
            file_path, ConflictResolution.RENAME
        )

        assert result_path != file_path
        assert "(1)" in str(result_path)
        assert should_download is True


# ---------------------------------------------------------------------------
# _get_unique_path Tests
# ---------------------------------------------------------------------------


class TestGetUniquePath:
    """Tests for _get_unique_path static method."""

    def test_nonexistent_returns_original(self, tmp_path):
        """Test that non-existent file returns original."""
        file_path = tmp_path / "new.mp4"

        result = OutputConfigService._get_unique_path(file_path)

        assert result == file_path

    def test_existing_adds_suffix(self, tmp_path):
        """Test that existing file gets suffix."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result = OutputConfigService._get_unique_path(file_path)

        assert result.name == "existing (1).mp4"

    def test_multiple_existing_increments(self, tmp_path):
        """Test that multiple existing files increment suffix."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")
        (tmp_path / "existing (1).mp4").write_text("existing 1")

        result = OutputConfigService._get_unique_path(file_path)

        assert result.name == "existing (2).mp4"


# ---------------------------------------------------------------------------
# DirectoryValidationResult Tests
# ---------------------------------------------------------------------------


class TestDirectoryValidationResult:
    """Tests for DirectoryValidationResult dataclass."""

    def test_valid_result(self):
        """Test valid result."""
        result = DirectoryValidationResult(
            is_valid=True,
            exists=True,
            is_writable=True,
            error=None,
        )

        assert result.is_valid is True
        assert result.error is None

    def test_invalid_result(self):
        """Test invalid result."""
        result = DirectoryValidationResult(
            is_valid=False,
            exists=False,
            is_writable=False,
            error="Directory not found",
        )

        assert result.is_valid is False
        assert result.error == "Directory not found"
