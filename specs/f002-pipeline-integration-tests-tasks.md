# Task Breakdown: F002: Pipeline Integration Tests

### Task 1: Move select import to module level
**Files:** dokima
**Dependencies:** [none]
**Description:** Move select import to module level

### Task 2: Extract _read_stdin_with_timeout() helper function
**Files:** dokima
**Dependencies:** 1
**Description:** Extract _read_stdin_with_timeout() helper function

### Task 3: Add PANEL_NO_LOCK env var to bypass flock in acquire_lock()
**Files:** dokima
**Dependencies:** [none]
**Description:** Add PANEL_NO_LOCK env var to bypass flock in acquire_lock()

### Task 4: Ensure PANEL_MAX_RETRIES=0 short-circuits all retry paths
**Files:** dokima
**Dependencies:** [none]
**Description:** Ensure PANEL_MAX_RETRIES=0 short-circuits all retry paths

### Task 5: Unskip 5 blocked existing tests
**Files:** tests/test_edge_cases.py, tests/test_final_coverage.py, tests/test_main_integration.py
**Dependencies:** 1, 2, 3, 4
**Description:** Unskip 5 blocked existing tests

### Task 6: Add pipeline integration test file with mocked external agents
**Files:** tests/test_pipeline_integration.py
**Dependencies:** 1, 2, 3
**Description:** Add pipeline integration test file with mocked external agents

### Task 7: Run full suite, update roadmap, close F002
**Files:** specs/roadmap.md, specs/STATUS.md
**Dependencies:** 5, 6
**Description:** Run full suite, update roadmap, close F002
