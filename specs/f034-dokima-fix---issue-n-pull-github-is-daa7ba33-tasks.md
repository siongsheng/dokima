# Task Breakdown: F034: dokima fix --issue N: pull GitHub issue body, extract file/line/fix/verify from structured format, spawn coder to implement. Also upgrade SHOULD FIX issue creation to include What/Fix/Verify sections for coder-readability.

### Task 1: Add --issue N argument to fix subparser in CLI entry point
**Files:** dokima
**Dependencies:** [none]
**Description:** Add --issue N argument to fix subparser in CLI entry point

### Task 2: Implement extract_issue_sections() in utils.py
**Files:** utils.py
**Dependencies:** [none]
**Description:** Implement extract_issue_sections() in utils.py

### Task 3: Implement run_fix_mode_issue() in pipeline.py
**Files:** pipeline.py
**Dependencies:** 2
**Description:** Implement run_fix_mode_issue() in pipeline.py

### Task 4: Upgrade SHOULD FIX issue body template in run_phase5_tech_lead()
**Files:** pipeline.py
**Dependencies:** 2
**Description:** Upgrade SHOULD FIX issue body template in run_phase5_tech_lead()

### Task 5: Add tests for --issue mode
**Files:** tests/test_fix_mode.py
**Dependencies:** 2, 3
**Description:** Add tests for --issue mode

### Task 6: Add tests for upgraded SHOULD FIX issue body format
**Files:** tests/test_f036_should_fix_extraction.py
**Dependencies:** 4
**Description:** Add tests for upgraded SHOULD FIX issue body format
