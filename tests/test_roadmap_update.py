"""Tests for update_roadmap_status()."""
import os
import pytest

def test_pending_to_in_progress(panel, fake_roadmap):
    content = "### F001: Login\n**Priority:** P0\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** T.\n"
    p = fake_roadmap(content)
    panel.update_roadmap_status(p, "F001", "in_progress")
    with open(p) as f:
        result = f.read()
    assert "[~] In Progress" in result
    assert "[ ] Pending" not in result

def test_in_progress_to_done(panel, fake_roadmap):
    content = "### F001: Login\n**Priority:** P0\n**Dependencies:** None\n**Status:** [~] In Progress\n**User Story:** T.\n"
    p = fake_roadmap(content)
    panel.update_roadmap_status(p, "F001", "done")
    with open(p) as f:
        result = f.read()
    assert "[x] Done" in result
    assert "[~] In Progress" not in result

def test_done_to_pending_revert(panel, fake_roadmap):
    content = "### F001: Login\n**Priority:** P0\n**Dependencies:** None\n**Status:** [x] Done\n**User Story:** T.\n"
    p = fake_roadmap(content)
    panel.update_roadmap_status(p, "F001", "pending")
    with open(p) as f:
        result = f.read()
    assert "[ ] Pending" in result
    assert "[x] Done" not in result

def test_feature_not_found_no_change(panel, fake_roadmap):
    content = "### F001: Login\n**Priority:** P0\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** T.\n"
    p = fake_roadmap(content)
    panel.update_roadmap_status(p, "F999", "done")
    with open(p) as f:
        result = f.read()
    assert result == content  # unchanged

def test_file_not_found_no_crash(panel):
    # Should not raise
    panel.update_roadmap_status("/nonexistent/roadmap.md", "F001", "done")


# ── F045: Single-feature-only update tests ──

def test_only_target_feature_updated(panel, fake_roadmap):
    """F045: Updating F001 does not change F002's status."""
    content = (
        "### F001: Login\n**Priority:** P0\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** T.\n\n"
        "### F002: Dashboard\n**Priority:** P1\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** T.\n"
    )
    p = fake_roadmap(content)
    panel.update_roadmap_status(p, "F001", "done")
    with open(p) as f:
        result = f.read()
    # F001 should be done
    assert "[x] Done" in result
    # F002 should still be pending
    assert "F002: Dashboard" in result
    # Count status markers — should have one [x] and one [ ]
    assert result.count("[x] Done") == 1
    assert result.count("[ ] Pending") == 1


def test_multiple_features_in_file_staged_correctly(panel, fake_roadmap):
    """F045: After updating F001, only F001's status line changes — all other lines identical."""
    content = (
        "### F001: Login\n**Priority:** P0\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** T.\n\n"
        "### F002: Dashboard\n**Priority:** P1\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** T.\n"
    )
    p = fake_roadmap(content)
    panel.update_roadmap_status(p, "F001", "done")
    with open(p) as f:
        result = f.read()

    # Split both into lines and compare
    original_lines = content.split("\n")
    result_lines = result.split("\n")
    assert len(original_lines) == len(result_lines), "Line count changed"

    diff_count = 0
    for i, (orig, res) in enumerate(zip(original_lines, result_lines)):
        if orig != res:
            diff_count += 1
            # Only the F001 status line should differ
            assert "Status:" in orig, f"Unexpected change at line {i}: {orig!r} → {res!r}"

    assert diff_count == 1, f"Expected 1 changed line, got {diff_count}"
