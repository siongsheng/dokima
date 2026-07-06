# Task Breakdown: F040: PipelineContext dataclass — replace 20+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, etc.) with a single PipelineContext dataclass passed to each phase function. Eliminates conftest __setattr__ override hack. Makes testing trivial — create a context, pass it in. All 1,029 tests protect this refactor.

### Task 1: Create PipelineContext dataclass in context.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Create PipelineContext dataclass in context.py

### Task 2: Add ctx fixture to tests/conftest.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Add ctx fixture to tests/conftest.py

### Task 3: Migrate utils.py globals to ctx parameter
**Files:** from spec
**Dependencies:** [none]
**Description:** Migrate utils.py globals to ctx parameter

### Task 4: Migrate agent.py globals to ctx parameter
**Files:** from spec
**Dependencies:** [none]
**Description:** Migrate agent.py globals to ctx parameter

### Task 5: Migrate vcs.py globals to ctx parameter
**Files:** from spec
**Dependencies:** [none]
**Description:** Migrate vcs.py globals to ctx parameter

### Task 6: Migrate tasks.py globals to ctx parameter
**Files:** from spec
**Dependencies:** [none]
**Description:** Migrate tasks.py globals to ctx parameter

### Task 7: Migrate pipeline.py globals to ctx parameter
**Files:** from spec
**Dependencies:** [none]
**Description:** Migrate pipeline.py globals to ctx parameter

### Task 8: Migrate roadmap.py globals to ctx parameter
**Files:** from spec
**Dependencies:** [none]
**Description:** Migrate roadmap.py globals to ctx parameter

### Task 9: Migrate dokima main() to construct and pass ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Migrate dokima main() to construct and pass ctx

### Task 10: Migrate test files from panel.GLOBAL to ctx.GLOBAL
**Files:** from spec
**Dependencies:** [none]
**Description:** Migrate test files from panel.GLOBAL to ctx.GLOBAL

### Task 11: Simplify conftest.py — remove setattr hack
**Files:** from spec
**Dependencies:** [none]
**Description:** Simplify conftest.py — remove setattr hack

### Task 12: Run full test suite and verify 100% pass rate
**Files:** from spec
**Dependencies:** [none]
**Description:** Run full test suite and verify 100% pass rate
