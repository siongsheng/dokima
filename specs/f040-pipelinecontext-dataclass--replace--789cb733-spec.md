# F040: PipelineContext dataclass — replace 20+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, etc.) with a single PipelineContext dataclass passed to each phase function. Eliminates conftest __setattr__ override hack. Makes testing trivial — create a context, pass it in. All 1,029 tests protect this refactor.

I now have complete understanding of the codebase. Let me produce the corrected spec with all three missing sections + corrected Task N: headers.
    
    
    
    F040: PipelineContext dataclass — Implementation Spec
    
    Status: Ready for Review | Confidence: High | Date: 2026-07-06
    
    
    
    1. Executive Summary
    
    Replace 20+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, PANEL_FEATURE, API_KEY, OUTPUT_LOG, HERMES_BIN, FALLBACK_MODELS, SKIP_AUTOFIX, FORCE_FULL, SKIP_HUMAN_GATE, max_parallel_override, RESUME, TEST_CMD, BUILD_CMD, LINT_CMD, PROFILES, PANEL_PORT, REAL_HOME, PANEL_DIR) spread across utils.py, vcs.py, and pipeline.py with a single PipelineContext dataclass. The context is constructed once in the dokima entry script and passed explicitly to every phase function. This eliminates the 50-line conftest setattr override hack (lines 42-53 of tests/conftest.py), the _sync_modules() propagation function (lines 758-772 of dokima), and 11 global statements in pipeline.py. Testing becomes trivial: ctx = PipelineContext(project_dir="/tmp/test", repo="t/t", ...); run_phase3_vet(ctx, ...). All 1,029 existing tests protect this refactor — they must pass identically post-merge.
    
    
    
    2. Constitution Check
    
    Axiom: Does it solve the user's own pain?
    Assessment: Yes. Every test file needs _load_panel() with 8+
      monkey-patches just to call a phase function. Every new test author hits
      the setattr hack and wonders why.
    ────────────────────────────────────────
    Axiom: Is it weekend-buildable?
    Assessment: Yes. Pure refactor with test safety net. 5-6 focused tasks,
      ~350 LOC total.
    ────────────────────────────────────────
    Axiom: Is there evidence people will pay?
    Assessment: N/A. Infrastructure quality for a FOSS tool.
    ────────────────────────────────────────
    Axiom: Is the tech stack boring and proven?
    Assessment: Yes. Python dataclasses.dataclass — stdlib since 3.7, zero
      dependencies.
    ────────────────────────────────────────
    Axiom: Does it avoid AI hype categories?
    Assessment: Yes. Pure engineering refactor.
    
    Verdict: All axioms pass. Proceed.
    
    
    
    3. Impact Section (Actual File Paths + LOC)
    
    Based on git diff origin/main...HEAD analysis of affected files:
    
    File: pipeline.py
    Type: Refactor: 11 global statements → ctx parameter in 9 functions
    Estimated ΔLOC: +15 / -55
    ────────────────────────────────────────
    File: utils.py
    Type: Remove 20+ module-level globals (lines 16-36); add PipelineContext
      import
    Estimated ΔLOC: +3 / -25
    ────────────────────────────────────────
    File: vcs.py
    Type: Remove module-level REPO (line 19)
    Estimated ΔLOC: +0 / -1
    ────────────────────────────────────────
    File: dokima (entry script)
    Type: Create ctx at startup, pass to run_pipeline; remove _sync_modules()
    Estimated ΔLOC: +25 / -28
    ────────────────────────────────────────
    File: tests/conftest.py
    Type: Remove setattr override (lines 31-78), replace with PipelineContext
      factory
    Estimated ΔLOC: +30 / -50
    ────────────────────────────────────────
    File: agent.py
    Type: Drop _IMPORTING_PANEL and module globals (line 23 area); accept ctx
      where needed
    Estimated ΔLOC: +5 / -10
    ────────────────────────────────────────
    File: tasks.py
    Type: Drop _IMPORTING_PANEL and module globals; accept ctx where needed
    Estimated ΔLOC: +5 / -10
    ────────────────────────────────────────
    File: roadmap.py
    Type: Drop _IMPORTING_PANEL; accept ctx where needed
    Estimated ΔLOC: +3 / -5
    ────────────────────────────────────────
    File: status.py
    Type: No change (already dataclass-based, no globals)
    Estimated ΔLOC: +0
    
    Total estimated ΔLOC: +86 / -184 (net -98 lines)
    
    Downstream dependencies: F041 (utils split) depends on F040. F043 (phase decomposition) depends on F040.
    
    
    
    4. What Changed (PR Body Template)
    
    This section describes what the merged PR will contain — used by the coder for the PR body.
    
    - PipelineContext dataclass added at pipeline.py (or standalone context.py) with all 20+ fields
    - Phase functions refactored: run_phase1_strategist(ctx, ...), run_phase2_coder(ctx, ...), run_phase3_vet(ctx, ...), run_phase4_nm(ctx, ...), run_phase5_tech_lead(ctx, ...), run_fix_mode(ctx, ...), run_fix_mode_issue(ctx, ...), run_post_pipeline(ctx, ...), run_pipeline(ctx, ...), discover_blocked_pr(ctx), extract_blockers_from_pr(ctx, ...)
    - _sync_modules() removed from entry script (lines 758-772)
    - conftest setattr hack removed — _load_panel() simplified to import + create ctx
    - Module-level globals removed from utils.py (lines 16-36), vcs.py (line 19)
    - Backward compatibility: _IMPORTING_PANEL references replaced with explicit ctx passing
    - All 1,029 tests pass identically
    
    
    
    5. Feature Breakdown
    
    Task 1: Create PipelineContext dataclass
    - Files: pipeline.py (or new context.py)
    - Dependencies: none
    - Parallelizable: no (foundation — everything depends on it)
    - Estimated LOC: ~50
    - Description: Define @dataclass class PipelineContext with all fields: project_dir, repo, default_branch, panel_feature, api_key, output_log, hermes_bin, fallback_models, skip_autofix, force_full, skip_human_gate, max_parallel_override, resume, test_cmd, build_cmd, lint_cmd, profiles_dir, panel_port, real_home, panel_dir. Add __post_init__ to compute hermes_bin and real_home from env if not provided. Add @classmethod from_environ(cls, project_dir, **overrides) factory. If creating standalone context.py, update dokima entry to import and export it.
    
    Task 2: Wire PipelineContext into entry script — remove _sync_modules()
    - Files: dokima
    - Dependencies: [Task 1]
    - Parallelizable: no
    - Estimated LOC: ~50
    - Description: In main(), construct PipelineContext after all CLI/env parsing completes (after _detect_default_branch, detect_commands, etc.). Pass ctx to run_pipeline(). Remove _sync_modules() function (lines 758-772). Remove all _utils.PROJECT_DIR = ... style assignments that currently happen at the end of main. The ctx is the single source of truth. Ensure --continuous loop updates ctx.panel_feature per iteration.
    
    Task 3: Refactor run_pipeline to accept ctx — cascade to all phase functions
    - Files: pipeline.py
    - Dependencies: [Task 1]
    - Parallelizable: no
    - Estimated LOC: ~80
    - Description: Add ctx: PipelineContext as first parameter to run_pipeline(). Replace all global PROJECT_DIR, REPO and direct uses of module globals with ctx.project_dir, ctx.repo, etc. Cascade: pass ctx to run_phase1_strategist(ctx, ...), run_phase2_coder(ctx, ...), run_phase3_vet(ctx, ...), run_phase4_nm(ctx, ...), run_phase5_tech_lead(ctx, ...), run_post_pipeline(ctx, ...), run_fix_mode(ctx, ...), run_fix_mode_issue(ctx, ...). Each of these functions drops its global statement and uses ctx.field instead. Update all f-string references ({PROJECT_DIR} → {ctx.project_dir}, {REPO} → {ctx.repo}, etc.).
    
    Task 4: Refactor discover_blocked_pr and extract_blockers_from_pr
    - Files: pipeline.py
    - Dependencies: [Task 3]
    - Parallelizable: no (same file as Task 3)
    - Estimated LOC: ~20
    - Description: discover_blocked_pr() has global REPO at line 213 — change to discover_blocked_pr(ctx). extract_blockers_from_pr() has global REPO at line 265 — change to extract_blockers_from_pr(ctx, ...). Replace all REPO references with ctx.repo. Update all call sites.
    
    Task 5: Remove module-level globals from utils.py — update tests
    - Files: utils.py, tests/conftest.py, all test files that use panel.PROJECT_DIR
    - Dependencies: [Task 3]
    - Parallelizable: no (conftest depends on finalized ctx shape)
    - Estimated LOC: ~60
    - Description: Remove module-level globals from utils.py lines 16-36 (PROJECT_DIR, REPO, DEFAULT_BRANCH, API_KEY, OUTPUT_LOG, HERMES_BIN, etc.). Replace _IMPORTING_PANEL = None with import of PipelineContext. Update functions in utils.py that read these globals to either accept ctx as parameter OR read from a module-level ctx reference set at startup. In conftest.py: Rewrite _load_panel() to return a PipelineContext instance instead of a module with setattr override. Remove lines 31-78 (the setattr + _sync_globals_on_setattr hack). Tests that do panel.PROJECT_DIR = ... will now do ctx = PipelineContext(project_dir=..., ...). The panel fixture yields a PipelineContext, not a module.
    
    Task 6: Remove module-level REPO from vcs.py
    - Files: vcs.py, pipeline.py (call sites), dokima
    - Dependencies: [Task 1]
    - Parallelizable: yes (isolated file, no overlap with Task 4-5)
    - Estimated LOC: ~15
    - Description: Remove module-level REPO = "" from vcs.py line 19. Functions that use REPO (vcs_pr_update_body at line 253 which references REPO in f-string) must accept it as a parameter or read from a passed context. The detect_vcs_backend() function currently sets REPO as a global — change it to return repo slug as part of its return value (or set it on the VCS module object). Update entry script to pass repo slug explicitly.
    
    Task 7: Update all test files to use PipelineContext
    - Files: tests/conftest.py, tests/test_*.py (~50 test files)
    - Dependencies: [Task 5]
    - Parallelizable: no
    - Estimated LOC: ~80
    - Description: After conftest is rewritten, update the panel fixture to yield a PipelineContext (or a tuple of ctx + module). Update the test_repo fixture (lines 166-190) to create a PipelineContext instead of setting panel.PROJECT_DIR/panel.REPO. Update the mock_orchestrator fixture (lines 193-231) to work with ctx. Run full test suite and fix any test that references panel.PROJECT_DIR, panel.REPO, panel.DEFAULT_BRANCH, panel.TEST_CMD, etc. — these will now be ctx.project_dir, ctx.repo, etc. Tests that import utils.PROJECT_DIR directly must also be updated.
    
    Task 8: Run full test suite — verify 1,029 pass, 4 skip, 0 fail
    - Files: all
    - Dependencies: [Task 7]
    - Parallelizable: no
    - Estimated LOC: ~0 (validation only)
    - Description: python3 -m pytest tests/ -q. All 1,029 tests must pass. Any failure must be traced to a missed reference and fixed. Run also: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" (build). Run python3 -m py_compile dokima (lint). All must succeed.
    
    
    
    6. Data Model
    
    python
    from dataclasses import dataclass, field
    import os, pwd
    from typing import Optional, Dict
    
    @dataclass
    class PipelineContext:
        """Single source of truth for all pipeline configuration and runtime state."""
        
        # ── Required (set at construction) ──
        project_dir: str
        repo: str = ""
        
        # ── Auto-detected (defaults from env, can be overridden) ──
        default_branch: str = "master"
        panel_feature: str = ""
        api_key: str = ""
        output_log: str = "/tmp/dokima-output.txt"
        
        # ── Derived from filesystem (computed in __post_init__) ──
        real_home: str = field(default_factory=lambda: pwd.getpwuid(os.getuid()).pw_dir)
        hermes_bin: str = field(default="")
        profiles_dir: str = field(default="")
        panel_dir: str = ""
        
        # ── Commands (detected from AGENTS.md) ──
        test_cmd: str = "npm test"
        build_cmd: str = "npm run build"
        lint_cmd: str = "npm run lint"
        
        # ── Feature flags ──
        skip_autofix: bool = False
        force_full: bool = False
        skip_human_gate: bool = False
        max_parallel_override: Optional[int] = None
        resume: Optional[bool] = None
        
        # ── Model configuration ──
        fallback_models: Dict[str, str] = field(default_factory=dict)
        panel_port: Dict[str, int] = field(default_factory=lambda: {
            "strategist": 8647, "tech-lead": 8644, "coder": 8645, "nm": 8648
        })
        
        # ── Transient (set during pipeline execution, NOT at construction) ──
        max_continuous: int = 20
        
        def __post_init__(self):
            """Compute derived paths from real_home."""
            hermes_root = os.path.join(self.real_home, ".hermes")
            if not self.hermes_bin:
                self.hermes_bin = os.path.join(hermes_root, "hermes-agent/venv/bin/hermes")
            if not self.profiles_dir:
                self.profiles_dir = os.path.join(hermes_root, "profiles")
        
        @classmethod
        def from_environ(cls, project_dir: str, **overrides) -> "PipelineContext":
            """Factory: construct from environment variables + overrides."""
            import os as _os
            ctx = cls(
                project_dir=project_dir,
                skip_autofix=_os.environ.get("PANEL_SKIP_AUTOFIX") == "1",
                force_full=_os.environ.get("PANEL_FORCE_FULL") == "1",
                skip_human_gate=_os.environ.get("PANEL_SKIP_HUMAN_GATE") == "1",
            )
            mp = _os.environ.get("PANEL_MAX_PARALLEL")
            if mp and mp.isdigit():
                ctx.max_parallel_override = int(mp)
            for k, v in overrides.items():
                if hasattr(ctx, k):
                    setattr(ctx, k, v)
            return ctx
    
    
    What persists: Nothing. PipelineContext is in-memory only, constructed per pipeline run.
    
    What's transient: Everything. Context is discarded when the pipeline exits.
    
    
    
    7. API Routes
    
    N/A — internal Python refactor with no HTTP surface.
    
    
    
    8. Component Tree
    
    N/A — no frontend.
    
    
    
    9. COTS Build-vs-Buy
    
    Component: dataclasses.dataclass
    Buy/Build: stdlib
    Justification: Python 3.7+ built-in. Zero deps.
    ────────────────────────────────────────
    Component: @dataclass(frozen=True)
    Buy/Build: Not used
    Justification: Mutable context needed — panel_feature changes per
      iteration in --continuous loop.
    
    Total new dependencies: 0.
    
    
    
    10. Test Plan (MANDATORY)
    
    Happy Path
    1. Construct PipelineContext: ctx = PipelineContext(project_dir="/tmp/test", repo="t/t") — all fields have defaults or computed values.
    2. from_environ factory: Set PANEL_SKIP_AUTOFIX=1, call from_environ("/tmp/test") — ctx.skip_autofix is True.
    3. Pass ctx to phase function: run_phase3_vet(ctx, feature="test", branch="feat/x", ...) — no crash, uses ctx.project_dir.
    4. Conftest panel fixture yields ctx: Test uses def test_something(panel): ctx = panel; assert ctx.project_dir == "/tmp/test-project".
    5. Existing test_repo fixture passes: After refactor, test_repo creates a ctx, sets ctx.project_dir, and pipeline tests use ctx.
    
    Edge Cases
    6. Empty repo: ctx = PipelineContext(project_dir="/tmp/test", repo="") — all functions that use ctx.repo handle empty string gracefully (same behavior as current empty-string default).
    7. custom hermes_bin: ctx = PipelineContext(project_dir="/tmp/test", hermes_bin="/usr/local/bin/hermes") — __post_init__ does NOT overwrite a user-provided value.
    8. Concurrent continuous loop iterations: Each call to run_pipeline(ctx, ...) in the --continuous loop mutates ctx.panel_feature — verify no stale values bleed between iterations.
    9. Missing home directory: pwd.getpwuid() raises on restricted containers — __post_init__ must handle gracefully (try/except, fall back to os.path.expanduser("~")).
    10. Resume from checkpoint: Resume path in run_pipeline (lines 2527-2548) must still work when using ctx instead of module globals.
    
    Failure Modes
    11. ctx not passed: Calling run_phase3_vet(feature=..., ...) without ctx as first param — TypeError with clear message.
    12. None ctx: ctx = None; run_phase3_vet(ctx, ...) — AttributeError when accessing ctx.project_dir. Acceptable (Python's standard behavior for None attribute access).
    13. Missing project_dir: PipelineContext(repo="t/t") — TypeError (dataclass enforces required field).
    14. Network error in detect_repo: Entry script already handles this — ctx is constructed after detection, so missing repo is caught before ctx construction.
    
    Contract Invariants
    15. Phase functions do not mutate ctx: A phase function must NEVER modify ctx.project_dir or ctx.repo. Only the entry script and run_pipeline may update ctx.panel_feature between iterations.
    16. ctx is always the first parameter: All phase functions accept ctx: PipelineContext as their first positional parameter.
    17. conftest creates ctx, not module: After refactor, conftest's _load_panel() returns a PipelineContext, not a types.ModuleType with setattr override.
    18. Zero module-level globals post-refactor: Running grep -rn "PROJECT_DIR\|^REPO\b" utils.py vcs.py must return zero module-level assignment hits (imports/references through ctx OK).
    
    
    
    11. Panel Split
    
    This is a sequential refactor with limited parallelism:
    
    
    Wave 1 (1 coder):
      Task 1: Create PipelineContext dataclass
    
    Wave 2 (1 coder):
      Task 2: Wire into entry script
      Task 6: Remove vcs.py REPO (parallelizable with Task 2 — separate files)
    
    Wave 3 (1 coder):
      Task 3: Refactor all phase functions
      Task 4: Refactor discover_blocked_pr + extract_blockers_from_pr
      (same file — must be sequential)
    
    Wave 4 (1 coder):
      Task 5: Remove utils.py globals + rewrite conftest
    
    Wave 5 (1 coder):
      Task 7: Update all test files
    
    Wave 6 (verification):
      Task 8: Full test suite
    
    
    Parallelism: Task 6 (vcs.py) can run in parallel with Task 2 (dokima entry) since they touch different files. All other tasks share files and must be sequential. 1 coder agent. Total: 6 waves.
    
    
    
    12. Build & Deploy
    
    - Build: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" — must succeed
    - Lint: python3 -m py_compile dokima — must succeed
    - Test: python3 -m pytest tests/ -q — must pass 1,029, skip 4, fail 0
    - Deploy: This is the dokima repo itself — merge to main, chmod +x dokima if needed. No Vercel/cloud deployment.
    - Env vars: No new env vars needed.
    - CI: No CI exists yet (F042). Manual verification only.
    
    
    
    13. Risk Register
    
    #: 1
    Risk: Test breakage during refactor — a missed PROJECT_DIR reference in a
      test causes cascade failure
    Severity: High
    Mitigation: 1,029 tests serve as safety net. Run full suite after every
      task. Fix any failure before proceeding.
    Trigger: Any test fails in Task 8
    Column 6:
    ────────────────────────────────────────
    #: 2
    Risk: Hidden global readers — functions that read PROJECT_DIR/REPO without
      global statement, accessed via from utils import PROJECT_DIR
    Severity: Medium
    Mitigation: grep -rn "PROJECT_DIR\
    Trigger: REPO\b" utils.py vcs.py pipeline.py agent.py tasks.py roadmap.py
      to find all references before cutting over.
    Column 6: More than 20 unique reference points found
    ────────────────────────────────────────
    #: 3
    Risk: conftest panel fixture consumers — ~50 test files use
      panel.PROJECT_DIR = ... pattern; rewriting all of them is tedious
    Severity: Medium
    Mitigation: Task 7 specifically covers this. The panel fixture emits a
      PipelineContext; tests reference ctx.project_dir instead of
      panel.PROJECT_DIR.
    Trigger: More than 15 test files fail after Task 5
    Column 6:
    ────────────────────────────────────────
    #: 4
    Risk: vcs.py REPO coupling — vcs_pr_update_body() at line 253 uses REPO in
      an f-string; changing it requires cascade to all VCS callers
    Severity: Low
    Mitigation: Only 2 VCS functions reference REPO. Refactor
      detect_vcs_backend() to return repo slug instead of mutating module
      global.
    Trigger: vcs.py functions break after REPO removal
    Column 6:
    ────────────────────────────────────────
    #: 5
    Risk: Continuous loop ctx mutation — --continuous mode updates
      PANEL_FEATURE per iteration; must update ctx.panel_feature instead
    Severity: Low
    Mitigation: Entry script loop at lines 717-751 already sets PANEL_FEATURE
      = feature before each run_pipeline() call — trivial to assign
      ctx.panel_feature = feature instead.
    Trigger: Continuous mode picks wrong feature
    Column 6:
    ────────────────────────────────────────
    #: 6
    Risk: _importing_panel pattern breakage — pipeline.py line 207-211 and
      other places use _IMPORTING_PANEL for test patch detection
    Severity: Medium
    Mitigation: Replace with direct ctx parameter passing. Test patches will
      mock run_phaseX functions directly rather than relying on module
      override detection.
    Trigger: Test test_f031_pipeline_refactor or similar override-detection
      tests fail
    Column 6:
    
    
    
    14. Anti-Creep
    
    NOT in scope — the coder must NOT build:
    - Immutable/frozen context (FrozenInstanceError breaks --continuous loop)
    - Thread-safety / locking on PipelineContext (single-threaded pipeline, no concurrent ctx access)
    - YAML/JSON serialization of PipelineContext (not needed — ctx is in-memory only)
    - CLI flag to dump ctx (out of scope for this refactor)
    - PipelineContext as a replacement for checkpoint data (checkpoints are already handled by load_checkpoint/save_checkpoint)
    - Moving status.py's PipelineStatus into PipelineContext (separate concern — build state vs. pipeline config)
    - Type annotations requiring Python 3.10+ (project targets Python 3.6+, use Optional[X] not X | None)
    - Removing _IMPORTING_PANEL from sub-modules that don't use globals (out of scope — only pipeline/agent/tasks/roadmap)
    
    
    
    15. Sign-Off Checklist
    
    - [ ] PipelineContext dataclass defined with all 20+ fields
    - [ ] __post_init__ computes derived paths correctly
    - [ ] from_environ() factory handles PANEL_SKIP_AUTOFIX, PANEL_FORCE_FULL, PANEL_SKIP_HUMAN_GATE, PANEL_MAX_PARALLEL
    - [ ] Entry script constructs ctx once, passes to run_pipeline(ctx, ...)
    - [ ] _sync_modules() removed from entry script
    - [ ] All 9 phase/fix/pipeline functions accept ctx as first parameter
    - [ ] All 11 global statements removed from pipeline.py
    - [ ] conftest setattr override hack removed (lines 42-53)
    - [ ] conftest _load_panel() returns PipelineContext, not module
    - [ ] All test files updated to use ctx.field instead of panel.FIELD
    - [ ] vcs.py REPO module-level global removed
    - [ ] utils.py module-level globals removed (lines 16-36)
    - [ ] Full test suite: 1,029 pass, 4 skip, 0 fail
    - [ ] Build and lint pass
    - [ ] grep -rn "PROJECT_DIR\s*=" utils.py pipeline.py returns zero module-level assignments (excluding ctx construction)
    
    
    
    Spec version: 1.0 | Author: Strategist (panel) | Next: Panel sign-off → coder implementation