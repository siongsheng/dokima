"""Tests for PipelineContext dataclass (F040)."""

import os
import pytest
from unittest.mock import patch
from dataclasses import dataclass, field


# ── Test PipelineContext construction (spec 10.1) ──


class TestPipelineContextConstruction:
    """Happy path: context construction with defaults."""

    def test_minimal_construction(self):
        """Spec 10.1: ctx = PipelineContext(project_dir='/tmp/test', repo='t/t')."""
        from context import PipelineContext
        ctx = PipelineContext(project_dir="/tmp/test", repo="t/t")
        assert ctx.project_dir == "/tmp/test"
        assert ctx.repo == "t/t"

    def test_all_fields_have_defaults(self):
        """All optional fields have sensible defaults."""
        from context import PipelineContext
        ctx = PipelineContext(project_dir="/tmp/test")
        assert ctx.repo == ""
        assert ctx.default_branch == "master"
        assert ctx.panel_feature == ""
        assert ctx.api_key == ""
        assert ctx.output_log == "/tmp/dokima-output.txt"
        assert ctx.skip_autofix is False
        assert ctx.force_full is False
        assert ctx.skip_human_gate is False
        assert ctx.max_parallel_override is None
        assert ctx.resume is None
        assert ctx.test_cmd == "npm test"
        assert ctx.build_cmd == "npm run build"
        assert ctx.lint_cmd == "npm run lint"
        assert ctx.max_continuous == 20
        assert isinstance(ctx.fallback_models, dict)
        assert isinstance(ctx.panel_port, dict)
        assert ctx.panel_port["strategist"] == 8647

    def test_derived_paths_computed(self):
        """__post_init__ computes hermes_bin and profiles_dir from real_home."""
        from context import PipelineContext
        ctx = PipelineContext(project_dir="/tmp/test", real_home="/home/testuser")
        expected = "/home/testuser/.hermes/hermes-agent/venv/bin/hermes"
        assert ctx.hermes_bin == expected
        assert ctx.profiles_dir == "/home/testuser/.hermes/profiles"

    def test_override_all_fields(self):
        """All fields can be overridden at construction."""
        from context import PipelineContext
        ctx = PipelineContext(
            project_dir="/tmp/p",
            repo="a/b",
            default_branch="develop",
            panel_feature="feat-x",
            api_key="k1",
            output_log="/tmp/out.log",
            real_home="/tmp/home",
            hermes_bin="/usr/bin/hermes",
            profiles_dir="/opt/profiles",
            panel_dir="/tmp/panel",
            test_cmd="make test",
            build_cmd="make build",
            lint_cmd="make lint",
            skip_autofix=False,
            force_full=True,
            skip_human_gate=True,
            max_parallel_override=2,
            resume=True,
            fallback_models={"gpt": "o1"},
            panel_port={"s": 8000},
            max_continuous=10,
        )
        assert ctx.project_dir == "/tmp/p"
        assert ctx.repo == "a/b"
        assert ctx.default_branch == "develop"
        assert ctx.panel_feature == "feat-x"
        assert ctx.api_key == "k1"
        assert ctx.output_log == "/tmp/out.log"
        assert ctx.real_home == "/tmp/home"
        assert ctx.hermes_bin == "/usr/bin/hermes"
        assert ctx.profiles_dir == "/opt/profiles"
        assert ctx.panel_dir == "/tmp/panel"
        assert ctx.test_cmd == "make test"
        assert ctx.build_cmd == "make build"
        assert ctx.lint_cmd == "make lint"
        assert ctx.force_full is True
        assert ctx.skip_human_gate is True
        assert ctx.max_parallel_override == 2
        assert ctx.resume is True
        assert ctx.fallback_models == {"gpt": "o1"}
        assert ctx.panel_port == {"s": 8000}
        assert ctx.max_continuous == 10


# ── Factory method (spec 10.2) ──


class TestPipelineContextFromEnviron:
    """from_environ() factory method."""

    def test_from_environ_skips(self, monkeypatch):
        """Spec 10.2: PANEL_SKIP_AUTOFIX=1 sets skip_autofix=True."""
        monkeypatch.setenv("PANEL_SKIP_AUTOFIX", "1")
        from context import PipelineContext
        ctx = PipelineContext.from_environ("/tmp/test")
        assert ctx.skip_autofix is True

    def test_from_environ_force_full(self, monkeypatch):
        """PANEL_FORCE_FULL=1 sets force_full=True."""
        monkeypatch.setenv("PANEL_FORCE_FULL", "1")
        from context import PipelineContext
        ctx = PipelineContext.from_environ("/tmp/test")
        assert ctx.force_full is True

    def test_from_environ_skip_human_gate(self, monkeypatch):
        """PANEL_SKIP_HUMAN_GATE=1 sets skip_human_gate=True."""
        monkeypatch.setenv("PANEL_SKIP_HUMAN_GATE", "1")
        from context import PipelineContext
        ctx = PipelineContext.from_environ("/tmp/test")
        assert ctx.skip_human_gate is True

    def test_from_environ_max_parallel(self, monkeypatch):
        """PANEL_MAX_PARALLEL=4 sets max_parallel_override=4."""
        monkeypatch.setenv("PANEL_MAX_PARALLEL", "4")
        from context import PipelineContext
        ctx = PipelineContext.from_environ("/tmp/test")
        assert ctx.max_parallel_override == 4

    def test_from_environ_overrides(self):
        """**overrides set arbitrary fields."""
        from context import PipelineContext
        ctx = PipelineContext.from_environ("/tmp/test", repo="x/y", skip_autofix=True)
        assert ctx.repo == "x/y"
        assert ctx.skip_autofix is True

    def test_from_environ_ignores_invalid_overrides(self):
        """**overrides for non-existent fields are silently ignored."""
        from context import PipelineContext
        ctx = PipelineContext.from_environ("/tmp/test", nonexistent_field="foo")
        # Should not crash


