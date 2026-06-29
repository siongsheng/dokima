"""Tests for F024: Auto-Release — Tagging, Changelog, and GitHub Releases."""
import subprocess, os, sys, json

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")

def _run(*args):
    """Run dokima with given args and return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=10
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def test_help_json_includes_release():
    """--help-json includes --release command in commands array."""
    rc, out, err = _run("--help-json")
    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
    data = json.loads(out)
    commands = data.get("commands", [])
    release_cmds = [c for c in commands if c.get("name") == "--release"]
    assert release_cmds, f"--release not in commands array: {commands}"
