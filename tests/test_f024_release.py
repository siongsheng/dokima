"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases.

Comprehensive test suite covering:
  _bump_version, _prune_old_tags, do_release preconditions, dry-run,
  --release CLI integration, HELP_TEXT, and --help-json output.
"""
import os
import sys
import subprocess
import tempfile
import json as _json
import pytest
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import utils as _utils_mod

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")


def _run(*args, cwd=None, timeout=10):
    """Run dokima with given args and return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=timeout, cwd=cwd
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def _make_git_repo(base_dir, name="test-project", version="1.0.0"):
    """Create a minimal git repo with a VERSION file and one commit.
    Returns the project directory path."""
    project_dir = os.path.join(base_dir, name)
    os.makedirs(project_dir, exist_ok=True)
    subprocess.run(["git", "init", project_dir],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "config", "user.email", "test@test.com"])
    subprocess.run(["git", "-C", project_dir, "config", "user.name", "Test"])
    with open(os.path.join(project_dir, "VERSION"), "w") as f:
        f.write(version + "\n")
    subprocess.run(["git", "-C", project_dir, "add", "-A"])
    subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return project_dir


# ═══════════════════════════════════════════════════════════════════════
# Task 10a: _bump_version — semver arithmetic
# ═══════════════════════════════════════════════════════════════════════

class TestBumpVersion:
    """_bump_version(current, bump) — semver bump arithmetic."""

    def test_patch_increments_z(self):
        """patch bumps Z: 1.2.1 → 1.2.2."""
        assert _utils_mod._bump_version("1.2.1", "patch") == "1.2.2"

    def test_minor_increments_y_resets_z(self):
        """minor bumps Y, resets Z to 0: 1.2.1 → 1.3.0."""
        assert _utils_mod._bump_version("1.2.1", "minor") == "1.3.0"

    def test_major_increments_x_resets_yz(self):
        """major bumps X, resets Y and Z to 0: 1.2.1 → 2.0.0."""
        assert _utils_mod._bump_version("1.2.1", "major") == "2.0.0"

    def test_nines_patch_no_carry(self):
        """9.9.9 patch → 9.9.10 (no carry to minor)."""
        assert _utils_mod._bump_version("9.9.9", "patch") == "9.9.10"

    def test_zero_version_minor(self):
        """0.0.1 → minor → 0.1.0."""
        assert _utils_mod._bump_version("0.0.1", "minor") == "0.1.0"

    def test_strips_whitespace(self):
        """Trailing/leading whitespace is stripped."""
        assert _utils_mod._bump_version("  1.2.1  ", "patch") == "1.2.2"

    def test_handles_v_prefix(self):
        """Leading 'v' prefix is stripped."""
        assert _utils_mod._bump_version("v1.2.1", "minor") == "1.3.0"

    def test_rejects_invalid_bump_type(self):
        """Invalid bump type raises ValueError."""
        with pytest.raises(ValueError):
            _utils_mod._bump_version("1.2.1", "prepatch")

    def test_rejects_unknown_bump_string(self):
        """Arbitrary string raises ValueError."""
        with pytest.raises(ValueError):
            _utils_mod._bump_version("1.2.1", "nonsense")

    def test_rejects_bad_version_format(self):
        """Non-semver version raises ValueError."""
        with pytest.raises(ValueError):
            _utils_mod._bump_version("not-a-version", "patch")

    def test_rejects_too_few_parts(self):
        """Two-part version raises ValueError."""
        with pytest.raises(ValueError):
            _utils_mod._bump_version("1.2", "patch")


# ═══════════════════════════════════════════════════════════════════════
# Task 10h: _prune_old_tags — tag pruning
# ═══════════════════════════════════════════════════════════════════════

