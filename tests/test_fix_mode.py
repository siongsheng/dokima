"""Tests for --fix mode: BLOCKED PR discovery, blocker extraction."""
import json
import os
import sys
from unittest.mock import patch, MagicMock

from conftest import _load_panel as _load


# ═══════════════════════════════════════════════════════════════════
# Task 3: discover_blocked_pr()
# ═══════════════════════════════════════════════════════════════════


def test_discover_blocked_pr_none(panel):
    """No BLOCKED PRs → returns None."""
    mock_stdout = "[]\n"
    with patch.object(panel, 'gh', return_value=(mock_stdout.strip(), "", 0)):
        result = panel.discover_blocked_pr()
        assert result is None


def test_discover_blocked_pr_found(panel):
    """One BLOCKED PR detected by title [BLOCKED] → returns dict."""
    pr_json = json.dumps([
        {"number": 42, "title": "[BLOCKED] Fix login bug", "body": "PR body",
         "headRefName": "feat/fix-login", "updatedAt": "2026-06-25T10:00:00Z"}
    ])
    with patch.object(panel, 'gh', return_value=(pr_json, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is not None
        assert result["number"] == 42
        assert result["headRefName"] == "feat/fix-login"


def test_discover_blocked_pr_detects_verdict(panel):
    """PR has VERDICT: BLOCKED in body → detected."""
    pr_json = json.dumps([
        {"number": 7, "title": "Some feature", "body": "## Review\n**Verdict:** BLOCKED",
         "headRefName": "feat/some", "updatedAt": "2026-06-25T09:00:00Z"}
    ])
    with patch.object(panel, 'gh', return_value=(pr_json, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is not None
        assert result["number"] == 7


def test_discover_blocked_pr_detects_blockers_section(panel):
    """PR has ### Blockers section → detected as BLOCKED."""
    pr_json = json.dumps([
        {"number": 13, "title": "Some feature", "body": "### Blockers\n- Bug here",
         "headRefName": "feat/some", "updatedAt": "2026-06-25T08:00:00Z"}
    ])
    with patch.object(panel, 'gh', return_value=(pr_json, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is not None
        assert result["number"] == 13


def test_discover_blocked_pr_multiple(panel):
    """Multiple BLOCKED PRs → picks most recent."""
    pr_json = json.dumps([
        {"number": 10, "title": "[BLOCKED] Old one", "body": "", "headRefName": "feat/old",
         "updatedAt": "2026-06-24T10:00:00Z"},
        {"number": 11, "title": "[BLOCKED] New one", "body": "", "headRefName": "feat/new",
         "updatedAt": "2026-06-25T10:00:00Z"},
    ])
    with patch.object(panel, 'gh', return_value=(pr_json, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is not None
        assert result["number"] == 11  # Most recent


# ═══════════════════════════════════════════════════════════════════
# Task 4: extract_blockers_from_pr()
# ═══════════════════════════════════════════════════════════════════


def test_extract_blockers_standard_section(panel):
    """### Blockers section → extracts list items."""
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- Login test fails
- Missing error handling
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert len(result) == 2
    assert "Login test fails" in result


def test_extract_blockers_empty(panel):
    """No blockers found → returns empty list."""
    pr_body = "## Review\n**Verdict:** BLOCKED\n"
    result = panel.extract_blockers_from_pr(pr_body)
    assert result == []


def test_extract_blockers_no_blockers_section(panel):
    """No ### Blockers section → returns empty (caller handles)."""
    pr_body = "Just some PR description."
    result = panel.extract_blockers_from_pr(pr_body)
    assert result == []


def test_extract_blockers_architectural_filtered(panel):
    """ARCHITECTURAL blockers are excluded from result."""
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- Login test fails
- ARCHITECTURAL: Need to restructure DB schema
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert len(result) == 1
    assert "Login test fails" in result


def test_extract_blockers_all_architectural(panel):
    """All architectural → returns empty list (caller checks separately)."""
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- ARCHITECTURAL: Redesign the whole system
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert result == []
