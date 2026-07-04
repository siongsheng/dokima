# Task Breakdown: F033: Cross-run learning via conventions.md: when TL blocks a PR for a pattern violation, append a one-line rule to conventions.md. Next strategist reads it. No vector DB, no pattern extraction — human-readable rules that compound.

### Task 1: Add _extract_convention_candidates() to utils.py
**Files:** utils.py
**Dependencies:** [none]
**Description:** Add _extract_convention_candidates() to utils.py

### Task 2: Add _append_convention_rules() to utils.py
**Files:** utils.py
**Dependencies:** 1
**Description:** Add _append_convention_rules() to utils.py

### Task 3: Wire hook into run_phase5_tech_lead() in pipeline.py
**Files:** pipeline.py
**Dependencies:** 2
**Description:** Wire hook into run_phase5_tech_lead() in pipeline.py

### Task 4: Import new functions in pipeline.py
**Files:** pipeline.py
**Dependencies:** 2
**Description:** Import new functions in pipeline.py

### Task 5: Write tests for convention extraction
**Files:** tests/test_f033_conventions.py
**Dependencies:** 1
**Description:** Write tests for convention extraction

### Task 6: Write tests for convention append + dedup
**Files:** tests/test_f033_conventions.py
**Dependencies:** 2, 5
**Description:** Write tests for convention append + dedup

### Task 7: Update AGENTS.md conventions section
**Files:** AGENTS.md
**Dependencies:** 4
**Description:** Update AGENTS.md conventions section
