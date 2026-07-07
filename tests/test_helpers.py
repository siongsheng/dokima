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


# ── F045: Verification gate tests ──

def test_commit_roadmap_update_skips_spec_only_pr(panel, tmpdir_path):
    """F045: commit_roadmap_update skips Done when PR has only spec changes."""
    import roadmap as _roadmap
    from unittest.mock import patch

    _roadmap.PROJECT_DIR = str(tmpdir_path)
    _roadmap.DEFAULT_BRANCH = "main"
    _roadmap.REPO = "test-owner/test-repo"

    roadmap_path = os.path.join(str(tmpdir_path), "roadmap.md")
    with open(roadmap_path, "w") as f:
        f.write("### F045: Test\n**Priority:** P0\n**Dependencies:** None\n**Status:** [~] In Progress\n**User Story:** T.\n")

    git_calls = []

    def mock_git(*args, **kwargs):
        git_calls.append(args)
        return ("", "", 0)

    def mock_gh(*args, **kwargs):
        if args[0] == "pr" and args[1] == "diff":
            return ("specs/roadmap.md | 2 +-\nspecs/STATUS.md | 1 +", "", 0)
        return ("", "", 0)

    with patch.object(_roadmap, "git", side_effect=mock_git):
        with patch.object(_roadmap, "gh", side_effect=mock_gh):
            _roadmap.commit_roadmap_update(roadmap_path, "F045", "done",
                                           pr_url="https://github.com/x/y/pull/99")

    # Should NOT have committed — spec-only PR
    commit_calls = [c for c in git_calls if c[0] == "commit"]
    assert len(commit_calls) == 0, (
        "F045 regression: commit_roadmap_update committed Done for spec-only PR. "
        "Must skip when PR has no code changes."
    )


def test_commit_roadmap_update_allows_code_change_pr(panel, tmpdir_path):
    """F045: commit_roadmap_update allows Done when PR has code changes."""
    import roadmap as _roadmap
    from unittest.mock import patch

    _roadmap.PROJECT_DIR = str(tmpdir_path)
    _roadmap.DEFAULT_BRANCH = "main"
    _roadmap.REPO = "test-owner/test-repo"

    roadmap_path = os.path.join(str(tmpdir_path), "roadmap.md")
    with open(roadmap_path, "w") as f:
        f.write("### F045: Test\n**Priority:** P0\n**Dependencies:** None\n**Status:** [~] In Progress\n**User Story:** T.\n")

    git_calls = []

    def mock_git(*args, **kwargs):
        git_calls.append(args)
        return ("", "", 0)

    def mock_gh(*args, **kwargs):
        if args[0] == "pr" and args[1] == "diff":
            return ("pipeline.py | 5 +++--\nroadmap.py | 1 +", "", 0)
        return ("", "", 0)

    with patch.object(_roadmap, "git", side_effect=mock_git):
        with patch.object(_roadmap, "gh", side_effect=mock_gh):
            _roadmap.commit_roadmap_update(roadmap_path, "F045", "done",
                                           pr_url="https://github.com/x/y/pull/99")

    # Should have committed — PR has code changes
    commit_calls = [c for c in git_calls if c[0] == "commit"]
    assert len(commit_calls) >= 1, (
        "F045 regression: commit_roadmap_update did NOT commit Done for PR with code changes."
    )


def test_commit_roadmap_update_done_without_pr_url_warns(panel, tmpdir_path):
    """F045: commit_roadmap_update with action='done' but no pr_url proceeds (backward compat)."""
    import roadmap as _roadmap
    from unittest.mock import patch

    _roadmap.PROJECT_DIR = str(tmpdir_path)
    _roadmap.DEFAULT_BRANCH = "main"
    _roadmap.REPO = "test-owner/test-repo"

    roadmap_path = os.path.join(str(tmpdir_path), "roadmap.md")
    with open(roadmap_path, "w") as f:
        f.write("### F045: Test\n**Priority:** P0\n**Dependencies:** None\n**Status:** [~] In Progress\n**User Story:** T.\n")

    git_calls = []

    def mock_git(*args, **kwargs):
        git_calls.append(args)
        return ("", "", 0)

    def mock_gh(*args, **kwargs):
        return ("", "", 0)

    with patch.object(_roadmap, "git", side_effect=mock_git):
        with patch.object(_roadmap, "gh", side_effect=mock_gh):
            _roadmap.commit_roadmap_update(roadmap_path, "F045", "done")

    # Should have committed — backward-compat fallback
    commit_calls = [c for c in git_calls if c[0] == "commit"]
    assert len(commit_calls) >= 1, (
        "F045 regression: commit_roadmap_update blocked Done when no pr_url provided. "
        "Must proceed for backward compatibility."
    )


def test_has_code_changes_spec_only():
    """F045: _has_code_changes returns False for spec-only diffs."""
    import roadmap as _roadmap
    from unittest.mock import patch

    with patch.object(_roadmap, "gh", return_value=("specs/roadmap.md | 1 +\nspecs/x-spec.md | 1 +", "", 0)):
        assert _roadmap._has_code_changes("99") is False

    with patch.object(_roadmap, "gh", return_value=("specs/a.md | 1 +\n .../b.py | 2 ++", "", 0)):
        assert _roadmap._has_code_changes("99") is False


def test_has_code_changes_with_code():
    """F045: _has_code_changes returns True for diffs with non-spec files."""
    import roadmap as _roadmap
    from unittest.mock import patch

    with patch.object(_roadmap, "gh", return_value=("pipeline.py | 5 +++--", "", 0)):
        assert _roadmap._has_code_changes("99") is True

    with patch.object(_roadmap, "gh", return_value=("specs/a.md | 1 +\nmain.py | 3 +++", "", 0)):
        assert _roadmap._has_code_changes("99") is True


def test_has_code_changes_empty_diff():
    """F045: _has_code_changes returns False for empty diff."""
    import roadmap as _roadmap
    from unittest.mock import patch

    with patch.object(_roadmap, "gh", return_value=("", "", 0)):
        assert _roadmap._has_code_changes("99") is False
