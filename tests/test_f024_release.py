"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases.

Covers _bump_version, _prune_old_tags, and do_release.
"""
import os
import sys
import subprocess
import tempfile
import pytest
from unittest.mock import patch, Mock

from conftest import _load_panel as _load

import utils as _utils_mod


# ── Task 1: _bump_version ──────────────────────────────────────────────

class TestBumpVersion:
    """_bump_version(current, bump) — semver arithmetic."""

    def test_patch_bump(self):
        """Patch increments Z, leaves X.Y unchanged."""
        result = _utils_mod._bump_version("1.2.1", "patch")
        assert result == "1.2.2"

    def test_minor_bump(self):
        """Minor increments Y and resets Z to 0."""
        result = _utils_mod._bump_version("1.2.1", "minor")
        assert result == "1.3.0"

    def test_major_bump(self):
        """Major increments X and resets Y and Z to 0."""
        result = _utils_mod._bump_version("1.2.1", "major")
        assert result == "2.0.0"

    def test_zero_version_patch(self):
        """Patch works from 0.0.0."""
        result = _utils_mod._bump_version("0.0.0", "patch")
        assert result == "0.0.1"

    def test_zero_version_minor(self):
        """Minor works from 0.0.1."""
        result = _utils_mod._bump_version("0.0.1", "minor")
        assert result == "0.1.0"

    def test_nines_patch(self):
        """9.9.9 -> patch -> 9.9.10 (not 10.0.0)."""
        result = _utils_mod._bump_version("9.9.9", "patch")
        assert result == "9.9.10"

    def test_strips_whitespace(self):
        """Trailing whitespace in version string is handled."""
        result = _utils_mod._bump_version("  1.2.1  ", "patch")
        assert result == "1.2.2"

    def test_rejects_invalid_bump_type(self):
        """Invalid bump type raises ValueError."""
        with pytest.raises(ValueError, match="patch.*minor.*major"):
            _utils_mod._bump_version("1.2.1", "invalid")

    def test_rejects_bad_version_format(self):
        """Non-semver version string raises ValueError."""
        with pytest.raises(ValueError, match="semver"):
            _utils_mod._bump_version("not-a-version", "patch")

    def test_rejects_too_few_parts(self):
        """Version with too few parts raises ValueError."""
        with pytest.raises(ValueError, match="semver"):
            _utils_mod._bump_version("1.2", "patch")

    def test_rejects_non_numeric(self):
        """Version with non-numeric parts raises ValueError."""
        with pytest.raises(ValueError, match="semver"):
            _utils_mod._bump_version("a.b.c", "patch")


# ── Task 2: _prune_old_tags ─────────────────────────────────────────────

class TestPruneOldTags:
    """_prune_old_tags(keep_count=10) — tag pruning."""

    def test_no_tags_is_silent_noop(self, capsys):
        """No tags at all — silent no-op."""
        if not hasattr(_utils_mod, '_prune_old_tags'):
            pytest.skip("_prune_old_tags not implemented yet")
        # Mock subprocess to return no tags
        pass  # placeholder — real test needs git mock

    def test_under_limit_is_silent_noop(self, capsys):
        """When tag count ≤ keep_count, silent no-op."""
        pass  # placeholder

    def test_over_limit_prunes_oldest(self):
        """When >keep_count tags, deletes oldest via git push --delete."""
        pass  # placeholder


# ── Task 3: do_release ──────────────────────────────────────────────────

class TestDoRelease:
    """do_release(bump, project_dir, dry_run=False) — release automation."""

    def test_dry_run_patch_prints_expected_plan(self, panel):
        """--dry-run with patch prints the plan without making changes."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        # Mock git state: clean tree, on default branch, up to date
        panel._utils.PROJECT_DIR = "/fake/project"
        panel.DEFAULT_BRANCH = "main"
        panel._utils.DEFAULT_BRANCH = "main"

        # Mock _detect_default_branch
        with patch.object(panel._utils, '_detect_default_branch', return_value="main"):
            # Mock subprocess for git checks
            with patch('subprocess.run') as mock_run:
                # git diff-index (clean tree)
                # git fetch + git rev-list (up to date)
                mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

                # Run do_release in dry_run mode
                with patch('builtins.print') as mock_print:
                    panel.do_release("patch", "/fake/project", dry_run=True)

        # Verify print output includes expected elements
        printed = [str(call) for call in mock_print.call_args_list]
        combined = " ".join(printed)

        # Should mention the bump, dry-run, tag
        assert "dry" in combined.lower() or "would" in combined.lower(), \
            f"Dry-run output should mention dry/would: {combined}"
        assert "v" in combined, f"Should mention version tag: {combined}"

    def test_rejects_invalid_bump_type(self, panel):
        """do_release with invalid bump type exits 1."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with pytest.raises(SystemExit) as exc_info:
            panel.do_release("invalid", "/fake/project")
        assert exc_info.value.code == 1

    def test_fails_on_non_git_dir(self, panel):
        """do_release fails when project_dir is not a git repo."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            # td is not a git repo
            panel._utils.PROJECT_DIR = td
            # Mock _detect_default_branch to avoid subprocess call
            with patch.object(panel._utils, '_detect_default_branch', return_value="main"):
                with pytest.raises(SystemExit) as exc_info:
                    panel.do_release("patch", td)
                assert exc_info.value.code == 1

    def test_fails_on_missing_version_file(self, panel):
        """do_release fails when VERSION file doesn't exist."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            # Initialize git repo
            subprocess.run(["git", "init", td], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            panel._utils.PROJECT_DIR = td

            with patch.object(panel._utils, '_detect_default_branch', return_value="main"):
                with pytest.raises(SystemExit) as exc_info:
                    panel.do_release("patch", td)
                assert exc_info.value.code == 1

    def test_fails_on_dirty_tree(self, panel):
        """do_release fails when working tree is dirty."""
        if not hasattr(panel, 'do_release'):
            pytest.skip("do_release not implemented yet")

        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init", td], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            # Create VERSION file
            with open(os.path.join(td, "VERSION"), "w") as f:
                f.write("1.0.0\n")
            # Create an untracked file to make tree dirty
            with open(os.path.join(td, "dirty.txt"), "w") as f:
                f.write("dirty\n")

            panel._utils.PROJECT_DIR = td
            with patch.object(panel._utils, '_detect_default_branch', return_value="main"):
                with pytest.raises(SystemExit) as exc_info:
                    panel.do_release("patch", td)
                assert exc_info.value.code == 1


# ── Helper: run dokima as subprocess ────────────────────────────────────
"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases."""
import subprocess, os, sys, json

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")

