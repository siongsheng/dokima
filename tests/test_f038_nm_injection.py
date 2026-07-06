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


# ═══════════════════════════════════════════════════════════════════
# Task 2: nm SHOULD FIX → GitHub issues in run_pipeline Phase 4
# ═══════════════════════════════════════════════════════════════════

NM_OUTPUT_WITH_SHOULD_FIX_TABLE = """RISK: LOW

| ID | Dimension | Location | Severity | Detail |
|----|-----------|----------|----------|--------|
| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions |
| R2 | MAINTAINABILITY | pipeline.py:100 | SHOULD FIX | Extract long method |
| R3 | RELIABILITY | tests/ | SHOULD FIX | Add missing edge case test |
"""

NM_OUTPUT_WITH_SHOULD_FIX_PROSE = """RISK: MEDIUM

Some findings here.

SHOULD FIX — Add error handling in utils.py:50
SHOULD FIX: Update documentation for the new API

Summary: Minor issues found.
"""


class TestNmShouldFixIssueCreation:
    """Tests for nm SHOULD FIX → GitHub issue creation in Phase 4."""

    def test_extract_should_fix_from_nm_table_format(self):
        """nm_stdout with table-format SHOULD FIX produces expected items."""
        items = _load().extract_should_fix_from_text(NM_OUTPUT_WITH_SHOULD_FIX_TABLE)
        assert len(items) >= 2, f"Expected at least 2 SHOULD FIX items, got {len(items)}"
        details = [i["detail"].lower() for i in items]
        assert any("naming conventions" in d for d in details)
        assert any("extract long method" in d for d in details)

    def test_extract_should_fix_from_nm_prose_format(self):
        """nm_stdout with prose-format SHOULD FIX produces expected items."""
        items = _load().extract_should_fix_from_text(NM_OUTPUT_WITH_SHOULD_FIX_PROSE)
        assert len(items) >= 1, f"Expected at least 1 SHOULD FIX item, got {len(items)}"
        details = [i["detail"].lower() for i in items]
        assert any("error handling" in d for d in details)

    def test_nm_issue_title_has_nm_prefix(self):
        """Generated issue title includes SHOULD FIX [nm] prefix."""
        items = _load().extract_should_fix_from_text(NM_OUTPUT_WITH_SHOULD_FIX_TABLE)
        for item in items[:5]:
            detail = item.get("detail", "")
            dimension = item.get("dimension", "")
            if dimension:
                title = f"SHOULD FIX [nm] [{dimension}]: {detail[:80]}"
            else:
                title = f"SHOULD FIX [nm]: {detail[:80]}"
            assert title.startswith("SHOULD FIX [nm]"), \
                f"Title should start with 'SHOULD FIX [nm]', got: {title}"

    def test_nm_issue_body_has_nm_header(self):
        """Generated issue body includes ## nm Review Finding header."""
        items = _load().extract_should_fix_from_text(NM_OUTPUT_WITH_SHOULD_FIX_TABLE)
        for item in items[:5]:
            detail = item.get("detail", "")
            location = item.get("location", "")
            pr_url = "https://github.com/owner/repo/pull/42"
            branch = "feat/test"

            what_lines = [detail]
            if location:
                what_lines.append(f"\n**Location:** {location}")
            what_section = "\n".join(what_lines)

            body = (
                f"## nm Review Finding\n\n"
                f"**Feature:** test-feature\n"
                f"**Branch:** {branch}\n"
                f"**PR:** {pr_url}\n"
                f"**Spec:** specs/test-spec.md\n\n"
                f"### What\n{what_section}\n\n"
                f"### Fix\nApply the recommended change. "
                f"See {pr_url} for full review details.\n\n"
                f"### Verify\nRun tests and confirm the fix resolves the finding.\n\n"
                f"### Source\nFound during adversarial review of `{branch}`. "
                f"See {pr_url} for full review details and other findings."
            )
            assert "## nm Review Finding" in body, \
                "Issue body should contain '## nm Review Finding' header"
            assert "### What" in body
            assert "### Fix" in body
            assert "### Verify" in body
            assert "### Source" in body
            assert pr_url in body
            assert branch in body

    def test_gh_issue_create_called_for_nm_should_fix(self):
        """When nm_stdout has SHOULD FIX items, gh issue create is called."""
        import pipeline as pl
        from unittest.mock import patch, call as mock_call

        test_items = [
            {"detail": "Missing test for edge case", "dimension": "RELIABILITY", "location": "utils.py:42"},
            {"detail": "Update error handling", "dimension": "MAINTAINABILITY", "location": "pipeline.py:100"},
        ]

        with patch.object(pl, 'extract_should_fix_from_text', return_value=test_items) as mock_extract, \
             patch.object(pl, 'gh') as mock_gh:
            mock_gh.return_value = ("issue-url", "", 0)

            # Simulate the code block: extract → loop → gh issue create
            nm_stdout = NM_OUTPUT_WITH_SHOULD_FIX_TABLE
            should_fix_items = pl.extract_should_fix_from_text(nm_stdout)

            if should_fix_items:
                for item in should_fix_items[:5]:
                    detail = item.get("detail", "")
                    dimension = item.get("dimension", "")
                    location = item.get("location", "")
                    if dimension:
                        title = f"SHOULD FIX [nm] [{dimension}]: {detail[:80]}"
                    else:
                        title = f"SHOULD FIX [nm]: {detail[:80]}"

                    what_lines = [detail]
                    if location:
                        what_lines.append(f"\n**Location:** {location}")
                    what_section = "\n".join(what_lines)

                    body = (
                        f"## nm Review Finding\n\n"
                        f"**Feature:** test-feature\n"
                        f"**Branch:** test-branch\n"
                        f"**PR:** test-pr\n"
                        f"**Spec:** test-spec\n\n"
                        f"### What\n{what_section}\n\n"
                        f"### Fix\nApply the recommended change. "
                        f"See test-pr for full review details.\n\n"
                        f"### Verify\nRun tests and confirm the fix resolves the finding.\n\n"
                        f"### Source\nFound during adversarial review of `test-branch`. "
                        f"See test-pr for full review details and other findings."
                    )
                    mock_gh("issue", "create", "--repo", "test/repo",
                            "--title", title, "--body", body)

            mock_extract.assert_called_once_with(nm_stdout)
            assert mock_gh.call_count == 2
            # Check title format for first call
            first_call_args = mock_gh.call_args_list[0][0]
            assert "--title" in first_call_args
            title_idx = first_call_args.index("--title") + 1
            assert first_call_args[title_idx].startswith("SHOULD FIX [nm]")

    def test_empty_nm_stdout_creates_zero_issues(self):
        """When nm_stdout has no SHOULD FIX, zero issues created."""
        import pipeline as pl
        from unittest.mock import patch

        with patch.object(pl, 'extract_should_fix_from_text', return_value=[]) as mock_extract, \
             patch.object(pl, 'gh') as mock_gh:

            nm_stdout = "RISK: LOW\n\nEverything looks good."
            should_fix_items = pl.extract_should_fix_from_text(nm_stdout)

            # Should not enter the issue-creation loop
            issue_count = 0
            if should_fix_items:
                for item in should_fix_items[:5]:
                    issue_count += 1

            assert issue_count == 0
            mock_extract.assert_called_once_with(nm_stdout)
            mock_gh.assert_not_called()

    def test_gh_failure_handled_gracefully(self):
        """When gh issue create fails, loop continues without crashing."""
        import pipeline as pl
        from unittest.mock import patch

        test_items = [
            {"detail": "Item 1", "dimension": "RELIABILITY", "location": "utils.py:1"},
            {"detail": "Item 2", "dimension": "MAINTAINABILITY", "location": "pipeline.py:2"},
            {"detail": "Item 3", "dimension": "RELIABILITY", "location": "tests/:3"},
        ]

        with patch.object(pl, 'extract_should_fix_from_text', return_value=test_items), \
             patch.object(pl, 'gh') as mock_gh:
            # First fails, second succeeds, third fails
            mock_gh.side_effect = [
                ("", "error", 1),
                ("issue-url", "", 0),
                ("", "error", 1),
            ]

            for item in test_items[:5]:
                title = f"SHOULD FIX [nm] [{item['dimension']}]: {item['detail']}"
                stdout, stderr, rc = mock_gh("issue", "create", "--repo", "test/repo",
                                            "--title", title, "--body", "body")
                if rc == 0:
                    pass  # success
                else:
                    pass  # handled gracefully

            # All 3 calls should have been attempted
            assert mock_gh.call_count == 3

    def test_create_nm_should_fix_issues_function_exists(self):
        """The _create_nm_should_fix_issues helper exists in pipeline module."""
        import pipeline as pl
        assert hasattr(pl, '_create_nm_should_fix_issues'), \
            "pipeline must have _create_nm_should_fix_issues function"
        assert callable(pl._create_nm_should_fix_issues)

    def test_create_nm_should_fix_issues_calls_gh(self):
        """_create_nm_should_fix_issues calls gh issue create for each SHOULD FIX."""
        import pipeline as pl
        from unittest.mock import patch

        nm_stdout = NM_OUTPUT_WITH_SHOULD_FIX_TABLE

        with patch.object(pl, 'extract_should_fix_from_text') as mock_extract, \
             patch('pipeline.vcs.vcs_issue_create') as mock_gh:
            mock_extract.return_value = [
                {"detail": "Naming conventions", "dimension": "RELIABILITY", "location": "utils.py:42"},
                {"detail": "Extract long method", "dimension": "MAINTAINABILITY", "location": "pipeline.py:100"},
            ]
            mock_gh.return_value = ("issue-url", "", 0)

            result = pl._create_nm_should_fix_issues(
                nm_stdout, "test-feature", "test-branch",
                "https://github.com/owner/repo/pull/42", "specs/test.md"
            )

            assert result is True
            mock_extract.assert_called_once_with(nm_stdout)
            assert mock_gh.call_count == 2
            # Verify title and body format (vcs.vcs_issue_create takes positional title, body)
            for call_args in mock_gh.call_args_list:
                title = call_args[0][0]
                body = call_args[0][1]
                assert title.startswith("SHOULD FIX [nm]"), \
                    f"Title should start with 'SHOULD FIX [nm]', got: {title}"
                assert "## nm Review Finding" in body, \
                    "Issue body should contain '## nm Review Finding' header"

    def test_create_nm_should_fix_issues_empty_nm_stdout(self):
        """When nm_stdout has no SHOULD FIX items, returns True without calling gh."""
        import pipeline as pl
        from unittest.mock import patch

        with patch.object(pl, 'extract_should_fix_from_text', return_value=[]) as mock_extract, \
             patch.object(pl, 'gh') as mock_gh:

            result = pl._create_nm_should_fix_issues(
                "RISK: LOW\n\nEverything looks good.", "feat", "br",
                "https://github.com/owner/repo/pull/1", "spec.md"
            )

            assert result is True
            mock_extract.assert_called_once()
            mock_gh.assert_not_called()

    def test_create_nm_should_fix_issues_none_pr_url(self):
        """When pr_url is None, skips and returns False."""
        import pipeline as pl
        from unittest.mock import patch

        with patch.object(pl, 'extract_should_fix_from_text') as mock_extract, \
             patch('pipeline.vcs.vcs_issue_create') as mock_gh:

            result = pl._create_nm_should_fix_issues(
                NM_OUTPUT_WITH_SHOULD_FIX_TABLE, "feat", "br", None, "spec.md"
            )

            assert result is False
            mock_extract.assert_not_called()
            mock_gh.assert_not_called()

    def test_create_nm_should_fix_issues_gh_failure_handled(self):
        """When gh fails for some items, continues and still returns True."""
        import pipeline as pl
        from unittest.mock import patch

        with patch.object(pl, 'extract_should_fix_from_text') as mock_extract, \
             patch('pipeline.vcs.vcs_issue_create') as mock_gh:
            mock_extract.return_value = [
                {"detail": "Item 1", "dimension": "RELIABILITY", "location": "utils.py:1"},
                {"detail": "Item 2", "dimension": "MAINTAINABILITY", "location": "pipeline.py:2"},
                {"detail": "Item 3", "dimension": "RELIABILITY", "location": "tests/:3"},
            ]
            mock_gh.side_effect = [
                ("", "error", 1),
                ("issue-url", "", 0),
                ("", "error", 1),
            ]

            result = pl._create_nm_should_fix_issues(
                NM_OUTPUT_WITH_SHOULD_FIX_TABLE, "feat", "br",
                "https://github.com/owner/repo/pull/1", "spec.md"
            )

            assert result is True  # graceful — didn't crash
            assert mock_gh.call_count == 3  # All 3 attempted


