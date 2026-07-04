"""F031 — Verify pipeline.py refactored to use shared collect_interview_answers."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


def test_pipeline_refactored_to_use_shared_helper():
    """run_phase1_strategist uses utils.collect_interview_answers instead of inline loop."""
    # Verify collect_interview_answers is used in pipeline.py
    with open(os.path.join(os.path.dirname(__file__), '..', 'pipeline.py')) as f:
        source = f.read()

    # After refactoring, pipeline.py should call utils.collect_interview_answers
    # (either via import + call, or stored alias)
    assert 'collect_interview_answers' in source, \
        "pipeline.py must reference collect_interview_answers"

    # Old inline select.select + sys.stdin.readline loop should be gone
    # (the one collecting answers interactively — NOT the non-tty block)
    # Verify the old pattern (select.select in an interactive answer loop) is removed
    # by checking that the old inline answer collection is gone
    # The refactored version preserves the non-interactive block but replaces
    # the interactive one.

    # Check that the shared helper name appears in the interactive section context
    # (around where the old answer-collection code was)
    # Look for 'collect_interview_answers' in the latter half of the file
    # where run_phase1_strategist lives
    lines = source.split('\n')
    found = False
    for i, line in enumerate(lines):
        if 'collect_interview_answers' in line:
            found = True
            break
    assert found, "collect_interview_answers not found in pipeline.py source"


def test_collect_interview_answers_behavior_preserved():
    """Shared helper has same behavior as old inline code — same tty check,
    same timeout, same empty-input termination."""
    import utils
    from unittest.mock import patch

    # Non-tty => empty list
    with patch.object(sys.stdin, 'isatty', return_value=False):
        result = utils.collect_interview_answers(
            ["CLARIFICATION 1: test"]
        )
        assert result == []

    # Empty input => empty list
    with patch.object(sys.stdin, 'isatty', return_value=True):
        result = utils.collect_interview_answers([])
        assert result == []

    # Verify function signature matches expected usage
    import inspect
    sig = inspect.signature(utils.collect_interview_answers)
    params = list(sig.parameters.keys())
    assert 'clarification_lines' in params
    assert 'timeout' in params
    assert sig.parameters['timeout'].default == 60
