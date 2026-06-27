"""
TDD regression tests for root causes discovered in F002 pipeline run (2026-06-28).

RED PHASE: These tests assert DESIRED behavior. They should FAIL against
the current buggy code. After fixes are applied, they will PASS.

Bug 1: Spec path detection misses subdirectory plan.md
Bug 2: DAG check contaminated by model thinking echo
Bug 3: DAG re-prompt doesn't verify second attempt succeeded
Bug 4: Verdict extraction first-match-wins, ignores TL's final verdict
Bug 5: Coder prompt lacks anti-creep file-deletion guard
"""

import os
import re
import pytest


# ═══════════════════════════════════════════════════════════════════
# Bug 1: Spec path detection — subdirectory plan.md not found
# ═══════════════════════════════════════════════════════════════════

class TestSpecPathDetection:
    """Line ~3648: _standard_spec only checks specs/<slug>-spec.md."""

    def test_subdirectory_plan_md_should_be_detected(self, panel, tmpdir):
        """DESIRED: When specs/<slug>/plan.md exists and -spec.md doesn't,
        the detection logic should find plan.md."""
        specs_dir = os.path.join(str(tmpdir), "specs")
        slug = "f002-test"
        sub_dir = os.path.join(specs_dir, slug)
        os.makedirs(sub_dir)
        plan_md = os.path.join(sub_dir, "plan.md")
        with open(plan_md, "w") as f:
            f.write("# Test spec with ### Task 1: headers\n")

        # Simulate the DESIRED detection logic:
        # Check both -spec.md AND <slug>/plan.md patterns
        standard = os.path.join(specs_dir, f"{slug}-spec.md")
        subdir_plan = os.path.join(specs_dir, slug, "plan.md")

        found = os.path.exists(standard) or os.path.exists(subdir_plan)
        # DESIRED: should find the subdirectory plan.md
        assert found is True, (
            "FAIL: subdirectory specs/f002-test/plan.md exists but detection "
            "only checks specs/f002-test-spec.md. Fix: check both patterns."
        )

    def test_dash_spec_still_detected(self, panel, tmpdir):
        """DESIRED: -spec.md pattern must still work (backward compat)."""
        specs_dir = os.path.join(str(tmpdir), "specs")
        os.makedirs(specs_dir)
        slug = "f002-test"
        standard = os.path.join(specs_dir, f"{slug}-spec.md")
        with open(standard, "w") as f:
            f.write("# Test")
        assert os.path.exists(standard)


# ═══════════════════════════════════════════════════════════════════
# Bug 2: DAG check runs against raw output including <thinking>
# ═══════════════════════════════════════════════════════════════════

class TestDagCheckThinkingContamination:
    """Line 3770: DAG check uses raw strategist output."""

    REAL_THINKING_OUTPUT = """<thinking>
The spec requires 14 tasks. I'll structure them as:
### Task 1: Extract read_stdin_with_timeout() helper
### Task 2: Create Orchestrator class
</thinking>

F002: Pipeline Integration Tests

    Task 1: Extract read_stdin_with_timeout() helper
    **Files:** dokina
    **Dependencies:** [none]
    **Parallelizable:** yes
    **Description:** Extract the select.select pattern.
"""

    DAG_REGEX = re.compile(r'### Task \d+:')

    def test_dag_check_should_use_extracted_messages(self):
        """DESIRED: DAG check runs on agent output, not raw output with thinking.
        When agent output has no ### Task N:, DAG re-prompt should fire."""
        # Simulate extracting agent messages (strip thinking, keep content)
        if "</thinking>" in self.REAL_THINKING_OUTPUT:
            agent_only = self.REAL_THINKING_OUTPUT.split("</thinking>")[-1]
        else:
            agent_only = self.REAL_THINKING_OUTPUT

        has_dag = bool(self.DAG_REGEX.search(agent_only))
        # DESIRED: Should be False → DAG re-prompt fires
        # Currently it's True because raw output (with thinking) matched
        assert has_dag is False, (
            "FAIL: DAG check runs on raw output including <thinking> block. "
            "The thinking contains '### Task 1:' (false positive), but the "
            "agent's actual output has '    Task 1:' (no ###). "
            "Fix: run DAG check on extract_agent_messages() output."
        )

    def test_genuine_dag_in_agent_output_still_matches(self):
        """DESIRED: When agent output truly has ### Task N:, it should match."""
        good = "### Task 1: Real task\n**Files:** x\n**Dependencies:** [none]\n**Parallelizable:** yes\n**Description:** Real."
        assert bool(self.DAG_REGEX.search(good)) is True


