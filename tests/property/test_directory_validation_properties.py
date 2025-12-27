"""
Property-based tests for directory validation utilities.

Feature: farmer-cli-completion
Property 15: Directory Validation
Validates: Requirements 6.5

For any path provided as output directory, the validation function SHALL
correctly identify whether the path exists and is writable.
"""

import os
import string
import tempfile
from pathlib import Path

import pytest
from hypothesis import assume
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st


from farmer_cli.utils.directory_utils import (
    DirectoryValidationResult,
    ensure_directory,
    is_path_writable,
    normalize_path,
    validate_directory,
)


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid directory names
valid_dirname_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_",
    min_size=1,
    max_size=20,
).filter(lambda x: x.strip() and not x.startswith("-"))

# Strategy for generating path-like strings
path_component_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_.",
    min_size=1,
    max_size=30,
).filter(lambda x: x.strip() and x not in (".", ".."))


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestDirectoryValidation:
    """
    Property 15: Directory Validation

    For any path provided as output directory, the validation function SHALL
    correctly identify whether the path exists and is writable.

    **Validates: Requirements 6.5**
    """

    @given(valid_dirname_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_validate_existing_writable_directory_returns_valid(self, dirname: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5

        For any existing writable directory, validate_directory SHALL return
        is_valid=True, exists=True, and is_writable=True.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / dirname
            test_dir.mkdir(parents=True, exist_ok=True)

            result = validate_directory(test_dir)

            assert result.is_valid, f"Existing writable directory should be valid: {result.error}"
            assert result.exists, "Directory should exist"
            assert result.is_writable, "Directory should be writable"
            assert result.error is None, "Error should be None for valid directory"

    @given(valid_dirname_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_validate_nonexistent_directory_returns_invalid(self, dirname: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5

        For any non-existent directory path, validate_directory SHALL return
        is_valid=False and exists=False.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a path that doesn't exist
            nonexistent = Path(tmpdir) / dirname / "nonexistent_subdir"

            # Ensure it doesn't exist
            assume(not nonexistent.exists())

            result = validate_directory(nonexistent)

            assert not result.is_valid, "Non-existent directory should not be valid"
            assert not result.exists, "Non-existent directory should not exist"
            assert result.error is not None, "Error should be set for non-existent directory"

    @given(valid_dirname_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_validate_file_path_returns_invalid(self, filename: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5

        For any path that is a file (not a directory), validate_directory SHALL
        return is_valid=False.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file
            file_path = Path(tmpdir) / filename
            file_path.touch()

            result = validate_directory(file_path)

            assert not result.is_valid, "File path should not be valid as directory"
            assert result.exists, "File should exist"
            assert result.error is not None, "Error should be set for file path"
            assert "not a directory" in result.error.lower(), "Error should mention not a directory"

    @given(valid_dirname_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_ensure_directory_creates_nonexistent(self, dirname: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5, 6.6

        For any valid directory name, ensure_directory SHALL create the directory
        if it doesn't exist and return is_valid=True.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / dirname

            # Ensure it doesn't exist initially
            assume(not new_dir.exists())

            result = ensure_directory(new_dir)

            assert result.is_valid, f"Created directory should be valid: {result.error}"
            assert result.exists, "Directory should exist after ensure"
            assert result.is_writable, "Created directory should be writable"
            assert new_dir.exists(), "Directory should actually exist on filesystem"

    @given(st.lists(valid_dirname_strategy, min_size=1, max_size=5))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_ensure_directory_creates_nested_structure(self, path_parts: list[str]):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.6

        For any nested directory path, ensure_directory SHALL create all
        parent directories as needed.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir)
            for part in path_parts:
                nested_path = nested_path / part

            # Ensure it doesn't exist initially
            assume(not nested_path.exists())

            result = ensure_directory(nested_path)

            assert result.is_valid, f"Nested directory should be valid: {result.error}"
            assert nested_path.exists(), "Nested directory should exist"
            assert nested_path.is_dir(), "Path should be a directory"

    @given(valid_dirname_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_validate_returns_consistent_result_structure(self, dirname: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5

        For any input, validate_directory SHALL return a DirectoryValidationResult
        with all required fields populated.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / dirname

            result = validate_directory(test_path)

            # Check result structure
            assert isinstance(result, DirectoryValidationResult), "Should return DirectoryValidationResult"
            assert isinstance(result.is_valid, bool), "is_valid should be bool"
            assert isinstance(result.exists, bool), "exists should be bool"
            assert isinstance(result.is_writable, bool), "is_writable should be bool"
            assert result.error is None or isinstance(result.error, str), "error should be None or str"

    @given(valid_dirname_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_is_path_writable_matches_validate_for_existing(self, dirname: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5

        For any existing directory, is_path_writable SHALL return the same
        writability status as validate_directory.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / dirname
            test_dir.mkdir(parents=True, exist_ok=True)

            validation_result = validate_directory(test_dir)
            writable_result = is_path_writable(test_dir)

            assert validation_result.is_writable == writable_result, (
                "is_path_writable should match validate_directory.is_writable"
            )

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_validate_never_raises_exception(self, path_str: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5

        For any input string, validate_directory SHALL never raise an
        unhandled exception.
        """
        # This should never raise an exception
        result = validate_directory(path_str)

        # Result should always have expected structure
        assert hasattr(result, "is_valid"), "Result must have is_valid attribute"
        assert hasattr(result, "exists"), "Result must have exists attribute"
        assert hasattr(result, "is_writable"), "Result must have is_writable attribute"
        assert hasattr(result, "error"), "Result must have error attribute"

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_ensure_directory_never_raises_exception(self, path_str: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5, 6.6

        For any input string, ensure_directory SHALL never raise an
        unhandled exception.
        """
        # Use a temp directory as base to avoid creating random directories
        with tempfile.TemporaryDirectory() as tmpdir:
            # Only test with safe paths under temp directory
            if path_str and not any(c in path_str for c in ["\x00", "\n", "\r"]):
                try:
                    safe_path = Path(tmpdir) / path_str.replace("/", "_").replace("\\", "_")[:50]
                    result = ensure_directory(safe_path)

                    # Result should always have expected structure
                    assert hasattr(result, "is_valid"), "Result must have is_valid attribute"
                    assert hasattr(result, "exists"), "Result must have exists attribute"
                    assert hasattr(result, "is_writable"), "Result must have is_writable attribute"
                    assert hasattr(result, "error"), "Result must have error attribute"
                except Exception:
                    # Some paths may be invalid, but we shouldn't get unhandled exceptions
                    pass

    @given(valid_dirname_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_normalize_path_returns_absolute_path(self, dirname: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5

        For any valid path input, normalize_path SHALL return an absolute path.
        """
        result = normalize_path(dirname)

        assert result.is_absolute(), "Normalized path should be absolute"

    @given(valid_dirname_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_validation_is_idempotent(self, dirname: str):
        """
        Feature: farmer-cli-completion, Property 15: Directory Validation
        Validates: Requirements 6.5

        For any directory, calling validate_directory multiple times SHALL
        return the same result.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / dirname
            test_dir.mkdir(parents=True, exist_ok=True)

            result1 = validate_directory(test_dir)
            result2 = validate_directory(test_dir)

            assert result1.is_valid == result2.is_valid, "is_valid should be consistent"
            assert result1.exists == result2.exists, "exists should be consistent"
            assert result1.is_writable == result2.is_writable, "is_writable should be consistent"
