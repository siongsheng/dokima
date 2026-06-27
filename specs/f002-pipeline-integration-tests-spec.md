# F002: Pipeline Integration Tests

Now I have a thorough understanding of the project. Let me produce the complete F002 spec with properly formatted task headers.
    
    
    
    Feature: F002: Pipeline Integration Tests  
    Project: /home/opc/dokima  
    Date: 2026-06-28  
    Status: Pending  
    Confidence: High
    
    DECISION TABLE
    
    SINGLE APPROACH: Expand integration test coverage in tests/test_main_integration.py using the existing _patch_and_run / _setup_test_project patterns — no new test infrastructure needed. The testing approach (exec-loaded module via conftest._load_panel, mock-based agent spawning, tmpdir-based project fixtures) is already battle-tested by the 30 existing test files (307 collected tests).
    
    Impact
    
    Developers get a single command (python3 -m pytest tests/test_main_integration.py -v) that verifies the full 5-phase pipeline against a mock test repo — end-to-end correctness gates that catch regressions before they reach main.
    
    What Changed
    
    - tests/test_main_integration.py: Adds 12-15 integration tests covering all 5 pipeline phases, phase transitions, and failure modes. Existing 4 tests preserved.
    - No changes to dokima required — all mocking is test-side via unittest.mock.patch.
    
    Confidence
    
    Confidence: High — the mocking infrastructure (_patch_and_run, _setup_test_project, spawn_agent override) already works and is validated by the existing 4 integration tests (test_strategist_called, test_stop_file_exits_before_pipeline, test_lock_held_and_released, test_coder_failure_not_marked_done). The feature is pure test expansion, zero production code changes.
    
    Impact Markers
    
    Impact: HIGH — F002 is the gatekeeper for all future pipeline changes. Without end-to-end integration tests, regressions in pipeline orchestration logic (phase transitions, depth gating, verdict propagation, retry loops) are invisible until production failures.
    
    API/Interface Proposal
    
    N/A — test-only change. No API, route, or data structure modifications.
    
    Security Considerations
    
    N/A — no attack surface change. Tests run with mocked agent spawning (no real Hermes sessions), mocked git/GitHub operations (no real remote pushes), and temporary directories (no filesystem pollution).
    
    Documentation Impact
    
    README: No change needed. Test execution commands in AGENTS.md already document python3 -m pytest tests/ -q.
    
    
    
    TASK BREAKDOWN
    
    Task 1: Phase 1 — Strategist produces valid spec and exits interview mode
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that the strategist phase produces a spec file with required sections (Executive Summary, Task Breakdown with ### Task N: headers, Decision Table) and handles interview mode gracefully — when strategist output contains CLARIFICATION markers, the panel exits with exit code 2 without proceeding to Phase 2.
    
    Task 2: Phase 1 — Strategist respects existing authoritative spec
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that when a spec already exists at specs/<slug>-spec.md, the strategist validates and enhances it rather than rewriting from scratch — verify the spec is read first and the strategist prompt includes the CRITICAL refinement instruction block.
    
    Task 3: Phase 2 — Coder produces RED commit then GREEN commit
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that the coder phase produces two commits on the feature branch — a RED commit (test: prefix) followed by a GREEN commit (feat: prefix) — and that the coder prompt includes TDD enforcement instructions from the ai-coding-best-practices-lite skill.
    
    Task 4: Phase 2 — Coder respects anti-creep rules (no unauthorized file changes)
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that the coder prompt includes CRITICAL RULES forbidding deletion of files not in task scope, unauthorized spec archival, and drive-by refactoring — verify by inspecting the prompt text sent to spawn_agent with profile='coder'.
    
    Task 5: Phase 3 — vet runs build and tests on coder branch
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that vet checks out the feature branch, runs the BUILD_CMD and TEST_CMD from AGENTS.md, and reports pass/fail with actual test counts — verify build_pass and test_pass booleans are set from real command output (not mocked to always pass).
    
    Task 6: Phase 3 — vet retries coder on verification failure (up to 2 retries)
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that when vet's first verification run fails (test or build non-zero exit), it spawns a coder fix attempt and re-runs verification — verify exactly 2 retries before VET_FAILED verdict and halt_and_revert is called on the 3rd failure.
    
    Task 7: Phase 3 — Branch checkout failure triggers halt_and_revert
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that when git checkout <branch> fails, vet immediately returns VET_FAILED verdict without attempting test/build execution — verify halt_and_revert is called with the correct phase label 'PHASE 3 (vet)'.
    
    Task 8: Phase 4 — nm performs adversarial review with different model family
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that the nm phase is spawned with the no-mistakes skill and a model from a different family than the coder — verify the nm invocation matches the expected profile/skill pattern and produces a review verdict (PASS/NEEDS_FIX/BLOCKED).
    
    Task 9: Phase 5 — Tech Lead checks spec compliance and architecture
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that the TL phase receives the spec_path, branch, and nm output as inputs, produces a verdict (APPROVE/NEEDS_FIX/BLOCKED), and checks for architecture drift against existing ADRs — verify TL prompt includes ADR reference and spec compliance instructions.
    
    Task 10: End-to-end — All 5 phases execute in correct order
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Full pipeline smoke test: run --next on a test project with a valid roadmap, verify spawn_agent is called in exact order (strategist → coder → vet → nm → TL), each phase receives output from the previous phase, and the pipeline completes without halt_and_revert.
    
    Task 11: End-to-end — Depth gating skips nm+TL for LOW-impact changes
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that when the strategist outputs Confidence: High + Impact: LOW, the pipeline runs only Phases 1-3 (strategist → coder → vet) and skips nm+TL — verify spawn_agent is NOT called with profile='nm' or profile='tech-lead'.
    
    Task 12: Failure mode — Coder timeout produces partial results (no crash)
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that when spawn_agent with profile='coder' raises TimeoutError or returns empty output, the panel captures partial results (whatever stdout was collected) and does not crash — verify that the pipeline proceeds to vet with available data or halts gracefully.
    
    Task 13: Failure mode — Strategist DAG re-prompt fires on missing ### Task N: headers
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that when strategist output contains zero ### Task N: headers (after extract_agent_messages filtering), the DAG re-prompt fires — a second strategist call is made with the DAG format enforcement prompt — and if the second output also fails, the panel warns and proceeds in degraded sequential mode.
    
    Task 14: Failure mode — Concurrent pipeline lock prevents duplicate runs
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that when the advisory lock file exists for the project, a second pipeline invocation exits early with a clear message — verify acquire_lock returns False and main() exits without spawning any agents.
    
    Task 15: Cleanup — Stop file and signal handling terminate gracefully
    Files: tests/test_main_integration.py
    Dependencies: none
    Parallelizable: yes
    Description: Test that (a) writing to the stop file path halts the pipeline loop before Phase 1 and removes the stop file, (b) SIGTERM/SIGINT triggers lock cleanup via the signal handler, and (c) stale worktrees from crashed runs are detected and removed on next startup.
    
    
    
    Risk Register
    
    Risk: Mocked agent output diverges from real Hermes behavior
    Severity: MEDIUM
    Mitigation: All tests use mock-based spawn_agent — the mock's return
      format must match real Hermes stdout. Keep mock output realistic (same
      JSON keys, same markdown structure).
    Trigger: Real pipeline run fails but tests pass
    ────────────────────────────────────────
    Risk: Test pollution: exec-loaded module globals leak across tests
    Severity: LOW
    Mitigation: conftest._reload_panel() provides fresh module between tests.
      Use it. Existing 307 tests already handle this correctly.
    Trigger: Intermittent test failures in CI
    ────────────────────────────────────────
    Risk: Integration tests depend on specific regex patterns that drift
    Severity: MEDIUM
    Mitigation: Use the SAME regex patterns as the production code (imported
      from dokima module after exec-load). Never duplicate regex in tests.
    Trigger: Panel regex changes break tests silently
    ────────────────────────────────────────
    Risk: Test file grows too large (12-15 new tests at ~30 lines each = ~450
      lines)
    Severity: LOW
    Mitigation: Keep tests focused — one assertion class per test. If file
      exceeds 600 lines, split into test_main_integration_strategist.py,
      test_main_integration_coder.py, etc.
    Trigger: test_main_integration.py > 600 lines
    ────────────────────────────────────────
    Risk: Mocked git/gh operations mask real CLI failures
    Severity: LOW
    Mitigation: Use real git init/setup in _setup_test_project for repo
      creation, only mock destructive operations (push, PR create). This
      mirrors existing pattern.
    Trigger: Tests pass but gh CLI breaking change undetected
    
    
    
    Anti-Creep
    
    - NOT in scope: Testing real Hermes Agent invocations (requires API keys, network, profiles — these are end-to-end acceptance tests, not unit-level integration tests).
    - NOT in scope: Testing the --continuous loop (F019/F020 territory — continuous mode has known bugs in continue_loop propagation).
    - NOT in scope: Testing parallel coder worktree isolation (F010 territory — worktree concurrency is a separate feature with its own test needs).
    - NOT in scope: Testing model fallback logic (F005 territory — provider-specific fallback chains).
    - NOT in scope: Performance benchmarks or cost tracking — pipeline correctness only, not pipeline efficiency.
    - NOT in scope: Modifying dokima to make it more testable. If a function is untestable without refactoring, skip the test and document the gap in a comment. F002 is test-expansion, not pipeline-refactoring.
    
    
    
    Sign-Off Checklist
    
    - [ ] All 15 tasks have ### Task N: headers with all 5 required fields (Files, Dependencies, Parallelizable, Description)
    - [ ] Existing 4 integration tests in test_main_integration.py preserved and still pass
    - [ ] New tests use _setup_test_project() + _patch_and_run() pattern (no new test infrastructure)
    - [ ] Mocked agent output matches real Hermes Agent response format (JSON with content/tokens keys)
    - [ ] No test duplicates an existing test in test_root_cause_regressions.py (check overlap before writing)
    - [ ] Depth gating test (Task 11) verifies nm+TL are skipped, not just that spawn count is lower
    - [ ] DAG re-prompt test (Task 13) uses extract_agent_messages() to strip thinking blocks before counting headers
    - [ ] All tests use _reload_panel() between tests to prevent global state pollution (or rely on conftest.panel fixture which is fresh per test)
    - [ ] Test file remains under 700 lines (manageability threshold)
    - [ ] All 307 existing tests still pass after F002 changes (python3 -m pytest tests/ -q)
    - [ ] Test descriptions are specific enough for the coder to implement without guessing mock behavior