# Task Breakdown: F040: PipelineContext dataclass — replace 20+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, etc.) with a single PipelineContext dataclass passed to each phase function. Eliminates conftest __setattr__ override hack. Makes testing trivial — create a context, pass it in. All 1,029 tests protect this refactor.

### Task 1: Define PipelineContext dataclass in utils.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Define PipelineContext dataclass in utils.py

### Task 2: Create PipelineContext at startup in dokima main()
**Files:** from spec
**Dependencies:** [none]
**Description:** Create PipelineContext at startup in dokima main()

### Task 3: Add ctx parameter to pipeline.py phase functions — signature only
**Files:** from spec
**Dependencies:** [none]
**Description:** Add ctx parameter to pipeline.py phase functions — signature only

### Task 4: Refactor run_phase1_strategist — switch globals to ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor run_phase1_strategist — switch globals to ctx

### Task 5: Refactor run_phase2_coder — switch globals to ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor run_phase2_coder — switch globals to ctx

### Task 6: Refactor run_phase3_vet, run_phase4_nm, run_phase5_tech_lead — switch globals to ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor run_phase3_vet, run_phase4_nm, run_phase5_tech_lead — switch globals to ctx

### Task 7: Refactor run_pipeline — create and propagate ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor run_pipeline — create and propagate ctx

### Task 8: Refactor run_post_pipeline, run_fix_mode, run_fix_mode_issue, discover_blocked_pr, extract_blockers_from_pr
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor run_post_pipeline, run_fix_mode, run_fix_mode_issue, discover_blocked_pr, extract_blockers_from_pr

### Task 9: Refactor roadmap.py — switch globals to ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor roadmap.py — switch globals to ctx

### Task 10: Refactor vcs.py — switch globals to ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor vcs.py — switch globals to ctx

### Task 11: Refactor agent.py — remove duplicate globals, use ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor agent.py — remove duplicate globals, use ctx

### Task 12: Refactor utils.py functions — switch globals to ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Refactor utils.py functions — switch globals to ctx

### Task 13: Remove module-level globals from utils.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Remove module-level globals from utils.py

### Task 14: Remove duplicate globals from agent.py
**Files:** from spec
**Dependencies:** [none]
**Description:** Remove duplicate globals from agent.py

### Task 15: Update conftest.py — remove setattr hack, use PipelineContext
**Files:** from spec
**Dependencies:** [none]
**Description:** Update conftest.py — remove setattr hack, use PipelineContext

### Task 16: Update test files — adapt signatures to use ctx
**Files:** from spec
**Dependencies:** [none]
**Description:** Update test files — adapt signatures to use ctx

### Task 17: Update dokima entry point — wire ctx through all call sites
**Files:** from spec
**Dependencies:** [none]
**Description:** Update dokima entry point — wire ctx through all call sites

### Task 18: Final verification — grep for stale globals, run full suite
**Files:** from spec
**Dependencies:** [none]
**Description:** Final verification — grep for stale globals, run full suite
