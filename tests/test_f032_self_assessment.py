"""F032: Agent-as-Judge Self-Assessment — verify 3-question block injected into coder prompt.

Tests:
- Normal coder prompt contains Q1 SPEC COVERAGE, Q2 CONFIDENCE, Q3 TL PREDICTION
- Prompt contains "Before pushing" context
- Fix mode prompt does NOT contain self-assessment questions
"""

import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _load_fresh_panel():
    """Load a fresh dokima panel, clearing stale module state."""
    from conftest import _load_panel
    return _load_panel()


# ── Normal mode: self-assessment present ────────────────────────

def test_coder_prompt_contains_self_assessment(tmp_path):
    """Normal coder prompt (non-fix) must contain Q1/Q2/Q3 self-assessment questions."""
    panel = _load_fresh_panel()

    # Set up project dir with required files
    project_dir = tmp_path / "test-project"
    specs_dir = project_dir / "specs"
    specs_dir.mkdir(parents=True)

    spec_path = specs_dir / "test-feature-spec.md"
    spec_path.write_text("# Test Feature\n\n## Description\nTest spec for self-assessment.\n")

    tasks_path = specs_dir / "test-feature-tasks.md"
    tasks_path.write_text("### Task 1: Do something\n**Files:** test.py\n**Description:** Test task.\n")

    # AGENTS.md for detect_commands
    agents_path = project_dir / "AGENTS.md"
    agents_path.write_text("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

    panel.PROJECT_DIR = str(project_dir)
    panel.REPO = "test-owner/test-repo"
    panel.DEFAULT_BRANCH = "main"
    panel.TEST_CMD = "echo test"
    panel.BUILD_CMD = "echo build"
    panel.LINT_CMD = "echo lint"

    captured_prompts = []

    def capture_prompt(profile, skills, prompt, **kwargs):
        captured_prompts.append(prompt)
        # Return output that won't trigger clarification gate or post-coder gate
        return "RED commit done. GREEN commit done. build pass. tests pass. All OK."

    with patch.object(panel, "spawn_agent", side_effect=capture_prompt):
        with patch.object(panel, "git", return_value=("", "", 0)):
            with patch.object(panel, "gh", return_value=("", "", 0)):
                with patch("time.sleep"):
                    result = panel.run_phase2_coder(
                        feature="Test Feature",
                        spec="# Test spec",
                        spec_path=str(spec_path),
                        tasks_extract_path=str(tasks_path),
                        pr_sections="## What Changed",
                        branch="feat/test-feature",
                        depth="vet",
                        mode="vet",
                        is_next=False,
                    )

    assert captured_prompts, "spawn_agent was never called — no prompt captured"
    prompt = captured_prompts[0]

    # Q1: SPEC COVERAGE
    assert "Q1" in prompt, f"Q1 missing from prompt:\n{prompt[:500]}"
    assert "SPEC COVERAGE" in prompt, f"SPEC COVERAGE missing from prompt"

    # Q2: CONFIDENCE
    assert "Q2" in prompt, f"Q2 missing from prompt"
    assert "CONFIDENCE" in prompt, f"CONFIDENCE missing from prompt"

    # Q3: TL PREDICTION
    assert "Q3" in prompt, f"Q3 missing from prompt"
    assert "TL PREDICTION" in prompt, f"TL PREDICTION missing from prompt"

    # Context
    assert "SELF-ASSESSMENT" in prompt, f"SELF-ASSESSMENT header missing from prompt"
    assert "Before pushing" in prompt, f"'Before pushing' missing from prompt"


def test_coder_prompt_self_assessment_before_report(tmp_path):
    """Self-assessment block must appear before the Report: tag."""
    panel = _load_fresh_panel()

    project_dir = tmp_path / "test-project"
    specs_dir = project_dir / "specs"
    specs_dir.mkdir(parents=True)

    spec_path = specs_dir / "test-feature-spec.md"
    spec_path.write_text("# Test Feature\n")

    tasks_path = specs_dir / "test-feature-tasks.md"
    tasks_path.write_text("### Task 1: Test\n**Files:** x.py\n")

    agents_path = project_dir / "AGENTS.md"
    agents_path.write_text("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

    panel.PROJECT_DIR = str(project_dir)
    panel.REPO = "test-owner/test-repo"
    panel.DEFAULT_BRANCH = "main"
    panel.TEST_CMD = "echo test"
    panel.BUILD_CMD = "echo build"
    panel.LINT_CMD = "echo lint"

    captured_prompts = []

    def capture_prompt(profile, skills, prompt, **kwargs):
        captured_prompts.append(prompt)
        return "RED done. GREEN done. build pass. tests pass."

    with patch.object(panel, "spawn_agent", side_effect=capture_prompt):
        with patch.object(panel, "git", return_value=("", "", 0)):
            with patch.object(panel, "gh", return_value=("", "", 0)):
                with patch("time.sleep"):
                    panel.run_phase2_coder(
                        feature="Test",
                        spec="# Test spec",
                        spec_path=str(spec_path),
                        tasks_extract_path=str(tasks_path),
                        pr_sections="",
                        branch="feat/test",
                        depth="vet",
                        mode="vet",
                        is_next=False,
                    )

    assert captured_prompts
    prompt = captured_prompts[0]

    # Self-assessment must appear BEFORE the Report: tag
    sa_idx = prompt.find("SELF-ASSESSMENT")
    report_idx = prompt.find("Report: both commit hashes")
    assert sa_idx != -1, "SELF-ASSESSMENT block not found"
    assert report_idx != -1, "Report: tag not found"
    assert sa_idx < report_idx, (
        f"SELF-ASSESSMENT ({sa_idx}) must appear BEFORE Report: tag ({report_idx})"
    )


# ── Fix mode: self-assessment absent ────────────────────────────

def test_fix_mode_prompt_does_not_contain_self_assessment(tmp_path):
    """Fix mode coder prompt must NOT contain self-assessment questions."""
    panel = _load_fresh_panel()

    project_dir = tmp_path / "test-project"
    specs_dir = project_dir / "specs"
    specs_dir.mkdir(parents=True)

    spec_path = specs_dir / "test-feature-spec.md"
    spec_path.write_text("# Fix spec — blockers")

    agents_path = project_dir / "AGENTS.md"
    agents_path.write_text("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

    panel.PROJECT_DIR = str(project_dir)
    panel.REPO = "test-owner/test-repo"
    panel.DEFAULT_BRANCH = "main"
    panel.TEST_CMD = "echo test"
    panel.BUILD_CMD = "echo build"
    panel.LINT_CMD = "echo lint"

    captured_prompts = []

    def capture_prompt(profile, skills, prompt, **kwargs):
        captured_prompts.append(prompt)
        return "Fix applied. RED done. GREEN done. build pass. tests pass."

    with patch.object(panel, "spawn_agent", side_effect=capture_prompt):
        with patch.object(panel, "git", return_value=("", "", 0)):
            with patch.object(panel, "gh", return_value=("", "", 0)):
                with patch("time.sleep"):
                    panel.run_phase2_coder(
                        feature="Fix Feature",
                        spec="Fix: resolve the blockers listed above",
                        spec_path=str(spec_path),
                        tasks_extract_path="",
                        pr_sections="",
                        branch="feat/fix-test",
                        depth="vet",
                        mode="fix",
                        is_next=False,
                    )

    assert captured_prompts, "Fix mode spawn_agent was never called"
    prompt = captured_prompts[0]

    # Fix mode must NOT have self-assessment questions
    assert "SELF-ASSESSMENT" not in prompt, (
        f"Fix mode should NOT have SELF-ASSESSMENT block but found:\n{prompt[:500]}"
    )
    assert "Q1:" not in prompt, f"Fix mode should NOT have Q1 but found:\n{prompt[:500]}"
    assert "Q2:" not in prompt, f"Fix mode should NOT have Q2 but found:\n{prompt[:500]}"
    assert "Q3:" not in prompt, f"Fix mode should NOT have Q3 but found:\n{prompt[:500]}"


# ── Prompt text quality ─────────────────────────────────────────

def test_self_assessment_block_is_not_empty(tmp_path):
    """Self-assessment block must have meaningful text, not just headers."""
    panel = _load_fresh_panel()

    project_dir = tmp_path / "test-project"
    specs_dir = project_dir / "specs"
    specs_dir.mkdir(parents=True)

    spec_path = specs_dir / "test-feature-spec.md"
    spec_path.write_text("# Test\n")

    tasks_path = specs_dir / "test-feature-tasks.md"
    tasks_path.write_text("### Task 1\n**Files:** x.py\n")

    agents_path = project_dir / "AGENTS.md"
    agents_path.write_text("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

    panel.PROJECT_DIR = str(project_dir)
    panel.REPO = "test-owner/test-repo"
    panel.DEFAULT_BRANCH = "main"
    panel.TEST_CMD = "echo test"
    panel.BUILD_CMD = "echo build"
    panel.LINT_CMD = "echo lint"

    captured_prompts = []

    def capture_prompt(profile, skills, prompt, **kwargs):
        captured_prompts.append(prompt)
        return "RED done. GREEN done. build pass. tests pass."

    with patch.object(panel, "spawn_agent", side_effect=capture_prompt):
        with patch.object(panel, "git", return_value=("", "", 0)):
            with patch.object(panel, "gh", return_value=("", "", 0)):
                with patch("time.sleep"):
                    panel.run_phase2_coder(
                        feature="Test",
                        spec="# Test",
                        spec_path=str(spec_path),
                        tasks_extract_path=str(tasks_path),
                        pr_sections="",
                        branch="feat/test",
                        depth="vet",
                        mode="vet",
                        is_next=False,
                    )

    assert captured_prompts
    prompt = captured_prompts[0]

    # Extract the self-assessment block (between SELF-ASSESSMENT and Report:)
    sa_start = prompt.find("SELF-ASSESSMENT")
    report_start = prompt.find("Report: both commit hashes")
    sa_block = prompt[sa_start:report_start] if sa_start < report_start else ""

    assert len(sa_block) > 100, (
        f"Self-assessment block too short ({len(sa_block)} chars):\n{sa_block}"
    )
    # The block must contain meaningful guidance, not just headers
    assert "spec requirement" in sa_block.lower() or "implementation" in sa_block.lower(), (
        f"Self-assessment block missing Q1 detail text:\n{sa_block}"
    )
    assert "Tech Lead" in sa_block or "TL" in sa_block or "tech lead" in sa_block.lower(), (
        f"Self-assessment block missing Q3 TL reference:\n{sa_block}"
    )
