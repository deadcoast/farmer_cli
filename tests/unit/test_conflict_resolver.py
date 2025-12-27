"""
Unit tests for the conflict_resolver.py module.

Tests cover:
- detect_conflict() function
- resolve_conflict() function with all resolution types
- get_unique_path() function
- get_conflict_options() function
- suggest_resolution() function
- ConflictResolver class methods

Requirements: 9.1, 9.3
"""

from pathlib import Path

import pytest

from farmer_cli.utils.conflict_resolver import ConflictResolution
from farmer_cli.utils.conflict_resolver import ConflictResolver
from farmer_cli.utils.conflict_resolver import ConflictResult
from farmer_cli.utils.conflict_resolver import detect_conflict
from farmer_cli.utils.conflict_resolver import get_conflict_options
from farmer_cli.utils.conflict_resolver import get_unique_path
from farmer_cli.utils.conflict_resolver import resolve_conflict
from farmer_cli.utils.conflict_resolver import suggest_resolution


# ---------------------------------------------------------------------------
# ConflictResolution Enum Tests
# ---------------------------------------------------------------------------


class TestConflictResolutionEnum:
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
# ConflictResult Dataclass Tests
# ---------------------------------------------------------------------------


class TestConflictResult:
    """Tests for ConflictResult dataclass."""

    def test_create_result(self, tmp_path):
        """Test creating a ConflictResult."""
        result = ConflictResult(
            resolved_path=tmp_path / "file.mp4",
            should_proceed=True,
            action_taken="renamed",
            original_path=tmp_path / "original.mp4",
        )

        assert result.resolved_path == tmp_path / "file.mp4"
        assert result.should_proceed is True
        assert result.action_taken == "renamed"
        assert result.original_path == tmp_path / "original.mp4"


# ---------------------------------------------------------------------------
# detect_conflict Tests
# ---------------------------------------------------------------------------


class TestDetectConflict:
    """Tests for detect_conflict function."""

    def test_no_conflict_nonexistent_file(self, tmp_path):
        """Test no conflict for non-existent file."""
        result = detect_conflict(tmp_path / "nonexistent.mp4")

        assert result is False

    def test_conflict_existing_file(self, tmp_path):
        """Test conflict detected for existing file."""
        existing = tmp_path / "existing.mp4"
        existing.write_text("content")

        result = detect_conflict(existing)

        assert result is True

    def test_conflict_with_string_path(self, tmp_path):
        """Test detect_conflict with string path."""
        existing = tmp_path / "existing.mp4"
        existing.write_text("content")

        result = detect_conflict(str(existing))

        assert result is True


# ---------------------------------------------------------------------------
# resolve_conflict Tests
# ---------------------------------------------------------------------------


