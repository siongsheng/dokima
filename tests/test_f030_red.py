"""RED tests for Task 1 — subcommand dispatch (will FAIL until argparse implemented)."""
import subprocess
import os
import sys

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")


def test_version_subcommand_prints_version():
    """dokima version prints 'dokima vX.Y.Z' and exits 0."""
    p = subprocess.run(
        [sys.executable, SCRIPT, "version"],
        capture_output=True, text=True, timeout=10,
    )
    assert p.returncode == 0, f"Expected exit 0, got {p.returncode}. stderr: {p.stderr}"
    assert p.stdout.strip().startswith("dokima v"), f"Expected 'dokima v...', got: {p.stdout.strip()!r}"


def test_version_subcommand_help_json_first_wins():
    """dokima --help-json version: --help-json wins (top-level flag)."""
    import json
    p = subprocess.run(
        [sys.executable, SCRIPT, "--help-json", "version"],
        capture_output=True, text=True, timeout=10,
    )
    assert p.returncode == 0, f"Expected exit 0, got {p.returncode}"
    data = json.loads(p.stdout)
    assert data["tool"] == "dokima"
