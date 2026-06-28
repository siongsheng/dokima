"""Tests for TaskDAG — compute_execution_mode() and related logic."""
import pytest
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ── Helper: build a TaskDAG from task specs ──────────────────────

def _make_dag(panel, task_specs):
    """Create a TaskDAG with the given task specs.
    
    Each spec: (tid, parallelizable, files) or (tid, parallelizable, files, deps)
    """
    dag = panel.TaskDAG()
    for spec in task_specs:
        tid = spec[0]
        parallelizable = spec[1]
        files = spec[2]
        deps = spec[3] if len(spec) > 3 else []
        dag.tasks[tid] = panel.Task(
            tid=tid,
            description=f"Task {tid}",
            files=files,
            dependencies=deps,
            parallelizable=parallelizable,
        )
    return dag


# ── compute_execution_mode tests ─────────────────────────────────

def test_all_parallel_3tasks_2files_single_session(panel):
    """3 parallelizable tasks, 2 distinct files → single_session."""
    dag = _make_dag(panel, [
        ("1", True, ["src/a.py"]),
        ("2", True, ["src/b.py"]),
        ("3", True, ["src/a.py"]),  # duplicate file — still 2 distinct
    ])
    assert dag.compute_execution_mode() == "single_session"


def test_non_parallelizable_task_returns_per_task_spawn(panel):
    """Any non-parallelizable task → per_task_spawn."""
    dag = _make_dag(panel, [
        ("1", True, ["src/a.py"]),
        ("2", False, ["src/b.py"]),  # non-parallelizable
        ("3", True, ["src/c.py"]),
    ])
    assert dag.compute_execution_mode() == "per_task_spawn"


def test_11_tasks_returns_per_task_spawn(panel):
    """More than 10 tasks → per_task_spawn (hard cap)."""
    specs = [(str(i), True, ["src/a.py"]) for i in range(1, 12)]
    dag = _make_dag(panel, specs)
    assert dag.compute_execution_mode() == "per_task_spawn"


def test_4_distinct_files_returns_per_task_spawn(panel):
    """More than 3 distinct files → per_task_spawn."""
    dag = _make_dag(panel, [
        ("1", True, ["src/a.py"]),
        ("2", True, ["src/b.py"]),
        ("3", True, ["src/c.py"]),
        ("4", True, ["src/d.py"]),  # 4th distinct file
    ])
    assert dag.compute_execution_mode() == "per_task_spawn"


def test_1_task_returns_single_session(panel):
    """Single task, regardless of file count → single_session."""
    dag = _make_dag(panel, [
        ("1", True, ["src/a.py"]),
    ])
    assert dag.compute_execution_mode() == "single_session"


def test_boundary_10tasks_3files_all_parallel_single_session(panel):
    """Exactly 10 tasks, exactly 3 files, all parallel → single_session (max)."""
    specs = [
        ("1", True, ["src/a.py"]),
        ("2", True, ["src/b.py"]),
        ("3", True, ["src/a.py"]),
        ("4", True, ["src/b.py"]),
        ("5", True, ["src/c.py"]),
        ("6", True, ["src/a.py"]),
        ("7", True, ["src/b.py"]),
        ("8", True, ["src/c.py"]),
        ("9", True, ["src/a.py"]),
        ("10", True, ["src/b.py"]),
    ]
    dag = _make_dag(panel, specs)
    assert dag.compute_execution_mode() == "single_session"


def test_empty_dag_returns_single_session(panel):
    """No tasks → single_session (nothing to parallel-spawn)."""
    dag = _make_dag(panel, [])
    assert dag.compute_execution_mode() == "single_session"


def test_mixed_5_parallel_1_not_returns_per_task_spawn(panel):
    """5 parallel + 1 non-parallel → per_task_spawn."""
    dag = _make_dag(panel, [
        ("1", True, ["src/a.py"]),
        ("2", True, ["src/b.py"]),
        ("3", True, ["src/c.py"]),
        ("4", True, ["src/a.py"]),
        ("5", True, ["src/b.py"]),
        ("6", False, ["src/d.py"]),  # non-parallel
    ])
    assert dag.compute_execution_mode() == "per_task_spawn"


def test_all_empty_files_returns_single_session(panel):
    """All tasks have empty files list → single_session (len=0 ≤ 3)."""
    dag = _make_dag(panel, [
        ("1", True, []),
        ("2", True, []),
        ("3", True, []),
    ])
    assert dag.compute_execution_mode() == "single_session"


def test_duplicate_file_normalization_still_3(panel):
    """Files with different casing/whitespace normalize to ≤3 distinct → single_session."""
    dag = _make_dag(panel, [
        ("1", True, ["SRC/A.PY"]),          # UPPER
        ("2", True, [" src/a.py "]),         # leading/trailing whitespace
        ("3", True, ["src/b.py"]),
        ("4", True, ["src/a.py"]),           # normal case
        ("5", True, ["src/b.py"]),
        ("6", True, ["src/c.py"]),
    ])
    # After .strip().lower(): 'src/a.py', 'src/b.py', 'src/c.py' = 3 distinct
    assert dag.compute_execution_mode() == "single_session"
