"""Tests for TaskDAG — execution mode computation, wave computation, and parsing."""

import pytest
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ── compute_execution_mode ────────────────────────────────────────

def test_all_parallel_3tasks_2files_single_session(panel):
    """3 tasks, all parallelizable, 2 distinct files → single_session."""
    dag = panel.TaskDAG()
    dag.tasks["1"] = panel.Task("1", "Task A", ["src/a.py"], [], True)
    dag.tasks["2"] = panel.Task("2", "Task B", ["src/b.py"], ["1"], True)
    dag.tasks["3"] = panel.Task("3", "Task C", ["src/a.py"], ["2"], True)
    assert dag.compute_execution_mode() == "single_session"


def test_any_non_parallelizable_per_task_spawn(panel):
    """A single non-parallelizable task → per_task_spawn."""
    dag = panel.TaskDAG()
    dag.tasks["1"] = panel.Task("1", "Task A", ["src/a.py"], [], True)
    dag.tasks["2"] = panel.Task("2", "Task B", ["src/b.py"], ["1"], False)
    assert dag.compute_execution_mode() == "per_task_spawn"


def test_11_tasks_per_task_spawn(panel):
    """More than 10 tasks → per_task_spawn (hard cap)."""
    dag = panel.TaskDAG()
    for i in range(1, 12):
        dag.tasks[str(i)] = panel.Task(str(i), f"Task {i}", [f"src/{i}.py"], [], True)
    assert dag.compute_execution_mode() == "per_task_spawn"


def test_4_distinct_files_per_task_spawn(panel):
    """4 distinct files → per_task_spawn."""
    dag = panel.TaskDAG()
    dag.tasks["1"] = panel.Task("1", "Task A", ["src/a.py"], [], True)
    dag.tasks["2"] = panel.Task("2", "Task B", ["src/b.py"], [], True)
    dag.tasks["3"] = panel.Task("3", "Task C", ["src/c.py"], [], True)
    dag.tasks["4"] = panel.Task("4", "Task D", ["src/d.py"], [], True)
    assert dag.compute_execution_mode() == "per_task_spawn"


def test_1_task_single_session(panel):
    """Single task, parallelizable → single_session."""
    dag = panel.TaskDAG()
    dag.tasks["1"] = panel.Task("1", "Task A", ["src/a.py"], [], True)
    assert dag.compute_execution_mode() == "single_session"


def test_10_tasks_3files_all_parallel_single_session(panel):
    """10 tasks, 3 files, all parallelizable → single_session (boundary)."""
    dag = panel.TaskDAG()
    for i in range(1, 11):
        file_idx = (i % 3) + 1
        dag.tasks[str(i)] = panel.Task(
            str(i), f"Task {i}", [f"src/{file_idx}.py"], [], True
        )
    assert dag.compute_execution_mode() == "single_session"


def test_empty_dag_single_session(panel):
    """Empty DAG with no tasks → single_session."""
    dag = panel.TaskDAG()
    assert dag.compute_execution_mode() == "single_session"


def test_mixed_parallel_non_parallel_per_task_spawn(panel):
    """5 parallel + 1 non-parallel → per_task_spawn (non-parallel wins)."""
    dag = panel.TaskDAG()
    for i in range(1, 6):
        dag.tasks[str(i)] = panel.Task(str(i), f"Task {i}", [f"src/{i}.py"], [], True)
    dag.tasks["6"] = panel.Task("6", "Task F", ["src/f.py"], [], False)
    assert dag.compute_execution_mode() == "per_task_spawn"


def test_all_tasks_empty_files_single_session(panel):
    """All tasks with empty files lists → single_session (0 ≤ 3 files)."""
    dag = panel.TaskDAG()
    dag.tasks["1"] = panel.Task("1", "Task A", [], [], True)
    dag.tasks["2"] = panel.Task("2", "Task B", [], ["1"], True)
    assert dag.compute_execution_mode() == "single_session"


def test_duplicate_files_normalized_single_session(panel):
    """Duplicate files with different casing/whitespace → normalized to ≤3 distinct."""
    dag = panel.TaskDAG()
    dag.tasks["1"] = panel.Task("1", "Task A", ["src/A.py"], [], True)
    dag.tasks["2"] = panel.Task("2", "Task B", [" src/a.py "], [], True)
    dag.tasks["3"] = panel.Task("3", "Task C", ["SRC/A.PY"], [], True)
    assert dag.compute_execution_mode() == "single_session"
