"""Tests for PipelineContext wiring in the dokima entry point — F040 Task 17.

The dokima entry point must create a PipelineContext, populate it from
CLI args and project state, and pass ctx through all call sites
(run_pipeline, run_next_setup, run_fix_mode, vcs functions).
"""

import sys
import os
import pwd
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── PipelineContext in utils ───────────────────────

def test_pipeline_context_importable():
    """PipelineContext is importable from utils."""
    from utils import PipelineContext
    assert PipelineContext is not None


def test_pipeline_context_is_dataclass():
    """PipelineContext is a dataclass (has __dataclass_fields__)."""
    from utils import PipelineContext
    assert hasattr(PipelineContext, '__dataclass_fields__')


def test_pipeline_context_default_values():
    """All fields have correct default values."""
    from utils import PipelineContext
    ctx = PipelineContext()

    assert ctx.PROJECT_DIR == ""
    assert ctx.REPO == ""
    assert ctx.API_KEY == ""
    assert ctx.PANEL_FEATURE == ""
    assert ctx.PANEL_DIR == ""
    assert ctx.DEFAULT_BRANCH == "master"
    assert ctx.TEST_CMD == "npm test"
    assert ctx.BUILD_CMD == "npm run build"
    assert ctx.LINT_CMD == "npm run lint"
    assert ctx.SKIP_AUTOFIX is False
    assert ctx.FORCE_FULL is False
    assert ctx.SKIP_HUMAN_GATE is False
    assert ctx.max_parallel_override is None
    assert ctx.RESUME is None
    assert ctx.FALLBACK_MODELS == {}


def test_pipeline_context_field_override():
    """All fields can be overridden on init."""
    from utils import PipelineContext
    ctx = PipelineContext(
        PROJECT_DIR="/custom/project",
        REPO="owner/custom-repo",
        DEFAULT_BRANCH="develop",
        API_KEY="custom-key",
        PANEL_FEATURE="Custom Feature",
        SKIP_AUTOFIX=True,
        FORCE_FULL=True,
        max_parallel_override=3,
    )

    assert ctx.PROJECT_DIR == "/custom/project"
    assert ctx.REPO == "owner/custom-repo"
    assert ctx.DEFAULT_BRANCH == "develop"
    assert ctx.API_KEY == "custom-key"
    assert ctx.PANEL_FEATURE == "Custom Feature"
    assert ctx.SKIP_AUTOFIX is True
    assert ctx.FORCE_FULL is True
    assert ctx.max_parallel_override == 3


def test_pipeline_context_partial_override():
    """Overriding some fields preserves defaults for others."""
    from utils import PipelineContext
    ctx = PipelineContext(PROJECT_DIR="/only/project", DEFAULT_BRANCH="next")

    assert ctx.PROJECT_DIR == "/only/project"
    assert ctx.DEFAULT_BRANCH == "next"
    assert ctx.REPO == ""
    assert ctx.API_KEY == ""
    assert ctx.SKIP_AUTOFIX is False


def test_pipeline_context_independent_instances():
    """Two PipelineContext instances are independent."""
    from utils import PipelineContext
    ctx_a = PipelineContext(PROJECT_DIR="/proj/a")
    ctx_b = PipelineContext(PROJECT_DIR="/proj/b")

    assert ctx_a.PROJECT_DIR == "/proj/a"
    assert ctx_b.PROJECT_DIR == "/proj/b"
    ctx_a.PROJECT_DIR = "/proj/a-modified"
    assert ctx_a.PROJECT_DIR == "/proj/a-modified"
    assert ctx_b.PROJECT_DIR == "/proj/b"


def test_pipeline_context_field_count():
    """PipelineContext has exactly 21 fields (matching all module globals)."""
    from utils import PipelineContext
    fields = list(PipelineContext.__dataclass_fields__.keys())
    assert len(fields) == 21, f"Expected 21 fields, got {len(fields)}: {fields}"


