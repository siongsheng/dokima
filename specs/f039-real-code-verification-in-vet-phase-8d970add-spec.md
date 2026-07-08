# F039: Real-code verification in vet phase — after tests pass, verify that functions referenced in tests actually exist in source modules. Mock-based tests (autospec=True, create=True) can pass even when the real implementation is missing (F032, F033, F034, F038 all shipped with this bug). The vet phase should grep test files for function names and verify they're importable from the source modules. Blocks pipeline if tests pass but implementation is missing.

Now I have complete understanding of the codebase and the current state of F039. Let me produce the corrected spec.
    
    
    
    markdown
    F039: Real-Code Verification in Vet Phase
    
    Status: In Progress
    Confidence: High
    Priority: P0
    Dependencies: None (core _verify_test_imports_exist is on main at f525e57; enhancements and tests are on feat/f039-real-code-verification-in-vet-phase-8d970add and need merge)
    
    
    
    Executive Summary
    
    Mock-based tests with autospec=True or create=True can pass even when the real implementation is missing — a bug that shipped in F032, F033, F034, and F038. The vet phase already has partial mitigation (_verify_test_imports_exist merged at f525e57 does basic from X import Y checks against 7 hardcoded modules). The feature branch (feat/f039-real-code-verification-in-vet-phase-8d970add) has 7 follow-on commits (not merged) adding auto-discovery of source modules, mock.patch/@patch string-reference detection, deduplication, and comprehensive tests. This spec drives merging those enhancements and filling remaining gaps.
    
    Confidence: High — the feature branch code exists, tests exist on branch, the gap is merge + integration + fill.
    
    
    
    Impact
    
    File: pipeline.py
    Change: _verify_test_imports_exist() — replace hardcoded module list with
      auto-discovery; add mock.patch/@patch string detection; add
      deduplication
    LOC: ~+60 / -20
    ────────────────────────────────────────
    File: tests/test_f039_real_code_verification.py
    Change: Merge from feature branch; add edge cases (dynamic imports,
      create=True mocks, stdlib imports)
    LOC: ~+80
    ────────────────────────────────────────
    File: specs/roadmap.md
    Change: Mark F039 Done
    LOC: ~+0 / -0 (status change)
    ────────────────────────────────────────
    File: AGENTS.md
    Change: Update test count if needed
    LOC: ~0
    
    Downstream impact: F045 (roadmap auto-update verification) depends on F039 being complete. F047 (thermo-nuclear TL) depends on F039 + F044. No module outside of pipeline.py is affected.
    
    
    
    What Changed (from f525e57 to planned merge)
    
    Enhancement: Auto-discover source modules
    Commit: b2447d1
    Description: Replace hardcoded ["pipeline", "utils", ...] with dynamic
      discovery of all .py files in project root (excluding init.py, test_*)
    ────────────────────────────────────────
    Enhancement: Mock string-reference detection
    Commit: 1ae9074
    Description: @patch('module.func') decorators and patch('module.func')
      calls reference functions by string — these were missed by the original
      AST-only ImportFrom check
    ────────────────────────────────────────
    Enhancement: Mock pattern coverage extension
    Commit: 7c10037
    Description: Also catch Mock(spec=module.Class) and
      create_autospec(module.Class) patterns
    ────────────────────────────────────────
    Enhancement: Deduplication
    Commit: 8b8347e
    Description: When a function is referenced via BOTH a decorator and an
      ImportFrom node, report it only once
    ────────────────────────────────────────
    Enhancement: Unit tests
    Commit: b1144f1, 5190bea
    Description: test_f039_real_code_verification.py with temp_project
      fixture, test for missing functions, test for existing functions, test
      for @patch detection
    ────────────────────────────────────────
    Enhancement: Integration tests
    Commit: fc7fddc, 1d95041
    Description: vet --verify-code CLI integration tests, verify_imports.py
      standalone script tests
    
    
    
    Feature Breakdown
    
    Task 1: Merge F039 branch enhancements and rebase
    Files: pipeline.py
    Dependencies: None
    Parallelizable: No
    Description: Cherry-pick or merge the 7 enhancement commits from feat/f039-real-code-verification-in-vet-phase-8d970add (b2447d1, 1ae9074, 7c10037, 8b8347e) onto current main. Resolve any conflicts with F041 utils split (utils.py refactored, but _verify_test_imports_exist lives in pipeline.py — low conflict risk). Verify the function still compiles: python3 -m py_compile pipeline.py.
    
    Task 2: Merge and extend test file
    Files: tests/test_f039_real_code_verification.py
    Dependencies: Task 1
    Parallelizable: No (needs merged code to test against)
    Description: Merge test commits (b1144f1, 5190bea) from feature branch. Extend the temp_project fixture to include edge cases:
    - Dynamic import: mod = importlib.import_module('utils'); mod.slugify(...) — should NOT false-positive
    - create=True mock: mocker.patch('pipeline.run_pipeline', create=True) — should be caught when run_pipeline doesn't exist
    - Stdlib import: from os import path — should NOT flag (stdlib modules are excluded)
    - Function defined in the test file itself: def helper(): pass then referenced — should NOT flag
    
    Task 3: Add the missing verify_source_function_exists unit tests
    Files: tests/test_f039_real_code_verification.py
    Dependencies: Task 2
    Parallelizable: No
    Description: Merge commit 5190bea — adds test_verify_source_function_exists_module_not_found, test_verify_source_function_exists_attr_not_found, test_verify_source_function_exists_found. These test the internal _verify_source_function_exists helper directly with mocked importlib.
    
    Task 4: Run full test suite and fix any regressions
    Files: All changed files
    Dependencies: Task 3
    Parallelizable: No
    Description: Run python3 -m pytest tests/ -q — ensure all 1029+ tests pass. Run the new F039 tests specifically: python3 -m pytest tests/test_f039_real_code_verification.py -v. If F041 utils split caused import conflicts, fix them.
    
    Task 5: Integration verification — run vet against known-missing scenario
    Files: pipeline.py
    Dependencies: Task 4
    Parallelizable: No
    Description: Manual verification: create a test file with from pipeline import nonexistent_func and no nonexistent_func in pipeline.py. Run the vet phase and confirm it BLOCKS with "tests pass but implementation is missing". Then add the function and confirm it passes. This is a manual integration smoke test — not automated (the full pipeline needs a live Hermes agent).
    
    Task 6: Mark F039 Done in roadmap
    Files: specs/roadmap.md
    Dependencies: Task 5
    Parallelizable: No
    Description: Update F039 status from [~] In Progress to [x] Done. Run python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" to verify the entry script still compiles.
    
    
    
    Data Model
    
    No new persistent data. _verify_test_imports_exist(project_dir) is a pure function:
    - Input: project_dir (str) — absolute path to project root
    - Output: list[str] — each element is "module.function: test_file:line_number"
    - Empty list means all verified functions exist
    - Side effects: None (reads source and test files, does not write)
    
    Internal data structures:
    python
    source_names: dict[str, set[str]]  # module_name -> {exported names}
    Auto-discovered: all .py files in project root not starting with test_ or __
    
    
    
    
    API / Interface
    
    _verify_test_imports_exist(project_dir: str) -> list[str] is called at pipeline.py:1175:
    python
    In run_phase3_vet, after tests pass:
    if test_pass:
        missing = _verify_test_imports_exist(PROJECT_DIR)
        if missing:
            # BLOCK pipeline — halt_and_revert
    
    
    No new CLI flags. No env vars. No config changes. The check is automatic in vet phase whenever tests pass.
    
    
    
    Security
    
    No security impact. This is a read-only verification function that:
    - Reads .py files from the project directory (already trusted — it's the repo being built)
    - Uses importlib.util to load modules (same trust boundary as running the tests themselves)
    - Does not execute any imported code beyond exec_module (same as what happens when tests run anyway)
    - No network access, no credential exposure, no subprocess calls
    
    
    
    Test Plan (MANDATORY)
    
    Happy path
    - Test file imports from pipeline import run_pipeline → run_pipeline exists in pipeline.py → empty list returned
    - Test file uses @patch('agent.call_agent') → call_agent exists in agent.py → empty list returned
    
    Edge cases
    - Empty tests/ directory: No test files → returns [] (no false positives)
    - No tests/ directory: os.path.isdir(tests_dir) is False → returns []
    - Import of private function: from pipeline import _internal → _internal exists → should be checked (private functions can be tested)
    - Import from stdlib: from os import path → os is not in source_names → should be SKIPPED (not flagged as missing)
    - Function defined in test file: def helper(): pass then from conftest import helper → helper is defined locally → should NOT be flagged
    - Dynamic import: mod = importlib.import_module('utils') → not an ImportFrom AST node → skipped (not a false positive — we can't statically trace dynamics)
    - create=True mock: mocker.patch('pipeline.nonexistent', create=True) → nonexistent not in pipeline.py → should be flagged
    - autospec=True on nonexistent: mocker.patch.object(SomeClass, 'missing_method', autospec=True) → not a string reference trap — this is a different pattern; verify it's caught or documented as out of scope
    - Mock(spec=module.Class): String reference via spec= parameter → check that module.Class exists
    - Duplicate references: Same function referenced via both @patch decorator AND from X import Y → should appear only once in missing list
    
    Failure modes
    - Source module fails to load: importlib.util raises Exception → module is silently excluded from source_names (pipeline should NOT crash)
    - Test file is unparseable: ast.parse raises SyntaxError → file is silently skipped
    - Circular imports in source: Module loads but some names are missing → they'll be flagged as missing (correct behavior — they're not importable)
    - Project dir is read-only: open(fpath) for test files fails → silently skipped
    
    Contract invariants
    - _verify_test_imports_exist MUST NOT modify any files
    - _verify_test_imports_exist MUST NOT raise exceptions (all exceptions caught internally)
    - Return type is ALWAYS list[str] (never None, never raises)
    - The function MUST be called ONLY when test_pass is True (it's a secondary gate, not a replacement for test failures)
    
    
    
    Risk Register
    
    #: R1
    Risk: Merge conflict with F041 utils split
    Severity: Medium
    Mitigation: _verify_test_imports_exist lives in pipeline.py, not utils.py
      — low chance of conflict. If conflict, manually resolve.
    Trigger: Merge attempt fails
    ────────────────────────────────────────
    #: R2
    Risk: importlib.util.exec_module executes top-level code with side effects
    Severity: Medium
    Mitigation: This is the same risk as running the tests themselves. Only
      run inside the project being tested — same trust boundary.
    Trigger: Module with os.system('rm -rf /') at top level
    ────────────────────────────────────────
    #: R3
    Risk: Auto-discovery picks up non-module .py files
    Severity: Low
    Mitigation: Filter: exclude test_*, init.py, and files in subdirectories.
      Only root-level .py files.
    Trigger: A setup.py or conftest.py gets included
    ────────────────────────────────────────
    #: R4
    Risk: False positives: function exists but as a dynamically-added
      attribute
    Severity: Low
    Mitigation: Document as known limitation. _verify_test_imports_exist
      checks dir(module) at load time — runtime-added attributes are
      invisible.
    Trigger: Code uses setattr(module, 'func', ...)
    ────────────────────────────────────────
    #: R5
    Risk: mock.patch string detection false positive on non-function strings
    Severity: Low
    Mitigation: @patch('database.connect') — database module might not be in
      source_names set. We only check modules we've loaded.
    Trigger: Third-party module strings in @patch
    ────────────────────────────────────────
    #: R6
    Risk: Pipeline blocks on legitimate test patterns
    Severity: Medium
    Mitigation: The function runs AFTER tests pass, so false positives block
      valid features. Downstream impact: developer frustration. Mitigation:
      clear error message with exact file:line references so developer can
      fix.
    Trigger: A false positive blocks the pipeline
    
    
    
    Anti-Creep
    
    NOT in scope:
    - No runtime tracing — we statically analyze imports only. Dynamic importlib.import_module() calls are out of scope.
    - No autospec=True on class attributes — mocker.patch.object(SomeClass, 'method', autospec=True) is a different pattern; the class exists, the issue is the method. Out of scope for F039.
    - No cross-package verification — only project-root .py modules are checked. Third-party packages are assumed correct.
    - No fix automation — F039 only BLOCKS. It does not auto-fix the missing implementation.
    - No test quality assessment — F039 checks existence, not correctness. A function could exist but be a stub.
    
    
    
    Sign-Off Checklist
    
    - [ ] All 7 enhancement commits from F039 branch successfully merged and compile
    - [ ] test_f039_real_code_verification.py merged and extended with edge cases
    - [ ] Full test suite passes: python3 -m pytest tests/ -q (1029+ tests)
    - [ ] F039-specific tests pass: python3 -m pytest tests/test_f039_real_code_verification.py -v
    - [ ] Manual smoke test: missing function causes pipeline BLOCK
    - [ ] Manual smoke test: all functions present allows pipeline to proceed
    - [ ] No regression in existing vet phase behavior
    - [ ] Roadmap updated: F039 → [x] Done
    - [ ] Any new conventions discovered during implementation added to specs/conventions.md
    - [ ] Feature branch deleted after merge
    
    
    
    
    The spec above has all required sections, properly formatted ### Task N: headers with Files:, Dependencies:, Parallelizable:, and Description: fields, plus the missing Impact and What Changed sections. The test plan includes specific edge cases and failure modes. Confidence is High — the implementation exists on the feature branch and just needs merge + test extension.