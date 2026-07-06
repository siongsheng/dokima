"""Tests for _extract_nm_summary() — nm output parsing, risk extraction, key findings, auto-fix detection.

Covers: happy path (full nm output), empty/None input, missing RISK line,
large output truncation, should_fix delegation, auto-fix pattern detection.
"""

import pytest
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ── Simulated nm outputs ──

NM_OUTPUT_FULL = """You are running the adversarial review agent.
Initializing model family: different from coder
Loading codebase...

STAGE 1: Diff Analysis

The diff contains 3 files changed, +120/-45 lines.

STAGE 2: Adversarial Review

RISK: MEDIUM

The implementation follows the spec but has several issues:

1. Missing test for the edge case where input is None
2. The error handling in utils.py uncaught exception on line 42
3. TDD violation: bundled commit at commit abc123

SHOULD FIX — Naming conventions for internal functions in utils.py:42
SHOULD FIX: Extract long method in pipeline.py:100
SHOULD FIX — Add missing edge case test in tests/

Summary: Overall acceptable but needs test coverage improvements.
"""

NM_OUTPUT_NO_RISK = """You are running the adversarial review agent.

STAGE 1: Diff Analysis

Diff has 1 file changed.

STAGE 2: Adversarial Review

No significant issues found. Code looks clean.

SHOULD FIX:
- [MAINTAINABILITY] docs/: Update README with new commands
"""

NM_OUTPUT_EMPTY = ""

NM_OUTPUT_WHITESPACE = "   \n\n  "

NM_OUTPUT_LARGE_BOILERPLATE = "You are running the adversarial review agent.\n" * 50 + \
    "Initializing model family...\n" * 20 + \
    "STAGE 1: Diff Analysis\n" + \
    "RISK: LOW\n" + \
    "Key finding text that should be captured.\n" * 200


# ── Happy path tests ──

def test_extract_nm_summary_returns_all_keys(panel):
    result = panel._extract_nm_summary(NM_OUTPUT_FULL)
    assert isinstance(result, dict)
    assert "risk" in result
    assert "auto_fix_count" in result
    assert "auto_fix_labels" in result
    assert "key_findings" in result
    assert "should_fix_items" in result


def test_extract_nm_summary_extracts_risk(panel):
    result = panel._extract_nm_summary(NM_OUTPUT_FULL)
    assert result["risk"] == "MEDIUM"


def test_extract_nm_summary_detects_auto_fix(panel):
    result = panel._extract_nm_summary(NM_OUTPUT_FULL)
    assert result["auto_fix_count"] >= 2
    labels = [l.lower() for l in result["auto_fix_labels"]]
    assert any("missing test" in l for l in labels)
    assert any("uncaught exception" in l for l in labels)


def test_extract_nm_summary_key_findings_skips_boilerplate(panel):
    result = panel._extract_nm_summary(NM_OUTPUT_FULL)
    key = result["key_findings"]
    assert "You are running" not in key
    assert "STAGE 1" not in key
    assert "STAGE 2" not in key
    assert "naming conventions" in key or "Naming conventions" in key


def test_extract_nm_summary_should_fix_delegation(panel):
    result = panel._extract_nm_summary(NM_OUTPUT_FULL)
    items = result["should_fix_items"]
    assert isinstance(items, list)
    # An nm output with SHOULD FIX patterns should find some items
    assert len(items) >= 1, f"Expected at least 1 SHOULD FIX item, got {len(items)}"


# ── Edge case tests ──

def test_extract_nm_summary_empty_string(panel):
    result = panel._extract_nm_summary(NM_OUTPUT_EMPTY)
    assert result["risk"] == "UNKNOWN"
    assert result["auto_fix_count"] == 0
    assert result["auto_fix_labels"] == []
    assert result["key_findings"] == ""
    assert result["should_fix_items"] == []


def test_extract_nm_summary_none_input(panel):
    result = panel._extract_nm_summary(None)
    assert result["risk"] == "UNKNOWN"
    assert result["auto_fix_count"] == 0
    assert result["auto_fix_labels"] == []
    assert result["key_findings"] == ""
    assert result["should_fix_items"] == []


def test_extract_nm_summary_whitespace_only(panel):
    result = panel._extract_nm_summary(NM_OUTPUT_WHITESPACE)
    assert result["risk"] == "UNKNOWN"
    assert result["auto_fix_count"] == 0


def test_extract_nm_summary_no_risk_line(panel):
    result = panel._extract_nm_summary(NM_OUTPUT_NO_RISK)
    assert result["risk"] == "UNKNOWN"


def test_extract_nm_summary_no_should_fix(panel):
    # Output with no SHOULD FIX keywords
    result = panel._extract_nm_summary("RISK: LOW\n\nAll good. No issues found.")
    assert result["risk"] == "LOW"
    assert result["should_fix_items"] == []


