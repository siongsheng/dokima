"""F031: Init interview answer collection tests.

Tests for collect_init_interview_answers() — TTY detection, non-TTY exit,
timeout, partial answers, empty input, and state persistence.
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# ── collect_init_interview_answers ──────────────────

def test_collect_interview_answers_exists():
    """collect_init_interview_answers() function exists in utils."""
    import utils
    assert hasattr(utils, 'collect_init_interview_answers'), \
        "collect_init_interview_answers function missing"
    assert callable(utils.collect_init_interview_answers)


def test_collect_interview_answers_non_tty(monkeypatch):
    """Non-TTY: saves state to JSON, returns exit code 2."""
    import utils
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: False)

    questions = [
        {"id": 1, "question": "Who are the users?",
         "assumption": "Internal team", "impact_if_wrong": "Wrong scope"}
    ]
    state = {
        "feature": "Test project",
        "project_dir": "/tmp/test",
        "round": 1,
        "max_rounds": 3,
        "confidence": "Low",
        "questions": questions,
        "answers": [],
        "original_prompt": "Prompt",
        "timestamp": "2026-07-04T12:00:00"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        tmp_path = f.name

    try:
        answers, exit_code = utils.collect_init_interview_answers(
            questions, state, path=tmp_path
        )
        assert exit_code == 2, f"Non-TTY should return exit code 2, got {exit_code}"
        assert answers == [], "Non-TTY should return empty answers"

        # Verify state was saved
        assert os.path.exists(tmp_path)
        with open(tmp_path) as f:
            saved = json.load(f)
        assert saved["feature"] == "Test project"
        assert saved["round"] == 1
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_collect_interview_answers_empty_clarifications(monkeypatch):
    """Empty/null questions list returns empty answers, exit 0 immediately."""
    import utils
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)

    answers, exit_code = utils.collect_init_interview_answers([], {})

    assert exit_code == 0
    assert answers == []


def test_collect_interview_answers_none_questions(monkeypatch):
    """None questions returns empty answers, exit 0."""
    import utils
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)

    answers, exit_code = utils.collect_init_interview_answers(None, {})

    assert exit_code == 0
    assert answers == []


def test_collect_interview_answers_timeout_returns_partial(monkeypatch):
    """select timeout during collection returns partial answers collected so far."""
    import utils
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)

    questions = [
        {"id": 1, "question": "Q1",
         "assumption": "A1", "impact_if_wrong": "Bad"},
        {"id": 2, "question": "Q2",
         "assumption": "A2", "impact_if_wrong": "Worse"}
    ]

    call_count = [0]
    def mock_select(rlist, wlist, xlist, timeout):
        call_count[0] += 1
        if call_count[0] == 1:
            return ([sys.stdin], [], [])
        # Second call: simulate timeout
        return ([], [], [])

    answers_given = ["User answer for Q1"]

    def mock_readline():
        if answers_given:
            return answers_given.pop(0) + "\n"
        return ""

    monkeypatch.setattr('select.select', mock_select)
    monkeypatch.setattr(sys.stdin, 'readline', mock_readline)

    answers, exit_code = utils.collect_init_interview_answers(questions, {})
    assert exit_code == 0
    # Should have at least the first answer
    assert len(answers) >= 1
    assert answers[0]["answer"] == "User answer for Q1"


def test_collect_interview_answers_empty_input_accepts_assumptions(monkeypatch):
    """Empty input (Enter with no text) breaks loop — accepts assumptions."""
    import utils
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)

    questions = [
        {"id": 1, "question": "Q1",
         "assumption": "A1", "impact_if_wrong": "Bad"},
        {"id": 2, "question": "Q2",
         "assumption": "A2", "impact_if_wrong": "Worse"}
    ]

    call_count = [0]
    def mock_select(rlist, wlist, xlist, timeout):
        call_count[0] += 1
        return ([sys.stdin], [], [])

    answers_given = [""]  # Empty input on first question
    def mock_readline():
        if answers_given:
            return answers_given.pop(0) + "\n"
        return ""

    monkeypatch.setattr('select.select', mock_select)
    monkeypatch.setattr(sys.stdin, 'readline', mock_readline)

    answers, exit_code = utils.collect_init_interview_answers(questions, {})
    assert exit_code == 0
    # Empty input → break, answers empty (assumptions accepted)
    assert answers == []


def test_collect_interview_answers_all_questions_answered(monkeypatch):
    """All questions answered successfully returns full answers list."""
    import utils
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)

    questions = [
        {"id": 1, "question": "Q1",
         "assumption": "A1", "impact_if_wrong": "Bad"},
        {"id": 2, "question": "Q2",
         "assumption": "A2", "impact_if_wrong": "Worse"}
    ]

    answers_given = ["Answer one", "Answer two"]
    q_idx = [0]

    def mock_select(rlist, wlist, xlist, timeout):
        return ([sys.stdin], [], [])

    def mock_readline():
        if q_idx[0] < len(answers_given):
            ans = answers_given[q_idx[0]]
            q_idx[0] += 1
            return ans + "\n"
        return ""

    monkeypatch.setattr('select.select', mock_select)
    monkeypatch.setattr(sys.stdin, 'readline', mock_readline)

    answers, exit_code = utils.collect_init_interview_answers(questions, {})
    assert exit_code == 0
    assert len(answers) == 2
    assert answers[0]["question_id"] == 1
    assert answers[0]["answer"] == "Answer one"
    assert answers[1]["question_id"] == 2
    assert answers[1]["answer"] == "Answer two"
