# Task Breakdown: F041: Split utils.py into domain modules — git_ops.py (git, gh wrappers), spec_extract.py (extract_pr_sections, extract_issue_sections, clean_spec_content), codebase_map.py (generate_codebase_map, _build_domain_map, _build_impact_map), control_panel.py (handle_status, handle_stop, handle_kill). 3,351 lines → ~4 × 800-line modules.

### Task 1: Create git_ops.py — extract VCS, token, and release functions from utils.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Create git_ops.py — extract VCS, token, and release functions from utils.py

### Task 2: Create spec_extract.py — extract text processing functions from utils.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Create spec_extract.py — extract text processing functions from utils.py

### Task 3: Create codebase_map.py — extract map generation functions from utils.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Create codebase_map.py — extract map generation functions from utils.py

### Task 4: Create control_panel.py — extract CLI control, status, and help from utils.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Create control_panel.py — extract CLI control, status, and help from utils.py

### Task 5: Add inter-module imports — wire new modules to import from each other
**Files:** from spec
**Dependencies:** [none]
**Description:** Add inter-module imports — wire new modules to import from each other

### Task 6: Update pipeline.py imports — import from 4 new modules instead of utils
**Files:** from spec
**Dependencies:** [none]
**Description:** Update pipeline.py imports — import from 4 new modules instead of utils

### Task 7: Update agent.py imports — import from git_ops.py instead of utils
**Files:** from spec
**Dependencies:** [none]
**Description:** Update agent.py imports — import from git_ops.py instead of utils

### Task 8: Update roadmap.py imports — import from 4 new modules instead of utils
**Files:** from spec
**Dependencies:** [none]
**Description:** Update roadmap.py imports — import from 4 new modules instead of utils

### Task 9: Update tasks.py imports — import from git_ops.py instead of utils
**Files:** from spec
**Dependencies:** [none]
**Description:** Update tasks.py imports — import from git_ops.py instead of utils

### Task 10: Update dokima entry script imports — import from 4 new modules
**Files:** from spec
**Dependencies:** [none]
**Description:** Update dokima entry script imports — import from 4 new modules

### Task 11: Update all test file imports — 14 files, pure import path changes
**Files:** from spec
**Dependencies:** [none]
**Description:** Update all test file imports — 14 files, pure import path changes

### Task 12: Run full test suite — verify all 1,029 tests pass
**Files:** from spec
**Dependencies:** [none]
**Description:** Run full test suite — verify all 1,029 tests pass
