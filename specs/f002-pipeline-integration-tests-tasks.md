# Task Breakdown: F002: Pipeline Integration Tests

### Task 1: Extract _read_stdin_with_timeout() helper
**Files:** dokima
**Dependencies:** [none]
**Description:** Extract _read_stdin_with_timeout() helper

### Task 2: Create Orchestrator class with injectable dependencies
**Files:** dokima
**Dependencies:** 1
**Description:** Create Orchestrator class with injectable dependencies

### Task 3: Add test_repo and mock_orchestrator fixtures
**Files:** tests/conftest.py
**Dependencies:** 2
**Description:** Add test_repo and mock_orchestrator fixtures

### Task 4: Phase 1-2 integration test — Strategist → Coder
**Files:** tests/test_pipeline_integration.py
**Dependencies:** 3
**Description:** Phase 1-2 integration test — Strategist → Coder

### Task 5: Phase 3-5 integration test — Vet → nm → TL
**Files:** tests/test_pipeline_integration.py
**Dependencies:** 4
**Description:** Phase 3-5 integration test — Vet → nm → TL

### Task 6: Flag parsing and CLI argument tests
**Files:** tests/test_main.py
**Dependencies:** 2
**Description:** Flag parsing and CLI argument tests

### Task 7: Lock, signal, and stdin edge case tests
**Files:** tests/test_main.py
**Dependencies:** 3
**Description:** Lock, signal, and stdin edge case tests

### Task 8: Final validation and F002 closure
**Files:** specs/roadmap.md, specs/STATUS.md
**Dependencies:** 4, 5, 6, 7
**Description:** Final validation and F002 closure