def test_extract_nm_summary_large_output_truncation(panel):
    result = panel._extract_nm_summary(NM_OUTPUT_LARGE_BOILERPLATE)
    key = result["key_findings"]
    assert len(key) <= 3000, f"key_findings too long: {len(key)} chars"
    assert "Key finding text" in key


def test_extract_nm_summary_key_findings_empty_when_all_boilerplate(panel):
    # Output that is ALL boilerplate, no substantive content
    boilerplate_only = "You are running the adversarial review agent.\nInitializing...\nSTAGE 1: Diff Analysis\nSTAGE 2: Adversarial Review\nRISK: LOW\n"
    result = panel._extract_nm_summary(boilerplate_only)
    # key_findings may be empty or minimal — should not contain boilerplate markers
    key = result["key_findings"]
    assert "STAGE 1" not in key
    assert "STAGE 2" not in key
    assert "You are running" not in key


def test_extract_nm_summary_risk_case_insensitive(panel):
    result = panel._extract_nm_summary("risk: high\n\nSome findings here.")
    assert result["risk"] == "HIGH"


def test_extract_nm_summary_auto_fix_bundled_commit(panel):
    output = "RISK: MEDIUM\n\nSTAGE 1\nTDD violation: bundled commit at abc123\nMissing test for edge case"
    result = panel._extract_nm_summary(output)
    labels = [l.lower() for l in result["auto_fix_labels"]]
    assert any("tdd violation" in l for l in labels) or any("bundled commit" in l for l in labels)


def test_extract_nm_summary_unhandled_error_pattern(panel):
    output = "RISK: MEDIUM\n\nSTAGE 1\nUnhandled error in pipeline\n"
    result = panel._extract_nm_summary(output)
    labels = [l.lower() for l in result["auto_fix_labels"]]
    assert any("unhandled error" in l for l in labels)


# ═══════════════════════════════════════════════════════════════════
# Task 2: nm PR body injection
# ═══════════════════════════════════════════════════════════════════


NM_REVIEW_STRIP_RE = r'\n### nm Review\n.*?(?=\n### |\n## |\Z)'


class TestNmReviewMarkdown:
    """Tests for building the ### nm Review markdown section."""

    def test_build_nm_review_risk_and_findings(self):
        """Builds markdown with risk header and key findings."""
        import pipeline as pl
        summary = {
            "risk": "MEDIUM",
            "auto_fix_count": 2,
            "auto_fix_labels": ["missing test", "uncaught exception"],
            "key_findings": "The implementation has several issues.",
            "should_fix_items": [],
        }
        md = pl._build_nm_review_section(summary)
        assert "### nm Review" in md
        assert "**Risk:** MEDIUM" in md
        assert "Auto-Fix Applied" in md
        assert "2 issue(s)" in md
        assert "missing test" in md
        assert "uncaught exception" in md
        assert "The implementation has several issues." in md

    def test_build_nm_review_minimal(self):
        """Minimal output — no auto-fix, no findings, no SHOULD FIX."""
        import pipeline as pl
        summary = {
            "risk": "UNKNOWN",
            "auto_fix_count": 0,
            "auto_fix_labels": [],
            "key_findings": "",
            "should_fix_items": [],
        }
        md = pl._build_nm_review_section(summary)
        assert "### nm Review" in md
        assert "**Risk:** UNKNOWN" in md
        assert "Auto-Fix Applied" not in md
        assert "No findings" in md

    def test_build_nm_review_with_should_fix(self):
        """Builds markdown with SHOULD FIX list."""
        import pipeline as pl
        summary = {
            "risk": "HIGH",
            "auto_fix_count": 0,
            "auto_fix_labels": [],
            "key_findings": "Critical issues found.",
            "should_fix_items": [
                {"detail": "Naming conventions in utils.py"},
                {"detail": "Extract long method in pipeline.py"},
            ],
        }
        md = pl._build_nm_review_section(summary)
        assert "### SHOULD FIX (2)" in md
        assert "Naming conventions in utils.py" in md
        assert "Extract long method in pipeline.py" in md

    def test_build_nm_review_auto_fix_no_should_fix(self):
        """Auto-fix section without SHOULD FIX items."""
        import pipeline as pl
        summary = {
            "risk": "LOW",
            "auto_fix_count": 1,
            "auto_fix_labels": ["missing test"],
            "key_findings": "One test missing.",
            "should_fix_items": [],
        }
        md = pl._build_nm_review_section(summary)
        assert "Auto-Fix Applied" in md
        assert "1 issue(s)" in md
        assert "missing test" in md
        assert "SHOULD FIX" not in md


