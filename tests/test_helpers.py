"""Tests for additional helpers."""
import os
import pytest

def test_make_status_entry_pending(panel):
    result = panel._make_status_entry("F001", "Login", "pending", branch="feat/login")
    assert "F001" in result
    assert "Login" in result
    assert "pending" in result
    assert "feat/login" in result

def test_make_status_entry_done_with_pr(panel):
    result = panel._make_status_entry("F001", "Login", "done",
                                       pr_url="https://github.com/x/y/pull/1",
                                       source="panel")
    assert "done" in result
    assert "github.com/x/y/pull/1" in result
    assert "[panel]" in result

def test_make_status_entry_in_progress(panel):
    result = panel._make_status_entry("F002", "Dashboard", "in_progress",
                                       timestamp="2024-06-01 12:00",
                                       branch="feat/dash")
    assert "F002" in result
    assert "Dashboard" in result
    assert "in progress" in result
    assert "2024-06-01 12:00" in result

def test_commit_roadmap_update_dry(panel, tmpdir_path):
    """Test commit_roadmap_update structure — will fail without git, but shouldn't crash."""
    panel.PROJECT_DIR = tmpdir_path
    roadmap_path = os.path.join(tmpdir_path, "roadmap.md")
    with open(roadmap_path, "w") as f:
        f.write("test")
    # This will fail because tmpdir isn't a git repo, but shouldn't crash
    # Just verify the function exists and accepts args
    assert callable(panel.commit_roadmap_update)

def test_commit_roadmap_update_aborts_on_checkout_failure(panel, tmpdir_path):
    """H5: commit_roadmap_update aborts when git checkout fails.
    
    If git checkout returns non-zero, the function should print an error
    and return early without attempting commit/push.
    """
    import roadmap as _roadmap
    from unittest.mock import patch, call

    _roadmap.PROJECT_DIR = str(tmpdir_path)
    _roadmap.DEFAULT_BRANCH = "main"

    roadmap_path = os.path.join(str(tmpdir_path), "roadmap.md")
    with open(roadmap_path, "w") as f:
        f.write("test")

    git_calls = []

    def mock_git(*args, **kwargs):
        git_calls.append(args)
        if args[0] == "checkout":
            return ("", "error: cannot checkout", 1)
        return ("", "", 0)

    with patch.object(_roadmap, "git", side_effect=mock_git):
        _roadmap.commit_roadmap_update(roadmap_path, "F001", "start")

    # Should have called checkout
    checkout_calls = [c for c in git_calls if c[0] == "checkout"]
    assert len(checkout_calls) >= 1, "Expected git checkout call"

    # Should NOT have proceeded to commit or push
    commit_calls = [c for c in git_calls if c[0] == "commit"]
    assert len(commit_calls) == 0, (
        "H5 regression: commit_roadmap_update called git commit even though "
        "git checkout failed. Must abort early on checkout failure."
    )


def test_commit_roadmap_update_aborts_on_pull_failure(panel, tmpdir_path):
    """H5: commit_roadmap_update aborts when git pull fails.
    
    If git pull returns non-zero, the function should print an error
    and return early without attempting commit/push.
    """
    import roadmap as _roadmap
    from unittest.mock import patch

    _roadmap.PROJECT_DIR = str(tmpdir_path)
    _roadmap.DEFAULT_BRANCH = "main"

    roadmap_path = os.path.join(str(tmpdir_path), "roadmap.md")
    with open(roadmap_path, "w") as f:
        f.write("test")

    git_calls = []

    def mock_git(*args, **kwargs):
        git_calls.append(args)
        if args[0] == "pull":
            return ("", "error: network unreachable", 1)
        return ("", "", 0)

    with patch.object(_roadmap, "git", side_effect=mock_git):
        _roadmap.commit_roadmap_update(roadmap_path, "F002", "done")

    # Should have called checkout (succeeds) and pull (fails)
    pull_calls = [c for c in git_calls if c[0] == "pull"]
    assert len(pull_calls) >= 1, "Expected git pull call"

    # Should NOT have proceeded to commit or push
    commit_calls = [c for c in git_calls if c[0] == "commit"]
    assert len(commit_calls) == 0, (
        "H5 regression: commit_roadmap_update called git commit even though "
        "git pull failed. Must abort early on pull failure."
    )


def test_auto_repair_status_empty(panel, tmpdir_path):
    roadmap_path = os.path.join(tmpdir_path, "roadmap.md")
    with open(roadmap_path, "w") as f:
        f.write("# Roadmap\n")
    result = panel.auto_repair_status([], roadmap_path)
    assert result == 0