# ── Dokima entry point imports PipelineContext ────

def test_dokima_exports_pipeline_context():
    """The dokima module exports PipelineContext (imported from utils)."""
    from conftest import _load_panel
    panel = _load_panel()

    # After loading, dokima should have PipelineContext in its namespace
    assert hasattr(panel, 'PipelineContext'), \
        "dokima module must export PipelineContext"
    assert panel.PipelineContext is not None


def test_pipeline_context_instantiable_from_dokima():
    """PipelineContext exported from dokima can be instantiated correctly."""
    from conftest import _load_panel
    panel = _load_panel()
    PipelineContext = panel.PipelineContext

    ctx = PipelineContext(
        PROJECT_DIR="/test/proj",
        REPO="owner/repo",
        DEFAULT_BRANCH="main",
        API_KEY="test-key",
    )

    assert ctx.PROJECT_DIR == "/test/proj"
    assert ctx.REPO == "owner/repo"
    assert ctx.DEFAULT_BRANCH == "main"
    assert ctx.API_KEY == "test-key"


# ── _sync_modules accepts ctx ─────────────────────

def test_sync_modules_accepts_ctx():
    """_sync_modules should accept an optional ctx parameter."""
    import inspect
    from conftest import _load_panel
    panel = _load_panel()

    sig = inspect.signature(panel._sync_modules)
    params = list(sig.parameters.keys())
    assert 'ctx' in params, \
        f"_sync_modules should accept ctx parameter, got params: {params}"


def test_sync_modules_populates_from_ctx():
    """_sync_modules with ctx populates module globals from ctx fields."""
    from conftest import _load_panel
    panel = _load_panel()
    PipelineContext = panel.PipelineContext

    ctx = PipelineContext(
        PROJECT_DIR="/ctx/project",
        REPO="ctx/repo",
        DEFAULT_BRANCH="ctx-main",
        API_KEY="ctx-key",
        SKIP_AUTOFIX=True,
        FORCE_FULL=True,
    )

    panel._sync_modules(ctx=ctx)

    assert panel._utils.PROJECT_DIR == "/ctx/project"
    assert panel._utils.REPO == "ctx/repo"
    assert panel._utils.DEFAULT_BRANCH == "ctx-main"
    assert panel._utils.SKIP_AUTOFIX is True
    assert panel._utils.FORCE_FULL is True


def test_sync_modules_backward_compat_no_ctx():
    """_sync_modules works without ctx (backward compat)."""
    from conftest import _load_panel
    panel = _load_panel()

    # Set globals directly on panel
    panel.PROJECT_DIR = "/backward/proj"
    panel.REPO = "backward/repo"

    # Call _sync_modules without ctx
    panel._sync_modules()

    assert panel._utils.PROJECT_DIR == "/backward/proj"
    assert panel._utils.REPO == "backward/repo"


# ── VCS wiring with ctx ───────────────────────────

def test_dokima_wires_ctx_to_vcs():
    """vcs module is accessed through dokima and accepts ctx param."""
    from conftest import _load_panel
    panel = _load_panel()

    # vcs module imported by dokima should be available
    assert hasattr(panel, 'vcs'), "dokima must import vcs module"

    # Check that key vcs functions accept ctx
    import inspect
    sig = inspect.signature(panel.vcs.detect_vcs_backend)
    params = list(sig.parameters.keys())
    assert 'ctx' in params, \
        f"detect_vcs_backend should accept ctx, got: {params}"


def test_dokima_vcs_parse_vcs_flag_accepts_ctx():
    """vcs.parse_vcs_flag accepts optional ctx."""
    from conftest import _load_panel
    panel = _load_panel()
    import inspect

    sig = inspect.signature(panel.vcs.parse_vcs_flag)
    params = list(sig.parameters.keys())
    assert 'ctx' in params, \
        f"parse_vcs_flag should accept ctx, got: {params}"
