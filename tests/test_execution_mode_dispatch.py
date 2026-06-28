"""Tests for execution-mode-driven pipeline dispatch.

Verifies that run_pipeline dispatches to run_phase2_coder for single_session DAGs
and run_parallel_coders for per_task_spawn DAGs, with env override support.
"""
import os
import sys
import pytest
from unittest.mock import patch

from conftest import _load_panel as _load, _reload_panel

_spawn_calls = []


def _setup(tmpdir, panel):
    import subprocess
    project_dir = os.path.join(str(tmpdir), "proj")
    os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
    with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
        f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")
    roadmap = "# Roadmap\n## Phase 1\n"
    roadmap += "### F019: Execution Mode\n"
    roadmap += "**Priority:** P0\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** Test.\n"
    with open(os.path.join(project_dir, "specs", "roadmap.md"), "w") as f:
        f.write(roadmap)
    subprocess.run(["git", "init", project_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
    subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
    subprocess.run(["git", "-C", project_dir, "add", "-A"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                    "https://github.com/t/t.git"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    panel.PROJECT_DIR = project_dir
    panel.REPO = "t/t"
    panel.DEFAULT_BRANCH = "master"
    # Always patch time.sleep to avoid delays
    return project_dir


def _run_pipeline(panel, project_dir, spawn_mock, extra_patches=None):
    """Run main() with standard patches + optional extras."""
    old = sys.argv
    try:
        sys.argv = ["dokima", "--next", project_dir]
        panel.spawn_agent = spawn_mock

        mock_run = type("RunResult", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

        patches = [
            patch("dokima.call_agent", return_value={"content": "M", "tokens": 1}),
            patch("dokima._set_gh_token"),
            patch("dokima.git", return_value=("", "", 0)),
            patch("dokima.gh", return_value=("", "", 0)),
            patch("dokima.load_key", return_value="fk"),
            patch("dokima.load_github_token", return_value="ft"),
            patch("dokima.detect_repo", return_value="t/t"),
            patch("dokima._safe_run", return_value=mock_run),
            patch("dokima.subprocess.run", return_value=mock_run),
            patch("dokima.time.sleep"),
        ]
        if extra_patches:
            patches.extend(extra_patches)

        for p in patches:
            p.start()
        try:
            panel.main()
        except SystemExit:
            pass
        finally:
            for p in reversed(patches):
                p.stop()
    finally:
        sys.argv = old


# ── Strategist outputs ────────────────────────────────────────────

SINGLE_SESSION_STRAT = """# F019

**Confidence:** High
**Impact:** LOW

### Task 1: Add tests
**Files:** src/a.py
**Dependencies:** None
**Parallelizable:** Yes

### Task 2: Implement logic
**Files:** src/a.py
**Dependencies:** Task 1
**Parallelizable:** Yes
"""

PER_TASK_SPAWN_STRAT = """# F019

**Confidence:** High
**Impact:** MEDIUM

### Task 1: Refactor module
**Files:** src/a.py
**Dependencies:** None
**Parallelizable:** No

### Task 2: Update tests
**Files:** tests/test_a.py
**Dependencies:** Task 1
**Parallelizable:** Yes
"""

# More than 10 tasks (all parallel, same file) → per_task_spawn by task count
HIGH_TASK_COUNT_STRAT = "\n".join(
    [f"# F019\n\n**Confidence:** High\n**Impact:** LOW\n"]
    + [f"### Task {i}: Do thing {i}\n**Files:** src/a.py\n**Dependencies:** None\n**Parallelizable:** Yes\n"
       for i in range(1, 12)]
)

# 4 distinct files → per_task_spawn by file count
FOUR_FILE_STRAT = """# F019

**Confidence:** High
**Impact:** LOW

### Task 1: Add tests
**Files:** src/a.py
**Dependencies:** None
**Parallelizable:** Yes

### Task 2: Add module
**Files:** src/b.py
**Dependencies:** None
**Parallelizable:** Yes

### Task 3: Add handler
**Files:** src/c.py
**Dependencies:** None
**Parallelizable:** Yes

### Task 4: Add routes
**Files:** src/d.py
**Dependencies:** None
**Parallelizable:** Yes
"""


# ── Tests ─────────────────────────────────────────────────────────

class TestExecutionModeDispatch:

    def test_single_session_dag_runs_phase2_coder(self, tmpdir):
        """single_session DAG → run_phase2_coder called, not run_parallel_coders."""
        panel = _load()
        project_dir = _setup(tmpdir, panel)
        _spawn_calls.clear()
        called_parallel = []
        called_sequential = []

        def mock(profile, skills, prompt, timeout=600, cwd=None):
            _spawn_calls.append(profile)
            if profile == "strategist":
                return SINGLE_SESSION_STRAT
            return "Mock"

        with patch("dokima.run_parallel_coders", side_effect=lambda *a, **kw: called_parallel.append(1) or True) as mock_parallel:
            with patch("dokima.run_phase2_coder", side_effect=lambda *a, **kw: called_sequential.append(1) or {
                    "coder_failed": False, "pr_url": None, "verdict": "APPROVED", "coder_output": ""}) as mock_seq:
                _run_pipeline(panel, project_dir, mock)

        assert len(called_sequential) > 0, "run_phase2_coder should have been called for single_session DAG"
        assert len(called_parallel) == 0, "run_parallel_coders should NOT have been called for single_session DAG"

    def test_per_task_spawn_dag_runs_parallel_coders(self, tmpdir):
        """per_task_spawn DAG (non-parallelizable task) → run_parallel_coders called, not run_phase2_coder."""
        panel = _load()
        project_dir = _setup(tmpdir, panel)
        _spawn_calls.clear()
        called_parallel = []
        called_sequential = []

        def mock(profile, skills, prompt, timeout=600, cwd=None):
            _spawn_calls.append(profile)
            if profile == "strategist":
                return PER_TASK_SPAWN_STRAT
            if profile.startswith("coder-"):
                return "Task completed"
            return "Mock"

        import tempfile
        wt_dir = tempfile.mkdtemp()
        wt_mgr = type("W", (), {
            "create": lambda s, *a: wt_dir,
            "remove": lambda s, *a: None,
            "cleanup_all": lambda s, *a: None,
        })()
        mock_proc = type("P", (), {"poll": lambda s: 0, "communicate": lambda s, t=None: (b"done", None)})()

        with patch("dokima.run_phase2_coder", side_effect=lambda *a, **kw: called_sequential.append(1) or {
                "coder_failed": False, "pr_url": None, "verdict": "APPROVED", "coder_output": ""}) as mock_seq:
            with patch("dokima.run_parallel_coders", side_effect=lambda *a, **kw: called_parallel.append(1) or True) as mock_parallel:
                with patch("dokima.WorktreeManager", return_value=wt_mgr):
                    with patch("dokima.subprocess.Popen", return_value=mock_proc):
                        _run_pipeline(panel, project_dir, mock)

        assert len(called_parallel) > 0, "run_parallel_coders should have been called for per_task_spawn DAG"
        assert len(called_sequential) == 0, "run_phase2_coder should NOT have been called for per_task_spawn DAG"

    def test_force_single_session_env_override(self, tmpdir):
        """PANEL_FORCE_EXECUTION_MODE=single_session overrides per_task_spawn DAG → run_phase2_coder."""
        panel = _load()
        project_dir = _setup(tmpdir, panel)
        _spawn_calls.clear()
        called_parallel = []
        called_sequential = []

        def mock(profile, skills, prompt, timeout=600, cwd=None):
            _spawn_calls.append(profile)
            if profile == "strategist":
                return PER_TASK_SPAWN_STRAT
            return "Mock"

        os.environ["PANEL_FORCE_EXECUTION_MODE"] = "single_session"
        try:
            with patch("dokima.run_parallel_coders", side_effect=lambda *a, **kw: called_parallel.append(1) or True) as mock_parallel:
                with patch("dokima.run_phase2_coder", side_effect=lambda *a, **kw: called_sequential.append(1) or {
                        "coder_failed": False, "pr_url": None, "verdict": "APPROVED", "coder_output": ""}) as mock_seq:
                    _run_pipeline(panel, project_dir, mock)
        finally:
            os.environ.pop("PANEL_FORCE_EXECUTION_MODE", None)

        assert len(called_sequential) > 0, "run_phase2_coder should have been called when PANEL_FORCE_EXECUTION_MODE=single_session"
        assert len(called_parallel) == 0, "run_parallel_coders should NOT have been called"

    def test_force_per_task_spawn_env_override(self, tmpdir):
        """PANEL_FORCE_EXECUTION_MODE=per_task_spawn overrides single_session DAG → run_parallel_coders."""
        panel = _load()
        project_dir = _setup(tmpdir, panel)
        _spawn_calls.clear()
        called_parallel = []
        called_sequential = []

        def mock(profile, skills, prompt, timeout=600, cwd=None):
            _spawn_calls.append(profile)
            if profile == "strategist":
                return SINGLE_SESSION_STRAT
            if profile.startswith("coder-"):
                return "Task completed"
            return "Mock"

        import tempfile
        wt_dir = tempfile.mkdtemp()
        wt_mgr = type("W", (), {
            "create": lambda s, *a: wt_dir,
            "remove": lambda s, *a: None,
            "cleanup_all": lambda s, *a: None,
        })()
        mock_proc = type("P", (), {"poll": lambda s: 0, "communicate": lambda s, t=None: (b"done", None)})()

        os.environ["PANEL_FORCE_EXECUTION_MODE"] = "per_task_spawn"
        try:
            with patch("dokima.run_phase2_coder", side_effect=lambda *a, **kw: called_sequential.append(1) or {
                    "coder_failed": False, "pr_url": None, "verdict": "APPROVED", "coder_output": ""}) as mock_seq:
                with patch("dokima.run_parallel_coders", side_effect=lambda *a, **kw: called_parallel.append(1) or True) as mock_parallel:
                    with patch("dokima.WorktreeManager", return_value=wt_mgr):
                        with patch("dokima.subprocess.Popen", return_value=mock_proc):
                            _run_pipeline(panel, project_dir, mock)
        finally:
            os.environ.pop("PANEL_FORCE_EXECUTION_MODE", None)

        assert len(called_parallel) > 0, "run_parallel_coders should have been called when PANEL_FORCE_EXECUTION_MODE=per_task_spawn"
        assert len(called_sequential) == 0, "run_phase2_coder should NOT have been called"

    def test_high_task_count_dag_runs_parallel_coders(self, tmpdir):
        """11 tasks (per_task_spawn by count) → run_parallel_coders, not run_phase2_coder."""
        panel = _load()
        project_dir = _setup(tmpdir, panel)
        _spawn_calls.clear()
        called_parallel = []
        called_sequential = []

        def mock(profile, skills, prompt, timeout=600, cwd=None):
            _spawn_calls.append(profile)
            if profile == "strategist":
                return HIGH_TASK_COUNT_STRAT
            if profile.startswith("coder-"):
                return "Task completed"
            return "Mock"

        import tempfile
        wt_dir = tempfile.mkdtemp()
        wt_mgr = type("W", (), {
            "create": lambda s, *a: wt_dir,
            "remove": lambda s, *a: None,
            "cleanup_all": lambda s, *a: None,
        })()
        mock_proc = type("P", (), {"poll": lambda s: 0, "communicate": lambda s, t=None: (b"done", None)})()

        with patch("dokima.run_phase2_coder", side_effect=lambda *a, **kw: called_sequential.append(1) or {
                "coder_failed": False, "pr_url": None, "verdict": "APPROVED", "coder_output": ""}) as mock_seq:
            with patch("dokima.run_parallel_coders", side_effect=lambda *a, **kw: called_parallel.append(1) or True) as mock_parallel:
                with patch("dokima.WorktreeManager", return_value=wt_mgr):
                    with patch("dokima.subprocess.Popen", return_value=mock_proc):
                        _run_pipeline(panel, project_dir, mock)

        assert len(called_parallel) > 0, "run_parallel_coders should be called for 11-task DAG"
        assert len(called_sequential) == 0, "run_phase2_coder should NOT be called for 11-task DAG"

    def test_four_files_dag_runs_parallel_coders(self, tmpdir):
        """4 distinct files (per_task_spawn by file count) → run_parallel_coders."""
        panel = _load()
        project_dir = _setup(tmpdir, panel)
        _spawn_calls.clear()
        called_parallel = []
        called_sequential = []

        def mock(profile, skills, prompt, timeout=600, cwd=None):
            _spawn_calls.append(profile)
            if profile == "strategist":
                return FOUR_FILE_STRAT
            if profile.startswith("coder-"):
                return "Task completed"
            return "Mock"

        import tempfile
        wt_dir = tempfile.mkdtemp()
        wt_mgr = type("W", (), {
            "create": lambda s, *a: wt_dir,
            "remove": lambda s, *a: None,
            "cleanup_all": lambda s, *a: None,
        })()
        mock_proc = type("P", (), {"poll": lambda s: 0, "communicate": lambda s, t=None: (b"done", None)})()

        with patch("dokima.run_phase2_coder", side_effect=lambda *a, **kw: called_sequential.append(1) or {
                "coder_failed": False, "pr_url": None, "verdict": "APPROVED", "coder_output": ""}) as mock_seq:
            with patch("dokima.run_parallel_coders", side_effect=lambda *a, **kw: called_parallel.append(1) or True) as mock_parallel:
                with patch("dokima.WorktreeManager", return_value=wt_mgr):
                    with patch("dokima.subprocess.Popen", return_value=mock_proc):
                        _run_pipeline(panel, project_dir, mock)

        assert len(called_parallel) > 0, "run_parallel_coders should be called for 4-file DAG"
        assert len(called_sequential) == 0, "run_phase2_coder should NOT be called for 4-file DAG"