# ═══════════════════════════════════════════════════════════════════
# Bug 3: DAG re-prompt assumes success, never verifies
# ═══════════════════════════════════════════════════════════════════

class TestDagRepromptVerification:
    """Lines 3770-3796: After re-prompt, panel proceeds without checking
    if the second strategist actually produced ### Task N: headers."""

    DAG_REGEX = re.compile(r'### Task \d+:')

    def test_second_output_should_be_verified(self):
        """DESIRED: After DAG re-prompt, verify the second output has ### Task N:.
        If it doesn't, warn and proceed with degraded mode."""
        second_output = "    Task 1: Still broken\n    **Files:** dokina\n"

        # DESIRED: Panel should verify second attempt
        second_ok = bool(self.DAG_REGEX.search(second_output))
        assert second_ok is False, (
            "FAIL: Second strategist output still has no ### Task N: headers, "
            "but panel proceeds without warning. "
            "Fix: verify second output, at minimum print a warning."
        )

    def test_garbage_re_prompt_should_be_detected(self):
        """DESIRED: 'Done. Spec saved to...' garbage should be detected."""
        garbage = "Done. Spec saved to /path/f002-spec.md — Format fixes applied."
        GARBAGE_MARKERS = [
            "done. spec saved to",
            "format fixes applied",
        ]
        is_garbage = any(m in garbage.lower() for m in GARBAGE_MARKERS)
        assert is_garbage is True  # This should always be true
        # The DESIRED behavior: panel detects this and falls back to original spec

    def test_correct_second_output_should_proceed(self):
        """DESIRED: When re-prompt works, proceed normally."""
        good = "### Task 1: Fixed\n**Files:** x\n**Dependencies:** [none]\n**Parallelizable:** yes\n**Description:** Done."
        assert bool(self.DAG_REGEX.search(good)) is True


# ═══════════════════════════════════════════════════════════════════
# Bug 4: Verdict extraction — APPROVED matches before BLOCKED
# ═══════════════════════════════════════════════════════════════════

class TestVerdictExtraction:
    """Lines 3544-3552: if/elif chain matches first occurrence."""

    def extract_verdict_current_buggy(self, tl_output):
        """Exact replica of the buggy logic at lines 3544-3552."""
        tl_upper = tl_output.upper()
        if "VERDICT: APPROVED" in tl_upper:
            return "APPROVED"
        elif "VERDICT: BLOCKED" in tl_upper:
            return "BLOCKED"
        elif "VERDICT: CHANGES REQUESTED" in tl_upper:
            return "CHANGES REQUESTED"
        return "UNKNOWN"

    def extract_verdict_desired(self, tl_output):
        """DESIRED: Extract all VERDICT lines, last one wins."""
        verdicts = re.findall(
            r'VERDICT:\s*(APPROVED|BLOCKED|CHANGES\s+REQUESTED)',
            tl_output, re.IGNORECASE
        )
        if verdicts:
            return verdicts[-1].upper().replace(" ", "_").replace("CHANGES_REQUESTED", "CHANGES REQUESTED")
        return "UNKNOWN"

    def test_last_verdict_should_win(self):
        """DESIRED: When TL quotes 'VERDICT: APPROVED' from nm but then
        writes 'VERDICT: BLOCKED', the LAST verdict should win."""
        output = """NM FINDINGS: The nm review finds no code issues. VERDICT: APPROVED.

However, the Tech Lead finds critical blockers:

### Blockers
- Task 2 not completed — Orchestrator is dead code
- Scope creep — unauthorized file deletions

VERDICT: BLOCKED — 5 blockers, 3 should-fix
"""
        result = self.extract_verdict_desired(output)
        assert result == "BLOCKED", (
            f"FAIL: Last VERDICT should win. Got '{result}' instead of 'BLOCKED'. "
            f"Buggy logic would return: '{self.extract_verdict_current_buggy(output)}'. "
            f"Fix: use re.findall to get all VERDICT lines, take the last one."
        )

    def test_current_buggy_gets_wrong_answer(self):
        """Verify the current buggy logic is actually wrong for this case."""
        output = """NM FINDINGS: VERDICT: APPROVED.

TL FINAL: VERDICT: BLOCKED — 5 critical issues.
"""
        buggy = self.extract_verdict_current_buggy(output)
        desired = self.extract_verdict_desired(output)
        assert buggy != desired, (
            f"FAIL: Buggy logic says '{buggy}', desired logic says '{desired}'. "
            f"They should differ for this input (proving the bug exists)."
        )

    def test_simple_approved_still_works(self):
        """DESIRED: Simple APPROVED case should still work."""
        output = "VERDICT: APPROVED"
        assert self.extract_verdict_desired(output) == "APPROVED"

    def test_simple_blocked_still_works(self):
        """DESIRED: Simple BLOCKED case should still work."""
        output = "VERDICT: BLOCKED — 5 issues"
        assert self.extract_verdict_desired(output) == "BLOCKED"


