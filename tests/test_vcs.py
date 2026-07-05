"""Tests for vcs.py — VCS abstraction layer."""
import os
import sys
import subprocess
import pytest
from unittest.mock import patch, MagicMock


# ── detect_vcs_backend() ────────────────────────────────────────────

class TestDetectVcsBackend:
    """Platform detection from git remote URL."""

    def test_github_ssh(self):
        """git@github.com:owner/repo.git → 'github', 'owner/repo'"""
        import vcs
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@github.com:owner/repo.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend == "github"
            assert vcs.REPO == "owner/repo"

    def test_github_https(self):
        """https://github.com/owner/repo.git → 'github', 'owner/repo'"""
        import vcs
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="https://github.com/owner/repo.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend == "github"

    def test_gitlab_ssh(self):
        """git@gitlab.com:group/project.git → 'gitlab', 'group/project'"""
        import vcs
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@gitlab.com:group/project.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend == "gitlab"
            assert vcs.REPO == "group/project"

    def test_gitlab_https(self):
        """https://gitlab.com/group/project.git → 'gitlab'"""
        import vcs
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="https://gitlab.com/group/project.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend == "gitlab"

    def test_gitlab_subgroup_ssh(self):
        """git@gitlab.com:group/subgroup/project.git → 'gitlab', full path"""
        import vcs
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@gitlab.com:group/subgroup/project.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend == "gitlab"
            assert vcs.REPO == "group/subgroup/project"

    def test_no_git_suffix(self):
        """Trailing .git absent → still matches"""
        import vcs
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="https://gitlab.com/team/proj\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend == "gitlab"

    def test_self_hosted_gitlab(self):
        """git@gitlab.internal.company.com:team/proj.git → 'gitlab'"""
        import vcs
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@gitlab.internal.company.com:team/proj.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend == "gitlab"

    def test_no_remote(self):
        """No git remote → returns None"""
        import vcs
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="fatal: not a git repository"
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend is None

    def test_unsupported_vcs(self):
        """Bitbucket remote → returns None"""
        import vcs
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@bitbucket.org:owner/repo.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend is None

    def test_never_raises(self):
        """detect_vcs_backend() never raises — returns str or None"""
        import vcs
        # Even if git command fails entirely, should not raise
        with patch.object(subprocess, 'run', side_effect=Exception("boom")):
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend is None


# ── parse_vcs_flag() ────────────────────────────────────────────────

class TestParseVcsFlag:
    """CLI --vcs flag parsing."""

    def test_vcs_flag_github(self):
        """--vcs github → returns 'github'"""
        import vcs
        with patch.object(sys, 'argv', ['dokima', '--vcs', 'github', 'run']):
            result = vcs.parse_vcs_flag()
            assert result == "github"

    def test_vcs_flag_gitlab(self):
        """--vcs gitlab → returns 'gitlab'"""
        import vcs
        with patch.object(sys, 'argv', ['dokima', '--vcs', 'gitlab']):
            result = vcs.parse_vcs_flag()
            assert result == "gitlab"

    def test_no_vcs_flag(self):
        """No --vcs flag → returns None"""
        import vcs
        with patch.object(sys, 'argv', ['dokima', 'run']):
            result = vcs.parse_vcs_flag()
            assert result is None

    def test_vcs_flag_absent_after_double_dash(self):
        """--vcs not present at all → returns None"""
        import vcs
        with patch.object(sys, 'argv', ['dokima', '--help']):
            result = vcs.parse_vcs_flag()
            assert result is None


# ── vcs_pr_create() ─────────────────────────────────────────────────

class TestVcsPrCreate:
    """PR/MR creation with correct CLI args per backend."""

    def test_github_pr_create(self):
        """GitHub → calls gh pr create with original args"""
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="https://github.com/owner/repo/pull/1", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_create("main", "feat/x", "Test PR", "Test body")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert args[0] == "gh"
            assert args[1] == "pr"
            assert args[2] == "create"
            assert "--base" in args
            assert "--head" in args
            assert "--title" in args
            assert "--body" in args

    def test_gitlab_mr_create(self):
        """GitLab → calls glab mr create with mapped args"""
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="https://gitlab.com/group/project/-/merge_requests/1", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_create("main", "feat/x", "Test MR", "Test body")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert args[0] == "glab"
            assert args[1] == "mr"
            assert args[2] == "create"
            assert "--target-branch" in args
            assert "--source-branch" in args
            assert "--title" in args
            assert "--description" in args


# ── vcs_pr_merge() ──────────────────────────────────────────────────

