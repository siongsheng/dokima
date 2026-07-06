# Task Breakdown: F039: Real-code verification in vet phase — after tests pass, verify that functions referenced in tests actually exist in source modules. Mock-based tests (autospec=True, create=True) can pass even when the real implementation is missing (F032, F033, F034, F038 all shipped with this bug). The vet phase should grep test files for function names and verify they're importable from the source modules. Blocks pipeline if tests pass but implementation is missing.

### Task 1: _verify_real_code() helper (utils.py)     ← coder A
**Files:** from spec
**Dependencies:** [none]
**Description:** _verify_real_code() helper (utils.py)     ← coder A

### Task 2: _parse_test_references() (utils.py)       ← coder B
**Files:** from spec
**Dependencies:** [none]
**Description:** _parse_test_references() (utils.py)       ← coder B

### Task 3: pipeline.py integration gate              ← coder A (needs Task 1 + 2)
**Files:** from spec
**Dependencies:** [none]
**Description:** pipeline.py integration gate              ← coder A (needs Task 1 + 2)

### Task 4: scripts/vet --verify-code flag            ← coder C
**Files:** from spec
**Dependencies:** [none]
**Description:** scripts/vet --verify-code flag            ← coder C

### Task 5: scripts/verify_imports.py standalone      ← coder C
**Files:** from spec
**Dependencies:** [none]
**Description:** scripts/verify_imports.py standalone      ← coder C

### Task 6: test_f039_real_code.py                    ← coder B (needs all implementation)
**Files:** from spec
**Dependencies:** [none]
**Description:** test_f039_real_code.py                    ← coder B (needs all implementation)
