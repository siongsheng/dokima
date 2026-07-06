"""Tests for shared conftest fixtures: test_repo and mock_orchestrator."""
import os
import sys
import subprocess


class TestTestRepoFixture:
    """Tests for the test_repo fixture in conftest.py."""

    def test_repo_creates_git_repo(self, panel, test_repo):
        """test_repo creates a git repository with at least one commit."""
        result = subprocess.run(
            ["git", "-C", test_repo, "rev-parse", "HEAD"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"git rev-parse failed: {result.stderr}"
        assert len(result.stdout.strip()) > 0, "No commit found"

    def test_repo_has_agents_md_and_specs(self, panel, test_repo):
        """test_repo creates AGENTS.md and specs/roadmap.md."""
        agents_path = os.path.join(test_repo, "AGENTS.md")
        assert os.path.exists(agents_path), "AGENTS.md not created"
        with open(agents_path) as f:
            content = f.read()
        assert "## Commands" in content, "AGENTS.md missing Commands section"
        assert "- Test:" in content, "AGENTS.md missing Test command"

        roadmap_path = os.path.join(test_repo, "specs", "roadmap.md")
        assert os.path.exists(roadmap_path), "roadmap.md not created"
        with open(roadmap_path) as f:
            content = f.read()
        assert "## Phase" in content, "roadmap.md missing Phase section"
        assert "### F001:" in content, "roadmap.md missing feature header"

    def test_repo_sets_panel_globals(self, panel, test_repo):
        """test_repo sets panel.PROJECT_DIR, panel.REPO, and panel.DEFAULT_BRANCH."""
        assert panel.PROJECT_DIR == test_repo, (
            f"Expected PROJECT_DIR={test_repo}, got {panel.PROJECT_DIR}"
        )
        assert panel.REPO == "test-owner/test-repo", (
            f"Expected REPO=test-owner/test-repo, got {panel.REPO}"
        )
        assert panel.DEFAULT_BRANCH == "master", (
            f"Expected DEFAULT_BRANCH=master, got {panel.DEFAULT_BRANCH}"
        )


class TestMockOrchestratorFixture:
    """Tests for the mock_orchestrator fixture in conftest.py."""

    def test_mock_orchestrator_mocks_spawn_agent(self, panel, mock_orchestrator):
        """mock_orchestrator replaces panel.spawn_agent with a mock."""
        # Verify spawn_agent is a callable that returns a predictable value
        result = panel.spawn_agent("coder", ["skill-a"], "test prompt")
        assert result == "Mock agent output", f"Unexpected return: {result}"

    def test_mock_orchestrator_tracks_calls(self, panel, mock_orchestrator):
        """mock_orchestrator records spawn_agent calls in spawn_calls."""
        panel.spawn_agent("strategist", ["skill-x"], "prompt 1")
        panel.spawn_agent("coder", ["skill-y"], "prompt 2")
        assert mock_orchestrator["spawn_calls"] == ["strategist", "coder"], (
            f"Expected ['strategist', 'coder'], got {mock_orchestrator['spawn_calls']}"
        )

    def test_mock_orchestrator_patches_key_functions(self, panel, mock_orchestrator):
        """mock_orchestrator patches git, gh, _set_gh_token, load_key, etc."""
        from unittest.mock import MagicMock
        assert isinstance(panel.git, MagicMock), "panel.git not patched"
        assert isinstance(panel.gh, MagicMock), "panel.gh not patched"
        assert isinstance(panel._set_gh_token, MagicMock), "panel._set_gh_token not patched"
        assert isinstance(panel.load_key, MagicMock), "panel.load_key not patched"
        assert isinstance(panel.load_github_token, MagicMock), "panel.load_github_token not patched"
        assert isinstance(panel.acquire_lock, MagicMock), "panel.acquire_lock not patched"
        assert isinstance(panel._cleanup_lock, MagicMock), "panel._cleanup_lock not patched"


class TestCtxFixture:
    """Tests for the ctx fixture in conftest.py."""

    def test_ctx_is_pipelinecontext(self, ctx):
        """ctx fixture returns a PipelineContext instance."""
        from context import PipelineContext
        assert isinstance(ctx, PipelineContext), (
            f"Expected PipelineContext, got {type(ctx)}"
        )

    def test_ctx_default_values(self, ctx):
        """ctx fixture has the expected test default values."""
        assert ctx.project_dir == "/tmp/test-project", (
            f"project_dir: expected /tmp/test-project, got {ctx.project_dir}"
        )
        assert ctx.repo == "test-owner/test-repo", (
            f"repo: expected test-owner/test-repo, got {ctx.repo}"
        )
        assert ctx.api_key == "test-key", (
            f"api_key: expected test-key, got {ctx.api_key}"
        )
        assert ctx.default_branch == "main", (
            f"default_branch: expected main, got {ctx.default_branch}"
        )
        assert ctx.output_log == "/dev/null", (
            f"output_log: expected /dev/null, got {ctx.output_log}"
        )
        assert ctx.test_cmd == "echo test", (
            f"test_cmd: expected echo test, got {ctx.test_cmd}"
        )
        assert ctx.build_cmd == "echo build", (
            f"build_cmd: expected echo build, got {ctx.build_cmd}"
        )
        assert ctx.lint_cmd == "echo lint", (
            f"lint_cmd: expected echo lint, got {ctx.lint_cmd}"
        )

    def test_ctx_is_not_autouse(self, request):
        """ctx fixture is not autouse — tests must request it explicitly."""
        assert "ctx" not in request.fixturenames, (
            "ctx fixture should not be autouse"
        )
