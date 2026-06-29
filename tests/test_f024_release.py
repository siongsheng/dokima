"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases.

Task 1: _bump_version unit tests.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import utils


# ── _bump_version ───────────────────────────────────

def test_bump_version_patch_increments_z():
    """patch: 1.2.1 → 1.2.2"""
    assert utils._bump_version("1.2.1", "patch") == "1.2.2"


def test_bump_version_minor_increments_y_and_resets_z():
    """minor: 1.2.1 → 1.3.0"""
    assert utils._bump_version("1.2.1", "minor") == "1.3.0"


def test_bump_version_major_increments_x_and_resets_y_z():
    """major: 1.2.1 → 2.0.0"""
    assert utils._bump_version("1.2.1", "major") == "2.0.0"


def test_bump_version_patch_no_carry():
    """patch: 1.2.9 → 1.2.10 (Z rolls, no carry to Y)"""
    assert utils._bump_version("1.2.9", "patch") == "1.2.10"


def test_bump_version_preserves_v_prefix():
    """Leading 'v' is preserved: v1.2.1 patch → v1.2.2"""
    assert utils._bump_version("v1.2.1", "patch") == "v1.2.2"


def test_bump_version_strips_whitespace():
    """Trailing whitespace/newlines are stripped."""
    assert utils._bump_version(" 1.2.1\n", "patch") == "1.2.2"


def test_bump_version_zero_to_one_minor():
    """0.0.1 minor → 0.1.0 (standard semver)"""
    assert utils._bump_version("0.0.1", "minor") == "0.1.0"


def test_bump_version_large_patch():
    """9.9.9 patch → 9.9.10 (not 10.0.0)"""
    assert utils._bump_version("9.9.9", "patch") == "9.9.10"


def test_bump_version_rejects_valid_but_unexpected_bump_types():
    """Invalid bump type (prepatch, prerelease, etc.) raises ValueError."""
    for bad in ("prepatch", "prerelease", "preminor", "premajor", "build", ""):
        with pytest.raises(ValueError):
            utils._bump_version("1.2.1", bad)
