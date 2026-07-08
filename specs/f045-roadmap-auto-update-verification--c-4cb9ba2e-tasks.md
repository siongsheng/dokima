# Task Breakdown: F045: Roadmap auto-update verification — `commit_roadmap_update()` marks features Done without verifying implementation exists. When a pipeline merges, it updates ALL feature statuses in roadmap.md — including unrelated ones. Fix: only update the specific feature that was built, and verify source changes exist before marking Done.

### Task 1: Extract _has_code_changes() helper from auto_repair_status
**Files:** roadmap.py
**Dependencies:** [none]
**Description:** Extract _has_code_changes() helper from auto_repair_status

### Task 2: Add verification gate to commit_roadmap_update() for "done" action
**Files:** roadmap.py
**Dependencies:** 1
**Description:** Add verification gate to commit_roadmap_update() for "done" action

### Task 3: Wire pr_url from pipeline.py callers into commit_roadmap_update()
**Files:** pipeline.py
**Dependencies:** 2
**Description:** Wire pr_url from pipeline.py callers into commit_roadmap_update()

### Task 4: Add tests for verification gate
**Files:** tests/test_helpers.py
**Dependencies:** 3
**Description:** Add tests for verification gate

### Task 5: Add single-feature-only update test
**Files:** tests/test_roadmap_update.py
**Dependencies:** 3
**Description:** Add single-feature-only update test

### Task 6: Run full test suite and verify zero regressions
**Files:** tests/
**Dependencies:** 4, 5
**Description:** Run full test suite and verify zero regressions
