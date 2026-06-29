"""Tests for F023: Pipeline Self-Healing.

Lock-age auto-cleanup, truncation detection, fix-hash cycle detection.
"""
import os
import sys
import time
import fcntl
import pytest
from unittest.mock import patch, Mock


# ── Task 1+5: Lock-age auto-cleanup in acquire_lock ─────────────────────

def test_lock_age_old_lock_with_live_pid_removed(panel, tmpdir_path, monkeypatch):
    """Lock file >12h old with live PID + owner verified → removed, retried, acquired.

    Simulates SIGKILL + PID recycling: a stale lock file whose PID now
    belongs to a different dokima process. The age check catches this.
    """
    panel.PROJECT_DIR = tmpdir_path
    lp = panel._lock_path()

    # Write our PID to the lock file
    with open(lp, "w") as f:
        f.write(f"{os.getpid()}\n")

    # Set mtime to 13 hours ago (exceeds 12h default threshold)
    old_mtime = time.time() - (13 * 3600)
    os.utime(lp, (old_mtime, old_mtime))

    # Mock: fcntl.flock raises on first call (simulating contention),
    # then succeeds on retry (after lock file removed + recreated)
    call_count = [0]

    def mock_flock(fd, op):
        call_count[0] += 1
        if call_count[0] == 1:
            # First attempt: restore PID to file (was truncated by open("w"))
            # and raise contention error
            fd.write(f"{os.getpid()}\n")
            fd.flush()
            raise BlockingIOError(11, "Resource temporarily unavailable")
        # Subsequent calls succeed (after lock removal + recreation)
        return

    # Mock _check_pid and _verify_pid_owner to return True
    # (simulating PID recycled to another dokima process)
    with patch.object(panel, 'fcntl') as mock_fcntl:
        mock_fcntl.flock = mock_flock
        mock_fcntl.LOCK_EX = fcntl.LOCK_EX
        mock_fcntl.LOCK_NB = fcntl.LOCK_NB

        held, fd = panel.acquire_lock()
        assert held is True
        assert fd is not None
        fd.close()

    try:
        os.remove(lp)
    except OSError:
        pass


def test_lock_age_fresh_lock_with_live_pid_exits(panel, tmpdir_path, monkeypatch):
    """Lock file <12h old with live PID → exits (preserved, not removed)."""
    panel.PROJECT_DIR = tmpdir_path
    lp = panel._lock_path()

    # Write our PID to the lock file
    with open(lp, "w") as f:
        f.write(f"{os.getpid()}\n")

    # Fresh mtime (now)
    os.utime(lp, (time.time(), time.time()))

    # Mock fcntl.flock to raise (simulating contention)
    call_count = [0]

    def mock_flock(fd, op):
        call_count[0] += 1
        if call_count[0] == 1:
            # Restore PID to file (was truncated by open("w"))
            fd.write(f"{os.getpid()}\n")
            fd.flush()
            raise BlockingIOError(11, "Resource temporarily unavailable")
        return

    # Intercept sys.exit
    old_exit = panel.sys.exit
    exit_codes = []
    def fake_exit(code=0):
        exit_codes.append(code)
        raise SystemExit(code)
    panel.sys.exit = fake_exit

    try:
        with patch.object(panel, 'fcntl') as mock_fcntl:
            mock_fcntl.flock = mock_flock
            mock_fcntl.LOCK_EX = fcntl.LOCK_EX
            mock_fcntl.LOCK_NB = fcntl.LOCK_NB

            try:
                panel.acquire_lock()
            except SystemExit:
                pass
    finally:
        panel.sys.exit = old_exit

    try:
        os.remove(lp)
    except OSError:
        pass

    assert len(exit_codes) > 0
    assert exit_codes[0] == 1


