"""Task 6: Migrate tasks.py globals to ctx parameter.

Tests verify that tasks.py functions accept PipelineContext as their first
parameter and use ctx attributes instead of module-level global imports.
"""
import os
import sys
import inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest
from context import PipelineContext


# ── WorktreeManager ctx migration tests ──────────────────────────

def test_worktree_manager_accepts_ctx():
    """WorktreeManager.__init__ accepts PipelineContext, derives project_root."""
    import tasks
    ctx = PipelineContext(project_dir="/tmp/test-project")
    wm = tasks.WorktreeManager(ctx)
    assert wm.project_root == "/tmp/test-project"
    expected_wt_dir = os.path.join("/tmp/test-project", ".dokima", "worktrees")
    assert wm.worktrees_dir == expected_wt_dir


def test_worktree_manager_default_project_dir():
    """WorktreeManager with empty ctx.project_dir defaults to cwd."""
    import tasks
    ctx = PipelineContext()
    wm = tasks.WorktreeManager(ctx)
    assert wm.project_root == os.path.abspath("")


# ── TaskDAG ctx migration tests ──────────────────────────────────

def test_task_dag_accepts_ctx():
    """TaskDAG.__init__ accepts PipelineContext."""
    import tasks
    ctx = PipelineContext()
    dag = tasks.TaskDAG(ctx)
    assert dag.tasks == {}
    assert hasattr(dag, 'ctx')


# ── spawn_coder_in_worktree ctx parameter test ───────────────────

def test_spawn_coder_in_worktree_accepts_ctx_as_first_param():
    """spawn_coder_in_worktree accepts ctx as first positional parameter."""
    import tasks
    ctx = PipelineContext(
        test_cmd="npm test",
        build_cmd="npm run build",
        lint_cmd="npm run lint",
        default_branch="main",
        hermes_bin="/fake/hermes",
        panel_feature="F001-test",
        output_log="/dev/null",
        fallback_models={},
    )
    task = tasks.Task(tid="1", description="test task", files=["a.py"],
                      dependencies=[], parallelizable=True)
    task.branch = "feat/f001-test-t1"
    # Verify the signature accepts ctx (first positional)
    sig = inspect.signature(tasks.spawn_coder_in_worktree)
    params = list(sig.parameters.keys())
    assert params[0] == 'ctx', f"First param should be 'ctx', got {params}"
    # Verify that ctx attribute values are accessible (no AttributeError)
    assert ctx.test_cmd == "npm test"
    assert ctx.build_cmd == "npm run build"
    assert ctx.default_branch == "main"
    assert ctx.hermes_bin == "/fake/hermes"
    assert ctx.panel_feature == "F001-test"
    assert ctx.output_log == "/dev/null"


# ── merge_worktree_branches ctx parameter test ───────────────────

def test_merge_worktree_branches_accepts_ctx():
    """merge_worktree_branches accepts ctx instead of project_dir."""
    import tasks
    sig = inspect.signature(tasks.merge_worktree_branches)
    params = list(sig.parameters.keys())
    assert params[0] == 'ctx', f"First param should be 'ctx', got {params}"


# ── run_parallel_coders ctx parameter test ───────────────────────

def test_run_parallel_coders_accepts_ctx():
    """run_parallel_coders accepts ctx instead of project_dir."""
    import tasks
    sig = inspect.signature(tasks.run_parallel_coders)
    params = list(sig.parameters.keys())
    assert params[0] == 'ctx', f"First param should be 'ctx', got {params}"


# ── No module-level PROJECT_DIR global ───────────────────────────

def test_no_project_dir_global():
    """tasks.py must NOT have a module-level PROJECT_DIR global."""
    import tasks
    assert not hasattr(tasks, 'PROJECT_DIR'), \
        "tasks.py must not have PROJECT_DIR global — use ctx.project_dir"


# ── No global imports from utils at module level ─────────────────

def test_no_global_imports_from_utils():
    """tasks.py must not import these globals from utils at module level."""
    import tasks
    banned = [
        'HERMES_BIN', 'DEFAULT_BRANCH', 'PANEL_FEATURE',
        'TEST_CMD', 'BUILD_CMD', 'LINT_CMD',
        'FALLBACK_MODELS', 'max_parallel_override', 'OUTPUT_LOG',
    ]
    for name in banned:
        assert not hasattr(tasks, name), \
            f"tasks.py must not have {name} as a module-level attribute"
