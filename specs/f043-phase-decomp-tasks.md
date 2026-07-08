# F043: Phase Function Decomposition

## Impact
Contributors can understand and modify phase functions without tracing 125 branching paths. Each sub-operation is independently testable.

### Task 1: Decompose run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** [none]
**Parallelizable:** no
**Description:** Extract sub-functions from run_phase1_strategist (656 lines, CC=125): _build_strategist_prompt(), _parse_strategist_output(), _handle_interview_mode(), _save_spec_files(). Each ≤ 150 lines.

### Task 2: Decompose run_pipeline and run_phase2_coder
**Files:** pipeline.py
**Dependencies:** [Task 1]
**Parallelizable:** no
**Description:** Extract from run_pipeline: _setup_pipeline_context(), _run_phase_sequence(). From run_phase2_coder: _build_coder_prompt(), _spawn_coder(), _monitor_coder(). Each ≤ 150 lines.

### Task 3: Decompose run_fix_mode and run_init
**Files:** pipeline.py, roadmap.py
**Dependencies:** [Task 2]
**Parallelizable:** no
**Description:** Extract from run_fix_mode: _detect_blockers(), _run_fix_pipeline(). From run_init: _interview_user(), _generate_constitution(). Each ≤ 150 lines.
