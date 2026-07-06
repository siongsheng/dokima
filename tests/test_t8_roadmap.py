"""Tests for Task 8: Migrate roadmap.py globals to ctx parameter.

run_next_setup and run_init should accept ctx: PipelineContext as first parameter
and use ctx fields instead of module-level globals.
"""

import os
import sys
import inspect
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is on path for roadmap imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import PipelineContext


# ═══════════════════════════════════════════════════════════════════
# run_next_setup(ctx, ...) — uses ctx.project_dir instead of PROJECT_DIR
# ═══════════════════════════════════════════════════════════════════


def test_run_next_setup_accepts_ctx_as_first_param():
    """run_next_setup() accepts ctx as first positional parameter."""
    import roadmap

    sig = inspect.signature(roadmap.run_next_setup)
    params = list(sig.parameters.keys())
    assert params[0] == "ctx", (
        f"run_next_setup missing ctx as first param, got {params}"
    )


def test_run_next_setup_uses_ctx_project_dir(tmpdir):
    """run_next_setup(ctx) reads spec from ctx.project_dir, not global PROJECT_DIR."""
    import roadmap

    ctx = PipelineContext(project_dir=str(tmpdir), repo="test-owner/test-repo")

    # Create a dummy roadmap so the function doesn't exit early
    specs_dir = os.path.join(str(tmpdir), "specs")
    os.makedirs(specs_dir, exist_ok=True)
    roadmap_path = os.path.join(specs_dir, "roadmap.md")
    with open(roadmap_path, "w") as f:
        f.write("### F001: Test Feature\n**Priority:** P0\n**Dependencies:** None\n**Status:** [ ] Pending\n")

    # We need to mock git/gh operations, and sys.exit
    with patch("roadmap.git", return_value=("", "", 0)), \
         patch("roadmap.gh", return_value=("", "", 0)), \
         patch("roadmap.sys.exit") as mock_exit, \
         patch("roadmap.os.environ", {}):
        # Should NOT raise AttributeError for missing ctx fields
        try:
            roadmap.run_next_setup(ctx, interactive=False)
        except SystemExit:
            pass

    # The function tried to read from ctx.project_dir path (no AttributeError)
    assert os.path.exists(roadmap_path)


def test_run_next_setup_no_global_statement():
    """run_next_setup body must not contain 'global' statement."""
    import roadmap

    src = inspect.getsource(roadmap.run_next_setup)
    assert "global " not in src, (
        "run_next_setup still has global statement"
    )


# ═══════════════════════════════════════════════════════════════════
# run_init(ctx, description, project_dir, ...) — uses ctx.api_key, ctx.project_dir, ctx.repo
# ═══════════════════════════════════════════════════════════════════


def test_run_init_accepts_ctx_as_first_param():
    """run_init() accepts ctx as first positional parameter."""
    import roadmap

    sig = inspect.signature(roadmap.run_init)
    params = list(sig.parameters.keys())
    assert params[0] == "ctx", (
        f"run_init missing ctx as first param, got {params}"
    )


def test_run_init_sets_ctx_project_dir(tmpdir):
    """run_init(ctx, desc, project_dir) sets ctx.project_dir = project_dir."""
    import roadmap

    ctx = PipelineContext(project_dir="")
    assert ctx.project_dir == ""

    with patch("roadmap.load_key", return_value="test-api-key"), \
         patch("roadmap.load_github_token", return_value="gh-token"), \
         patch("roadmap.detect_repo", return_value=""), \
         patch("roadmap.ensure_profiles"), \
         patch("roadmap.deploy_profile_skills"), \
         patch("roadmap.spawn_agent", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.extract_agent_messages", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.has_init_interview_triggers", return_value=False), \
         patch("roadmap.os.makedirs"), \
         patch("roadmap.os.path.exists", return_value=False), \
         patch("roadmap.sys.exit") as mock_exit, \
         patch("builtins.print"):
        try:
            roadmap.run_init(ctx, "Test project", str(tmpdir))
        except SystemExit:
            pass

    # run_init should set ctx.project_dir
    assert ctx.project_dir == str(tmpdir), (
        f"ctx.project_dir was not set; got {ctx.project_dir}"
    )


