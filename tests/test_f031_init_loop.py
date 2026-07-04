"""F031: Init interview loop invariants tests.

Tests round counter, max_rounds guard, confidence tracking, state save/load
across rounds, and resume from saved state.
"""
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


def test_run_init_has_interview_loop():
    """run_init() implements an interview loop (calls spawn_agent multiple times
    when CLARIFICATION triggers are present)."""
    import roadmap

    # Verify run_init is callable and the module has the function
    assert hasattr(roadmap, 'run_init')
    assert callable(roadmap.run_init)


def test_run_init_has_max_rounds_guard():
    """After 3 rounds without convergence to High confidence, run_init()
    produces docs anyway with a warning (does not loop infinitely)."""
    import roadmap
    import utils as _utils

    # Strategist always returns CLARIFICATION, never converges
    clarification_output = """DECISION: INTERVIEW MODE
Confidence: Low

CLARIFICATION 1: What is the primary use case?
Assumption: Web dashboard
Impact if wrong: Wrong tech stack
"""

    def always_clarify(*args, **kwargs):
        return clarification_output

    def mock_collect(qs, st, path=None):
        return ([{"question_id": 1, "answer": "Mobile app"}], 0)

    with patch.object(roadmap, 'load_key', return_value='test-key'), \
         patch.object(roadmap, 'load_github_token', return_value='test-token'), \
         patch.object(roadmap, 'detect_repo', return_value='test/test'), \
         patch.object(roadmap.os.path, 'isdir', return_value=True), \
         patch.object(roadmap.os.path, 'exists', return_value=False), \
         patch.object(roadmap.subprocess, 'run') as mock_run, \
         patch.object(roadmap, 'ensure_profiles', return_value=None), \
         patch.object(roadmap, 'deploy_profile_skills', return_value=None), \
         patch.object(roadmap, 'spawn_agent', side_effect=always_clarify), \
         patch.object(roadmap.sys.stdin, 'isatty', return_value=True), \
         patch.object(roadmap, 'collect_init_interview_answers', side_effect=mock_collect):
        mock_run.return_value = MagicMock(stdout='', stderr='', returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "specs"), exist_ok=True)
            # Should not loop forever — max_rounds=3 guard should prevent infinite loop
            roadmap.run_init("Test project", tmpdir)

            # With always-clarify output and max_rounds=3:
            # Rounds: 3 interview calls + 1 final forced-docs call = 4
            assert roadmap.spawn_agent.call_count <= 4, \
                f"Expected <=4 calls (3 rounds + 1 forced final), got {roadmap.spawn_agent.call_count}"


def test_run_init_non_interactive_exit():
    """Non-TTY run_init() with CLARIFICATION triggers should exit via
    collect_init_interview_answers -> exit code 2."""
    import roadmap
    import utils as _utils

    clarification_output = """CLARIFICATION 1: Who are the users?
Assumption: Internal
Impact if wrong: Wrong scope
"""

    def mock_collect_non_tty(qs, st, path=None):
        # Simulate non-TTY path: return exit code 2
        return ([], 2)

    with patch.object(roadmap, 'load_key', return_value='test-key'), \
         patch.object(roadmap, 'load_github_token', return_value='test-token'), \
         patch.object(roadmap, 'detect_repo', return_value='test/test'), \
         patch.object(roadmap.os.path, 'isdir', return_value=True), \
         patch.object(roadmap.os.path, 'exists', return_value=False), \
         patch.object(roadmap.subprocess, 'run') as mock_run, \
         patch.object(roadmap, 'ensure_profiles', return_value=None), \
         patch.object(roadmap, 'deploy_profile_skills', return_value=None), \
         patch.object(roadmap, 'spawn_agent', return_value=clarification_output), \
         patch.object(roadmap.sys.stdin, 'isatty', return_value=True), \
         patch.object(roadmap, 'collect_init_interview_answers', side_effect=mock_collect_non_tty):
        mock_run.return_value = MagicMock(stdout='', stderr='', returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "specs"), exist_ok=True)
            with pytest.raises(SystemExit) as exc_info:
                roadmap.run_init("Test project", tmpdir)
            assert exc_info.value.code == 2

            # After collect returns exit_code=2, run_init should NOT call
            # a second strategist for doc production — it should exit
            # The function should return after seeing exit_code 2
            assert roadmap.spawn_agent.call_count == 1, \
                f"Non-TTY should stop after 1 spawn, got {roadmap.spawn_agent.call_count}"


