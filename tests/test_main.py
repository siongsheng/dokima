"""Tests for main() and Orchestrator class."""
import io
import os
import pytest


def test_repo_fixture_creates_valid_git_repo(test_repo):
    """test_repo fixture creates a valid git repo with AGENTS.md."""
    agents_path = os.path.join(test_repo, "AGENTS.md")
    assert os.path.exists(agents_path), "AGENTS.md should exist"
    with open(agents_path) as f:
        content = f.read()
    assert "test" in content.lower() or "pytest" in content.lower()
    # Verify it's a git repo
    from subprocess import run, PIPE
    r = run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, cwd=test_repo)
    assert r.returncode == 0, f"Not a git repo: {r.stderr}"
    # Should have initial commit
    r2 = run(["git", "log", "--oneline", "-1"], capture_output=True, text=True, cwd=test_repo)
    assert r2.returncode == 0 and r2.stdout.strip(), "Repo should have at least one commit"



def test_orchestrator_constructable(panel):
    """Orchestrator can be constructed with default dependencies."""
    orch = panel.Orchestrator(
        project_dir="/tmp/test",
        feature="Test feature",
        stdin=io.StringIO(),
        lock_fn=lambda: (True, -1),
        safe_run_fn=lambda cmd, cwd, timeout: None,
        gh_cli_fn=lambda *a, **kw: "",
    )
    assert orch is not None
    assert orch.project_dir == "/tmp/test"
    assert orch.feature == "Test feature"


def test_orchestrator_run_calls_lock_cleanup(panel):
    """Orchestrator.run() calls cleanup_lock at end."""
    cleanup_called = []
    orch = panel.Orchestrator(
        project_dir="/tmp/test",
        feature="Test feature",
        stdin=io.StringIO(),
        lock_fn=lambda: (True, -1),
        safe_run_fn=lambda cmd, cwd, timeout: None,
        gh_cli_fn=lambda *a, **kw: "",
        cleanup_lock_fn=lambda: cleanup_called.append(True),
    )
    try:
        orch.run()
    except SystemExit:
        pass
    assert cleanup_called, "cleanup_lock should be called by run()"


def test_orchestrator_with_flags(panel):
    """Orchestrator accepts and stores flag values."""
    orch = panel.Orchestrator(
        project_dir="/tmp/test",
        feature="Test feature",
        stdin=io.StringIO(),
        lock_fn=lambda: (True, -1),
        safe_run_fn=lambda cmd, cwd, timeout: None,
        gh_cli_fn=lambda *a, **kw: "",
        is_next=True,
        is_continuous=False,
        is_fix=False,
        skip_auto_archive=True,
    )
    assert orch.is_next is True
    assert orch.is_continuous is False
    assert orch.is_fix is False
    assert orch.skip_auto_archive is True
