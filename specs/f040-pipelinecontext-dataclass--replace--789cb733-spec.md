# F040: PipelineContext dataclass — replace 20+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, etc.) with a single PipelineContext dataclass passed to each phase function. Eliminates conftest __setattr__ override hack. Makes testing trivial — create a context, pass it in. All 1,029 tests protect this refactor.

Now I have complete understanding of the codebase. Here is the corrected, complete spec:
    
    
    
    F040: PipelineContext Dataclass — Replace Module-Level Globals
    
    Version: 1.0.0
    Status: Spec Complete — Ready for Panel
    Confidence: High
    
    
    
    1. Executive Summary
    
    Replace 17 module-level globals spread across 7 files (PROJECT_DIR, REPO, DEFAULT_BRANCH, API_KEY, PANEL_FEATURE, etc.) with a single PipelineContext dataclass. This eliminates the conftest setattr override hack (lines 42-53) and the initial sync loop (lines 67-78) — both fragile workarounds for propagating mutable globals across F022's modular architecture. All 1,033 tests continue to pass, and test setup shrinks from 15 lines of module-reload+global-assignment boilerplate to ctx = PipelineContext(PROJECT_DIR="/tmp/test"). Every function that currently reads these globals receives ctx as its first parameter. No behavior change — purely an internal refactor.
    
    
    
    2. Constitution Check
    
    Axiom: Solve user's own pain?
    Assessment: Yes. The setattr hack is the #1 source of test fragility —
      every test file must _load_panel(), every new global must be added to
      the sync list in 3 places.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Assessment: Yes. Pure refactor — no new logic, no API surface change.
      9,349 lines touched but changes are mechanical.
    ────────────────────────────────────────
    Axiom: Evidence people want?
    Assessment: N/A (internal quality refactor)
    ────────────────────────────────────────
    Axiom: Boring/proven tech stack?
    Assessment: Yes. Python dataclasses — stdlib since 3.7, zero dependencies.
    ────────────────────────────────────────
    Axiom: Avoid AI hype?
    Assessment: Yes. No AI, no LLM, no vector DB.
    
    Verdict: All checks pass. This is the right refactor at the right time.
    
    
    
    3. What Changed
    
    This section documents the diff for humans reviewing the PR.
    
    Removed:
    - 17 module-level globals across dokima, utils.py, agent.py, pipeline.py, roadmap.py, tasks.py, vcs.py
    - 20 global statements across pipeline.py (12), utils.py (3), dokima (2), roadmap.py (2), vcs.py (1)
    - setattr override hack in tests/conftest.py (lines 42-53) — the _sync_globals_on_setattr closure
    - Initial sync loop in tests/conftest.py (lines 67-78) — the backward-compat sync of pre-setattr values
    - _IMPORTING_PANEL hack in utils.py, agent.py — used for stale-module workaround
    
    Added:
    - PipelineContext dataclass in context.py (~12 fields, frozen=False)
    - ctx: PipelineContext parameter on every function that currently reads globals (phase functions, post-pipeline, fix mode, init, next-setup, all VCS ops via vcs.py)
    - ctx fixture in tests/conftest.py — returns a default PipelineContext for test isolation
    - ctx parameter on WorktreeManager.init and TaskDAG.init (currently read PROJECT_DIR from module level)
    
    Changed (behavior-preserving):
    - test_repo fixture: sets ctx.PROJECT_DIR/ctx.REPO/ctx.DEFAULT_BRANCH instead of panel.PROJECT_DIR/panel.REPO/etc.
    - mock_orchestrator fixture: patches ctx fields instead of panel globals
    - All 21 test files that assign panel.GLOBAL = value → assign ctx.GLOBAL = value
    - dokima main(): constructs PipelineContext from parsed args/env and passes it through the call chain
    - vcs.py: detect_vcs_backend(ctx, project_dir) → populates ctx.REPO, ctx.VCS_BACKEND instead of module-level globals
    
    NOT changed:
    - HELP_TEXT (constant — stays module-level)
    - VERSION (computed constant — stays module-level)
    - PANEL_PORT, PROFILES, REAL_HOME, HERMES, HERMES_BIN (derived from REAL_HOME which is stable per machine — stay module-level constants)
    - _LOG_FILE_HANDLE, _LOCK_FD, _LOG_FILE, _STDOUT_ORIG, _GH_TOKEN_CACHE (process-level state, not pipeline config — stay module-level)
    - _PROVIDER_FAILURE_PATTERNS, FALLBACK_MODEL_RE (compiled regex constants — stay module-level)
    - MAX_CONTINUOUS (constant — stays module-level)
    - _PROFILE_CONFIGS, _PROFILE_ORDER (constants — stay module-level)
    
    
    
    4. Impact
    
    Files Modified (evidence from git grep / code inspection)
    
    File: context.py
    Current Lines: 0
    Nature of Change: NEW — PipelineContext dataclass
    Est. Lines Changed: +45
    ────────────────────────────────────────
    File: dokima
    Current Lines: 775
    Nature of Change: Construct ctx in main(), pass to all callees; remove
      global declarations
    Est. Lines Changed: +30/-60
    ────────────────────────────────────────
    File: utils.py
    Current Lines: 3,351
    Nature of Change: Remove 17 module-level globals; add ctx param to
      functions that reference globals
    Est. Lines Changed: +60/-80
    ────────────────────────────────────────
    File: agent.py
    Current Lines: 226
    Nature of Change: Remove API_KEY, FALLBACK_MODELS, _IMPORTING_PANEL
      globals; add ctx param to call_agent, spawn_agent
    Est. Lines Changed: +8/-12
    ────────────────────────────────────────
    File: pipeline.py
    Current Lines: 2,805
    Nature of Change: Remove 12 global statements; add ctx param to all 7
      phase/post-phase functions; replace direct global reads with ctx.
      attribute access
    Est. Lines Changed: +80/-40
    ────────────────────────────────────────
    File: roadmap.py
    Current Lines: 1,026
    Nature of Change: Remove 2 global statements; add ctx param to
      run_next_setup, run_init
    Est. Lines Changed: +12/-8
    ────────────────────────────────────────
    File: tasks.py
    Current Lines: 667
    Nature of Change: Remove PROJECT_DIR global; add ctx to WorktreeManager,
      TaskDAG, parallel coder functions
    Est. Lines Changed: +15/-5
    ────────────────────────────────────────
    File: vcs.py
    Current Lines: 268
    Nature of Change: Remove REPO global; detect_vcs_backend populates ctx
      instead; all ops receive ctx
    Est. Lines Changed: +10/-14
    ────────────────────────────────────────
    File: tests/conftest.py
    Current Lines: 231
    Nature of Change: Replace _load_panel() with ctx fixture; remove setattr
      hack and sync loop; simplify test_repo, mock_orchestrator
    Est. Lines Changed: +30/-120
    ────────────────────────────────────────
    File: 21 test files
    Current Lines: ~3,500
    Nature of Change: Replace panel.GLOBAL = value with ctx.GLOBAL = value
    Est. Lines Changed: +100/-100
    ────────────────────────────────────────
    File: TOTAL
    Current Lines: ~9,349
    Nature of Change:
    Est. Lines Changed: +390 / -439
    
    Dependency Impact
    
    - Blocks No One. pipeline.py, roadmap.py, tasks.py, utils.py, agent.py, vcs.py are all consumers of the globals being replaced — but all changes are mechanical and same-session.
    - Unblocks F041 (split utils.py into domain modules). F041 currently depends on F040 because utils.py's globals are the coupling point between future sub-modules. With ctx passed explicitly, the split becomes a pure file reorg.
    - Unblocks F043 (phase function decomposition). Phase functions currently use global PROJECT_DIR, REPO, ... — eliminating globals makes function extraction trivial.
    - Safe for parallel work. No other in-progress features touch these globals. F039 (real-code verification) is independent.
    
    
    
    5. Feature Breakdown
    
    
    
    Task 1: Create PipelineContext dataclass in context.py
    - Files: context.py (NEW)
    - Dependencies: None
    - Parallelizable: yes
    - Estimated LOC: ~45
    - Description: Create PipelineContext dataclass with fields: project_dir, repo, default_branch, api_key, panel_feature, panel_dir, output_log, hermes_bin, fallback_models, skip_autofix, force_full, skip_human_gate, max_parallel_override, resume, test_cmd, build_cmd, lint_cmd. Add vcs_backend and vcs_token_env fields for vcs.py migration. All fields have sensible defaults (empty string, False, None, etc.). Include __post_init__ that validates project_dir exists if set. No imports beyond dataclasses and os.
    
    Task 2: Add ctx fixture to tests/conftest.py
    - Files: tests/conftest.py
    - Dependencies: [Task 1]
    - Parallelizable: yes
    - Estimated LOC: ~30
    - Description: Create a ctx pytest fixture that returns a PipelineContext with test defaults (project_dir="/tmp/test-project", repo="test-owner/test-repo", api_key="test-key", default_branch="main", output_log="/dev/null", test_cmd="echo test", build_cmd="echo build", lint_cmd="echo lint"). Mark it autouse=False so tests opt in explicitly. This is the new way to create test contexts — no more _load_panel() for simple tests.
    
    Task 3: Migrate utils.py globals to ctx parameter
    - Files: utils.py
    - Dependencies: [Task 1]
    - Parallelizable: yes
    - Estimated LOC: ~140
    - Description: Remove 17 module-level globals from utils.py (lines 16-36). Add ctx: PipelineContext parameter to every function in utils.py that currently reads these globals. Key functions: _validate_project_dir, detect_repo, detect_commands, _detect_referenced_repo, _detect_default_branch, _set_gh_token, acquire_lock, _cleanup_lock, save_checkpoint, load_checkpoint, delete_checkpoint, validate_checkpoint, _phase_should_skip, try_auto_merge, _supplement_pr_sections, halt_and_revert, archive_specs_for_feature, generate_codebase_map, _check_pr_body_quality, verify_spec_quality, extract_pr_sections, clean_spec_content, _write_log_line, _redact_secrets, handle_status, handle_stop, handle_kill, handle_list_crons. Keep constants (HELP_TEXT, VERSION, MAX_CONTINUOUS, REAL_HOME, HERMES, PROFILES, HERMES_BIN) and process-level state (_LOG_FILE_HANDLE, _LOCK_FD, etc.) at module level.
    
    Task 4: Migrate agent.py globals to ctx parameter
    - Files: agent.py
    - Dependencies: [Task 1, Task 3]
    - Parallelizable: yes
    - Estimated LOC: ~20
    - Description: Remove API_KEY, FALLBACK_MODELS, _IMPORTING_PANEL, PANEL_PORT globals from agent.py (lines 13-14). Add ctx parameter to call_agent (reads API_KEY), spawn_agent (reads FALLBACK_MODELS, HERMES_BIN, OUTPUT_LOG), _run_agent (reads OUTPUT_LOG, HERMES_BIN), _detect_provider_failure (unchanged — no globals), _load_fallback_config (reads FALLBACK_MODELS). Keep _PROVIDER_FAILURE_PATTERNS and FALLBACK_MODEL_RE as module-level constants.
    
    Task 5: Migrate vcs.py globals to ctx parameter
    - Files: vcs.py
    - Dependencies: [Task 1]
    - Parallelizable: yes
    - Estimated LOC: ~24
    - Description: Remove VCS_BACKEND, VCS_TOKEN_ENV, REPO globals from vcs.py (lines 17-19). detect_vcs_backend(ctx, project_dir) sets ctx.vcs_backend, ctx.vcs_token_env, ctx.repo directly. All VCS operation functions (vcs_pr_create, vcs_pr_merge, vcs_pr_view, vcs_pr_list, vcs_pr_diff, vcs_issue_create, vcs_issue_view, vcs_release_create, vcs_pr_update_body, vcs_repo_clone, _run_vcs) receive ctx instead of reading module-level REPO/VCS_BACKEND/VCS_TOKEN_ENV.
    
    Task 6: Migrate tasks.py globals to ctx parameter
    - Files: tasks.py
    - Dependencies: [Task 1, Task 3]
    - Parallelizable: yes
    - Estimated LOC: ~20
    - Description: Remove PROJECT_DIR global from tasks.py (line 33). WorktreeManager.init receives ctx instead of project_root string (derives path from ctx.project_dir). TaskDAG.init receives ctx. run_parallel_coders, spawn_coder_in_worktree, merge_worktree_branches, _reap_completed, _poll_until_wave_done receive ctx. Remove imports of globals from utils (HERMES_BIN, DEFAULT_BRANCH, PANEL_FEATURE, TEST_CMD, BUILD_CMD, LINT_CMD, FALLBACK_MODELS, max_parallel_override, OUTPUT_LOG) — all now accessed via ctx.
    
    Task 7: Migrate pipeline.py globals to ctx parameter
    - Files: pipeline.py
    - Dependencies: [Task 1, Task 3, Task 4, Task 5, Task 6]
    - Parallelizable: no (depends on all module migrations being done first)
    - Estimated LOC: ~120
    - Description: Remove all 12 global statements from pipeline.py. Add ctx: PipelineContext as first parameter to: run_phase1_strategist, run_phase2_coder, run_phase3_vet, run_phase4_nm, run_phase5_tech_lead, run_fix_mode, run_pipeline, run_post_pipeline, discover_blocked_pr, extract_blockers_from_pr, _verify_pr_impact_alignment. Replace every PROJECT_DIR, REPO, DEFAULT_BRANCH, TEST_CMD, BUILD_CMD, LINT_CMD, OUTPUT_LOG, PANEL_FEATURE, PROFILES, REAL_HOME direct reference with ctx. attribute access. This is the largest mechanical change — ~80 lines replaced.
    
    Task 8: Migrate roadmap.py globals to ctx parameter
    - Files: roadmap.py
    - Dependencies: [Task 1, Task 7]
    - Parallelizable: no (depends on pipeline.py to avoid merge conflicts)
    - Estimated LOC: ~20
    - Description: Remove 2 global statements from roadmap.py. Add ctx parameter to run_next_setup (reads PROJECT_DIR, REPO, DEFAULT_BRANCH) and run_init (reads API_KEY, PROJECT_DIR, REPO). Replace direct global reads with ctx. attribute access.
    
    Task 9: Migrate dokima main() to construct and pass ctx
    - Files: dokima
    - Dependencies: [Task 7, Task 8]
    - Parallelizable: no (top-level integration — must be last)
    - Estimated LOC: ~90
    - Description: In main(), construct PipelineContext(...) from parsed args and environment after argument parsing. Remove the global API_KEY, PROJECT_DIR, REPO, ... declaration. Pass ctx to every callee: run_pipeline(ctx, feature, ...), run_fix_mode(ctx, project_dir, ...), run_init(ctx, description, project_dir, ...), run_next_setup(ctx, ...), run_add_to_roadmap(ctx, ...), generate_codebase_map(ctx.project_dir). Remove module-level globals from dokima (lines 70-78): OUTPUT_LOG, DEFAULT_BRANCH, SKIP_AUTOFIX, FORCE_FULL, SKIP_HUMAN_GATE, max_parallel_override, FALLBACK_MODELS, RESUME, MAX_CONTINUOUS. Derive OUTPUT_LOG inside main() before constructing ctx (it uses datetime.datetime.now()).
    
    Task 10: Migrate test files from panel.GLOBAL to ctx.GLOBAL
    - Files: tests/test_f023_self_healing.py, tests/test_triple_bug_fix.py, tests/test_final_edge.py, tests/test_final_coverage.py, tests/test_functions_unit.py, tests/test_acquire_lock.py, tests/test_detect_commands.py, tests/test_edge_cases.py, tests/test_f003_robustness.py, tests/test_f002_closure.py, tests/test_conftest_fixtures.py, tests/test_execution_mode_dispatch.py, tests/test_f022_pipeline.py, tests/test_f022_roadmap.py, tests/test_f022_tasks.py, tests/test_f022_utils.py, tests/test_f022_utils_complete.py, tests/test_f022_agent.py, tests/test_clean_spec.py, tests/test_codebase_map.py, tests/test_control_panel.py
    - Dependencies: [Task 2, Task 9]
    - Parallelizable: yes (all 21 test files are independent of each other)
    - Estimated LOC: ~200
    - Description: Replace all panel.PROJECT_DIR = ..., panel.REPO = ..., panel.DEFAULT_BRANCH = ..., panel.API_KEY = ..., panel.PANEL_FEATURE = ... assignments with ctx.PROJECT_DIR = ... etc. Update test_repo fixture to receive and modify ctx instead of panel. Update mock_orchestrator fixture to patch ctx fields. Replace _load_panel() calls with PipelineContext(...) in tests that bypass the panel fixture. Tests that need the full panel module for behavior verification continue using the panel fixture — only global-setting lines change.
    
    Task 11: Simplify conftest.py — remove setattr hack
    - Files: tests/conftest.py
    - Dependencies: [Task 10]
    - Parallelizable: no (must run after all test migrations to ensure nothing breaks)
    - Estimated LOC: ~50 (net -90)
    - Description: Remove _sync_globals_on_setattr (lines 42-53) and the initial sync loop (lines 67-78). Remove _IMPORTING_PANEL linkage (lines 62-65). Simplify _load_panel() to no longer set module globals or install setattr — it becomes _load_panel(ctx: PipelineContext) that injects ctx into the module's namespace for backward compat during transition, or is removed entirely if all callers have migrated. The panel fixture remains but no longer needs the sys.modules save/restore dance since modules don't carry mutable globals.
    
    Task 12: Run full test suite and verify 100% pass rate
    - Files: None (verification only)
    - Dependencies: [Task 11]
    - Parallelizable: no
    - Estimated LOC: 0
    - Description: Run python3 -m pytest tests/ -q. Verify all 1,033 tests pass, 4 skipped (unchanged). Run python3 -m pytest tests/ -q --ignore=tests/test_main_integration.py for quick suite. Verify no global statements remain in production code. Verify setattr is not present in conftest.py. Run python3 -m py_compile on all modified files to catch syntax errors.
    
    
    
    6. Data Model
    
    PipelineContext
    
    
    @dataclass
    class PipelineContext:
        # Paths
        project_dir: str = ""
        panel_dir: str = ""
        output_log: str = "/tmp/dokita-output.txt"
        hermes_bin: str = ""  # derived from REAL_HOME, default set by main()
    
        # VCS
        repo: str = ""
        default_branch: str = "master"
        vcs_backend: str = "github"
        vcs_token_env: str = "GH_TOKEN"
    
        # Auth
        api_key: str = ""
    
        # Feature
        panel_feature: str = ""
    
        # Commands (from AGENTS.md detection)
        test_cmd: str = "npm test"
        build_cmd: str = "npm run build"
        lint_cmd: str = "npm run lint"
    
        # Model fallback
        fallback_models: dict = field(default_factory=dict)
    
        # Feature flags
        skip_autofix: bool = False
        force_full: bool = False
        skip_human_gate: bool = False
        max_parallel_override: int | None = None
        resume: bool | None = None
    
    
    Frozen? No (frozen=False). The main() function mutates fields during startup (e.g., detect_vcs_backend sets ctx.repo, ctx.vcs_backend). Phase functions read-only. Tests mutate freely for setup.
    
    Storage: Transient — constructed in main(), garbage-collected at process exit. Not serialized.
    
    What stays module-level: HELP_TEXT, VERSION, MAX_CONTINUOUS, REAL_HOME, HERMES, PROFILES, HERMES_BIN (derived once at import time), PANEL_PORT, compiled regex patterns, _LOG_FILE_HANDLE, _LOCK_FD, _LOG_FILE, _STDOUT_ORIG, _GH_TOKEN_CACHE, _PROFILE_CONFIGS, _PROFILE_ORDER. These are either true constants, process-level handles, or derived-once-from-pwd values that never change during a process lifetime.
    
    
    
    7. API Routes
    
    Not applicable — this is an internal refactor. No external API surface changes. CLI behavior is identical. dokima add, dokima next, dokima fix, dokima init, dokima status, dokima stop, dokima kill all work exactly as before.
    
    
    
    8. Component Tree
    
    Not applicable — no UI/frontend. This is a Python CLI engine.
    
    
    
    9. COTS Build-vs-Buy
    
    Component: PipelineContext
    Decision: Build
    Justification: 45-line dataclass. No library needed. Python stdlib
      dataclasses is the COTS here.
    ────────────────────────────────────────
    Component: Dependency injection framework
    Decision: Skip
    Justification: pip install dependency-injector would be 10x the LOC of
      just passing ctx. YAGNI.
    ────────────────────────────────────────
    Component: Pydantic/settings management
    Decision: Skip
    Justification: No validation beyond os.path.exists. pydantic would add a
      dependency for zero benefit.
    ────────────────────────────────────────
    Component: contextvars (stdlib)
    Decision: Skip
    Justification: Would be implicit magic — same problem as globals. Explicit
      ctx parameter is the point.
    
    Verdict: Pure stdlib — zero new dependencies. dataclasses is the only import added, and it's been in stdlib since Python 3.7.
    
    
    
    10. Test Plan (MANDATORY)
    
    Happy Path
    - Create a PipelineContext(PROJECT_DIR="/tmp/test", REPO="o/r"), pass to run_pipeline(ctx, "F001: test", False, False, None). Pipeline runs all 5 phases. All globals previously set as module-level are accessed via ctx. — no AttributeError, no NameError.
    - run_phase1_strategist(ctx, "F001: test", None) returns a dict with spec, spec_path, pr_sections, etc. — same keys as before.
    - run_fix_mode(ctx, "/tmp/test-project") discovers blocked PRs using ctx.repo instead of module-level REPO.
    - detect_vcs_backend(ctx, "/tmp/test-project") sets ctx.vcs_backend, ctx.vcs_token_env, ctx.repo.
    
    Edge Cases
    - Empty context: PipelineContext() with all defaults. _validate_project_dir(ctx) should reject empty project_dir gracefully (existing behavior).
    - None values: PipelineContext(max_parallel_override=None, resume=None). Phase functions must handle ctx.max_parallel_override is None correctly (existing behavior).
    - Missing api_key: Phase 1 strategist receives ctx.api_key = "". Should fail with clear error (existing behavior — load_key() is called in main(), not affected).
    - ctx mutation during pipeline: A phase function mutates ctx.panel_feature. Next phase sees the new value. This is acceptable (same as current global mutation pattern) but should be documented.
    - Concurrent ctx access: Two parallel coders both read ctx.test_cmd. No mutation — safe. If one mutates ctx.skip_autofix, the other sees the change. This matches current global behavior — no regression.
    
    Failure Modes
    - Missing ctx parameter: A function in utils.py that wasn't updated still reads module-level PROJECT_DIR. It will read an empty string (the module-level default) instead of the test value. This should be caught by tests that set ctx.project_dir to a non-default value — the function will fail with "PROJECT_DIR not set" or produce wrong output.
    - ctx passed to function that doesn't accept it: TypeError: unexpected keyword argument. Caught at import time by py_compile, at test time by pytest.
    - ctx field name mismatch: ctx.project_dir vs ctx.PROJECT_DIR. Dataclass enforces correct field names — AttributeError at runtime.
    - vcs.py _run_vcs reads ctx.repo that wasn't set: detect_vcs_backend sets it. If called without detection first, ctx.repo is empty string — VCS commands fail with clear error.
    
    Contract Invariants
    - After main() constructs ctx, ctx.project_dir is a valid existing directory containing .git
    - After detect_vcs_backend(ctx, project_dir), ctx.repo is non-empty if the remote was detected
    - Phase functions never mutate ctx.project_dir, ctx.repo, ctx.default_branch, ctx.test_cmd, ctx.build_cmd, ctx.lint_cmd
    - ctx.output_log is set once in main() and never changes
    - _load_panel() in tests (if retained for backward compat) does NOT install setattr
    
    
    
    11. Panel Split
    
    Wave 1 (parallel — no shared files):
    - Task 1: context.py (NEW) — no dependencies
    - Task 2: ctx fixture in conftest.py — depends on Task 1 but different file
    - Task 3: utils.py migration — depends on Task 1, different file from Task 2
    - Task 5: vcs.py migration — depends on Task 1, different file from all above
    - Task 6: tasks.py migration — depends on Tasks 1, 3 (imports from utils), but different file from Task 5
    
    Wave 2 (sequential — shares files or depends on Wave 1):
    - Task 4: agent.py migration — depends on Tasks 1, 3
    - Task 7: pipeline.py migration — depends on Tasks 1, 3, 4, 5, 6 (pipeline calls all modules)
    - Task 8: roadmap.py migration — depends on Tasks 1, 7 (to avoid merge conflicts with pipeline.py bulk changes)
    
    Wave 3 (sequential — integration layer):
    - Task 9: dokima main() — depends on Tasks 7, 8
    - Task 10: migrate test files — depends on Tasks 2, 9
    
    Wave 4 (cleanup):
    - Task 11: simplify conftest.py — depends on Task 10
    - Task 12: final test run — depends on Task 11
    
    Coder count: 3 (Wave 1 fans out to 3 parallel coders; Waves 2-4 are sequential per file contention)
    
    
    
    12. Build & Deploy
    
    Build: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" + python3 -m py_compile context.py utils.py agent.py pipeline.py roadmap.py tasks.py vcs.py
    
    CI: python3 -m pytest tests/ -q (same as existing — no new CI steps)
    
    Deploy: No deploy — this is a Python script. dokima symlink doesn't change. install.sh doesn't change.
    
    Env vars: None added or removed. API_SERVER_KEY, GH_TOKEN, PANEL_FALLBACK_*, PANEL_SKIP_AUTOFIX, PANEL_FORCE_FULL, PANEL_SKIP_HUMAN_GATE, PANEL_RESUME are read in main() and stored in ctx — same behavior, different storage location.
    
    
    
    13. Risk Register
    
    #: R1
    Risk: Stale global statement missed — function reads empty module-level
      default instead of ctx value
    Severity: HIGH
    Mitigation: Grep for ^\s*global\s after migration — zero matches required.
      Tests that set non-default ctx values (e.g.,
      ctx.project_dir="/tmp/test") will fail if a function reads the
      module-level empty string.
    Trigger: CI fails.
    ────────────────────────────────────────
    #: R2
    Risk: _IMPORTING_PANEL removal breaks F022b's stale-module workaround in
      tests
    Severity: MEDIUM
    Mitigation: The workaround exists because of the global-sync problem. Once
      globals are gone, there's nothing to sync. _isolate_panel_modules
      fixture may become unnecessary — verify with a full test run. If some
      tests still rely on it, keep the fixture but remove _IMPORTING_PANEL
      linkage.
    Trigger: Test isolation failures in CI.
    ────────────────────────────────────────
    #: R3
    Risk: Test file that bypasses the panel fixture and directly sets module
      globals breaks
    Severity: MEDIUM
    Mitigation: grep -r "_load_panel()" tests/ to find non-fixture callers.
      These tests need explicit ctx construction. Most already go through the
      panel fixture.
    Trigger: Individual test failures — each is isolated.
    ────────────────────────────────────────
    #: R4
    Risk: vcs.py functions called before detect_vcs_backend() — ctx.repo is
      empty
    Severity: LOW
    Mitigation: detect_vcs_backend() is called in main() before any VCS
      operation. The refactor preserves this ordering. Add assertion in
      _run_vcs: assert ctx.repo, "ctx.repo not set — call detect_vcs_backend()
      first".
    Trigger: VCS command fails with assertion error.
    ────────────────────────────────────────
    #: R5
    Risk: HERMES_BIN duplicate definition — dokima and utils.py both define it
    Severity: LOW
    Mitigation: After migration, ctx.hermes_bin is set by main(). Remove both
      module-level definitions. Functions use ctx.hermes_bin.
    Trigger: AttributeError if ctx.hermes_bin is empty.
    ────────────────────────────────────────
    #: R6
    Risk: OUTPUT_LOG with timestamp in name — constructed in main(), stored in
      ctx
    Severity: LOW
    Mitigation: Move the datetime.datetime.now() call to main() before
      constructing ctx. Update any code that read the module-level OUTPUT_LOG
      to use ctx.output_log.
    Trigger: Timestamp mismatch if referenced after midnight (unlikely in a
      single pipeline run).
    
    
    
    14. Anti-Creep
    
    Features explicitly NOT in scope for F040:
    
    - Do NOT add type hints to functions that currently lack them. Adding ctx: PipelineContext is the only type annotation change.
    - Do NOT refactor function bodies beyond replacing global X with ctx.X reads. No restructuring, no extraction.
    - Do NOT add validation logic to PipelineContext.__post_init__ beyond the existing _validate_project_dir pattern.
    - Do NOT convert PipelineContext to frozen=True — mutation is used intentionally in main() and tests.
    - Do NOT introduce dependency injection frameworks — pip install nothing new.
    - Do NOT change CLI behavior, help text, or output format.
    - Do NOT touch nm or vet bash scripts — they don't use Python globals.
    - Do NOT change the dokima shebang or install.sh.
    - Do NOT add ctx to functions that don't read any global — e.g., slugify, _hash_output, _detect_truncation are pure functions with no global dependencies.
    
    
    
    15. Sign-Off Checklist
    
    - [ ] PipelineContext field list approved — all 17 globals captured, nothing missed
    - [ ] Decision on HERMES_BIN duplication: set only in main(), removed from utils.py
    - [ ] Decision on OUTPUT_LOG construction: moved to main(), stored in ctx
    - [ ] Decision on PANEL_PORT and PROFILES: stay module-level constants (derived from REAL_HOME)
    - [ ] Decision on _IMPORTING_PANEL removal: confirmed it only existed for global sync
    - [ ] Task 1-12 ordering approved — Wave 1 parallelism validated (context.py, conftest, utils, vcs, tasks all different files)
    - [ ] Test migration strategy approved: ctx fixture + mechanical panel.X → ctx.X replacement
    - [ ] Anti-creep boundaries confirmed: no type hints beyond ctx, no function body refactors, no new deps
    - [ ] 3-coder panel allocation for Wave 1 approved
    - [ ] Acceptance criteria: grep "global " dokima utils.py agent.py pipeline.py roadmap.py tasks.py vcs.py returns 0 matches
    - [ ] Acceptance criteria: grep "setattr" tests/conftest.py returns 0 matches
    - [ ] Acceptance criteria: 1,033 tests pass, 4 skipped (unchanged)