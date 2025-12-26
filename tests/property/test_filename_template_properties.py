"""
Property-based tests for filename template utilities.

Feature: farmer-cli-completion
Property 14: Filename Template Rendering
Validates: Requirements 6.2

For any valid filename template and video metadata dictionary,
the rendered filename SHALL contain no invalid filesystem characters
and SHALL be non-empty.
"""

import re
import string

import pytest
from hypothesis import assume
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st


from farmer_cli.utils.filename_template import FilenameTemplate
from farmer_cli.utils.filename_template import INVALID_FILENAME_CHARS
from farmer_cli.utils.filename_template import MAX_FILENAME_LENGTH


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating safe text (no control characters)
safe_text_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " -_.,!@#$%^&()[]{}+=",
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip())  # Ensure non-empty after strip

# Strategy for generating video extensions
extension_strategy = st.sampled_from(["mp4", "webm", "mkv", "avi", "mov", "flv", "m4v"])

# Strategy for generating valid video metadata
video_metadata_strategy = st.fixed_dictionaries({
    "title": safe_text_strategy,
    "uploader": safe_text_strategy,
    "upload_date": st.from_regex(r"[0-9]{8}", fullmatch=True),
    "id": st.text(alphabet=string.ascii_letters + string.digits + "-_", min_size=5, max_size=20),
    "ext": extension_strategy,
    "playlist": safe_text_strategy,
    "playlist_index": st.integers(min_value=1, max_value=9999).map(lambda x: f"{x:02d}"),
})

# Strategy for generating valid template strings
valid_template_strategy = st.sampled_from([
    "%(title)s.%(ext)s",
    "%(title)s - %(uploader)s.%(ext)s",
    "%(upload_date)s - %(title)s.%(ext)s",
    "%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s",
    "%(uploader)s - %(title)s [%(id)s].%(ext)s",
    "%(title)s (%(upload_date)s).%(ext)s",
])

