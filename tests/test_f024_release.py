"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases.

Task 4: --release flag scanning — validation of bump type arg.
"""
import subprocess, os, sys

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")


def _run(*args):
    """Run dokima with given args and return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=10,
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def test_release_invalid_bump_exits_1():
    """dokima --release invalid exits 1 with error about bump type."""
    rc, out, err = _run("--release", "invalid")
    assert rc == 1, f"Expected exit 1, got {rc}. stdout={out!r} stderr={err!r}"
    combined = (out + err).lower()
    assert any(
        word in combined for word in ("patch", "minor", "major")
    ), f"Expected mention of valid bump types, got: out={out!r} err={err!r}"


def test_release_missing_bump_exits_1():
    """dokima --release without a bump type exits 1."""
    rc, out, err = _run("--release")
    assert rc == 1, f"Expected exit 1, got {rc}. stdout={out!r} stderr={err!r}"
    combined = (out + err).lower()
    assert any(
        word in combined for word in ("bump", "patch", "minor", "major", "release")
    ), f"Expected error about missing bump type, got: out={out!r} err={err!r}"