def test_lock_age_env_var_threshold(panel, tmpdir_path, monkeypatch):
    """PANEL_LOCK_MAX_AGE_SECS env var controls the threshold."""
    panel.PROJECT_DIR = tmpdir_path
    lp = panel._lock_path()

    # Set threshold to 2 seconds via env var
    monkeypatch.setenv("PANEL_LOCK_MAX_AGE_SECS", "2")

    # Write our PID to the lock file
    with open(lp, "w") as f:
        f.write(f"{os.getpid()}\n")

    # Set mtime to 3 seconds ago (exceeds 2s threshold)
    old_mtime = time.time() - 3
    os.utime(lp, (old_mtime, old_mtime))

    call_count = [0]

    def mock_flock(fd, op):
        call_count[0] += 1
        if call_count[0] == 1:
            # Restore PID to file (was truncated by open("w"))
            fd.write(f"{os.getpid()}\n")
            fd.flush()
            raise BlockingIOError(11, "Resource temporarily unavailable")
        return

    with patch.object(panel, 'fcntl') as mock_fcntl:
        mock_fcntl.flock = mock_flock
        mock_fcntl.LOCK_EX = fcntl.LOCK_EX
        mock_fcntl.LOCK_NB = fcntl.LOCK_NB

        held, fd = panel.acquire_lock()
        assert held is True
        fd.close()

    try:
        os.remove(lp)
    except OSError:
        pass


def test_lock_age_dead_pid_still_cleaned(panel, tmpdir_path, monkeypatch):
    """Lock file with dead PID is cleaned up regardless of age (existing behavior)."""
    panel.PROJECT_DIR = tmpdir_path
    lp = panel._lock_path()

    # Write dead PID to the lock file
    with open(lp, "w") as f:
        f.write("99999999\n")

    # Recent mtime
    os.utime(lp, (time.time(), time.time()))

    call_count = [0]

    def mock_flock(fd, op):
        call_count[0] += 1
        if call_count[0] == 1:
            # Restore PID to file (was truncated by open("w"))
            fd.write("99999999\n")
            fd.flush()
            raise BlockingIOError(11, "Resource temporarily unavailable")
        return

    with patch.object(panel, 'fcntl') as mock_fcntl:
        mock_fcntl.flock = mock_flock
        mock_fcntl.LOCK_EX = fcntl.LOCK_EX
        mock_fcntl.LOCK_NB = fcntl.LOCK_NB

        held, fd = panel.acquire_lock()
        assert held is True
        fd.close()

    try:
        os.remove(lp)
    except OSError:
        pass


# ── Task 2+6: Truncation detection ────────────────────────────────────

def test_detect_truncation_no_report_marker_mid_sentence(panel):
    """Output missing Report: line + ends mid-sentence → truncated."""
    output = "I have implemented the feature and added tests.\nThe code is ready"
    assert panel._detect_truncation(output) is True


def test_detect_truncation_has_report_line(panel):
    """Output with Report: line → not truncated."""
    output = "Implemented feature\n\nReport: all tests pass, build clean\n\nDone."
    assert panel._detect_truncation(output) is False


def test_detect_truncation_ends_with_terminal_punctuation(panel):
    """Output ends with . ! or ? → not truncated (even without Report: line)."""
    output = "The feature is complete and all tests pass."
    assert panel._detect_truncation(output) is False


def test_detect_truncation_empty_output(panel):
    """Empty output → truncated (coder crashed)."""
    assert panel._detect_truncation("") is True


def test_detect_truncation_none_input(panel):
    """None input → not truncated (safety)."""
    assert panel._detect_truncation(None) is False


def test_detect_truncation_short_without_report(panel):
    """Short output (< 200 chars) without Report: line → truncated."""
    output = "Just a few words"
    assert panel._detect_truncation(output) is True


def test_detect_truncation_whitespace_only(panel):
    """Whitespace-only output → truncated."""
    assert panel._detect_truncation("   \n  \n  ") is True


def test_detect_truncation_ends_with_exclamation(panel):
    """Output ending with ! → not truncated."""
    output = "Everything is working!"
    assert panel._detect_truncation(output) is False


def test_detect_truncation_ends_with_question(panel):
    """Output ending with ? → not truncated."""
    output = "Is everything working?"
    assert panel._detect_truncation(output) is False
