"""Tests for filename_template.py module."""

import pytest


class TestFilenameTemplate:
    """Tests for FilenameTemplate class."""

    def test_init_default(self):
        """Test default initialization."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()

        assert template.template == "%(title)s.%(ext)s"

    def test_init_custom(self):
        """Test custom template initialization."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate("%(title)s - %(uploader)s.%(ext)s")

        assert template.template == "%(title)s - %(uploader)s.%(ext)s"


class TestRender:
    """Tests for render method."""

    def test_render_success(self):
        """Test successful render."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate("%(title)s.%(ext)s")
        result = template.render({"title": "Test Video", "ext": "mp4"})

        assert result.success
        assert result.filename == "Test_Video.mp4"
        assert result.error is None

    def test_render_empty_info(self):
        """Test render with empty video info."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template.render({})

        assert not result.success
        assert result.error == "Video info cannot be empty"

    def test_render_none_info(self):
        """Test render with None video info."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template.render(None)

        assert not result.success

    def test_render_with_none_values(self):
        """Test render with None values in video info."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate("%(title)s.%(ext)s")
        result = template.render({"title": None, "ext": "mp4"})

        assert result.success
        assert ".mp4" in result.filename

    def test_render_complex_template(self):
        """Test render with complex template."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate("%(title)s - %(uploader)s [%(id)s].%(ext)s")
        result = template.render({
            "title": "My Video",
            "uploader": "Channel",
            "id": "abc123",
            "ext": "mp4",
        })

        assert result.success
        assert "My_Video" in result.filename
        assert "Channel" in result.filename

    def test_render_invalid_template(self):
        """Test render with invalid template."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate("")
        result = template.render({"title": "Test", "ext": "mp4"})

        assert not result.success
        assert result.error is not None

    def test_render_missing_variable(self):
        """Test render with missing template variable."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate("%(title)s - %(custom_var)s.%(ext)s")
        result = template.render({"title": "Test", "ext": "mp4", "custom_var": ""})

        # Should succeed with empty string for missing var
        assert result.success

    def test_render_special_characters(self):
        """Test render with special characters in values."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate("%(title)s.%(ext)s")
        result = template.render({"title": "Test: Video <1>", "ext": "mp4"})

        assert result.success
        # Special chars should be replaced
        assert ":" not in result.filename
        assert "<" not in result.filename


class TestValidate:
    """Tests for validate method."""

    def test_validate_valid_template(self):
        """Test validation of valid template."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template.validate("%(title)s.%(ext)s")

        assert result.is_valid
        assert result.error is None

    def test_validate_empty_template(self):
        """Test validation of empty template."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template.validate("")

        assert not result.is_valid
        assert "empty" in result.error.lower()

    def test_validate_no_placeholder(self):
        """Test validation of template without placeholders."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template.validate("static_filename.mp4")

        assert not result.is_valid
        assert "placeholder" in result.error.lower()

    def test_validate_unclosed_placeholder(self):
        """Test validation of template with unclosed placeholder."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template.validate("%(title.%(ext)s")

        assert not result.is_valid

    def test_validate_malformed_placeholder(self):
        """Test validation of template with malformed placeholder."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template.validate("%(title)d.%(ext)s")

        assert not result.is_valid

    def test_validate_too_long(self):
        """Test validation of too long template."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        long_template = "%(title)s" + "x" * 500 + ".%(ext)s"
        result = template.validate(long_template)

        assert not result.is_valid
        assert "long" in result.error.lower()

    def test_validate_non_string(self):
        """Test validation of non-string template."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template.validate(123)

        assert not result.is_valid
        assert "string" in result.error.lower()


class TestSanitizeFilename:
    """Tests for _sanitize_filename method."""

    def test_sanitize_normal(self):
        """Test sanitizing normal filename."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template._sanitize_filename("test_video.mp4")

        assert result == "test_video.mp4"

    def test_sanitize_empty(self):
        """Test sanitizing empty filename."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template._sanitize_filename("")

        assert result == ""

    def test_sanitize_invalid_chars(self):
        """Test sanitizing filename with invalid characters."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template._sanitize_filename("test:video<1>.mp4")

        assert ":" not in result
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_multiple_underscores(self):
        """Test sanitizing filename with multiple underscores."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template._sanitize_filename("test___video.mp4")

        assert "___" not in result

    def test_sanitize_leading_trailing(self):
        """Test sanitizing filename with leading/trailing chars."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        result = template._sanitize_filename("  _test_video_  ")

        assert not result.startswith("_")
        assert not result.startswith(" ")
        assert not result.endswith("_")
        assert not result.endswith(" ")

    def test_sanitize_too_long(self):
        """Test sanitizing too long filename."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate, MAX_FILENAME_LENGTH

        template = FilenameTemplate()
        long_name = "a" * 300 + ".mp4"
        result = template._sanitize_filename(long_name)

        assert len(result) <= MAX_FILENAME_LENGTH

    def test_sanitize_too_long_preserves_extension(self):
        """Test that sanitizing preserves extension for long filenames."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        long_name = "a" * 300 + ".mp4"
        result = template._sanitize_filename(long_name)

        assert result.endswith(".mp4")


class TestGetVariables:
    """Tests for get_variables method."""

    def test_get_variables(self):
        """Test getting all variables."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate()
        variables = template.get_variables()

        assert isinstance(variables, dict)
        assert "title" in variables
        assert "ext" in variables
        assert "uploader" in variables


class TestGetRequiredVariables:
    """Tests for get_required_variables method."""

    def test_get_required_variables_simple(self):
        """Test getting required variables from simple template."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate("%(title)s.%(ext)s")
        required = template.get_required_variables()

        assert "title" in required
        assert "ext" in required
        assert len(required) == 2

    def test_get_required_variables_complex(self):
        """Test getting required variables from complex template."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        template = FilenameTemplate("%(title)s - %(uploader)s [%(id)s].%(ext)s")
        required = template.get_required_variables()

        assert "title" in required
        assert "uploader" in required
        assert "id" in required
        assert "ext" in required


class TestGetDefaultTemplate:
    """Tests for get_default_template class method."""

    def test_get_default_template(self):
        """Test getting default template."""
        from src.farmer_cli.utils.filename_template import FilenameTemplate

        default = FilenameTemplate.get_default_template()

        assert default == "%(title)s.%(ext)s"
