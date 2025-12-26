"""
Filename template utility for Farmer CLI.

This module provides functionality for generating filenames from templates
with variable substitution, supporting video metadata placeholders.
"""

import re
import string
from typing import Any
from typing import NamedTuple


# Characters that are invalid in filenames across different operating systems
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

# Maximum filename length (conservative for cross-platform compatibility)
MAX_FILENAME_LENGTH = 200

# Default template
DEFAULT_TEMPLATE = "%(title)s.%(ext)s"


class TemplateValidationResult(NamedTuple):
    """Result of template validation."""

    is_valid: bool
    error: str | None


class RenderResult(NamedTuple):
    """Result of filename rendering."""

    filename: str | None
    success: bool
    error: str | None


class FilenameTemplate:
    """
    Handles filename templating with variable substitution.

    Supports yt-dlp style template variables for generating filenames
    from video metadata.

    Parameters
    ----------
    template : str, optional
        The template string with %(variable)s placeholders.
        Defaults to "%(title)s.%(ext)s".

    Examples
    --------
    >>> template = FilenameTemplate("%(title)s - %(uploader)s.%(ext)s")
    >>> result = template.render({"title": "My Video", "uploader": "Channel", "ext": "mp4"})
    >>> result.filename
    'My Video - Channel.mp4'
    """

    # Supported template variables with descriptions
    VARIABLES = {
        "title": "Video title",
        "uploader": "Channel/uploader name",
        "upload_date": "Upload date (YYYYMMDD)",
        "id": "Video ID",
        "ext": "File extension",
        "playlist": "Playlist name",
        "playlist_index": "Position in playlist",
        "duration": "Video duration in seconds",
        "view_count": "Number of views",
        "like_count": "Number of likes",
        "channel": "Channel name (alias for uploader)",
        "channel_id": "Channel ID",
        "description": "Video description",
        "timestamp": "Unix timestamp",
        "resolution": "Video resolution",
        "fps": "Frames per second",
        "format_id": "Format identifier",
    }

    def __init__(self, template: str = DEFAULT_TEMPLATE):
        """
        Initialize the filename template.

        Parameters
        ----------
        template : str
            The template string with %(variable)s placeholders.
        """
        self.template = template

    def render(self, video_info: dict[str, Any]) -> RenderResult:
        """
        Render a filename from the template and video information.

        Parameters
        ----------
        video_info : dict[str, Any]
            Dictionary containing video metadata with keys matching
            template variables.

        Returns
        -------
        RenderResult
            A named tuple with filename, success, and error fields.

        Examples
        --------
        >>> template = FilenameTemplate("%(title)s.%(ext)s")
        >>> result = template.render({"title": "Test Video", "ext": "mp4"})
        >>> result.filename
        'Test Video.mp4'
        """
        if not video_info:
            return RenderResult(
                filename=None,
                success=False,
                error="Video info cannot be empty",
            )

        # Validate template first
        validation = self.validate(self.template)
        if not validation.is_valid:
            return RenderResult(
                filename=None,
                success=False,
                error=validation.error,
            )

        try:
            # Create a copy with string values and defaults for missing keys
            safe_info = {}
            for key in self.VARIABLES:
                value = video_info.get(key, "")
                # Convert to string and handle None
                if value is None:
                    value = ""
                safe_info[key] = str(value)

            # Also include any extra keys from video_info
            for key, value in video_info.items():
                if key not in safe_info:
                    if value is None:
                        value = ""
                    safe_info[key] = str(value)

            # Perform template substitution
            try:
                filename = self.template % safe_info
            except KeyError as e:
                return RenderResult(
                    filename=None,
                    success=False,
                    error=f"Missing template variable: {e}",
                )
            except ValueError as e:
                return RenderResult(
                    filename=None,
                    success=False,
                    error=f"Invalid template format: {e}",
                )

            # Sanitize the filename
            filename = self._sanitize_filename(filename)

            # Check for empty result
            if not filename or filename.isspace():
                return RenderResult(
                    filename=None,
                    success=False,
                    error="Rendered filename is empty",
                )

            return RenderResult(
                filename=filename,
                success=True,
                error=None,
            )

        except Exception as e:
            return RenderResult(
                filename=None,
                success=False,
                error=f"Failed to render filename: {e}",
            )

    def validate(self, template: str) -> TemplateValidationResult:
        """
        Validate a template string.

        Parameters
        ----------
        template : str
            The template string to validate.

        Returns
        -------
        TemplateValidationResult
            A named tuple with is_valid and error fields.

        Examples
        --------
        >>> FilenameTemplate().validate("%(title)s.%(ext)s")
        TemplateValidationResult(is_valid=True, error=None)
        >>> FilenameTemplate().validate("")
        TemplateValidationResult(is_valid=False, error="Template cannot be empty")
        """
        if not template:
            return TemplateValidationResult(
                is_valid=False,
                error="Template cannot be empty",
            )

        if not isinstance(template, str):
            return TemplateValidationResult(
                is_valid=False,
                error="Template must be a string",
            )

        # Check for at least one variable placeholder
        placeholder_pattern = r"%\([a-zA-Z_][a-zA-Z0-9_]*\)s"
        if not re.search(placeholder_pattern, template):
            return TemplateValidationResult(
                is_valid=False,
                error="Template must contain at least one %(variable)s placeholder",
            )

        # Check for malformed placeholders
        # Look for % not followed by valid placeholder pattern or %%
        # Valid: %(name)s or %%
        # Invalid: %( without closing, %(name) without s, bare %

        # First, temporarily remove valid placeholders to check for malformed ones
        temp = re.sub(r"%\([a-zA-Z_][a-zA-Z0-9_]*\)s", "", template)
        temp = re.sub(r"%%", "", temp)  # Remove escaped %

        # Now check if there are any remaining % that indicate malformed placeholders
        if "%" in temp:
            # Check if it's a malformed placeholder pattern
            if re.search(r"%\([^)]*$", temp):  # Unclosed parenthesis
                return TemplateValidationResult(
                    is_valid=False,
                    error="Template contains unclosed placeholder",
                )
            if re.search(r"%\([^)]*\)[^s]", temp):  # Missing 's' suffix
                return TemplateValidationResult(
                    is_valid=False,
                    error="Template contains malformed placeholder (missing 's' suffix)",
                )
            if re.search(r"%[^(%]", temp):  # % not followed by ( or %
                return TemplateValidationResult(
                    is_valid=False,
                    error="Template contains invalid % character",
                )

        # Extract all variable names from template
        var_pattern = r"%\(([a-zA-Z_][a-zA-Z0-9_]*)\)s"
        variables = re.findall(var_pattern, template)

        # Check for unknown variables (warning, not error)
        unknown_vars = [v for v in variables if v not in self.VARIABLES]
        if unknown_vars:
            # We allow unknown variables but they must be provided in video_info
            pass

        # Check template length (rough estimate)
        if len(template) > MAX_FILENAME_LENGTH * 2:
            return TemplateValidationResult(
                is_valid=False,
                error="Template is too long",
            )

        return TemplateValidationResult(is_valid=True, error=None)

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing invalid characters.

        Parameters
        ----------
        filename : str
            The filename to sanitize.

        Returns
        -------
        str
            The sanitized filename.
        """
        if not filename:
            return ""

        # Remove invalid characters
        sanitized = re.sub(INVALID_FILENAME_CHARS, "_", filename)

        # Replace multiple underscores/spaces with single ones
        sanitized = re.sub(r"[_\s]+", "_", sanitized)

        # Remove leading/trailing underscores and spaces
        sanitized = sanitized.strip("_ ")

        # Truncate if too long (preserve extension if present)
        if len(sanitized) > MAX_FILENAME_LENGTH:
            # Try to preserve extension
            if "." in sanitized:
                name, ext = sanitized.rsplit(".", 1)
                max_name_len = MAX_FILENAME_LENGTH - len(ext) - 1
                if max_name_len > 0:
                    sanitized = f"{name[:max_name_len]}.{ext}"
                else:
                    sanitized = sanitized[:MAX_FILENAME_LENGTH]
            else:
                sanitized = sanitized[:MAX_FILENAME_LENGTH]

        return sanitized

    def get_variables(self) -> dict[str, str]:
        """
        Get all supported template variables with descriptions.

        Returns
        -------
        dict[str, str]
            Dictionary mapping variable names to descriptions.
        """
        return self.VARIABLES.copy()

    def get_required_variables(self) -> list[str]:
        """
        Get the list of variables required by the current template.

        Returns
        -------
        list[str]
            List of variable names used in the template.
        """
        var_pattern = r"%\(([a-zA-Z_][a-zA-Z0-9_]*)\)s"
        return re.findall(var_pattern, self.template)

    @classmethod
    def get_default_template(cls) -> str:
        """
        Get the default filename template.

        Returns
        -------
        str
            The default template string.
        """
        return DEFAULT_TEMPLATE