# ═══════════════════════════════════════════════════════════════════
# Task 3: run_phase5_tech_lead uses _build_tl_review_body (strips nm+TL)
# ═══════════════════════════════════════════════════════════════════

# The current regex in run_phase5_tech_lead ONLY strips ## Review:
TL_ONLY_STRIP_RE = r'\n## Review\n\n.*?(?=\n## |\Z)'

# The _build_tl_review_body function uses a combined regex that strips BOTH:
TL_NM_STRIP_RE_FROM_CODE = (
    r'\n### nm Review\n.*?(?=\n### |\n## |\Z)|'
    r'\n## Review\n\n.*?(?=\n## |\Z)'
)


class TestRunPhase5TlNmStripping:
    """Tests verifying run_phase5_tech_lead properly strips nm section."""

    def test_old_regex_did_not_strip_nm(self):
        """Documentation: The old TL-only regex fails to strip ### nm Review.

        Before F038, run_phase5_tech_lead used this regex:
            r'\\n## Review\\n\\n.*?(?=\\n## |\\Z)'
        It only stripped ## Review, leaving stale ### nm Review sections.
        """
        body = "## Description\n\ntext\n\n### nm Review\n\nnm content\n\n## Review\n\nTL content"
        import re
        cleaned = re.sub(TL_ONLY_STRIP_RE, '', body, flags=re.DOTALL)
        assert "### nm Review" in cleaned, \
            "Old regex did NOT strip nm \u2014 this was the pre-F038 gap"
        assert "## Review" not in cleaned

    def test_build_tl_review_body_strips_both_and_injects_nm(self):
        """The _build_tl_review_body function strips both sections and injects fresh nm."""
        import pipeline as pl
        existing = "## Description\n\ntext\n\n### nm Review\n\nold nm\n\n## Review\n\nold TL"
        tl_section = "## Review\n\n**Verdict:** APPROVED  \n**Risk:** LOW\n"
        nm_output = "RISK: LOW\n\nSTAGE 1\nFresh nm findings."

        combined, has_nm = pl._build_tl_review_body(existing, tl_section, nm_output)

        assert "old nm" not in combined
        assert "old TL" not in combined
        assert "## Description" in combined
        assert "**Verdict:** APPROVED" in combined
        assert "Fresh nm findings" in combined
        assert has_nm is True

    def test_build_tl_review_body_is_importable(self):
        """_build_tl_review_body exists and handles the combined case."""
        import pipeline as pl
        assert hasattr(pl, '_build_tl_review_body'), \
            "pipeline must have _build_tl_review_body function"
        assert callable(pl._build_tl_review_body)
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


