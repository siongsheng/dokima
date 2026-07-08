# Task Breakdown: F043: Phase function decomposition — split run_phase1_strategist (656 lines, CC=125), run_phase2_coder (277, CC=77), run_pipeline (280, CC=79), run_fix_mode (281, CC=67), run_init (455, CC=60) into sub-operations. Target: max 150 lines, CC < 30 per function.

### Task 1: Extract _build_strategist_prompt from run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** [none]
**Description:** Extract _build_strategist_prompt from run_phase1_strategist

### Task 2: Extract _handle_interview_gate from run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** 1
**Description:** Extract _handle_interview_gate from run_phase1_strategist

### Task 3: Extract _enforce_dag_format from run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** 1
**Description:** Extract _enforce_dag_format from run_phase1_strategist

### Task 4: Extract _extract_and_clean_spec from run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** 3
**Description:** Extract _extract_and_clean_spec from run_phase1_strategist

### Task 5: Extract _save_spec_and_tasks from run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** 4
**Description:** Extract _save_spec_and_tasks from run_phase1_strategist

### Task 6: Extract _run_spec_pre_review from run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** 5
**Description:** Extract _run_spec_pre_review from run_phase1_strategist

### Task 7: Extract _compute_depth_and_mode from run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** [none]
**Description:** Extract _compute_depth_and_mode from run_phase1_strategist

### Task 8: Extract _run_human_gate from run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** 5, 7
**Description:** Extract _run_human_gate from run_phase1_strategist

### Task 9: Extract _create_adr_if_applicable from run_phase1_strategist
**Files:** pipeline.py
**Dependencies:** [none]
**Description:** Extract _create_adr_if_applicable from run_phase1_strategist

### Task 10: Refactor run_phase1_strategist to call sub-functions
**Files:** pipeline.py
**Dependencies:** 2, 6, 8, 9
**Description:** Refactor run_phase1_strategist to call sub-functions

### Task 11: Extract _build_coder_prompt from run_phase2_coder
**Files:** pipeline.py
**Dependencies:** 10
**Description:** Extract _build_coder_prompt from run_phase2_coder

### Task 12: Extract _select_coder_model from run_phase2_coder
**Files:** pipeline.py
**Dependencies:** 10
**Description:** Extract _select_coder_model from run_phase2_coder

### Task 13: Extract _run_coder_clarification_gate from run_phase2_coder
**Files:** pipeline.py
**Dependencies:** 11
**Description:** Extract _run_coder_clarification_gate from run_phase2_coder

### Task 14: Extract _handle_coder_truncation from run_phase2_coder
**Files:** pipeline.py
**Dependencies:** 11
**Description:** Extract _handle_coder_truncation from run_phase2_coder

### Task 15: Extract _verify_coder_output from run_phase2_coder
**Files:** pipeline.py
**Dependencies:** 14
**Description:** Extract _verify_coder_output from run_phase2_coder

### Task 16: Refactor run_phase2_coder to call sub-functions
**Files:** pipeline.py
**Dependencies:** 11, 12, 13, 15
**Description:** Refactor run_phase2_coder to call sub-functions

### Task 17: Extract _handle_resume_or_checkpoint from run_pipeline
**Files:** pipeline.py
**Dependencies:** 16
**Description:** Extract _handle_resume_or_checkpoint from run_pipeline

### Task 18: Extract _dispatch_execution_mode from run_pipeline
**Files:** pipeline.py
**Dependencies:** 17
**Description:** Extract _dispatch_execution_mode from run_pipeline

### Task 19: Extract _run_remaining_phases from run_pipeline
**Files:** pipeline.py
**Dependencies:** 18
**Description:** Extract _run_remaining_phases from run_pipeline

### Task 20: Refactor run_pipeline to call sub-functions
**Files:** pipeline.py
**Dependencies:** 17, 19
**Description:** Refactor run_pipeline to call sub-functions

### Task 21: Extract _discover_and_validate_blocked_pr from run_fix_mode
**Files:** pipeline.py
**Dependencies:** 20
**Description:** Extract _discover_and_validate_blocked_pr from run_fix_mode

### Task 22: Extract _extract_and_filter_blockers from run_fix_mode
**Files:** pipeline.py
**Dependencies:** 21
**Description:** Extract _extract_and_filter_blockers from run_fix_mode

### Task 23: Extract _run_fix_human_gate from run_fix_mode
**Files:** pipeline.py
**Dependencies:** 22
**Description:** Extract _run_fix_human_gate from run_fix_mode

### Task 24: Extract _run_fix_coder_phase from run_fix_mode
**Files:** pipeline.py
**Dependencies:** 23
**Description:** Extract _run_fix_coder_phase from run_fix_mode

### Task 25: Extract _run_fix_verification_phases from run_fix_mode
**Files:** pipeline.py
**Dependencies:** 24
**Description:** Extract _run_fix_verification_phases from run_fix_mode

### Task 26: Refactor run_fix_mode to call sub-functions
**Files:** pipeline.py
**Dependencies:** 21, 25
**Description:** Refactor run_fix_mode to call sub-functions

### Task 27: Extract _build_interview_preamble from run_init
**Files:** roadmap.py
**Dependencies:** 26
**Description:** Extract _build_interview_preamble from run_init

### Task 28: Extract _run_interview_loop from run_init
**Files:** roadmap.py
**Dependencies:** 27
**Description:** Extract _run_interview_loop from run_init

### Task 29: Extract _produce_constitution_docs from run_init
**Files:** roadmap.py
**Dependencies:** 28
**Description:** Extract _produce_constitution_docs from run_init

### Task 30: Extract _post_init_greenfield_setup from run_init
**Files:** roadmap.py
**Dependencies:** [none]
**Description:** Extract _post_init_greenfield_setup from run_init

### Task 31: Refactor run_init to call sub-functions
**Files:** roadmap.py
**Dependencies:** 29, 30
**Description:** Refactor run_init to call sub-functions

### Task 32: Add import verification tests for new sub-functions
**Files:** tests/test_f022_pipeline.py, tests/test_f022_roadmap.py, tests/test_f031_init_loop.py
**Dependencies:** 10, 16, 20, 26, 31
**Description:** Add import verification tests for new sub-functions
