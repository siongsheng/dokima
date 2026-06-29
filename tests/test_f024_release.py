"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases."""
import sys, os
from unittest.mock import patch

# Ensure the project root is on the path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils


class TestBumpVersion:
    """Tests for _bump_version() helper."""

    def test_bump_patch_increments_z(self):
        """patch: 1.2.1 → 1.2.2"""
        result = utils._bump_version("1.2.1", "patch")
        assert result == "1.2.2", f"Expected 1.2.2, got {result}"

    def test_bump_minor_increments_y_resets_z(self):
        """minor: 1.2.1 → 1.3.0"""
        result = utils._bump_version("1.2.1", "minor")
        assert result == "1.3.0", f"Expected 1.3.0, got {result}"

    def test_bump_major_increments_x_resets_yz(self):
        """major: 1.2.1 → 2.0.0"""
        result = utils._bump_version("1.2.1", "major")
        assert result == "2.0.0", f"Expected 2.0.0, got {result}"

    def test_bump_patch_from_zero(self):
        """patch: 0.0.1 → 0.0.2"""
        result = utils._bump_version("0.0.1", "patch")
        assert result == "0.0.2", f"Expected 0.0.2, got {result}"

    def test_bump_minor_from_zero(self):
        """minor: 0.0.1 → 0.1.0"""
        result = utils._bump_version("0.0.1", "minor")
        assert result == "0.1.0", f"Expected 0.1.0, got {result}"

    def test_bump_major_from_zero(self):
        """major: 0.0.1 → 1.0.0"""
        result = utils._bump_version("0.0.1", "major")
        assert result == "1.0.0", f"Expected 1.0.0, got {result}"

    def test_patch_at_nine(self):
        """patch: 9.9.9 → 9.9.10 (NOT 10.0.0)"""
        result = utils._bump_version("9.9.9", "patch")
        assert result == "9.9.10", f"Expected 9.9.10, got {result}"

    def test_minor_wraps_z(self):
        """minor: 1.9.5 → 1.10.0"""
        result = utils._bump_version("1.9.5", "minor")
        assert result == "1.10.0", f"Expected 1.10.0, got {result}"

    def test_major_wraps_yz(self):
        """major: 5.9.1 → 6.0.0"""
        result = utils._bump_version("5.9.1", "major")
        assert result == "6.0.0", f"Expected 6.0.0, got {result}"


class TestBumpVersionRejectsInvalid:
    """Tests for _bump_version() rejecting invalid bump types."""

    def test_rejects_nonsense(self):
        """Invalid bump type raises ValueError."""
        try:
            utils._bump_version("1.2.1", "nonsense")
            assert False, "Expected ValueError"
        except ValueError:
            pass

    def test_rejects_prepatch(self):
        """prepatch is not a valid bump type."""
        try:
            utils._bump_version("1.2.1", "prepatch")
            assert False, "Expected ValueError"
        except ValueError:
            pass

    def test_rejects_empty_bump(self):
        """Empty bump type raises ValueError."""
        try:
            utils._bump_version("1.2.1", "")
            assert False, "Expected ValueError"
        except ValueError:
            pass

    def test_rejects_invalid_version(self):
        """Invalid version string raises ValueError."""
        try:
            utils._bump_version("not.a.version", "patch")
            assert False, "Expected ValueError"
        except ValueError:
            pass


