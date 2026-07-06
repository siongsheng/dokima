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

SHOULD FIX items:
- [RELIABILITY] utils.py:42: Naming conventions for internal functions
- [RELIABILITY] pipeline.py:100: Extract long method
- [MAINTAINABILITY] tests/: Add missing edge case test

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
