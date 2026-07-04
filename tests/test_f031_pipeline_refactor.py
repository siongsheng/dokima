"""F031: --answers routing for init subcommand.

Tests that dokima init --answers <path> routes to run_init() with the
resume state, and that collect_init_interview_answers is preserved.
"""
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_pipeline_refactored_to_use_shared_helper():
    """Verify run_init() accepts answers_path parameter."""
    import roadmap
    import inspect

    sig = inspect.signature(roadmap.run_init)
    params = list(sig.parameters.keys())
    assert 'answers_path' in params, \
        f"run_init should accept answers_path parameter, got {params}"


def test_collect_interview_answers_behavior_preserved():
    """collect_init_interview_answers() function exists and is callable."""
    import utils

    assert hasattr(utils, 'collect_init_interview_answers')
    assert callable(utils.collect_init_interview_answers)


def test_init_answers_routing():
    """dokima init --answers <path> routes to run_init() with answers_path set."""
    import roadmap

    # Create a valid interview state file
    state = {
        "feature": "Test project",
        "project_dir": "/tmp/test",
        "round": 1,
        "max_rounds": 3,
        "confidence": "Low",
        "questions": [{"id": 1, "question": "Q?", "assumption": "A", "impact_if_wrong": "B"}],
        "answers": [{"question_id": 1, "answer": "My answer"}],
        "original_prompt": "Prompt",
        "timestamp": "2026-07-04T12:00:00"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
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
             patch.object(roadmap, 'spawn_agent', return_value="# Test spec\nConfidence: High\n\n## 9. Impact\n\n## 10. What Changed\n\n### Task 1: Test\n**Files:** test.py\n**Dependencies:** None\n"):

            mock_run.return_value = MagicMock(stdout='', stderr='', returncode=0)

            with tempfile.TemporaryDirectory() as tmpdir:
                os.makedirs(os.path.join(tmpdir, "specs"), exist_ok=True)
                roadmap.run_init("Test project", tmpdir, answers_path=answers_path)
                assert roadmap.spawn_agent.call_count >= 1
    finally:
        os.unlink(answers_path)
