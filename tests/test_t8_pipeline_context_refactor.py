"""Tests for Task 8: Refactor run_post_pipeline, run_fix_mode, run_fix_mode_issue,
discover_blocked_pr, extract_blockers_from_pr — switch globals to ctx fields."""

import json as _json
from unittest.mock import patch, MagicMock

from utils import PipelineContext


# ═══════════════════════════════════════════════════════════════════
# discover_blocked_pr(ctx) — uses ctx.repo instead of global REPO
# ═══════════════════════════════════════════════════════════════════


def test_discover_blocked_pr_accepts_ctx_and_uses_repo(panel):
    """discover_blocked_pr(ctx) uses ctx.repo when calling gh."""
    ctx = PipelineContext(repo="ctx-owner/ctx-repo")
    with patch.object(panel, 'gh', return_value=("[]", "", 0)) as mock_gh:
        panel.discover_blocked_pr(ctx)
        # Verify gh was called with ctx.repo
        mock_gh.assert_called_once()
        args = mock_gh.call_args[0]
        assert "ctx-owner/ctx-repo" in str(args)


def test_discover_blocked_pr_ctx_repo_in_json_query(panel):
    """discover_blocked_pr(ctx) passes ctx.repo into --repo flag of gh pr list."""
    ctx = PipelineContext(repo="myorg/myrepo")
    mock_stdout = _json.dumps([
        {"number": 1, "title": "[BLOCKED] Bug", "body": "",
         "headRefName": "feat/x", "updatedAt": "2026-01-01T00:00:00Z"}
    ])
    with patch.object(panel, 'gh', return_value=(mock_stdout, "", 0)) as mock_gh:
        result = panel.discover_blocked_pr(ctx)
        assert result is not None
        assert result["number"] == 1
        # Verify --repo flag was passed with ctx.repo
        args = mock_gh.call_args[0]
        assert "--repo" in args
        idx = args.index("--repo")
        assert args[idx + 1] == "myorg/myrepo"


def test_discover_blocked_pr_no_ctx_uses_default_repo(panel):
    """discover_blocked_pr(ctx) with default repo="" still works."""
    ctx = PipelineContext()  # repo=""
    with patch.object(panel, 'gh', return_value=("[]", "", 0)) as mock_gh:
        result = panel.discover_blocked_pr(ctx)
        assert result is None
        mock_gh.assert_called_once()


# ═══════════════════════════════════════════════════════════════════
# extract_blockers_from_pr(ctx, ...) — uses ctx.repo for PR comments fallback
# ═══════════════════════════════════════════════════════════════════


