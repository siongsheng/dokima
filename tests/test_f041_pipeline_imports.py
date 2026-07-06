"""Tests for F041 Task 6: pipeline.py imports from 4 domain modules.

Verify that pipeline.py imports functions from the correct domain modules
(git_ops, spec_extract, codebase_map, control_panel) instead of utils.
"""
import pytest


class TestPipelineImports:
    """pipeline.py should import from 4 new domain modules, not utils."""

    # ── git_ops ─────────────────────────────────────
    def test_pipeline_git_from_git_ops(self):
        """git() in pipeline should come from git_ops, not utils."""
        import pipeline
        assert pipeline.git.__module__ == 'git_ops', \
            f"pipeline.git from {pipeline.git.__module__}, expected git_ops"

    def test_pipeline_gh_from_git_ops(self):
        """gh() in pipeline should come from git_ops, not utils."""
        import pipeline
        assert pipeline.gh.__module__ == 'git_ops', \
            f"pipeline.gh from {pipeline.gh.__module__}, expected git_ops"

    def test_pipeline_safe_run_from_git_ops(self):
        """_safe_run() in pipeline should come from git_ops, not utils."""
        import pipeline
        assert pipeline._safe_run.__module__ == 'git_ops', \
            f"pipeline._safe_run from {pipeline._safe_run.__module__}, expected git_ops"

    def test_pipeline_detect_repo_from_git_ops(self):
        """detect_repo() in pipeline should come from git_ops, not utils."""
        import pipeline
        assert pipeline.detect_repo.__module__ == 'git_ops', \
            f"pipeline.detect_repo from {pipeline.detect_repo.__module__}, expected git_ops"

    def test_pipeline_load_github_token_from_git_ops(self):
        """load_github_token() in pipeline should come from git_ops, not utils."""
        import pipeline
        assert pipeline.load_github_token.__module__ == 'git_ops', \
            f"pipeline.load_github_token from {pipeline.load_github_token.__module__}, expected git_ops"

    def test_pipeline_halt_and_revert_from_git_ops(self):
        """halt_and_revert() in pipeline should come from git_ops, not utils."""
        import pipeline
        assert pipeline.halt_and_revert.__module__ == 'git_ops', \
            f"pipeline.halt_and_revert from {pipeline.halt_and_revert.__module__}, expected git_ops"

    # ── spec_extract ────────────────────────────────
    def test_pipeline_extract_pr_sections_from_spec_extract(self):
        """extract_pr_sections() should come from spec_extract, not utils."""
        import pipeline
        assert pipeline.extract_pr_sections.__module__ == 'spec_extract', \
            f"pipeline.extract_pr_sections from {pipeline.extract_pr_sections.__module__}, expected spec_extract"

    def test_pipeline_clean_spec_content_from_spec_extract(self):
        """clean_spec_content() should come from spec_extract, not utils."""
        import pipeline
        assert pipeline.clean_spec_content.__module__ == 'spec_extract', \
            f"pipeline.clean_spec_content from {pipeline.clean_spec_content.__module__}, expected spec_extract"

    def test_pipeline_verify_spec_quality_from_spec_extract(self):
        """verify_spec_quality() should come from spec_extract, not utils."""
        import pipeline
        assert pipeline.verify_spec_quality.__module__ == 'spec_extract', \
            f"pipeline.verify_spec_quality from {pipeline.verify_spec_quality.__module__}, expected spec_extract"

    def test_pipeline_extract_issue_sections_from_spec_extract(self):
        """extract_issue_sections() should come from spec_extract, not utils."""
        import pipeline
        assert pipeline.extract_issue_sections.__module__ == 'spec_extract', \
            f"pipeline.extract_issue_sections from {pipeline.extract_issue_sections.__module__}, expected spec_extract"

    def test_pipeline_format_blocker_cross_reference_from_spec_extract(self):
        """format_blocker_cross_reference() should come from spec_extract, not utils."""
        import pipeline
        assert pipeline.format_blocker_cross_reference.__module__ == 'spec_extract', \
            f"pipeline.format_blocker_cross_reference from {pipeline.format_blocker_cross_reference.__module__}, expected spec_extract"

    # ── codebase_map ────────────────────────────────
    def test_pipeline_generate_codebase_map_from_codebase_map(self):
        """generate_codebase_map() should come from codebase_map, not utils."""
        import pipeline
        assert pipeline.generate_codebase_map.__module__ == 'codebase_map', \
            f"pipeline.generate_codebase_map from {pipeline.generate_codebase_map.__module__}, expected codebase_map"

    def test_pipeline_describe_file_from_codebase_map(self):
        """_describe_file() should come from codebase_map, not utils."""
        import pipeline
        assert pipeline._describe_file.__module__ == 'codebase_map', \
            f"pipeline._describe_file from {pipeline._describe_file.__module__}, expected codebase_map"

    def test_pipeline_extract_map_enrichments_from_codebase_map(self):
        """extract_map_enrichments() should come from codebase_map, not utils."""
        import pipeline
        assert pipeline.extract_map_enrichments.__module__ == 'codebase_map', \
            f"pipeline.extract_map_enrichments from {pipeline.extract_map_enrichments.__module__}, expected codebase_map"

    # ── control_panel ───────────────────────────────
    def test_pipeline_handle_status_from_control_panel(self):
        """handle_status() should come from control_panel, not utils."""
        import pipeline
        assert pipeline.handle_status.__module__ == 'control_panel', \
            f"pipeline.handle_status from {pipeline.handle_status.__module__}, expected control_panel"

    def test_pipeline_show_help_from_control_panel(self):
        """show_help() should come from control_panel, not utils."""
        import pipeline
        assert pipeline.show_help.__module__ == 'control_panel', \
            f"pipeline.show_help from {pipeline.show_help.__module__}, expected control_panel"

    def test_pipeline_update_status_md_from_control_panel(self):
        """update_status_md() should come from control_panel, not utils."""
        import pipeline
        assert pipeline.update_status_md.__module__ == 'control_panel', \
            f"pipeline.update_status_md from {pipeline.update_status_md.__module__}, expected control_panel"

    # ── utils (still from utils) ────────────────────
    def test_pipeline_slugify_stays_in_utils(self):
        """slugify() should still come from utils."""
        import pipeline
        assert pipeline.slugify.__module__ == 'utils', \
            f"pipeline.slugify from {pipeline.slugify.__module__}, expected utils"

    def test_pipeline_acquire_lock_stays_in_utils(self):
        """acquire_lock() should still come from utils."""
        import pipeline
        assert pipeline.acquire_lock.__module__ == 'utils', \
            f"pipeline.acquire_lock from {pipeline.acquire_lock.__module__}, expected utils"

    def test_pipeline_save_checkpoint_stays_in_utils(self):
        """save_checkpoint() should still come from utils."""
        import pipeline
        assert pipeline.save_checkpoint.__module__ == 'utils', \
            f"pipeline.save_checkpoint from {pipeline.save_checkpoint.__module__}, expected utils"

    def test_pipeline_lock_path_stays_in_utils(self):
        """_lock_path() should still come from utils."""
        import pipeline
        assert pipeline._lock_path.__module__ == 'utils', \
            f"pipeline._lock_path from {pipeline._lock_path.__module__}, expected utils"
