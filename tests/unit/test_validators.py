"""
Unit tests for farmer_cli.utils.validators module.

Tests the validation functions for various input types.

Feature: farmer-cli-completion
Requirements: 9.1, 9.3
"""

import pytest


class TestValidateJson:
    """Tests for validate_json function."""

    def test_valid_json_object(self):
        """Test that valid JSON object returns True."""
        from farmer_cli.utils.validators import validate_json

        assert validate_json('{"key": "value"}') is True

    def test_valid_json_array(self):
        """Test that valid JSON array returns True."""
        from farmer_cli.utils.validators import validate_json

        assert validate_json('[1, 2, 3]') is True

    def test_valid_json_string(self):
        """Test that valid JSON string returns True."""
        from farmer_cli.utils.validators import validate_json

        assert validate_json('"hello"') is True

    def test_valid_json_number(self):
        """Test that valid JSON number returns True."""
        from farmer_cli.utils.validators import validate_json

        assert validate_json('42') is True

    def test_valid_json_boolean(self):
        """Test that valid JSON boolean returns True."""
        from farmer_cli.utils.validators import validate_json

        assert validate_json('true') is True

    def test_valid_json_null(self):
        """Test that valid JSON null returns True."""
        from farmer_cli.utils.validators import validate_json

        assert validate_json('null') is True

    def test_invalid_json(self):
        """Test that invalid JSON returns False."""
        from farmer_cli.utils.validators import validate_json

        assert validate_json('{invalid}') is False

    def test_empty_string(self):
        """Test that empty string returns False."""
        from farmer_cli.utils.validators import validate_json

        assert validate_json('') is False

    def test_none_value(self):
        """Test that None returns False."""
        from farmer_cli.utils.validators import validate_json

        assert validate_json(None) is False


class TestValidateEmail:
    """Tests for validate_email function."""

    def test_valid_email(self):
        """Test that valid email returns True."""
        from farmer_cli.utils.validators import validate_email

        assert validate_email("user@example.com") is True

    def test_valid_email_with_subdomain(self):
        """Test that email with subdomain returns True."""
        from farmer_cli.utils.validators import validate_email

        assert validate_email("user@mail.example.com") is True

    def test_valid_email_with_plus(self):
        """Test that email with plus sign returns True."""
        from farmer_cli.utils.validators import validate_email

        assert validate_email("user+tag@example.com") is True

    def test_valid_email_with_dots(self):
        """Test that email with dots in local part returns True."""
        from farmer_cli.utils.validators import validate_email

        assert validate_email("first.last@example.com") is True

    def test_invalid_email_no_at(self):
        """Test that email without @ returns False."""
        from farmer_cli.utils.validators import validate_email

        assert validate_email("userexample.com") is False

    def test_invalid_email_no_domain(self):
        """Test that email without domain returns False."""
        from farmer_cli.utils.validators import validate_email

        assert validate_email("user@") is False

    def test_invalid_email_no_tld(self):
        """Test that email without TLD returns False."""
        from farmer_cli.utils.validators import validate_email

        assert validate_email("user@example") is False

    def test_empty_email(self):
        """Test that empty string returns False."""
        from farmer_cli.utils.validators import validate_email

        assert validate_email("") is False


class TestValidatePath:
    """Tests for validate_path function."""

    def test_valid_path(self):
        """Test that valid path returns True."""
        from farmer_cli.utils.validators import validate_path

        assert validate_path("/tmp/test") is True

    def test_relative_path(self):
        """Test that relative path returns True."""
        from farmer_cli.utils.validators import validate_path

        assert validate_path("./test/file.txt") is True

    def test_must_exist_existing_path(self, tmp_path):
        """Test that existing path with must_exist returns True."""
        from farmer_cli.utils.validators import validate_path

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        assert validate_path(str(test_file), must_exist=True) is True

    def test_must_exist_nonexistent_path(self):
        """Test that nonexistent path with must_exist returns False."""
        from farmer_cli.utils.validators import validate_path

        assert validate_path("/nonexistent/path/file.txt", must_exist=True) is False

    def test_must_be_dir_with_directory(self, tmp_path):
        """Test that directory with must_be_dir returns True."""
        from farmer_cli.utils.validators import validate_path

        assert validate_path(str(tmp_path), must_be_dir=True) is True

    def test_must_be_dir_with_file(self, tmp_path):
        """Test that file with must_be_dir returns False."""
        from farmer_cli.utils.validators import validate_path

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        assert validate_path(str(test_file), must_be_dir=True) is False

    def test_must_be_dir_nonexistent(self):
        """Test that nonexistent path with must_be_dir returns True (doesn't exist yet)."""
        from farmer_cli.utils.validators import validate_path

        assert validate_path("/nonexistent/dir", must_be_dir=True) is True


