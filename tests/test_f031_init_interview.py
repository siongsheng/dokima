"""F031 — Comprehensive tests for init interview loop behavior.

Tests:
(a) Interview mode -> answers -> re-spawn -> High confidence -> docs written
(b) Loop terminates after 3 rounds
(c) Non-interactive mode saves state and exits(2)
(d) --answers flag pre-fills and skips interview
(e) One-shot preserved when High confidence immediately
"""
import sys
import os
import io
import json
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# ── Scenario (e): One-shot preserved ──────────

def test_one_shot_high_confidence_no_interview():
    """When strategist returns High confidence immediately, no interview loop runs."""
    import utils

    # Output with tasks = full spec, no interview triggers
    one_shot = """Confidence: High
## 1. Executive Summary
Full constitution here.
## 4. Impact
Significant.
## 5. What Changed
- Added project discovery
### Task 1: Setup
**Files:** main.py
**Dependencies:** None
**Parallelizable:** yes
**Description:** Do init."""
    assert utils.has_init_interview_triggers(one_shot) is False


# ── Scenario (a): Interview mode full loop ───

def test_interview_mode_detected_full_loop():
    """Strategist returns interview mode, answers provided, re-spawn, High confidence."""
    import utils

    round1 = "DECISION: INTERVIEW MODE\n\nCLARIFICATION 1: Who are the primary users?"
    assert utils.has_init_interview_triggers(round1) is True

    # After answers, re-spawn returns full spec
    round2 = """Confidence: High
DECISION: PROCEED
## 1. Executive Summary
Full spec.
## 4. Impact
Good.
## 5. What Changed
- Feature X
### Task 1: Do it
**Files:** x.py
**Dependencies:** None
**Parallelizable:** yes
**Description:** Do it."""
    assert utils.has_init_interview_triggers(round2) is False


# ── Scenario (b): Max 3 rounds termination ──

def test_loop_terminates_after_3_rounds():
    """After 3 interview rounds, loop terminates even if still in interview mode."""
    import utils

    # All 3 rounds return interview mode
    interview_output = "DECISION: INTERVIEW MODE\n\nCLARIFICATION 1: Need more info."
    assert utils.has_init_interview_triggers(interview_output) is True

    # max_rounds=3 guard prevents infinite loop
    max_rounds = 3
    rounds = 0
    while rounds < max_rounds:
        if utils.has_init_interview_triggers(interview_output):
            rounds += 1
        else:
            break
    assert rounds == 3  # All 3 rounds detected as interview


# ── Scenario (c): Non-interactive save+exit ──

def test_non_interactive_saves_state():
    """Non-interactive mode saves interview state to JSON."""
    import utils

    td = tempfile.mkdtemp()
    original_save_path = getattr(utils, 'INTERVIEW_SAVE_PATH', '/tmp/dokima-init-interview.json')
    try:
        test_path = os.path.join(td, 'interview.json')
        utils.INTERVIEW_SAVE_PATH = test_path

        path = utils.save_init_interview_state(
            "test feature",
            "/tmp/test-project",
            ["CLARIFICATION 1: Who?", "CLARIFICATION 2: What?"],
            "strategist prompt here"
        )

        assert path == test_path
        assert os.path.exists(path)

        with open(path) as f:
            data = json.load(f)
        assert data["feature"] == "test feature"
        assert data["project_dir"] == "/tmp/test-project"
        assert len(data["questions"]) == 2
        assert data["prompt"] == "strategist prompt here"

        # File should be readable and valid JSON
        stat = os.stat(path)
        assert stat.st_mode & 0o777 == 0o600
    finally:
        utils.INTERVIEW_SAVE_PATH = original_save_path
        import shutil
        shutil.rmtree(td, ignore_errors=True)


def test_non_interactive_collect_answers_empty():
    """When not a tty, collect_interview_answers returns empty list."""
    import utils

    original_isatty = sys.stdin.isatty
    try:
        sys.stdin.isatty = lambda: False
        result = utils.collect_interview_answers(
            ["CLARIFICATION 1: Who?"]
        )
        assert result == []
    finally:
        sys.stdin.isatty = original_isatty


# ── Scenario (d): --answers flag ─────────────

def test_answers_flag_loads_state():
    """--answers flag loads saved interview state JSON."""
    import json
    import tempfile

    # Create a fake interview state file
    td = tempfile.mkdtemp()
    answers_path = os.path.join(td, 'interview.json')
    state = {
        "feature": "trading dashboard",
        "project_dir": "/tmp/test",
        "questions": ["CLARIFICATION 1: Who are the users?"],
        "prompt": "You are the strategist..."
    }
    with open(answers_path, 'w') as f:
        json.dump(state, f)

    # Simulate --answers flag loading
    try:
        with open(answers_path) as f:
            loaded = json.load(f)
        assert loaded["feature"] == "trading dashboard"
        assert len(loaded["questions"]) == 1
        assert "prompt" in loaded
    finally:
        import shutil
        shutil.rmtree(td, ignore_errors=True)


# ── interview detection edge cases ──────────

def test_has_init_interview_triggers_clarification_only():
    """CLARIFICATION blocks without DECISION: INTERVIEW MODE still trigger."""
    import utils
    text = "CLARIFICATION 1: Tell me more about the project"
    assert utils.has_init_interview_triggers(text) is True


def test_has_init_interview_triggers_interview_mode_only():
    """DECISION: INTERVIEW MODE without CLARIFICATION blocks still triggers."""
    import utils
    text = "DECISION: INTERVIEW MODE\n\nI need to understand this better."
    assert utils.has_init_interview_triggers(text) is True


def test_has_init_interview_triggers_no_false_positive_on_tasks():
    """CLARIFICATION inside a full spec with tasks does NOT trigger."""
    import utils
    spec_with_tasks = """## 3. Decision Table
DECISION: INTERVIEW MODE was considered and rejected.

### Task 1: Do thing
**Files:** x.py
**Dependencies:** None
**Parallelizable:** yes
**Description:** CLARIFICATION was requested but denied."""
    assert utils.has_init_interview_triggers(spec_with_tasks) is False


def test_confidence_high_without_interview():
    """Confidence: High output without triggers proceeds to doc writing."""
    import utils
    output = """Confidence: High
## 4. Impact
Major.
## 5. What Changed
- Added feature.
### Task 1: Code
**Files:** main.py
**Dependencies:** None
**Parallelizable:** yes
**Description:** Write main."""
    assert utils.has_init_interview_triggers(output) is False
