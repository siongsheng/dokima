# Task Breakdown: F013: Vendor-Agnostic Model Config

### Task 1: Add vendor model maps constant
**Files:** dokima
**Dependencies:** [none]
**Description:** Add vendor model maps constant

### Task 2: Add _build_profile_configs() function
**Files:** dokima
**Dependencies:** 1
**Description:** Add _build_profile_configs() function

### Task 3: Wire vendor config into ensure_profiles()
**Files:** dokima
**Dependencies:** 2
**Description:** Wire vendor config into ensure_profiles()

### Task 4: Add vendor info to startup output in main()
**Files:** dokima
**Dependencies:** 2
**Description:** Add vendor info to startup output in main()

### Task 5: Update test_profile_templates.py for vendor-agnostic configs
**Files:** tests/test_profile_templates.py
**Dependencies:** 2, 3
**Description:** Update test_profile_templates.py for vendor-agnostic configs

### Task 6: Update conventions.md model compatibility table
**Files:** specs/conventions.md
**Dependencies:** 1
**Description:** Update conventions.md model compatibility table

### Task 7: Add PANEL_VENDOR and PANEL_MODEL_* to HELP_JSON env vars block
**Files:** dokima
**Dependencies:** 1
**Description:** Add PANEL_VENDOR and PANEL_MODEL_* to HELP_JSON env vars block
