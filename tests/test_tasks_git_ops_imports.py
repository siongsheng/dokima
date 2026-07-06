"""Tests for tasks.py imports — F041 Task 9: import from git_ops.py instead of utils.

Verifies that tasks.py imports git, _safe_run, and load_github_token from
git_ops module rather than from utils.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTasksGitOpsImports:
    """Verify tasks.py imports VCS functions from git_ops, not utils."""

    def test_tasks_imports_git_from_git_ops(self):
        """tasks.git should come from git_ops module, not utils."""
        import git_ops  # noqa: F401

        import tasks

        assert hasattr(tasks, "git"), "tasks.git should exist"
        assert tasks.git.__module__ == "git_ops", (
            f"tasks.git should be from git_ops, got {tasks.git.__module__}"
        )

    def test_tasks_imports_safe_run_from_git_ops(self):
        """tasks._safe_run should come from git_ops module, not utils."""
        import tasks

        assert hasattr(tasks, "_safe_run"), "tasks._safe_run should exist"
        assert tasks._safe_run.__module__ == "git_ops", (
            f"tasks._safe_run should be from git_ops, got {tasks._safe_run.__module__}"
        )

    def test_tasks_imports_load_github_token_from_git_ops(self):
        """tasks.load_github_token should come from git_ops module, not utils."""
        import tasks

        assert hasattr(tasks, "load_github_token"), "tasks.load_github_token should exist"
        assert tasks.load_github_token.__module__ == "git_ops", (
            f"tasks.load_github_token should be from git_ops, "
            f"got {tasks.load_github_token.__module__}"
        )

    def test_git_ops_module_exists_and_has_git_function(self):
        """git_ops module should exist with the git function."""
        import git_ops

        assert hasattr(git_ops, "git"), "git_ops should have git function"
        assert callable(git_ops.git), "git_ops.git should be callable"

    def test_git_ops_module_has_safe_run(self):
        """git_ops module should have _safe_run function."""
        import git_ops

        assert hasattr(git_ops, "_safe_run"), "git_ops should have _safe_run function"
        assert callable(git_ops._safe_run), "git_ops._safe_run should be callable"

    def test_git_ops_module_has_load_github_token(self):
        """git_ops module should have load_github_token function."""
        import git_ops

        assert hasattr(git_ops, "load_github_token"), (
            "git_ops should have load_github_token function"
        )
        assert callable(git_ops.load_github_token), (
            "git_ops.load_github_token should be callable"
        )
