# F002: Pipeline Integration Tests

Now I have the full picture. F002 is marked [x] Done in roadmap but 6 tests remain skipped — the root-cause fixes (module-level select, PANEL_NO_LOCK, PANEL_MAX_RETRIES short-circuit) were never implemented. The spec below captures what remains.
    
    
    
    Position: F002 is marked Done but incomplete — 6 tests remain skipped because the three root-cause fixes (module-level select, PANEL_NO_LOCK env var, retry short-circuit) were deferred. This spec is the minimal completion: 7 tasks, ~200 LOC, 3 code changes + 4 test changes. Confidence: High.
    
    Ponytail Guard — Pre-Spec Review
    Feature: F002: Pipeline Integration Tests
    Rung: 7 — Minimum that works
    Existing solution: 331 collected tests, 4 active integration tests, 2 skipped integration tests, 4 skipped edge-case/coverage tests. Root causes identified but unfixed.
    Spec needed: yes
    Spec scope: (a) Move select to module level, (b) Add PANEL_NO_LOCK=1 to bypass flock, (c) Ensure PANEL_MAX_RETRIES=0 short-circuits all retry paths, (d) Unskip 5 blocked tests, (e) Add pipeline integration test file, (f) Validate full suite.
    
    
    
    F002: Pipeline Integration Tests
    
    Status: [~] In Progress
    Priority: P0
    Dependencies: None
    Confidence: High
    Impact: HIGH
    
    Decision Table
    
    SINGLE APPROACH: Fix three root causes that block all 5 skipped tests (local select import, hardwired flock, retry loops) with minimal code injections — env-var gates rather than class extraction. Then add a single new test file verifying pipeline phases with mocked dependencies. No Orchestrator class needed. No new fixtures beyond those in conftest.py.
    
    Impact
    
    python3 -m pytest tests/ -q passes 300+ tests with only 1 intentional skip (bash -lc fallback removed). Pipeline correctness — from strategist DAG extraction through TL verdict parsing — is verified on every commit.
    
    What Changed
    
    - dokima: Move select from local imports (lines 3071, 3880) to module level. Extract _read_stdin_with_timeout() helper. Add PANEL_NO_LOCK=1 gate in acquire_lock(). Ensure PANEL_MAX_RETRIES=0 propagates to coder retry and post-pipeline retry paths.
    - tests/test_pipeline_integration.py (NEW): Phase verification — strategist DAG extraction → coder commit verification → verdict parsing (vet/nm/TL). All external spawn_agent mocked.
    - tests/test_edge_cases.py: Unskip test_clarification_triggers_questions and test_human_gate_reject.
    - tests/test_final_coverage.py: Unskip test_interview_mode_triggers_clarification.
    - tests/test_main_integration.py: Unskip test_lock_held_and_released and test_coder_failure_not_marked_done.
    - specs/roadmap.md: Verify F002 [x] Done.
    - specs/STATUS.md: Add F002 completion entry with test counts.
    
    API/Interface Proposal
    
    N/A — internal refactor only. No CLI changes. PANEL_NO_LOCK and PANEL_MAX_RETRIES are existing conventions extended to coverage gaps.
    
    Security Considerations
    
    PANEL_NO_LOCK=1 skips flock entirely. Test-only flag — no attack surface in production. Document as test-only in AGENTS.md env vars section. No shell injection, no credential exposure.
    
    Documentation Impact
    
    AGENTS.md: Add PANEL_NO_LOCK=1 to env vars section. README: No change needed.
    
    
    
    Task 1: Move select import to module level
    Files: dokima
    Dependencies: [none]
    Parallelizable: yes
    Description: Move import select from two local sites (lines 3071 and 3880 inside main() clarification loops) to the module-level imports near line 65 with other stdlib imports, making select patchable via unittest.mock.patch and unblocking 2 skipped tests that mock stdin behavior.
    
    Task 2: Extract _read_stdin_with_timeout() helper function
    Files: dokima
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Extract the select.select([sys.stdin], [], [], timeout) + sys.stdin.readline() pattern into a standalone _read_stdin_with_timeout(prompt="", timeout=60, stdin=None) function accepting an optional stdin parameter for test injection, replacing two inline 6-line blocks in main() with single calls.
    
    Task 3: Add PANEL_NO_LOCK env var to bypass flock in acquire_lock()
    Files: dokima
    Dependencies: [none]
    Parallelizable: yes
    Description: Add a check at the top of acquire_lock() at line 654: if os.environ.get("PANEL_NO_LOCK") == "1", return (True, None) immediately without calling flock(), unblocking test_lock_held_and_released which needs to test real inner lock behavior without the outer main() lock.
    
    Task 4: Ensure PANEL_MAX_RETRIES=0 short-circuits all retry paths
    Files: dokima
    Dependencies: [none]
    Parallelizable: yes
    Description: Audit the coder failure path in run_pipeline() and the post-pipeline retry logic in run_post_pipeline() to ensure PANEL_MAX_RETRIES=0 causes immediate return of CODER_FAILED verdict without entering retry/backoff loops, unblocking test_coder_failure_not_marked_done which hangs on retry.
    
    Task 5: Unskip 5 blocked existing tests
    Files: tests/test_edge_cases.py, tests/test_final_coverage.py, tests/test_main_integration.py
    Dependencies: [Task 1, Task 2, Task 3, Task 4]
    Parallelizable: yes
    Description: Remove @pytest.mark.skip decorators from all 5 tests blocked by the three root causes (local select import, hardwired flock, retry loops): test_clarification_triggers_questions, test_human_gate_reject, test_interview_mode_triggers_clarification, test_lock_held_and_released, test_coder_failure_not_marked_done. Leave test_functions_unit.py:23 skip intact (intentional: bash -lc fallback removed).
    
    Task 6: Add pipeline integration test file with mocked external agents
    Files: tests/test_pipeline_integration.py
    Dependencies: [Task 1, Task 2, Task 3]
    Parallelizable: yes
    Description: Create tests/test_pipeline_integration.py with 3 test classes: (a) TestStrategistOutputParsing — mock strategist spawn returning valid DAG spec with ### Task N: headers, verify task extraction count and spec file creation, (b) TestVerdictExtraction — mock coder output with PASS/FAIL/CODER_FAILED patterns, verify run_pipeline() returns correct verdict string, (c) TestNmTLVerdict — mock nm returning APPROVED/BLOCKED verdicts, verify TL last-match extraction handles recent bug patterns. All external spawn_agent calls mocked. Max 200 LOC.
    
    Task 7: Run full suite, update roadmap, close F002
    Files: specs/roadmap.md, specs/STATUS.md
    Dependencies: [Task 5, Task 6]
    Parallelizable: no
    Description: Run python3 -m pytest tests/ -q --ignore=tests/test_main_integration.py and verify 0 failures, then run python3 -m pytest tests/ -q (full suite including integration) verifying 0 failures and at most 1 intentional skip. Verify specs/roadmap.md shows F002 [x] Done. Update specs/STATUS.md with F002 completion entry and final test counts. Commit: feat: F002 pipeline integration tests — 7 tasks, 5 unskipped tests, phase verification.
    
    
    
    Risk Register
    
    Risk: PANEL_NO_LOCK=1 accidentally enabled in production
    Severity: MEDIUM
    Mitigation: Name is explicitly negative (NO_LOCK). Documented as test-only
      in AGENTS.md.
    Trigger: User sets env var in shell profile
    ────────────────────────────────────────
    Risk: Retry short-circuit breaks legitimate retry in non-test mode
    Severity: LOW
    Mitigation: Only activates when PANEL_MAX_RETRIES=0 explicitly — default
      is 3.
    Trigger: User sets to 0 thinking it means "unlimited"
    ────────────────────────────────────────
    Risk: select import at module level changes import order
    Severity: LOW
    Mitigation: select is stdlib with no side effects. Move near other stdlib
      imports.
    Trigger: Circular import (impossible — stdlib)
    ────────────────────────────────────────
    Risk: New integration tests rely on git repo fixture — CI may not have git
    Severity: LOW
    Mitigation: test_main_integration.py already uses real git init. Same
      pattern.
    Trigger: CI runner without git binary
    
    Anti-Creep
    
    - NOT extracting an Orchestrator class — env-var injection is simpler and already the project convention (PANEL_SKIP_HUMAN_GATE, PANEL_MAX_RETRIES, PANEL_PARALLEL)
    - NOT creating new fixtures (test_repo, orchestrator) — existing panel + tmpdir fixtures + _setup_test_project helper are sufficient
    - NOT testing every edge case in the archived F002 spec (coder RED-only, nm model down, timeout handling) — F003 covers those
    - NOT modifying test_main.py (doesn't exist, not needed)
    - NOT touching test_functions_unit.py:23 intentional skip
    - NOT adding coverage targets — python3 -m pytest is the only metric
    
    Sign-Off Checklist
    
    - [ ] select import moved to module level — grep confirms no import select inside functions
    - [ ] _read_stdin_with_timeout() has stdin=None parameter — tests can inject StringIO
    - [ ] PANEL_NO_LOCK=1 bypasses acquire_lock() — second concurrent panel instance does not hang
    - [ ] PANEL_MAX_RETRIES=0 exits coder failure path in under 5 seconds
    - [ ] 5 previously-skipped tests now pass
    - [ ] test_pipeline_integration.py has at least 3 test classes covering strategist, coder verdicts, nm/TL verdicts
    - [ ] Full test suite: python3 -m pytest tests/ -q → 0 failures, at most 1 skip
    - [ ] specs/roadmap.md shows F002 [x] Done
    - [ ] specs/STATUS.md updated with F002 entry
    - [ ] PANEL_NO_LOCK documented in AGENTS.md env vars section