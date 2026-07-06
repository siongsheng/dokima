# Task Breakdown: F041: Split utils.py into domain modules — git_ops.py (git, gh wrappers), spec_extract.py (extract_pr_sections, extract_issue_sections, clean_spec_content), codebase_map.py (generate_codebase_map, _build_domain_map, _build_impact_map), control_panel.py (handle_status, handle_stop, handle_kill). 3,351 lines → ~4 × 800-line modules.

### Task 1: Create git_ops.py — extract git/GH wrappers
**Files:** utils.py, git_ops.py
**Dependencies:** [none]
**Description:** Create git_ops.py — extract git/GH wrappers

### Task 2: Create spec_extract.py — extract spec parsing functions
**Files:** utils.py, spec_extract.py
**Dependencies:** 1
**Description:** Create spec_extract.py — extract spec parsing functions

### Task 3: Create codebase_map.py — extract map generation functions
**Files:** utils.py, codebase_map.py
**Dependencies:** 2
**Description:** Create codebase_map.py — extract map generation functions

### Task 4: Create control_panel.py — extract control panel handlers
**Files:** utils.py, control_panel.py
**Dependencies:** 3
**Description:** Create control_panel.py — extract control panel handlers

### Task 5: Update importers across pipeline.py, agent.py, tasks.py, roadmap.py, dokima
**Files:** pipeline.py, agent.py, tasks.py, roadmap.py, dokima
**Dependencies:** 4
**Description:** Update importers across pipeline.py, agent.py, tasks.py, roadmap.py, dokima

### Task 6: Verify — run full test suite, build, lint
**Files:** tests/*.py
**Dependencies:** 5
**Description:** Verify — run full test suite, build, lint
