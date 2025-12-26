"""
URL validation utilities for Farmer CLI.

This module provides functions for validating URLs, checking supported platforms,
and extracting video IDs from various video hosting services.
"""

import re
from typing import NamedTuple
from urllib.parse import parse_qs
from urllib.parse import urlparse


# Supported platforms with their URL patterns
SUPPORTED_PLATFORMS = {
    "youtube": {
        "domains": ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"],
        "patterns": [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})",
        ],
    },
    "vimeo": {
        "domains": ["vimeo.com", "www.vimeo.com", "player.vimeo.com"],
        "patterns": [
            r"vimeo\.com/(?:video/)?(\d+)",
            r"player\.vimeo\.com/video/(\d+)",
        ],
    },
    "direct": {
        "domains": [],  # Direct URLs don't have specific domains
        "patterns": [
            r".*\.(mp4|webm|mkv|avi|mov|flv|wmv|m4v)(\?.*)?$",
        ],
    },
}

# URL validation regex pattern
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


class VideoIdResult(NamedTuple):
    """Result of video ID extraction."""

    platform: str | None
    video_id: str | None
    success: bool
    error: str | None


class UrlValidationResult(NamedTuple):
    """Result of URL validation."""

    is_valid: bool
    error: str | None


def is_valid_url(url: str) -> UrlValidationResult:
    """
    Validate if a string is a valid HTTP/HTTPS URL.

    Parameters
    ----------
    url : str
        The URL string to validate.

    Returns
    -------
    UrlValidationResult
        A named tuple with is_valid (bool) and error (str | None).

    Examples
    --------
    >>> is_valid_url("https://www.youtube.com/watch?v=abc123")
    UrlValidationResult(is_valid=True, error=None)
    >>> is_valid_url("not-a-url")
    UrlValidationResult(is_valid=False, error="Invalid URL format")
    """
    if not url:
        return UrlValidationResult(is_valid=False, error="URL cannot be empty")

    if not isinstance(url, str):
        return UrlValidationResult(is_valid=False, error="URL must be a string")

    url = url.strip()

    # Check for dangerous schemes
    dangerous_schemes = ["javascript:", "data:", "file:", "vbscript:"]
    url_lower = url.lower()
    for scheme in dangerous_schemes:
        if url_lower.startswith(scheme):
            return UrlValidationResult(
                is_valid=False, error=f"Unsupported URL scheme: {scheme.rstrip(':')}"
            )

    # Check URL pattern
    if not URL_PATTERN.match(url):
        return UrlValidationResult(is_valid=False, error="Invalid URL format")

    # Try to parse the URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return UrlValidationResult(is_valid=False, error="Invalid URL structure")
    except Exception:
        return UrlValidationResult(is_valid=False, error="Failed to parse URL")

    return UrlValidationResult(is_valid=True, error=None)


def is_supported_platform(url: str) -> tuple[bool, str | None]:
    """
    Check if a URL is from a supported video platform.

    Parameters
    ----------
    url : str
        The URL to check.

    Returns
    -------
    tuple[bool, str | None]
        A tuple of (is_supported, platform_name).
        If not supported, platform_name is None.

    Examples
    --------
    >>> is_supported_platform("https://www.youtube.com/watch?v=abc123")
    (True, 'youtube')
    >>> is_supported_platform("https://example.com/video")
    (False, None)
    """
    # First validate the URL
    validation = is_valid_url(url)
    if not validation.is_valid:
        return (False, None)

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove port if present
        if ":" in domain:
            domain = domain.split(":")[0]

        # Check each platform
        for platform, config in SUPPORTED_PLATFORMS.items():
            # Check domain match
            if config["domains"]:
                if domain in config["domains"]:
                    return (True, platform)

            # Check pattern match for direct URLs
            if platform == "direct":
                for pattern in config["patterns"]:
                    if re.search(pattern, url, re.IGNORECASE):
                        return (True, platform)

        return (False, None)

    except Exception:
        return (False, None)


def extract_video_id(url: str) -> VideoIdResult:
    """
    Extract the video ID from a supported platform URL.

    Parameters
    ----------
    url : str
        The video URL to parse.

    Returns
    -------
    VideoIdResult
        A named tuple with platform, video_id, success, and error fields.

    Examples
    --------
    >>> extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    VideoIdResult(platform='youtube', video_id='dQw4w9WgXcQ', success=True, error=None)
    >>> extract_video_id("https://vimeo.com/123456789")
    VideoIdResult(platform='vimeo', video_id='123456789', success=True, error=None)
    """
    # Validate URL first
    validation = is_valid_url(url)
    if not validation.is_valid:
        return VideoIdResult(
            platform=None,
            video_id=None,
            success=False,
            error=validation.error,
        )

    # Check if platform is supported
    is_supported, platform = is_supported_platform(url)
    if not is_supported:
        return VideoIdResult(
            platform=None,
            video_id=None,
            success=False,
            error="URL is not from a supported platform",
        )

    # Handle direct video URLs
    if platform == "direct":
        # For direct URLs, use the filename as the ID
        try:
            parsed = urlparse(url)
            path = parsed.path
            filename = path.split("/")[-1]
            # Remove extension
            video_id = re.sub(r"\.(mp4|webm|mkv|avi|mov|flv|wmv|m4v)$", "", filename, flags=re.IGNORECASE)
            if video_id:
                return VideoIdResult(
                    platform=platform,
                    video_id=video_id,
                    success=True,
                    error=None,
                )
        except Exception:
            pass
        return VideoIdResult(
            platform=platform,
            video_id=None,
            success=False,
            error="Could not extract video ID from direct URL",
        )

    # Extract video ID using platform patterns
    config = SUPPORTED_PLATFORMS.get(platform, {})
    patterns = config.get("patterns", [])

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            video_id = match.group(1)
            return VideoIdResult(
                platform=platform,
                video_id=video_id,
                success=True,
                error=None,
            )

    # Special handling for YouTube URLs with query parameters
    if platform == "youtube":
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if "v" in query_params:
                video_id = query_params["v"][0]
                if len(video_id) == 11:
                    return VideoIdResult(
                        platform=platform,
                        video_id=video_id,
                        success=True,
                        error=None,
                    )
        except Exception:
            pass

    return VideoIdResult(
        platform=platform,
        video_id=None,
        success=False,
        error=f"Could not extract video ID from {platform} URL",
    )


def get_supported_platforms() -> list[str]:
    """
    Get a list of supported platform names.

    Returns
    -------
    list[str]
        List of supported platform names.
    """
    return list(SUPPORTED_PLATFORMS.keys())


def get_platform_domains(platform: str) -> list[str]:
    """
    Get the domains associated with a platform.

    Parameters
    ----------
    platform : str
        The platform name.

    Returns
    -------
    list[str]
        List of domains for the platform, or empty list if not found.
    """
    config = SUPPORTED_PLATFORMS.get(platform, {})
    return config.get("domains", [])