class TestValidatePositiveInt:
    """Tests for validate_positive_int function."""

    def test_positive_integer(self):
        """Test that positive integer returns True."""
        from farmer_cli.utils.validators import validate_positive_int

        assert validate_positive_int(5) is True

    def test_positive_integer_string(self):
        """Test that positive integer string returns True."""
        from farmer_cli.utils.validators import validate_positive_int

        assert validate_positive_int("10") is True

    def test_zero(self):
        """Test that zero returns False."""
        from farmer_cli.utils.validators import validate_positive_int

        assert validate_positive_int(0) is False

    def test_negative_integer(self):
        """Test that negative integer returns False."""
        from farmer_cli.utils.validators import validate_positive_int

        assert validate_positive_int(-5) is False

    def test_float(self):
        """Test that float is converted to int."""
        from farmer_cli.utils.validators import validate_positive_int

        assert validate_positive_int(5.9) is True

    def test_invalid_string(self):
        """Test that invalid string returns False."""
        from farmer_cli.utils.validators import validate_positive_int

        assert validate_positive_int("abc") is False

    def test_none(self):
        """Test that None returns False."""
        from farmer_cli.utils.validators import validate_positive_int

        assert validate_positive_int(None) is False


class TestValidatePort:
    """Tests for validate_port function."""

    def test_valid_port(self):
        """Test that valid port returns True."""
        from farmer_cli.utils.validators import validate_port

        assert validate_port(8080) is True

    def test_port_one(self):
        """Test that port 1 returns True."""
        from farmer_cli.utils.validators import validate_port

        assert validate_port(1) is True

    def test_port_max(self):
        """Test that port 65535 returns True."""
        from farmer_cli.utils.validators import validate_port

        assert validate_port(65535) is True

    def test_port_zero(self):
        """Test that port 0 returns False."""
        from farmer_cli.utils.validators import validate_port

        assert validate_port(0) is False

    def test_port_too_high(self):
        """Test that port > 65535 returns False."""
        from farmer_cli.utils.validators import validate_port

        assert validate_port(65536) is False

    def test_port_negative(self):
        """Test that negative port returns False."""
        from farmer_cli.utils.validators import validate_port

        assert validate_port(-1) is False

    def test_port_string(self):
        """Test that port string is converted."""
        from farmer_cli.utils.validators import validate_port

        assert validate_port("443") is True

    def test_port_invalid_string(self):
        """Test that invalid string returns False."""
        from farmer_cli.utils.validators import validate_port

        assert validate_port("abc") is False


