# F043: Phase function decomposition — split run_phase1_strategist (656 lines, CC=125), run_phase2_coder (277, CC=77), run_pipeline (280, CC=79), run_fix_mode (281, CC=67), run_init (455, CC=60) into sub-operations. Target: max 150 lines, CC < 30 per function.

Now I have full understanding of all five functions and the existing (minimal) spec. Here is the complete corrected spec — every section, every line, with the three missing elements (Impact, What Changed, proper ### Task N: headers) restored and all required spec-strategist-lite sections added.
    
    
    
    F043: Phase Function Decomposition
    
    Status: In Progress
    Confidence: High
    Version: 1.2.0
    
    
    
    1. Executive Summary
    
    Five phase functions in the dokima pipeline exceed maintainability thresholds: run_phase1_strategist (656 lines, CC=125), run_phase2_coder (277, CC=77), run_pipeline (280, CC=79), run_fix_mode (281, CC=67), and run_init (455, CC=60). This feature decomposes each into focused sub-operations with clear interfaces, targeting max 150 lines and CC < 30 per function. The refactoring is behavior-preserving — all 1,029+ existing tests must continue passing. No new functionality is added; this is a pure structural improvement that enables faster agent context loading, easier testing, and safer future changes. Confidence is High because the boundaries between sub-operations are already visible in the code (comment blocks, phase markers, control-flow gates).
    
    
    
    2. Constitution Check
    
    Axiom: Solves user's own pain
    Verdict: YES
    Detail: Shaun (the user) cannot modify pipeline phases without tracing 125
      branching paths — this is his own repo, his own pain
    ────────────────────────────────────────
    Axiom: Weekend-buildable
    Verdict: YES
    Detail: Pure refactoring — extract functions, no new logic, tests already
      exist as safety net
    ────────────────────────────────────────
    Axiom: Evidence people will pay
    Verdict: N/A
    Detail: Internal tooling — no revenue model check needed
    ────────────────────────────────────────
    Axiom: Tech stack boring and proven
    Verdict: YES
    Detail: Python 3.6+ — same language, same modules, zero new dependencies
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories
    Verdict: YES
    Detail: No AI, no "platform for X" — just structural refactoring
    
    No misalignments flagged. The feature aligns with the project's stated goal of modular, maintainable code (F022, F022b, F041 all paved the same path).
    
    
    
    3. Ponytail Guard — Pre-Spec Review
    
    Feature: F043: Phase function decomposition
    Rung: 7 — the minimum that works (existing functions are genuinely too large)
    Existing solution: None — these functions are monolithic by design, no sub-functions exist to compose differently
    Spec needed: YES — purely covers the extraction boundaries, not new functionality
    Spec scope: Define which sub-functions to extract, their signatures, their callers, and the order of operations
    
    
    
    4. Impact
    
    Confidence: High / Impact: MEDIUM
    
    This refactoring touches the core pipeline orchestration — every feature run passes through these functions. However, it is behavior-preserving with existing test coverage as a safety net. The primary impact is on contributors (faster understanding, easier debugging) and agent context windows (smaller functions = less token pressure). Pipeline operators see zero change — same CLI, same output, same behavior.
    
    Risks: if sub-function boundaries are wrong, callers break. Mitigated by 1,029+ existing tests.
    
    
    
    5. What Changed
    
    - pipeline.py: Extract ~18 sub-functions from run_phase1_strategist, run_phase2_coder, run_pipeline, run_fix_mode. Each original function becomes a thin orchestrator calling sub-functions. No logic changes.
    - roadmap.py: Extract ~6 sub-functions from run_init. Interview loop, doc production, post-init setup each get their own function.
    - tests/test_f022_pipeline.py: Add import checks for new sub-functions (following existing pattern: test_pipeline_has_X).
    - tests/test_f022_roadmap.py: Add import checks for new roadmap sub-functions.
    - tests/test_f031_init_loop.py: Update test references if sub-function names change call sites.
    
    
    
    6. Feature Breakdown — Task List
    
    All tasks are behavior-preserving extractions. Each sub-function is tested implicitly by the existing test suite. New tests only verify that the new functions are importable (following the F022 pattern).
    
    Task 1: Extract _build_strategist_prompt from run_phase1_strategist
    Files: pipeline.py
    Dependencies: [none]
    Parallelizable: no
    Estimated LOC: ~80
    Description: Extract the multi-paragraph strategist prompt assembly (lines 1924-2023) into _build_strategist_prompt(feature, refine_note, ref_context, user_answers_prefill) -> str. This includes the map hint, existing spec note, external reference injection, user clarifications, task format requirements, and coder constraints. The extracted function returns the complete prompt string. The caller passes the assembled prompt to spawn_agent.
    
    Task 2: Extract _handle_interview_gate from run_phase1_strategist
    Files: pipeline.py
    Dependencies: [Task 1]
    Parallelizable: no
    Estimated LOC: ~130
    Description: Extract the interview gate logic (lines 2075-2180) into _handle_interview_gate(strat_output, strat_prompt, feature, user_answers_prefill) -> tuple[str, bool]. Returns (possibly_re_run_output, did_re_run). Covers: interview mode detection, non-TTY interview state saving + sys.exit(2), interactive clarification loop, and re-spawning strategist with user answers. Returns the final strat_output (original or re-run).
    
    Task 3: Extract _enforce_dag_format from run_phase1_strategist
    Files: pipeline.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Estimated LOC: ~50
    Description: Extract DAG format enforcement (lines 2028-2068) into _enforce_dag_format(strat_output, feature) -> str. Checks if output has ### Task N: headers; if not and not on fallback, re-prompts strategist with format correction. Returns possibly-re-prompted output. Includes the re-prompt verification check.
    
    Task 4: Extract _extract_and_clean_spec from run_phase1_strategist
    Files: pipeline.py
    Dependencies: [Task 3]
    Parallelizable: no
    Estimated LOC: ~60
    Description: Extract spec extraction, garbage detection, and fallback recovery (lines 2182-2277) into _extract_and_clean_spec(strat_output, orig_strat_output) -> str. Handles: agent message extraction, spec < 100 char fallback, clean_spec_content, garbage marker detection, write_file path recovery, and original-output fallback.
    
    Task 5: Extract _save_spec_and_tasks from run_phase1_strategist
    Files: pipeline.py
    Dependencies: [Task 4]
    Parallelizable: no
    Estimated LOC: ~50
    Description: Extract spec saving and task extraction (lines 2279-2320) into _save_spec_and_tasks(feature, spec) -> tuple[str, str]. Returns (spec_path, tasks_extract_path). Handles: slug generation, spec file writing, TaskDAG parsing, and task extract file writing. Includes error handling for task extraction failures.
    
    Task 6: Extract _run_spec_pre_review from run_phase1_strategist
    Files: pipeline.py
    Dependencies: [Task 5]
    Parallelizable: yes
    Estimated LOC: ~40
    Description: Extract Tech Lead spec pre-review (lines 2322-2358) into _run_spec_pre_review(spec_path) -> None. Spawns tech-lead agent with adversarial-review-lite skill, extracts and prints review text. Respects PANEL_SKIP_ORCHESTRATOR_REVIEW env var.
    
    Task 7: Extract _compute_depth_and_mode from run_phase1_strategist
    Files: pipeline.py
    Dependencies: [none]
    Parallelizable: yes
    Estimated LOC: ~30
    Description: Extract the depth matrix computation (lines 2362-2392) into _compute_depth_and_mode(spec) -> tuple[str, str, str]. Returns (confidence, impact, depth). Parses confidence/impact markers from spec text, applies depth_matrix lookup, respects FORCE_FULL override, and determines passive/active mode. Pure function — no side effects.
    
    Task 8: Extract _run_human_gate from run_phase1_strategist
    Files: pipeline.py
    Dependencies: [Task 5, Task 7]
    Parallelizable: no
    Estimated LOC: ~60
    Description: Extract the human gate interactive spec review (lines 2400-2457) into _run_human_gate(feature, spec_path, tasks_extract_path, depth, impact, branch, spec) -> str. Returns potentially-updated spec (if user edited). Handles: review with less, edit with vim, task re-extraction after edit, and quit. Respects SKIP_HUMAN_GATE and TTY checks.
    
    Task 9: Extract _create_adr_if_applicable from run_phase1_strategist
    Files: pipeline.py
    Dependencies: [none]
    Parallelizable: yes
    Estimated LOC: ~30
    Description: Extract ADR creation (lines 2459-2499) into _create_adr_if_applicable(spec_path, spec, feature) -> None. Checks adr-tools binary existence, extracts decision table from spec, runs adr new, appends source link to ADR and ADR link to spec. Best-effort — failures are logged, not fatal.
    
    Task 10: Refactor run_phase1_strategist to call sub-functions
    Files: pipeline.py
    Dependencies: [Task 2, Task 6, Task 8, Task 9]
    Parallelizable: no
    Estimated LOC: ~100
    Description: Rewrite run_phase1_strategist as a thin orchestrator (~100 lines) that calls: _build_strategist_prompt, spawn_agent, _enforce_dag_format, config restore, _handle_interview_gate, _extract_and_clean_spec, _save_spec_and_tasks, map enrichment (inline), extract_pr_sections (inline), _run_spec_pre_review, _compute_depth_and_mode, _status_update (inline), _run_human_gate, _create_adr_if_applicable, and returns the same dict. All original logic preserved. No behavioral change.
    
    Task 11: Extract _build_coder_prompt from run_phase2_coder
    Files: pipeline.py
    Dependencies: [Task 10]
    Parallelizable: no
    Estimated LOC: ~120
    Description: Extract coder prompt construction (lines 720-830) into _build_coder_prompt(feature, spec, spec_path, tasks_extract_path, branch, depth, mode) -> str. Returns the complete coder prompt string. Handles: fix mode vs normal mode path, file hints extraction (from tasks_extract and spec_path fallback), code context extraction, TDD instructions, self-assessment questions, and depth=vet PR creation instructions.
    
    Task 12: Extract _select_coder_model from run_phase2_coder
    Files: pipeline.py
    Dependencies: [Task 10]
    Parallelizable: yes
    Estimated LOC: ~20
    Description: Extract model selection logic (lines 832-844) into _select_coder_model(mode, tasks_extract_path) -> str | None. Returns model string for upgrade (deepseek-v4-pro for fix mode or ≥8 tasks) or None for profile default.
    
    Task 13: Extract _run_coder_clarification_gate from run_phase2_coder
    Files: pipeline.py
    Dependencies: [Task 11]
    Parallelizable: yes
    Estimated LOC: ~55
    Description: Extract coder clarification gate (lines 852-891) into _run_coder_clarification_gate(coder_output, coder_prompt) -> str. Checks for CLARIFICATION NEEDED markers, prompts user for answers (with 60s timeout), re-runs coder with answers if provided. Returns final coder_output.
    
    Task 14: Extract _handle_coder_truncation from run_phase2_coder
    Files: pipeline.py
    Dependencies: [Task 11]
    Parallelizable: yes
    Estimated LOC: ~30
    Description: Extract truncation detection and retry (lines 893-908) into _handle_coder_truncation(coder_output, coder_prompt, _truncation_retried) -> tuple[str, bool]. Returns (possibly_retried_output, was_retried). Detects truncation, retries once with truncation note appended to prompt.
    
    Task 15: Extract _verify_coder_output from run_phase2_coder
    Files: pipeline.py
    Dependencies: [Task 14]
    Parallelizable: yes
    Estimated LOC: ~30
    Description: Extract post-coder verification (lines 919-944) into _verify_coder_output(coder_output) -> tuple[bool, list[str]]. Returns (is_ok, issues_list). Checks: RED commit found, GREEN commit found, build passing, tests passing. Pure output analysis — no agent spawns.
    
    Task 16: Refactor run_phase2_coder to call sub-functions
    Files: pipeline.py
    Dependencies: [Task 11, Task 12, Task 13, Task 15]
    Parallelizable: no
    Estimated LOC: ~80
    Description: Rewrite run_phase2_coder as a thin orchestrator (~80 lines) that calls: _select_coder_model, _build_coder_prompt, spawn_agent, _run_coder_clarification_gate, _handle_coder_truncation, timeout contingency (inline), _verify_coder_output, halt_and_revert (inline), PR URL extraction (inline). Returns the same dict. All original logic preserved.
    
    Task 17: Extract _handle_resume_or_checkpoint from run_pipeline
    Files: pipeline.py
    Dependencies: [Task 16]
    Parallelizable: no
    Estimated LOC: ~50
    Description: Extract resume/checkpoint logic (lines 2526-2613) into _handle_resume_or_checkpoint(feature, feature_slug, resume) -> dict. Returns dict with: spec, spec_path, pr_sections, tasks_extract_path, depth, branch, confidence, impact, mode, strat_output, parallel_enabled, phases_completed, cp. Handles: checkpoint loading, validation, phase skipping, or running phase 1 + committing spec + saving checkpoint.
    
    Task 18: Extract _dispatch_execution_mode from run_pipeline
    Files: pipeline.py
    Dependencies: [Task 17]
    Parallelizable: no
    Estimated LOC: ~100
    Description: Extract execution mode dispatch (lines 2626-2707) into _dispatch_execution_mode(dag, spec, spec_path, tasks_extract_path, feature, branch, depth, impact, mode, parallel_enabled, pr_sections, phases_completed, is_next, is_continuous, resume, strat_output) -> dict. Returns dict with: coder_failed, pr_url, verdict, should_return (bool), exit_code. Handles both per_task_spawn and single_session paths. For per_task_spawn: wave computation, parallel coders, merge, depth=vet PR creation. For single_session: delegates to run_phase2_coder.
    
    Task 19: Extract _run_remaining_phases from run_pipeline
    Files: pipeline.py
    Dependencies: [Task 18]
    Parallelizable: no
    Estimated LOC: ~50
    Description: Extract phases 3-5 dispatch (lines 2727-2790) into _run_remaining_phases(coder_failed, depth, feature, branch, pr_sections, impact, spec_path, confidence, pr_url, nm_output, phases_completed, feature_slug, resume, strat_output, mode) -> dict. Returns dict with: coder_failed, pr_url, verdict, tl_output, nm_output, continue_loop. Handles: vet, nm (with PR body injection + SHOULD FIX issues), TL dispatch, and depth-based skipping.
    
    Task 20: Refactor run_pipeline to call sub-functions
    Files: pipeline.py
    Dependencies: [Task 17, Task 19]
    Parallelizable: no
    Estimated LOC: ~60
    Description: Rewrite run_pipeline as a thin orchestrator (~60 lines) that calls: _sanitize_prompt (inline), _status_update (inline), _handle_resume_or_checkpoint, DAG parse + compute_execution_mode (inline), _dispatch_execution_mode, _run_remaining_phases, run_post_pipeline (inline). Returns exit code 0. All original logic preserved.
    
    Task 21: Extract _discover_and_validate_blocked_pr from run_fix_mode
    Files: pipeline.py
    Dependencies: [Task 20]
    Parallelizable: no
    Estimated LOC: ~60
    Description: Extract PR discovery and validation (lines 428-473) into _discover_and_validate_blocked_pr() -> dict | None. Calls discover_blocked_pr(), checks PR state (merged/closed), checks most recent TL review verdict (skip if APPROVED). Returns PR dict or None if nothing to fix. Prints status messages inline.
    
    Task 22: Extract _extract_and_filter_blockers from run_fix_mode
    Files: pipeline.py
    Dependencies: [Task 21]
    Parallelizable: no
    Estimated LOC: ~60
    Description: Extract blocker extraction and filtering (lines 475-529) into _extract_and_filter_blockers(pr_body, pr_num, fix_all) -> tuple[list, list]. Returns (code_blockers, should_fix_items). Handles: extract_blockers_from_pr, EC13 fallback, architectural filter, SHOULD FIX extraction for --fix-all, and non-blocker prose filtering.
    
    Task 23: Extract _run_fix_human_gate from run_fix_mode
    Files: pipeline.py
    Dependencies: [Task 22]
    Parallelizable: yes
    Estimated LOC: ~30
    Description: Extract abbreviated human gate (lines 531-553) into _run_fix_human_gate(fix_tasks, skip_gate) -> list | None. Returns updated fix_tasks after optional editing, or None if user quit. Handles: TTY check, [y/e/q] prompt, EDITOR-based editing.
    
    Task 24: Extract _run_fix_coder_phase from run_fix_mode
    Files: pipeline.py
    Dependencies: [Task 23]
    Parallelizable: no
    Estimated LOC: ~60
    Description: Extract the fix-specific coder execution (lines 577-630) into _run_fix_coder_phase(project_dir, pr_branch, pr_num, pr_title, fix_tasks, spec_path) -> dict. Constructs the fix-only coder prompt (with target file hints), calls run_phase2_coder in fix mode, returns coder_result dict. Handles branch checkout and pull.
    
    Task 25: Extract _run_fix_verification_phases from run_fix_mode
    Files: pipeline.py
    Dependencies: [Task 24]
    Parallelizable: no
    Estimated LOC: ~50
    Description: Extract vet + nm + TL re-review dispatch (lines 633-700) into _run_fix_verification_phases(pr_title, pr_branch, pr_num, pr_url, blockers, spec_path, nm_result) -> None. Runs run_phase3_vet, run_phase4_nm, and a scoped TL re-review for blocker verification. Prints verdict. Calls generate_codebase_map on success.
    
    Task 26: Refactor run_fix_mode to call sub-functions
    Files: pipeline.py
    Dependencies: [Task 21, Task 25]
    Parallelizable: no
    Estimated LOC: ~50
    Description: Rewrite run_fix_mode as a thin orchestrator (~50 lines) that calls: PROJECT_DIR assignment + header printing (inline), _discover_and_validate_blocked_pr, _extract_and_filter_blockers, _run_fix_human_gate, spec_path discovery (inline), _run_fix_coder_phase, _run_fix_verification_phases. All original logic preserved.
    
    Task 27: Extract _build_interview_preamble from run_init
    Files: roadmap.py
    Dependencies: [Task 26]
    Parallelizable: no
    Estimated LOC: ~100
    Description: Extract the full interview preamble construction (lines 666-761) into _build_interview_preamble(description, project_dir, is_greenfield) -> str. Returns the complete strategist prompt for init mode, including: greenfield/existing detection, audit section, interview instructions, constitution doc format specs, roadmap format rules, AGENTS.md template, and validation loop instructions.
    
    Task 28: Extract _run_interview_loop from run_init
    Files: roadmap.py
    Dependencies: [Task 27]
    Parallelizable: no
    Estimated LOC: ~120
    Description: Extract the interview loop logic (lines 785-931) into _run_interview_loop(interview_preamble, init_skills, interview_state, accumulated_answers, MAX_INTERVIEW_ROUNDS) -> tuple[int, list, dict]. Returns (current_round, accumulated_answers, interview_state). Handles: round iteration, prompt assembly with QA context, strategist spawning, CLARIFICATION trigger detection, question parsing (with assumption/impact extraction), answer collection (delegating to collect_init_interview_answers), and round advancement.
    
    Task 29: Extract _produce_constitution_docs from run_init
    Files: roadmap.py
    Dependencies: [Task 28]
    Parallelizable: no
    Estimated LOC: ~40
    Description: Extract final doc production (lines 933-960) into _produce_constitution_docs(interview_preamble, accumulated_answers, init_skills, is_first_round_high, max_exhausted) -> str. Spawns strategist with accumulated answers, returns strat_output. Handles the "no more questions, produce docs NOW" final prompt for exhausted rounds vs first-round High confidence path.
    
    Task 30: Extract _post_init_greenfield_setup from run_init
    Files: roadmap.py
    Dependencies: [none]
    Parallelizable: yes
    Estimated LOC: ~50
    Description: Extract greenfield post-init setup (lines 976-1004) into _post_init_greenfield_setup(project_dir, description, is_greenfield, has_remote, is_tty) -> None. Handles: AGENTS.md creation if missing, GitHub remote prompt (interactive only), and STATUS.md initialization. Best-effort — failures logged, not fatal.
    
    Task 31: Refactor run_init to call sub-functions
    Files: roadmap.py
    Dependencies: [Task 29, Task 30]
    Parallelizable: no
    Estimated LOC: ~70
    Description: Rewrite run_init as a thin orchestrator (~70 lines) that calls: API key loading + project detection (inline), ensure_profiles/deploy_profile_skills (inline), max_turns override (inline), _build_interview_preamble, _run_interview_loop, max rounds check (inline), _produce_constitution_docs, config restore (inline), interview state cleanup (inline), _post_init_greenfield_setup, and completion summary (inline). All original logic preserved.
    
    Task 32: Add import verification tests for new sub-functions
    Files: tests/test_f022_pipeline.py, tests/test_f022_roadmap.py, tests/test_f031_init_loop.py
    Dependencies: [Task 10, Task 16, Task 20, Task 26, Task 31]
    Parallelizable: yes
    Estimated LOC: ~80
    Description: Add test_pipeline_has_X assertions for every new sub-function in pipeline.py (following existing F022 test pattern: assert callable, assert on module). Add corresponding tests for roadmap.py sub-functions. Update test_f031_init_loop.py references if sub-function extraction changes call patterns (unlikely — this is pure extraction). Run full test suite to verify zero regressions: python3 -m pytest tests/ -q.
    
    
    
    7. Data Model
    
    N/A — pure refactoring. No new entities, no schema changes, no new storage. All sub-functions operate on the same in-memory types (str, dict, list) as the originals. Module-level globals (PROJECT_DIR, REPO, etc.) are still accessed via global — F040 (PipelineContext) handles their removal in a separate feature.
    
    
    
    8. API Routes
    
    N/A — no API surface change. The public interface is run_phase1_strategist(), run_phase2_coder(), run_pipeline(), run_fix_mode(), and run_init() — all five retain their exact signatures and return types. Callers in dokima entry point and test_main_integration.py are unaffected.
    
    
    
    9. Component Tree
    
    N/A — no frontend. Pure Python refactoring of pipeline orchestration.
    
    
    
    10. COTS Build-vs-Buy
    
    N/A — no third-party dependencies. All sub-functions use the same stdlib and existing imports as their parent functions. Zero new packages.
    
    
    
    11. Test Plan (MANDATORY)
    
    Happy Path
    - python3 -m pytest tests/ -q passes with 1,029+ tests green, same as baseline
    - All five refactored functions produce identical output to pre-refactoring versions for the same inputs
    - dokima next "test feature" completes full pipeline without errors
    - dokima fix completes fix pipeline without errors
    - dokima init "test project" /tmp/test produces all four constitution docs
    
    Edge Cases
    - Empty spec: What if _extract_and_clean_spec receives a 50-char spec? Fallback to raw strat_output must work.
    - No tasks in DAG: What if _save_spec_and_tasks parses a spec with zero ### Task N: headers? tasks_extract_path must be empty string, not crash.
    - Max interview rounds exhausted: What if _run_interview_loop hits MAX_INTERVIEW_ROUNDS=3 with Low confidence? _produce_constitution_docs must run with best-available info.
    - Fix mode with zero code blockers: What if _extract_and_filter_blockers returns empty code_blockers? run_fix_mode must print "All blockers are architectural" and return.
    - PR already merged/closed: What if _discover_and_validate_blocked_pr finds a merged PR? Must return None, not proceed to fix.
    - Non-TTY mode: All human gates must skip gracefully when stdin is not a TTY. No crash, no hang on input().
    - Truncation on first retry still truncated: _handle_coder_truncation must not loop infinitely — max 1 retry.
    
    Failure Modes
    - spawn_agent timeout: What if the strategist times out during _handle_interview_gate? Timeout contingency must print error and not hang.
    - TaskDAG parse failure: What if _save_spec_and_tasks gets a malformed spec? Exception caught, tasks_extract_path set to empty string, pipeline continues with coder reading full spec.
    - git checkout failure in fix mode: What if _run_fix_coder_phase can't checkout pr_branch? Error must propagate through coder_failed, not crash.
    - write_file recovery fails: What if _extract_and_clean_spec detects garbage but write_file path doesn't exist? Must fall back to original pre-re-prompt spec, not return garbage.
    - ADR tools missing: _create_adr_if_applicable must handle adr binary not found gracefully — print info message, continue.
    
    Contract Invariants
    - run_phase1_strategist return shape: Must always return a dict with keys: spec, spec_path, pr_sections, tasks_extract_path, depth, branch, confidence, impact, mode, strat_output, parallel_enabled. Missing any key breaks run_pipeline.
    - run_phase2_coder return shape: Must always return dict with: coder_output, pr_url, coder_failed, verdict.
    - run_pipeline exit code: Must always return 0 (success) or exit via sys.exit on fatal errors. Never return non-zero without exit.
    - run_fix_mode side effects: Must never modify repo state if PR is already merged/approved. Must checkout DEFAULT_BRANCH on completion.
    - run_init side effects: Must create specs/ directory and at minimum specs/roadmap.md. Must restore strategist config yaml to original max_turns.
    - No new global state: Sub-functions must not introduce new module-level globals. All state flows through parameters and return values.
    - Same log output: _write_log_line calls and print() timing must be preserved — agents and cron jobs parse these.
    
    
    
    12. Panel Split (Parallelization)
    
    Sequential waves — refactoring a single file forces sequential execution on most tasks:
    
    Wave: 1
    Tasks: T1
    Rationale: Foundation — _build_strategist_prompt is the largest single
      extraction
    ────────────────────────────────────────
    Wave: 2
    Tasks: T2, T3, T6, T9
    Rationale: Four extractions from run_phase1_strategist — all share
      pipeline.py but touch non-overlapping line ranges: T2 (lines 2075-2180),
      T3 (2028-2068), T6 (2322-2358), T9 (2459-2499). These can run in
      parallel with careful merge coordination.
    ────────────────────────────────────────
    Wave: 3
    Tasks: T4, T5, T7
    Rationale: T4 depends on T3's output format. T5 depends on T4. T7 is pure
      function, no shared state — can run alongside T4/T5.
    ────────────────────────────────────────
    Wave: 4
    Tasks: T8
    Rationale: Depends on T5 (spec_path) and T7 (depth/mode)
    ────────────────────────────────────────
    Wave: 5
    Tasks: T10
    Rationale: Orchestrator refactor — depends on all extractions being in
      place
    ────────────────────────────────────────
    Wave: 6
    Tasks: T11, T12
    Rationale: T11 (_build_coder_prompt) and T12 (_select_coder_model) touch
      different sections — can be parallel
    ────────────────────────────────────────
    Wave: 7
    Tasks: T13, T14, T15, T17, T30
    Rationale: Five pure extractions across three files. T13/T14/T15 touch
      pipeline.py coder section. T17 touches pipeline.py pipeline section. T30
      touches roadmap.py. All non-overlapping.
    ────────────────────────────────────────
    Wave: 8
    Tasks: T16, T18, T19
    Rationale: T16 depends on T11-15. T18/T19 depend on T17.
    ────────────────────────────────────────
    Wave: 9
    Tasks: T20
    Rationale: run_pipeline orchestrator — depends on T17-19
    ────────────────────────────────────────
    Wave: 10
    Tasks: T21, T27
    Rationale: T21 (fix_mode) and T27 (init) are in separate files — fully
      parallel
    ────────────────────────────────────────
    Wave: 11
    Tasks: T22, T23, T28
    Rationale: T22/T23 on pipeline.py, T28 on roadmap.py — parallel across
      files
    ────────────────────────────────────────
    Wave: 12
    Tasks: T24, T25
    Rationale: T24 depends on T23, T25 depends on T24
    ────────────────────────────────────────
    Wave: 13
    Tasks: T26
    Rationale: run_fix_mode orchestrator
    ────────────────────────────────────────
    Wave: 14
    Tasks: T29
    Rationale: Depends on T28
    ────────────────────────────────────────
    Wave: 15
    Tasks: T31
    Rationale: run_init orchestrator
    ────────────────────────────────────────
    Wave: 16
    Tasks: T32
    Rationale: Import verification tests — depends on all refactors being
      complete
    
    Agent allocation: 1-2 coder agents per wave. The tightest dependencies are in the Phase 1 chain (T1→T4→T5→T8→T10).
    
    
    
    13. Build & Deploy
    
    - CI: python3 -m pytest tests/ -q on every push
    - Build check: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" — verifies no syntax errors introduced
    - Lint: python3 -m py_compile pipeline.py && python3 -m py_compile roadmap.py
    - Deploy: No deployment — dokima is a CLI tool installed via git clone + symlink
    - Env vars: None added. Existing env vars (PANEL_REASONING, PANEL_SKIP_ORCHESTRATOR_REVIEW, etc.) continue to work.
    
    
    
    14. Risk Register
    
    #: R1
    Risk: Sub-function signature mismatch causes NameError at import time
    Severity: HIGH
    Mitigation: Each refactor task runs python3 -m py_compile on the module
      before marking complete
    Trigger: Import fails in CI
    ────────────────────────────────────────
    #: R2
    Risk: Behavioral regression from incorrect extraction boundaries
    Severity: HIGH
    Mitigation: Full test suite (1,029 tests) must stay green. Run before and
      after every task.
    Trigger: Any test failure
    ────────────────────────────────────────
    #: R3
    Risk: Circular import from new sub-function referencing wrong module
    Severity: MEDIUM
    Mitigation: All sub-functions stay in the same module as their parent. No
      new cross-module imports.
    Trigger: ImportError on module load
    ────────────────────────────────────────
    #: R4
    Risk: Print() ordering change breaks cron job log parsing
    Severity: MEDIUM
    Mitigation: Preserve exact print() call order and flush=True placement.
      Match original line-by-line.
    Trigger: Log parsing in CI breaks
    ────────────────────────────────────────
    #: R5
    Risk: F040 (PipelineContext) merges first and creates conflicts
    Severity: MEDIUM
    Mitigation: F043 explicitly depends on F040 in roadmap. If F040 lands
      first, adjust sub-function signatures to accept ctx parameter.
    Trigger: Merge conflict on pipeline.py
    ────────────────────────────────────────
    #: R6
    Risk: run_init interview loop extraction breaks non-TTY answer collection
    Severity: LOW
    Mitigation: _run_interview_loop delegates to
      collect_init_interview_answers unchanged. No logic change.
    Trigger: test_f031_collect_answers fails
    
    
    
    15. Anti-Creep (NOT in Scope)
    
    - Do NOT introduce PipelineContext (F040). This feature uses the existing global-based architecture. F040 handles context migration separately.
    - Do NOT change any function signatures visible to callers. run_phase1_strategist, run_phase2_coder, run_pipeline, run_fix_mode, and run_init keep their exact parameter lists and return types.
    - Do NOT add type hints. Follow existing convention — the codebase uses docstrings, not type annotations.
    - Do NOT add logging frameworks, error telemetry, or metrics. Print() to stdout is the existing convention.
    - Do NOT restructure modules. All pipeline sub-functions stay in pipeline.py. All roadmap sub-functions stay in roadmap.py.
    - Do NOT optimize, deduplicate, or "while-I'm-here" refactor. If two sub-functions happen to share 5 lines of logic, leave the duplication. This feature is extraction only.
    - Do NOT add new test coverage beyond import verification. Existing tests cover behavior. Adding behavioral tests risks testing the test suite, not the code.
    - Do NOT modify the dokima entry point, utils.py, agent.py, tasks.py, status.py, or vcs.py. This feature touches pipeline.py and roadmap.py only.
    
    
    
    16. Sign-Off Checklist
    
    - [ ] All 1,029+ existing tests pass before any change begins (baseline)
    - [ ] After each task: python3 -m py_compile pipeline.py && python3 -m py_compile roadmap.py passes
    - [ ] After all tasks: python3 -m pytest tests/ -q — 0 new failures
    - [ ] Manual smoke test: dokima next "simple test feature" /tmp/dokima-test-repo completes without errors
    - [ ] Manual smoke test: dokima init "test project" /tmp/dokima-init-test produces all four docs
    - [ ] grep -c "^def " pipeline.py shows original 5 phase functions + new sub-functions (no deletions)
    - [ ] grep -c "^def " roadmap.py shows run_init + new sub-functions (no deletions)
    - [ ] No function exceeds 150 lines: awk '/^def /{name=$2; start=NR} /^$|^def /{if(start) print name, NR-start; start=0}' pipeline.py roadmap.py | awk '$2>150' returns empty
    - [ ] Code review: verify each sub-function is a pure extraction — no logic changes, no reordering
    - [ ] Git diff confirms only pipeline.py and roadmap.py changed (plus test files for T32)
    - [ ] Commit message follows convention: refactor: decompose phase functions into sub-operations (F043)