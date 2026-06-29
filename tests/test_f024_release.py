"""Tests for F024 Task 5: --release dispatch — flag parsing and early-exit dispatch."""
import subprocess, os, sys, json, tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")

def _run(*args, cwd=None, timeout=10):
    """Run dokima with given args and return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=timeout, cwd=cwd
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


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


def test_release_flag_no_bump_shows_error():
    """dokima --release (no bump type) produces a bump-type-specific error.
    Currently this falls through as feature desc '--release'. Once implemented,
    output must mention 'patch', 'minor', or 'major' as valid bump types."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run("--release", cwd=td)
        combined = (out + err).lower()
        # Must mention at least one valid bump type, and not a git-repo error
        bump_mentioned = "patch" in combined or "minor" in combined or "major" in combined
        is_git_error = "not a valid git repository" in combined
        assert bump_mentioned and not is_git_error, \
            f"Expected bump-type error, got out={out!r} err={err!r}"


def test_release_flag_invalid_bump_shows_error():
    """dokima --release invalid exits non-zero with bump type error.
    The bump type 'prepatch' should NOT be accepted."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run("--release", "prepatch", cwd=td)
        assert rc != 0, f"Expected non-zero exit, got {rc}. out={out!r} err={err!r}"
        combined = (out + err).lower()
        # Must mention valid bump types as guidance
        assert "patch" in combined, f"Expected 'patch' in error, got out={out!r} err={err!r}"
        assert "minor" in combined, f"Expected 'minor' in error, got out={out!r} err={err!r}"
        assert "major" in combined, f"Expected 'major' in error, got out={out!r} err={err!r}"
        # Must NOT be a git-repo error
        assert "not a valid git repository" not in combined, \
            f"Should be a bump-type error, not git-repo error. Got: {combined!r}"


def test_release_flag_accepts_minor():
    """dokima --release minor is recognized and dispatched (not treated as feature desc)."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run("--release", "minor", cwd=td)
        combined = out + err
        assert "is not a valid git repository" not in combined, \
            f"--release minor should be recognized as a flag. Got: {combined!r}"


def test_release_flag_accepts_major():
    """dokima --release major is recognized and dispatched (not treated as feature desc)."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run("--release", "major", cwd=td)
        combined = out + err
        assert "is not a valid git repository" not in combined, \
            f"--release major should be recognized as a flag. Got: {combined!r}"


def test_release_flag_with_project_dir():
    """dokima --release patch with a project dir dispatches, doesn't error on feature desc."""
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run("--release", "patch", td, cwd=td)
        combined = out + err
        assert "Feature description required" not in combined, \
            f"--release should be a flag. Got: {combined!r}"
        assert "is not a valid git repository" not in combined, \
            f"--release should dispatch before project validation. Got: {combined!r}"