class TestValidateUrl:
    """Tests for validate_url function."""

    def test_valid_http_url(self):
        """Test that valid HTTP URL returns True."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("http://example.com") is True

    def test_valid_https_url(self):
        """Test that valid HTTPS URL returns True."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("https://example.com") is True

    def test_url_with_path(self):
        """Test that URL with path returns True."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("https://example.com/path/to/page") is True

    def test_url_with_port(self):
        """Test that URL with port returns True."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("http://example.com:8080") is True

    def test_url_with_query(self):
        """Test that URL with query string returns True."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("https://example.com?key=value") is True

    def test_localhost_url(self):
        """Test that localhost URL returns True."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("http://localhost:3000") is True

    def test_ip_address_url(self):
        """Test that IP address URL returns True."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("http://192.168.1.1") is True

    def test_invalid_url_no_protocol(self):
        """Test that URL without protocol returns False."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("example.com") is False

    def test_invalid_url_ftp(self):
        """Test that FTP URL returns False."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("ftp://example.com") is False

    def test_empty_url(self):
        """Test that empty string returns False."""
        from farmer_cli.utils.validators import validate_url

        assert validate_url("") is False


class TestValidateVersion:
    """Tests for validate_version function."""

    def test_valid_version(self):
        """Test that valid version returns True."""
        from farmer_cli.utils.validators import validate_version

        assert validate_version("1.2.3") is True

    def test_version_with_prerelease(self):
        """Test that version with prerelease returns True."""
        from farmer_cli.utils.validators import validate_version

        assert validate_version("1.0.0-alpha") is True

    def test_version_with_build(self):
        """Test that version with build metadata returns True."""
        from farmer_cli.utils.validators import validate_version

        assert validate_version("1.0.0+build.123") is True

    def test_version_with_prerelease_and_build(self):
        """Test that version with both prerelease and build returns True."""
        from farmer_cli.utils.validators import validate_version

        assert validate_version("1.0.0-beta.1+build.456") is True

    def test_invalid_version_two_parts(self):
        """Test that two-part version returns False."""
        from farmer_cli.utils.validators import validate_version

        assert validate_version("1.2") is False

    def test_invalid_version_one_part(self):
        """Test that one-part version returns False."""
        from farmer_cli.utils.validators import validate_version

        assert validate_version("1") is False

    def test_invalid_version_letters(self):
        """Test that version with letters in main part returns False."""
        from farmer_cli.utils.validators import validate_version

        assert validate_version("a.b.c") is False

    def test_empty_version(self):
        """Test that empty string returns False."""
        from farmer_cli.utils.validators import validate_version

        assert validate_version("") is False


class TestValidateNonEmpty:
    """Tests for validate_non_empty function."""

    def test_non_empty_string(self):
        """Test that non-empty string returns True."""
        from farmer_cli.utils.validators import validate_non_empty

        assert validate_non_empty("hello") is True

    def test_empty_string(self):
        """Test that empty string returns False."""
        from farmer_cli.utils.validators import validate_non_empty

        assert validate_non_empty("") is False

    def test_whitespace_string(self):
        """Test that whitespace-only string returns False."""
        from farmer_cli.utils.validators import validate_non_empty

        assert validate_non_empty("   ") is False

    def test_none(self):
        """Test that None returns False."""
        from farmer_cli.utils.validators import validate_non_empty

        assert validate_non_empty(None) is False

    def test_non_empty_list(self):
        """Test that non-empty list returns True."""
        from farmer_cli.utils.validators import validate_non_empty

        assert validate_non_empty([1, 2, 3]) is True

    def test_empty_list(self):
        """Test that empty list returns False."""
        from farmer_cli.utils.validators import validate_non_empty

        assert validate_non_empty([]) is False

    def test_non_empty_dict(self):
        """Test that non-empty dict returns True."""
        from farmer_cli.utils.validators import validate_non_empty

        assert validate_non_empty({"key": "value"}) is True

    def test_empty_dict(self):
        """Test that empty dict returns False."""
        from farmer_cli.utils.validators import validate_non_empty

        assert validate_non_empty({}) is False

    def test_number(self):
        """Test that number returns True (no __len__)."""
        from farmer_cli.utils.validators import validate_non_empty

        assert validate_non_empty(42) is True


class TestValidateChoice:
    """Tests for validate_choice function."""

    def test_valid_choice(self):
        """Test that valid choice returns True."""
        from farmer_cli.utils.validators import validate_choice

        assert validate_choice("a", ["a", "b", "c"]) is True

    def test_invalid_choice(self):
        """Test that invalid choice returns False."""
        from farmer_cli.utils.validators import validate_choice

        assert validate_choice("d", ["a", "b", "c"]) is False

    def test_integer_choice(self):
        """Test that integer choice works."""
        from farmer_cli.utils.validators import validate_choice

        assert validate_choice(2, [1, 2, 3]) is True

    def test_none_choice(self):
        """Test that None choice works if in list."""
        from farmer_cli.utils.validators import validate_choice

        assert validate_choice(None, [None, "a", "b"]) is True

    def test_empty_choices(self):
        """Test that empty choices list returns False."""
        from farmer_cli.utils.validators import validate_choice

        assert validate_choice("a", []) is False


class TestValidateRange:
    """Tests for validate_range function."""

    def test_value_in_range(self):
        """Test that value in range returns True."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range(5, min_val=1, max_val=10) is True

    def test_value_at_min(self):
        """Test that value at min returns True."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range(1, min_val=1, max_val=10) is True

    def test_value_at_max(self):
        """Test that value at max returns True."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range(10, min_val=1, max_val=10) is True

    def test_value_below_min(self):
        """Test that value below min returns False."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range(0, min_val=1, max_val=10) is False

    def test_value_above_max(self):
        """Test that value above max returns False."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range(11, min_val=1, max_val=10) is False

    def test_only_min(self):
        """Test that only min constraint works."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range(100, min_val=1) is True

    def test_only_max(self):
        """Test that only max constraint works."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range(-100, max_val=0) is True

    def test_float_value(self):
        """Test that float value works."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range(5.5, min_val=5.0, max_val=6.0) is True

    def test_string_number(self):
        """Test that string number is converted."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range("5", min_val=1, max_val=10) is True

    def test_invalid_value(self):
        """Test that invalid value returns False."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range("abc", min_val=1, max_val=10) is False

    def test_none_value(self):
        """Test that None returns False."""
        from farmer_cli.utils.validators import validate_range

        assert validate_range(None, min_val=1, max_val=10) is False
