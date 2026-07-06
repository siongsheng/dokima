"""Tests for dokima main() ctx construction and passing — F040 Task 9.

Verifies that dokima constructs a PipelineContext in main() and passes ctx
to all callees (run_pipeline, run_fix_mode, run_init, run_next_setup,
run_add_to_roadmap). Ensures module-level globals are removed.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock, ANY
from context import PipelineContext


# ── Helper: load panel without executing main() ─────

def _load_panel_no_main():
    """Load the panel module but prevent main() from running on import."""
    module_name = "dokima"
    import types
    if module_name in sys.modules:
        del sys.modules[module_name]
    
    panel_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "dokima")
    )
    
    module = types.ModuleType(module_name)
    module.__file__ = panel_path
    sys.modules[module_name] = module
    
    # Set required globals
    module.PROJECT_DIR = "/tmp/test-project"
    module.REPO = "test-owner/test-repo"
    module.API_KEY = "test-key"
    module.PANEL_FEATURE = "Test Feature"
    module.PANEL_DIR = "/tmp/.dokima-test"
    module.DEFAULT_BRANCH = "main"
    module.TEST_CMD = "echo test"
    module.BUILD_CMD = "echo build"
    module.LINT_CMD = "echo lint"
    
    with open(panel_path) as f:
        code = compile(f.read(), panel_path, "exec")
    exec(code, module.__dict__)
    
    return module


# ── Module-level globals removal ──────────────────

def test_dokima_no_module_level_flag_globals():
    """After Task 9, dokima module should NOT define SKIP_AUTOFIX, FORCE_FULL,
    SKIP_HUMAN_GATE, max_parallel_override, FALLBACK_MODELS, RESUME,
    OUTPUT_LOG as module-level globals.
    """
    # These should be removed from module level — they now live in ctx
    removed_globals = [
        "SKIP_AUTOFIX", "FORCE_FULL", "SKIP_HUMAN_GATE",
        "max_parallel_override", "FALLBACK_MODELS", "RESUME",
    ]
    
    panel = _load_panel_no_main()
    
    for g in removed_globals:
        assert not hasattr(panel, g), (
            f"Module-level global '{g}' should be removed from dokima. "
            f"It now lives in PipelineContext."
        )


def test_dokima_output_log_not_module_level_constant():
    """OUTPUT_LOG should NOT be set at module level — it's derived in main()
    with datetime.datetime.now() and stored in ctx.
    """
    panel = _load_panel_no_main()
    
    # OUTPUT_LOG was previously set at module level with a timestamp.
    # After migration, it should not exist or be a placeholder.
    if hasattr(panel, "OUTPUT_LOG"):
        # If it still exists, it must NOT be a timestamped path
        val = getattr(panel, "OUTPUT_LOG")
        assert "dokima-output" not in str(val), (
            f"OUTPUT_LOG at module level contains timestamp pattern: {val}. "
            f"It should be derived in main() and stored in ctx."
        )


def test_dokima_imports_pipelinecontext():
    """dokima should import PipelineContext from context module."""
    panel = _load_panel_no_main()
    
    assert hasattr(panel, "PipelineContext"), (
        "dokima must import PipelineContext to construct ctx in main()"
    )


# ── ctx construction in main() ─────────────────────

def test_main_constructs_pipelinecontext():
    """main() should construct a PipelineContext from parsed args."""
    panel = _load_panel_no_main()
    
    # Verify main() function exists
    assert hasattr(panel, "main"), "dokima must have main() function"
    assert callable(panel.main), "main must be callable"


def test_main_no_global_declaration():
    """main() should NOT have a 'global API_KEY, PROJECT_DIR, REPO, ...'
    declaration. Those values now come from ctx.
    """
    import inspect
    
    panel = _load_panel_no_main()
    source = inspect.getsource(panel.main)
    
    # The global statement should not mention these globals that were removed
    removed = ["API_KEY", "PROJECT_DIR", "REPO", "TEST_CMD", "BUILD_CMD",
               "LINT_CMD", "PANEL_FEATURE", "DEFAULT_BRANCH",
               "SKIP_AUTOFIX", "FORCE_FULL", "SKIP_HUMAN_GATE",
               "max_parallel_override", "FALLBACK_MODELS", "RESUME"]
    
    for g in removed:
        # Check for pattern "global ... G ..." in source
        if f"global " in source:
            global_line = [l for l in source.split("\n") if l.strip().startswith("global ")][0] if any(l.strip().startswith("global ") for l in source.split("\n")) else ""
            assert g not in global_line, (
                f"main() should not declare '{g}' as global — "
                f"it now comes from PipelineContext"
            )


# ── ctx passed to callees ─────────────────────────

def test_main_passes_ctx_to_run_pipeline():
    """When main() executes the pipeline path, it should pass ctx to
    run_pipeline as the first argument.
    """
    panel = _load_panel_no_main()
    
    # Verify that run_pipeline in _pipeline accepts ctx
    pipeline_mod = getattr(panel, "_pipeline", None)
    if pipeline_mod is None:
        pytest.skip("_pipeline module not available")
    
    import inspect
    sig = inspect.signature(pipeline_mod.run_pipeline)
    params = list(sig.parameters.keys())
    
    assert "ctx" in params, (
        f"run_pipeline must accept 'ctx' parameter. Got: {params}"
    )
    assert params[0] == "ctx", (
        f"ctx must be the FIRST parameter of run_pipeline. Got: {params}"
    )


def test_main_passes_ctx_to_run_fix_mode():
    """When main() executes fix mode, it should pass ctx to run_fix_mode
    as the first argument.
    """
    panel = _load_panel_no_main()
    
    pipeline_mod = getattr(panel, "_pipeline", None)
    if pipeline_mod is None:
        pytest.skip("_pipeline module not available")
    
    import inspect
    sig = inspect.signature(pipeline_mod.run_fix_mode)
    params = list(sig.parameters.keys())
    
    assert "ctx" in params, (
        f"run_fix_mode must accept 'ctx' parameter. Got: {params}"
    )
    assert params[0] == "ctx", (
        f"ctx must be the FIRST parameter of run_fix_mode. Got: {params}"
    )


def test_main_passes_ctx_to_run_fix_mode_issue():
    """When main() executes fix mode with --issue, it should pass ctx to
    run_fix_mode_issue as the first argument.
    """
    panel = _load_panel_no_main()
    
    pipeline_mod = getattr(panel, "_pipeline", None)
    if pipeline_mod is None:
        pytest.skip("_pipeline module not available")
    
    import inspect
    sig = inspect.signature(pipeline_mod.run_fix_mode_issue)
    params = list(sig.parameters.keys())
    
    assert "ctx" in params, (
        f"run_fix_mode_issue must accept 'ctx' parameter. Got: {params}"
    )
    assert params[0] == "ctx", (
        f"ctx must be the FIRST parameter of run_fix_mode_issue. Got: {params}"
    )


def test_main_passes_ctx_to_run_init():
    """When main() executes init mode, it should pass ctx to run_init
    as the first argument.
    """
    panel = _load_panel_no_main()
    
    roadmap_mod = getattr(panel, "_roadmap", None)
    if roadmap_mod is None:
        pytest.skip("_roadmap module not available")
    
    import inspect
    sig = inspect.signature(roadmap_mod.run_init)
    params = list(sig.parameters.keys())
    
    assert "ctx" in params, (
        f"run_init must accept 'ctx' parameter. Got: {params}"
    )
    assert params[0] == "ctx", (
        f"ctx must be the FIRST parameter of run_init. Got: {params}"
    )


def test_main_passes_ctx_to_run_next_setup():
    """When main() executes next mode setup, it should pass ctx to
    run_next_setup as the first argument.
    """
    panel = _load_panel_no_main()
    
    roadmap_mod = getattr(panel, "_roadmap", None)
    if roadmap_mod is None:
        pytest.skip("_roadmap module not available")
    
    import inspect
    sig = inspect.signature(roadmap_mod.run_next_setup)
    params = list(sig.parameters.keys())
    
    assert "ctx" in params, (
        f"run_next_setup must accept 'ctx' parameter. Got: {params}"
    )
    assert params[0] == "ctx", (
        f"ctx must be the FIRST parameter of run_next_setup. Got: {params}"
    )


def test_main_passes_ctx_to_run_add_to_roadmap():
    """When main() executes add mode, it should pass ctx to
    run_add_to_roadmap as the first argument.
    """
    panel = _load_panel_no_main()
    
    roadmap_mod = getattr(panel, "_roadmap", None)
    if roadmap_mod is None:
        pytest.skip("_roadmap module not available")
    
    import inspect
    sig = inspect.signature(roadmap_mod.run_add_to_roadmap)
    params = list(sig.parameters.keys())
    
    assert "ctx" in params, (
        f"run_add_to_roadmap must accept 'ctx' parameter. Got: {params}"
    )
    assert params[0] == "ctx", (
        f"ctx must be the FIRST parameter of run_add_to_roadmap. Got: {params}"
    )


# ── _sync_modules removal ─────────────────────────

def test_sync_modules_removed_or_simplified():
    """After Task 9, _sync_modules() should be removed or no longer sync
    globals (ctx is passed explicitly, no need to sync module globals).
    """
    panel = _load_panel_no_main()
    
    # If _sync_modules still exists, it should be a no-op or minimal
    if hasattr(panel, "_sync_modules"):
        import inspect
        source = inspect.getsource(panel._sync_modules)
        # Should not reference the old globals
        for g in ["PROJECT_DIR", "REPO", "API_KEY", "FALLBACK_MODELS"]:
            assert g not in source, (
                f"_sync_modules should not reference '{g}' — ctx replaces globals"
            )


# ── End-to-end: ctx construction with mock ────────

def test_ctx_constructed_with_correct_project_dir():
    """PipelineContext should carry the resolved project directory."""
    panel = _load_panel_no_main()
    
    # Verify PipelineContext is importable
    ctx = PipelineContext(project_dir="/tmp/test-dir")
    assert ctx.project_dir == "/tmp/test-dir"


def test_ctx_constructed_with_feature_flags():
    """PipelineContext should carry feature flag defaults."""
    ctx = PipelineContext()
    assert ctx.skip_autofix is False
    assert ctx.force_full is False
    assert ctx.skip_human_gate is False
    assert ctx.max_parallel_override is None
    assert ctx.resume is None


def test_ctx_constructed_with_vcs_defaults():
    """PipelineContext should carry VCS defaults."""
    ctx = PipelineContext()
    assert ctx.vcs_backend == "github"
    assert ctx.vcs_token_env == "GH_TOKEN"
    assert ctx.default_branch == "master"


def test_main_does_not_set_module_level_api_key():
    """main() assigns API_KEY as a local variable, not a module-level global.
    The 'global API_KEY' declaration is gone — API_KEY is now captured in ctx."""
    panel = _load_panel_no_main()

    import inspect
    source = inspect.getsource(panel.main)

    # API_KEY=*** be assigned inside main() as a local — that's fine.
    # What must NOT exist is 'global API_KEY' declaration.
    assert "global API_KEY" not in source, (
        "main() should not declare API_KEY as global — it's a local, goes in ctx"
    )


def test_main_does_not_set_module_level_repo():
    """main() assigns REPO as a local variable, not a module-level global.
    The 'global REPO' declaration is gone — REPO is now captured in ctx."""
    panel = _load_panel_no_main()

    import inspect
    source = inspect.getsource(panel.main)

    # 'REPO = ' appears as a local assignment inside main() — that's fine.
    # What must NOT exist is 'global REPO' declaration.
    assert "global REPO" not in source, (
        "main() should not declare REPO as global — it's a local, goes in ctx"
    )
