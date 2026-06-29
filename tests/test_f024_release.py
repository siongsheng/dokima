"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases.

Task 5: --release dispatch — needs do_release importable.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock


def _mock_all(panel):
    """Mock everything main() touches so it doesn't run the real pipeline."""
    panel._set_gh_token = MagicMock()
    panel.git = MagicMock(return_value=("", "", 0))
    panel.gh = MagicMock(return_value=("", "", 0))
    panel.load_key = MagicMock(return_value="test-key")
    panel.load_github_token = MagicMock(return_value="test-token")
    panel.detect_repo = MagicMock(return_value="test-owner/test-repo")
    panel.acquire_lock = MagicMock(return_value=(True, None))
    panel._cleanup_lock = MagicMock()
    panel._detect_default_branch = MagicMock(return_value="main")
    panel.detect_commands = MagicMock(return_value=("echo test", "echo build", "echo lint"))
    panel.run_pipeline = MagicMock()
    panel.spawn_agent = MagicMock()
    panel._validate_project_dir = MagicMock(return_value=True)
    # Also patch the module-level imports to prevent real calls
    panel._sync_modules = MagicMock()
    panel._load_fallback_config = MagicMock(return_value={})


def test_release_dispatches_to_do_release(panel, test_repo):
    """Task 5: --release patch dispatches to do_release with correct args."""
    old_argv = sys.argv
    try:
        sys.argv = ["dokima", "--release", "patch", test_repo]
        _mock_all(panel)
        mock_do_release = MagicMock()
        panel.do_release = mock_do_release

        panel.main()

        mock_do_release.assert_called_once()
        args, kwargs = mock_do_release.call_args
        assert args[0] == "patch", f"Expected bump='patch', got {args[0]}"
        assert os.path.abspath(args[1]) == os.path.abspath(test_repo), \
            f"Expected project_dir={test_repo}, got {args[1]}"
    finally:
        sys.argv = old_argv


def test_release_minor_dispatches_correctly(panel, test_repo):
    """--release minor passes 'minor' as bump type."""
    old_argv = sys.argv
    try:
        sys.argv = ["dokima", "--release", "minor", test_repo]
        _mock_all(panel)
        mock_do_release = MagicMock()
        panel.do_release = mock_do_release

        panel.main()

        args, kwargs = mock_do_release.call_args
        assert args[0] == "minor"
    finally:
        sys.argv = old_argv


def test_release_major_dispatches_correctly(panel, test_repo):
    """--release major passes 'major' as bump type."""
    old_argv = sys.argv
    try:
        sys.argv = ["dokima", "--release", "major", test_repo]
        _mock_all(panel)
        mock_do_release = MagicMock()
        panel.do_release = mock_do_release

        panel.main()

        args, kwargs = mock_do_release.call_args
        assert args[0] == "major"
    finally:
        sys.argv = old_argv


def test_release_uses_cwd_when_no_project_dir(panel, test_repo):
    """--release without project_dir uses cwd from panel.PROJECT_DIR."""
    old_argv = sys.argv
    old_cwd = os.getcwd()
    try:
        sys.argv = ["dokima", "--release", "patch"]
        os.chdir(test_repo)
        _mock_all(panel)
        mock_do_release = MagicMock()
        panel.do_release = mock_do_release

        panel.main()

        args, kwargs = mock_do_release.call_args
        assert os.path.abspath(args[1]) == os.path.abspath(test_repo), \
            f"Expected project_dir={test_repo}, got {args[1]}"
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
