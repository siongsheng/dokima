"""Task 6 tests: run_phase3_vet, run_phase4_nm, run_phase5_tech_lead use ctx fields.

Verifies:
1. Global declarations removed from all three functions
2. Module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, TEST_CMD, BUILD_CMD,
   LINT_CMD) replaced with ctx.FIELD access
3. When ctx is provided with known values, ctx fields flow through to sub-calls
"""
import os
import re
import sys

import pytest

# Add parent directory so we can import panel modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import PipelineContext


PIPELINE_PATH = os.path.join(os.path.dirname(__file__), "..", "pipeline.py")


# ── helpers ────────────────────────────────────────────────────────────────


def _read_pipeline():
    with open(PIPELINE_PATH) as f:
        return f.read()


def _extract_function(source, func_name):
    """Extract full function body from source by balancing def/indentation."""
    pattern = re.compile(rf'^def\s+{re.escape(func_name)}\s*\(', re.MULTILINE)
    m = pattern.search(source)
    if not m:
        return ""
    start = m.start()
    lines = source[start:].split("\n")
    def_line = lines[0]
    base_indent = len(def_line) - len(def_line.lstrip())
    body_lines = [def_line]
    for line in lines[1:]:
        if line.strip() == "":
            body_lines.append(line)
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= base_indent and line.strip():
            break
        body_lines.append(line)
    return "\n".join(body_lines)


def _ctx_field_count(func_body, field_name):
    """Count occurrences of ctx.FIELD_NAME in function body."""
    pattern = re.compile(rf'\bctx\.{re.escape(field_name)}\b')
    return len(pattern.findall(func_body))


# ── source-code inspection tests ───────────────────────────────────────────