class TestNmReviewStripRegex:
    """Tests for the regex that strips old ### nm Review sections."""

    def test_strips_nm_section(self):
        body = "## Description\n\nSome text\n\n### nm Review\n\nOld nm content\n\n## Review\n\nTL section"
        import re
        cleaned = re.sub(NM_REVIEW_STRIP_RE, '', body, flags=re.DOTALL)
        assert "### nm Review" not in cleaned
        assert "Old nm content" not in cleaned
        assert "## Description" in cleaned
        assert "## Review" in cleaned

    def test_preserves_other_sections(self):
        body = "## Description\n\ntext\n\n### nm Review\n\nnm stuff\n\n## Review\nTL\n\n## Validation\nok"
        import re
        cleaned = re.sub(NM_REVIEW_STRIP_RE, '', body, flags=re.DOTALL)
        assert "## Description" in cleaned
        assert "## Review" in cleaned
        assert "## Validation" in cleaned
        assert "### nm Review" not in cleaned

    def test_no_nm_section_unchanged(self):
        body = "## Description\n\nSome text\n\n## Review\n\nTL section"
        import re
        cleaned = re.sub(NM_REVIEW_STRIP_RE, '', body, flags=re.DOTALL)
        assert cleaned == body

    def test_strips_multiple_nm_sections(self):
        body = "\n### nm Review\nfirst\n\n## Review\nTL\n\n### nm Review\nsecond\n\n## End"
        import re
        cleaned = re.sub(NM_REVIEW_STRIP_RE, '', body, flags=re.DOTALL)
        assert "first" not in cleaned
        assert "second" not in cleaned
        assert "## Review" in cleaned
        assert "## End" in cleaned

    def test_nm_review_at_end_of_body(self):
        body = "## Description\n\ntext\n\n### nm Review\n\nlast section"
        import re
        cleaned = re.sub(NM_REVIEW_STRIP_RE, '', body, flags=re.DOTALL)
        assert "### nm Review" not in cleaned
        assert "last section" not in cleaned
        assert "## Description" in cleaned


class TestNmInjectionIntegration:
    """Integration tests for nm PR body injection in run_phase4_nm."""

    def test_inject_nm_into_pr_body_updates_body(self):
        """When pr_url is set, injects nm section into PR body."""
        from unittest.mock import patch
        import vcs
        import pipeline as pl

        summary = {
            "risk": "MEDIUM",
            "auto_fix_count": 0,
            "auto_fix_labels": [],
            "key_findings": "Some findings.",
            "should_fix_items": [],
        }

        existing_body = "## Description\n\nExisting content\n\n## Review\n\nTL stuff"
        pr_url = "https://github.com/owner/repo/pull/42"
        pr_num = "42"

        with patch.object(vcs, 'vcs_pr_view') as mock_view, \
             patch.object(vcs, 'vcs_pr_update_body') as mock_update:
            mock_view.return_value = (existing_body, "", 0)
            mock_update.return_value = ("", "", 0)

            result = pl._inject_nm_into_pr_body(pr_url, summary)

        assert result is True
        mock_view.assert_called_once()
        mock_update.assert_called_once()
        updated_body = mock_update.call_args[0][1]
        assert "### nm Review" in updated_body
        assert "**Risk:** MEDIUM" in updated_body
        assert "Existing content" in updated_body

    def test_inject_nm_into_pr_body_no_pr_url(self):
        """When pr_url is None, skips injection gracefully."""
        import pipeline as pl
        summary = {"risk": "LOW", "auto_fix_count": 0, "auto_fix_labels": [],
                   "key_findings": "", "should_fix_items": []}
        result = pl._inject_nm_into_pr_body(None, summary)
        assert result is False

    def test_inject_nm_into_pr_body_vcs_view_fails(self):
        """When vcs_pr_view fails, returns False without crashing."""
        from unittest.mock import patch
        import vcs
        import pipeline as pl

        summary = {"risk": "LOW", "auto_fix_count": 0, "auto_fix_labels": [],
                   "key_findings": "", "should_fix_items": []}
        pr_url = "https://github.com/owner/repo/pull/42"

        with patch.object(vcs, 'vcs_pr_view') as mock_view:
            mock_view.return_value = ("", "error", 1)

            result = pl._inject_nm_into_pr_body(pr_url, summary)

        assert result is False

    def test_inject_nm_into_pr_body_vcs_update_fails(self):
        """When vcs_pr_update_body fails, returns False without crashing."""
        from unittest.mock import patch
        import vcs
        import pipeline as pl

        summary = {"risk": "LOW", "auto_fix_count": 0, "auto_fix_labels": [],
                   "key_findings": "", "should_fix_items": []}
        pr_url = "https://github.com/owner/repo/pull/42"

        with patch.object(vcs, 'vcs_pr_view') as mock_view, \
             patch.object(vcs, 'vcs_pr_update_body') as mock_update:
            mock_view.return_value = ("body", "", 0)
            mock_update.return_value = ("", "update error", 1)

            result = pl._inject_nm_into_pr_body(pr_url, summary)

        assert result is False


