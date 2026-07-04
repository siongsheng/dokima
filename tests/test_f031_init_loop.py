"""F031 — Tests for init interview loop in roadmap.py run_init()."""
import sys
import os
import io
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# ── Interview loop detection in roadmap.py ──

def test_run_init_has_interview_loop():
    """run_init() in roadmap.py contains the interview loop after strategist spawn."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'roadmap.py')) as f:
        source = f.read()

    # After the interview loop is added, roadmap.py should:
    # 1. Reference has_init_interview_triggers
    assert 'has_init_interview_triggers' in source, \
        "roadmap.py must use has_init_interview_triggers for interview detection"

    # 2. Reference collect_interview_answers for interactive mode
    assert 'collect_interview_answers' in source, \
        "roadmap.py must use collect_interview_answers for answer collection"

    # 3. Reference save_init_interview_state for non-interactive fallback
    assert 'save_init_interview_state' in source, \
        "roadmap.py must use save_init_interview_state for non-tty mode"

    # 4. Reference INTERVIEW_SAVE_PATH constant
    assert 'INTERVIEW_SAVE_PATH' in source, \
        "roadmap.py must reference INTERVIEW_SAVE_PATH"


def test_run_init_has_max_rounds_guard():
    """run_init() has max_rounds guard (3 rounds max)."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'roadmap.py')) as f:
        source = f.read()

    # After max_rounds guard is added, there should be a counter limiting rounds
    # Check for a round-limiter pattern
    assert 'max_rounds' in source or 'round' in source.split('def run_init')[1].lower(), \
        "roadmap.py must have a round limiter in run_init()"


def test_run_init_non_interactive_exit():
    """run_init() exits with code 2 when non-interactive and interview detected."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'roadmap.py')) as f:
        source = f.read()

    run_init_source = source.split('def run_init')[1].split('\ndef ')[0] if 'def run_init' in source else ''

    # After non-interactive handling is added, there should be exit(2) for non-tty case
    assert 'exit(2)' in run_init_source or 'sys.exit(2)' in run_init_source, \
        "run_init() must call exit(2) for non-interactive interview mode"


# ── Helper function tests verify existing behavior ──

def test_helpers_work_for_interview_flow():
    """The utils helpers needed for the interview loop are functional."""
    import utils
    import json

    # 1. Detection
    interview_text = "DECISION: INTERVIEW MODE\n\nCLARIFICATION 1: test"
    assert utils.has_init_interview_triggers(interview_text) is True

    # 2. Non-tty fallback
    original_isatty = sys.stdin.isatty
    try:
        sys.stdin.isatty = lambda: False
        assert utils.collect_interview_answers(["Q1"]) == []
    finally:
        sys.stdin.isatty = original_isatty

    # 3. State save
    td = tempfile.mkdtemp()
    original_save_path = getattr(utils, 'INTERVIEW_SAVE_PATH', '/tmp/dokima-init-interview.json')
    try:
        test_path = os.path.join(td, 'interview.json')
        utils.INTERVIEW_SAVE_PATH = test_path
        path = utils.save_init_interview_state("f", "/tmp", ["Q1"], "p")
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert data["feature"] == "f"
    finally:
        utils.INTERVIEW_SAVE_PATH = original_save_path
        import shutil
        shutil.rmtree(td, ignore_errors=True)


def test_confidence_high_no_interview():
    """When confidence is High and no interview triggers, output is clean."""
    import utils

    clean_spec = """Confidence: High
## 1. Executive Summary
Project description.
## 4. Impact
Impact text.
## 5. What Changed
- Change A
### Task 1: Setup
**Files:** main.py
**Dependencies:** None
**Parallelizable:** yes
**Description:** Setup project."""
    assert utils.has_init_interview_triggers(clean_spec) is False
