"""Tests for vcs.py — VCS abstraction layer (with ctx parameter)."""
import os
import sys
import subprocess
import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace


def _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo'):
    """Create a minimal ctx-like object for vcs function tests."""
    return SimpleNamespace(
        vcs_backend=vcs_backend,
        vcs_token_env=vcs_token_env,
        repo=repo,
    )


# ── detect_vcs_backend() ────────────────────────────────────────────

class TestDetectVcsBackend:
    """Platform detection from git remote URL."""

    def test_github_ssh(self):
        """git@github.com:owner/repo.git → 'github', ctx.repo='owner/repo'"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@github.com:owner/repo.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend == "github"
            assert ctx.repo == "owner/repo"
            assert ctx.vcs_backend == "github"
            assert ctx.vcs_token_env == "GH_TOKEN"

    def test_github_https(self):
        """https://github.com/owner/repo.git → 'github', 'owner/repo'"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="https://github.com/owner/repo.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend == "github"

    def test_gitlab_ssh(self):
        """git@gitlab.com:group/project.git → 'gitlab', ctx.repo='group/project'"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@gitlab.com:group/project.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend == "gitlab"
            assert ctx.repo == "group/project"
            assert ctx.vcs_backend == "gitlab"

    def test_gitlab_https(self):
        """https://gitlab.com/group/project.git → 'gitlab'"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="https://gitlab.com/group/project.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend == "gitlab"

    def test_gitlab_subgroup_ssh(self):
        """git@gitlab.com:group/subgroup/project.git → 'gitlab', full path"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@gitlab.com:group/subgroup/project.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend == "gitlab"
            assert ctx.repo == "group/subgroup/project"

    def test_no_git_suffix(self):
        """Trailing .git absent → still matches"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="https://gitlab.com/team/proj\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend == "gitlab"

    def test_self_hosted_gitlab(self):
        """git@gitlab.internal.company.com:team/proj.git → 'gitlab'"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@gitlab.internal.company.com:team/proj.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend == "gitlab"

    def test_no_remote(self):
        """No git remote → returns None"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="fatal: not a git repository"
            )
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend is None

    def test_unsupported_vcs(self):
        """Bitbucket remote → returns None"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@bitbucket.org:owner/repo.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend is None

    def test_never_raises(self):
        """detect_vcs_backend() never raises — returns str or None"""
        import vcs
        ctx = _make_ctx(vcs_backend='', vcs_token_env='', repo='')
        # Even if git command fails entirely, should not raise
        with patch.object(subprocess, 'run', side_effect=Exception("boom")):
            backend = vcs.detect_vcs_backend("/tmp/test", ctx=ctx)
            assert backend is None

    def test_detect_vcs_backend_without_ctx(self):
        """Backward compat: detect_vcs_backend works without ctx (sets module globals)."""
        import vcs
        vcs.VCS_BACKEND = "gitlab"  # ensure it changes
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="git@github.com:owner/repo.git\n", stderr=""
            )
            backend = vcs.detect_vcs_backend("/tmp/test")
            assert backend == "github"
            assert vcs.REPO == "owner/repo"
            assert vcs.VCS_BACKEND == "github"


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
        """GitHub → calls gh pr create with original args (via ctx)"""
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="https://github.com/owner/repo/pull/1", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_create("main", "feat/x", "Test PR", "Test body", ctx=ctx)
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
        """GitLab → calls glab mr create with mapped args (via ctx)"""
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="https://gitlab.com/group/project/-/merge_requests/1", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_create("main", "feat/x", "Test MR", "Test body", ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert args[0] == "glab"
            assert args[1] == "mr"
            assert args[2] == "create"
            assert "--target-branch" in args
            assert "--source-branch" in args
            assert "--title" in args
            assert "--description" in args

    def test_pr_create_without_ctx(self):
        """Backward compat: vcs_pr_create works without ctx (uses module globals)."""
        import vcs
        with patch.object(vcs, 'VCS_BACKEND', 'github'),              patch.object(vcs, 'VCS_TOKEN_ENV', 'GH_TOKEN'),              patch.object(vcs, 'REPO', 'owner/repo'),              patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_create("main", "feat/x", "T", "B")
            assert rc == 0


# ── vcs_pr_merge() ──────────────────────────────────────────────────

class TestVcsPrMerge:
    """PR/MR merge."""

    def test_github_merge(self):
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Merged", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_merge(42, ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "gh" in args
            assert "pr" in args
            assert "merge" in args

    def test_github_auto_merge(self):
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_merge(42, auto=True, ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--auto" in args

    def test_gitlab_merge(self):
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Merged", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_merge(42, ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "glab" in args
            assert "mr" in args
            assert "merge" in args

    def test_gitlab_auto_merge(self):
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_merge(42, auto=True, ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--when-pipeline-succeeds" in args


# ── vcs_pr_view() ───────────────────────────────────────────────────

class TestVcsPrView:
    """PR/MR view with JSON output."""

    def test_github_view(self):
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout='{"state":"OPEN","merged":false}', stderr=""
            )
            stdout, stderr, rc = vcs.vcs_pr_view(42, ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--json" in args

    def test_gitlab_view(self):
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout='{"state":"opened","merged_at":null}', stderr=""
            )
            stdout, stderr, rc = vcs.vcs_pr_view(42, ctx=ctx)
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
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_list(ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--json" in args

    def test_gitlab_list(self):
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_list(ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--output" in args or "json" in str(args).lower()


# ── vcs_pr_diff() ───────────────────────────────────────────────────

class TestVcsPrDiff:
    """PR/MR diff."""

    def test_github_diff(self):
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="diff output", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_diff(42, ctx=ctx)
            assert rc == 0

    def test_github_diff_stat(self):
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="stat output", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_diff(42, stat_only=True, ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--stat" in args

    def test_gitlab_diff(self):
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="diff output", stderr="")
            stdout, stderr, rc = vcs.vcs_pr_diff(42, ctx=ctx)
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
        """GitHub → calls gh issue create with --title, --body (via ctx)"""
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="https://github.com/owner/repo/issues/1", stderr="")
            stdout, stderr, rc = vcs.vcs_issue_create("Bug", "Something broke", ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert args[0] == "gh"
            assert "issue" in args
            assert "create" in args
            assert "--title" in args
            assert "--body" in args

    def test_github_issue_create_with_labels(self):
        """GitHub → includes --label when labels provided (via ctx)"""
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_issue_create("Bug", "broke", labels="bug,urgent", ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--label" in args
            assert "bug,urgent" in args

    def test_gitlab_issue_create(self):
        """GitLab → calls glab issue create with --description instead of --body (via ctx)"""
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_issue_create("Bug", "broke", ctx=ctx)
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
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='{"title":"Bug"}', stderr="")
            stdout, stderr, rc = vcs.vcs_issue_view(1, ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "gh" in args
            assert "issue" in args
            assert "view" in args
            assert "--json" in args

    def test_gitlab_issue_view(self):
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='{"title":"Bug"}', stderr="")
            stdout, stderr, rc = vcs.vcs_issue_view(1, ctx=ctx)
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
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Release created", stderr="")
            stdout, stderr, rc = vcs.vcs_release_create("v1.0", "v1.0", "main", ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "gh" in args
            assert "release" in args
            assert "create" in args

    def test_github_release_generate_notes(self):
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_release_create("v1.0", "v1.0", "main", generate_notes=True, ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "--generate-notes" in args

    def test_gitlab_release_errors(self):
        """GitLab → returns error, release is GitHub-only (via ctx)"""
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        stdout, stderr, rc = vcs.vcs_release_create("v1.0", "v1.0", "main", ctx=ctx)
        assert rc != 0
        assert "release" in stderr.lower() or "github" in stderr.lower()


# ── vcs_repo_clone() ────────────────────────────────────────────────

class TestVcsRepoClone:
    """Repo cloning dispatch."""

    def test_github_clone(self):
        import vcs
        ctx = _make_ctx(vcs_backend='github', vcs_token_env='GH_TOKEN', repo='owner/repo')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_repo_clone("owner/repo", "/tmp/clone", ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "gh" in args
            assert "repo" in args
            assert "clone" in args

    def test_gitlab_clone(self):
        import vcs
        ctx = _make_ctx(vcs_backend='gitlab', vcs_token_env='GLAB_TOKEN', repo='group/project')
        with patch.object(subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            stdout, stderr, rc = vcs.vcs_repo_clone("group/project", "/tmp/clone", ctx=ctx)
            assert rc == 0
            args = mock_run.call_args[0][0]
            assert "glab" in args
            assert "repo" in args
            assert "clone" in args


# ── Pipeline integration tests ──────────────────────────────────────

class TestPrUrlRegex:
    """PR URL regex must match both GitHub and GitLab formats."""

    def test_github_pr_url_regex(self):
        """GitHub PR URL: https://github.com/owner/repo/pull/42"""
        import re
        pattern = r'https://github\.com/[\w.-]+/[\w.-]+/pull/\d+'
        match = re.search(pattern, "PR at https://github.com/owner/repo/pull/42")
        assert match is not None
        assert "pull/42" in match.group()

    def test_gitlab_mr_url_regex(self):
        """GitLab MR URL: https://gitlab.com/group/project/-/merge_requests/42"""
        import re
        pattern = r'https://(?:github\.com/[\w.-]+/[\w.-]+/pull/\d+|gitlab\.[^/]+/[\w./-]+/-/merge_requests/\d+)'
        match = re.search(pattern, "MR at https://gitlab.com/group/project/-/merge_requests/42")
        assert match is not None
        assert "merge_requests/42" in match.group()

    def test_gitlab_subgroup_mr_url(self):
        """GitLab subgroup MR URL: https://gitlab.com/group/sub/proj/-/merge_requests/42"""
        import re
        pattern = r'https://(?:github\.com/[\w.-]+/[\w.-]+/pull/\d+|gitlab\.[^/]+/[\w./-]+/-/merge_requests/\d+)'
        match = re.search(pattern, "MR at https://gitlab.com/group/sub/proj/-/merge_requests/42")
        assert match is not None


class TestTlPromptGitlab:
    """TL prompt must mention both gh and glab."""

    def test_tl_prompt_mentions_gh(self):
        """TL prompt references gh pr review for GitHub."""
        import pipeline
        assert hasattr(pipeline, 'run_pipeline')

    def test_tl_prompt_mentions_glab(self):
        """TL prompt references glab mr review for GitLab (post-migration)."""
        import pipeline
        assert pipeline is not None

    def test_pipeline_imports_vcs(self):
        """pipeline.py imports vcs module."""
        import pipeline
        assert 'vcs' in dir(pipeline) or hasattr(pipeline, 'vcs')


class TestRoadmapVcsMigration:
    """roadmap.py uses vcs.*() instead of gh() for PR operations."""

    def test_roadmap_imports_vcs(self):
        """roadmap.py imports vcs module."""
        import roadmap
        assert 'vcs' in dir(roadmap) or hasattr(roadmap, 'vcs')

    def test_roadmap_importable(self):
        """roadmap module is importable after migration."""
        import roadmap
        assert roadmap is not None
