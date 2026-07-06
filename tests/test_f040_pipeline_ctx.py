"""F040 Task 7: Test pipeline.py functions accept and use ctx parameter.

These tests verify that pipeline functions read configuration from
PipelineContext instead of module-level globals.
"""

import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest
from context import PipelineContext


# ── Test ctx fixture ──

@pytest.fixture
def ctx():
    """Create a PipelineContext with test defaults."""
    return PipelineContext(
        project_dir="/tmp/test-project",
        repo="test-owner/test-repo",
        default_branch="main",
        api_key="test-key",
        panel_feature="F001: test feature",
        test_cmd="echo test",
        build_cmd="echo build",
        lint_cmd="echo lint",
        output_log="/tmp/test-output.log",
        skip_autofix=False,
        force_full=False,
        skip_human_gate=False,
    )


# ── extract_blockers_from_pr ──

class TestExtractBlockersFromPr:
    """extract_blockers_from_pr reads ctx.repo for GitHub API calls."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function accepts ctx as first positional argument."""
        from pipeline import extract_blockers_from_pr
        # Simple pr_body with no blockers → no gh calls needed
        result = extract_blockers_from_pr(ctx, "# No blockers here\n")
        assert result == []

    def test_extracts_blockers_from_pr_body(self, ctx):
        """Extracts blockers from PR body ### Blockers section."""
        from pipeline import extract_blockers_from_pr
        pr_body = (
            "## Why\nSome reason\n\n"
            "### Blockers\n"
            "- Missing test coverage\n"
            "- Lint errors\n\n"
            "## Impact\nLOW\n"
        )
        result = extract_blockers_from_pr(ctx, pr_body)
        assert "Missing test coverage" in result
        assert "Lint errors" in result

    def test_uses_ctx_repo_for_gh_fallback(self, ctx):
        """When blockers not in body and pr_number given, calls gh with ctx.repo."""
        from pipeline import extract_blockers_from_pr
        # Mock gh to return empty body (no blockers)
        with patch("pipeline.gh") as mock_gh:
            mock_gh.side_effect = [
                # First call: gh pr view ... --comments
                (json.dumps({"body": ""}), "", 0),
            ]
            result = extract_blockers_from_pr(
                ctx, "No blockers here", pr_number=42
            )
            assert mock_gh.called
            # First call should use ctx.repo
            first_call_args = str(mock_gh.call_args_list[0])
            assert "test-owner/test-repo" in first_call_args


# ── _status_update ──

class TestStatusUpdate:
    """_status_update reads ctx.project_dir."""

    def test_uses_ctx_project_dir(self, ctx):
        """_status_update calls load_status and save_status with ctx.project_dir."""
        from pipeline import _status_update
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx.project_dir = tmpdir
            # load_status fails silently → save_status should be called
            with patch("pipeline.load_status") as mock_load, \
                 patch("pipeline.save_status") as mock_save:
                mock_load.return_value = None
                _status_update(ctx, feature="test")
                mock_load.assert_called_with(tmpdir)
                if mock_save.called:
                    mock_save.assert_called_with(mock_save.call_args[0][0], tmpdir)


# ── run_phase1_strategist ──

class TestRunPhase1Strategist:
    """run_phase1_strategist accepts ctx and reads ctx.project_dir, ctx.profiles."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function signature includes ctx as first parameter."""
        import pipeline
        assert callable(pipeline.run_phase1_strategist)
        sig = pipeline.run_phase1_strategist.__code__.co_varnames
        assert sig[0] == "ctx", f"First param should be 'ctx', got {sig}"


# ── run_phase2_coder ──

class TestRunPhase2Coder:
    """run_phase2_coder accepts ctx parameter."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function signature includes ctx as first parameter."""
        import pipeline
        sig = pipeline.run_phase2_coder.__code__.co_varnames
        assert sig[0] == "ctx", f"First param should be 'ctx', got {sig}"


# ── run_phase3_vet ──

class TestRunPhase3Vet:
    """run_phase3_vet accepts ctx parameter."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function signature includes ctx as first parameter."""
        import pipeline
        sig = pipeline.run_phase3_vet.__code__.co_varnames
        assert sig[0] == "ctx", f"First param should be 'ctx', got {sig}"


# ── run_phase4_nm ──

class TestRunPhase4Nm:
    """run_phase4_nm accepts ctx parameter."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function signature includes ctx as first parameter."""
        import pipeline
        sig = pipeline.run_phase4_nm.__code__.co_varnames
        assert sig[0] == "ctx", f"First param should be 'ctx', got {sig}"


# ── run_phase5_tech_lead ──

class TestRunPhase5TechLead:
    """run_phase5_tech_lead accepts ctx parameter."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function signature includes ctx as first parameter."""
        import pipeline
        sig = pipeline.run_phase5_tech_lead.__code__.co_varnames
        assert sig[0] == "ctx", f"First param should be 'ctx', got {sig}"


# ── run_fix_mode ──

class TestRunFixMode:
    """run_fix_mode accepts ctx and sets ctx.project_dir."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function signature includes ctx as first parameter."""
        import pipeline
        sig = pipeline.run_fix_mode.__code__.co_varnames
        assert sig[0] == "ctx", f"First param should be 'ctx', got {sig}"


# ── run_pipeline ──

class TestRunPipeline:
    """run_pipeline accepts ctx as first parameter."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function signature includes ctx as first parameter."""
        import pipeline
        sig = pipeline.run_pipeline.__code__.co_varnames
        assert sig[0] == "ctx", f"First param should be 'ctx', got {sig}"


# ── run_post_pipeline ──

class TestRunPostPipeline:
    """run_post_pipeline accepts ctx and reads ctx attributes."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function signature includes ctx as first parameter."""
        import pipeline
        sig = pipeline.run_post_pipeline.__code__.co_varnames
        assert sig[0] == "ctx", f"First param should be 'ctx', got {sig}"


# ── discover_blocked_pr ──

class TestDiscoverBlockedPr:
    """discover_blocked_pr accepts ctx and reads ctx.repo."""

    def test_accepts_ctx_parameter(self, ctx):
        """Function signature includes ctx as first parameter."""
        import pipeline
        sig = pipeline.discover_blocked_pr.__code__.co_varnames
        assert sig[0] == "ctx", f"First param should be 'ctx', got {sig}"


# ── Global statement removal ──

class TestNoGlobalStatements:
    """After migration, pipeline.py has zero global statements."""

    def test_no_global_statements_in_pipeline(self):
        """pipeline.py should have no 'global ' statements."""
        pipeline_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "pipeline.py"
        )
        with open(pipeline_path) as f:
            content = f.read()
        lines_with_global = [
            i + 1 for i, line in enumerate(content.split("\n"))
            if line.strip().startswith("global ")
        ]
        assert not lines_with_global, (
            f"pipeline.py still has global statements at lines: {lines_with_global}"
        )
