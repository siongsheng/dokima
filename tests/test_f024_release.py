"""Tests for _prune_old_tags — release tag pruning helper.
Tests via panel fixture (class-based) and via direct utils import (module-level).
"""
import pytest
from unittest.mock import patch


# ── Module-level tests (direct utils import) ──────────

def test_prune_no_tags_silent_noop():
    """When no tags exist, _prune_old_tags is silent no-op returning 0."""
    import utils
    with patch('utils.git', return_value=("", "", 0)):
        result = utils._prune_old_tags()
        assert result == 0


def test_prune_fewer_than_keep_count():
    """When tags <= keep_count, no pruning occurs."""
    import utils
    tags = "v3.0.0\nv2.0.0\nv1.0.0"
    with patch('utils.git', return_value=(tags, "", 0)):
        result = utils._prune_old_tags(keep_count=5)
        assert result == 0


def test_prune_exactly_keep_count():
    """When tags == keep_count, no pruning occurs."""
    import utils
    tags = "\n".join("v{}.0.0".format(i) for i in range(10, 0, -1))
    with patch('utils.git', return_value=(tags, "", 0)):
        result = utils._prune_old_tags(keep_count=10)
        assert result == 0


def test_prune_more_than_keep_count():
    """When >keep_count tags exist, keeps newest and prunes rest."""
    import utils
    # 12 version tags v12.0.0 through v1.0.0 (newest first)
    tags = "\n".join("v{}.0.0".format(i) for i in range(12, 0, -1))

    call_args = []

    def mock_git(*args):
        call_args.append(args)
        if args[0] == "tag":
            return (tags, "", 0)
        elif args[0] == "push":
            return ("", "", 0)
        return ("", "", 1)

    with patch('utils.git', side_effect=mock_git):
        result = utils._prune_old_tags(keep_count=10)

    assert result == 2  # 12 tags, keep 10 → prune 2
    push_calls = [a for a in call_args if a[0] == "push"]
    assert len(push_calls) == 2
    deleted_tags = [a[-1] for a in push_calls]
    assert "v1.0.0" in deleted_tags, f"Expected v1.0.0 to be pruned, got: {deleted_tags}"
    assert "v2.0.0" in deleted_tags, f"Expected v2.0.0 to be pruned, got: {deleted_tags}"


def test_prune_ignores_non_version_tags():
    """Only vX.Y.Z tags are considered for pruning."""
    import utils
    tags = "v3.0.0\nsome-custom-tag\nv2.0.0\nbeta\nv1.0.0\nexperiment"

    call_args = []

    def mock_git(*args):
        call_args.append(args)
        if args[0] == "tag":
            return (tags, "", 0)
        elif args[0] == "push":
            return ("", "", 0)
        return ("", "", 1)

    with patch('utils.git', side_effect=mock_git):
        result = utils._prune_old_tags(keep_count=2)

    # Only 3 version tags: v3.0.0, v2.0.0, v1.0.0 — keep 2 → prune v1.0.0
    assert result == 1
    push_calls = [a for a in call_args if a[0] == "push"]
    assert len(push_calls) == 1
    assert push_calls[0][-1] == "v1.0.0"


def test_prune_push_failure_continues():
    """When push --delete fails for a tag, warn and continue with remaining."""
    import utils
    tags = "\n".join("v{}.0.0".format(i) for i in range(12, 0, -1))

    call_args = []

    def mock_git(*args):
        call_args.append(args)
        if args[0] == "tag":
            return (tags, "", 0)
        elif args[0] == "push":
            # First push call fails, second succeeds
            push_count = len([a for a in call_args if a[0] == "push"])
            if push_count == 1:
                return ("", "remote: error", 1)
            return ("", "", 0)
        return ("", "", 1)

    with patch('utils.git', side_effect=mock_git):
        result = utils._prune_old_tags(keep_count=10)

    # 2 tags to prune, 1 succeeded
    assert result == 1


def test_prune_git_tag_failure():
    """When git tag command fails, returns 0 silently."""
    import utils
    with patch('utils.git', return_value=("", "fatal: not a git repo", 128)):
        result = utils._prune_old_tags()
        assert result == 0