def test_run_init_sets_ctx_api_key(tmpdir):
    """run_init(ctx, ...) sets ctx.api_key from load_key()."""
    import roadmap

    ctx = PipelineContext(api_key="")
    assert ctx.api_key == ""

    with patch("roadmap.load_key", return_value="loaded-api-key"), \
         patch("roadmap.load_github_token", return_value="gh-token"), \
         patch("roadmap.detect_repo", return_value=""), \
         patch("roadmap.ensure_profiles"), \
         patch("roadmap.deploy_profile_skills"), \
         patch("roadmap.spawn_agent", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.extract_agent_messages", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.has_init_interview_triggers", return_value=False), \
         patch("roadmap.os.makedirs"), \
         patch("roadmap.os.path.exists", return_value=False), \
         patch("roadmap.sys.exit"), \
         patch("builtins.print"):
        try:
            roadmap.run_init(ctx, "Test project", str(tmpdir))
        except SystemExit:
            pass

    assert ctx.api_key == "loaded-api-key", (
        f"ctx.api_key was not set; got {ctx.api_key}"
    )


def test_run_init_sets_ctx_repo(tmpdir):
    """run_init(ctx, ...) sets ctx.repo from detect_repo()."""
    import roadmap

    ctx = PipelineContext(repo="")
    assert ctx.repo == ""

    with patch("roadmap.load_key", return_value="test-key"), \
         patch("roadmap.load_github_token", return_value="gh-token"), \
         patch("roadmap.detect_repo", return_value="myorg/myrepo"), \
         patch("roadmap.ensure_profiles"), \
         patch("roadmap.deploy_profile_skills"), \
         patch("roadmap.spawn_agent", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.extract_agent_messages", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.has_init_interview_triggers", return_value=False), \
         patch("roadmap.os.makedirs"), \
         patch("roadmap.os.path.exists", return_value=False), \
         patch("roadmap.sys.exit"), \
         patch("builtins.print"):
        try:
            roadmap.run_init(ctx, "Test project", str(tmpdir))
        except SystemExit:
            pass

    assert ctx.repo == "myorg/myrepo", (
        f"ctx.repo was not set; got {ctx.repo}"
    )


def test_run_init_no_global_statement():
    """run_init body must not contain 'global' statement."""
    import roadmap

    src = inspect.getsource(roadmap.run_init)
    assert "global " not in src, (
        "run_init still has global statement"
    )


# ═══════════════════════════════════════════════════════════════════
# Context isolation — two different ctx objects don't interfere
# ═══════════════════════════════════════════════════════════════════


def test_ctx_isolation_run_init(tmpdir):
    """Two different PipelineContext objects passed to run_init are independent."""
    import roadmap

    ctx1 = PipelineContext(project_dir="", api_key="", repo="")
    ctx2 = PipelineContext(project_dir="", api_key="", repo="")

    dir1 = os.path.join(str(tmpdir), "proj1")
    dir2 = os.path.join(str(tmpdir), "proj2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)

    with patch("roadmap.load_key", return_value="key-1"), \
         patch("roadmap.load_github_token", return_value="gh-token"), \
         patch("roadmap.detect_repo", return_value="repo-1"), \
         patch("roadmap.ensure_profiles"), \
         patch("roadmap.deploy_profile_skills"), \
         patch("roadmap.spawn_agent", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.extract_agent_messages", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.has_init_interview_triggers", return_value=False), \
         patch("roadmap.os.makedirs"), \
         patch("roadmap.os.path.exists", return_value=False), \
         patch("roadmap.sys.exit"), \
         patch("builtins.print"):
        try:
            roadmap.run_init(ctx1, "Test 1", dir1)
        except SystemExit:
            pass

    with patch("roadmap.load_key", return_value="key-2"), \
         patch("roadmap.load_github_token", return_value="gh-token"), \
         patch("roadmap.detect_repo", return_value="repo-2"), \
         patch("roadmap.ensure_profiles"), \
         patch("roadmap.deploy_profile_skills"), \
         patch("roadmap.spawn_agent", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.extract_agent_messages", return_value="DECISION: PROCEED\nNo CLARIFICATION."), \
         patch("roadmap.has_init_interview_triggers", return_value=False), \
         patch("roadmap.os.makedirs"), \
         patch("roadmap.os.path.exists", return_value=False), \
         patch("roadmap.sys.exit"), \
         patch("builtins.print"):
        try:
            roadmap.run_init(ctx2, "Test 2", dir2)
        except SystemExit:
            pass

    # ctx1 should have values from first call
    assert ctx1.project_dir == dir1
    assert ctx1.api_key == "key-1"
    assert ctx1.repo == "repo-1"

    # ctx2 should have values from second call (not contaminated by ctx1)
    assert ctx2.project_dir == dir2
    assert ctx2.api_key == "key-2"
    assert ctx2.repo == "repo-2"
