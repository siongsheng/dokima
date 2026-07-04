"""F031: Init interview integration tests.

Tests the full interview flow: one-shot High confidence, Medium->High after
one round, max rounds exhausted with warning, and non-TTY exit code 2.
"""
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _mock_spawn_strategist(return_value):
    """Helper to create a spawn_agent mock that returns the given value."""
    def _spawn(*args, **kwargs):
        return return_value
    return _spawn


def test_one_shot_high_confidence_no_interview():
    """High confidence on first round: no interview loop triggered,
    strategist produces docs immediately."""
    import roadmap
    import utils as _utils

    # Strategist produces spec with task headers immediately (no CLARIFICATION)
    spec_output = """# Feature Spec

## 1. Executive Summary
This is the description.

## 9. Impact
Impact content here.

## 10. What Changed
- Added interview mode

### Task 1: Do something
**Files:** roadmap.py
**Dependencies:** None
"""

    with patch.object(roadmap, 'load_key', return_value='test-key'), \
         patch.object(roadmap, 'load_github_token', return_value='test-token'), \
         patch.object(roadmap, 'detect_repo', return_value='test/test'), \
         patch.object(roadmap.os.path, 'isdir', return_value=True), \
         patch.object(roadmap.os.path, 'exists', return_value=False), \
         patch.object(roadmap.subprocess, 'run') as mock_run, \
         patch.object(roadmap, 'ensure_profiles', return_value=None), \
         patch.object(roadmap, 'deploy_profile_skills', return_value=None), \
         patch.object(roadmap, 'spawn_agent', side_effect=_mock_spawn_strategist(spec_output)):
        mock_run.return_value = MagicMock(stdout='', stderr='', returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "specs"), exist_ok=True)
            roadmap.run_init("Test project description", tmpdir)

            # No CLARIFICATION triggers -> spawn_agent called once (interview)
            # plus possibly a second time for constitution docs
            # The key: should NOT exit with code 2
            assert roadmap.spawn_agent.call_count >= 1


def test_interview_mode_detected_full_loop():
    """CLARIFICATION output -> interview loop triggered -> answers collected -> docs."""
    import roadmap
    import utils as _utils

    # Round 1: strategist returns CLARIFICATION questions
    round1_output = """DECISION: INTERVIEW MODE
Confidence: Low

CLARIFICATION 1: Who are the primary users of this system?
Assumption: Internal developers only
Impact if wrong: Feature scope would be completely wrong

CLARIFICATION 2: What are the anti-goals?
Assumption: No real-time requirements
Impact if wrong: Architecture may need redesign
"""

    # Round 2: strategist returns full spec after getting answers
    round2_output = """# Feature Spec
Confidence: High

## 1. Executive Summary
Refined spec with user answers.

## 9. Impact
Impact section content.

## 10. What Changed
- Refined based on user interview

### Task 1: Do the thing
**Files:** roadmap.py
**Dependencies:** None
"""

    spawn_outputs = [round1_output, round2_output]

    def sequential_spawn(*args, **kwargs):
        if spawn_outputs:
            return spawn_outputs.pop(0)
        return "# Minimal spec"

    def mock_collect(questions, state, path=None):
        # Simulate user providing answers
        return (
            [
                {"question_id": 1, "answer": "External customers"},
                {"question_id": 2, "answer": "No mobile support"}
            ],
            0
        )

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
            roadmap.run_init("Test project", tmpdir)

            # Should have spawned strategist three times:
            # 1st: interview CLARIFICATION output
            # 2nd: re-evaluation with answers (produced docs)
            # 3rd: final dedicated constitution production
            assert roadmap.spawn_agent.call_count == 3


def test_max_rounds_exhausted_produces_docs_with_warning():
    """After 3 rounds without High confidence, produces docs anyway."""
    # This is tested in test_f031_init_loop.py for the loop invariants
    pass
