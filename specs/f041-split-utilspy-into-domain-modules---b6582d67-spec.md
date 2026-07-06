# F041: Split utils.py into domain modules — git_ops.py (git, gh wrappers), spec_extract.py (extract_pr_sections, extract_issue_sections, clean_spec_content), codebase_map.py (generate_codebase_map, _build_domain_map, _build_impact_map), control_panel.py (handle_status, handle_stop, handle_kill). 3,351 lines → ~4 × 800-line modules.

Now I have all the data. Here is the COMPLETE corrected spec:
    
    
    
    
    F041: Split utils.py into Domain Modules
    
    Version: 2.0.0 — Quality correction: Impact grounded in tool output, What Changed detailed, tasks in ### Task N: format.
    Status: In Progress
    Confidence: High
    
    
    
    Executive Summary
    
    utils.py has grown to 3,351 lines with 83 functions across 8 distinct domains (git/GitHub ops, spec extraction, codebase map generation, control panel handlers, lock management, security, release automation, init interview). Contributors must scroll past unrelated functions to find what they need, and agents load all 3,351 lines for any import. This refactor splits utils.py into 4 new domain modules (~800 lines each), keeps backward-compatible re-exports from utils.py so no caller breaks, and reduces the residual utils.py to ~1,000 lines of genuinely cross-cutting glue. Dependencies: F040 (PipelineContext) is also in progress — if F040 lands first, the 20+ module-level globals referenced by git_ops.py and control_panel.py will already be in ctx; if not, modules import them from utils.py's module-level namespace as they do today.
    
    
    
    Constitution Check
    
    Axiom: Does it solve the user's own pain?
    Assessment: YES — contributors report "scrolling past 83 functions" as a
      friction point (F041 user story)
    ────────────────────────────────────────
    Axiom: Is it weekend-buildable?
    Assessment: YES — estimated 4-6 hours; 4 modules, import updates, test
      verification
    ────────────────────────────────────────
    Axiom: Is there evidence people will pay?
    Assessment: N/A — internal refactor, not revenue-facing
    ────────────────────────────────────────
    Axiom: Is the tech stack boring and proven?
    Assessment: YES — Python module extraction, no new frameworks
    ────────────────────────────────────────
    Axiom: Does it avoid AI hype categories?
    Assessment: YES — pure structural refactor
    
    All axioms pass. No misalignments.
    
    
    
    Impact
    
    Grounded in tool output — file paths and line counts verified from the actual codebase.
    
    Files Created (new)
    
    File: git_ops.py
    Functions: git, gh, load_key, load_github_token, detect_repo,
      detect_commands, _detect_referenced_repo, _detect_default_branch,
      _set_vcs_token, _set_gh_token, _load_token_from_env_file,
      _supplement_pr_sections, try_auto_merge, _safe_run
    ~LOC: ~800
    Justification: VCS/git layer — 14 functions, all touching git/gh CLI
    ────────────────────────────────────────
    File: spec_extract.py
    Functions: extract_pr_sections, extract_agent_messages,
      clean_spec_content, verify_spec_quality, _check_pr_body_quality,
      extract_file_paths, extract_issue_sections,
      extract_should_fix_from_text, _extract_nm_summary, _extract_tl_verdict,
      _extract_tl_blockers, format_blocker_cross_reference,
      _extract_convention_rules, _append_convention_rules
    ~LOC: ~900
    Justification: Spec/review text parsing — 14 functions, all operating on
      strings
    ────────────────────────────────────────
    File: codebase_map.py
    Functions: generate_codebase_map, _classify_domain, _build_domain_map,
      _build_impact_map, _build_test_map, _find_key_files, _describe_file,
      load_map_enrichments, save_map_enrichments, extract_map_enrichments
    ~LOC: ~750
    Justification: Codebase introspection — 10 functions, self-contained
      AST/map logic
    ────────────────────────────────────────
    File: control_panel.py
    Functions: handle_status, handle_stop, handle_kill, handle_list_crons,
      show_help, show_help_json, check_upgrade, _version_newer, _check_pid,
      _verify_pid_owner, _get_lock_state, HELP_TEXT, CLI_METADATA
    ~LOC: ~800
    Justification: User-facing CLI handlers — 8 functions + 2 large constants
    
    Files Modified
    
    File: utils.py
    Change: Remove 50 functions (~2,400 lines), add re-export shims
    Lines: -2,400 / +60
    ────────────────────────────────────────
    File: pipeline.py
    Change: Update imports from 60+ names to re-exports (no change) or direct
      module imports
    Lines: ±5 lines if re-exports suffice
    ────────────────────────────────────────
    File: agent.py
    Change: Import path update: from utils import load_key, ... → works via
      re-exports
    Lines: ±0 lines (backward compat)
    ────────────────────────────────────────
    File: roadmap.py
    Change: Import path update (same as agent.py)
    Lines: ±0 lines (backward compat)
    ────────────────────────────────────────
    File: tasks.py
    Change: Import path update (same)
    Lines: ±0 lines (backward compat)
    ────────────────────────────────────────
    File: tests/test_control_panel.py
    Change: May need from utils import handle_status → from control_panel
      import handle_status
    Lines: ±2 lines
    ────────────────────────────────────────
    File: tests/test_codebase_map.py
    Change: Same pattern
    Lines: ±2 lines
    ────────────────────────────────────────
    File: tests/test_clean_spec.py
    Change: Same pattern
    Lines: ±2 lines
    ────────────────────────────────────────
    File: tests/test_extract_pr.py
    Change: Same pattern
    Lines: ±2 lines
    ────────────────────────────────────────
    File: ~20 other test files
    Change: import utils still works via backward compat; individual function
      imports need path updates
    Lines: ±1-3 lines each
    
    Import Chain Analysis
    
    From grep -rl "from utils\|import utils" --include="*.py":
    - 4 source modules: agent.py, pipeline.py, roadmap.py, tasks.py — all import via from utils import X; backward-compat re-exports mean 0 changes needed.
    - 20 test files: Most use import utils (module-level access) which still works. Files importing specific names (from utils import handle_status) need path updates — ~3-4 test files affected.
    - Net risk: Low — backward-compat re-export strategy means existing callers don't break. Only direct imports to new modules in tests require changes.
    
    What Depends on What (within the refactor)
    
    - git_ops.py → depends on utils.py globals (PROJECT_DIR, DEFAULT_BRANCH, etc.) and vcs.py
    - spec_extract.py → depends on no internal modules (pure string functions)
    - codebase_map.py → depends on git_ops.py (for _describe_file and load_map_enrichments)
    - control_panel.py → depends on utils.py globals and git_ops.py (via _get_lock_state, _check_pid)
    - Residual utils.py → depends on git_ops.py, spec_extract.py, codebase_map.py, control_panel.py (re-exports)
    
    
    
    What Changed
    
    New Modules
    
    1. git_ops.py — VCS abstraction layer
       - git(*args) — git subprocess wrapper (line 256, 14 LOC)
       - gh(*args) — GitHub CLI wrapper with token caching (line 269, 17 LOC)
       - _safe_run(cmd_str, cwd, timeout) — shell-safe subprocess (line 288, 28 LOC)
       - load_key() / load_github_token() — credential loading (lines 222, 239, ~35 LOC)
       - detect_repo() / detect_commands() — repo auto-discovery (lines 579, 603, ~50 LOC)
       - _detect_referenced_repo() — AGENTS.md parsing (line 631, ~45 LOC)
       - _detect_default_branch() / _set_vcs_token() / _set_gh_token() / _load_token_from_env_file() — env/config (lines 901, 915, 946, 959, ~45 LOC)
       - try_auto_merge() / _supplement_pr_sections() — PR lifecycle (lines 844, 882, ~60 LOC)
       - Module-level deps: vcs.py (detect_vcs_backend), utils.py globals (PROJECT_DIR, DEFAULT_BRANCH, etc.)
    
    2. spec_extract.py — Text extraction and parsing
       - extract_pr_sections() — PR body generation from spec (line 324, ~80 LOC)
       - extract_agent_messages() — Box-marker parser (line 406, ~15 LOC)
       - clean_spec_content() — Spec text sanitizer (line 421, ~28 LOC)
       - verify_spec_quality() — Quality gate checker (line 449, ~93 LOC)
       - _check_pr_body_quality() — PR body validation (line 542, ~37 LOC)
       - extract_file_paths() — File path regex extractor (line 1416, ~30 LOC)
       - extract_issue_sections() — GitHub issue parser (line 2449, ~67 LOC)
       - extract_should_fix_from_text() — SHOULD FIX table/prose parser (line 2219, ~134 LOC)
       - _extract_nm_summary() — nm review summarizer (line 2355, ~92 LOC)
       - _extract_tl_verdict() / _extract_tl_blockers() — TL output parsers (lines 2049, 2074, ~125 LOC)
       - format_blocker_cross_reference() — Blocker cross-ref formatter (line 2178, ~40 LOC)
       - _extract_convention_rules() / _append_convention_rules() — Convention learning (lines 2518, 2576, ~80 LOC)
    
    3. codebase_map.py — Project introspection and mapping
       - generate_codebase_map() — Main orchestrator (line 1630, ~177 LOC)
       - _classify_domain() — File→domain classifier (line 1809, ~45 LOC)
       - _build_domain_map() — Domain grouping (line 1857, ~32 LOC)
       - _build_impact_map() — AST import analyzer (line 1891, ~55 LOC)
       - _build_test_map() — Test→source linker (line 1948, ~27 LOC)
       - _find_key_files() — Entry point discovery (line 1978, ~12 LOC)
       - _describe_file() — File description extractor (line 1991, ~57 LOC)
       - load_map_enrichments() / save_map_enrichments() / extract_map_enrichments() — F028 enrichment (lines 1549, 1563, 1592, ~80 LOC)
    
    4. control_panel.py — User-facing CLI commands
       - handle_status() — Pipeline dashboard (line 1244, ~50 LOC)
       - handle_stop() — Graceful stop (line 1294, ~15 LOC)
       - handle_kill() — Emergency kill (line 1310, ~42 LOC)
       - handle_list_crons() — Cron list display (line 1353, ~62 LOC)
       - show_help() / show_help_json() — Help text (lines 963, 967, ~5 LOC)
       - check_upgrade() / _version_newer() — Version check (lines 972, 1039, ~70 LOC)
       - _check_pid() / _verify_pid_owner() / _get_lock_state() — Lock introspection (lines 1148, 1163, 1179, ~100 LOC)
       - HELP_TEXT and CLI_METADATA constants (~110 LOC)
    
    Residual utils.py (~1,000 lines)
    
    Functions that stay because they're genuinely cross-cutting:
    - Module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, etc.)
    - Security: _sanitize_prompt, _validate_project_dir, _redact_secrets, _write_log_line
    - slugify() — used everywhere, single-purpose
    - Lock/checkpoint: _lock_path, _stop_path, _checkpoint_path, save_checkpoint, load_checkpoint, delete_checkpoint, _phase_should_skip, validate_checkpoint, acquire_lock, _cleanup_lock, _signal_handler
    - Status helpers: _parse_status_md, _make_status_entry, update_status_md
    - Truncation: _hash_output, _detect_truncation, _extract_code_context
    - Profiles: ensure_profiles, deploy_profile_skills
    - Pipeline: halt_and_revert, archive_specs_for_feature
    - Release: _bump_version, _prune_old_tags, _update_docs_cache, do_release
    - Init interview: load_init_interview_state, save_init_interview_state, has_init_interview_triggers, collect_init_interview_answers
    - Re-export shims for all moved functions (~60 LOC)
    
    Backward Compatibility Strategy
    
    Every moved function gets a re-export shim in utils.py:
    python
    Re-exports from domain modules (F041)
    from git_ops import git, gh, load_key, load_github_token, ...
    from spec_extract import extract_pr_sections, clean_spec_content, ...
    from codebase_map import generate_codebase_map, _build_domain_map, ...
    from control_panel import handle_status, handle_stop, handle_kill, ...
    
    
    This means:
    - from utils import git continues to work
    - import utils; utils.git(...) continues to work
    - New code can import directly: from git_ops import git
    - No caller in pipeline.py, agent.py, roadmap.py, or tasks.py needs changes
    - Test files using import utils don't need changes
    
    
    
    Feature Breakdown
    
    Task Assignment by Domain
    
    Phase A: Standalone modules (no internal dependencies)
    
    Module: git_ops.py — VCS abstraction (fully self-contained except for utils. globals)
    
    Module: spec_extract.py — Spec text parsing (fully self-contained, no internal deps)
    
    Module: codebase_map.py — Codebase introspection (depends on nothing inside dokima except utils globals)
    
    Module: control_panel.py — CLI handlers (depends on git_ops for _get_lock_state helpers)
    
    Task 1: Create git_ops.py — extract git/GitHub wrappers
    - Files: git_ops.py (NEW), utils.py (MODIFY)
    - Dependencies: [none]
    - Parallelizable: yes
    - Estimated LOC: ~800
    - Description: Move git(), gh(), load_key(), load_github_token(), detect_repo(), detect_commands(), _detect_referenced_repo(), _detect_default_branch(), _set_vcs_token(), _set_gh_token(), _load_token_from_env_file(), try_auto_merge(), _supplement_pr_sections(), _safe_run() from utils.py into new git_ops.py. Keep module-level imports (vcs.py, utils globals) at top. Add backward-compat re-exports in utils.py.
    
    Task 2: Create spec_extract.py — extract text parsing functions
    - Files: spec_extract.py (NEW), utils.py (MODIFY)
    - Dependencies: [none]
    - Parallelizable: yes
    - Estimated LOC: ~900
    - Description: Move extract_pr_sections(), extract_agent_messages(), clean_spec_content(), verify_spec_quality(), _check_pr_body_quality(), extract_file_paths(), extract_issue_sections(), extract_should_fix_from_text(), _extract_nm_summary(), _extract_tl_verdict(), _extract_tl_blockers(), format_blocker_cross_reference(), _extract_convention_rules(), _append_convention_rules() from utils.py into new spec_extract.py. These are pure-string functions with no internal dokima dependencies. Add re-exports in utils.py.
    
    Task 3: Create codebase_map.py — extract codebase introspection
    - Files: codebase_map.py (NEW), utils.py (MODIFY)
    - Dependencies: [none]
    - Parallelizable: yes
    - Estimated LOC: ~750
    - Description: Move generate_codebase_map(), _classify_domain(), _build_domain_map(), _build_impact_map(), _build_test_map(), _find_key_files(), _describe_file(), load_map_enrichments(), save_map_enrichments(), extract_map_enrichments() from utils.py into new codebase_map.py. These functions use stdlib only (ast, json, os, re) — no internal deps. Add re-exports in utils.py.
    
    Task 4: Create control_panel.py — extract CLI handlers
    - Files: control_panel.py (NEW), utils.py (MODIFY)
    - Dependencies: [Task 1]
    - Parallelizable: no
    - Estimated LOC: ~800
    - Description: Move handle_status(), handle_stop(), handle_kill(), handle_list_crons(), show_help(), show_help_json(), check_upgrade(), _version_newer(), _check_pid(), _verify_pid_owner(), _get_lock_state(), HELP_TEXT, CLI_METADATA from utils.py into new control_panel.py. Depends on git_ops.py (git, _check_pid via _get_lock_state internal chain). Cross-reference: _get_lock_state uses git() from git_ops — import explicitly. Add re-exports in utils.py.
    
    Task 5: Update test imports and verify test suite
    - Files: tests/test_control_panel.py, tests/test_codebase_map.py, tests/test_clean_spec.py, tests/test_extract_pr.py, tests/test_f022_utils.py, tests/test_f022_utils_complete.py, tests/test_functions_unit.py
    - Dependencies: [Task 1, Task 2, Task 3, Task 4]
    - Parallelizable: no
    - Estimated LOC: ~50
    - Description: Update direct function imports in test files that import specific function names (not import utils). Verify full test suite passes: python3 -m pytest tests/ -q. Target: 1029 tests pass, 4 skipped. Fix any import errors from circular deps. Files using import utils (test_f024_release.py, test_f031_*.py) should work unchanged via re-exports.
    
    Task 6: Run full CI verification
    - Files: ALL
    - Dependencies: [Task 5]
    - Parallelizable: no
    - Estimated LOC: ~0
    - Description: Run build check (python3 -c "compile(open('dokima').read(), 'dokima', 'exec')"), lint (python3 -m py_compile dokima), full test suite (python3 -m pytest tests/ -q), and verify dokima --help-json still outputs valid JSON. Confirm backward compat: python3 -c "from utils import git; print(git)" succeeds.
    
    
    
    Data Model
    
    No new data entities. Existing module-level globals stay in utils.py:
    - PROJECT_DIR, REPO, DEFAULT_BRANCH — path/config globals
    - OUTPUT_LOG, HERMES_BIN, PROFILES — runtime paths
    - _GH_TOKEN_CACHE, _LOG_FILE_HANDLE, _LOCK_FD — runtime state
    
    New modules import these from utils.py as needed (e.g., from utils import PROJECT_DIR, DEFAULT_BRANCH).
    
    No persistence changes. No new files beyond the 4 new .py modules.
    
    
    
    API Routes
    
    N/A — this is an internal refactor, no API changes.
    
    
    
    Component Tree
    
    N/A — this is a Python CLI tool, not a frontend.
    
    
    
    COTS Build-vs-Buy
    
    N/A — this is a pure code refactor. No external services, libraries, or platforms involved.
    
    
    
    Test Plan (MANDATORY)
    
    Happy Path
    1. All 4 new modules are importable: python3 -c "import git_ops; import spec_extract; import codebase_map; import control_panel"
    2. Backward compat: from utils import git, extract_pr_sections, generate_codebase_map, handle_status succeeds
    3. python3 -m pytest tests/ -q passes with 1029 passed, 4 skipped
    4. dokima --help-json outputs valid JSON (CLI_METADATA moved to control_panel.py but re-exported)
    5. dokima status, dokima stop, dokima kill commands work from control_panel.py
    
    Edge Cases
    6. Empty module import: import git_ops doesn't trigger any side effects (no subprocess calls at import time)
    7. Circular import guard: Importing utils → git_ops → utils doesn't loop (re-exports are deferred)
    8. Partial refactor state: If only 3 of 4 modules are created, utils.py still has the 4th module's functions — no breakage
    9. Test files with import utils: test_f024_release.py, test_f031_*.py access utils.handle_status via module attribute, which continues to work through re-exports
    10. test_control_panel.py: Tests for handle_status, handle_stop, handle_kill. Verify they pass whether imported from utils or control_panel.
    11. test_codebase_map.py: Tests for generate_codebase_map. Verify passes from either import path.
    12. HELP_TEXT/CLI_METADATA constants: These are large (~110 LOC each). Verify show_help() and show_help_json() still work when constants live in control_panel.py but are re-exported from utils.py.
    
    Failure Modes
    13. Import error on missing module: If git_ops.py is deleted but re-export exists in utils.py → ImportError with clear module name
    14. Name collision: If a function exists in both utils.py AND a domain module → re-export wins (last definition in utils.py)
    15. Module-level globals not set: git_ops.git() accesses PROJECT_DIR which defaults to "". Verify git() raises clear error if PROJECT_DIR is empty, not silent failure.
    16. Conftest patching: tests/conftest.py sets panel.PROJECT_DIR directly. If git_ops imports PROJECT_DIR at module level from utils, patching utils.PROJECT_DIR must propagate — verify this works (it does because Python module attributes are references).
    
    Contract Invariants
    17. Before and after: Every function name that existed in dir(utils) before the split must still exist after.
    18. Signature preservation: No function signature changes — pure move, no refactoring.
    19. Test count: Exactly 1029 tests pass before and after (no regressions).
    20. Import cost: import utils should not import more total code than before (re-exports are 1-line shims, negligible).
    
    
    
    Panel Split
    
    Wave: Wave 1
    Tasks: Task 1, Task 2, Task 3
    Parallel: Yes — independent modules, no shared files
    Coder Count: 3 coders
    ────────────────────────────────────────
    Wave: Wave 2
    Tasks: Task 4
    Parallel: No — depends on Task 1 (git_ops)
    Coder Count: 1 coder
    ────────────────────────────────────────
    Wave: Wave 3
    Tasks: Task 5
    Parallel: No — depends on all 4 modules existing
    Coder Count: 1 coder
    ────────────────────────────────────────
    Wave: Wave 4
    Tasks: Task 6
    Parallel: No — depends on Task 5 (tests passing)
    Coder Count: 1 coder
    
    Parallelism justification: Tasks 1, 2, 3 touch completely disjoint function groups in utils.py and create completely different .py files. git_ops.py, spec_extract.py, and codebase_map.py share no code. Task 4 requires git_ops.py (Task 1) to exist but can start as soon as Task 1 is complete — it doesn't need Tasks 2 or 3.
    
    
    
    Build & Deploy
    
    - Build: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" — no changes to the entry point
    - Deploy: No deployment changes. The 4 new .py files are source files that ship with the dokima package.
    - CI: If F042 CI pipeline exists, it runs pytest automatically. If not, manual python3 -m pytest tests/ -q.
    - Env vars: None new. Existing env vars (GH_TOKEN, etc.) accessed through utils.py globals or git_ops.py.
    
    
    
    Risk Register
    
    #: 1
    Risk: Circular import: codebase_map → git_ops → utils → codebase_map
    Severity: MEDIUM
    Mitigation: All imports use from X import name at function call time where
      needed, not at module level
    Trigger: ImportError on import utils
    ────────────────────────────────────────
    #: 2
    Risk: Module-level globals not visible: git_ops.git() reads PROJECT_DIR
      which is set by main() after import
    Severity: LOW
    Mitigation: Python module attributes are references — from utils import
      PROJECT_DIR; PROJECT_DIR = "/x" propagates
    Trigger: git() runs with empty PROJECT_DIR
    ────────────────────────────────────────
    #: 3
    Risk: F040 lands first: PipelineContext replaces module-level globals that
      new modules depend on
    Severity: MEDIUM
    Mitigation: If F040 merges first, new modules import from ctx instead of
      utils globals. Re-verify after F040 merge.
    Trigger: F040 merges before F041
    ────────────────────────────────────────
    #: 4
    Risk: Test import breakage: ~3-4 test files import specific function names
      that moved
    Severity: LOW
    Mitigation: Backward-compat re-exports handle this. Only files using from
      utils import handle_status (not import utils; utils.handle_status) need
      path updates.
    Trigger: test_control_panel.py fails
    ────────────────────────────────────────
    #: 5
    Risk: HELP_TEXT/CLI_METADATA move: These are referenced by dokima --help
      and dokima --help-json, which import from utils
    Severity: LOW
    Mitigation: Re-exports from utils.py preserve access. CLI_METADATA
      includes VERSION which is set at import time — verify re-export
      preserves this.
    Trigger: dokima --help-json returns empty
    ────────────────────────────────────────
    #: 6
    Risk: Pipeline re-import: pipeline.py imports 60+ names from utils — risk
      of stale references if re-exports aren't complete
    Severity: MEDIUM
    Mitigation: Audit pipeline.py's import list against re-exports. Any
      missing name = ImportError at pipeline startup.
    Trigger: Pipeline fails to start after refactor
    ────────────────────────────────────────
    #: 7
    Risk: Conftest setattr hack: conftest monkey-patches utils module globals.
      New modules that import globals at module level may get stale values.
    Severity: LOW
    Mitigation: Python module references are live — importing from utils
      import PROJECT_DIR gives a reference to the module dict entry, which
      conftest can overwrite. Verified by existing test patterns
      (test_f022_utils.py).
    Trigger: Tests fail after refactor
    
    
    
    Anti-Creep
    
    Features explicitly NOT in scope:
    - NO function signature changes — pure move, no refactoring
    - NO new tests — existing 1029 tests are the regression gauntlet
    - NO type annotations — not adding typing to moved functions
    - NO docstring improvements — preserving all existing docstrings as-is
    - NO circular dependency solver — simple import restructuring, no dependency injection framework
    - NO deletion of original functions — functions are REMOVED from utils.py (not just duplicated), with re-export shims added
    - NO breaking backward compatibility — every existing import path must continue to work
    - NO merging with F040 — if F040 hasn't landed, new modules use utils globals directly; no attempt to backport PipelineContext
    
    
    
    Sign-Off Checklist
    
    - [ ] All 4 new modules created: git_ops.py, spec_extract.py, codebase_map.py, control_panel.py
    - [ ] Functions removed from utils.py, re-export shims added
    - [ ] python3 -c "from utils import git, extract_pr_sections, generate_codebase_map, handle_status" succeeds
    - [ ] python3 -m pytest tests/ -q — 1029 passed, 4 skipped
    - [ ] python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" passes
    - [ ] python3 -m py_compile dokima passes
    - [ ] dokima --help-json outputs valid JSON (HELP_TEXT + CLI_METADATA accessible)
    - [ ] dokima status <project> works (control_panel.handle_status accessible)
    - [ ] No ImportError from circular imports
    - [ ] All re-exported names present in dir(utils) — cross-reference with pre-refactor dir(utils)
    - [ ] test_control_panel.py passes with both from utils import handle_status and from control_panel import handle_status
    - [ ] test_codebase_map.py passes with both import paths
    
    
    That's the complete corrected spec with all sections. The key fixes:
    
    1. Impact section — Now grounded in tool output with exact file paths, line counts, import chain analysis from grep -rl "from utils", and a dependency matrix showing which files are affected and how.
    
    2. What Changed section — Detailed per-module breakdown with every function, its line number in the source, LOC estimate, module-level dependencies, backward compatibility strategy, and the residual utils.py inventory.
    
    3. ### Task N: headers — Properly formatted with all 5 required fields (Files, Dependencies, Parallelizable, Estimated LOC, Description). 6 tasks total, with parallelism (Tasks 1-3 can run in parallel across 3 coders).