class TestVcsPrMerge:
    """PR/MR merge."""

    def test_github_merge(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Merged", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_merge(42)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "gh" in args
            assert "pr" in args
            assert "merge" in args

    def test_github_auto_merge(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_merge(42, auto=True)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--auto" in args

    def test_gitlab_merge(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Merged", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_merge(42)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "glab" in args
            assert "mr" in args
            assert "merge" in args

    def test_gitlab_auto_merge(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_merge(42, auto=True)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--when-pipeline-succeeds" in args


# ── vcs_pr_view() ───────────────────────────────────────────────────

class TestVcsPrView:
    """PR/MR view with JSON output."""

    def test_github_view(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout='{"state":"OPEN","merged":false}', stderr=""
            )
            stdout, stderr, rc = vcs.vcs_pr_view(42)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--json" in args

    def test_gitlab_view(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout='{"state":"opened","merged_at":null}', stderr=""
            )
            stdout, stderr, rc = vcs.vcs_pr_view(42)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "glab" in args
            assert "mr" in args
            assert "view" in args


# ── vcs_pr_list() ───────────────────────────────────────────────────

class TestVcsPrList:
    """PR/MR listing."""

    def test_github_list(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_list()
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--json" in args

    def test_gitlab_list(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_list()
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--output" in args or "json" in str(args).lower()


# ── vcs_pr_diff() ───────────────────────────────────────────────────

class TestVcsPrDiff:
    """PR/MR diff."""

    def test_github_diff(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="diff output", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_diff(42)
            assert rc == 0

    def test_github_diff_stat(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="stat output", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_diff(42, stat_only=True)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--stat" in args

    def test_gitlab_diff(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="diff output", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_diff(42)
            assert rc == 0


# ── Contract invariants ─────────────────────────────────────────────

class TestContractInvariants:
    """All vcs_*() functions return (stdout, stderr, returncode) tuple."""

    def test_vcs_return_type(self):
        import vcs
        for fn_name in ['vcs_pr_create', 'vcs_pr_merge', 'vcs_pr_view',
                        'vcs_pr_list', 'vcs_pr_diff']:
            fn = getattr(vcs, fn_name)
            import inspect
            sig = inspect.signature(fn)
            # Verify callable — actual return type tested in operation tests
            assert callable(fn), f"{fn_name} is not callable"


# ── vcs_issue_create() ──────────────────────────────────────────────

class TestVcsIssueCreate:
    """Issue creation with correct CLI args per backend."""

    def test_github_issue_create(self):
        """GitHub → calls gh issue create with --title, --body"""
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="https://github.com/owner/repo/issues/1", stderr="")
            stdout, stderr, rc = vcs.vcs_issue_create("Bug", "Something broke")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert args[0] == "gh"
            assert "issue" in args
            assert "create" in args
            assert "--title" in args
            assert "--body" in args

    def test_github_issue_create_with_labels(self):
        """GitHub → includes --label when labels provided"""
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_issue_create("Bug", "broke", labels="bug,urgent")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--label" in args
            assert "bug,urgent" in args

    def test_gitlab_issue_create(self):
        """GitLab → calls glab issue create with --description instead of --body"""
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_issue_create("Bug", "broke")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert args[0] == "glab"
            assert "issue" in args
            assert "create" in args
            assert "--description" in args


# ── vcs_issue_view() ────────────────────────────────────────────────

class TestVcsIssueView:
    """Issue view with JSON output."""

    def test_github_issue_view(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='{"title":"Bug"}', stderr="")
            stdout, stderr, rc = vcs.vcs_issue_view(1)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "gh" in args
            assert "issue" in args
            assert "view" in args
            assert "--json" in args

    def test_gitlab_issue_view(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='{"title":"Bug"}', stderr="")
            stdout, stderr, rc = vcs.vcs_issue_view(1)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "glab" in args
            assert "issue" in args
            assert "view" in args


# ── vcs_release_create() ────────────────────────────────────────────

class TestVcsReleaseCreate:
    """Release creation — GitHub only; GitLab errors."""

    def test_github_release(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Release created", stderr="")
            stdout, stderr, rc = vcs.vcs_release_create("v1.0", "v1.0", "main")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "gh" in args
            assert "release" in args
            assert "create" in args

    def test_github_release_generate_notes(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_release_create("v1.0", "v1.0", "main", generate_notes=True)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--generate-notes" in args

    def test_gitlab_release_errors(self):
        """GitLab → returns error, release is GitHub-only"""
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'):
            stdout, stderr, rc = vcs.vcs_release_create("v1.0", "v1.0", "main")
            assert rc != 0
            assert "release" in stderr.lower() or "github" in stderr.lower()


# ── vcs_repo_clone() ────────────────────────────────────────────────

class TestVcsRepoClone:
    """Repo cloning dispatch."""

    def test_github_clone(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'), \
             patch.object(vcs, 'REPO', 'owner/repo'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_repo_clone("owner/repo", "/tmp/clone")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "gh" in args
            assert "repo" in args
            assert "clone" in args

    def test_gitlab_clone(self):
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'gitlab'), \
             patch.object(vcs, 'VCS_TOKEN_ENV', 'GLAB_TOKEN'), \
             patch.object(vcs, 'REPO', 'group/project'), \
             patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_repo_clone("group/project", "/tmp/clone")
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "glab" in args
            assert "repo" in args
            assert "clone" in args
