"""F031: Back-and-forth interview mode — utils helpers.

Tests for INTERVIEW_SAVE_PATH, load_init_interview_state(),
save_init_interview_state(), and has_init_interview_triggers().
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# ── INTERVIEW_SAVE_PATH ──────────────────────────────

def test_interview_save_path_constant_exists():
    """F031: INTERVIEW_SAVE_PATH constant is defined and points to init interview JSON."""
    import utils
    assert hasattr(utils, 'INTERVIEW_SAVE_PATH'), "INTERVIEW_SAVE_PATH constant missing"
    assert utils.INTERVIEW_SAVE_PATH == "/tmp/dokima-init-interview.json"


# ── load_init_interview_state ─────────────────────────

def test_load_init_interview_state_from_file():
    """load_init_interview_state() reads valid JSON and returns the dict."""
    import utils
    state = {
        "feature": "Test project",
        "project_dir": "/tmp/test",
        "round": 1,
        "max_rounds": 3,
        "confidence": "Low",
        "questions": [
            {"id": 1, "question": "Who are the users?",
             "assumption": "Internal team", "impact_if_wrong": "Wrong scope"}
        ],
        "answers": [],
        "original_prompt": "Test prompt",
        "timestamp": "2026-07-04T12:00:00"
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(state, f)
        tmp_path = f.name
    try:
        result = utils.load_init_interview_state(tmp_path)
        assert result is not None
        assert result["feature"] == "Test project"
        assert result["round"] == 1
        assert result["confidence"] == "Low"
        assert len(result["questions"]) == 1
    finally:
        os.unlink(tmp_path)


def test_load_init_interview_state_default_path():
    """load_init_interview_state() uses INTERVIEW_SAVE_PATH when no path given."""
    import utils
    # Verify it's callable with no args — will return None since /tmp file
    # doesn't exist in test
    result = utils.load_init_interview_state()
    # Default path likely doesn't exist in test env → None
    assert result is None


def test_load_init_interview_state_missing_file():
    """load_init_interview_state() returns None when file doesn't exist."""
    import utils
    result = utils.load_init_interview_state("/nonexistent/path/interview.json")
    assert result is None


def test_load_init_interview_state_corrupted_json():
    """load_init_interview_state() returns None for corrupted/invalid JSON."""
    import utils
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("this is not valid json {{{")
        tmp_path = f.name
    try:
        result = utils.load_init_interview_state(tmp_path)
        assert result is None
    finally:
        os.unlink(tmp_path)


def test_load_init_interview_state_empty_file():
    """load_init_interview_state() returns None for empty file."""
    import utils
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("")
        tmp_path = f.name
    try:
        result = utils.load_init_interview_state(tmp_path)
        assert result is None
    finally:
        os.unlink(tmp_path)


# ── save_init_interview_state ────────────────────────

def test_save_init_interview_state_exists():
    """save_init_interview_state() function exists in utils."""
    import utils
    assert hasattr(utils, 'save_init_interview_state'), \
        "save_init_interview_state function missing"
    assert callable(utils.save_init_interview_state)


def test_save_init_interview_state_roundtrip():
    """save_init_interview_state() + load_init_interview_state() roundtrip."""
    import utils
    state = {
        "feature": "Roundtrip test",
        "project_dir": "/tmp/rt",
        "round": 2,
        "max_rounds": 3,
        "confidence": "Medium",
        "questions": [
            {"id": 1, "question": "Q1", "assumption": "A1", "impact_if_wrong": "Bad"}
        ],
        "answers": [{"question_id": 1, "answer": "Test answer"}],
        "original_prompt": "Prompt",
        "timestamp": "2026-07-04T12:00:00"
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        tmp_path = f.name
    try:
        utils.save_init_interview_state(
            feature="Roundtrip test",
            project_dir="/tmp/rt",
            round_num=2,
            confidence="Medium",
            questions=state["questions"],
            answers=state["answers"],
            original_prompt="Prompt",
            path=tmp_path
        )
        loaded = utils.load_init_interview_state(tmp_path)
        assert loaded is not None
        assert loaded["feature"] == "Roundtrip test"
        assert loaded["round"] == 2
        assert loaded["confidence"] == "Medium"
        assert len(loaded["answers"]) == 1
        assert loaded["answers"][0]["answer"] == "Test answer"
    finally:
        os.unlink(tmp_path)


def test_save_init_interview_state_default_answers():
    """save_init_interview_state() defaults answers to empty list."""
    import utils
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        tmp_path = f.name
    try:
        utils.save_init_interview_state(
            feature="Test",
            project_dir="/tmp/t",
            round_num=1,
            confidence="Low",
            questions=[],
            original_prompt="P",
            path=tmp_path
        )
        loaded = utils.load_init_interview_state(tmp_path)
        assert loaded is not None
        assert loaded["answers"] == []
    finally:
        os.unlink(tmp_path)


# ── has_init_interview_triggers ──────────────────────

def test_has_init_interview_triggers_exists():
    """has_init_interview_triggers() function exists in utils."""
    import utils
    assert hasattr(utils, 'has_init_interview_triggers'), \
        "has_init_interview_triggers function missing"
    assert callable(utils.has_init_interview_triggers)


def test_has_init_interview_triggers_clarification_block():
    """has_init_interview_triggers() detects CLARIFICATION 1: blocks."""
    import utils
    text = "Here is my analysis.\n\nCLARIFICATION 1: Who are the users?\nAssumption: Internal team\nImpact if wrong: Wrong scope"
    assert utils.has_init_interview_triggers(text) is True


def test_has_init_interview_triggers_interview_mode_only():
    """has_init_interview_triggers() detects INTERVIEW MODE string."""
    import utils
    text = "DECISION: INTERVIEW MODE\n\nCLARIFICATION 1: Who are users?"
    assert utils.has_init_interview_triggers(text) is True


def test_has_init_interview_triggers_no_triggers():
    """has_init_interview_triggers() returns False for normal spec output."""
    import utils
    text = "# Feature Spec\n\n## Impact\n\nThis is a normal spec document.\n\n### Task 1: Do something"
    assert utils.has_init_interview_triggers(text) is False


def test_has_init_interview_triggers_empty():
    """has_init_interview_triggers() returns False for empty input."""
    import utils
    assert utils.has_init_interview_triggers("") is False


def test_has_init_interview_triggers_false_positive_prose():
    """has_init_interview_triggers() does NOT trigger on prose mentioning CLARIFICATION."""
    import utils
    text = "# Test\n\nINTERVIEW MODE is a feature we should build. CLARIFICATION is key."
    # This has the words but not in the structured format — should return False
    # because the regex requires line-start CLARIFICATION with digits
    assert utils.has_init_interview_triggers(text) is False
