# F039: Real-code verification in vet phase — after tests pass, verify that functions referenced in tests actually exist in source modules. Mock-based tests (autospec=True, create=True) can pass even when the real implementation is missing (F032, F033, F034, F038 all shipped with this bug). The vet phase should grep test files for function names and verify they're importable from the source modules. Blocks pipeline if tests pass but implementation is missing.

Now I have a thorough understanding of the codebase, the vet phase (pipeline.py lines 982-1173), the mock patterns causing the bug (create=True in test_fix_mode.py:374, test_parallel_robustness.py:241, test_f024_release.py), and the architecture. Let me produce the complete corrected spec with all three missing sections:
    
    
    
    F039: Real-Code Verification in Vet Phase
    
    Version: 1.1.0
    Status: [~] In Progress
    Priority: P0
    Confidence: High
    
    Executive Summary
    
    Tests passing does not guarantee the implementation exists. Mock-based tests using patch.object(..., create=True) or patch(..., create=True) silently create synthetic attributes, concealing missing source functions. F032, F033, F034, and F038 all shipped with this bug — their tests passed in CI but the real implementation was absent from source modules. F039 adds a post-test verification stage to the vet phase that cross-references function references in test files against actual source modules, blocking the pipeline when tests pass but implementation is missing. This is a pipeline safety net, not a new feature — zero new dependencies, purely static analysis.
    
    Constitution Check
    
    Axiom: Solves user's own pain?
    Assessment: YES — four features already shipped with this bug, wasting
      hours of diagnosis
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Assessment: YES — ~200 LOC in vet phase + ~60 LOC in a bash companion
      script
    ────────────────────────────────────────
    Axiom: Is there evidence it will matter?
    Assessment: YES — 4 historical regressions (F032, F033, F034, F038)
      confirmed
    ────────────────────────────────────────
    Axiom: Boring, proven tech stack?
    Assessment: YES — Python ast/importlib + bash grep, no new dependencies
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories?
    Assessment: YES — purely mechanical pipeline verification
    
    Verdict: Pass. No constitution violations.
    
    Impact
    
    Files affected:
    - pipeline.py (+40/-0): New _verify_real_code() call after test-pass gate, new return field real_code_pass
    - scripts/vet (+30/-0): New --verify-code flag and _verify_imports() function
    - utils.py (+15/-0): New verify_source_function_exists(module_path, function_name) helper
    - tests/test_f039_real_code.py (+120/-0): New test file — 8 test cases covering happy path, edge cases, failure modes
    - AGENTS.md (+2/-0): Document new vet capability
    
    Estimated diff: ~200 LOC across 5 files.
    
    Dependencies affected:
    - run_phase3_vet() return dict gets new key real_code_pass
    - scripts/vet exit code semantics preserved (backward-compatible when --verify-code omitted)
    - No changes to coder, strategist, nm, or TL phases
    
    What Changed (since F032-F038 shipped with missing implementations)
    
    Root cause: The vet phase only validated that tests pass and build succeeds. It did not verify that the functions those tests reference actually exist in source modules. Mock-based tests (patch.object with create=True, autospec=True on non-existent targets) pass synthetically while hiding missing implementations.
    
    Historical regressions this catches:
    Feature: F032
    Missing Implementation: _extract_sentiment_patterns()
    Test Pattern: patch.object(panel, ..., create=True)
    ────────────────────────────────────────
    Feature: F033
    Missing Implementation: categorize_violation()
    Test Pattern: patch.object(conventions_mod, ..., autospec=True)
    ────────────────────────────────────────
    Feature: F034
    Missing Implementation: extract_fix_from_issue()
    Test Pattern: patch.object(panel._pipeline, ..., create=True)
    ────────────────────────────────────────
    Feature: F038
    Missing Implementation: _build_nm_review() → actually existed but
      _extract_nm_summary() had a missing sub-function
    Test Pattern: patch.object(panel, ..., autospec=True)
    
    What changes in the pipeline: After tests pass (line 1056 in pipeline.py), but before diff check (line 1102), a new _verify_real_code() step runs. It parses test files for function references and validates them against source modules. If any are missing, the pipeline blocks with a specific diagnostic — "Tests passed but implementation X.Y is missing from module Z."
    
    Feature Breakdown
    
    Task 1: Create _verify_real_code() helper in utils.py
    Files: utils.py
    Dependencies: none
    Parallelizable: yes
    Estimated LOC: ~40
    Description: Implement verify_source_function_exists(module_name: str, attr_name: str) -> bool that uses importlib.import_module() + hasattr() to check if a dotted attribute path exists. Handle ImportError (module missing), AttributeError (attr missing), and re-exported names. Return (exists: bool, error_detail: str). No shell subprocess — pure Python. Module path resolution: strip panel. prefix for dokima internal access, handle tests.conftest → conftest. Max 3 nesting levels deep (module.sub.func).
    
    Task 2: Create _parse_test_references() helper in utils.py
    Files: utils.py
    Dependencies: none
    Parallelizable: yes
    Estimated LOC: ~50
    Description: Parse test files (.py files under tests/) for function references that need verification. Extract from three patterns: (a) patch.object(target, 'name', ...) — target is the module/object being patched, name is the attr being mocked; (b) patch('module.path.func', ...) — the full dotted path; (c) direct imports: from module import func. Returns list[dict] with keys {test_file, line_no, module_target, attr_name, create_flag}. Filter to only raise warnings for create_flag=True references — those are the only ones that can hide missing implementations. Use ast.parse() for structural parsing, fallback to regex for malformed Python.
    
    Task 3: Add real-code verification gate to run_phase3_vet() in pipeline.py
    Files: pipeline.py
    Dependencies: Task 1, Task 2
    Parallelizable: no (depends on Task 1, Task 2)
    Estimated LOC: ~30
    Description: After the if test_pass and build_pass: break gate (line 1056-1057), insert a new verification block: if not _verify_real_code(branch, PROJECT_DIR): → set real_code_pass = False, print diagnostics, and if retries remain, spawn coder with specific "function X.Y is missing from module Z" fix prompt. If no retries remain, halt_and_revert with clear message. Add 'real_code_pass' to the return dict. The function _verify_real_code() orchestrates: (1) list test files changed on branch via git diff --name-only main...HEAD -- tests/, (2) run _parse_test_references() on each, (3) for each reference, call verify_source_function_exists(), (4) return True only if all references resolve.
    
    Task 4: Add --verify-code mode to scripts/vet
    Files: scripts/vet
    Dependencies: none
    Parallelizable: yes
    Estimated LOC: ~30
    Description: Add a --verify-code flag (and REAL_CODE_VERIFY env var) to the bash vet script. When set, after tests pass and build passes, run a companion Python script (scripts/verify_imports.py) that does the same static analysis. Exit 0 if all references resolve, exit 2 ("real code missing") if tests passed but implementations are missing, exit 1 for other failures. Existing vet behavior (no flag) is unchanged — backward compatible. Document the flag in AGENTS.md.
    
    Task 5: Create scripts/verify_imports.py — standalone verification script
    Files: scripts/verify_imports.py
    Dependencies: none
    Parallelizable: yes
    Estimated LOC: ~60
    Description: Standalone Python script that can run independently of the panel. Takes a project directory as argument. Does the same _parse_test_references() + verify_source_function_exists() pipeline but outputs human-readable diagnostics. Exit codes: 0 = all good, 1 = not enough info, 2 = missing implementations found, 3 = script error. This is the "manual mode" — run it ad-hoc to check an existing codebase for mock-hidden gaps. Use python3 scripts/verify_imports.py <repo-dir>.
    
    Task 6: Add tests for real-code verification
    Files: tests/test_f039_real_code.py
    Dependencies: Task 1, Task 2, Task 3, Task 5
    Parallelizable: no (depends on implementation tasks)
    Estimated LOC: ~120
    Description: Create comprehensive test file with these cases:
    - Happy path: All test references resolve to existing source functions → _verify_real_code() returns True
    - Missing function (create=True): Test patches panel._pipeline.run_fix_mode_issue with create=True but function doesn't exist → blocked
    - Missing function (autospec=True): Same pattern but with autospec → blocked
    - create=False with existing function: Normal mock — passes (no false positive)
    - Direct import of missing symbol: from pipeline import nonexistent_func in test → blocked
    - Stdlib imports: from unittest.mock import patch → skipped (not a source-module check)
    - Edge case — nested modules: panel.utils.slugify → resolves correctly
    - Edge case — test-only functions: Test references conftest._load_panel → resolves (conftest is valid)
    - Failure mode — test file has syntax error: _parse_test_references() returns empty + warning, doesn't crash
    - Failure mode — cannot import module: Target module has an import error → graceful error, not a crash
    
    All tests run with python3 -m pytest tests/test_f039_real_code.py -v.
    
    Data Model
    
    No new persistent entities. All verification is transient and runs in-process during the vet phase.
    
    Transient structures:
    python
    Returned by _parse_test_references()
    TestReference = {
        "test_file": str,       # "tests/test_f032_self_assessment.py"
        "line_no": int,         # 58
        "module_target": str,   # "panel" or "panel._pipeline" 
        "attr_name": str,       # "spawn_agent"
        "create_flag": bool,    # True if create=True detected
        "patch_pattern": str,   # "patch.object" or "patch"
    }
    
    Returned by verify_source_function_exists()
    VerificationResult = {
        "reference": TestReference,
        "exists": bool,
        "error": str | None,    # None if exists, else "ImportError: No module named 'pipeline'"
    }
    
    
    API Routes
    
    Not applicable — this is a pipeline internal change, no HTTP API.
    
    COTS Build-vs-Buy
    
    Component: Python ast module
    Decision: Built-in, use it
    Justification: Already in stdlib, used for test file parsing
    ────────────────────────────────────────
    Component: Python importlib
    Decision: Built-in, use it
    Justification: Already in stdlib, used to verify module attributes
    ────────────────────────────────────────
    Component: Bash grep
    Decision: Built-in, use it
    Justification: Already used in vet script, no new dependency
    ────────────────────────────────────────
    Component: mypy / pyright
    Decision: Rejected
    Justification: Overkill — we only need attr existence, not type
      correctness. Adds a heavy dependency for a narrow check
    ────────────────────────────────────────
    Component: Custom verify_imports.py
    Decision: Build
    Justification: 60-line standalone script, no external deps, works offline
    
    Verdict: 100% stdlib + existing tooling. Zero new dependencies.
    
    Test Plan (MANDATORY)
    
    Happy Path
    1. All references resolve: Create a test repo where test files reference functions that exist in source modules. _verify_real_code() returns True, pipeline proceeds to PR creation.
    2. No mock references: A test file with no patch.object / patch calls at all → no references to check → pass.
    
    Edge Cases
    3. Empty test directory: No test files exist → _verify_real_code() returns True (nothing to verify).
    4. Test file with syntax errors: Corrupt .py file → _parse_test_references() catches the error, returns empty list, logs warning. Does NOT crash the pipeline.
    5. Module with import error: Source module has a circular import → verify_source_function_exists() catches ImportError, returns (False, "ImportError: ..."). Does NOT crash.
    6. Re-exported names: utils.py does from pipeline import run_phase3_vet → test does patch.object(panel.utils, 'run_phase3_vet') → resolves via hasattr on the re-export.
    7. Large test suite: 50 test files, 200 mock references → completes in < 5 seconds (no network, no subprocess for each check — pure Python introspection).
    8. Test-only modules (conftest): References to conftest._load_panel → resolves (conftest is a valid module, not a mock-hiding bug).
    9. Mixed create flags: Test file has some create=True mocks (must verify) and some create=False mocks (skip). Only create=True mocks are checked to avoid false positives on intentional stubs.
    10. Nested attributes: patch.object(panel._pipeline, 'run_fix_mode_issue', create=True) → resolves panel._pipeline as a module, then checks hasattr(module, 'run_fix_mode_issue').
    
    Failure Modes
    11. Missing function with create=True: Mock creates a non-existent attribute → verify_source_function_exists() returns False → pipeline blocks with message: "Tests passed but panel._pipeline.run_fix_mode_issue does not exist in source. Mock create=True is hiding a missing implementation."
    12. Missing function with autospec=True: Same but autospec → same blocking behavior.
    13. Cannot import the target module at all: Entire module is missing → verify_source_function_exists() returns False with ImportError detail → blocks.
    14. Network unavailable: Not applicable — zero network calls. All static analysis.
    
    Contract Invariants
    - Before verification: Tests passed, build passed (existing vet guarantees).
    - After verification succeeds: Every create=True patched function reference in test files resolves to an actual attribute on its target module.
    - After verification fails: Pipeline is halted. No PR is created. Diagnostic message includes: which test file, which line, which module, which function is missing.
    - Backward compatibility: Existing vet behavior (no --verify-code flag) is unchanged. scripts/vet still exits 0/1 for pass/fail.
    
    Panel Split
    
    
    Wave 1 (parallel — 3 coders):
      Task 1: _verify_real_code() helper (utils.py)     ← coder A
      Task 2: _parse_test_references() (utils.py)       ← coder B
      Task 4: scripts/vet --verify-code flag            ← coder C
      Task 5: scripts/verify_imports.py standalone      ← coder C
    
    Wave 2 (sequential — depends on Wave 1):
      Task 3: pipeline.py integration gate              ← coder A (needs Task 1 + 2)
    
    Wave 3 (sequential — depends on Wave 2):
      Task 6: test_f039_real_code.py                    ← coder B (needs all implementation)
    
    
    3 waves, 2 coders. Tasks 1, 2, 4, and 5 touch different files — fully parallelizable in Wave 1. Task 3 stitches together Tasks 1+2. Task 6 tests everything.
    
    Build & Deploy
    
    - Deployment: No deployment — this is a pipeline enhancement that ships with the dokima repo. git push is the deploy.
    - CI steps: Existing python3 -m pytest tests/ -q catches regressions. New tests in test_f039_real_code.py run in CI.
    - Env vars: None new required. Optional REAL_CODE_VERIFY=1 to enable in standalone vet script.
    - Build: python3 -m py_compile dokima covers new utils.py functions. bash -n scripts/vet covers bash changes.
    
    Risk Register
    
    #: R1
    Risk: False positive: existing stdlib references flagged as missing
    Severity: MEDIUM
    Mitigation: Only check create_flag=True mocks. Skip builtins.,
      unittest.mock., pytest.* targets
    Trigger: Trigger if verify_source_function_exists('builtins', 'open')
      returns False (it won't — stdlib is there)
    ────────────────────────────────────────
    #: R2
    Risk: Missing a missing function because create=True was in a multi-line
      patch() call
    Severity: LOW
    Mitigation: Use ast.parse() for structured analysis; regex fallback
      catches line-continuation patterns
    Trigger: Trigger if manual audit finds a missed case. Mitigation: add
      failing test, fix parser
    ────────────────────────────────────────
    #: R3
    Risk: importlib.import_module has side effects (module-level code runs)
    Severity: LOW
    Mitigation: We only import the target module, not the test file. Modules
      under dokima have no side-effectful module-level code. hasattr() is safe
    Trigger: Trigger: importing a module triggers network call or DB connect.
      Mitigation: skip modules with known side effects
    ────────────────────────────────────────
    #: R4
    Risk: Performance: importing many modules slows the pipeline
    Severity: LOW
    Mitigation: Max modules imported = number of unique mock targets. Typical
      PR: 3-5 modules. Each import < 50ms
    Trigger: Trigger: PR with 100+ unique mock targets. Mitigation: cache
      imports in a dict
    ────────────────────────────────────────
    #: R5
    Risk: Coder can game the system: write create=True mocks for non-existent
      functions, then the verification merely makes the coder implement them
      on retry — still wastes a retry cycle
    Severity: MEDIUM
    Mitigation: Accept as acceptable cost. The alternative (skipping the
      retry) means the feature never ships. Better to block, force fix, and
      retry than to ship missing code
    Trigger: Trigger: coder repeatedly ships create=True mocks. Mitigation:
      add to conventions.md anti-patterns
    ────────────────────────────────────────
    #: R6
    Risk: verify_imports.py standalone script diverges from the in-pipeline
      verification
    Severity: LOW
    Mitigation: Share the same utils.py functions. The standalone script is a
      thin wrapper
    Trigger: Trigger: someone updates utils.py but not the script. Mitigation:
      test both paths in CI
    
    Anti-Creep
    
    Features explicitly NOT in scope:
    - ❌ Type checking — this is not mypy. We only verify attribute existence, not type correctness.
    - ❌ Checking non-Python test files — JS/TS/Go projects are out of scope. Dokima is Python-first.
    - ❌ Verifying create=False mocks — those are intentional stubs for test isolation, not bugs.
    - ❌ Cross-referencing function behavior — we don't check that the function does what the test expects, only that it exists.
    - ❌ Modifying coder behavior — this is a vet-phase gate, not a coder-phase guardrail. The coder can still produce bad mocks; the vet catches them.
    - ❌ Any changes to nm, TL, or strategist phases.
    - ❌ Any new external dependencies — stdlib only.
    
    Sign-Off Checklist
    
    - [ ] Read and understood the bug pattern (F032-F038 shipped with mock-hidden missing implementations)
    - [ ] Approved the create_flag=True filter (don't flag legitimate create=False mocks)
    - [ ] Approved the retry model (coder gets one chance to implement the missing function, same as test-failure retry)
    - [ ] Confirmed scripts/vet backward compatibility (existing calls without --verify-code unchanged)
    - [ ] Reviewed Task 6 test cases — all 10 cases cover the right behaviors
    - [ ] Approved the Parallelization plan (Wave 1: 3 parallel tasks, Wave 2: integration, Wave 3: tests)
    - [ ] Confirmed zero new dependencies
    - [ ] Confirmed create=True is the only mock pattern that can hide missing implementations (autospec=True on a non-existent target also raises, but create=True suppresses it)
    - [ ] Approved exit code 2 for "real code missing" in standalone script (distinct from exit 1 "test failure")
    - [ ] Reviewed Risk R5 — coder can waste a retry cycle. Accept or reject the retry model.