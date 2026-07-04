"""F031 — Unit tests for interview detection helpers added to utils.py."""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# ── INTERVIEW_SAVE_PATH constant ──────────────

def test_interview_save_path_constant_exists():
    """INTERVIEW_SAVE_PATH constant is defined."""
    import utils
    assert hasattr(utils, 'INTERVIEW_SAVE_PATH')
    assert isinstance(utils.INTERVIEW_SAVE_PATH, str)
    assert 'dokima-init-interview' in utils.INTERVIEW_SAVE_PATH


# ── has_init_interview_triggers ────────────────

def test_has_init_interview_triggers_clarification_block():
    """Detects CLARIFICATION N: blocks in output."""
    import utils
    text = "DECISION: INTERVIEW MODE\n\nCLARIFICATION 1: Who are the primary users?"
    assert utils.has_init_interview_triggers(text) is True


def test_has_init_interview_triggers_interview_mode_only():
    """Detects INTERVIEW MODE declaration."""
    import utils
    text = "DECISION: INTERVIEW MODE\n\nI need more information before proceeding."
    assert utils.has_init_interview_triggers(text) is True


def test_has_init_interview_triggers_no_triggers():
    """Returns False when no triggers present."""
    import utils
    text = "DECISION: PROCEED\n\n## 1. Executive Summary\nThis is a full spec."
    assert utils.has_init_interview_triggers(text) is False


def test_has_init_interview_triggers_empty():
    """Returns False for empty string."""
    import utils
    assert utils.has_init_interview_triggers("") is False


def test_has_init_interview_triggers_none():
    """Returns False for None input."""
    import utils
    assert utils.has_init_interview_triggers(None) is False


def test_has_init_interview_triggers_task_headers_false_positive():
    """Returns False when CLARIFICATION appears inside task descriptions (false positive guard)."""
    import utils
    text = """## 3. Decision Table
DECISION: INTERVIEW MODE is not needed here.

### Task 1: Do thing
Files: x.py

CLARIFICATION is a word used in the description"""
    assert utils.has_init_interview_triggers(text) is False


# ── save_init_interview_state ─────────────────

def test_save_init_interview_state_writes_json():
    """Writes interview state to JSON file and returns the path."""
    import utils
    td = tempfile.mkdtemp()
    original_save_path = getattr(utils, 'INTERVIEW_SAVE_PATH', '/tmp/dokima-init-interview.json')
    try:
        test_path = os.path.join(td, 'interview.json')
        utils.INTERVIEW_SAVE_PATH = test_path

        result = utils.save_init_interview_state(
            "trading dashboard",
            "/tmp/test-project",
            ["CLARIFICATION 1: Who are the users?"],
            "You are the strategist..."
        )
        assert result == test_path
        assert os.path.exists(test_path)

        with open(test_path) as f:
            data = json.load(f)
        assert data["feature"] == "trading dashboard"
        assert data["project_dir"] == "/tmp/test-project"
        assert len(data["questions"]) == 1
        assert data["prompt"] == "You are the strategist..."
    finally:
        utils.INTERVIEW_SAVE_PATH = original_save_path
        import shutil
        shutil.rmtree(td, ignore_errors=True)


def test_save_init_interview_state_chmod_600():
    """Saved file has restrictive permissions (0o600)."""
    import utils
    td = tempfile.mkdtemp()
    original_save_path = getattr(utils, 'INTERVIEW_SAVE_PATH', '/tmp/dokima-init-interview.json')
    try:
        test_path = os.path.join(td, 'interview.json')
        utils.INTERVIEW_SAVE_PATH = test_path

        utils.save_init_interview_state(
            "test feature",
            "/tmp/test",
            ["Q1"],
            "prompt"
        )
        stat = os.stat(test_path)
        # Permission should be 0o600 (owner rw only)
        assert stat.st_mode & 0o777 == 0o600
    finally:
        utils.INTERVIEW_SAVE_PATH = original_save_path
        import shutil
        shutil.rmtree(td, ignore_errors=True)


def test_save_init_interview_state_empty_questions():
    """Handles empty questions list gracefully."""
    import utils
    td = tempfile.mkdtemp()
    original_save_path = getattr(utils, 'INTERVIEW_SAVE_PATH', '/tmp/dokima-init-interview.json')
    try:
        test_path = os.path.join(td, 'interview.json')
        utils.INTERVIEW_SAVE_PATH = test_path

        result = utils.save_init_interview_state(
            "test",
            "/tmp/test",
            [],
            "prompt"
        )
        assert result == test_path
        with open(test_path) as f:
            data = json.load(f)
        assert data["questions"] == []
    finally:
        utils.INTERVIEW_SAVE_PATH = original_save_path
        import shutil
        shutil.rmtree(td, ignore_errors=True)
