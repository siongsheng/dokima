"""RED tests for Task 2 — HELP_TEXT uses subcommand syntax (will FAIL until HELP_TEXT updated)."""
import subprocess
import os
import sys

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")


def _run(*args):
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=10,
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def test_help_shows_subcommand_syntax():
    """--help uses subcommand syntax: 'dokima add' not 'dokima --add'."""
    rc, out, err = _run("--help")
    assert rc == 0
    assert "dokima add" in out, f"Expected 'dokima add' in help, got:\n{out[:500]}"
    assert "dokima --add" not in out, f"Old --add syntax should NOT appear:\n{out[:500]}"


def test_help_shows_next_subcommand():
    """--help shows 'dokima next' not 'dokima --next'."""
    rc, out, err = _run("--help")
    assert rc == 0
    assert "dokima next" in out
    assert "dokima --next" not in out


def test_help_shows_fix_subcommand():
    """--help shows 'dokima fix' not 'dokima --fix'."""
    rc, out, err = _run("--help")
    assert rc == 0
    assert "dokima fix" in out
    assert "dokima --fix" not in out


def test_help_shows_status_subcommand():
    """--help shows 'dokima status' not 'dokima --status'."""
    rc, out, err = _run("--help")
    assert rc == 0
    assert "dokima status" in out
    assert "dokima --status" not in out
