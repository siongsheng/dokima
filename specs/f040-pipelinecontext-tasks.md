# F040: PipelineContext Dataclass

## Impact
Contributors write tests by creating a PipelineContext instead of monkey-patching 20+ module globals through conftest.

## What Changed
- New `PipelineContext` dataclass in pipeline.py
- All modules accept `ctx` parameter instead of reading globals
- conftest.py simplified

### Task 1: Create PipelineContext dataclass
**Files:** pipeline.py
**Dependencies:** [none]
**Parallelizable:** no
**Description:** Add PipelineContext dataclass with fields: project_dir, repo, default_branch, test_cmd, build_cmd, lint_cmd, depth, confidence, impact, mode, parallel_enabled, branch, spec_path, pr_url, feature. Add _apply_context(ctx) to set module globals.

### Task 2: Update phase functions to accept ctx
**Files:** pipeline.py
**Dependencies:** [Task 1]
**Parallelizable:** no
**Description:** Update run_phase1_strategist, run_phase2_coder, run_phase3_vet, run_phase4_nm, run_phase5_tech_lead, run_fix_mode, run_fix_mode_issue, run_pipeline to accept optional `ctx` parameter. Call _apply_context(ctx) at function start.

### Task 3: Update conftest to use PipelineContext
**Files:** tests/conftest.py
**Dependencies:** [Task 2]
**Parallelizable:** no
**Description:** Replace __setattr__ override hacks with PipelineContext creation. Create ctx fixture that builds PipelineContext for tests.
