"""Tests for PipelineContext dataclass in context.py."""
import os
import tempfile
import pytest


class TestPipelineContextDefaults:
    """Verify all default values match the spec."""

    def test_import_exists(self):
        from context import PipelineContext
        assert PipelineContext is not None

    def test_default_values(self):
        from context import PipelineContext
        ctx = PipelineContext()

        # Paths
        assert ctx.project_dir == ""
        assert ctx.panel_dir == ""
        assert ctx.output_log == "/tmp/dokita-output.txt"
        assert ctx.hermes_bin == ""

        # VCS
        assert ctx.repo == ""
        assert ctx.default_branch == "master"
        assert ctx.vcs_backend == "github"
        assert ctx.vcs_token_env == "GH_TOKEN"

        # Auth
        assert ctx.api_key == ""

        # Feature
        assert ctx.panel_feature == ""

        # Commands
        assert ctx.test_cmd == "npm test"
        assert ctx.build_cmd == "npm run build"
        assert ctx.lint_cmd == "npm run lint"

        # Model fallback
        assert ctx.fallback_models == {}

        # Feature flags
        assert ctx.fallback_models == {}
        assert ctx.skip_autofix is False
        assert ctx.force_full is False
        assert ctx.skip_human_gate is False
        assert ctx.max_parallel_override is None
        assert ctx.resume is None

    def test_fallback_models_independent_per_instance(self):
        from context import PipelineContext
        ctx1 = PipelineContext()
        ctx2 = PipelineContext()
        ctx1.fallback_models["openai"] = "gpt-4"
        assert ctx2.fallback_models == {}


class TestPipelineContextInit:
    """Verify all fields can be set at construction."""

    def test_all_fields_settable(self):
        from context import PipelineContext
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = PipelineContext(
                project_dir=tmpdir,
                panel_dir="/my/panel",
                output_log="/my/log.txt",
                hermes_bin="/usr/bin/hermes",
                repo="owner/repo",
                default_branch="develop",
                vcs_backend="gitlab",
                vcs_token_env="GITLAB_TOKEN",
                api_key="sk-abc123",
                panel_feature="F001: test",
                test_cmd="cargo test",
                build_cmd="cargo build",
                lint_cmd="cargo clippy",
                fallback_models={"openai": "gpt-4o"},
                skip_autofix=True,
                force_full=True,
                skip_human_gate=True,
                max_parallel_override=3,
                resume=True,
            )

            assert ctx.project_dir == tmpdir
            assert ctx.panel_dir == "/my/panel"
            assert ctx.output_log == "/my/log.txt"
            assert ctx.hermes_bin == "/usr/bin/hermes"
            assert ctx.repo == "owner/repo"
            assert ctx.default_branch == "develop"
            assert ctx.vcs_backend == "gitlab"
            assert ctx.vcs_token_env == "GITLAB_TOKEN"
            assert ctx.api_key == "sk-abc123"
            assert ctx.panel_feature == "F001: test"
            assert ctx.test_cmd == "cargo test"
            assert ctx.build_cmd == "cargo build"
            assert ctx.lint_cmd == "cargo clippy"
            assert ctx.fallback_models == {"openai": "gpt-4o"}
            assert ctx.skip_autofix is True
            assert ctx.force_full is True
            assert ctx.skip_human_gate is True
            assert ctx.max_parallel_override == 3
            assert ctx.resume is True

    def test_mutable_after_construction(self):
        from context import PipelineContext
        ctx = PipelineContext()
        ctx.project_dir = "/new/path"
        ctx.repo = "new/repo"
        ctx.max_parallel_override = 8
        assert ctx.project_dir == "/new/path"
        assert ctx.repo == "new/repo"
        assert ctx.max_parallel_override == 8


class TestPostInitValidation:
    """Verify __post_init__ validation behavior."""

    def test_empty_project_dir_no_error(self):
        from context import PipelineContext
        ctx = PipelineContext()  # project_dir defaults to ""
        assert ctx.project_dir == ""

    def test_nonexistent_project_dir_raises(self):
        from context import PipelineContext
        with pytest.raises(ValueError, match="Project directory does not exist"):
            PipelineContext(project_dir="/nonexistent/path/that/does/not/exist")

    def test_existing_project_dir_no_error(self):
        from context import PipelineContext
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = PipelineContext(project_dir=tmpdir)
            assert ctx.project_dir == tmpdir

    def test_project_dir_as_file_raises(self):
        from context import PipelineContext
        with tempfile.NamedTemporaryFile() as tmpfile:
            with pytest.raises(ValueError, match="Project directory does not exist"):
                PipelineContext(project_dir=tmpfile.name)


class TestIsDataclass:
    """Verify PipelineContext is a proper dataclass."""

    def test_is_dataclass(self):
        import dataclasses
        from context import PipelineContext
        assert dataclasses.is_dataclass(PipelineContext)

    def test_not_frozen(self):
        from context import PipelineContext
        ctx = PipelineContext()
        # Must be able to set attributes after construction
        ctx.project_dir = "/new"
        ctx.repo = "new/repo"
        ctx.max_parallel_override = 5
        assert ctx.project_dir == "/new"


class TestDataTypeEnforcement:
    """Verify field types are respected at a basic level."""

    def test_bool_fields_are_bool(self):
        from context import PipelineContext
        ctx = PipelineContext()
        assert isinstance(ctx.skip_autofix, bool)
        assert isinstance(ctx.force_full, bool)
        assert isinstance(ctx.skip_human_gate, bool)

    def test_fallback_models_is_dict(self):
        from context import PipelineContext
        ctx = PipelineContext()
        assert isinstance(ctx.fallback_models, dict)

    def test_max_parallel_override_is_none_by_default(self):
        from context import PipelineContext
        ctx = PipelineContext()
        assert ctx.max_parallel_override is None

    def test_max_parallel_override_accepts_int(self):
        from context import PipelineContext
        ctx = PipelineContext(max_parallel_override=4)
        assert isinstance(ctx.max_parallel_override, int)
        assert ctx.max_parallel_override == 4

    def test_resume_is_none_by_default(self):
        from context import PipelineContext
        ctx = PipelineContext()
        assert ctx.resume is None

    def test_resume_accepts_bool(self):
        from context import PipelineContext
        ctx = PipelineContext(resume=True)
        assert ctx.resume is True

    def test_str_fields_are_str(self):
        from context import PipelineContext
        ctx = PipelineContext(project_dir="/tmp", repo="o/r")
        assert isinstance(ctx.project_dir, str)
        assert isinstance(ctx.repo, str)
        assert isinstance(ctx.api_key, str)