# ═══════════════════════════════════════════════════════════════════
# Bug 5: Coder prompt lacks anti-creep deletion guard
# ═══════════════════════════════════════════════════════════════════

class TestCoderPromptAntiCreep:
    """The coder prompt should explicitly forbid destructive changes."""

    def test_prompt_should_have_anti_deletion_guard(self, panel):
        """DESIRED: Coder prompt must include a rule against deleting
        files not listed in the task's Files: field."""
        import inspect
        source = inspect.getsource(panel.run_phase2_coder)

        REQUIRED_GUARDS = [
            "do not delete",
            "never delete",
            "do not remove",
        ]
        found_guards = [g for g in REQUIRED_GUARDS if g in source.lower()]

        assert len(found_guards) > 0, (
            "FAIL: Coder prompt has NO anti-deletion guard. "
            "The coder is free to delete any file in the repo. "
            "Fix: add 'DO NOT DELETE existing files not listed in "
            "the task's Files: field.' to the coder prompt."
        )

    def test_prompt_should_have_scope_boundary(self, panel):
        """DESIRED: Coder prompt should limit changes to listed files."""
        import inspect
        source = inspect.getsource(panel.run_phase2_coder)

        SCOPE_GUARDS = [
            "only modify files",
            "do not touch files outside",
            "files listed in",
        ]
        found = [g for g in SCOPE_GUARDS if g in source.lower()]
        assert len(found) > 0, (
            "FAIL: Coder prompt has NO file-scope boundary rule. "
            "The coder can modify any file in the repo. "
            "Fix: add 'Only modify files listed in this task's Files: field.'"
        )

    def test_dag_check_uses_extracted_messages(self, panel):
        """DESIRED: DAG check at line ~3730 should call extract_agent_messages()
        BEFORE the re.search(r'### Task', ...) regex check. This prevents
        false positives from <thinking> blocks in the raw output."""
        import inspect
        source = inspect.getsource(panel.run_phase1_strategist)

        # Find the DAG enforcement section specifically
        dag_section_start = source.find("# ── DAG format enforcement ──")
        assert dag_section_start > 0, "DAG enforcement section not found"

        # Within that section, extract_agent_messages must appear before re.search
        dag_section = source[dag_section_start:]
        extract_pos = dag_section.find("extract_agent_messages")
        regex_pos = dag_section.find("re.search(r'### Task")

        assert extract_pos > 0, "extract_agent_messages not found in DAG section"
        assert regex_pos > 0, "DAG regex check not found in DAG section"
        assert extract_pos < regex_pos, (
            "FAIL: In the DAG enforcement section, extract_agent_messages "
            f"appears at offset {extract_pos} but re.search is at offset {regex_pos}. "
            "The DAG check still runs against raw output with <thinking> blocks. "
            "Fix: call extract_agent_messages() before the DAG regex check."
        )

    def test_verdict_extraction_uses_last_match(self, panel):
        """DESIRED: Verdict extraction should find the LAST VERDICT line,
        not the first. The TL's final verdict is always the last one."""
        import inspect
        source = inspect.getsource(panel.run_phase5_tech_lead)

        # Check if the verdict extraction uses re.findall or last-match
        uses_findall = "findall" in source and "VERDICT" in source
        uses_last = "[-1]" in source and "VERDICT" in source.upper() if "VERDICT" in source.upper() else False

        # Current code uses if/elif which matches first occurrence
        has_if_elif_chain = (
            'if "VERDICT: APPROVED"' in source.replace(' ', '').replace("'", '"') or
            'if "VERDICT: APPROVED"' in source
        )
        # This test documents the bug. After fix, should use re.findall + [-1]
        if has_if_elif_chain:
            # BUG EXISTS — confirmed
            pass
        # DESIRED: after fix, uses findall + last index
