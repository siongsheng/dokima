"""Tests for git_ops.py — git/GitHub wrapper functions extracted from utils.py.

Verifies:
- git_ops module exists with expected functions
- utils.py re-exports git_ops functions (backward compat)
- git() works correctly in a real repo
"""

import os
import subprocess
import pytest

from conftest import _load_panel as _load


class TestGitOpsModule:
    """Verify git_ops.py module structure."""

    def test_module_importable(self):
        """git_ops module can be imported."""
        import git_ops

        assert git_ops is not None

    def test_has_git(self):
        """git_ops exports git()."""
        import git_ops

        assert hasattr(git_ops, "git")
        assert callable(git_ops.git)

    def test_has_gh(self):
        """git_ops exports gh()."""
        import git_ops

        assert hasattr(git_ops, "gh")
        assert callable(git_ops.gh)

    def test_has_detect_repo(self):
        """git_ops exports detect_repo()."""
        import git_ops

        assert hasattr(git_ops, "detect_repo")
        assert callable(git_ops.detect_repo)

    def test_has_set_gh_token(self):
        """git_ops exports _set_gh_token()."""
        import git_ops

        assert hasattr(git_ops, "_set_gh_token")
        assert callable(git_ops._set_gh_token)

    def test_has_detect_default_branch(self):
        """git_ops exports _detect_default_branch()."""
        import git_ops

        assert hasattr(git_ops, "_detect_default_branch")
        assert callable(git_ops._detect_default_branch)

    def test_has_load_key(self):
        """git_ops exports load_key()."""
        import git_ops

        assert hasattr(git_ops, "load_key")
        assert callable(git_ops.load_key)

    def test_has_load_github_token(self):
        """git_ops exports load_github_token()."""
        import git_ops

        assert hasattr(git_ops, "load_github_token")
        assert callable(git_ops.load_github_token)

    def test_has_safe_run(self):
        """git_ops exports _safe_run()."""
        import git_ops

        assert hasattr(git_ops, "_safe_run")
        assert callable(git_ops._safe_run)

    def test_has_detect_commands(self):
        """git_ops exports detect_commands()."""
        import git_ops

        assert hasattr(git_ops, "detect_commands")
        assert callable(git_ops.detect_commands)

    def test_has_detect_referenced_repo(self):
        """git_ops exports _detect_referenced_repo()."""
        import git_ops

        assert hasattr(git_ops, "_detect_referenced_repo")
        assert callable(git_ops._detect_referenced_repo)

    def test_has_set_vcs_token(self):
        """git_ops exports _set_vcs_token()."""
        import git_ops

        assert hasattr(git_ops, "_set_vcs_token")
        assert callable(git_ops._set_vcs_token)

    def test_has_load_token_from_env_file(self):
        """git_ops exports _load_token_from_env_file()."""
        import git_ops

        assert hasattr(git_ops, "_load_token_from_env_file")
        assert callable(git_ops._load_token_from_env_file)

    def test_has_try_auto_merge(self):
        """git_ops exports try_auto_merge()."""
        import git_ops

        assert hasattr(git_ops, "try_auto_merge")
        assert callable(git_ops.try_auto_merge)

    def test_has_supplement_pr_sections(self):
        """git_ops exports _supplement_pr_sections()."""
        import git_ops

        assert hasattr(git_ops, "_supplement_pr_sections")
        assert callable(git_ops._supplement_pr_sections)


class TestUtilsReExport:
    """Verify utils.py re-exports git_ops functions for backward compat."""

    def test_utils_has_git(self):
        """utils.git exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "git")
        assert callable(utils.git)

    def test_utils_has_gh(self):
        """utils.gh exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "gh")
        assert callable(utils.gh)

    def test_utils_has_detect_repo(self):
        """utils.detect_repo exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "detect_repo")
        assert callable(utils.detect_repo)

    def test_utils_has_set_gh_token(self):
        """utils._set_gh_token exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "_set_gh_token")
        assert callable(utils._set_gh_token)

    def test_utils_has_detect_default_branch(self):
        """utils._detect_default_branch exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "_detect_default_branch")
        assert callable(utils._detect_default_branch)

    def test_utils_has_load_key(self):
        """utils.load_key exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "load_key")
        assert callable(utils.load_key)

    def test_utils_has_load_github_token(self):
        """utils.load_github_token exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "load_github_token")
        assert callable(utils.load_github_token)

    def test_utils_has_safe_run(self):
        """utils._safe_run exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "_safe_run")
        assert callable(utils._safe_run)

    def test_utils_has_detect_commands(self):
        """utils.detect_commands exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "detect_commands")
        assert callable(utils.detect_commands)

    def test_utils_has_try_auto_merge(self):
        """utils.try_auto_merge exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "try_auto_merge")
        assert callable(utils.try_auto_merge)

    def test_utils_has_set_vcs_token(self):
        """utils._set_vcs_token exists (re-exported from git_ops)."""
        import utils

        assert hasattr(utils, "_set_vcs_token")
        assert callable(utils._set_vcs_token)


class TestGitFunction:
    """Functional tests for git()."""

    def test_git_rev_parse(self, panel, tmpdir):
        """git() works in a real repo via the panel fixture."""
        project_dir = os.path.join(str(tmpdir), "git-test")
        os.makedirs(project_dir)
        subprocess.run(
            ["git", "init", project_dir],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        panel._utils.PROJECT_DIR = project_dir
        stdout, stderr, rc = panel.git("rev-parse", "--git-dir")
        assert rc == 0
        assert ".git" in stdout

    def test_git_in_nongit_dir(self, panel, tmpdir):
        """git() returns non-zero in a non-git directory."""
        panel._utils.PROJECT_DIR = str(tmpdir)
        stdout, stderr, rc = panel.git("status")
        assert rc != 0

    def test_git_version_from_utils(self):
        """git() is callable directly from utils module."""
        import utils

        stdout, stderr, rc = utils.git("--version")
        assert rc == 0
        assert "git version" in stdout