# ═══════════════════════════════════════════════════════════════════
# Task 3: TL PR body injection preserves and refreshes nm section
# ═══════════════════════════════════════════════════════════════════

TL_NM_COMBINED_STRIP_RE = (
    r'\n### nm Review\n.*?(?=\n### |\n## |\Z)|'
    r'\n## Review\n\n.*?(?=\n## |\Z)'
)


class TestTlStripNmSection:
    """Tests for combined TL + nm section stripping regex."""

    def test_strips_both_tl_and_nm_sections(self):
        body = "## Description\n\ntext\n\n### nm Review\n\nnm content\n\n## Review\n\nTL content\n\n## Validation\nok"
        import re
        cleaned = re.sub(TL_NM_COMBINED_STRIP_RE, '', body, flags=re.DOTALL)
        assert "### nm Review" not in cleaned
        assert "nm content" not in cleaned
        assert "## Review" not in cleaned
        assert "TL content" not in cleaned
        assert "## Description" in cleaned
        assert "## Validation" in cleaned

    def test_strips_tl_review_only_when_no_nm(self):
        body = "## Description\n\ntext\n\n## Review\n\nTL content\n\n## Validation\nok"
        import re
        cleaned = re.sub(TL_NM_COMBINED_STRIP_RE, '', body, flags=re.DOTALL)
        assert "## Review" not in cleaned
        assert "TL content" not in cleaned
        assert "## Description" in cleaned
        assert "## Validation" in cleaned

    def test_strips_nm_only_when_no_tl(self):
        body = "## Description\n\ntext\n\n### nm Review\n\nnm content\n\n## Validation\nok"
        import re
        cleaned = re.sub(TL_NM_COMBINED_STRIP_RE, '', body, flags=re.DOTALL)
        assert "### nm Review" not in cleaned
        assert "nm content" not in cleaned
        assert "## Description" in cleaned
        assert "## Validation" in cleaned

    def test_no_sections_unchanged(self):
        body = "## Description\n\nSome text\n\n## Validation\nok"
        import re
        cleaned = re.sub(TL_NM_COMBINED_STRIP_RE, '', body, flags=re.DOTALL)
        assert cleaned == body


class TestTlNmRefresh:
    """Tests for nm section refresh during TL PR body injection."""

    def test_build_combined_review_with_nm_output(self):
        """When nm_output is non-empty, builds both TL Review and nm Review."""
        import pipeline as pl
        from unittest.mock import patch

        nm_output = "RISK: LOW\n\nSTAGE 1: Diff\nAll good."
        summary = {"risk": "LOW", "auto_fix_count": 0, "auto_fix_labels": [],
                   "key_findings": "All good.", "should_fix_items": []}

        tl_section = "\n\n## Review\n\n**Verdict:** APPROVED  \n**Risk:** LOW\n"
        existing_body = "## Description\n\nSome text"

        with patch.object(pl, '_extract_nm_summary', return_value=summary):
            combined, has_nm = pl._build_tl_review_body(
                existing_body, tl_section, nm_output
            )

        assert "## Review" in combined
        assert "### nm Review" in combined
        assert "All good." in combined
        assert has_nm is True

    def test_build_combined_review_without_nm_output(self):
        """When nm_output is empty, builds only TL Review without nm section."""
        import pipeline as pl

        tl_section = "\n\n## Review\n\n**Verdict:** APPROVED  \n**Risk:** LOW\n"
        existing_body = "## Description\n\nSome text"

        combined, has_nm = pl._build_tl_review_body(
            existing_body, tl_section, ""
        )

        assert "## Review" in combined
        assert "### nm Review" not in combined
        assert has_nm is False

    def test_build_combined_review_strips_old_nm(self):
        """When existing body has old nm section, it's stripped before rebuild."""
        import pipeline as pl
        from unittest.mock import patch

        nm_output = "RISK: LOW\n\nSTAGE 1: Diff\nFresh findings."
        summary = {"risk": "LOW", "auto_fix_count": 0, "auto_fix_labels": [],
                   "key_findings": "Fresh findings.", "should_fix_items": []}
        tl_section = "\n\n## Review\n\n**Verdict:** APPROVED  \n**Risk:** LOW\n"
        existing_body = "## Description\n\nSome text\n\n### nm Review\n\nOld nm content\n\n## Review\n\nOld TL content"

        with patch.object(pl, '_extract_nm_summary', return_value=summary):
            combined, has_nm = pl._build_tl_review_body(
                existing_body, tl_section, nm_output
            )

        assert "Old nm content" not in combined
        assert "Old TL content" not in combined
        assert "Fresh findings." in combined
        assert "### nm Review" in combined
        assert "## Review" in combined