class TestPruneOldTags:
    """Tests for _prune_old_tags() helper."""

    def test_no_tags_silent_noop(self):
        """No tags → silent no-op."""
        git_calls = []

        def fake_git(*args):
            git_calls.append(args)
            if args[0] == "tag":
                return ("", "", 0)  # No tags
            return ("", "", 0)

        with patch.object(utils, "git", side_effect=fake_git):
            utils._prune_old_tags()

        # Only the tag listing call, no push deletes
        assert len([c for c in git_calls if c[0] == "push"]) == 0

    def test_fewer_than_keep_count_silent_noop(self):
        """5 tags, keep_count=10 → no pruning."""
        git_calls = []

        def fake_git(*args):
            git_calls.append(args)
            if args[0] == "tag":
                return ("v1.0.0\nv0.9.0\nv0.8.0\nv0.7.0\nv0.6.0", "", 0)
            return ("", "", 0)

        with patch.object(utils, "git", side_effect=fake_git):
            utils._prune_old_tags(keep_count=10)

        push_deletes = [c for c in git_calls if c[0] == "push"]
        assert len(push_deletes) == 0

    def test_exactly_keep_count_silent_noop(self):
        """Exactly 10 tags, keep_count=10 → no pruning."""
        git_calls = []
        tags = "\n".join(f"v1.{i}.0" for i in range(9, -1, -1))

        def fake_git(*args):
            git_calls.append(args)
            if args[0] == "tag":
                return (tags, "", 0)
            return ("", "", 0)

        with patch.object(utils, "git", side_effect=fake_git):
            utils._prune_old_tags(keep_count=10)

        push_deletes = [c for c in git_calls if c[0] == "push"]
        assert len(push_deletes) == 0

    def test_more_than_keep_count_prunes_extras(self):
        """12 tags, keep_count=10 → 2 deleted."""
        git_calls = []

        def fake_git(*args):
            git_calls.append(args)
            if args[0] == "tag":
                tags = "\n".join(f"v1.{i}.0" for i in range(11, -1, -1))
                return (tags, "", 0)
            return ("", "", 0)

        with patch.object(utils, "git", side_effect=fake_git):
            utils._prune_old_tags(keep_count=10)

        push_deletes = [c for c in git_calls if c[0] == "push"]
        assert len(push_deletes) == 2
        # Check they delete the oldest tags (index 10, 11)
        deleted_tags = set()
        for call_args in push_deletes:
            for a in call_args:
                if isinstance(a, str) and a.startswith("v"):
                    deleted_tags.add(a)
        assert "v1.0.0" in deleted_tags
        assert "v1.1.0" in deleted_tags
        # The 10 newest should NOT be deleted
        assert "v1.11.0" not in deleted_tags
        assert "v1.10.0" not in deleted_tags

    def test_non_version_tags_ignored(self):
        """Non-vX.Y.Z tags are ignored in count, none deleted."""
        git_calls = []
        tags = "v1.2.0\nv1.1.0\nexperiment\nbeta\nv1.0.0"

        def fake_git(*args):
            git_calls.append(args)
            if args[0] == "tag":
                return (tags, "", 0)
            return ("", "", 0)

        with patch.object(utils, "git", side_effect=fake_git):
            utils._prune_old_tags(keep_count=10)

        push_deletes = [c for c in git_calls if c[0] == "push"]
        assert len(push_deletes) == 0

    def test_custom_keep_count(self):
        """keep_count=2 keeps 2, deletes the rest."""
        git_calls = []

        def fake_git(*args):
            git_calls.append(args)
            if args[0] == "tag":
                tags = "v3.0.0\nv2.0.0\nv1.0.0\nv0.9.0"
                return (tags, "", 0)
            return ("", "", 0)

        with patch.object(utils, "git", side_effect=fake_git):
            utils._prune_old_tags(keep_count=2)

        push_deletes = [c for c in git_calls if c[0] == "push"]
        assert len(push_deletes) == 2

    def test_push_delete_failure_continues(self):
        """If push --delete fails, continue with remaining."""
        git_calls = []
        call_count = [0]

        def fake_git(*args):
            git_calls.append(args)
            if args[0] == "tag":
                tags = "v3.0.0\nv2.0.0\nv1.0.0"
                return (tags, "", 0)
            if args[0] == "push":
                call_count[0] += 1
                if call_count[0] == 1:
                    return ("", "error", 1)  # First delete fails
                return ("", "", 0)
            return ("", "", 0)

        with patch.object(utils, "git", side_effect=fake_git):
            utils._prune_old_tags(keep_count=1)

        # Should have tried 2 deletes (v2.0.0 and v1.0.0)
        push_deletes = [c for c in git_calls if c[0] == "push"]
        assert len(push_deletes) == 2


class TestReleaseHelpText:
    """Tests that --release appears in HELP_TEXT and CLI_METADATA."""

    SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")

    def _run(self, *args):
        import subprocess
        p = subprocess.run(
            [sys.executable, self.SCRIPT] + list(args),
            capture_output=True, text=True, timeout=10
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()

    def test_help_includes_release_command(self):
        """--help output includes --release in COMMANDS section."""
        rc, out, err = self._run("--help")
        assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
        assert "--release" in out, f"Expected --release in help output, got:\n{out}"

    def test_help_json_includes_release(self):
        """--help-json output includes --release entry."""
        rc, out, err = self._run("--help-json")
        assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
        assert "--release" in out, f"Expected --release in --help-json output, got:\n{out}"