class TestResolveConflict:
    """Tests for resolve_conflict function."""

    def test_no_conflict_returns_original(self, tmp_path):
        """Test that non-existent file returns original path."""
        file_path = tmp_path / "new_file.mp4"

        result = resolve_conflict(file_path)

        assert result.resolved_path == file_path
        assert result.should_proceed is True
        assert result.action_taken == "no_conflict"

    def test_skip_resolution(self, tmp_path):
        """Test SKIP resolution."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result = resolve_conflict(file_path, ConflictResolution.SKIP)

        assert result.resolved_path == file_path
        assert result.should_proceed is False
        assert result.action_taken == "skipped"

    def test_overwrite_resolution(self, tmp_path):
        """Test OVERWRITE resolution."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result = resolve_conflict(file_path, ConflictResolution.OVERWRITE)

        assert result.resolved_path == file_path
        assert result.should_proceed is True
        assert result.action_taken == "overwrite"

    def test_rename_resolution(self, tmp_path):
        """Test RENAME resolution."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result = resolve_conflict(file_path, ConflictResolution.RENAME)

        assert result.resolved_path != file_path
        assert "(1)" in str(result.resolved_path)
        assert result.should_proceed is True
        assert result.action_taken == "renamed"

    def test_default_resolution_is_rename(self, tmp_path):
        """Test that default resolution is RENAME."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result = resolve_conflict(file_path)

        assert result.action_taken == "renamed"

    def test_original_path_preserved(self, tmp_path):
        """Test that original path is preserved in result."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result = resolve_conflict(file_path, ConflictResolution.RENAME)

        assert result.original_path == file_path


# ---------------------------------------------------------------------------
# get_unique_path Tests
# ---------------------------------------------------------------------------


class TestGetUniquePath:
    """Tests for get_unique_path function."""

    def test_nonexistent_returns_original(self, tmp_path):
        """Test that non-existent file returns original."""
        file_path = tmp_path / "new.mp4"

        result = get_unique_path(file_path)

        assert result == file_path

    def test_existing_adds_suffix(self, tmp_path):
        """Test that existing file gets suffix."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result = get_unique_path(file_path)

        assert result.name == "existing (1).mp4"

    def test_multiple_existing_increments(self, tmp_path):
        """Test that multiple existing files increment suffix."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")
        (tmp_path / "existing (1).mp4").write_text("existing 1")

        result = get_unique_path(file_path)

        assert result.name == "existing (2).mp4"

    def test_preserves_extension(self, tmp_path):
        """Test that file extension is preserved."""
        file_path = tmp_path / "video.webm"
        file_path.write_text("content")

        result = get_unique_path(file_path)

        assert result.suffix == ".webm"

    def test_preserves_parent_directory(self, tmp_path):
        """Test that parent directory is preserved."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file_path = subdir / "video.mp4"
        file_path.write_text("content")

        result = get_unique_path(file_path)

        assert result.parent == subdir

    def test_string_path_input(self, tmp_path):
        """Test with string path input."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        result = get_unique_path(str(file_path))

        assert isinstance(result, Path)
        assert "(1)" in result.name

    def test_max_attempts_raises(self, tmp_path):
        """Test that exceeding max_attempts raises ValueError."""
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("existing")

        # Create files for attempts 1-5
        for i in range(1, 6):
            (tmp_path / f"existing ({i}).mp4").write_text(f"existing {i}")

        with pytest.raises(ValueError, match="Unable to find unique"):
            get_unique_path(file_path, max_attempts=5)


# ---------------------------------------------------------------------------
# get_conflict_options Tests
# ---------------------------------------------------------------------------


class TestGetConflictOptions:
    """Tests for get_conflict_options function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        result = get_conflict_options()

        assert isinstance(result, list)

    def test_has_three_options(self):
        """Test that there are three options."""
        result = get_conflict_options()

        assert len(result) == 3

    def test_options_are_tuples(self):
        """Test that options are tuples."""
        result = get_conflict_options()

        for option in result:
            assert isinstance(option, tuple)
            assert len(option) == 3

    def test_includes_rename(self):
        """Test that RENAME option is included."""
        result = get_conflict_options()

        resolutions = [opt[1] for opt in result]
        assert ConflictResolution.RENAME in resolutions

    def test_includes_overwrite(self):
        """Test that OVERWRITE option is included."""
        result = get_conflict_options()

        resolutions = [opt[1] for opt in result]
        assert ConflictResolution.OVERWRITE in resolutions

    def test_includes_skip(self):
        """Test that SKIP option is included."""
        result = get_conflict_options()

        resolutions = [opt[1] for opt in result]
        assert ConflictResolution.SKIP in resolutions

    def test_options_have_descriptions(self):
        """Test that all options have descriptions."""
        result = get_conflict_options()

        for name, resolution, description in result:
            assert isinstance(name, str)
            assert len(name) > 0
            assert isinstance(description, str)
            assert len(description) > 0


# ---------------------------------------------------------------------------
# suggest_resolution Tests
# ---------------------------------------------------------------------------


class TestSuggestResolution:
    """Tests for suggest_resolution function."""

    def test_nonexistent_file_suggests_rename(self, tmp_path):
        """Test that non-existent file suggests RENAME."""
        result = suggest_resolution(tmp_path / "nonexistent.mp4")

        assert result == ConflictResolution.RENAME

    def test_small_file_suggests_overwrite(self, tmp_path):
        """Test that small file suggests OVERWRITE."""
        small_file = tmp_path / "small.mp4"
        small_file.write_text("x" * 100)  # Less than 1KB

        result = suggest_resolution(small_file)

        assert result == ConflictResolution.OVERWRITE

    def test_large_file_suggests_rename(self, tmp_path):
        """Test that large file suggests RENAME."""
        large_file = tmp_path / "large.mp4"
        large_file.write_text("x" * 2000)  # More than 1KB

        result = suggest_resolution(large_file)

        assert result == ConflictResolution.RENAME


# ---------------------------------------------------------------------------
# ConflictResolver Class Tests
# ---------------------------------------------------------------------------


class TestConflictResolverInit:
    """Tests for ConflictResolver initialization."""

    def test_default_resolution(self):
        """Test default resolution is RENAME."""
        resolver = ConflictResolver()

        assert resolver.default_resolution == ConflictResolution.RENAME

    def test_custom_default_resolution(self):
        """Test custom default resolution."""
        resolver = ConflictResolver(default_resolution=ConflictResolution.SKIP)

        assert resolver.default_resolution == ConflictResolution.SKIP

    def test_remember_choice_default_false(self):
        """Test remember_choice defaults to False."""
        resolver = ConflictResolver()

        assert resolver._remember_choice is False

    def test_remember_choice_enabled(self):
        """Test remember_choice can be enabled."""
        resolver = ConflictResolver(remember_choice=True)

        assert resolver._remember_choice is True


