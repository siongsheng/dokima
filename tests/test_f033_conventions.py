"""Tests for F033: Cross-run learning via conventions.md — extraction + append + dedup."""

import os
import pytest
import tempfile
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ── Test data for _extract_convention_candidates ──

PATTERN_TL_OUTPUT = """### BLOCKERS (1)

**1. No hardcoded paths in module code**
Spec violation: pipeline.py line 42 uses a hardcoded path `/tmp/output`.

VERDICT: BLOCKED
"""

ONE_OFF_TL_OUTPUT = """### BLOCKERS (1)

**1. BLOCKER: missing test for handle_timeout()**
The function handle_timeout() has no test coverage.

VERDICT: BLOCKED
"""

MIXED_TL_OUTPUT = """### BLOCKERS (2)

**1. BLOCKER: No hardcoded paths in module code**
Uses /tmp/hardcoded in pipeline.py.

**2. BLOCKER: missing test for handle_timeout()**
No test for handle_timeout().

**3. BLOCKER: Always use list args for subprocess calls**
Found string-based subprocess.run call.

VERDICT: BLOCKED
"""

MULTI_PATTERN_TL = """### BLOCKERS (3)

**1. BLOCKER: Never use shell=True in subprocess calls**
Found shell=True in utils.py.

**2. BLOCKER: All commits must follow TDD — RED before GREEN**
Found bundled commit at abc123.

**3. BLOCKER: Must validate user input before processing**
Missing validation in handler.

VERDICT: BLOCKED
"""

EMPTY_TL = ""

NO_BLOCKER_TL = """Everything looks good.

VERDICT: APPROVED
"""

BLOCKER_NO_CONVENTION = """### BLOCKERS (1)

**1. BLOCKER: function foo() returns wrong type**
Should return str, returns int at line 47.

VERDICT: BLOCKED
"""


# ── Tests for _extract_convention_candidates ──

class TestExtractConventionCandidates:
    """Task 5: Test _extract_convention_candidates() extraction logic."""

    def test_extracts_pattern_rule(self, panel):
        """TL output with 'BLOCKER: No hardcoded paths' → extracts rule."""
        candidates = panel._extract_convention_candidates(PATTERN_TL_OUTPUT)
        assert len(candidates) >= 1
        assert any("hardcoded" in c.lower() for c in candidates)

    def test_filters_one_off_blocker(self, panel):
        """TL output with 'BLOCKER: missing test for handle_timeout()' → filtered out."""
        candidates = panel._extract_convention_candidates(ONE_OFF_TL_OUTPUT)
        assert candidates == []

    def test_empty_output_returns_empty(self, panel):
        """Empty TL output → empty list."""
        candidates = panel._extract_convention_candidates(EMPTY_TL)
        assert candidates == []

    def test_mixed_one_off_and_pattern(self, panel):
        """Mixed blockers — only patterns extracted, one-offs filtered."""
        candidates = panel._extract_convention_candidates(MIXED_TL_OUTPUT)
        # Should contain pattern rules but not the one-off
        assert any("hardcoded" in c.lower() for c in candidates)
        assert any("list args" in c.lower() or "subprocess" in c.lower() for c in candidates)
        # No one-off rule about handle_timeout
        assert not any("handle_timeout" in c for c in candidates)

    def test_multiple_pattern_keywords(self, panel):
        """Multiple pattern keywords (never, always, must, all) all extracted."""
        candidates = panel._extract_convention_candidates(MULTI_PATTERN_TL)
        assert len(candidates) >= 3

    def test_no_blocker_lines_returns_empty(self, panel):
        """TL output with no BLOCKER lines → empty list."""
        candidates = panel._extract_convention_candidates(NO_BLOCKER_TL)
        assert candidates == []

    def test_blocker_without_convention_keywords_filtered(self, panel):
        """BLOCKER without convention keyword (no/never/always/must) → filtered."""
        candidates = panel._extract_convention_candidates(BLOCKER_NO_CONVENTION)
        assert candidates == []


# ── Test data for _append_convention_rules ──


# ── Tests for _append_convention_rules ──
# (Task 6: added after Task 2 implementation)