def _run(*args):
    """Run dokima with given args and return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=10
"""Tests for F024 Task 5: --release dispatch — flag parsing and early-exit dispatch."""
import subprocess, os, sys, json, tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")

def _run(*args, cwd=None, timeout=10):
    """Run dokima with given args and return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=timeout, cwd=cwd
>>>>>>> feat/f024-auto-release--tagging-changelog-and-67c3b89d-t9
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


<<<<<<< HEAD
class TestReleaseCliIntegration:
    """Integration tests for dokima --release CLI flag."""

    def test_release_in_help_text(self):
        """--help output includes --release command."""
        rc, out, err = _run("--help")
        assert rc == 0, f"Expected exit 0, got {rc}"
        assert "--release" in out, f"--release not in help output:\n{out}"

    def test_release_in_help_json(self):
        """--help-json includes --release command."""
        import json as _json
        rc, out, err = _run("--help-json")
        assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
        data = _json.loads(out)
        commands = data.get("commands", [])
        release_cmds = [c for c in commands if c.get("name") == "--release"]
        assert release_cmds, f"--release not in commands array: {commands}"

    def test_release_without_bump_type_shows_error(self):
        """dokima --release (no bump type) exits 1."""
        rc, out, err = _run("--release")
        assert rc == 1, f"Expected exit 1, got {rc}. stdout: {out!r}"

    def test_release_with_invalid_bump_type_exits_1(self):
        """dokima --release invalid exits 1."""
        rc, out, err = _run("--release", "invalid")
        assert rc == 1, f"Expected exit 1, got {rc}. stdout: {out!r}"
"""Tests for F024 Task 4: --release flag scanning in dokima main()."""
"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases."""
import os
import sys
import subprocess
import json
import tempfile
import pytest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")