def test_prune_default_keep_count():
    """Default keep_count is 10."""
    import utils
    tags = "\n".join("v{}.0.0".format(i) for i in range(15, 0, -1))

    call_args = []

    def mock_git(*args):
        call_args.append(args)
        if args[0] == "tag":
            return (tags, "", 0)
        elif args[0] == "push":
            return ("", "", 0)
        return ("", "", 1)

    with patch('utils.git', side_effect=mock_git):
        result = utils._prune_old_tags()

    # 15 tags, default keep_count=10 → prune 5
    assert result == 5
    push_calls = [a for a in call_args if a[0] == "push"]
    assert len(push_calls) == 5


# ── Panel fixture tests (class-based) ──────────────────

class TestPruneOldTags:
    """Tests for _prune_old_tags(keep_count=10) via panel fixture."""

    # ── no-op cases ──────────────────────────────────────────────

    def test_no_tags_is_silent_noop(self, panel):
        """With no tags at all, the function does nothing."""
        calls = []
        def fake_git(*args):
            calls.append(args)
            return ("", "", 0)
        panel.git = fake_git

        panel._utils._prune_old_tags()

        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        assert len(push_calls) == 0, "should not push-delete when no tags exist"

    def test_fewer_tags_than_keep_count_is_silent_noop(self, panel):
        """When there are fewer tags than keep_count, nothing is pruned."""
        calls = []
        def fake_git(*args):
            calls.append(args)
            if args[0] == "tag":
                return ("v1.0.0\nv1.0.1\nv1.0.2", "", 0)
            return ("", "", 0)
        panel.git = fake_git

        panel._utils._prune_old_tags(keep_count=10)

        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        assert len(push_calls) == 0, "3 tags < 10 keep_count, should be no-op"

    def test_exactly_keep_count_tags_is_silent_noop(self, panel):
        """When there are exactly keep_count tags, nothing is pruned."""
        calls = []
        tags = "\n".join(f"v0.0.{i}" for i in range(1, 6))
        def fake_git(*args):
            calls.append(args)
            if args[0] == "tag":
                return (tags, "", 0)
            return ("", "", 0)
        panel.git = fake_git

        panel._utils._prune_old_tags(keep_count=5)

        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        assert len(push_calls) == 0, "5 tags == 5 keep_count, should be no-op"

    # ── pruning cases ────────────────────────────────────────────

    def test_more_than_keep_count_prunes_oldest(self, panel):
        """When there are > keep_count tags, the oldest ones are deleted."""
        calls = []
        # git tag --sort=-v:refname returns newest first (descending)
        tags = "\n".join(f"v0.0.{i}" for i in range(15, 0, -1))  # v0.0.15 .. v0.0.1
        def fake_git(*args):
            calls.append(args)
            if args[0] == "tag":
                return (tags, "", 0)
            return ("", "", 0)
        panel.git = fake_git

        panel._utils._prune_old_tags(keep_count=10)

        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        assert len(push_calls) == 5, f"should prune 5 tags (15-10=5), got {len(push_calls)} pushes"
        # Should delete the OLDEST (tags[10:] after descending sort: v0.0.5 .. v0.0.1)
        deleted = [c[3] for c in push_calls if len(c) >= 4]
        assert "v0.0.1" in deleted, "oldest tag should be pruned"
        assert "v0.0.5" in deleted, "oldest tags should be pruned"
        assert "v0.0.15" not in deleted, "newest tags should be kept"

    def test_mixed_non_semver_tags_are_ignored(self, panel):
        """Only vX.Y.Z tags are pruned; other tags (experiment, beta) are ignored."""
        calls = []
        tags = ("v2.0.0\nv1.9.9\nv1.0.0\nbeta\n"
                "experiment\nv0.9.0\nv0.1.0\nnot-a-version\n"
                "v3.0.0\nv3.1.0\nv3.2.0\nv3.3.0")
        def fake_git(*args):
            calls.append(args)
            if args[0] == "tag":
                return (tags, "", 0)
            return ("", "", 0)
        panel.git = fake_git

        panel._utils._prune_old_tags(keep_count=5)

        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        # Only vX.Y.Z tags: v3.3.0, v3.2.0, v3.1.0, v3.0.0, v2.0.0, v1.9.9, v1.0.0, v0.9.0, v0.1.0 = 9 tags
        # Keep 5, prune 4
        assert len(push_calls) == 4, f"should prune 4 semver tags (9-5=4), got {len(push_calls)}"
        # beta, experiment, not-a-version should NOT be in any push call
        deleted_tags = [c[3] for c in push_calls if len(c) >= 4]
        for non_semver in ("beta", "experiment", "not-a-version"):
            assert non_semver not in deleted_tags, f"non-semver tag '{non_semver}' should not be pruned"

    # ── edge cases ───────────────────────────────────────────────

    def test_git_tag_failure_is_silent(self, panel):
        """If git tag --sort fails (non-zero return code), function returns silently."""
        calls = []
        def fake_git(*args):
            calls.append(args)
            return ("", "permission denied", 1)
        panel.git = fake_git

        panel._utils._prune_old_tags()

        # Should not attempt any pushes
        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        assert len(push_calls) == 0, "should not push if tag listing fails"

    def test_custom_keep_count(self, panel):
        """keep_count can be set to a custom value."""
        calls = []
        tags = "\n".join(f"v{1 + i//3}.{i%3}.{i%3}" for i in range(10))
        def fake_git(*args):
            calls.append(args)
            if args[0] == "tag":
                return (tags, "", 0)
            return ("", "", 0)
        panel.git = fake_git

        panel._utils._prune_old_tags(keep_count=3)

        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        assert len(push_calls) == 7, f"10 tags, keep 3 → prune 7, got {len(push_calls)} pruned"

    def test_push_failure_on_one_tag_continues(self, panel):
        """If git push --delete fails for one tag, warn and continue with remaining."""
        calls = []
        tags = "\n".join(f"v0.0.{i}" for i in range(1, 13))  # 12 tags, keep 10 → prune 2
        def fake_git(*args):
            calls.append(args)
            if args[0] == "tag":
                return (tags, "", 0)
            if args[0] == "push" and args[3] == "v0.0.1":
                raise RuntimeError("remote rejected")
            return ("", "", 0)
        panel.git = fake_git

        # Should not raise — handles exception internally
        panel._utils._prune_old_tags(keep_count=10)

        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        # Both pushes should have been attempted even if first failed
        assert len(push_calls) == 2, f"should attempt both pushes, got {len(push_calls)}"

    def test_only_v_prefix_tags_are_pruned(self, panel):
        """Tags without v prefix (e.g., '1.0.0') are NOT pruned."""
        calls = []
        # git tag --sort=-v:refname returns newest first
        tags = "v3.0.0\nv2.0.0\nv1.0.0\n1.0.0\n2.0.0\n3.0.0"
        def fake_git(*args):
            calls.append(args)
            if args[0] == "tag":
                return (tags, "", 0)
            return ("", "", 0)
        panel.git = fake_git

        panel._utils._prune_old_tags(keep_count=2)

        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        # Only v-prefixed: v3.0.0, v2.0.0, v1.0.0 = 3 tags. Keep 2 → prune 1
        assert len(push_calls) == 1, f"should prune 1 tag (3 v-tags - 2 keep = 1), got {len(push_calls)}"
        deleted = push_calls[0][3] if len(push_calls[0]) >= 4 else None
        assert deleted == "v1.0.0", f"oldest v-tag should be pruned, got {deleted}"