class TestPruneOldTags:
    """_prune_old_tags(keep_count=10) — keeps N newest vX.Y.Z tags."""

    def test_no_tags_is_silent_noop(self):
        """With no tags at all, function does nothing (no push --delete calls)."""
        if not hasattr(_utils_mod, '_prune_old_tags'):
            pytest.skip("_prune_old_tags not implemented yet")

        with patch('subprocess.run') as mock_run:
            mock_result = Mock(returncode=0, stdout="", stderr="")
            mock_run.return_value = mock_result
            _utils_mod.PROJECT_DIR = "/fake/repo"
            _utils_mod._prune_old_tags(keep_count=10)
            push_calls = [c for c in mock_run.call_args_list
                          if len(c[0]) >= 1 and "push" in str(c[0])]
            assert len(push_calls) == 0

    def test_under_limit_is_silent_noop(self):
        """When tag count ≤ keep_count, nothing is pruned."""
        if not hasattr(_utils_mod, '_prune_old_tags'):
            pytest.skip("_prune_old_tags not implemented yet")

        with patch('subprocess.run') as mock_run:
            def side_effect(*args, **kwargs):
                m = Mock(returncode=0, stdout="", stderr="")
                cmd = args[0] if args else []
                if "tag" in cmd:
                    m.stdout = "v1.0.0\nv1.0.1\nv1.0.2"
                return m
            mock_run.side_effect = side_effect
            _utils_mod.PROJECT_DIR = "/fake/repo"
            _utils_mod._prune_old_tags(keep_count=10)
            push_calls = [c for c in mock_run.call_args_list
                          if len(c[0]) >= 1 and "push" in str(c[0])]
            assert len(push_calls) == 0

    def test_over_limit_prunes_oldest(self):
        """When >keep_count, deletes oldest vX.Y.Z tags via git push --delete."""
        if not hasattr(_utils_mod, '_prune_old_tags'):
            pytest.skip("_prune_old_tags not implemented yet")

        with patch('subprocess.run') as mock_run:
            tags = "\n".join(f"v0.0.{i}" for i in range(15, 0, -1))
            def side_effect(*args, **kwargs):
                m = Mock(returncode=0, stdout="", stderr="")
                cmd = args[0] if args else []
                if "tag" in cmd:
                    m.stdout = tags
                return m
            mock_run.side_effect = side_effect
            _utils_mod.PROJECT_DIR = "/fake/repo"
            _utils_mod._prune_old_tags(keep_count=10)
            push_calls = [c for c in mock_run.call_args_list
                          if len(c[0]) >= 1 and "push" in str(c[0])]
            assert len(push_calls) == 5  # 15 tags - 10 keep = 5 pruned

    def test_non_semver_tags_are_ignored(self):
        """Only vX.Y.Z tags are pruned; other tags (beta, experiment) are skipped."""
        if not hasattr(_utils_mod, '_prune_old_tags'):
            pytest.skip("_prune_old_tags not implemented yet")

        with patch('subprocess.run') as mock_run:
            tags = "v2.0.0\nv1.0.0\nbeta\nexperiment\nv0.1.0"
            def side_effect(*args, **kwargs):
                m = Mock(returncode=0, stdout="", stderr="")
                cmd = args[0] if args else []
                if "tag" in cmd:
                    m.stdout = tags
                return m
            mock_run.side_effect = side_effect
            _utils_mod.PROJECT_DIR = "/fake/repo"
            _utils_mod._prune_old_tags(keep_count=2)
            push_calls = [c for c in mock_run.call_args_list
                          if len(c[0]) >= 1 and "push" in str(c[0])]
            # Only v-tagged: v2.0.0, v1.0.0, v0.1.0 = 3. Keep 2 → prune 1.
            assert len(push_calls) == 1
            # Verify non-semver tags are not deleted
            args_str = " ".join(str(a) for a in push_calls[0][0])
            assert "beta" not in args_str
            assert "experiment" not in args_str


# ═══════════════════════════════════════════════════════════════════════
# Task 10c-g: do_release — precondition validation + dry-run
# ═══════════════════════════════════════════════════════════════════════