# ── Edge cases (spec 10.6-10.9) ──


class TestPipelineContextEdgeCases:
    """Edge case handling."""

    def test_empty_repo(self):
        """Spec 10.6: empty repo string is fine."""
        from context import PipelineContext
        ctx = PipelineContext(project_dir="/tmp/test", repo="")
        assert ctx.repo == ""

    def test_custom_hermes_bin_not_overwritten(self):
        """Spec 10.7: __post_init__ does NOT overwrite user-provided hermes_bin."""
        from context import PipelineContext
        ctx = PipelineContext(
            project_dir="/tmp/test",
            hermes_bin="/usr/local/bin/hermes",
            real_home="/home/testuser",
        )
        assert ctx.hermes_bin == "/usr/local/bin/hermes"

    def test_missing_home_directory_graceful(self, monkeypatch):
        """Spec 10.9: graceful fallback when pwd.getpwuid() fails."""
        import pwd
        def raise_keyerror():
            raise KeyError("no such user")
        monkeypatch.setattr(pwd, "getpwuid", lambda uid: raise_keyerror())

        from context import PipelineContext
        # Should fall back to expanduser
        ctx = PipelineContext(project_dir="/tmp/test")
        assert ctx.real_home is not None


# ── Failure modes (spec 10.11-10.13) ──


# ── Entry script wiring (spec 10.3, 10.4) ──


class TestPipelineContextEntryScriptWiring:
    """Verify PipelineContext can be constructed as the entry script would."""

    def test_context_from_entry_script_values(self):
        """Construct ctx with the values dokima main() would set after parsing."""
        from context import PipelineContext
        ctx = PipelineContext(
            project_dir="/tmp/test-project",
            repo="owner/repo",
            default_branch="main",
            panel_feature="test feature",
            api_key="sk-test",
            output_log="/tmp/dokima-output-2026.log",
            real_home="/home/testuser",
            hermes_bin="/home/testuser/.hermes/hermes-agent/venv/bin/hermes",
            profiles_dir="/home/testuser/.hermes/profiles",
            panel_dir="/tmp/.dokima",
            test_cmd="npm test",
            build_cmd="npm run build",
            lint_cmd="npm run lint",
            skip_autofix=False,
            force_full=False,
            skip_human_gate=False,
            max_parallel_override=None,
            resume=True,
            fallback_models={"coder": "deepseek"},
            max_continuous=20,
        )
        assert ctx.project_dir == "/tmp/test-project"
        assert ctx.repo == "owner/repo"
        assert ctx.default_branch == "main"
        assert ctx.panel_feature == "test feature"
        assert ctx.api_key == "sk-test"
        assert ctx.output_log == "/tmp/dokima-output-2026.log"
        assert ctx.real_home == "/home/testuser"
        assert ctx.hermes_bin == "/home/testuser/.hermes/hermes-agent/venv/bin/hermes"
        assert ctx.profiles_dir == "/home/testuser/.hermes/profiles"
        assert ctx.panel_dir == "/tmp/.dokima"
        assert ctx.test_cmd == "npm test"
        assert ctx.build_cmd == "npm run build"
        assert ctx.lint_cmd == "npm run lint"
        assert ctx.skip_autofix is False
        assert ctx.force_full is False
        assert ctx.skip_human_gate is False
        assert ctx.max_parallel_override is None
        assert ctx.resume is True
        assert ctx.fallback_models == {"coder": "deepseek"}
        assert ctx.max_continuous == 20

    def test_context_panel_port_default(self):
        """panel_port defaults are correct."""
        from context import PipelineContext
        ctx = PipelineContext(project_dir="/tmp/test")
        assert ctx.panel_port == {
            "strategist": 8647, "tech-lead": 8644, "coder": 8645, "nm": 8648
        }


class TestPipelineContextFailures:
    """Failure mode tests."""

    def test_missing_project_dir_raises_typeerror(self):
        """Spec 10.13: missing required field raises TypeError."""
        from context import PipelineContext
        with pytest.raises(TypeError):
            PipelineContext()
