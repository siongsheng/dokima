# Task Breakdown: F039: Real-code verification in vet phase — after tests pass, verify that functions referenced in tests actually exist in source modules. Mock-based tests (autospec=True, create=True) can pass even when the real implementation is missing (F032, F033, F034, F038 all shipped with this bug). The vet phase should grep test files for function names and verify they're importable from the source modules. Blocks pipeline if tests pass but implementation is missing.

### Task 1: Merge F039 branch enhancements and rebase
**Files:** pipeline.py
**Dependencies:** [none]
**Description:** Merge F039 branch enhancements and rebase

### Task 2: Merge and extend test file
**Files:** tests/test_f039_real_code_verification.py
**Dependencies:** 1
**Description:** Merge and extend test file

### Task 3: Add the missing verify_source_function_exists unit tests
**Files:** tests/test_f039_real_code_verification.py
**Dependencies:** 2
**Description:** Add the missing verify_source_function_exists unit tests

### Task 4: Run full test suite and fix any regressions
**Files:** All changed files
**Dependencies:** 3
**Description:** Run full test suite and fix any regressions

### Task 5: Integration verification — run vet against known-missing scenario
**Files:** pipeline.py
**Dependencies:** 4
**Description:** Integration verification — run vet against known-missing scenario

### Task 6: Mark F039 Done in roadmap
**Files:** specs/roadmap.md
**Dependencies:** 5
**Description:** Mark F039 Done in roadmap
