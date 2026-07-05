"""Tests for F037: Blocker Resolution Tracking."""
import subprocess
from unittest.mock import MagicMock, patch

import pytest


# ── Task 1: vcs_pr_update_body() ────────────────────────────────────

class TestVcsPrUpdateBody:
    """VCS-agnostic PR body update."""

    def test_vcs_pr_update_body_github(self):
        """GitHub → calls gh api PATCH with correct args."""
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_update_body(42, "Updated body")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert args[0] == "gh"
            assert args[1] == "api"
            assert "repos/owner/repo/pulls/42" in args
            assert "--method" in args
            assert "PATCH" in args
            assert "-f" in args
            assert "body=Updated body" in args

    def test_vcs_pr_update_body_gitlab(self):
        """GitLab → calls glab mr update with correct args."""
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_update_body(42, "Updated body")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert args[0] == "glab"
            assert args[1] == "mr"
            assert args[2] == "update"
            assert "42" in args
            assert "--description" in args
            assert "Updated body" in args