class TestPruneOldTagsOrdering:
    """Tests verifying version ordering is correct (newest kept, oldest pruned)."""

    def test_major_minor_patch_ordering(self, panel):
        """Tags should be sorted by semver: v2.0.0 > v1.9.9 > v1.0.0."""
        calls = []
        # Deliberately out of order; git tag --sort=-v:refname should sort them
        tags = "v1.9.9\nv1.0.0\nv2.0.0\nv0.1.0\nv1.5.0"
        def fake_git(*args):
            calls.append(args)
            if args[0] == "tag":
                # Simulate git's descending version sort
                return ("v2.0.0\nv1.9.9\nv1.5.0\nv1.0.0\nv0.1.0", "", 0)
            return ("", "", 0)
        panel.git = fake_git

        panel._utils._prune_old_tags(keep_count=3)

        push_calls = [c for c in calls if len(c) >= 1 and c[0] == "push"]
        assert len(push_calls) == 2  # 5 tags - 3 keep = 2
        deleted = [c[3] for c in push_calls if len(c) >= 4]
        # Oldest two should be deleted: v1.0.0 and v0.1.0
        assert "v1.0.0" in deleted
        assert "v0.1.0" in deleted
        assert "v2.0.0" not in deleted
        assert "v1.9.9" not in deleted
        assert "v1.5.0" not in deleted