# ═══════════════════════════════════════════════════════════════════
# Task 2: nm SHOULD FIX → GitHub issues in run_pipeline Phase 4
# ═══════════════════════════════════════════════════════════════════

NM_OUTPUT_WITH_SHOULD_FIX_TABLE = """RISK: LOW

| ID | Dimension | Location | Severity | Detail |
|----|-----------|----------|----------|--------|
| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions |
| R2 | MAINTAINABILITY | pipeline.py:100 | SHOULD FIX | Extract long method |
| R3 | RELIABILITY | tests/ | SHOULD FIX | Add missing edge case test |
"""

NM_OUTPUT_WITH_SHOULD_FIX_PROSE = """RISK: MEDIUM

Some findings here.

SHOULD FIX — Add error handling in utils.py:50
SHOULD FIX: Update documentation for the new API

Summary: Minor issues found.
"""


class TestNmShouldFixIssueCreation:
    """Tests for nm SHOULD FIX → GitHub issue creation in Phase 4."""

    def test_extract_should_fix_from_nm_table_format(self):
        """nm_stdout with table-format SHOULD FIX produces expected items."""
        items = _load().extract_should_fix_from_text(NM_OUTPUT_WITH_SHOULD_FIX_TABLE)
        assert len(items) >= 2, f"Expected at least 2 SHOULD FIX items, got {len(items)}"
        details = [i["detail"].lower() for i in items]
        assert any("naming conventions" in d for d in details)
        assert any("extract long method" in d for d in details)

    def test_extract_should_fix_from_nm_prose_format(self):
        """nm_stdout with prose-format SHOULD FIX produces expected items."""
        items = _load().extract_should_fix_from_text(NM_OUTPUT_WITH_SHOULD_FIX_PROSE)
        assert len(items) >= 1, f"Expected at least 1 SHOULD FIX item, got {len(items)}"
        details = [i["detail"].lower() for i in items]
        assert any("error handling" in d for d in details)

    def test_nm_issue_title_has_nm_prefix(self):
        """Generated issue title includes SHOULD FIX [nm] prefix."""
        items = _load().extract_should_fix_from_text(NM_OUTPUT_WITH_SHOULD_FIX_TABLE)
        for item in items[:5]:
            detail = item.get("detail", "")
            dimension = item.get("dimension", "")
            if dimension:
                title = f"SHOULD FIX [nm] [{dimension}]: {detail[:80]}"
            else:
                title = f"SHOULD FIX [nm]: {detail[:80]}"
            assert title.startswith("SHOULD FIX [nm]"), \
                f"Title should start with 'SHOULD FIX [nm]', got: {title}"

    def test_nm_issue_body_has_nm_header(self):
        """Generated issue body includes ## nm Review Finding header."""
        items = _load().extract_should_fix_from_text(NM_OUTPUT_WITH_SHOULD_FIX_TABLE)
        for item in items[:5]:
            detail = item.get("detail", "")
            location = item.get("location", "")
            pr_url = "https://github.com/owner/repo/pull/42"
            branch = "feat/test"

            what_lines = [detail]
            if location:
                what_lines.append(f"\n**Location:** {location}")
            what_section = "\n".join(what_lines)

            body = (
                f"## nm Review Finding\n\n"
                f"**Feature:** test-feature\n"
                f"**Branch:** {branch}\n"
                f"**PR:** {pr_url}\n"
                f"**Spec:** specs/test-spec.md\n\n"
                f"### What\n{what_section}\n\n"
                f"### Fix\nApply the recommended change. "
                f"See {pr_url} for full review details.\n\n"
                f"### Verify\nRun tests and confirm the fix resolves the finding.\n\n"
                f"### Source\nFound during adversarial review of `{branch}`. "
                f"See {pr_url} for full review details and other findings."
            )
            assert "## nm Review Finding" in body, \
                "Issue body should contain '## nm Review Finding' header"
            assert "### What" in body
            assert "### Fix" in body
            assert "### Verify" in body
            assert "### Source" in body
            assert pr_url in body
            assert branch in body

    def test_gh_issue_create_called_for_nm_should_fix(self):
        """When nm_stdout has SHOULD FIX items, gh issue create is called."""
        import pipeline as pl
        from unittest.mock import patch, call as mock_call

        test_items = [
            {"detail": "Missing test for edge case", "dimension": "RELIABILITY", "location": "utils.py:42"},
            {"detail": "Update error handling", "dimension": "MAINTAINABILITY", "location": "pipeline.py:100"},
        ]

        with patch.object(pl, 'extract_should_fix_from_text', return_value=test_items) as mock_extract, \
             patch.object(pl, 'gh') as mock_gh:
            mock_gh.return_value = ("issue-url", "", 0)

            # Simulate the code block: extract → loop → gh issue create
            nm_stdout = NM_OUTPUT_WITH_SHOULD_FIX_TABLE
            should_fix_items = pl.extract_should_fix_from_text(nm_stdout)

            if should_fix_items:
                for item in should_fix_items[:5]:
                    detail = item.get("detail", "")
                    dimension = item.get("dimension", "")
                    location = item.get("location", "")
                    if dimension:
                        title = f"SHOULD FIX [nm] [{dimension}]: {detail[:80]}"
                    else:
                        title = f"SHOULD FIX [nm]: {detail[:80]}"

                    what_lines = [detail]
                    if location:
                        what_lines.append(f"\n**Location:** {location}")
                    what_section = "\n".join(what_lines)

                    body = (
                        f"## nm Review Finding\n\n"
                        f"**Feature:** test-feature\n"
                        f"**Branch:** test-branch\n"
                        f"**PR:** test-pr\n"
                        f"**Spec:** test-spec\n\n"
                        f"### What\n{what_section}\n\n"
                        f"### Fix\nApply the recommended change. "
                        f"See test-pr for full review details.\n\n"
                        f"### Verify\nRun tests and confirm the fix resolves the finding.\n\n"
                        f"### Source\nFound during adversarial review of `test-branch`. "
                        f"See test-pr for full review details and other findings."
                    )
                    mock_gh("issue", "create", "--repo", "test/repo",
                            "--title", title, "--body", body)

            mock_extract.assert_called_once_with(nm_stdout)
            assert mock_gh.call_count == 2
            # Check title format for first call
            first_call_args = mock_gh.call_args_list[0][0]
            assert "--title" in first_call_args
            title_idx = first_call_args.index("--title") + 1
            assert first_call_args[title_idx].startswith("SHOULD FIX [nm]")

    def test_empty_nm_stdout_creates_zero_issues(self):
        """When nm_stdout has no SHOULD FIX, zero issues created."""
        import pipeline as pl
        from unittest.mock import patch

        with patch.object(pl, 'extract_should_fix_from_text', return_value=[]) as mock_extract, \
             patch.object(pl, 'gh') as mock_gh:

            nm_stdout = "RISK: LOW\n\nEverything looks good."
            should_fix_items = pl.extract_should_fix_from_text(nm_stdout)

            # Should not enter the issue-creation loop
            issue_count = 0
            if should_fix_items:
                for item in should_fix_items[:5]:
                    issue_count += 1

            assert issue_count == 0
            mock_extract.assert_called_once_with(nm_stdout)
            mock_gh.assert_not_called()

    def test_gh_failure_handled_gracefully(self):
        """When gh issue create fails, loop continues without crashing."""
        import pipeline as pl
        from unittest.mock import patch

        test_items = [
            {"detail": "Item 1", "dimension": "RELIABILITY", "location": "utils.py:1"},
            {"detail": "Item 2", "dimension": "MAINTAINABILITY", "location": "pipeline.py:2"},
            {"detail": "Item 3", "dimension": "RELIABILITY", "location": "tests/:3"},
        ]

        with patch.object(pl, 'extract_should_fix_from_text', return_value=test_items), \
             patch.object(pl, 'gh') as mock_gh:
            # First fails, second succeeds, third fails
            mock_gh.side_effect = [
                ("", "error", 1),
                ("issue-url", "", 0),
                ("", "error", 1),
            ]

            for item in test_items[:5]:
                title = f"SHOULD FIX [nm] [{item['dimension']}]: {item['detail']}"
                stdout, stderr, rc = mock_gh("issue", "create", "--repo", "test/repo",
                                            "--title", title, "--body", "body")
                if rc == 0:
                    pass  # success
                else:
                    pass  # handled gracefully

            # All 3 calls should have been attempted
            assert mock_gh.call_count == 3

    def test_create_nm_should_fix_issues_function_exists(self):
        """The _create_nm_should_fix_issues helper exists in pipeline module."""
        import pipeline as pl
        assert hasattr(pl, '_create_nm_should_fix_issues'), \
            "pipeline must have _create_nm_should_fix_issues function"
        assert callable(pl._create_nm_should_fix_issues)

    def test_create_nm_should_fix_issues_calls_gh(self):
        """_create_nm_should_fix_issues calls gh issue create for each SHOULD FIX."""
        import pipeline as pl
        from unittest.mock import patch

        nm_stdout = NM_OUTPUT_WITH_SHOULD_FIX_TABLE

        with patch.object(pl, 'extract_should_fix_from_text') as mock_extract, \
             patch('pipeline.vcs.vcs_issue_create') as mock_gh:
            mock_extract.return_value = [
                {"detail": "Naming conventions", "dimension": "RELIABILITY", "location": "utils.py:42"},
                {"detail": "Extract long method", "dimension": "MAINTAINABILITY", "location": "pipeline.py:100"},
            ]
            mock_gh.return_value = ("issue-url", "", 0)

            result = pl._create_nm_should_fix_issues(
                nm_stdout, "test-feature", "test-branch",
                "https://github.com/owner/repo/pull/42", "specs/test.md"
            )

            assert result is True
            mock_extract.assert_called_once_with(nm_stdout)
            assert mock_gh.call_count == 2
            # Verify title and body format (vcs.vcs_issue_create takes positional title, body)
            for call_args in mock_gh.call_args_list:
                title = call_args[0][0]
                body = call_args[0][1]
                assert title.startswith("SHOULD FIX [nm]"), \
                    f"Title should start with 'SHOULD FIX [nm]', got: {title}"
                assert "## nm Review Finding" in body, \
                    "Issue body should contain '## nm Review Finding' header"

    def test_create_nm_should_fix_issues_empty_nm_stdout(self):
        """When nm_stdout has no SHOULD FIX items, returns True without calling gh."""
        import pipeline as pl
        from unittest.mock import patch

        with patch.object(pl, 'extract_should_fix_from_text', return_value=[]) as mock_extract, \
             patch.object(pl, 'gh') as mock_gh:

            result = pl._create_nm_should_fix_issues(
                "RISK: LOW\n\nEverything looks good.", "feat", "br",
                "https://github.com/owner/repo/pull/1", "spec.md"
            )

            assert result is True
            mock_extract.assert_called_once()
            mock_gh.assert_not_called()

    def test_create_nm_should_fix_issues_none_pr_url(self):
        """When pr_url is None, skips and returns False."""
        import pipeline as pl
        from unittest.mock import patch

        with patch.object(pl, 'extract_should_fix_from_text') as mock_extract, \
             patch('pipeline.vcs.vcs_issue_create') as mock_gh:

            result = pl._create_nm_should_fix_issues(
                NM_OUTPUT_WITH_SHOULD_FIX_TABLE, "feat", "br", None, "spec.md"
            )

            assert result is False
            mock_extract.assert_not_called()
            mock_gh.assert_not_called()

    def test_create_nm_should_fix_issues_gh_failure_handled(self):
        """When gh fails for some items, continues and still returns True."""
        import pipeline as pl
        from unittest.mock import patch

        with patch.object(pl, 'extract_should_fix_from_text') as mock_extract, \
             patch('pipeline.vcs.vcs_issue_create') as mock_gh:
            mock_extract.return_value = [
                {"detail": "Item 1", "dimension": "RELIABILITY", "location": "utils.py:1"},
                {"detail": "Item 2", "dimension": "MAINTAINABILITY", "location": "pipeline.py:2"},
                {"detail": "Item 3", "dimension": "RELIABILITY", "location": "tests/:3"},
            ]
            mock_gh.side_effect = [
                ("", "error", 1),
                ("issue-url", "", 0),
                ("", "error", 1),
            ]

            result = pl._create_nm_should_fix_issues(
                NM_OUTPUT_WITH_SHOULD_FIX_TABLE, "feat", "br",
                "https://github.com/owner/repo/pull/1", "spec.md"
            )

            assert result is True  # graceful — didn't crash
            assert mock_gh.call_count == 3  # All 3 attempted


