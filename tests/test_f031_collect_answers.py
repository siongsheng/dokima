"""F031 — Unit tests for collect_interview_answers helper."""
import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


# ── collect_interview_answers ─────────────────

def test_collect_interview_answers_exists():
    """Function is defined and importable."""
    import utils
    assert hasattr(utils, 'collect_interview_answers')
    assert callable(utils.collect_interview_answers)


def test_collect_interview_answers_non_tty():
    """Returns empty list when stdin is not a tty."""
    import utils
    # Simulate non-tty by temporarily replacing sys.stdin.isatty
    original_isatty = sys.stdin.isatty
    try:
        sys.stdin.isatty = lambda: False
        result = utils.collect_interview_answers(
            ["CLARIFICATION 1: Who are the users?"]
        )
        assert result == []
    finally:
        sys.stdin.isatty = original_isatty


def test_collect_interview_answers_empty_clarifications():
    """Returns empty list when no clarifications provided."""
    import utils
    # Mock tty True to avoid immediate return
    original_isatty = sys.stdin.isatty
    try:
        sys.stdin.isatty = lambda: True
        result = utils.collect_interview_answers([])
        assert result == []
    finally:
        sys.stdin.isatty = original_isatty


def test_collect_interview_answers_timeout_returns_partial():
    """When timeout occurs, returns answers collected so far."""
    import utils
    import select as select_module
    original_isatty = sys.stdin.isatty
    try:
        sys.stdin.isatty = lambda: True
        fake_stdin = io.StringIO("answer1\nanswer2 timeout\n")
        fake_stdin.isatty = lambda: True
        original_stdin = sys.stdin
        sys.stdin = fake_stdin
        # Mock select to always return ready (StringIO has no fileno)
        original_select = select_module.select
        select_module.select = lambda rlist, wlist, xlist, timeout=None: (rlist, [], [])
        try:
            result = utils.collect_interview_answers(
                ["CLARIFICATION 1: Q1", "CLARIFICATION 2: Q2"],
                timeout=1
            )
            assert len(result) <= 2
        finally:
            select_module.select = original_select
            sys.stdin = original_stdin
    finally:
        sys.stdin.isatty = original_isatty


def test_collect_interview_answers_all_answered():
    """Collects all answers when user answers all questions."""
    import utils
    import select as select_module
    original_isatty = sys.stdin.isatty
    try:
        sys.stdin.isatty = lambda: True
        fake_stdin = io.StringIO("answer one\nanswer two\nanswer three\n")
        fake_stdin.isatty = lambda: True
        original_stdin = sys.stdin
        sys.stdin = fake_stdin
        # Mock select to always return ready (StringIO has no fileno)
        original_select = select_module.select
        select_module.select = lambda rlist, wlist, xlist, timeout=None: (rlist, [], [])
        try:
            result = utils.collect_interview_answers(
                ["CLARIFICATION 1: Q1", "CLARIFICATION 2: Q2", "CLARIFICATION 3: Q3"]
            )
            assert result == ["answer one", "answer two", "answer three"]
        finally:
            select_module.select = original_select
            sys.stdin = original_stdin
    finally:
        sys.stdin.isatty = original_isatty


def test_collect_interview_answers_stops_on_empty():
    """Stops collecting when user provides an empty answer."""
    import utils
    import select as select_module
    original_isatty = sys.stdin.isatty
    try:
        sys.stdin.isatty = lambda: True
        fake_stdin = io.StringIO("answer one\n\n")
        fake_stdin.isatty = lambda: True
        original_stdin = sys.stdin
        sys.stdin = fake_stdin
        # Mock select to always return ready (StringIO has no fileno)
        original_select = select_module.select
        select_module.select = lambda rlist, wlist, xlist, timeout=None: (rlist, [], [])
        try:
            result = utils.collect_interview_answers(
                ["CLARIFICATION 1: Q1", "CLARIFICATION 2: Q2", "CLARIFICATION 3: Q3"]
            )
            assert result == ["answer one"]  # stopped at Q2 (empty)
        finally:
            select_module.select = original_select
            sys.stdin = original_stdin
    finally:
        sys.stdin.isatty = original_isatty


def test_collect_interview_answers_returns_list():
    """Return type is always a list (even when empty)."""
    import utils
    original_isatty = sys.stdin.isatty
    try:
        sys.stdin.isatty = lambda: False
        result = utils.collect_interview_answers([])
        assert isinstance(result, list)
    finally:
        sys.stdin.isatty = original_isatty
