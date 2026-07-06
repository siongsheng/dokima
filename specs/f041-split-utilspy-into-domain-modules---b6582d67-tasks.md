# Task Breakdown: F041: Split utils.py into domain modules — git_ops.py (git, gh wrappers), spec_extract.py (extract_pr_sections, extract_issue_sections, clean_spec_content), codebase_map.py (generate_codebase_map, _build_domain_map, _build_impact_map), control_panel.py (handle_status, handle_stop, handle_kill). 3,351 lines → ~4 × 800-line modules.

### Task 1: Create git_ops.py — extract git/GitHub wrappers
**Files:** from spec
**Dependencies:** [none]
**Description:** Create git_ops.py — extract git/GitHub wrappers

### Task 2: Create spec_extract.py — extract text parsing functions
**Files:** from spec
**Dependencies:** [none]
**Description:** Create spec_extract.py — extract text parsing functions

### Task 3: Create codebase_map.py — extract codebase introspection
**Files:** from spec
**Dependencies:** [none]
**Description:** Create codebase_map.py — extract codebase introspection

### Task 4: Create control_panel.py — extract CLI handlers
**Files:** from spec
**Dependencies:** [none]
**Description:** Create control_panel.py — extract CLI handlers

### Task 5: Update test imports and verify test suite
**Files:** from spec
**Dependencies:** [none]
**Description:** Update test imports and verify test suite

### Task 6: Run full CI verification
**Files:** from spec
**Dependencies:** [none]
**Description:** Run full CI verification