def _run(*args, cwd=None, timeout=15):
    """Run dokima with given args and return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=timeout, cwd=cwd
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


class TestReleaseFlagScanning:
    """Task 4: --release flag scanning and bump type validation."""

    def test_release_patch_exits_zero(self):
        """--release patch exits 0 (recognised, does not demand feature desc)."""
        rc, stdout, stderr = _run("--release", "patch")
        assert rc == 0, (
            f"Expected exit 0, got {rc}\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_release_minor_exits_zero(self):
        """--release minor is a valid bump type."""
        rc, stdout, stderr = _run("--release", "minor")
        assert rc == 0, (
            f"Expected exit 0, got {rc}\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_release_major_exits_zero(self):
        """--release major is a valid bump type."""
        rc, stdout, stderr = _run("--release", "major")
        assert rc == 0, (
            f"Expected exit 0, got {rc}\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_release_invalid_bump_exits_one(self):
        """--release with invalid bump type (prepatch) exits 1 with error."""
        rc, stdout, stderr = _run("--release", "prepatch")
        assert rc == 1, f"Expected exit 1, got {rc}"
        combined = stdout + stderr
        assert "Invalid release bump type" in combined, (
            f"Expected 'Invalid release bump type' in output, got: {combined}"
        )

    def test_release_invalid_bump_exits_one_foo(self):
        """--release with invalid bump type (foo) exits 1 with error."""
        rc, stdout, stderr = _run("--release", "foo")
        assert rc == 1, f"Expected exit 1, got {rc}"
        combined = stdout + stderr
        assert "Invalid release bump type" in combined, (
            f"Expected 'Invalid release bump type' in output, got: {combined}"
        )

    def test_release_invalid_bump_shows_valid_types(self):
        """--release invalid mentions valid bump types in error."""
        rc, out, err = _run("--release", "invalid")
        assert rc == 1, f"Expected exit 1, got {rc}. stdout={out!r} stderr={err!r}"
        combined = (out + err).lower()
        assert any(
            word in combined for word in ("patch", "minor", "major")
        ), f"Expected mention of valid bump types, got: out={out!r} err={err!r}"

    def test_release_missing_bump_exits_one(self):
        """--release without a bump type exits 1 with error message."""
        rc, stdout, stderr = _run("--release")
        assert rc == 1, f"Expected exit 1, got {rc}"
        combined = stdout + stderr
        assert "requires a bump type" in combined, (
            f"Expected 'requires a bump type' in output, got: {combined}"
        )

    def test_release_missing_bump_shows_usage_words(self):
        """--release without bump type mentions patch/minor/major."""
        rc, out, err = _run("--release")
        assert rc == 1, f"Expected exit 1, got {rc}. stdout={out!r} stderr={err!r}"
        combined = (out + err).lower()
        assert any(
            word in combined for word in ("bump", "patch", "minor", "major")
        ), f"Expected error about missing bump type, got: out={out!r} err={err!r}"

    def test_release_flag_does_not_break_help(self):
        """--release patch --help: --help wins (checked first)."""
        rc, stdout, stderr = _run("--help", "--release", "patch")
        assert rc == 0, f"Expected exit 0, got {rc}"
        assert "COMMANDS:" in stdout, (
            f"Expected 'COMMANDS:' in help output, got: {stdout[:200]}"
        )

    def test_release_flag_with_extra_arg_exits_zero(self):
        """--release patch with project_dir arg exits 0."""
        rc, stdout, stderr = _run("--release", "patch", "/tmp")
        assert rc == 0, (
            f"Expected exit 0, got {rc}\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )
def test_release_flag_is_recognized():
    """dokima --release patch is recognized as a flag, not a feature description.
    Currently --release is not a known flag, so it falls through as a positional
    arg and PROJECT_DIR validation fails. Once implemented, the output should
    NOT contain 'is not a valid git repository'."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run("--release", "patch", cwd=td)
        combined = out + err
        assert "is not a valid git repository" not in combined, \
            f"--release should be recognized as a flag. Got: {combined!r}"


class TestReleaseDispatch:
    """Task 5: --release dispatch — flag parsing and early-exit dispatch."""

    def test_release_flag_is_recognized(self):
        """dokima --release patch is recognized as a flag, not a feature description."""
        with tempfile.TemporaryDirectory() as td:
            rc, out, err = _run("--release", "patch", cwd=td)
            combined = out + err
            assert "is not a valid git repository" not in combined, \
                f"--release should be recognized as a flag. Got: {combined!r}"

    def test_release_flag_no_bump_shows_error(self):
        """dokima --release (no bump type) produces a bump-type-specific error."""
        with tempfile.TemporaryDirectory() as td:
            rc, out, err = _run("--release", cwd=td)
            combined = (out + err).lower()
            bump_mentioned = "patch" in combined or "minor" in combined or "major" in combined
            is_git_error = "not a valid git repository" in combined
            assert bump_mentioned and not is_git_error, \
                f"Expected bump-type error, got out={out!r} err={err!r}"

    def test_release_flag_invalid_bump_shows_error(self):
        """dokima --release invalid exits non-zero with bump type error."""
        with tempfile.TemporaryDirectory() as td:
            rc, out, err = _run("--release", "prepatch", cwd=td)
            assert rc != 0, f"Expected non-zero exit, got {rc}. out={out!r} err={err!r}"
            combined = (out + err).lower()
            assert "patch" in combined, f"Expected 'patch' in error, got out={out!r} err={err!r}"
            assert "minor" in combined, f"Expected 'minor' in error, got out={out!r} err={err!r}"
            assert "major" in combined, f"Expected 'major' in error, got out={out!r} err={err!r}"
            assert "not a valid git repository" not in combined, \
                f"Should be a bump-type error, not git-repo error. Got: {combined!r}"

    def test_release_flag_accepts_minor(self):
        """dokima --release minor is recognized and dispatched."""
        with tempfile.TemporaryDirectory() as td:
            rc, out, err = _run("--release", "minor", cwd=td)
            combined = out + err
            assert "is not a valid git repository" not in combined, \
                f"--release minor should be recognized as a flag. Got: {combined!r}"

    def test_release_flag_accepts_major(self):
        """dokima --release major is recognized and dispatched."""
        with tempfile.TemporaryDirectory() as td:
            rc, out, err = _run("--release", "major", cwd=td)
            combined = out + err
            assert "is not a valid git repository" not in combined, \
                f"--release major should be recognized as a flag. Got: {combined!r}"

    def test_release_flag_with_project_dir(self):
        """dokima --release patch with a project dir dispatches."""
        with tempfile.TemporaryDirectory() as td:
            rc, out, err = _run("--release", "patch", td, cwd=td)
            combined = out + err
            assert "Feature description required" not in combined, \
                f"--release should be a flag. Got: {combined!r}"
            assert "is not a valid git repository" not in combined, \
                f"--release should dispatch before project validation. Got: {combined!r}"