# Strategy for generating metadata with potentially problematic characters
problematic_text_strategy = st.text(
    alphabet=string.printable,
    min_size=1,
    max_size=100,
)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestFilenameTemplateRendering:
    """
    Property 14: Filename Template Rendering

    For any valid filename template and video metadata dictionary,
    the rendered filename SHALL contain no invalid filesystem characters
    and SHALL be non-empty.

    **Validates: Requirements 6.2**
    """

    @given(valid_template_strategy, video_metadata_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_rendered_filename_contains_no_invalid_characters(
        self, template: str, metadata: dict
    ):
        """
        Feature: farmer-cli-completion, Property 14: Filename Template Rendering
        Validates: Requirements 6.2

        For any valid template and metadata, the rendered filename SHALL
        contain no invalid filesystem characters.
        """
        ft = FilenameTemplate(template)
        result = ft.render(metadata)

        # Should succeed with valid inputs
        assert result.success, f"Render should succeed: {result.error}"
        assert result.filename is not None, "Filename should not be None"

        # Check for invalid characters
        invalid_chars_found = re.findall(INVALID_FILENAME_CHARS, result.filename)
        assert not invalid_chars_found, (
            f"Filename '{result.filename}' contains invalid characters: {invalid_chars_found}"
        )

    @given(valid_template_strategy, video_metadata_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_rendered_filename_is_non_empty(self, template: str, metadata: dict):
        """
        Feature: farmer-cli-completion, Property 14: Filename Template Rendering
        Validates: Requirements 6.2

        For any valid template and metadata, the rendered filename SHALL
        be non-empty.
        """
        ft = FilenameTemplate(template)
        result = ft.render(metadata)

        # Should succeed with valid inputs
        assert result.success, f"Render should succeed: {result.error}"
        assert result.filename is not None, "Filename should not be None"

        # Filename should be non-empty
        assert len(result.filename) > 0, "Filename should not be empty"
        assert not result.filename.isspace(), "Filename should not be only whitespace"

    @given(valid_template_strategy, video_metadata_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_rendered_filename_respects_max_length(self, template: str, metadata: dict):
        """
        Feature: farmer-cli-completion, Property 14: Filename Template Rendering
        Validates: Requirements 6.2

        For any valid template and metadata, the rendered filename SHALL
        not exceed the maximum filename length.
        """
        ft = FilenameTemplate(template)
        result = ft.render(metadata)

        # Should succeed with valid inputs
        assert result.success, f"Render should succeed: {result.error}"
        assert result.filename is not None, "Filename should not be None"

        # Filename should not exceed max length
        assert len(result.filename) <= MAX_FILENAME_LENGTH, (
            f"Filename length {len(result.filename)} exceeds max {MAX_FILENAME_LENGTH}"
        )

    @given(st.text(min_size=1, max_size=200), extension_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_sanitization_removes_all_invalid_characters(
        self, title: str, ext: str
    ):
        """
        Feature: farmer-cli-completion, Property 14: Filename Template Rendering
        Validates: Requirements 6.2

        For any title string (including those with invalid characters),
        the sanitized filename SHALL contain no invalid filesystem characters.
        """
        # Skip if title is empty or only whitespace
        assume(title.strip())

        ft = FilenameTemplate("%(title)s.%(ext)s")
        metadata = {"title": title, "ext": ext}
        result = ft.render(metadata)

        # If render succeeds, check for invalid characters
        if result.success and result.filename:
            invalid_chars_found = re.findall(INVALID_FILENAME_CHARS, result.filename)
            assert not invalid_chars_found, (
                f"Filename '{result.filename}' contains invalid characters: {invalid_chars_found}"
            )

    @given(problematic_text_strategy, extension_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_render_never_raises_exception(self, title: str, ext: str):
        """
        Feature: farmer-cli-completion, Property 14: Filename Template Rendering
        Validates: Requirements 6.2

        For any input, render() SHALL never raise an unhandled exception.
        """
        ft = FilenameTemplate("%(title)s.%(ext)s")
        metadata = {"title": title, "ext": ext}

        # This should never raise an exception
        result = ft.render(metadata)

        # Result should always have expected structure
        assert hasattr(result, "filename"), "Result must have filename attribute"
        assert hasattr(result, "success"), "Result must have success attribute"
        assert hasattr(result, "error"), "Result must have error attribute"

        # If failed, error should be descriptive
        if not result.success:
            assert result.error is not None, "Error should not be None on failure"
            assert len(result.error) > 0, "Error message should not be empty"

    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.none()),
        min_size=0,
        max_size=10,
    ))
    @settings(max_examples=100)
    @pytest.mark.property
    def test_render_handles_arbitrary_metadata(self, metadata: dict):
        """
        Feature: farmer-cli-completion, Property 14: Filename Template Rendering
        Validates: Requirements 6.2

        For any arbitrary metadata dictionary, render() SHALL handle it
        gracefully without raising exceptions.
        """
        ft = FilenameTemplate("%(title)s.%(ext)s")

        # This should never raise an exception
        result = ft.render(metadata)

        # Result should always have expected structure
        assert hasattr(result, "filename"), "Result must have filename attribute"
        assert hasattr(result, "success"), "Result must have success attribute"
        assert hasattr(result, "error"), "Result must have error attribute"

    @given(valid_template_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_validate_accepts_valid_templates(self, template: str):
        """
        Feature: farmer-cli-completion, Property 14: Filename Template Rendering
        Validates: Requirements 6.2

        For any valid template string, validate() SHALL return is_valid=True.
        """
        ft = FilenameTemplate()
        result = ft.validate(template)

        assert result.is_valid, f"Valid template '{template}' should be accepted: {result.error}"
        assert result.error is None, "Error should be None for valid template"

    @given(st.sampled_from([
        "",
        "no_placeholders",
        "%(incomplete",
        "%(bad)d",
        "%s only",
    ]))
    @settings(max_examples=50)
    @pytest.mark.property
    def test_validate_rejects_invalid_templates(self, template: str):
        """
        Feature: farmer-cli-completion, Property 14: Filename Template Rendering
        Validates: Requirements 6.2

        For any invalid template string, validate() SHALL return is_valid=False
        with a descriptive error message.
        """
        ft = FilenameTemplate()
        result = ft.validate(template)

        assert not result.is_valid, f"Invalid template '{template}' should be rejected"
        assert result.error is not None, "Error should not be None for invalid template"
        assert len(result.error) > 0, "Error message should not be empty"
