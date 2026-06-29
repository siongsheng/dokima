"""Tests for F021: Semantic Versioning + GitHub Releases — --version and --upgrade flags."""
import subprocess, os, sys, json

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")

def _run(*args):
    """Run dokima with given args and return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=10
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def test_version_flag_prints_version_and_exits_0():
    """dokima --version prints 'dokima vX.Y.Z' and exits 0."""
    rc, out, err = _run("--version")
    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
    assert out.startswith("dokima v"), f"Expected 'dokima v...', got: {out}"
    # Should have a semver-like version after the 'v'
    parts = out.split("v", 1)
    assert len(parts) == 2, f"Expected 'dokima v<version>', got: {out}"
    version = parts[1]
    # Should be something like X.Y.Z
    assert "." in version, f"Expected semver, got version: {version}"
