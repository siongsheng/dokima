# Task Breakdown: F037: Blocker Resolution Tracking — cross-reference fix PRs to the original blocker PR they resolve. After completes and TL approves, auto-update the original PR's section with strikethrough + link to the resolution PR. Optionally create GitHub issues from blockers (matching SHOULD FIX pattern) and auto-close them when the fix PR merges.

### Task 1: Add vcs_pr_update_body() to VCS abstraction layer
**Files:** from spec
**Dependencies:** [none]
**Description:** Add vcs_pr_update_body() to VCS abstraction layer

### Task 2: Add format_blocker_cross_reference() helper to utils.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Add format_blocker_cross_reference() helper to utils.py

### Task 3: Add create_blocker_issues() to pipeline.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Add create_blocker_issues() to pipeline.py

### Task 4: Add post-fix PR body update to run_fix_mode()
**Files:** from spec
**Dependencies:** [none]
**Description:** Add post-fix PR body update to run_fix_mode()

### Task 5: Add auto_close_referenced_issues() to pipeline.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Add auto_close_referenced_issues() to pipeline.py

### Task 6: Wire flag parsing for --create-blocker-issues
**Files:** from spec
**Dependencies:** [none]
**Description:** Wire flag parsing for --create-blocker-issues

### Task 7: Add test file tests/test_f037_blocker_resolution.py
**Files:** vcs.py
**Dependencies:** [none]
**Description:** Add test file tests/test_f037_blocker_resolution.py
