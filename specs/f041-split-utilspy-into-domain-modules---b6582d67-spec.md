# F041: Split utils.py into domain modules — git_ops.py (git, gh wrappers), spec_extract.py (extract_pr_sections, extract_issue_sections, clean_spec_content), codebase_map.py (generate_codebase_map, _build_domain_map, _build_impact_map), control_panel.py (handle_status, handle_stop, handle_kill). 3,351 lines → ~4 × 800-line modules.

Now I have full understanding of the codebase. Let me produce the corrected spec.
    
    F041: Split utils.py into Domain Modules — Implementation Spec
    
    Status: Ready for Review | Confidence: High | Date: 2026-07-07
    
    
    
    1. Executive Summary
    
    Split 3,351-line utils.py (83 functions, 131KB) into 4 domain modules plus a slimmed utils.py. Each new module maps to a clear domain: git_ops.py (VCS + release, ~800 lines), spec_extract.py (text extraction from specs/PRs/issues, ~900 lines), codebase_map.py (codebase map generation, ~650 lines), control_panel.py (CLI status/stop/kill/help, ~450 lines). The remaining utils.py (~550 lines) holds security, locking, checkpointing, profiling, and interview helpers — the cross-cutting infrastructure. Zero behavior change. All 1,029 tests must pass identically. F040 (PipelineContext) is a prerequisite — this spec assumes ctx replaces module-level globals, but the split itself works either way (the new modules import from utils for globals that still exist).
    
    2. Constitution Check
    
    Axiom: Solve user's own pain?
    Assessment: Yes. Navigating 3,351 lines with 83 functions to find one is
      daily friction.
    Pass?: ✓
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Assessment: Yes. Pure cut-and-paste refactor, 7 tasks, ~150 LOC net
      change.
    Pass?: ✓
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Assessment: N/A — FOSS infrastructure quality.
    Pass?: ✓
    ────────────────────────────────────────
    Axiom: Boring and proven?
    Assessment: Yes. Python modules, no new dependencies, no frameworks.
    Pass?: ✓
    ────────────────────────────────────────
    Axiom: Avoid AI hype?
    Assessment: Yes. Pure engineering refactor.
    Pass?: ✓
    
    Verdict: All axioms pass. Proceed.
    
    3. Impact Section
    
    Based on actual file analysis of utils.py (grep ^def  yields 83 functions) and consumer imports (grep from utils import across all .py files):
    
    
    File: utils.py
    Type: Remove ~2,800 lines (80% of file). Keep ~550 lines of cross-cutting infrastructure.
    Functions moved out: 65 of 83 functions
    Functions kept: 18 functions (security, locking, checkpointing, profiles, interview)
    ΔLOC: -2,800
    ────────────────────────────────────────
    File: git_ops.py (NEW)
    Type: New module — VCS operations, token management, release automation
    Functions: git(), gh(), _safe_run(), detect_repo(), detect_commands(),
      _detect_referenced_repo(), _supplement_pr_sections(), _detect_default_branch(),
      _set_vcs_token(), _load_token_from_env_file(), _set_gh_token(), load_key(),
      load_github_token(), try_auto_merge(), _bump_version(), _prune_old_tags(),
      _update_docs_cache(), do_release(), halt_and_revert()
    ΔLOC: +800
    ────────────────────────────────────────
    File: spec_extract.py (NEW)
    Type: New module — text extraction from specs, PRs, issues, agent output
    Functions: extract_pr_sections(), extract_agent_messages(), clean_spec_content(),
      verify_spec_quality(), _check_pr_body_quality(), extract_issue_sections(),
      extract_should_fix_from_text(), _extract_tl_verdict(), _extract_tl_blockers(),
      format_blocker_cross_reference(), _extract_nm_summary(), extract_file_paths(),
      _hash_output(), _detect_truncation(), _extract_code_context(),
      _extract_convention_rules(), _append_convention_rules()
    ΔLOC: +900
    ────────────────────────────────────────
    File: codebase_map.py (NEW)
    Type: New module — codebase map generation, enrichments
    Functions: generate_codebase_map(), _classify_domain(), _build_domain_map(),
      _build_impact_map(), _build_test_map(), _find_key_files(), _describe_file(),
      load_map_enrichments(), save_map_enrichments(), extract_map_enrichments()
    ΔLOC: +650
    ────────────────────────────────────────
    File: control_panel.py (NEW)
    Type: New module — CLI control panel, status, help, upgrade
    Functions: handle_status(), handle_stop(), handle_kill(), handle_list_crons(),
      show_help(), show_help_json(), check_upgrade(), _version_newer(),
      _parse_status_md(), _make_status_entry(), update_status_md(),
      _get_lock_state()
    Constants: HELP_TEXT, CLI_METADATA
    ΔLOC: +450
    ────────────────────────────────────────
    File: pipeline.py
    Type: Update imports — ~28 functions now from 4 modules instead of 1
    ΔLOC: +4 / -28 (import lines only)
    ────────────────────────────────────────
    File: agent.py
    Type: Update imports — 3 functions now from git_ops.py instead of utils
    ΔLOC: +1 / -1
    ────────────────────────────────────────
    File: roadmap.py
    Type: Update imports — ~20 functions from 4 modules instead of 1
    ΔLOC: +4 / -20
    ────────────────────────────────────────
    File: tasks.py
    Type: Update imports — 5 functions from git_ops.py + utils instead of utils
    ΔLOC: +2 / -10
    ────────────────────────────────────────
    File: dokima (entry script)
    Type: Update imports — ~40 functions from 4 modules instead of 1
    ΔLOC: +6 / -40
    ────────────────────────────────────────
    File: 14 test files
    Type: Update imports — functions now from specific modules
    Affected: test_f022_utils.py, test_f022_utils_complete.py, test_f024_release.py,
      test_f031_collect_answers.py, test_f031_init_interview.py, test_f031_init_loop.py,
      test_f031_pipeline_refactor.py, test_f031_utils_helpers.py,
      test_f037_blocker_resolution.py, test_fix_mode.py, test_functions_unit.py,
      test_sandbox_fixes.py, test_task6_profiles.py, test_task7_vcs_flag.py
    ΔLOC: ~30 / ~30 (change imports, same function names)
    ────────────────────────────────────────
    Total net ΔLOC: +2,867 / -2,929 (net -62 lines from de-duplicating import blocks)
    
    
    Downstream dependency: F042 (CI pipeline) and F043 (phase decomposition) both benefit from narrower import scopes but don't depend on this split.
    
    4. What Changed (PR Body Template)
    
    - git_ops.py created from utils.py — holds git(), gh(), _safe_run(), detect_repo(), detect_commands(), _set_vcs_token(), load_key(), load_github_token(), try_auto_merge(), _bump_version(), do_release(), halt_and_revert(), and 6 more VCS helpers (19 functions total)
    - spec_extract.py created from utils.py — holds extract_pr_sections(), clean_spec_content(), verify_spec_quality(), extract_issue_sections(), extract_should_fix_from_text(), _extract_tl_verdict(), _extract_tl_blockers(), format_blocker_cross_reference(), _extract_nm_summary(), extract_file_paths(), _extract_convention_rules(), _append_convention_rules(), and 5 more extraction helpers (17 functions total)
    - codebase_map.py created from utils.py — holds generate_codebase_map(), _build_domain_map(), _build_impact_map(), _build_test_map(), _classify_domain(), _describe_file(), _find_key_files(), load_map_enrichments(), save_map_enrichments(), extract_map_enrichments() (10 functions total)
    - control_panel.py created from utils.py — holds handle_status(), handle_stop(), handle_kill(), handle_list_crons(), show_help(), show_help_json(), check_upgrade(), _version_newer(), _parse_status_md(), _make_status_entry(), update_status_md(), _get_lock_state(), plus HELP_TEXT and CLI_METADATA constants (12 functions + 2 constants)
    - utils.py slimmed from 3,351 lines to ~550 lines — retains _sanitize_prompt(), _validate_project_dir(), _redact_secrets(), _write_log_line(), slugify(), lock/checkpoint paths, acquire_lock(), _cleanup_lock(), _signal_handler(), ensure_profiles(), deploy_profile_skills(), archive_specs_for_feature(), interview helpers, and all module-level globals (18 functions + globals)
    - All 5 consumer modules (pipeline.py, agent.py, roadmap.py, tasks.py, dokima) updated to import from the correct new modules
    - All 14 test files updated to import from the correct new modules
    - Zero behavior change — every function is copied verbatim, every test passes as before
    
    5. Feature Breakdown — Tasks
    
    Task 1: Create git_ops.py — extract VCS, token, and release functions from utils.py
    - Files: utils.py (remove functions), git_ops.py (create)
    - Dependencies: none
    - Parallelizable: no
    - Description: Create git_ops.py with these functions copied verbatim from utils.py: git(), gh(), _safe_run(), detect_repo(), detect_commands(), _detect_referenced_repo(), _supplement_pr_sections(), _detect_default_branch(), _set_vcs_token(), _load_token_from_env_file(), _set_gh_token(), load_key(), load_github_token(), try_auto_merge(), _bump_version(), _prune_old_tags(), _update_docs_cache(), do_release(), halt_and_revert(). Add module docstring. Add imports at top (sys, os, json, subprocess, re, time, datetime, shlex, tempfile — whatever these functions actually use). Remove these 19 functions from utils.py. Remove _GH_TOKEN_CACHE from utils.py globals (move to git_ops.py).
    
    Task 2: Create spec_extract.py — extract text processing functions from utils.py
    - Files: utils.py (remove functions), spec_extract.py (create)
    - Dependencies: Task 1
    - Parallelizable: no
    - Description: Create spec_extract.py with these functions copied verbatim from utils.py: extract_pr_sections(), extract_agent_messages(), clean_spec_content(), verify_spec_quality(), _check_pr_body_quality(), extract_issue_sections(), extract_should_fix_from_text(), _extract_tl_verdict(), _extract_tl_blockers(), format_blocker_cross_reference(), _extract_nm_summary(), extract_file_paths(), _hash_output(), _detect_truncation(), _extract_code_context(), _extract_convention_rules(), _append_convention_rules(). Add module docstring and necessary imports. Remove these 17 functions from utils.py.
    
    Task 3: Create codebase_map.py — extract map generation functions from utils.py
    - Files: utils.py (remove functions), codebase_map.py (create)
    - Dependencies: Task 2
    - Parallelizable: no
    - Description: Create codebase_map.py with these functions copied verbatim from utils.py: generate_codebase_map(), _classify_domain(), _build_domain_map(), _build_impact_map(), _build_test_map(), _find_key_files(), _describe_file(), load_map_enrichments(), save_map_enrichments(), extract_map_enrichments(). Add module docstring and necessary imports (os, json, re, datetime, ast, hashlib). Remove these 10 functions from utils.py.
    
    Task 4: Create control_panel.py — extract CLI control, status, and help from utils.py
    - Files: utils.py (remove functions + constants), control_panel.py (create)
    - Dependencies: Task 3
    - Parallelizable: no
    - Description: Create control_panel.py with these functions copied verbatim from utils.py: handle_status(), handle_stop(), handle_kill(), handle_list_crons(), show_help(), show_help_json(), check_upgrade(), _version_newer(), _parse_status_md(), _make_status_entry(), update_status_md(), _get_lock_state(). Also move HELP_TEXT and CLI_METADATA constants. Add module docstring and necessary imports (sys, os, json, re, subprocess, time). Remove these 12 functions and 2 constants from utils.py. Note: control_panel functions reference utils module-level globals (OUTPUT_LOG, DEFAULT_BRANCH) — import these from utils at the top of control_panel.py.
    
    Task 5: Add inter-module imports — wire new modules to import from each other
    - Files: git_ops.py, spec_extract.py, codebase_map.py, control_panel.py
    - Dependencies: Task 4
    - Parallelizable: no
    - Description: Add cross-module imports where needed. spec_extract.py functions (verify_spec_quality) call extract_pr_sections — already in same module, no cross-import needed. codebase_map.py functions call _describe_file, _classify_domain — both in same module. control_panel.py functions call _get_lock_state, _parse_status_md, update_status_md — all in same module. check_upgrade() calls do_release() which moved to git_ops.py — add from git_ops import do_release to control_panel.py. handle_list_crons() uses subprocess — already imported. Verify no circular imports by checking the call graph. _append_convention_rules() in spec_extract.py calls git() — add from git_ops import git to spec_extract.py. _extract_code_context() reads files from disk — already stdlib, no cross-import needed. _check_pr_body_quality() calls extract_pr_sections() — same module. Verify all internal calls resolve.
    
    Task 6: Update pipeline.py imports — import from 4 new modules instead of utils
    - Files: pipeline.py
    - Dependencies: Task 5
    - Parallelizable: yes
    - Description: Replace the monolithic from utils import (...) block (lines 12-41) with imports from the 4 new modules plus slimmed utils. Map each function: git/gh/VCS → git_ops.py. spec extraction/PR/TL/blocker → spec_extract.py. codebase map → codebase_map.py. control panel/status/help → control_panel.py. Lock/checkpoint/security globals → utils.py. Keep the same function names — this is a pure import path change. Do NOT change any function calls in the file body.
    
    Task 7: Update agent.py imports — import from git_ops.py instead of utils
    - Files: agent.py
    - Dependencies: Task 5
    - Parallelizable: yes
    - Description: agent.py line 8 imports: load_key, load_github_token from git_ops.py; _redact_secrets, _write_log_line, HERMES_BIN, OUTPUT_LOG from utils.py. Split the single from utils import ... line into two import statements: from git_ops import load_key, load_github_token and from utils import _redact_secrets, _write_log_line, HERMES_BIN, OUTPUT_LOG.
    
    Task 8: Update roadmap.py imports — import from 4 new modules instead of utils
    - Files: roadmap.py
    - Dependencies: Task 5
    - Parallelizable: yes
    - Description: Replace the monolithic from utils import (...) block (lines 10-25) with imports from the 4 new modules plus slimmed utils. Map: load_key, git, gh, detect_repo, load_github_token → git_ops.py. extract_pr_sections, clean_spec_content, verify_spec_quality, extract_agent_messages → spec_extract.py. generate_codebase_map, extract_file_paths → separate spec_extract/codebase_map. show_help, check_upgrade → control_panel.py. slugify, acquire_lock, _cleanup_lock, save_checkpoint, delete_checkpoint, _signal_handler, _safe_run, _redact_secrets, _write_log_line, update_status_md, _extract_tl_verdict, _extract_tl_blockers → appropriate modules. Keep globals (HERMES, HERMES_BIN, DEFAULT_BRANCH, etc.) from utils.py. Also update the deferred import at line 562 (ensure_profiles, deploy_profile_skills → utils.py).
    
    Task 9: Update tasks.py imports — import from git_ops.py instead of utils
    - Files: tasks.py
    - Dependencies: Task 5
    - Parallelizable: yes
    - Description: tasks.py line 9 imports slugify, git, _safe_run, load_github_token. Map: git, _safe_run, load_github_token → git_ops.py. slugify → utils.py. Globals (HERMES_BIN, DEFAULT_BRANCH, PANEL_FEATURE, etc.) → utils.py. Split into two import statements: from git_ops import git, _safe_run, load_github_token and from utils import slugify, HERMES_BIN, DEFAULT_BRANCH, ....
    
    Task 10: Update dokima entry script imports — import from 4 new modules
    - Files: dokima
    - Dependencies: Task 5
    - Parallelizable: yes
    - Description: Replace the monolithic from utils import (...) block (lines 23-43) with imports from the 4 new modules plus slimmed utils. Map each function to its new home. Also add import git_ops as _git_ops, import spec_extract as _spec_extract, import codebase_map as _codebase_map, import control_panel as _control_panel at the top alongside the existing import utils as _utils for module-level state propagation if needed. Keep import utils as _utils for the globals that still live there.
    
    Task 11: Update all test file imports — 14 files, pure import path changes
    - Files: tests/test_f022_utils.py, tests/test_f022_utils_complete.py, tests/test_f024_release.py, tests/test_f031_collect_answers.py, tests/test_f031_init_interview.py, tests/test_f031_init_loop.py, tests/test_f031_pipeline_refactor.py, tests/test_f031_utils_helpers.py, tests/test_f037_blocker_resolution.py, tests/test_fix_mode.py, tests/test_functions_unit.py, tests/test_sandbox_fixes.py, tests/test_task6_profiles.py, tests/test_task7_vcs_flag.py
    - Dependencies: Task 5
    - Parallelizable: yes
    - Description: For each test file, update the from utils import X or import utils statements to import from the correct new module. The function names and signatures are unchanged — tests only need the import path updated. For tests that do import utils and call utils.some_function(), either switch to from new_module import some_function or keep as import new_module as utils_alias if there are many call sites. Prefer explicit imports over aliases to make test code self-documenting.
    
    Task 12: Run full test suite — verify all 1,029 tests pass
    - Files: (none — validation only)
    - Dependencies: Tasks 6, 7, 8, 9, 10, 11
    - Parallelizable: no
    - Description: Run python3 -m pytest tests/ -q from the project root. All 1,029 tests must pass. If any test fails, fix the import path in that test and re-run. Run the full integration suite: python3 -m pytest tests/ -q (no exclusions). Also run python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" to verify the entry script compiles. Run python3 -m py_compile dokima for lint. Verify bash -n scripts/nm && bash -n scripts/vet.
    
    6. Data Model
    
    No new entities. This is a pure refactor — all data structures remain identical. The only structural change is which file each function lives in.
    
    Module dependency graph (post-split):
    
    
    utils.py          ← cross-cutting infrastructure (no new deps)
    git_ops.py        ← imports from utils (globals: PROJECT_DIR, DEFAULT_BRANCH, etc.)
    spec_extract.py   ← imports from git_ops (git for _append_convention_rules, _extract_code_context)
    codebase_map.py   ← imports from utils (globals: PROJECT_DIR)
    control_panel.py  ← imports from utils (globals: OUTPUT_LOG), imports from git_ops (do_release for check_upgrade)
    pipeline.py       ← imports from all 5 modules
    agent.py          ← imports from git_ops + utils
    roadmap.py        ← imports from all 5 modules
    tasks.py          ← imports from git_ops + utils
    dokima            ← imports from all 5 modules + vcs + agent + tasks + roadmap + pipeline
    
    
    7. COTS Build-vs-Buy
    
    Decision: Python module system
    Verdict: Build (stdlib)
    Justification: Python's import is the mechanism. No framework needed.
    ────────────────────────────────────────
    Decision: Import sorting tool (isort)
    Verdict: Buy if available, skip if not
    Justification: Pure cosmetic. Not worth a dependency if not already
      installed.
    ────────────────────────────────────────
    Decision: Refactoring tool
    Verdict: Build
    Justification: Manual cut-and-paste with test safety net. No automated
      refactor tool needed — the functions are already independent.
    
    8. Test Plan
    
    Happy path:
    - After the split, python3 -m pytest tests/ -q reports 1,029 passed, 4 skipped — identical to pre-split
    - python3 -c "from git_ops import git, gh, detect_repo" succeeds
    - python3 -c "from spec_extract import extract_pr_sections, clean_spec_content" succeeds
    - python3 -c "from codebase_map import generate_codebase_map" succeeds
    - python3 -c "from control_panel import handle_status, show_help" succeeds
    - python3 -c "from utils import slugify, acquire_lock, _sanitize_prompt" succeeds
    - The entry script python3 dokima --help-json outputs valid JSON
    
    Edge cases:
    - A test does import utils; utils.slugify("test") — must still work (utils.py keeps slugify)
    - A test does import utils; utils.extract_pr_sections(...) — must update import (extract_pr_sections moved to spec_extract)
    - Codebase map regeneration: running generate_codebase_map(project_dir) after the split must produce a map that lists the 4 new modules and no longer lists utils.py's moved functions under a single "Utilities" header — they should appear under appropriate domain groups
    - test_codebase_map.py tests that write synthetic Python files with import utils — those test fixtures don't need to change (they test analysis, not real imports)
    - _extract_code_context() calls git("diff", ...) — after split, spec_extract.py must import git from git_ops.py
    - check_upgrade() calls do_release() — after split, control_panel.py must import do_release from git_ops.py
    
    Failure modes:
    - Circular import: if two modules import from each other at module level, Python raises ImportError. Verify by importing each module in isolation.
    - Missing function: if a function is moved but a caller still imports from utils, tests fail with ImportError. Every test failure is a signal.
    - Stale .pyc cache: pycache directories may have old bytecode. Run find . -name 'pycache' -exec rm -rf {} + before testing.
    - F040 not yet merged: if PipelineContext isn't available, the new modules still import from utils for globals — this works. The spec doesn't assume F040 is done.
    
    Contract invariants:
    - After the split, every public function that existed before still exists at the same import depth (no nested submodules)
    - All function signatures are byte-for-byte identical to pre-split
    - All module-level globals remain in utils.py — no globals are duplicated across modules
    - from utils import X still works for everything that stays in utils.py
    - The git log shows the new files as "created" but blame traces through to the original utils.py (functions are copied verbatim, not rewritten)
    
    9. Panel Split
    
    Wave 1 (sequential — all modify utils.py):
    - Task 1 → Task 2 → Task 3 → Task 4 → Task 5
    - 1 coder agent, 5 sequential steps
    - Each task creates one new module and removes its functions from utils.py
    
    Wave 2 (parallel — different files):
    - Tasks 6, 7, 8, 9, 10, 11 — all parallel
    - 5 coder agents max (one per consumer file + one for all 14 test files)
    - Each task touches completely different files
    
    Wave 3 (sequential — validation):
    - Task 12
    - 1 coder agent, runs tests and fixes any breakage
    
    Total: 3 waves, 12 tasks, ~5 coders in wave 2
    
    10. Build & Deploy
    
    - No deploy step — this is a source refactor
    - CI: F042's test.yml runs python3 -m pytest tests/ -q on push/PR — this will catch import errors
    - Pre-merge: run full test suite locally
    - Post-merge: verify dokima next still works end-to-end on a test project
    
    11. Risk Register
    
    #: R1
    Risk: Circular import between new modules
    Severity: High
    Mitigation: Verify import graph before committing. spec_extract → git_ops
      is the only cross-import. No module imports from spec_extract except
      pipeline/roadmap/dokima.
    Trigger: ImportError at module load
    ────────────────────────────────────────
    #: R2
    Risk: Test imports broken — 14 files need updates
    Severity: Medium
    Mitigation: Batch test import updates in Task 11. Every test failure after
      split is an import path problem — grep for from utils import in test
      files and fix.
    Trigger: Test count drops below 1,029
    ────────────────────────────────────────
    #: R3
    Risk: Stale bytecode causing false passes
    Severity: Low
    Mitigation: find . -name 'pycache' -delete before final test run
    Trigger: Tests pass but production fails
    ────────────────────────────────────────
    #: R4
    Risk: F040 PipelineContext not yet merged
    Severity: Medium
    Mitigation: This spec works without F040 — new modules import globals from
      utils.py. If F040 is merged first, the new modules get ctx instead of
      globals (simpler). Either order works.
    Trigger: F040 merged first → simpler imports; F041 merged first → works
      as-is
    ────────────────────────────────────────
    #: R5
    Risk: _IMPORTING_PANEL override pattern breaks
    Severity: Medium
    Mitigation: halt_and_revert() and detect_repo() use _IMPORTING_PANEL for
      test patching. These move to git_ops.py. Ensure git_ops.py has from
      utils import _IMPORTING_PANEL or accept _IMPORTING_PANEL as a parameter.
    Trigger: Test patching fails silently
    ────────────────────────────────────────
    #: R6
    Risk: HELP_TEXT/CLI_METADATA references moved functions
    Severity: Low
    Mitigation: These are string constants, not code. Moving them to
      control_panel.py doesn't break anything — they're just printed. Verify
      dokima --help still works.
    Trigger: --help output is empty or truncated
    
    12. Anti-Creep
    
    Features explicitly NOT in scope:
    - Do NOT refactor function internals. Copy-paste verbatim. No "while I'm here" improvements.
    - Do NOT change function signatures. Even if _safe_run(cmd_str, cwd, timeout=300) could take a context, don't touch it.
    - Do NOT add type hints. This is a mechanical split, not a typing pass.
    - Do NOT add tests. The existing 1,029 tests are the safety net. No new test coverage.
    - Do NOT add init.py or make a package. Modules stay at the project root alongside utils.py.
    - Do NOT touch vcs.py, status.py, or any other module. Only utils.py and the new files.
    - Do NOT run isort or any auto-formatter. Manual imports only — coder decides import order.
    - Do NOT merge functions from within a module. Even if two spec_extract functions are similar, keep them separate.
    
    13. Sign-Off Checklist
    
    - [ ] All 4 new modules (git_ops.py, spec_extract.py, codebase_map.py, control_panel.py) created at project root
    - [ ] Each new module has a docstring describing its domain
    - [ ] utils.py slimmed to ~550 lines — only cross-cutting infrastructure remains
    - [ ] All consumer module imports updated (pipeline.py, agent.py, roadmap.py, tasks.py, dokima)
    - [ ] All 14 test file imports updated
    - [ ] No circular imports — each new module imports cleanly in isolation
    - [ ] python3 -m pytest tests/ -q reports 1,029 passed, 4 skipped (same as pre-split)
    - [ ] python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" succeeds
    - [ ] python3 -m py_compile dokima succeeds
    - [ ] dokima --help prints the full help text (HELP_TEXT constant moved but still accessible)
    - [ ] dokima --help-json outputs valid JSON (CLI_METADATA moved but still accessible)
    - [ ] Codebase map regenerated — shows new modules under appropriate domain groups