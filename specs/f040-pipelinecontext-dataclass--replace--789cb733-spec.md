# F040: PipelineContext dataclass — replace 20+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, etc.) with a single PipelineContext dataclass passed to each phase function. Eliminates conftest __setattr__ override hack. Makes testing trivial — create a context, pass it in. All 1,029 tests protect this refactor.

Now I have all the evidence. Here is the complete corrected spec.
    
    
    
    F040: PipelineContext Dataclass — Replace Module-Level Globals
    
    Executive Summary
    
    Dokima currently uses 25+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, API_KEY, etc.) scattered across utils.py, agent.py, pipeline.py, and the dokima entry point. Functions mutate these via global declarations (18 instances across 4 files). Testing requires conftest's setattr override hack (lines 41-53) that intercepts assignments and syncs to sub-modules. This refactor replaces all pipeline state with a single PipelineContext dataclass passed explicitly to every phase function. Testing becomes trivial: create a context, pass it in. All 1,029 tests protect this refactor. Confidence: High.
    
    Constitution Check
    
    Axiom: Solve user's own pain?
    Status: ✅ YES
    Notes: Every test writer suffers the conftest hack; every contributor
      traces global declarations through 8+ functions
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: ✅ YES
    Notes: ~500 LOC refactor, 10-15 tasks, one session
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A
    Notes: Internal refactor — not a product feature
    ────────────────────────────────────────
    Axiom: Boring, proven tech?
    Status: ✅ YES
    Notes: Python dataclass, explicit parameter passing — no new frameworks
    ────────────────────────────────────────
    Axiom: Avoid AI hype?
    Status: ✅ YES
    Notes: Pure structural refactor, zero AI
    
    Verdict: PASS. No misalignments.
    
    Impact
    
    Files touched: dokima (+30/-20), utils.py (+25/-200), agent.py (+10/-15), pipeline.py (+40/-110), roadmap.py (+10/-10), vcs.py (+5/-5), tasks.py (+5/-0), tests/conftest.py (+15/-55), 30+ test files (minor signature updates).
    
    Breaking change. Every call site that references utils.PROJECT_DIR, utils.REPO, etc. must be updated. All 1,029 tests will need signature adjustments. This is a safe breaking change because tests ARE the safety net — if anything breaks, tests catch it immediately.
    
    Global declarations eliminated: 18 global statements removed across pipeline.py (12), roadmap.py (2), utils.py (2), vcs.py (2). Functions become pure — no hidden state.
    
    Conftest hack eliminated: The setattr override (lines 41-53) and F022 sync logic (lines 60-78) are completely removed. Tests create PipelineContext(...) directly instead of monkey-patching module attributes.
    
    Refs: pipeline.py has 132 references to old globals — highest-touch file. roadmap.py, vcs.py each reference globals in 2 functions. agent.py duplicates PANEL_PORT, API_KEY, FALLBACK_MODELS (already defined in utils.py).
    
    What Changed
    
    - Added: PipelineContext dataclass in utils.py — single source of truth for all pipeline configuration
    - Added: ctx parameter to all phase functions (run_phase1_strategist, run_phase2_coder, run_phase3_vet, run_phase4_nm, run_phase5_tech_lead, run_pipeline, run_fix_mode, run_fix_mode_issue, run_post_pipeline)
    - Added: ctx parameter to utility functions that read globals (load_key, git, gh, _safe_run, _write_log_line, acquire_lock, _cleanup_lock, save_checkpoint, load_checkpoint, delete_checkpoint, _signal_handler)
    - Added: ctx parameter to roadmap functions (run_add_to_roadmap, run_next_setup, run_init) and vcs functions
    - Removed: 25+ module-level global assignments in utils.py (lines 11-52), agent.py (lines 12-16)
    - Removed: All 18 global declarations from pipeline.py, roadmap.py, utils.py, vcs.py
    - Removed: conftest.py setattr override hack (lines 41-53) and F022 sync logic (lines 60-78)
    - Removed: Duplicate globals in agent.py (API_KEY, PANEL_PORT, FALLBACK_MODELS — now in context)
    - Updated: conftest fixtures (panel, test_repo, mock_orchestrator) to create/use PipelineContext instead of module attribute assignment
    
    Data Model
    
    python
    @dataclass
    class PipelineContext:
        # Project identity
        project_dir: str                    # was: utils.PROJECT_DIR
        repo: str                          # was: utils.REPO
        default_branch: str = "master"     # was: utils.DEFAULT_BRANCH
        panel_feature: str = ""            # was: utils.PANEL_FEATURE
        panel_dir: str = ""                # was: utils.PANEL_DIR
    
        # Paths (computed at startup, immutable per run)
        real_home: str = ""                # was: utils.REAL_HOME
        hermes_home: str = ""              # was: utils.HERMES
        hermes_bin: str = ""               # was: utils.HERMES_BIN
        profiles_dir: str = ""             # was: utils.PROFILES
        output_log: str = ""               # was: utils.OUTPUT_LOG
    
        # API
        api_key: str = ""                  # was: utils.API_KEY
    
        # Agent ports
        panel_port: dict = field(default_factory=lambda: {  # was: utils.PANEL_PORT
            "strategist": 8647, "tech-lead": 8644,
            "coder": 8645, "nm": 8648
        })
    
        # Model fallback
        fallback_models: dict = field(default_factory=dict)  # was: utils.FALLBACK_MODELS
    
        # Pipeline flags
        skip_autofix: bool = False         # was: utils.SKIP_AUTOFIX
        force_full: bool = False           # was: utils.FORCE_FULL
        skip_human_gate: bool = False      # was: utils.SKIP_HUMAN_GATE
        max_parallel_override: int | None = None  # was: utils.max_parallel_override
        resume: bool | None = None         # was: utils.RESUME
        max_continuous: int = 20           # was: utils.MAX_CONTINUOUS
    
        # Project commands (detected from AGENTS.md)
        test_cmd: str = "npm test"         # was: utils.TEST_CMD
        build_cmd: str = "npm run build"   # was: utils.BUILD_CMD
        lint_cmd: str = "npm run lint"     # was: utils.LINT_CMD
    
        # Transient runtime state (was module-level globals in utils)
        _log_file_handle: Any = field(default=None, repr=False)
        _lock_fd: Any = field(default=None, repr=False)
        _log_file: Any = field(default=None, repr=False)
        _stdout_orig: Any = field(default=None, repr=False)
        _gh_token_cache: str | None = field(default=None, repr=False)
    
    
    Storage: In-memory only. Created in main(), passed through the call chain. No serialization needed — checkpoint logic already handles its own paths.
    
    What stays module-level: VERSION, HELP_TEXT, CLI_METADATA (true constants, never mutated). _PROVIDER_FAILURE_PATTERNS, FALLBACK_MODEL_RE (compiled regex, immutable). _IMPORTING_PANEL (test override detection — addressed separately in Task 15).
    
    API Routes
    
    N/A — this is an internal refactor. No external API surface changes.
    
    Component Tree
    
    N/A — not a frontend feature.
    
    COTS Build-vs-Buy
    
    Component: PipelineContext
    Decision: Build
    Justification: Standard Python dataclass — 30 lines, zero dependencies
    ────────────────────────────────────────
    Component: Type checking
    Decision: Buy (stdlib)
    Justification: dataclasses.dataclass, typing.Optional — already in Python
      3.6+
    
    Nothing to buy. This is purely a structural refactor using Python's standard library.
    
    Test Plan (MANDATORY)
    
    Happy path
    - Create a PipelineContext(project_dir="/tmp/test", repo="o/r", api_key="k") and pass it to run_pipeline(ctx, feature="test"). Pipeline runs all phases, no exceptions.
    - Each phase function accepts ctx as first positional argument. Existing mock-based tests pass with updated signatures.
    - conftest.py fixtures create context objects instead of monkey-patching module attributes.
    
    Edge cases
    - Default values: Create PipelineContext() with no arguments — all fields have sensible defaults (empty strings, False, default ports). No NoneType errors.
    - Mutable defaults: panel_port and fallback_models use field(default_factory=...) to avoid shared-mutable-default trap.
    - Context isolation: Two tests creating different PipelineContext objects do not interfere — no shared global state.
    - Missing AGENTS.md: test_cmd/build_cmd/lint_cmd default to "npm test" etc. when AGENTS.md is absent — pipeline doesn't crash.
    - Large repo name: repo="very-long-org-name/very-long-repo-name-with-many-chars" — gh commands handle it.
    - Unicode project_dir: Paths with non-ASCII characters (CJK, emoji in dir name) — subprocess calls work.
    - Concurrent pipelines: Two PipelineContext objects in separate threads share no mutable state.
    
    Failure modes
    - Missing required fields: run_pipeline(ctx) where ctx.project_dir is empty string — raises ValueError with clear message.
    - Invalid hermes_bin: Path doesn't exist — spawn_agent fails with clear error, not a silent hang.
    - Bad default_branch: Branch doesn't exist in repo — git checkout fails, pipeline catches and reports.
    - Empty api_key: API calls get 401 — pipeline detects provider failure, triggers fallback or fails cleanly.
    - Context passed to old-style function: Function expecting module globals but receiving context — AttributeError. Caught by type checker (mypy) in CI, not at runtime.
    
    Contract invariants
    - ctx.project_dir is never mutated after main() sets it (except in run_fix_mode which rebinds the local ctx — safe because it's a new object).
    - ctx.api_key is never logged or printed — _redact_secrets protects it.
    - ctx._log_file_handle is closed on pipeline exit — _cleanup_lock or atexit handler.
    - No function reads utils.PROJECT_DIR after the refactor — verified by grep -r "utils\.PROJECT_DIR\|utils\.REPO\|utils\.DEFAULT_BRANCH" returning zero results.
    
    Feature Breakdown
    
    Task 1: Define PipelineContext dataclass in utils.py
    - Files: utils.py
    - Dependencies: none
    - Parallelizable: yes
    - Description: Add @dataclass class PipelineContext with all 30 fields documented in the Data Model section above. Import dataclass, field, Any from dataclasses/typing. Place at top of utils.py after imports, before existing globals. Do NOT remove existing globals yet — keep both in parallel during transition.
    
    Task 2: Create PipelineContext at startup in dokima main()
    - Files: dokima
    - Dependencies: [Task 1]
    - Parallelizable: no (same file as Task 3)
    - Description: In main(), after parsing all flags and detecting project config, construct PipelineContext(...) with all resolved values. Store as ctx. Do NOT pass it to functions yet — just create it and verify it builds.
    
    Task 3: Add ctx parameter to pipeline.py phase functions — signature only
    - Files: pipeline.py
    - Dependencies: [Task 1]
    - Parallelizable: no (same file as Task 4-8)
    - Description: Add ctx: PipelineContext as first parameter to all 11 functions that currently use global declarations: run_pipeline, run_phase1_strategist, run_phase2_coder, run_phase3_vet, run_phase4_nm, run_phase5_tech_lead, run_post_pipeline, run_fix_mode, run_fix_mode_issue, discover_blocked_pr, extract_blockers_from_pr. Signature change only — functions still use globals internally.
    
    Task 4: Refactor run_phase1_strategist — switch globals to ctx
    - Files: pipeline.py
    - Dependencies: [Task 3]
    - Parallelizable: no (same file)
    - Description: Replace all global PROJECT_DIR, REPO, DEFAULT_BRANCH, TEST_CMD, BUILD_CMD in run_phase1_strategist with ctx.project_dir, ctx.repo, etc. Remove the global declaration. This is the 656-line, CC=125 function — do NOT restructure logic, only swap variable references.
    
    Task 5: Refactor run_phase2_coder — switch globals to ctx
    - Files: pipeline.py
    - Dependencies: [Task 3]
    - Parallelizable: no (same file)
    - Description: Replace all global PROJECT_DIR, REPO, DEFAULT_BRANCH, TEST_CMD, BUILD_CMD, LINT_CMD in run_phase2_coder with ctx field access. Remove global declaration.
    
    Task 6: Refactor run_phase3_vet, run_phase4_nm, run_phase5_tech_lead — switch globals to ctx
    - Files: pipeline.py
    - Dependencies: [Task 3]
    - Parallelizable: no (same file)
    - Description: Replace all global declarations in run_phase3_vet (PROJECT_DIR, REPO, DEFAULT_BRANCH, TEST_CMD, BUILD_CMD), run_phase4_nm (TEST_CMD, BUILD_CMD, LINT_CMD), and run_phase5_tech_lead (PROJECT_DIR, REPO) with ctx field access. Remove global declarations.
    
    Task 7: Refactor run_pipeline — create and propagate ctx
    - Files: pipeline.py
    - Dependencies: [Task 4, Task 5, Task 6]
    - Parallelizable: no (same file)
    - Description: In run_pipeline, replace global PROJECT_DIR, PROFILES, REAL_HOME with ctx fields. Pass ctx to every phase function call: run_phase1_strategist(ctx, ...), run_phase2_coder(ctx, ...), etc. This is the integration point — all phase functions now receive ctx.
    
    Task 8: Refactor run_post_pipeline, run_fix_mode, run_fix_mode_issue, discover_blocked_pr, extract_blockers_from_pr
    - Files: pipeline.py
    - Dependencies: [Task 7]
    - Parallelizable: no (same file)
    - Description: Switch remaining pipeline.py functions from globals to ctx fields. Remove all remaining global declarations in pipeline.py (should be zero after this task).
    
    Task 9: Refactor roadmap.py — switch globals to ctx
    - Files: roadmap.py
    - Dependencies: [Task 1]
    - Parallelizable: yes (different file from pipeline.py tasks)
    - Description: Add ctx: PipelineContext parameter to functions using global REPO, DEFAULT_BRANCH, API_KEY, PROJECT_DIR (run_add_to_roadmap, run_next_setup, run_init). Replace global references with ctx fields. Remove global declarations.
    
    Task 10: Refactor vcs.py — switch globals to ctx
    - Files: vcs.py
    - Dependencies: [Task 1]
    - Parallelizable: yes (different file)
    - Description: Add ctx parameter to VCS functions using global VCS_BACKEND, VCS_TOKEN_ENV, REPO. Replace with ctx equivalents or compute from ctx fields. Remove global declarations.
    
    Task 11: Refactor agent.py — remove duplicate globals, use ctx
    - Files: agent.py
    - Dependencies: [Task 1]
    - Parallelizable: yes (different file)
    - Description: Remove duplicate module-level globals (API_KEY, PANEL_PORT, FALLBACK_MODELS — already defined in utils.py and now in ctx). Update call_agent, _run_agent to accept ctx or have ctx passed through spawn_agent. _run_agent currently reads HERMES_BIN — switch to ctx.hermes_bin.
    
    Task 12: Refactor utils.py functions — switch globals to ctx
    - Files: utils.py
    - Dependencies: [Task 1]
    - Parallelizable: yes (different file)
    - Description: Add ctx parameter to functions reading module globals: load_key, git, gh, _write_log_line, acquire_lock, _cleanup_lock, _signal_handler, save_checkpoint, load_checkpoint, delete_checkpoint, _safe_run, load_github_token. Replace PROJECT_DIR, OUTPUT_LOG, PROFILES, HERMES_BIN, DEFAULT_BRANCH references with ctx fields. Keep old signatures working via default ctx=None and fallback to globals during transition.
    
    Task 13: Remove module-level globals from utils.py
    - Files: utils.py
    - Dependencies: [Task 8, Task 12]
    - Parallelizable: no (must be after all consumers switch)
    - Description: Delete lines 11-52 in utils.py (all mutable module-level globals). Keep VERSION, HELP_TEXT, CLI_METADATA (true constants). Run full test suite — confirm zero failures.
    
    Task 14: Remove duplicate globals from agent.py
    - Files: agent.py
    - Dependencies: [Task 11, Task 13]
    - Parallelizable: no
    - Description: Delete lines 12-16 in agent.py (API_KEY, PANEL_PORT, FALLBACK_MODELS, _IMPORTING_PANEL). Keep _PROVIDER_FAILURE_PATTERNS, FALLBACK_MODEL_RE (compiled regex constants). Run tests — zero failures.
    
    Task 15: Update conftest.py — remove setattr hack, use PipelineContext
    - Files: tests/conftest.py
    - Dependencies: [Task 1]
    - Parallelizable: yes (tests can update signatures in parallel with source refactoring)
    - Description: Replace _load_panel()'s setattr hack (lines 41-53) and F022 sync logic (lines 60-78) with PipelineContext creation. The panel fixture should yield a tuple/module that includes a pre-built context. The test_repo fixture creates a context with the temp project_dir. The mock_orchestrator fixture patches ctx methods instead of module globals. Remove _IMPORTING_PANEL link setup (lines 60-65) — override detection can use mock.patch directly now.
    
    Task 16: Update test files — adapt signatures to use ctx
    - Files: tests/test_f022_pipeline.py, tests/test_f022_roadmap.py, tests/test_execution_mode_dispatch.py, tests/test_edge_cases.py, tests/test_f006_recovery.py, tests/test_continuous.py, tests/test_f031_init_loop.py, tests/test_f031_init_interview.py, tests/test_f031_collect_answers.py, tests/test_f032_agent_judge.py, tests/test_f034_fix_issue.py, tests/test_f037_blocker_resolution.py, tests/test_f038_pr_sections.py, tests/test_f039_real_code.py, tests/test_f023_self_healing.py, tests/test_conftest_fixtures.py, tests/test_f025_dashboard.py
    - Dependencies: [Task 15]
    - Parallelizable: yes (all test files are independent — no shared state)
    - Description: Update all test files that reference panel.PROJECT_DIR, panel.REPO, panel.DEFAULT_BRANCH, panel.TEST_CMD, panel.BUILD_CMD, panel.LINT_CMD, panel.API_KEY, panel.PANEL_FEATURE, panel.PANEL_DIR, panel.OUTPUT_LOG to use ctx.project_dir, ctx.repo, etc. Tests that call pipeline functions directly must pass ctx as first argument. Target: zero test failures after this task.
    
    Task 17: Update dokima entry point — wire ctx through all call sites
    - Files: dokima
    - Dependencies: [Task 8, Task 9, Task 10, Task 11, Task 12]
    - Parallelizable: no (must be after all function signatures update)
    - Description: In main(), pass ctx as first argument to every call from dokima to pipeline/roadmap/vcs functions: run_pipeline(ctx, ...), run_init(ctx, ...), run_fix_mode(ctx, ...), etc. Remove the old module-level global assignments (lines 65-78 in dokima — REAL_HOME through MAX_CONTINUOUS). These are now provided by ctx's factory or main() construction.
    
    Task 18: Final verification — grep for stale globals, run full suite
    - Files: none (verification only)
    - Dependencies: [Task 13, Task 14, Task 16, Task 17]
    - Parallelizable: no (final gate)
    - Description: Run grep -rn "utils\.PROJECT_DIR\|utils\.REPO\|utils\.DEFAULT_BRANCH\|utils\.API_KEY\|utils\.OUTPUT_LOG\|utils\.PANEL_FEATURE" .py tests/ — must return zero results. Run grep -rn "^\sglobal " pipeline.py roadmap.py utils.py agent.py vcs.py — must return zero results. Run python3 -m pytest tests/ -q — 1,029 pass, 4 skipped.
    
    Panel Split
    
    Wave: Wave 1
    Tasks: T1, T9, T10, T11, T12, T15
    Parallel coders: 6 (all independent files)
    ────────────────────────────────────────
    Wave: Wave 2
    Tasks: T2, T3
    Parallel coders: 2 (T2=dokima, T3=pipeline.py — different files after T1)
    ────────────────────────────────────────
    Wave: Wave 3
    Tasks: T4, T5, T6, T16
    Parallel coders: 4 (T4-6 are same file pipeline.py so sequential, T16 is
      all test files parallel)
    ────────────────────────────────────────
    Wave: Wave 4
    Tasks: T7, T8
    Parallel coders: 1 (sequential — both pipeline.py)
    ────────────────────────────────────────
    Wave: Wave 5
    Tasks: T13, T14, T17
    Parallel coders: 3 (T13=utils.py, T14=agent.py, T17=dokima — all different
      files)
    ────────────────────────────────────────
    Wave: Wave 6
    Tasks: T18
    Parallel coders: 1 (verification gate)
    
    Actual coder agents needed: 4-6. Pipeline.py work (T4-T8, ~7 tasks) should be one coder sequentially to avoid merge conflicts. All other files can fan out in parallel.
    
    Build & Deploy
    
    - Build: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')"
    - Test: python3 -m pytest tests/ -q — 1,029 pass, 4 skipped
    - Lint: python3 -m py_compile dokima
    - CI: No CI yet (F042 adds it later). Manual verification.
    - Deploy: No deployment — this is a structural refactor. dokima remains a single script.
    
    Risk Register
    
    Risk: Context not propagated to deep call chain
    Severity: HIGH
    Mitigation: Exhaustive grep for old globals (T18 verification gate).
      Functions with ctx=None default fall back to globals during transition.
    Trigger: Any test fails after T13
    ────────────────────────────────────────
    Risk: Pipeline.py merge conflicts from multi-coder
    Severity: MEDIUM
    Mitigation: Pipeline.py tasks (T3-T8) assigned to single coder
      sequentially. Other files parallelize.
    Trigger: Coder attempts parallel edits to pipeline.py
    ────────────────────────────────────────
    Risk: Test update scope underestimated
    Severity: MEDIUM
    Mitigation: T16 lists all 17 affected test files. Parallel test updates
      reduce wall-clock time.
    Trigger: New test failures not matching known patterns
    ────────────────────────────────────────
    Risk: _IMPORTING_PANEL breaking test override detection
    Severity: MEDIUM
    Mitigation: T15 addresses this. Without setattr sync, override detection
      uses mock.patch directly — simpler.
    Trigger: Tests using panel.spawn_agent = mock fail
    ────────────────────────────────────────
    Risk: VCS module (vcs.py) has its own global pattern
    Severity: LOW
    Mitigation: T10 handles this specifically. VCS_BACKEND/VCS_TOKEN_ENV can
      also move into ctx.
    Trigger: vcs.py tests fail
    ────────────────────────────────────────
    Risk: Mutable default in dataclass (PANEL_PORT dict)
    Severity: LOW
    Mitigation: Use field(default_factory=dict) — standard Python pattern,
      tested.
    Trigger: dict shared across contexts
    ────────────────────────────────────────
    Risk: Phase function call site misses ctx argument
    Severity: LOW
    Mitigation: Python raises TypeError immediately — no silent failure. Tests
      catch all call sites.
    Trigger: Phase function invoked without ctx
    ────────────────────────────────────────
    Risk: Performance regression from ctx passing
    Severity: VERY LOW
    Mitigation: Dataclass is a single object reference — zero overhead vs
      module globals.
    Trigger: Not applicable
    
    Anti-Creep
    
    Features explicitly NOT in scope:
    - Do NOT split utils.py — that's F041, separate feature.
    - Do NOT add CI pipeline — that's F042.
    - Do NOT decompose phase functions — that's F043.
    - Do NOT change any function logic — this is a pure mechanical refactor. If a function currently works, it works the same after.
    - Do NOT introduce type hints beyond PipelineContext — ctx: PipelineContext is sufficient. Full mypy typing is out of scope.
    - Do NOT serialize PipelineContext — no JSON/dict conversion, no checkpoint persistence of ctx.
    - Do NOT restructure the module layout — utils.py stays utils.py. Agent.py stays agent.py.
    - Do NOT add new tests — the 1,029 existing tests are the safety net. Update them, don't grow them.
    
    Sign-Off Checklist
    
    - [ ] PipelineContext dataclass covers all 25+ globals currently in use (T1)
    - [ ] All 18 global declarations removed from pipeline.py, roadmap.py, utils.py, vcs.py (T18 verification)
    - [ ] conftest.py setattr hack completely removed (T15)
    - [ ] conftest.py F022 sync logic (lines 60-78) completely removed (T15)
    - [ ] All pipeline phase functions accept ctx as first parameter (T3-T8)
    - [ ] All roadmap functions accept ctx (T9)
    - [ ] All VCS functions accept ctx (T10)
    - [ ] agent.py duplicate globals removed (T14)
    - [ ] utils.py mutable globals removed, constants preserved (T13)
    - [ ] Full test suite: python3 -m pytest tests/ -q → 1,029 pass, 4 skipped (T18)
    - [ ] Zero grep hits for old global access pattern (T18)
    - [ ] Zero global declarations in source modules (T18)