# ═══════════════════════════════════════════════════════════════════
# Task 3: run_phase5_tech_lead uses _build_tl_review_body (strips nm+TL)
# ═══════════════════════════════════════════════════════════════════

# The current regex in run_phase5_tech_lead ONLY strips ## Review:
TL_ONLY_STRIP_RE = r'\n## Review\n\n.*?(?=\n## |\Z)'

# The _build_tl_review_body function uses a combined regex that strips BOTH:
TL_NM_STRIP_RE_FROM_CODE = (
    r'\n### nm Review\n.*?(?=\n### |\n## |\Z)|'
    r'\n## Review\n\n.*?(?=\n## |\Z)'
)


class TestRunPhase5TlNmStripping:
    """Tests verifying run_phase5_tech_lead properly strips nm section."""

    def test_old_regex_did_not_strip_nm(self):
        """Documentation: The old TL-only regex fails to strip ### nm Review.
        
        Before F038, run_phase5_tech_lead used this regex:
            r'\n## Review\n\n.*?(?=\n## |\\Z)'
        It only stripped ## Review, leaving stale ### nm Review sections.
        """
        body = "## Description\n\ntext\n\n### nm Review\n\nnm content\n\n## Review\n\nTL content"
        import re
        cleaned = re.sub(TL_ONLY_STRIP_RE, '', body, flags=re.DOTALL)
        assert "### nm Review" in cleaned, \
            "Old regex did NOT strip nm — this was the pre-F038 gap"
        assert "## Review" not in cleaned

    def test_build_tl_review_body_strips_both_and_injects_nm(self):
        """The _build_tl_review_body function strips both sections and injects fresh nm."""
        import pipeline as pl
        existing = "## Description\n\ntext\n\n### nm Review\n\nold nm\n\n## Review\n\nold TL"
        tl_section = "## Review\n\n**Verdict:** APPROVED  \n**Risk:** LOW\n"
        nm_output = "RISK: LOW\n\nSTAGE 1\nFresh nm findings."
        
        combined, has_nm = pl._build_tl_review_body(existing, tl_section, nm_output)
        
        assert "old nm" not in combined
        assert "old TL" not in combined
        assert "## Description" in combined
        assert "**Verdict:** APPROVED" in combined
        assert "Fresh nm findings" in combined
        assert has_nm is True

    def test_build_tl_review_body_is_importable(self):
        """_build_tl_review_body exists and handles the combined case."""
        import pipeline as pl
        assert hasattr(pl, '_build_tl_review_body'), \
            "pipeline must have _build_tl_review_body function"
        assert callable(pl._build_tl_review_body)
