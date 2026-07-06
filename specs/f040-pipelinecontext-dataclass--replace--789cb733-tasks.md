# Task Breakdown: F040: PipelineContext dataclass — replace 20+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, etc.) with a single PipelineContext dataclass passed to each phase function. Eliminates conftest __setattr__ override hack. Makes testing trivial — create a context, pass it in. All 1,029 tests protect this refactor.

### Task 1: Create PipelineContext dataclass
**Files:** from spec
**Dependencies:** [none]
**Description:** Create PipelineContext dataclass

### Task 2: Wire into entry script
**Files:** from spec
**Dependencies:** [none]
**Description:** Wire into entry script

### Task 3: Refactor all phase functions
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor all phase functions

### Task 4: Refactor discover_blocked_pr + extract_blockers_from_pr
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor discover_blocked_pr + extract_blockers_from_pr

### Task 5: Remove utils.py globals + rewrite conftest
**Files:** from spec
**Dependencies:** [none]
**Description:** Remove utils.py globals + rewrite conftest

### Task 6: Remove vcs.py REPO (parallelizable with Task 2 — separate files)
**Files:** from spec
**Dependencies:** [none]
**Description:** Remove vcs.py REPO (parallelizable with Task 2 — separate files)

### Task 7: Update all test files
**Files:** from spec
**Dependencies:** [none]
**Description:** Update all test files

### Task 8: Full test suite
**Files:** from spec
**Dependencies:** [none]
**Description:** Full test suite
