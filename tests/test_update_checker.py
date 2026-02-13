"""Tests for update_checker module."""

from maestro.update_checker import compare_versions, parse_version


def test_parse_version_simple():
    """Test parsing simple version strings."""
    assert parse_version("1.3.0") == (1, 3, 0)
    assert parse_version("2.0.0") == (2, 0, 0)
    assert parse_version("0.1.5") == (0, 1, 5)


def test_parse_version_with_v_prefix():
    """Test parsing version strings with 'v' prefix."""
    assert parse_version("v1.3.0") == (1, 3, 0)
    assert parse_version("v2.0.0") == (2, 0, 0)


def test_parse_version_invalid():
    """Test parsing invalid version strings."""
    assert parse_version("invalid") == (0, 0, 0)
    assert parse_version("") == (0, 0, 0)
    assert parse_version("1.a.0") == (0, 0, 0)


def test_compare_versions_minor_update():
    """Test comparing versions with minor update."""
    assert compare_versions("1.2.0", "1.3.0") is True
    assert compare_versions("1.3.0", "1.2.0") is False


def test_compare_versions_major_update():
    """Test comparing versions with major update."""
    assert compare_versions("1.3.0", "2.0.0") is True
    assert compare_versions("2.0.0", "1.3.0") is False


def test_compare_versions_patch_update():
    """Test comparing versions with patch update."""
    assert compare_versions("1.3.0", "1.3.1") is True
    assert compare_versions("1.3.1", "1.3.0") is False


def test_compare_versions_same():
    """Test comparing identical versions."""
    assert compare_versions("1.3.0", "1.3.0") is False
    assert compare_versions("2.0.0", "2.0.0") is False


def test_compare_versions_with_v_prefix():
    """Test comparing versions with 'v' prefix."""
    assert compare_versions("v1.2.0", "v1.3.0") is True
    assert compare_versions("1.2.0", "v1.3.0") is True
    assert compare_versions("v1.2.0", "1.3.0") is True