class TestConflictResolverDefaultResolution:
    """Tests for default_resolution property."""

    def test_get_default_resolution(self):
        """Test getting default resolution."""
        resolver = ConflictResolver(default_resolution=ConflictResolution.OVERWRITE)

        assert resolver.default_resolution == ConflictResolution.OVERWRITE

    def test_set_default_resolution(self):
        """Test setting default resolution."""
        resolver = ConflictResolver()
        resolver.default_resolution = ConflictResolution.SKIP

        assert resolver.default_resolution == ConflictResolution.SKIP


class TestConflictResolverResolve:
    """Tests for ConflictResolver.resolve method."""

    def test_resolve_uses_default(self, tmp_path):
        """Test resolve uses default resolution."""
        resolver = ConflictResolver(default_resolution=ConflictResolution.SKIP)
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("content")

        result = resolver.resolve(file_path)

        assert result.action_taken == "skipped"

    def test_resolve_with_override(self, tmp_path):
        """Test resolve with resolution override."""
        resolver = ConflictResolver(default_resolution=ConflictResolution.SKIP)
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("content")

        result = resolver.resolve(file_path, ConflictResolution.OVERWRITE)

        assert result.action_taken == "overwrite"

    def test_resolve_uses_remembered_choice(self, tmp_path):
        """Test resolve uses remembered choice."""
        resolver = ConflictResolver(
            default_resolution=ConflictResolution.RENAME,
            remember_choice=True,
        )
        resolver.remember(ConflictResolution.SKIP)

        file_path = tmp_path / "existing.mp4"
        file_path.write_text("content")

        result = resolver.resolve(file_path)

        assert result.action_taken == "skipped"


class TestConflictResolverRemember:
    """Tests for ConflictResolver.remember method."""

    def test_remember_stores_choice(self):
        """Test remember stores the choice."""
        resolver = ConflictResolver(remember_choice=True)

        resolver.remember(ConflictResolution.OVERWRITE)

        assert resolver._remembered_choice == ConflictResolution.OVERWRITE

    def test_clear_remembered(self):
        """Test clear_remembered clears the choice."""
        resolver = ConflictResolver(remember_choice=True)
        resolver.remember(ConflictResolution.OVERWRITE)

        resolver.clear_remembered()

        assert resolver._remembered_choice is None


class TestConflictResolverHasConflict:
    """Tests for ConflictResolver.has_conflict method."""

    def test_has_conflict_true(self, tmp_path):
        """Test has_conflict returns True for existing file."""
        resolver = ConflictResolver()
        file_path = tmp_path / "existing.mp4"
        file_path.write_text("content")

        assert resolver.has_conflict(file_path) is True

    def test_has_conflict_false(self, tmp_path):
        """Test has_conflict returns False for non-existent file."""
        resolver = ConflictResolver()

        assert resolver.has_conflict(tmp_path / "nonexistent.mp4") is False


class TestConflictResolverResolveBatch:
    """Tests for ConflictResolver.resolve_batch method."""

    def test_resolve_batch_empty_list(self):
        """Test resolve_batch with empty list."""
        resolver = ConflictResolver()

        result = resolver.resolve_batch([])

        assert result == []

    def test_resolve_batch_multiple_files(self, tmp_path):
        """Test resolve_batch with multiple files."""
        resolver = ConflictResolver()

        # Create some existing files
        (tmp_path / "file1.mp4").write_text("content1")
        (tmp_path / "file2.mp4").write_text("content2")

        paths = [
            tmp_path / "file1.mp4",
            tmp_path / "file2.mp4",
            tmp_path / "file3.mp4",  # Non-existent
        ]

        results = resolver.resolve_batch(paths)

        assert len(results) == 3
        assert results[0].action_taken == "renamed"
        assert results[1].action_taken == "renamed"
        assert results[2].action_taken == "no_conflict"

    def test_resolve_batch_with_resolution(self, tmp_path):
        """Test resolve_batch with specified resolution."""
        resolver = ConflictResolver()

        (tmp_path / "file1.mp4").write_text("content1")
        (tmp_path / "file2.mp4").write_text("content2")

        paths = [tmp_path / "file1.mp4", tmp_path / "file2.mp4"]

        results = resolver.resolve_batch(paths, ConflictResolution.SKIP)

        assert all(r.action_taken == "skipped" for r in results)