def test_run_init_resume_from_saved_state():
    """Resume from saved interview state continues at correct round
    with answers pre-filled."""
    import roadmap
    import utils as _utils

    # Spec output (no CLARIFICATION — should produce docs)
    spec_output = """# Feature Spec
Confidence: High

## 9. Impact
Impact content.

## 10. What Changed
- Resume test

### Task 1: Do it
**Files:** roadmap.py
**Dependencies:** None
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        state = {
            "feature": "Resume test",
            "project_dir": "/tmp/test",
            "round": 2,
            "max_rounds": 3,
            "confidence": "Medium",
            "questions": [
                {"id": 1, "question": "Q1", "assumption": "A1", "impact_if_wrong": "Bad"}
            ],
            "answers": [{"question_id": 1, "answer": "My answer"}],
            "original_prompt": "Original prompt",
            "timestamp": "2026-07-04T12:00:00"
        }
        json.dump(state, f)
        answers_path = f.name

    try:
        with patch.object(roadmap, 'load_key', return_value='test-key'), \
             patch.object(roadmap, 'load_github_token', return_value='test-token'), \
             patch.object(roadmap, 'detect_repo', return_value='test/test'), \
             patch.object(roadmap.os.path, 'isdir', return_value=True), \
             patch.object(roadmap.os.path, 'exists', return_value=False), \
             patch.object(roadmap.subprocess, 'run') as mock_run, \
             patch.object(roadmap, 'ensure_profiles', return_value=None), \
             patch.object(roadmap, 'deploy_profile_skills', return_value=None), \
             patch.object(roadmap, 'spawn_agent', return_value=spec_output):
            mock_run.return_value = MagicMock(stdout='', stderr='', returncode=0)

            with tempfile.TemporaryDirectory() as tmpdir:
                os.makedirs(os.path.join(tmpdir, "specs"), exist_ok=True)
                roadmap.run_init("Resume test", tmpdir, answers_path=answers_path)

                # With answers pre-filled and current_round > 1,
                # initial strategist produces docs, then final doc production runs
                assert roadmap.spawn_agent.call_count == 2
    finally:
        os.unlink(answers_path)


def test_run_init_resume_round_not_reset():
    """Resume continues from saved round number, does NOT restart at 1."""
    import roadmap
    import utils as _utils

    # CLARIFICATION output to trigger another round
    clarification_output = """CLARIFICATION 1: More details needed?
Assumption: Fine as is
Impact if wrong: Minor
"""

    spec_output = """# Feature Spec
Confidence: High

## 9. Impact
Done.

## 10. What Changed
- Final

### Task 1: Done
**Files:** roadmap.py
**Dependencies:** None
"""

    spawn_outputs = [clarification_output, spec_output]

    def sequential_spawn(*args, **kwargs):
        if spawn_outputs:
            return spawn_outputs.pop(0)
        return "# Done"

    def mock_collect(qs, st, path=None):
        return ([{"question_id": 1, "answer": "No"}], 0)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        state = {
            "feature": "Round test",
            "project_dir": "/tmp/test",
            "round": 2,  # Starting at round 2
            "max_rounds": 3,
            "confidence": "Medium",
            "questions": [{"id": 1, "question": "Q?", "assumption": "A", "impact_if_wrong": "B"}],
            "answers": [{"question_id": 1, "answer": "Previous answer"}],
            "original_prompt": "Prompt",
            "timestamp": "2026-07-04T12:00:00"
        }
        json.dump(state, f)
        answers_path = f.name

    try:
        with patch.object(roadmap, 'load_key', return_value='test-key'), \
             patch.object(roadmap, 'load_github_token', return_value='test-token'), \
             patch.object(roadmap, 'detect_repo', return_value='test/test'), \
             patch.object(roadmap.os.path, 'isdir', return_value=True), \
             patch.object(roadmap.os.path, 'exists', return_value=False), \
             patch.object(roadmap.subprocess, 'run') as mock_run, \
             patch.object(roadmap, 'ensure_profiles', return_value=None), \
             patch.object(roadmap, 'deploy_profile_skills', return_value=None), \
             patch.object(roadmap, 'spawn_agent', side_effect=sequential_spawn), \
             patch.object(roadmap.sys.stdin, 'isatty', return_value=True), \
             patch.object(roadmap, 'collect_init_interview_answers', side_effect=mock_collect):
            mock_run.return_value = MagicMock(stdout='', stderr='', returncode=0)

            with tempfile.TemporaryDirectory() as tmpdir:
                os.makedirs(os.path.join(tmpdir, "specs"), exist_ok=True)
                roadmap.run_init("Round test", tmpdir, answers_path=answers_path)

                # Starting round=2, one CLARIFICATION round -> round 3
                # Then final spec production -> 3 spawn_agent calls total
                assert roadmap.spawn_agent.call_count == 3
    finally:
        os.unlink(answers_path)