class TestPhase3VetNoGlobals:
    """run_phase3_vet: globals removed, ctx fields used."""

    def test_no_global_statements(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase3_vet")
        assert "global " not in body, (
            "run_phase3_vet still has global statement(s)"
        )

    def test_uses_ctx_PROJECT_DIR(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase3_vet")
        count = _ctx_field_count(body, "PROJECT_DIR")
        assert count >= 5, (
            f"run_phase3_vet should use ctx.PROJECT_DIR at least 5 times, got {count}"
        )

    def test_uses_ctx_REPO(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase3_vet")
        count = _ctx_field_count(body, "REPO")
        assert count >= 2, (
            f"run_phase3_vet should use ctx.REPO at least twice, got {count}"
        )

    def test_uses_ctx_DEFAULT_BRANCH(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase3_vet")
        count = _ctx_field_count(body, "DEFAULT_BRANCH")
        assert count >= 2, (
            f"run_phase3_vet should use ctx.DEFAULT_BRANCH at least twice, got {count}"
        )

    def test_uses_ctx_TEST_CMD(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase3_vet")
        count = _ctx_field_count(body, "TEST_CMD")
        assert count >= 1, (
            f"run_phase3_vet should use ctx.TEST_CMD, got {count}"
        )

    def test_uses_ctx_BUILD_CMD(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase3_vet")
        count = _ctx_field_count(body, "BUILD_CMD")
        assert count >= 1, (
            f"run_phase3_vet should use ctx.BUILD_CMD, got {count}"
        )

    def test_uses_ctx_LINT_CMD(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase3_vet")
        count = _ctx_field_count(body, "LINT_CMD")
        assert count >= 1, (
            f"run_phase3_vet should use ctx.LINT_CMD (from detect_commands assignment), got {count}"
        )


class TestPhase4NmNoGlobals:
    """run_phase4_nm: globals removed, ctx fields used."""

    def test_no_global_statements(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase4_nm")
        assert "global " not in body, (
            "run_phase4_nm still has global statement(s)"
        )

    def test_uses_ctx_PROJECT_DIR(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase4_nm")
        count = _ctx_field_count(body, "PROJECT_DIR")
        assert count >= 3, (
            f"run_phase4_nm should use ctx.PROJECT_DIR at least 3 times, got {count}"
        )

    def test_uses_ctx_REPO(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase4_nm")
        count = _ctx_field_count(body, "REPO")
        assert count >= 1, (
            f"run_phase4_nm should use ctx.REPO, got {count}"
        )

    def test_uses_ctx_TEST_CMD(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase4_nm")
        count = _ctx_field_count(body, "TEST_CMD")
        assert count >= 1, (
            f"run_phase4_nm should use ctx.TEST_CMD, got {count}"
        )

    def test_uses_ctx_BUILD_CMD(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase4_nm")
        count = _ctx_field_count(body, "BUILD_CMD")
        assert count >= 1, (
            f"run_phase4_nm should use ctx.BUILD_CMD, got {count}"
        )

    def test_uses_ctx_SKIP_AUTOFIX(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase4_nm")
        count = _ctx_field_count(body, "SKIP_AUTOFIX")
        assert count >= 1, (
            f"run_phase4_nm should use ctx.SKIP_AUTOFIX, got {count}"
        )


class TestPhase5TechLeadNoGlobals:
    """run_phase5_tech_lead: globals removed, ctx fields used."""

    def test_no_global_statements(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase5_tech_lead")
        assert "global " not in body, (
            "run_phase5_tech_lead still has global statement(s)"
        )

    def test_uses_ctx_PROJECT_DIR(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase5_tech_lead")
        count = _ctx_field_count(body, "PROJECT_DIR")
        assert count >= 3, (
            f"run_phase5_tech_lead should use ctx.PROJECT_DIR at least 3 times, got {count}"
        )

    def test_uses_ctx_REPO(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase5_tech_lead")
        count = _ctx_field_count(body, "REPO")
        assert count >= 3, (
            f"run_phase5_tech_lead should use ctx.REPO at least 3 times, got {count}"
        )

    def test_uses_ctx_DEFAULT_BRANCH(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase5_tech_lead")
        count = _ctx_field_count(body, "DEFAULT_BRANCH")
        assert count >= 2, (
            f"run_phase5_tech_lead should use ctx.DEFAULT_BRANCH at least twice, got {count}"
        )

    def test_uses_ctx_TEST_CMD(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase5_tech_lead")
        count = _ctx_field_count(body, "TEST_CMD")
        assert count >= 1, (
            f"run_phase5_tech_lead should use ctx.TEST_CMD, got {count}"
        )

    def test_uses_ctx_BUILD_CMD(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase5_tech_lead")
        count = _ctx_field_count(body, "BUILD_CMD")
        assert count >= 1, (
            f"run_phase5_tech_lead should use ctx.BUILD_CMD, got {count}"
        )

    def test_uses_ctx_SKIP_AUTOFIX(self):
        src = _read_pipeline()
        body = _extract_function(src, "run_phase5_tech_lead")
        count = _ctx_field_count(body, "SKIP_AUTOFIX")
        assert count >= 1, (
            f"run_phase5_tech_lead should use ctx.SKIP_AUTOFIX, got {count}"
        )


# ── behavioral tests ───────────────────────────────────────────────────────


class TestPhase3VetUsesCtxFields:
    """run_phase3_vet: when ctx is passed, ctx fields are used for commands."""

    def test_ctx_PROJECT_DIR_used_in_safe_run(self, panel, test_repo):
        """_safe_run receives ctx.PROJECT_DIR as cwd."""
        from unittest.mock import patch

        ctx = PipelineContext(
            PROJECT_DIR="/custom/project",
            REPO="custom/repo",
            DEFAULT_BRANCH="develop",
            TEST_CMD="custom-test",
            BUILD_CMD="custom-build",
        )

        with patch.object(panel, "git", return_value=("", "", 0)):
            with patch.object(panel, "gh", return_value=("", "", 0)):
                with patch.object(panel._agent, "spawn_agent", return_value="ok"):
                    with patch.object(panel, "halt_and_revert"):
                        with patch.object(panel, "detect_commands", return_value=("ct", "cb", "cl")):
                            with patch.object(
                                panel, "_safe_run",
                                return_value=type("R", (), {"stdout": "", "returncode": 0, "stderr": ""})()
                            ) as mock_sr:
                                panel.run_phase3_vet(
                                    feature="Test",
                                    branch="feat/test",
                                    pr_sections="## What",
                                    impact="LOW",
                                    spec_path="",
                                    ctx=ctx,
                                )
                                calls = [c for c in mock_sr.call_args_list
                                         if c[1].get("cwd") == "/custom/project"]
                                assert len(calls) >= 1, (
                                    f"_safe_run was not called with cwd='/custom/project'. "
                                    f"Call args: {mock_sr.call_args_list[:3]}"
                                )

    def test_ctx_none_still_works(self, panel, test_repo):
        """Backward compat: ctx=None uses module globals (no crash)."""
        from unittest.mock import patch

        ag_path = os.path.join(test_repo, "AGENTS.md")
        with open(ag_path, "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")
        panel.TEST_CMD = "echo ok"
        panel.BUILD_CMD = "echo ok"

        with patch.object(panel, "git", return_value=("", "", 0)):
            with patch.object(panel, "gh", return_value=("", "", 0)):
                with patch.object(panel._agent, "spawn_agent", return_value="ok"):
                    with patch.object(panel, "_safe_run",
                                      return_value=type("R", (), {"stdout": "", "returncode": 0, "stderr": ""})()):
                        result = panel.run_phase3_vet(
                            feature="Test",
                            branch="feat/test",
                            pr_sections="## What",
                            impact="LOW",
                            spec_path="",
                        )
        assert "pr_url" in result


class TestPhase4NmUsesCtxFields:
    """run_phase4_nm: when ctx is passed, ctx fields are used."""

    def test_ctx_PROJECT_DIR_used_for_nm_cmd(self, panel, test_repo):
        """nm command path uses ctx.PROJECT_DIR."""
        from unittest.mock import patch

        ctx = PipelineContext(
            PROJECT_DIR="/custom/project",
            REPO="custom/repo",
            TEST_CMD="ct",
            BUILD_CMD="cb",
            SKIP_AUTOFIX=True,
        )

        with patch.object(panel, "gh", return_value=("", "", 0)):
            with patch.object(panel, "_safe_run",
                              return_value=type("R", (), {"stdout": "", "returncode": 0, "stderr": ""})()
                              ) as mock_sr:
                result = panel.run_phase4_nm(
                    feature="Test",
                    branch="feat/test",
                    impact="MEDIUM",
                    pr_url_in="https://github.com/x/y/pull/1",
                    ctx=ctx,
                )
        nm_calls = [c for c in mock_sr.call_args_list
                     if c[0] and "/custom/project/scripts/nm" in str(c[0])]
        assert len(nm_calls) >= 1, (
            f"nm command should use /custom/project/scripts/nm. "
            f"Call args: {mock_sr.call_args_list[:3]}"
        )
        assert result["nm_ok"] is True

    def test_ctx_none_still_works(self, panel, test_repo):
        """Backward compat: ctx=None uses module globals."""
        from unittest.mock import patch

        with patch.object(panel, "gh", return_value=("", "", 0)):
            with patch.object(panel, "_safe_run",
                              return_value=type("R", (), {"stdout": "", "returncode": 0, "stderr": ""})()):
                result = panel.run_phase4_nm(
                    feature="Test",
                    branch="feat/test",
                    impact="MEDIUM",
                    pr_url_in="https://github.com/x/y/pull/1",
                )
        assert result["nm_ok"] is True


class TestPhase5TechLeadUsesCtxFields:
    """run_phase5_tech_lead: when ctx is passed, ctx fields are used."""

    def test_ctx_REPO_used_in_gh_pr_view(self, panel, test_repo):
        """gh pr view call uses ctx.REPO."""
        from unittest.mock import patch

        ctx = PipelineContext(
            PROJECT_DIR="/custom/project",
            REPO="custom/repo",
            DEFAULT_BRANCH="develop",
            TEST_CMD="ct",
            BUILD_CMD="cb",
            SKIP_AUTOFIX=True,
        )

        with patch.object(panel, "gh", return_value=("", "", 0)) as mock_gh:
            with patch.object(panel._agent, "spawn_agent", return_value="APPROVED"):
                panel.run_phase5_tech_lead(
                    feature="Test",
                    pr_url="https://github.com/x/y/pull/42",
                    branch="feat/test",
                    spec_path="/tmp/fake-spec.md",
                    impact="LOW",
                    ctx=ctx,
                )
        repo_calls = [c for c in mock_gh.call_args_list
                      if "--repo" in str(c[0]) and "custom/repo" in str(c[0])]
        assert len(repo_calls) >= 1, (
            f"gh should be called with --repo custom/repo. "
            f"All calls: {mock_gh.call_args_list[:5]}"
        )

    def test_ctx_none_still_works(self, panel, test_repo):
        """Backward compat: ctx=None uses module globals."""
        from unittest.mock import patch

        with patch.object(panel, "gh", return_value=("", "", 0)):
            with patch.object(panel._agent, "spawn_agent",
                              return_value="VERDICT: APPROVED\nRISK: LOW\nRELEASE: NO"):
                result = panel.run_phase5_tech_lead(
                    feature="Test",
                    pr_url="https://github.com/x/y/pull/42",
                    branch="feat/test",
                    spec_path="/tmp/fake-spec.md",
                    impact="LOW",
                )
        assert "verdict" in result
