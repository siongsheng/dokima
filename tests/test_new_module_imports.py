"""Tests for F041 Task 10 — dokima entry script imports from 4 domain modules.

Verifies:
1. All 4 new domain modules are importable
2. Each module exports the correct functions
3. The dokima entry script compiles after import updates
"""
import sys
import os
import importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ── git_ops.py ──────────────────────────────────────────────────

GIT_OPS_FUNCTIONS = [
    "git", "gh", "_safe_run", "detect_repo", "detect_commands",
    "_detect_referenced_repo", "_supplement_pr_sections", "_detect_default_branch",
    "_set_vcs_token", "_load_token_from_env_file", "_set_gh_token",
    "load_key", "load_github_token", "try_auto_merge",
    "_bump_version", "_prune_old_tags", "_update_docs_cache",
    "do_release", "halt_and_revert",
]


class TestGitOpsModule:
    """git_ops.py — VCS, token, and release operations."""

    def test_module_importable(self):
        import git_ops  # noqa: F401

    @pytest.mark.parametrize("func_name", GIT_OPS_FUNCTIONS)
    def test_function_exists(self, func_name):
        import git_ops
        assert hasattr(git_ops, func_name), f"git_ops missing: {func_name}"
        assert callable(getattr(git_ops, func_name)), f"{func_name} not callable"

    def test_gh_token_cache_exists(self):
        import git_ops
        assert hasattr(git_ops, "_GH_TOKEN_CACHE")
        assert git_ops._GH_TOKEN_CACHE is None

    def test_bump_version_patch(self):
        import git_ops
        assert git_ops._bump_version("1.2.1", "patch") == "1.2.2"

    def test_bump_version_minor(self):
        import git_ops
        assert git_ops._bump_version("1.2.1", "minor") == "1.3.0"

    def test_bump_version_major(self):
        import git_ops
        assert git_ops._bump_version("1.2.1", "major") == "2.0.0"

    def test_bump_version_invalid(self):
        import git_ops
        with pytest.raises(ValueError):
            git_ops._bump_version("1.2.1", "nonsense")


# ── spec_extract.py ─────────────────────────────────────────────

SPEC_EXTRACT_FUNCTIONS = [
    "extract_pr_sections", "extract_agent_messages", "clean_spec_content",
    "verify_spec_quality", "_check_pr_body_quality",
    "extract_issue_sections", "format_blocker_cross_reference",
    "extract_should_fix_from_text",
]


class TestSpecExtractModule:
    """spec_extract.py — text processing and spec extraction."""

    def test_module_importable(self):
        import spec_extract  # noqa: F401

    @pytest.mark.parametrize("func_name", SPEC_EXTRACT_FUNCTIONS)
    def test_function_exists(self, func_name):
        import spec_extract
        assert hasattr(spec_extract, func_name), f"spec_extract missing: {func_name}"
        assert callable(getattr(spec_extract, func_name)), f"{func_name} not callable"

    def test_extract_pr_sections_basic(self):
        from spec_extract import extract_pr_sections
        spec = """# Feature — Spec

## 3. Impact

Minimal impact.

## 4. What Changed

- `src/main.py` **(NEW)**: Main entry point
"""
        result = extract_pr_sections(spec, "Feature")
        assert "## Why" in result
        assert "src/main.py" in result

    def test_clean_spec_strips_chatter(self):
        from spec_extract import clean_spec_content
        raw = "I understand now.\n\n# Feature — Spec\n\n## Decision Table\n"
        result = clean_spec_content(raw)
        assert "I understand" not in result
        assert result.startswith("# Feature")


# ── codebase_map.py ─────────────────────────────────────────────

CODEBASE_MAP_FUNCTIONS = [
    "generate_codebase_map", "load_map_enrichments",
    "save_map_enrichments", "extract_map_enrichments",
]

CODEBASE_MAP_PRIVATE = [
    "_classify_domain", "_build_domain_map", "_build_impact_map",
    "_build_test_map", "_find_key_files", "_describe_file",
]


class TestCodebaseMapModule:
    """codebase_map.py — domain-aware project mapping."""

    def test_module_importable(self):
        import codebase_map  # noqa: F401

    @pytest.mark.parametrize("func_name", CODEBASE_MAP_FUNCTIONS)
    def test_public_function_exists(self, func_name):
        import codebase_map
        assert hasattr(codebase_map, func_name), f"codebase_map missing: {func_name}"
        assert callable(getattr(codebase_map, func_name)), f"{func_name} not callable"

    @pytest.mark.parametrize("func_name", CODEBASE_MAP_PRIVATE)
    def test_private_function_exists(self, func_name):
        import codebase_map
        assert hasattr(codebase_map, func_name), f"codebase_map missing: {func_name}"
        assert callable(getattr(codebase_map, func_name)), f"{func_name} not callable"

    def test_generate_codebase_map_signature(self):
        import codebase_map
        import inspect
        sig = inspect.signature(codebase_map.generate_codebase_map)
        params = list(sig.parameters.keys())
        assert "project_dir" in params
        assert "full" in params


# ── control_panel.py ────────────────────────────────────────────

CONTROL_PANEL_FUNCTIONS = [
    "handle_status", "handle_stop", "handle_kill", "handle_list_crons",
    "show_help", "show_help_json", "check_upgrade", "_version_newer",
    "_parse_status_md", "_make_status_entry", "update_status_md",
    "_get_lock_state",
]


class TestControlPanelModule:
    """control_panel.py — CLI control, status, help, stop, kill."""

    def test_module_importable(self):
        import control_panel  # noqa: F401

    @pytest.mark.parametrize("func_name", CONTROL_PANEL_FUNCTIONS)
    def test_function_exists(self, func_name):
        import control_panel
        assert hasattr(control_panel, func_name), f"control_panel missing: {func_name}"
        assert callable(getattr(control_panel, func_name)), f"{func_name} not callable"


# ── Dokima entry script compilation ─────────────────────────────

def test_dokima_entry_compiles():
    """The dokima entry script must compile after import updates."""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dokima_path = os.path.join(script_dir, "dokima")
    with open(dokima_path) as f:
        source = f.read()
    compile(source, dokima_path, "exec")
