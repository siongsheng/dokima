# Task Breakdown: F040: PipelineContext dataclass — replace 20+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, etc.) with a single PipelineContext dataclass passed to each phase function. Eliminates conftest __setattr__ override hack. Makes testing trivial — create a context, pass it in. All 1,029 tests protect this refactor.

### Task 1: Create PipelineContext dataclass
**Files:** pipeline.py (or new context.py)
**Dependencies:** [none]
**Description:** Create PipelineContext dataclass

### Task 2: Wire PipelineContext into entry script — remove _sync_modules()
**Files:** dokima
**Dependencies:** 1
**Description:** Wire PipelineContext into entry script — remove _sync_modules()

### Task 3: Refactor run_pipeline to accept ctx — cascade to all phase functions
**Files:** pipeline.py
**Dependencies:** 1
**Description:** Refactor run_pipeline to accept ctx — cascade to all phase functions

### Task 4: Refactor discover_blocked_pr and extract_blockers_from_pr
**Files:** pipeline.py
**Dependencies:** 3
**Description:** Refactor discover_blocked_pr and extract_blockers_from_pr

### Task 5: Remove module-level globals from utils.py — update tests
**Files:** utils.py, tests/conftest.py, all test files that use panel.PROJECT_DIR
**Dependencies:** 3
**Description:** Remove module-level globals from utils.py — update tests

### Task 6: Remove module-level REPO from vcs.py
**Files:** vcs.py, pipeline.py (call sites), dokima
**Dependencies:** 1
**Description:** Remove module-level REPO from vcs.py

### Task 7: Update all test files to use PipelineContext
**Files:** tests/conftest.py, tests/test_*.py (~50 test files)
**Dependencies:** 5
**Description:** Update all test files to use PipelineContext

### Task 8: Run full test suite — verify 1,029 pass, 4 skip, 0 fail
**Files:** all
**Dependencies:** 7
**Description:** Run full test suite — verify 1,029 pass, 4 skip, 0 fail
