# Task Breakdown: F005: Model Family Fallback

### Task 1: Add FALLBACK_MODEL env-var constant
**Files:** dokima
**Dependencies:** [none]
**Description:** Add FALLBACK_MODEL env-var constant

### Task 2: Add provider failure detection helper
**Files:** dokima
**Dependencies:** [none]
**Description:** Add provider failure detection helper

### Task 3: Add fallback retry logic to spawn_agent
**Files:** dokima
**Dependencies:** 1, 2
**Description:** Add fallback retry logic to spawn_agent

### Task 4: Write unit tests for fallback detection
**Files:** tests/test_f005_fallback.py
**Dependencies:** 2
**Description:** Write unit tests for fallback detection

### Task 5: Write unit tests for fallback retry
**Files:** tests/test_f005_fallback.py
**Dependencies:** 3, 4
**Description:** Write unit tests for fallback retry

### Task 6: Test fallback does NOT fire on legitimate output
**Files:** tests/test_f005_fallback.py
**Dependencies:** 3
**Description:** Test fallback does NOT fire on legitimate output

### Task 7: Update conventions.md
**Files:** specs/conventions.md
**Dependencies:** 3
**Description:** Update conventions.md
