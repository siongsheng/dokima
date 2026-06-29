"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases.

Tests cover:
  (a) _bump_version correct for patch/minor/major
  (b) _bump_version rejects invalid bump
  (c) do_release with --dry-run prints expected plan
  (d) do_release fails on non-git dir
  (e) do_release fails on dirty tree
  (f) do_release fails on non-default branch
  (g) do_release fails on invalid bump type
  (h) _prune_old_tags keeps 10 newest
  (i) --release in HELP_TEXT output
  (j) --release in --help-json output
"""
import json
import os
import subprocess
import sys
import types
from unittest.mock import patch

import pytest

PANEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dokima"))


# ── helpers ───────────────────────────────────────────────────────────────

def _make_git_repo(path):
    """Create a git repo at path. Return the path."""
    os.makedirs(path, exist_ok=True)
    subprocess.run(["git", "init", path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", path, "config", "user.email", "test@test.com"])
    subprocess.run(["git", "-C", path, "config", "user.name", "Test"])
    # Create a VERSION file
    with open(os.path.join(path, "VERSION"), "w") as f:
        f.write("1.2.1\n")
    # Initial commit (clean tree)
    subprocess.run(["git", "-C", path, "add", "-A"])
    subprocess.run(["git", "-C", path, "commit", "-m", "init"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return path


class TestBumpVersion:
    """(a) _bump_version correct for patch/minor/major
       (b) _bump_version rejects invalid bump"""

    def test_bump_patch(self, panel):
        from utils import _bump_version
        assert _bump_version("1.2.1", "patch") == "1.2.2"

    def test_bump_minor(self, panel):
        from utils import _bump_version
        assert _bump_version("1.2.1", "minor") == "1.3.0"

    def test_bump_major(self, panel):
        from utils import _bump_version
        assert _bump_version("1.2.1", "major") == "2.0.0"

    def test_bump_strips_v_prefix(self, panel):
        from utils import _bump_version
        assert _bump_version("v1.2.1", "patch") == "1.2.2"

    def test_bump_strips_whitespace(self, panel):
        from utils import _bump_version
        assert _bump_version("  1.2.1  ", "patch") == "1.2.2"

    def test_bump_patch_at_edge(self, panel):
        from utils import _bump_version
        assert _bump_version("9.9.9", "patch") == "9.9.10"

    def test_bump_from_zero(self, panel):
        from utils import _bump_version
        assert _bump_version("0.0.1", "minor") == "0.1.0"

    def test_rejects_invalid_bump_type(self, panel):
        from utils import _bump_version
        with pytest.raises(ValueError, match="Invalid bump type"):
            _bump_version("1.2.1", "prepatch")

    def test_rejects_invalid_bump_prerelease(self, panel):
        from utils import _bump_version
        with pytest.raises(ValueError, match="Invalid bump type"):
            _bump_version("1.2.1", "prerelease")

    def test_rejects_non_semver_version(self, panel):
        from utils import _bump_version
        with pytest.raises(ValueError, match="Invalid version string"):
            _bump_version("not-a-version", "patch")

    def test_rejects_two_part_version(self, panel):
        from utils import _bump_version
        with pytest.raises(ValueError, match="Invalid version string"):
            _bump_version("1.2", "patch")


class TestPruneOldTags:
    """(h) _prune_old_tags keeps 10 newest"""

    def test_prune_keeps_10_when_more_exist(self, panel):
        """When >10 release tags exist, prune the older ones."""
        from utils import _prune_old_tags
        tags = [f"v1.{i}.0" for i in range(20, 0, -1)]  # 20 tags, newest first
        mock_output = "\n".join(tags)

        with patch("subprocess.run") as mock_run:
            # First call: git tag --sort=-v:refname
            tag_call = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=mock_output, stderr="")
            # Subsequent calls: git push origin --delete
            push_call = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr="")

            mock_run.side_effect = [tag_call] + [push_call] * 20

            _prune_old_tags(keep_count=10)

            # Should have called git tag once, then git push --delete for 10 old tags
            assert mock_run.call_count >= 11  # 1 tag list + 10 deletes
            # Verify first call was git tag
            first_call_args = mock_run.call_args_list[0][0][0]
            assert first_call_args[0] == "git"
            assert first_call_args[1] == "tag"
            # Verify delete calls
            for i in range(1, 11):
                call_args = mock_run.call_args_list[i][0][0]
                assert call_args[0] == "git"
                assert call_args[1] == "push"

    def test_prune_silent_when_10_or_fewer(self, panel):
        """When <=10 release tags, no pruning happens."""
        from utils import _prune_old_tags
        tags = [f"v1.{i}.0" for i in range(10, 0, -1)]  # 10 tags, newest first
        mock_output = "\n".join(tags)

        with patch("subprocess.run") as mock_run:
            tag_call = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=mock_output, stderr="")
            mock_run.return_value = tag_call

            _prune_old_tags(keep_count=10)

            # Only one call: git tag --sort=-v:refname
            assert mock_run.call_count == 1

    def test_prune_silent_when_no_tags(self, panel):
        """When no tags exist, silent no-op."""
        from utils import _prune_old_tags

        with patch("subprocess.run") as mock_run:
            tag_call = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr="")
            mock_run.return_value = tag_call

            _prune_old_tags(keep_count=10)

            assert mock_run.call_count == 1  # only tag listing

    def test_prune_handles_git_failure(self, panel):
        """When git tag fails, function returns silently."""
        from utils import _prune_old_tags

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="")

            # Should not raise
            _prune_old_tags(keep_count=10)

    def test_prune_handles_timeout(self, panel):
        """When git times out, function returns silently."""
        from utils import _prune_old_tags

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 10)):
            # Should not raise
            _prune_old_tags(keep_count=10)

    def test_prune_filters_non_semver_tags(self, panel):
        """Only vX.Y.Z tags are pruned; other tags are ignored."""
        from utils import _prune_old_tags
        tags = (["v2.0.0", "v1.9.0", "v1.8.0", "v1.7.0", "v1.6.0",
                 "v1.5.0", "v1.4.0", "v1.3.0", "v1.2.0", "v1.1.0",
                 "v1.0.0", "beta-release", "experiment",  # 11 semver + 2 non-semver
                 "v0.9.0", "v0.8.0"])  # these extra 2 should be pruned
        mock_output = "\n".join(tags)

        with patch("subprocess.run") as mock_run:
            tag_call = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=mock_output, stderr="")
            push_call = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr="")
            # 1 tag call + up to 13 pushes (but only 3 semver tags beyond keep_count: v1.0.0, v0.9.0, v0.8.0)
            mock_run.side_effect = [tag_call] + [push_call] * 20

            _prune_old_tags(keep_count=10)

            # First call is git tag
            # Deletes should target v1.0.0, v0.9.0, v0.8.0 (the 3 semver tags beyond 10)
            delete_calls = mock_run.call_args_list[1:]
            deleted_tags = []
            for call in delete_calls:
                args = call[0][0]
                if args[1] == "push":
                    # git push origin --delete <tag>
                    deleted_tags.append(args[4])
            assert "beta-release" not in deleted_tags
            assert "experiment" not in deleted_tags
            assert "v1.0.0" in deleted_tags


class TestDoRelease:
    """(c) do_release with --dry-run prints expected plan
       (d) do_release fails on non-git dir
       (e) do_release fails on dirty tree
       (f) do_release fails on non-default branch
       (g) do_release fails on invalid bump type"""

    def test_dry_run_prints_plan(self, panel, tmpdir_path):
        """--dry-run should print the release plan without making changes."""
        from utils import do_release
        repo = _make_git_repo(os.path.join(tmpdir_path, "test-release"))

        with patch("sys.exit") as mock_exit, \
             patch("subprocess.run") as mock_run:
            # Mock all git subprocess calls
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="main\n", stderr="")
            # But we need rev-list to return empty (up to date)
            # And diff-index to return 0 (clean tree)
            # And git rev-parse --abbrev-ref to return "main"

            def mock_side_effect(*args, **kwargs):
                cmd = args[0]
                if cmd[0] == "git" and "rev-parse" in cmd:
                    return subprocess.CompletedProcess(
                        args=[], returncode=0, stdout="main\n", stderr="")
                elif cmd[0] == "git" and "diff-index" in cmd:
                    return subprocess.CompletedProcess(
                        args=[], returncode=0, stdout="", stderr="")
                elif cmd[0] == "git" and "rev-list" in cmd:
                    return subprocess.CompletedProcess(
                        args=[], returncode=0, stdout="", stderr="")
                elif cmd[0] == "git" and "fetch" in cmd:
                    return subprocess.CompletedProcess(
                        args=[], returncode=0, stdout="", stderr="")
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr="")

            mock_run.side_effect = mock_side_effect

            with patch("builtins.print") as mock_print:
                do_release("patch", repo, dry_run=True)

            # Verify it printed the dry-run plan
            printed = [str(call[0][0]) if call[0] else ""
                       for call in mock_print.call_args_list]
            full_output = " ".join(printed)
            assert "[DRY RUN]" in full_output
            assert "1.2.1" in full_output
            assert "1.2.2" in full_output
            assert "No changes made" in full_output

    def test_fails_on_non_git_dir(self, panel, tmpdir_path):
        """Non-git directory should cause exit(1)."""
        from utils import do_release
        non_git = os.path.join(tmpdir_path, "not-a-repo")
        os.makedirs(non_git, exist_ok=True)

        with pytest.raises(SystemExit) as exc_info, \
             patch("builtins.print") as mock_print:
            do_release("patch", non_git)

        assert exc_info.value.code == 1
        printed = str(mock_print.call_args[0][0]) if mock_print.call_args else ""
        assert "not a git repository" in printed.lower() or "Not a git" in printed

    def test_fails_on_dirty_tree(self, panel, tmpdir_path):
        """Dirty working tree should cause exit(1) with git status."""
        from utils import do_release
        repo = _make_git_repo(os.path.join(tmpdir_path, "dirty-repo"))
        # Make the tree dirty
        with open(os.path.join(repo, "DIRTY"), "w") as f:
            f.write("unstaged change\n")

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "git" and "rev-parse" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="main\n", stderr="")
            elif cmd[0] == "git" and "diff-index" in cmd:
                # Simulate dirty: non-zero exit
                return subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="", stderr="")
            elif cmd[0] == "git" and "status" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout=" M DIRTY\n", stderr="")
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run_side_effect), \
             patch("utils._detect_default_branch", return_value="main"), \
             pytest.raises(SystemExit) as exc_info, \
             patch("builtins.print") as mock_print:
            do_release("patch", repo)

        assert exc_info.value.code == 1
        printed = " ".join([str(c[0][0]) if c[0] else ""
                            for c in mock_print.call_args_list])
        assert "dirty" in printed.lower() or "commit or stash" in printed.lower()

    def test_fails_on_non_default_branch(self, panel, tmpdir_path):
        """Not on default branch should cause exit(1)."""
        from utils import do_release
        repo = _make_git_repo(os.path.join(tmpdir_path, "branch-repo"))

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "git" and "rev-parse" in cmd:
                # Return a different branch name
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="feature-branch\n", stderr="")
            elif cmd[0] == "git" and "diff-index" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run_side_effect), \
             pytest.raises(SystemExit) as exc_info, \
             patch("builtins.print") as mock_print:
            do_release("patch", repo)

        assert exc_info.value.code == 1
        printed = str(mock_print.call_args[0][0]) if mock_print.call_args else ""
        assert "default branch" in printed.lower() or "expected" in printed.lower()

    def test_fails_on_invalid_bump_type(self, panel, tmpdir_path):
        """Invalid bump type should cause exit(1)."""
        from utils import do_release
        repo = _make_git_repo(os.path.join(tmpdir_path, "bump-repo"))

        with pytest.raises(SystemExit) as exc_info, \
             patch("builtins.print") as mock_print:
            do_release("invalid", repo)

        assert exc_info.value.code == 1
        printed = str(mock_print.call_args[0][0]) if mock_print.call_args else ""
        assert "invalid bump" in printed.lower() or "must be one of" in printed.lower()

    def test_fails_when_behind_origin(self, panel, tmpdir_path):
        """Behind origin should cause exit(1)."""
        from utils import do_release
        repo = _make_git_repo(os.path.join(tmpdir_path, "behind-repo"))

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "git" and "rev-parse" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="main\n", stderr="")
            elif cmd[0] == "git" and "diff-index" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr="")
            elif cmd[0] == "git" and "fetch" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr="")
            elif cmd[0] == "git" and "rev-list" in cmd:
                # Behind by 3 commits
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="abc\ndef\nghi\n", stderr="")
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run_side_effect), \
             patch("utils._detect_default_branch", return_value="main"), \
             pytest.raises(SystemExit) as exc_info, \
             patch("builtins.print") as mock_print:
            do_release("patch", repo)

        assert exc_info.value.code == 1
        printed = str(mock_print.call_args[0][0]) if mock_print.call_args else ""
        assert "behind" in printed.lower() or "pull" in printed.lower()

    def test_dry_run_makes_no_changes(self, panel, tmpdir_path):
        """--dry-run must not modify VERSION file or git state."""
        from utils import do_release
        repo = _make_git_repo(os.path.join(tmpdir_path, "dry-no-change"))
        version_path = os.path.join(repo, "VERSION")
        original_content = open(version_path).read()

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "git" and "rev-parse" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="main\n", stderr="")
            elif cmd[0] == "git" and "diff-index" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr="")
            elif cmd[0] == "git" and "rev-list" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr="")
            elif cmd[0] == "git" and "fetch" in cmd:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run_side_effect), \
             patch("sys.exit"), \
             patch("builtins.print"):
            do_release("patch", repo, dry_run=True)

        # VERSION file should be unchanged
        assert open(version_path).read() == original_content


class TestReleaseHelpText:
    """(i) --release in HELP_TEXT output"""

    def test_release_in_help_text(self, panel):
        """HELP_TEXT should contain --release documentation."""
        assert "--release" in panel.HELP_TEXT, (
            "--release should be documented in HELP_TEXT COMMANDS section"
        )
        assert "patch" in panel.HELP_TEXT, (
            "HELP_TEXT should mention patch bump type"
        )

    def test_release_in_help_output(self, panel):
        """dokima --help should include --release."""
        result = subprocess.run(
            [sys.executable, PANEL_PATH, "--help"],
            capture_output=True, text=True, timeout=15
        )
        assert "--release" in result.stdout, (
            "--release should appear in --help output"
        )


class TestReleaseHelpJson:
    """(j) --release in --help-json output"""

    def _run_help_json(self):
        """Run dokima --help-json and return parsed JSON."""
        result = subprocess.run(
            [sys.executable, PANEL_PATH, "--help-json"],
            capture_output=True, text=True, timeout=15
        )
        return result.returncode, json.loads(result.stdout)

    def test_release_in_help_json_commands(self, panel):
        """--release should appear in CLI_METADATA commands output."""
        rc, data = self._run_help_json()
        assert rc == 0
        command_names = [c["name"] for c in data["commands"]]
        assert "--release" in command_names, (
            "--release should be in --help-json commands"
        )

    def test_release_command_has_required_fields(self, panel):
        """--release command entry should have name, syntax, description."""
        rc, data = self._run_help_json()
        assert rc == 0
        release_cmd = None
        for cmd in data["commands"]:
            if cmd["name"] == "--release":
                release_cmd = cmd
                break
        assert release_cmd is not None, "--release not found in commands"
        assert "syntax" in release_cmd, "Missing syntax field"
        assert "description" in release_cmd, "Missing description field"
        assert "release" in release_cmd["description"].lower(), (
            "Description should mention release"
        )


class TestReleaseFlagDispatch:
    """Integration tests for --release flag parsing in dokima."""

    def _run_dokima(self, *args):
        """Run dokima with given args, return (returncode, stdout, stderr)."""
        cmd = [sys.executable, PANEL_PATH] + list(args)
        # Set env to avoid real repo interactions
        env = os.environ.copy()
        env["GH_TOKEN"] = "test-token"
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=env)
        return result.returncode, result.stdout, result.stderr

    def test_release_flag_without_bump_type_shows_error(self, panel):
        """--release without bump type should exit with error."""
        rc, stdout, stderr = self._run_dokima("--release")
        assert rc != 0, "Expected non-zero exit for missing bump type"
        combined = stdout + stderr
        assert "release requires a bump type" in combined.lower() or \
               "patch" in combined.lower()

    def test_release_flag_with_invalid_bump_type_shows_error(self, panel):
        """--release with invalid bump type should exit with error."""
        rc, stdout, stderr = self._run_dokima("--release", "badbump")
        assert rc != 0, "Expected non-zero exit for invalid bump type"
        combined = stdout + stderr
        assert "invalid" in combined.lower()
