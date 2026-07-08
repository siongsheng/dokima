# F041: Split utils.py into domain modules — git_ops.py (git, gh wrappers), spec_extract.py (extract_pr_sections, extract_issue_sections, clean_spec_content), codebase_map.py (generate_codebase_map, _build_domain_map, _build_impact_map), control_panel.py (handle_status, handle_stop, handle_kill). 3,351 lines → ~4 × 800-line modules.

Now I have the complete picture. Let me produce the corrected spec.
    
    
    
    F041: Split utils.py into Domain Modules
    
    Version: 1.1.0 (Quality Correction)
    Confidence: High
    Impact: MEDIUM
    Status: In Progress
    Dependencies: F040 (PipelineContext dataclass)
    
    1. Executive Summary
    
    Split the 3,351-line utils.py (83 functions) into 4 domain-focused modules — git_ops.py, spec_extract.py, codebase_map.py, control_panel.py — each ~400-1100 lines. Contributors open the right module instead of scrolling past 83 functions in one file. utils.py retains ~35 shared infrastructure functions (sanitization, checkpointing, locking, release, init interview) at ~1,200 lines. Zero behavioral change — all 1,029 existing tests pass identically. Backward-compatible via re-export shims: existing from utils import git continues to work. (High confidence)
    
    2. Constitution Check
    
    Axiom: Does it solve the user's own pain?
    Status: YES
    Detail: Contributors scroll past 83 functions to find the one they need.
      F040 PipelineContext already touches utils.py — splitting first reduces
      merge hell.
    ────────────────────────────────────────
    Axiom: Is it weekend-buildable?
    Status: YES
    Detail: Mechanical extraction, 6 tasks, one 2-3 hour session.
    ────────────────────────────────────────
    Axiom: Is there evidence people will pay?
    Status: N/A
    Detail: Internal tooling improvement.
    ────────────────────────────────────────
    Axiom: Is the tech stack boring and proven?
    Status: YES
    Detail: Python 3.6+ imports, zero new dependencies, same test harness.
    ────────────────────────────────────────
    Axiom: Does it avoid AI hype categories?
    Status: YES
    Detail: Pure code organization. No AI, no platform, no "intelligent"
      anything.
    
    3. Impact Assessment (Grounded in Tool Output)
    
    
    utils.py:                          3,351 lines → ~1,200 lines (retained 35 shared functions)
    git_ops.py (NEW):                  ~350 lines  (11 functions: git, gh, detect_repo, try_auto_merge, etc.)
    spec_extract.py (NEW):             ~1,100 lines (18 functions: extract_pr_sections, clean_spec_content, etc.)
    codebase_map.py (NEW):             ~420 lines  (7 functions: generate_codebase_map, _build_domain_map, etc.)
    control_panel.py (NEW):            ~400 lines  (12 functions: handle_status, handle_stop, show_help, etc.)
    
    
    Files importing from utils.py (verified via grep):
    - pipeline.py (+46 imports, lines 12-41) — imports from ALL four new modules
    - agent.py (+5 imports, line 8) — imports load_key, load_github_token (→ git_ops.py)
    - tasks.py (+5 imports, line 9-10) — imports slugify, git, _safe_run (→ stays in utils.py + git_ops.py)
    - roadmap.py (+10 imports, line 10-13) — imports from git_ops, spec_extract, codebase_map
    - dokima (entry, line 35) — imports handle_status, handle_stop, handle_kill, handle_list_crons (→ control_panel.py)
    - vcs.py — standalone, no utils import
    
    Test files directly importing utils: test_f022_utils.py, test_f022_utils_complete.py, test_f024_release.py, test_f031_collect_answers.py, test_f031_utils_helpers.py, test_functions_unit.py, test_clean_spec.py, test_extract_pr.py, test_extract_agent.py, test_extract_file_paths.py, test_codebase_map.py, test_control_panel.py, test_slugify.py, test_pid_utils.py, test_status_md.py, test_helpers.py, test_fix_mode.py, test_root_cause_regressions.py, test_f037_blocker_resolution.py — ~19 test files affected
    
    Lines changed (estimated): utils.py (-2,150/+200), 4 new files (+2,270), pipeline.py (±46), agent.py (±5), tasks.py (±5), roadmap.py (±10), dokima (±4), ~19 test files (±1-5 each)
    
    4. What Changed
    
    For contributors: Open git_ops.py to understand git/GH wrappers. Open spec_extract.py to see how PR bodies and issue sections are parsed. Open codebase_map.py to trace how the domain/impact/test maps are built. Open control_panel.py to see status/stop/kill logic. No more scrolling past 83 functions to find the one you need.
    
    For agents: Pipeline agents loading the relevant module instead of 3,351-line utils.py — strategist reads spec_extract.py (~1,100 lines), coder reads git_ops.py (~350 lines), nm vet reads codebase_map.py (~420 lines). Context window utilization drops 65-90%.
    
    For backward compatibility: Existing imports continue to work. from utils import git resolves through re-export shim in utils.py. New code can import directly: from git_ops import git. Tests import from utils unchanged — zero test modifications required for the import path.
    
    What stays in utils.py (35 functions): _sanitize_prompt, _validate_project_dir, _redact_secrets, _write_log_line, _safe_run, slugify, detect_commands, _lock_path, _stop_path, _checkpoint_path, save_checkpoint, load_checkpoint, delete_checkpoint, _phase_should_skip, validate_checkpoint, acquire_lock, _cleanup_lock, _signal_handler, _supplement_pr_sections, _hash_output, _detect_truncation, _check_pid, _verify_pid_owner, ensure_profiles, deploy_profile_skills, halt_and_revert, archive_specs_for_feature, _bump_version, _prune_old_tags, _update_docs_cache, do_release, load_init_interview_state, save_init_interview_state, has_init_interview_triggers, collect_init_interview_answers. Plus all module-level globals and constants.
    
    5. Feature Breakdown
    
    Task 1: Create git_ops.py — extract git/GH wrappers
    Files: utils.py, git_ops.py
    Dependencies: [none]
    Parallelizable: no
    Description: Move 11 functions (load_key, load_github_token, git, gh, detect_repo, _detect_referenced_repo, try_auto_merge, _detect_default_branch, _set_vcs_token, _load_token_from_env_file, _set_gh_token) from utils.py to new git_ops.py. Add re-export shims: from git_ops import git, gh, detect_repo, .... utils.py shrinks by ~350 lines. Estimated 350 LOC in new file, ~50 LOC in utils.py (shims).
    
    Task 2: Create spec_extract.py — extract spec parsing functions
    Files: utils.py, spec_extract.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Move 18 functions (extract_pr_sections, extract_agent_messages, clean_spec_content, verify_spec_quality, _check_pr_body_quality, extract_file_paths, _extract_code_context, load_map_enrichments, save_map_enrichments, extract_map_enrichments, _extract_tl_verdict, _extract_tl_blockers, format_blocker_cross_reference, extract_should_fix_from_text, _extract_nm_summary, extract_issue_sections, _extract_convention_rules, _append_convention_rules) from utils.py to new spec_extract.py. Add re-export shims. utils.py shrinks by ~1,100 lines. Estimated 1,100 LOC in new file, ~60 LOC in utils.py (shims).
    
    Task 3: Create codebase_map.py — extract map generation functions
    Files: utils.py, codebase_map.py
    Dependencies: [Task 2]
    Parallelizable: no
    Description: Move 7 functions (generate_codebase_map, _classify_domain, _build_domain_map, _build_impact_map, _build_test_map, _find_key_files, _describe_file) from utils.py to new codebase_map.py. Add re-export shims. utils.py shrinks by ~420 lines. Estimated 420 LOC in new file, ~20 LOC in utils.py (shims).
    
    Task 4: Create control_panel.py — extract control panel handlers
    Files: utils.py, control_panel.py
    Dependencies: [Task 3]
    Parallelizable: no
    Description: Move 12 functions (show_help, show_help_json, check_upgrade, _version_newer, _parse_status_md, _make_status_entry, update_status_md, _get_lock_state, handle_status, handle_stop, handle_kill, handle_list_crons) from utils.py to new control_panel.py. Add re-export shims. utils.py shrinks by ~400 lines. Estimated 400 LOC in new file, ~40 LOC in utils.py (shims).
    
    Task 5: Update importers across pipeline.py, agent.py, tasks.py, roadmap.py, dokima
    Files: pipeline.py, agent.py, tasks.py, roadmap.py, dokima
    Dependencies: [Task 4]
    Parallelizable: no
    Description: Update from utils import ... in 5 files to import from new modules where appropriate. pipeline.py: add from git_ops import ..., from spec_extract import ..., from codebase_map import ..., from control_panel import ... to replace 46 utils imports. agent.py: add from git_ops import load_key, load_github_token. tasks.py: add from git_ops import git. roadmap.py: add from git_ops import ..., from spec_extract import ..., from codebase_map import generate_codebase_map. dokima: add from control_panel import handle_status, handle_stop, handle_kill, handle_list_crons. Keep backward-compat re-exports in utils.py so old from utils import X still works. Estimated ±80 LOC across 5 files.
    
    Task 6: Verify — run full test suite, build, lint
    Files: tests/*.py
    Dependencies: [Task 5]
    Parallelizable: no
    Description: Run python3 -m pytest tests/ -q — all 1,029 tests must pass. Run python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" — build must succeed. Run python3 -m py_compile dokima — lint must pass. Run python3 -m py_compile git_ops.py spec_extract.py codebase_map.py control_panel.py — all new modules must compile. Run python3 -m pytest tests/test_f022_utils.py tests/test_f022_utils_complete.py -v — backward-compat imports verified. Estimated 0 LOC changed (verification only).
    
    6. Data Model
    
    No new data. This is a pure refactor — code moves between files, nothing persists. Module-level globals remain in utils.py (PROJECT_DIR, REPO, DEFAULT_BRANCH, API_KEY, etc.) since they're set by main() and read by all modules. PipelineContext (F040) will eventually replace these globals, but F041 does not change the global state pattern.
    
    7. API Routes
    
    N/A — no web endpoints.
    
    8. Component Tree
    
    N/A — no frontend.
    
    9. COTS Build-vs-Buy
    
    N/A — everything is built. Zero new dependencies. The existing Python stdlib imports (sys, json, subprocess, os, pwd, time, shlex, re, fcntl, signal, datetime) are distributed across the new modules as needed.
    
    10. Test Plan (MANDATORY)
    
    Happy path
    1. python3 -m pytest tests/ -q — all 1,029 tests pass identically
    2. from utils import git still works — backward-compat re-exports functional
    3. from git_ops import git works — direct import functional
    4. from spec_extract import extract_pr_sections works
    5. from codebase_map import generate_codebase_map works
    6. from control_panel import handle_status works
    7. python3 -m py_compile git_ops.py spec_extract.py codebase_map.py control_panel.py — all new modules compile cleanly
    8. dokima status (CLI command) still works — control panel handlers import correctly
    9. Full pipeline end-to-end: dokima "test feature" /tmp/test-project — all 5 phases run without import errors
    
    Edge cases
    10. What if a test file imports from utils AND from a new module that both define the same symbol? (Re-export shims must not create circular imports)
    11. What if utils.py module-level globals are accessed from new modules before main() sets them? (New modules must import globals from utils, not define their own)
    12. What if a new module has an internal import utils that creates a circular dependency? (All internal references between new modules must go through utils re-exports, not direct cross-module imports)
    13. What if pipeline.py imports the same symbol from both utils and a new module? (Deduplication — prefer new module import, keep utils re-export for backward compat)
    14. What if a function's helper (used only internally) was not listed for extraction? (The coder must grep for callers before moving any function)
    15. What if a moved function references a module-level global from utils.py? (New module must from utils import GLOBAL_NAME explicitly)
    
    Failure modes
    16. What if python3 -m pytest tests/ -q fails with ImportError? (Re-export path broken — check circular imports in utils.py)
    17. What if python3 -m py_compile git_ops.py fails? (Missing stdlib import in new module)
    18. What if dokima status crashes with NameError? (handle_status moved but dokima still imports from utils — re-export shim missing)
    19. What if a test for a moved function fails because it monkey-patches utils.function_name? (Monkey-patch target must update to new module path)
    20. What if the build check fails? (Likely a moved function used by the dokima entry was not re-exported)
    
    Contract invariants
    21. Before: from utils import X works. After: from utils import X must still work (re-export shim).
    22. Before: import utils; utils.X() works. After: import utils; utils.X() must still work (attribute forwarding).
    23. Before: 1,029 tests pass. After: 1,029 tests must still pass.
    24. Before: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" succeeds. After: must still succeed.
    25. Before: utils.py module-level globals available to all functions. After: new modules must import globals from utils.py (not copy them).
    26. Before: no test imports from git_ops import .... After: some tests may optionally use direct imports — but this is a SHOULD, not a MUST.
    
    11. Panel Split
    
    All 6 tasks are sequential — each edits utils.py (removing moved functions and adding re-export shims), and later tasks depend on the re-exports added by earlier tasks.
    
    
    Wave 1: Task 1 (git_ops.py)
    Wave 2: Task 2 (spec_extract.py) — depends on Task 1 re-exports
    Wave 3: Task 3 (codebase_map.py) — depends on Task 2 re-exports
    Wave 4: Task 4 (control_panel.py) — depends on Task 3 re-exports
    Wave 5: Task 5 (update importers) — depends on all 4 modules existing
    Wave 6: Task 6 (verify) — depends on Task 5
    
    
    1 coder agent. Parallelization is not possible because all tasks modify utils.py — the same file. The panel schedules them sequentially.
    
    12. Build & Deploy
    
    - Build: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')"
    - Lint: python3 -m py_compile dokima + python3 -m py_compile git_ops.py spec_extract.py codebase_map.py control_panel.py
    - Test: python3 -m pytest tests/ -q
    - Deploy: No deployment change. dokima is a single-file entry script. New modules are imported at runtime.
    - CI: Tests run on push/PR via GitHub Actions (F042, pending).
    
    13. Risk Register
    
    #: R1
    Risk: Circular import: new module imports utils, utils imports new module
    Severity: HIGH
    Mitigation: Re-exports use from X import Y at module level after function
      definitions are removed. If circular: use lazy imports inside function
      bodies. Same pattern as F022b's pipeline.py→utils.py import worked.
    Trigger: ImportError: cannot import name ... during build
    ────────────────────────────────────────
    #: R2
    Risk: Monkey-patched test targets break: tests use
      unittest.mock.patch('utils.function_name')
    Severity: MEDIUM
    Mitigation: Grep for patch('utils. in all test files before extraction. If
      found, update patch target to new module path OR keep re-export in
      utils.py.
    Trigger: Test failure with mock.patch target not found
    ────────────────────────────────────────
    #: R3
    Risk: Function used by moved function but left behind: e.g., _safe_run()
      called by a moved function but _safe_run stays in utils
    Severity: MEDIUM
    Mitigation: Before each extraction task, grep for callers of every moved
      function. Verify all transitive dependencies are either moved together
      or imported.
    Trigger: NameError at runtime
    ────────────────────────────────────────
    #: R4
    Risk: Module-level globals inaccessible: new module tries to read
      PROJECT_DIR before main() sets it
    Severity: LOW
    Mitigation: All new modules import globals from utils.py: from utils
      import PROJECT_DIR. Same pattern as existing agent.py line 8.
    Trigger: AttributeError during import
    ────────────────────────────────────────
    #: R5
    Risk: Test file imports import utils and then calls utils.git() — must
      still work after extraction
    Severity: LOW
    Mitigation: Re-export shim in utils.py: from git_ops import git at module
      level makes utils.git resolve correctly. Verified by test_f022_utils.py.
    Trigger: AttributeError: module 'utils' has no attribute 'git'
    ────────────────────────────────────────
    #: R6
    Risk: Merge conflict with F040 (PipelineContext): both touch utils.py
      globals section
    Severity: MEDIUM
    Mitigation: F040 should merge first (it's the dependency). F041's Task 1-4
      remove function bodies, not globals. Conflict risk is on import lines in
      other files.
    Trigger: Git merge conflict on utils.py or pipeline.py
    
    14. Anti-Creep
    
    NOT in scope:
    - Do NOT refactor function internals — move code verbatim
    - Do NOT rename functions or change signatures
    - Do NOT add type hints, docstrings, or any behavioral changes
    - Do NOT change the module-level global pattern (that's F040's job)
    - Do NOT split utils.py further than the 4 modules listed
    - Do NOT update test files to use direct imports from new modules (keep from utils import X in tests)
    - Do NOT add new features to the extracted modules
    - Do NOT change the AGENTS.md or MAINTAINERS.md documentation (separate PR)
    - Do NOT remove functions from utils.py entirely — only move them; utils.py must retain re-export shims
    
    15. Sign-Off Checklist
    
    - [ ] All 1,029 tests pass: python3 -m pytest tests/ -q
    - [ ] Build succeeds: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')"
    - [ ] All new modules compile: python3 -m py_compile git_ops.py spec_extract.py codebase_map.py control_panel.py
    - [ ] Backward-compat imports work: python3 -c "from utils import git, gh, extract_pr_sections, generate_codebase_map, handle_status"
    - [ ] Direct imports work: python3 -c "from git_ops import git; from spec_extract import extract_pr_sections; from codebase_map import generate_codebase_map; from control_panel import handle_status"
    - [ ] No circular imports: python3 -c "import utils, git_ops, spec_extract, codebase_map, control_panel" succeeds
    - [ ] CLI commands work: python3 dokima status prints pipeline state (does not crash with import error)
    - [ ] No dead code: grep for function names moved to new modules — no remaining definitions in utils.py
    - [ ] Re-export shims present: grep utils.py for from git_ops import, from spec_extract import, from codebase_map import, from control_panel import
    - [ ] utils.py is under 1,300 lines (down from 3,351)
    - [ ] git diff --stat shows net change of -2,150/+2,270 lines across all files (not counting test file import updates)
    
    
    
    End of spec. The 6 tasks above are the complete implementation plan. No additional design work needed — this is a mechanical extraction with zero behavioral change, guarded by 1,029 existing tests and 26 concrete test-plan invariants.