def test_extract_blockers_accepts_ctx_standard(panel):
    """extract_blockers_from_pr(ctx, pr_body) extracts blockers from ### Blockers section."""
    ctx = PipelineContext(repo="test-owner/test-repo")
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- Login test fails
- Missing error handling
"""
    result = panel.extract_blockers_from_pr(ctx, pr_body)
    assert len(result) == 2
    assert "Login test fails" in result


def test_extract_blockers_ctx_falls_back_to_repo(panel):
    """extract_blockers_from_pr(ctx, pr_body, pr_number=N) uses ctx.repo for gh call."""
    ctx = PipelineContext(repo="test-owner/test-repo")
    # mock gh to return just the body text (as --jq ".body" would)
    with patch.object(panel, 'gh', return_value=(
        "### Blockers\n- From comments\n", "", 0
    )) as mock_gh:
        # No blockers in body → falls back to PR comments via gh
        result = panel.extract_blockers_from_pr(ctx, "", pr_number=42)
        assert len(result) >= 1
        mock_gh.assert_called_once()
        args = mock_gh.call_args[0]
        assert "42" in str(args)
        assert "test-owner/test-repo" in str(args)


# ═══════════════════════════════════════════════════════════════════
# run_post_pipeline(ctx, ...) — uses ctx.project_dir, ctx.repo, ctx.output_log, ctx.panel_feature
# ═══════════════════════════════════════════════════════════════════


def test_run_post_pipeline_accepts_ctx(panel, tmpdir):
    """run_post_pipeline(ctx, ...) prints ctx.project_dir and ctx.repo."""
    ctx = PipelineContext(
        project_dir=str(tmpdir), repo="test-owner/test-repo",
        output_log="/tmp/test-log.txt", panel_feature="F001: Test"
    )
    with patch("builtins.print") as mock_print:
        panel.run_post_pipeline(
            ctx, feature="test", is_next=False, is_continuous=False,
            continue_loop=True, pr_url="https://github.com/t/t/pull/1",
            verdict="APPROVED", impact="LOW", branch="feat/x",
            spec_path="/tmp/spec.md", strat_output="output", mode="active"
        )
    printed = " ".join(str(call) for call in mock_print.call_args_list)
    assert str(tmpdir) in printed
    assert "test-owner/test-repo" in printed


# ═══════════════════════════════════════════════════════════════════
# run_fix_mode(ctx, ...) — uses ctx.project_dir, ctx.repo, etc.
# ═══════════════════════════════════════════════════════════════════


def test_run_fix_mode_accepts_ctx(panel, tmpdir):
    """run_fix_mode(ctx, project_dir) accepts ctx and prints project_dir."""
    ctx = PipelineContext(project_dir=str(tmpdir), repo="test-owner/test-repo")
    # Patch pipeline-level functions (where run_fix_mode looks them up at call time)
    with patch('pipeline.discover_blocked_pr', return_value=None) as mock_disc, \
         patch("builtins.print") as mock_print:
        panel.run_fix_mode(ctx, str(tmpdir))
        # Verify ctx was passed to discover_blocked_pr
        mock_disc.assert_called_once()
        # First arg should be ctx
        assert mock_disc.call_args[0][0] is ctx


# ═══════════════════════════════════════════════════════════════════
# run_fix_mode_issue(ctx, ...) — uses ctx.project_dir, ctx.repo, ctx.default_branch, ctx.test_cmd, ctx.build_cmd
# ═══════════════════════════════════════════════════════════════════


def test_run_fix_mode_issue_accepts_ctx():
    """run_fix_mode_issue(ctx, project_dir, issue_number) accepts ctx as first arg."""
    import inspect
    import pipeline

    sig = inspect.signature(pipeline.run_fix_mode_issue)
    params = list(sig.parameters.keys())
    assert params[0] == "ctx", f"run_fix_mode_issue missing ctx as first param, got {params}"

    ctx = PipelineContext(
        project_dir="/tmp/test", repo="test-owner/test-repo",
        default_branch="main", test_cmd="pytest", build_cmd="build"
    )
    # Just verify the function can be called with ctx without TypeError
    # (we mock at pipeline level for deep execution tests below)
    from unittest.mock import patch
    with patch('pipeline.gh', return_value=("", "", 0)), \
         patch('pipeline.git', return_value=("", "", 0)), \
         patch('pipeline.run_phase2_coder', return_value={"coder_failed": True}), \
         patch('pipeline.run_phase3_vet', return_value={}), \
         patch('pipeline.run_phase4_nm', return_value={}), \
         patch("builtins.print"):
        # Should not raise TypeError for missing ctx
        pipeline.run_fix_mode_issue(ctx, "/tmp/test", 42)


# ═══════════════════════════════════════════════════════════════════
# Signature tests — verify ctx is first positional parameter
# ═══════════════════════════════════════════════════════════════════


def test_all_five_functions_accept_ctx_first(panel):
    """All five Task 8 functions accept ctx as first positional parameter."""
    import inspect
    import pipeline
    from utils import PipelineContext

    ctx = PipelineContext()
    funcs = [
        panel.run_post_pipeline,
        panel.discover_blocked_pr,
        panel.extract_blockers_from_pr,
        panel.run_fix_mode,
        pipeline.run_fix_mode_issue,
    ]
    for func in funcs:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        assert params[0] == "ctx", f"{func.__name__} missing ctx as first param, got {params}"
