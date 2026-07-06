"""Tests for F041 Task 8: roadmap.py imports from 4 new domain modules.

Verify that roadmap.py imports VCS/token functions from git_ops.py,
spec extraction functions from spec_extract.py,
map generation from codebase_map.py,
control panel functions from control_panel.py,
and remaining infrastructure from slimmed utils.py.
"""
import pytest
import importlib
import sys


class TestRoadmapImports:
    """Verify roadmap.py imports from correct domain modules."""

    # ── git_ops.py symbols ──────────────────────────────────────

    def test_roadmap_imports_git_from_git_ops(self):
        """roadmap.git should be the function object from git_ops, not utils."""
        import roadmap
        from git_ops import git as git_ops_git
        assert roadmap.git is git_ops_git, (
            "roadmap.git should be git_ops.git"
        )

    def test_roadmap_imports_gh_from_git_ops(self):
        """roadmap.gh should be the function object from git_ops."""
        import roadmap
        from git_ops import gh as git_ops_gh
        assert roadmap.gh is git_ops_gh, (
            "roadmap.gh should be git_ops.gh"
        )

    def test_roadmap_imports_load_key_from_git_ops(self):
        """roadmap.load_key should be the function object from git_ops."""
        import roadmap
        from git_ops import load_key as git_ops_load_key
        assert roadmap.load_key is git_ops_load_key, (
            "roadmap.load_key should be git_ops.load_key"
        )

    def test_roadmap_imports_detect_repo_from_git_ops(self):
        """roadmap.detect_repo should be the function object from git_ops."""
        import roadmap
        from git_ops import detect_repo as git_ops_detect_repo
        assert roadmap.detect_repo is git_ops_detect_repo, (
            "roadmap.detect_repo should be git_ops.detect_repo"
        )

    def test_roadmap_imports_load_github_token_from_git_ops(self):
        """roadmap.load_github_token should be the function object from git_ops."""
        import roadmap
        from git_ops import load_github_token as git_ops_load_github_token
        assert roadmap.load_github_token is git_ops_load_github_token, (
            "roadmap.load_github_token should be git_ops.load_github_token"
        )

    def test_roadmap_imports_safe_run_from_git_ops(self):
        """roadmap._safe_run should be the function object from git_ops."""
        import roadmap
        from git_ops import _safe_run as git_ops_safe_run
        assert roadmap._safe_run is git_ops_safe_run, (
            "roadmap._safe_run should be git_ops._safe_run"
        )

    # ── spec_extract.py symbols ─────────────────────────────────

    def test_roadmap_imports_extract_pr_sections_from_spec_extract(self):
        """roadmap.extract_pr_sections should be from spec_extract."""
        import roadmap
        from spec_extract import extract_pr_sections as se_extract_pr_sections
        assert roadmap.extract_pr_sections is se_extract_pr_sections, (
            "roadmap.extract_pr_sections should be spec_extract.extract_pr_sections"
        )

    def test_roadmap_imports_clean_spec_content_from_spec_extract(self):
        """roadmap.clean_spec_content should be from spec_extract."""
        import roadmap
        from spec_extract import clean_spec_content as se_clean_spec_content
        assert roadmap.clean_spec_content is se_clean_spec_content, (
            "roadmap.clean_spec_content should be spec_extract.clean_spec_content"
        )

    def test_roadmap_imports_verify_spec_quality_from_spec_extract(self):
        """roadmap.verify_spec_quality should be from spec_extract."""
        import roadmap
        from spec_extract import verify_spec_quality as se_verify_spec_quality
        assert roadmap.verify_spec_quality is se_verify_spec_quality, (
            "roadmap.verify_spec_quality should be spec_extract.verify_spec_quality"
        )

    def test_roadmap_imports_extract_tl_verdict_from_spec_extract(self):
        """roadmap._extract_tl_verdict should be from spec_extract."""
        import roadmap
        from spec_extract import _extract_tl_verdict as se_extract_tl_verdict
        assert roadmap._extract_tl_verdict is se_extract_tl_verdict, (
            "roadmap._extract_tl_verdict should be spec_extract._extract_tl_verdict"
        )

    def test_roadmap_imports_extract_tl_blockers_from_spec_extract(self):
        """roadmap._extract_tl_blockers should be from spec_extract."""
        import roadmap
        from spec_extract import _extract_tl_blockers as se_extract_tl_blockers
        assert roadmap._extract_tl_blockers is se_extract_tl_blockers, (
            "roadmap._extract_tl_blockers should be spec_extract._extract_tl_blockers"
        )

    def test_roadmap_imports_extract_file_paths_from_spec_extract(self):
        """roadmap.extract_file_paths should be from spec_extract."""
        import roadmap
        from spec_extract import extract_file_paths as se_extract_file_paths
        assert roadmap.extract_file_paths is se_extract_file_paths, (
            "roadmap.extract_file_paths should be spec_extract.extract_file_paths"
        )

    def test_roadmap_imports_extract_agent_messages_from_spec_extract(self):
        """roadmap.extract_agent_messages should be from spec_extract."""
        import roadmap
        from spec_extract import extract_agent_messages as se_extract_agent_messages
        assert roadmap.extract_agent_messages is se_extract_agent_messages, (
            "roadmap.extract_agent_messages should be spec_extract.extract_agent_messages"
        )

    # ── codebase_map.py symbols ─────────────────────────────────

    def test_roadmap_imports_generate_codebase_map_from_codebase_map(self):
        """roadmap.generate_codebase_map should be from codebase_map."""
        import roadmap
        from codebase_map import generate_codebase_map as cm_generate_codebase_map
        assert roadmap.generate_codebase_map is cm_generate_codebase_map, (
            "roadmap.generate_codebase_map should be codebase_map.generate_codebase_map"
        )

    # ── control_panel.py symbols ────────────────────────────────

    def test_roadmap_imports_update_status_md_from_control_panel(self):
        """roadmap.update_status_md should be from control_panel."""
        import roadmap
        from control_panel import update_status_md as cp_update_status_md
        assert roadmap.update_status_md is cp_update_status_md, (
            "roadmap.update_status_md should be control_panel.update_status_md"
        )

    def test_roadmap_imports_show_help_from_control_panel(self):
        """roadmap.show_help should be from control_panel."""
        import roadmap
        from control_panel import show_help as cp_show_help
        assert roadmap.show_help is cp_show_help, (
            "roadmap.show_help should be control_panel.show_help"
        )

    def test_roadmap_imports_check_upgrade_from_control_panel(self):
        """roadmap.check_upgrade should be from control_panel."""
        import roadmap
        from control_panel import check_upgrade as cp_check_upgrade
        assert roadmap.check_upgrade is cp_check_upgrade, (
            "roadmap.check_upgrade should be control_panel.check_upgrade"
        )

    # ── utils.py symbols (should still come from utils) ─────────

    def test_roadmap_imports_slugify_from_utils(self):
        """roadmap.slugify should still come from utils (cross-cutting)."""
        import roadmap
        from utils import slugify as utils_slugify
        assert roadmap.slugify is utils_slugify, (
            "roadmap.slugify should be utils.slugify"
        )

    def test_roadmap_imports_project_dir_from_utils(self):
        """roadmap.PROJECT_DIR should still come from utils (global)."""
        import roadmap
        from utils import PROJECT_DIR as utils_PROJECT_DIR
        assert roadmap.PROJECT_DIR is utils_PROJECT_DIR, (
            "roadmap.PROJECT_DIR should be utils.PROJECT_DIR"
        )

    def test_roadmap_imports_default_branch_from_utils(self):
        """roadmap.DEFAULT_BRANCH should still come from utils (global)."""
        import roadmap
        from utils import DEFAULT_BRANCH as utils_DEFAULT_BRANCH
        assert roadmap.DEFAULT_BRANCH is utils_DEFAULT_BRANCH, (
            "roadmap.DEFAULT_BRANCH should be utils.DEFAULT_BRANCH"
        )

    def test_roadmap_imports_repo_from_utils(self):
        """roadmap.REPO should still come from utils (global)."""
        import roadmap
        from utils import REPO as utils_REPO
        assert roadmap.REPO is utils_REPO, (
            "roadmap.REPO should be utils.REPO"
        )

    # ── Deferred imports (line ~562) ───────────────────────────

    def test_roadmap_deferred_import_ensure_profiles_from_utils(self):
        """ensure_profiles should still come from utils (deferred import)."""
        import roadmap
        from utils import ensure_profiles as utils_ensure_profiles
        assert roadmap.ensure_profiles is utils_ensure_profiles, (
            "roadmap.ensure_profiles should be utils.ensure_profiles"
        )

    def test_roadmap_deferred_import_deploy_profile_skills_from_utils(self):
        """deploy_profile_skills should still come from utils (deferred import)."""
        import roadmap
        from utils import deploy_profile_skills as utils_deploy_profile_skills
        assert roadmap.deploy_profile_skills is utils_deploy_profile_skills, (
            "roadmap.deploy_profile_skills should be utils.deploy_profile_skills"
        )

    # ── Clean import check ─────────────────────────────────────

    def test_roadmap_imports_without_error(self):
        """roadmap module should import cleanly without ImportError."""
        if 'roadmap' in sys.modules:
            del sys.modules['roadmap']
        try:
            import roadmap
            assert hasattr(roadmap, 'parse_roadmap')
            assert hasattr(roadmap, 'run_next_setup')
            assert hasattr(roadmap, 'run_add_to_roadmap')
        except ImportError as e:
            pytest.fail(f"roadmap failed to import: {e}")