class TestDoReleasePreconditions:
    """do_release validates preconditions before making any changes."""

    def test_dry_run_prints_plan_and_exits_0(self, panel):
        """--dry-run prints the planned actions without making changes."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            project_dir = _make_git_repo(td)
            # Mock all subprocess calls to simulate clean repo state
            with patch('subprocess.run') as mock_run:
                def subprocess_side_effect(*args, **kwargs):
                    m = Mock(returncode=0, stdout="", stderr="")
                    cmd = args[0] if args else []
                    cmd_str = " ".join(str(a) for a in cmd)
                    if "rev-parse" in cmd_str:
                        m.stdout = "main"
                    elif "diff-index" in cmd_str:
                        m.returncode = 0
                    elif "rev-list" in cmd_str:
                        m.stdout = ""
                    elif "fetch" in cmd_str:
                        pass
                    return m
                mock_run.side_effect = subprocess_side_effect

                with patch('utils._detect_default_branch', return_value="main"):
                    with patch('builtins.print') as mock_print:
                        with pytest.raises(SystemExit) as exc_info:
                            panel.do_release("patch", project_dir, dry_run=True)
                        assert exc_info.value.code == 0

                printed = " ".join(str(c) for c in mock_print.call_args_list
                                   if c and c[0])
                assert "[DRY RUN]" in printed or "dry" in printed.lower(), \
                    f"Dry-run output should mention dry run: {printed}"
                assert "v1.0.1" in printed, \
                    f"Dry-run should mention target version v1.0.1: {printed}"

    def test_fails_on_non_git_dir(self, panel):
        """do_release exits 1 when project_dir is not a git repo."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            with pytest.raises(SystemExit) as exc_info:
                panel.do_release("patch", td)
            assert exc_info.value.code == 1

    def test_fails_on_invalid_bump_type(self, panel):
        """do_release exits 1 for invalid bump type."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with pytest.raises(SystemExit) as exc_info:
            panel.do_release("invalid", "/fake/project")
        assert exc_info.value.code == 1

    def test_fails_on_missing_version_file(self, panel):
        """do_release exits 1 when VERSION file doesn't exist."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            # Initialize git repo WITHOUT a VERSION file
            subprocess.run(["git", "init", td],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "-C", td, "config", "user.email", "test@test.com"])
            subprocess.run(["git", "-C", td, "config", "user.name", "Test"])
            # Create a dummy file so repo has at least one commit
            with open(os.path.join(td, "README.md"), "w") as f:
                f.write("# test\n")
            subprocess.run(["git", "-C", td, "add", "-A"])
            subprocess.run(["git", "-C", td, "commit", "-m", "init"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            with pytest.raises(SystemExit) as exc_info:
                panel.do_release("patch", td)
            assert exc_info.value.code == 1

    def test_fails_on_dirty_tree(self, panel):
        """do_release exits 1 when working tree has uncommitted changes."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            # Initialize git repo with VERSION committed
            subprocess.run(["git", "init", td],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "-C", td, "config", "user.email", "test@test.com"])
            subprocess.run(["git", "-C", td, "config", "user.name", "Test"])
            with open(os.path.join(td, "VERSION"), "w") as f:
                f.write("1.0.0\n")
            subprocess.run(["git", "-C", td, "add", "-A"])
            subprocess.run(["git", "-C", td, "commit", "-m", "init"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Create an untracked file to make tree dirty
            with open(os.path.join(td, "dirty.txt"), "w") as f:
                f.write("dirty\n")

            with pytest.raises(SystemExit) as exc_info:
                panel.do_release("patch", td)
            assert exc_info.value.code == 1

    def test_fails_on_non_default_branch(self, panel):
        """do_release exits 1 when not on the default branch."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            # Initialize git repo with VERSION committed
            subprocess.run(["git", "init", td],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "-C", td, "config", "user.email", "test@test.com"])
            subprocess.run(["git", "-C", td, "config", "user.name", "Test"])
            with open(os.path.join(td, "VERSION"), "w") as f:
                f.write("1.0.0\n")
            subprocess.run(["git", "-C", td, "add", "-A"])
            subprocess.run(["git", "-C", td, "commit", "-m", "init"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Create and switch to a non-default branch
            subprocess.run(["git", "-C", td, "checkout", "-b", "feature-branch"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            with pytest.raises(SystemExit) as exc_info:
                panel.do_release("patch", td)
            assert exc_info.value.code == 1

    def test_fails_when_behind_origin(self, panel):
        """do_release exits 1 when local branch is behind origin."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            project_dir = _make_git_repo(td)
            # Mock subprocess: git fetch succeeds, git rev-list returns commits
            with patch('subprocess.run') as mock_run:
                def side_effect(*args, **kwargs):
                    m = Mock(returncode=0, stdout="", stderr="")
                    cmd_str = " ".join(str(a) for a in args[0]) if args else ""
                    if "rev-list" in cmd_str:
                        # Simulate 3 commits behind
                        m.stdout = "abc\ndef\nghi"
                    elif "diff-index" in cmd_str:
                        m.returncode = 0  # Clean tree
                    elif "rev-parse" in cmd_str:
                        m.stdout = "main"
                    return m
                mock_run.side_effect = side_effect

                # Patch _detect_default_branch
                with patch.object(panel._utils, '_detect_default_branch',
                                  return_value="main"):
                    with pytest.raises(SystemExit) as exc_info:
                        panel.do_release("patch", project_dir)
                    assert exc_info.value.code == 1


# ═══════════════════════════════════════════════════════════════════════
# Task 10i-j: CLI integration — HELP_TEXT and --help-json
# ═══════════════════════════════════════════════════════════════════════

class TestReleaseCliIntegration:
    """Integration tests for dokima --release via subprocess invocation."""

    def test_release_in_help_text(self):
        """--help output includes --release command."""
        rc, out, err = _run("--help")
        assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
        assert "--release" in out, \
            f"--release not in help output:\n{out}"

    def test_release_in_help_json(self):
        """--help-json includes --release command in commands array."""
        rc, out, err = _run("--help-json")
        assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
        data = _json.loads(out)
        commands = data.get("commands", [])
        release_cmds = [c for c in commands if c.get("name") == "--release"]
        assert len(release_cmds) == 1, \
            f"--release not found in commands array (found {len(release_cmds)}): {commands}"

    def test_release_no_bump_shows_error(self):
        """dokima --release (no bump type) exits non-zero with bump type error."""
        rc, out, err = _run("--release")
        assert rc != 0, f"Expected non-zero exit, got {rc}"
        combined = (out + err).lower()
        is_panel_error = "feature description required" in combined
        # Should NOT be the generic "Feature description required" error
        # (which would mean --release wasn't recognized as a flag)
        assert not is_panel_error, \
            f"--release should be recognized as a flag. Got out={out!r} err={err!r}"

    def test_release_invalid_bump_exits_1(self):
        """dokima --release invalid exits 1."""
        rc, out, err = _run("--release", "invalid")
        assert rc == 1, f"Expected exit 1, got {rc}. out={out!r} err={err!r}"
        combined = (out + err).lower()
        assert "patch" in combined or "minor" in combined or "major" in combined, \
            f"Error should mention valid bump types. Got out={out!r} err={err!r}"

    def test_release_patch_in_non_git_dir(self):
        """dokima --release patch in non-git dir dispatches to do_release."""
        with tempfile.TemporaryDirectory() as td:
            rc, out, err = _run("--release", "patch", cwd=td)
            combined = out + err
            # Should dispatch to do_release (not panel's generic validation)
            assert "the panel requires a git repository to operate in" not in combined.lower(), \
                f"Should dispatch to do_release, not panel. Got: {combined!r}"

    def test_release_patch_in_git_repo_with_version(self):
        """dokima --release patch --dry-run in a git repo prints plan."""
        with tempfile.TemporaryDirectory() as base:
            project_dir = _make_git_repo(base)
            rc, out, err = _run("--release", "patch", "--dry-run", project_dir,
                                cwd=project_dir)
            combined = out + err
            # Should dispatch to do_release (not panel's generic validation)
            assert "the panel requires a git repository to operate in" not in combined.lower(), \
                f"Should dispatch to do_release. Got: {combined!r}"


# ═══════════════════════════════════════════════════════════════════════
# Edge cases from spec §11 Test Plan
# ═══════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge cases from spec §11 Test Plan."""

    def test_bump_version_handles_v_prefix_in_file(self):
        """VERSION file with 'v' prefix is handled (spec line 319)."""
        assert _utils_mod._bump_version("v1.2.1", "patch") == "1.2.2"

    def test_bump_version_single_digit_components(self):
        """0.0.0 → patch → 0.0.1."""
        assert _utils_mod._bump_version("0.0.0", "patch") == "0.0.1"

    def test_bump_version_large_components(self):
        """Large version numbers handled correctly."""
        assert _utils_mod._bump_version("99.99.99", "patch") == "99.99.100"
        assert _utils_mod._bump_version("99.99.99", "minor") == "99.100.0"
        assert _utils_mod._bump_version("99.99.99", "major") == "100.0.0"

    def test_dry_run_makes_zero_changes(self, panel):
        """--dry-run must make zero changes to filesystem/git state (spec §11)."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            project_dir = _make_git_repo(td, version="2.0.0")
            version_path = os.path.join(project_dir, "VERSION")

            # Record initial state
            with open(version_path) as f:
                initial_version = f.read().strip()

            # Mock subprocess to simulate clean repo state
            with patch('subprocess.run') as mock_run:
                def subprocess_side_effect(*args, **kwargs):
                    m = Mock(returncode=0, stdout="", stderr="")
                    cmd = args[0] if args else []
                    cmd_str = " ".join(str(a) for a in cmd)
                    if "rev-parse" in cmd_str:
                        m.stdout = "main"
                    elif "diff-index" in cmd_str:
                        m.returncode = 0
                    elif "rev-list" in cmd_str:
                        m.stdout = ""
                    elif "fetch" in cmd_str:
                        pass
                    return m
                mock_run.side_effect = subprocess_side_effect

                with patch('utils._detect_default_branch', return_value="main"):
                    with patch('builtins.print'):
                        with pytest.raises(SystemExit) as exc_info:
                            panel.do_release("patch", project_dir, dry_run=True)
                        assert exc_info.value.code == 0

            # Verify VERSION file unchanged
            with open(version_path) as f:
                assert f.read().strip() == initial_version, \
                    "VERSION file must not change during dry-run"


class TestPruneOldTagsOrdering:
    """Verify version ordering: newest kept, oldest pruned."""

    def test_keeps_newest_deletes_oldest(self):
        """Newest tags are retained, oldest are pruned."""
        if not hasattr(_utils_mod, '_prune_old_tags'):
            pytest.skip("_prune_old_tags not implemented yet")

        with patch('subprocess.run') as mock_run:
            tags = "v3.0.0\nv2.0.0\nv1.0.0"  # newest first
            def side_effect(*args, **kwargs):
                m = Mock(returncode=0, stdout="", stderr="")
                cmd = args[0] if args else []
                if "tag" in cmd:
                    m.stdout = tags
                return m
            mock_run.side_effect = side_effect
            _utils_mod.PROJECT_DIR = "/fake/repo"
            _utils_mod._prune_old_tags(keep_count=2)
            push_calls = [c for c in mock_run.call_args_list
                          if len(c[0]) >= 1 and "push" in str(c[0])]
            assert len(push_calls) == 1  # 3 tags - 2 keep = 1
            # The deleted one should be the OLDEST (v1.0.0)
            args_str = " ".join(str(a) for a in push_calls[0][0])
            assert "v1.0.0" in args_str, f"Oldest tag v1.0.0 should be pruned: {args_str}"
            assert "v3.0.0" not in args_str, "Newest tag v3.0.0 must not be pruned"