class TestDryRun:
    """Task 6: --dry-run flag with --release."""

    def test_release_patch_dry_run_exits_zero(self):
        """--release patch --dry-run exits 0 (dry run completes successfully)."""
        rc, stdout, stderr = _run("--release", "patch", "--dry-run")
        assert rc == 0, (
            f"Expected exit 0, got {rc}\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_release_patch_dry_run_prints_dry_run_header(self):
        """--release patch --dry-run prints '[DRY RUN]' indicator."""
        rc, stdout, stderr = _run("--release", "patch", "--dry-run")
        combined = stdout + stderr
        assert "[DRY RUN]" in combined, (
            f"Expected '[DRY RUN]' in output, got: {combined!r}"
        )

    def test_release_patch_dry_run_shows_planned_version(self):
        """--release patch --dry-run shows the planned new version."""
        rc, stdout, stderr = _run("--release", "patch", "--dry-run")
        combined = stdout + stderr
        assert "Would release" in combined, (
            f"Expected 'Would release' in output, got: {combined!r}"
        )

    def test_release_patch_dry_run_no_git_error(self):
        """--release patch --dry-run does NOT produce a git-repo error."""
        rc, stdout, stderr = _run("--release", "patch", "--dry-run")
        combined = stdout + stderr
        assert "is not a valid git repository" not in combined, (
            f"--dry-run should be recognized as a flag. Got: {combined!r}"
        )

    def test_release_major_dry_run_exits_zero(self):
        """--release major --dry-run exits 0."""
        rc, stdout, stderr = _run("--release", "major", "--dry-run")
        assert rc == 0, (
            f"Expected exit 0, got {rc}\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_release_minor_dry_run_exits_zero(self):
        """--release minor --dry-run exits 0."""
        rc, stdout, stderr = _run("--release", "minor", "--dry-run")
        assert rc == 0, (
            f"Expected exit 0, got {rc}\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_release_dry_run_with_project_dir(self):
        """--release patch --dry-run with project_dir arg works."""
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "-C", td, "init", "-q"], capture_output=True)
            # Create a VERSION file so dry-run can read it
            version_path = os.path.join(td, "VERSION")
            with open(version_path, "w") as f:
                f.write("1.0.0\n")
            rc, stdout, stderr = _run("--release", "patch", "--dry-run", td, cwd=td)
            assert rc == 0, (
                f"Expected exit 0, got {rc}\n"
                f"stdout: {stdout}\nstderr: {stderr}"
            )

    def test_dry_run_before_release(self):
        """--dry-run --release patch (flag order swap) is recognized."""
        rc, stdout, stderr = _run("--dry-run", "--release", "patch")
        combined = stdout + stderr
        assert "is not a valid git repository" not in combined, (
            f"--dry-run should be recognized before --release. Got: {combined!r}"
        )

<<<<<<< HEAD
def test_release_flag_with_project_dir():
    """dokima --release patch with a project dir dispatches, doesn't error on feature desc."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run("--release", "patch", td, cwd=td)
        combined = out + err
        assert "Feature description required" not in combined, \
            f"--release should be a flag. Got: {combined!r}"
        assert "is not a valid git repository" not in combined, \
            f"--release should dispatch before project validation. Got: {combined!r}"
=======
=======
def test_help_json_includes_release():
    """--help-json includes --release command in commands array."""
    rc, out, err = _run("--help-json")
    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
    data = json.loads(out)
    commands = data.get("commands", [])
    release_cmds = [c for c in commands if c.get("name") == "--release"]
    assert release_cmds, f"--release not in commands array: {commands}"
>>>>>>> feat/f024-auto-release--tagging-changelog-and-67c3b89d-t9
