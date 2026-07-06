"""Tests for PipelineContext dataclass — F040 Task 1.

PipelineContext replaces 20+ module-level globals with a single dataclass
passed to each phase function, eliminating conftest __setattr__ override hacks.
"""

import sys
import os
import pwd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# ── PipelineContext importability ──────────────────

def test_pipeline_context_importable():
    """PipelineContext is importable from utils."""
    from utils import PipelineContext
    assert PipelineContext is not None


def test_pipeline_context_is_dataclass():
    """PipelineContext is a dataclass (has __dataclass_fields__)."""
    from utils import PipelineContext
    assert hasattr(PipelineContext, '__dataclass_fields__')


# ── Default values ─────────────────────────────────

def test_pipeline_context_default_values():
    """All fields have correct default values."""
    from utils import PipelineContext
    ctx = PipelineContext()

    # String fields with empty defaults
    assert ctx.PROJECT_DIR == ""
    assert ctx.REPO == ""
    assert ctx.API_KEY == ""
    assert ctx.PANEL_FEATURE == ""
    assert ctx.PANEL_DIR == ""

    # String fields with non-empty defaults
    assert ctx.DEFAULT_BRANCH == "master"
    assert ctx.OUTPUT_LOG == "/tmp/dokima-output.txt"
    assert ctx.TEST_CMD == "npm test"
    assert ctx.BUILD_CMD == "npm run build"
    assert ctx.LINT_CMD == "npm run lint"

    # Bool fields
    assert ctx.SKIP_AUTOFIX is False
    assert ctx.FORCE_FULL is False
    assert ctx.SKIP_HUMAN_GATE is False

    # Optional fields
    assert ctx.max_parallel_override is None
    assert ctx.RESUME is None

    # Dict fields
    assert ctx.FALLBACK_MODELS == {}

    # Computed fields (not empty — factory sets them)
    assert ctx.REAL_HOME == pwd.getpwuid(os.getuid()).pw_dir
    assert ctx.HERMES == os.path.join(pwd.getpwuid(os.getuid()).pw_dir, ".hermes")
    assert ctx.HERMES_BIN == os.path.join(
        pwd.getpwuid(os.getuid()).pw_dir, ".hermes", "hermes-agent/venv/bin/hermes"
    )
    assert ctx.PROFILES == os.path.join(
        pwd.getpwuid(os.getuid()).pw_dir, ".hermes", "profiles"
    )
    assert ctx.PANEL_PORT == {
        "strategist": 8647,
        "tech-lead": 8644,
        "coder": 8645,
        "nm": 8648,
    }


# ── Field override on init ─────────────────────────

def test_pipeline_context_field_override():
    """All fields can be overridden on init."""
    from utils import PipelineContext
    ctx = PipelineContext(
        PROJECT_DIR="/custom/project",
        REPO="owner/custom-repo",
        DEFAULT_BRANCH="develop",
        API_KEY="custom-key",
        OUTPUT_LOG="/custom/output.log",
        REAL_HOME="/custom/home",
        HERMES="/custom/home/.hermes",
        HERMES_BIN="/custom/bin/hermes",
        PROFILES="/custom/profiles",
        PANEL_PORT={"s": 8000},
        PANEL_FEATURE="Custom Feature",
        PANEL_DIR="/custom/.dokima",
        FALLBACK_MODELS={"coder": "gpt-4"},
        SKIP_AUTOFIX=True,
        FORCE_FULL=True,
        SKIP_HUMAN_GATE=True,
        max_parallel_override=3,
        RESUME="abc123",
        TEST_CMD="cargo test",
        BUILD_CMD="cargo build",
        LINT_CMD="cargo clippy",
    )

    assert ctx.PROJECT_DIR == "/custom/project"
    assert ctx.REPO == "owner/custom-repo"
    assert ctx.DEFAULT_BRANCH == "develop"
    assert ctx.API_KEY == "custom-key"
    assert ctx.OUTPUT_LOG == "/custom/output.log"
    assert ctx.REAL_HOME == "/custom/home"
    assert ctx.HERMES == "/custom/home/.hermes"
    assert ctx.HERMES_BIN == "/custom/bin/hermes"
    assert ctx.PROFILES == "/custom/profiles"
    assert ctx.PANEL_PORT == {"s": 8000}
    assert ctx.PANEL_FEATURE == "Custom Feature"
    assert ctx.PANEL_DIR == "/custom/.dokima"
    assert ctx.FALLBACK_MODELS == {"coder": "gpt-4"}
    assert ctx.SKIP_AUTOFIX is True
    assert ctx.FORCE_FULL is True
    assert ctx.SKIP_HUMAN_GATE is True
    assert ctx.max_parallel_override == 3
    assert ctx.RESUME == "abc123"
    assert ctx.TEST_CMD == "cargo test"
    assert ctx.BUILD_CMD == "cargo build"
    assert ctx.LINT_CMD == "cargo clippy"


# ── Partial override preserves defaults ─────────────

def test_pipeline_context_partial_override():
    """Overriding some fields preserves defaults for others."""
    from utils import PipelineContext
    ctx = PipelineContext(PROJECT_DIR="/only/project", DEFAULT_BRANCH="next")

    assert ctx.PROJECT_DIR == "/only/project"
    assert ctx.DEFAULT_BRANCH == "next"
    # Unchanged defaults
    assert ctx.REPO == ""
    assert ctx.API_KEY == ""
    assert ctx.SKIP_AUTOFIX is False
    assert ctx.FORCE_FULL is False


# ── Separate instances are independent ──────────────

def test_pipeline_context_independent_instances():
    """Two PipelineContext instances are independent."""
    from utils import PipelineContext
    ctx_a = PipelineContext(PROJECT_DIR="/proj/a")
    ctx_b = PipelineContext(PROJECT_DIR="/proj/b")

    assert ctx_a.PROJECT_DIR == "/proj/a"
    assert ctx_b.PROJECT_DIR == "/proj/b"
    # Mutating one doesn't affect the other
    ctx_a.PROJECT_DIR = "/proj/a-modified"
    assert ctx_a.PROJECT_DIR == "/proj/a-modified"
    assert ctx_b.PROJECT_DIR == "/proj/b"


# ── Field name count ────────────────────────────────

def test_pipeline_context_field_count():
    """PipelineContext has exactly 21 fields (matching all module globals)."""
    from utils import PipelineContext
    fields = list(PipelineContext.__dataclass_fields__.keys())
    assert len(fields) == 21, f"Expected 21 fields, got {len(fields)}: {fields}"
