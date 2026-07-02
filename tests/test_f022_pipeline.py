"""F022 Modular Architecture — test that pipeline.py exists with all required functions."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest


def test_pipeline_module_importable():
    """pipeline.py must exist and be importable."""
    import pipeline
    assert pipeline is not None

def test_pipeline_has_run_pipeline():
    import pipeline
    assert hasattr(pipeline, "run_pipeline")
    assert callable(pipeline.run_pipeline)

def test_pipeline_has_run_phase1_strategist():
    import pipeline
    assert hasattr(pipeline, "run_phase1_strategist")
    assert callable(pipeline.run_phase1_strategist)

def test_pipeline_has_run_phase2_coder():
    import pipeline
    assert hasattr(pipeline, "run_phase2_coder")
    assert callable(pipeline.run_phase2_coder)

def test_pipeline_has_run_phase3_vet():
    import pipeline
    assert hasattr(pipeline, "run_phase3_vet")
    assert callable(pipeline.run_phase3_vet)

def test_pipeline_has_run_phase4_nm():
    import pipeline
    assert hasattr(pipeline, "run_phase4_nm")
    assert callable(pipeline.run_phase4_nm)

def test_pipeline_has_run_phase5_tech_lead():
    import pipeline
    assert hasattr(pipeline, "run_phase5_tech_lead")
    assert callable(pipeline.run_phase5_tech_lead)

def test_pipeline_has_run_fix_mode():
    import pipeline
    assert hasattr(pipeline, "run_fix_mode")
    assert callable(pipeline.run_fix_mode)

def test_pipeline_has_run_post_pipeline():
    import pipeline
    assert hasattr(pipeline, "run_post_pipeline")
    assert callable(pipeline.run_post_pipeline)

def test_pipeline_has_discover_blocked_pr():
    import pipeline
    assert hasattr(pipeline, "discover_blocked_pr")
    assert callable(pipeline.discover_blocked_pr)

def test_pipeline_has_extract_blockers_from_pr():
    import pipeline
    assert hasattr(pipeline, "extract_blockers_from_pr")
    assert callable(pipeline.extract_blockers_from_pr)


# ── F027: Codebase map hint injection ────────────────────────────

def test_make_map_hint_exists(tmp_path):
    """When map file exists, _make_map_hint returns a hint string."""
    import pipeline
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    map_path = specs_dir / "codebase-map.md"
    map_path.write_text("# Test Map\n\nSome content here.")

    hint = pipeline._make_map_hint(str(tmp_path))
    assert "codebase-map.md" in hint
    assert str(os.path.getsize(str(map_path))) in hint


def test_make_map_hint_missing(tmp_path):
    """When map file does not exist, _make_map_hint returns empty string."""
    import pipeline
    hint = pipeline._make_map_hint(str(tmp_path))
    assert hint == ""


def test_make_map_hint_empty_file(tmp_path):
    """When map file is 0 bytes, _make_map_hint returns empty string."""
    import pipeline
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    map_path = specs_dir / "codebase-map.md"
    map_path.write_text("")

    hint = pipeline._make_map_hint(str(tmp_path))
    assert hint == ""
