# F002: Pipeline Integration Tests

Now I have a complete understanding of the project. Let me run the ponytail guard pre-spec check, then produce the spec.
    
    Ponytail Guard — Pre-Spec Review
    Feature: F002: Pipeline Integration Tests
    Rung: 7 — The minimum that works. Test infrastructure exists (panel fixture, _patch_and_run, _setup_test_project), but end-to-end integration tests covering all 5 pipeline phases, depth gating, verdict propagation, and failure modes do NOT exist. The 7 existing tests in test_main_integration.py are thin smoke tests (agent ordering, stop file) — not pipeline-level verification.
    Existing solution: test_main_integration.py (192 lines, 4 active + 2 skipped + 1 pass), test_root_cause_regressions.py (539 lines, 27 unit-level regression tests for specific bugs). Neither exercises the full run_pipeline() orchestration through all 5 phases.
    Spec needed: yes
    Spec scope: Integration tests verifying pipeline orchestration — phase transitions, depth gating, verdict propagation, and graceful failure handling — all through the existing mock-based test infrastructure.
    
    
    
    F002: Pipeline Integration Tests
    
    Executive Summary: Add 6 integration tests to tests/test_main_integration.py that exercise the full 5-phase pipeline (run_pipeline() through run_post_pipeline()) using the existing mock infrastructure. Each test verifies a distinct pipeline behavior: phase ordering, depth gating, failure recovery, and verdict propagation. The test infrastructure (panel fixture, _patch_and_run, _setup_test_project) is battle-tested by 319 collected tests. Five root cause bugs discovered in the previous F002 run are already fixed and regression-tested in test_root_cause_regressions.py. Confidence: High.
    
    Constitution Check:
    - Solves user's own pain? YES — without integration tests, pipeline regressions are invisible until production failures.
    - Weekend-buildable? YES — 6 tests, ~300 LOC, one test file.
    - Evidence people will pay? N/A — internal quality gate.
    - Tech stack boring and proven? YES — pytest + unittest.mock, same patterns as 319 existing tests.
    - Avoids AI hype? YES — no AI features, pure test coverage.
    
    SINGLE APPROACH: Expand tests/test_main_integration.py using the existing _patch_and_run / _setup_test_project / panel fixture patterns. No new test infrastructure. No production code changes.
    
    Impact: Developers get python3 -m pytest tests/test_main_integration.py -v as a single-command pipeline correctness gate — catching phase-ordering, depth-gating, and verdict-propagation regressions before they reach main.
    
    What Changed:
    - tests/test_main_integration.py: Adds 6 integration tests in new TestFullPipeline and TestDepthGating classes. Existing 7 tests preserved.
    - No changes to dokima — all mocking is test-side.
    
    Confidence: High
    Impact: HIGH
    
    API/Interface Proposal: N/A — test-only change.
    
    Security Considerations: N/A — no attack surface change. Mocked agents, no real Hermes sessions.
    
    Documentation Impact: README: No change needed. Test command already documented in AGENTS.md.
    
    
    
    Test Plan
    
    Feature Area: Pipeline Phase Ordering
    - Happy path: run_pipeline() calls phases in order: strategist → coder → vet → nm → TL. spawn_agent receives correct profiles in correct sequence.
    - Edge cases: Depth=coder skips vet+nm+TL. Depth=vet+nm skips TL only. Coder failed skips all subsequent phases.
    - Failure modes: Strategist returns empty output → pipeline aborts before coder. Coder times out → vet still runs with partial data.
    - Contract invariants: spec_path is always created before coder starts. pr_url is non-None only after vet or nm creates PR. verdict is always a recognized string (APPROVED/BLOCKED/CHANGES_REQUESTED/CODER_FAILED/VET_FAILED/UNKNOWN).
    
    Feature Area: Depth Gating
    - Happy path: Confidence=High + Impact=LOW → depth=coder → only Phase 1+2 run.
    - Edge cases: Confidence=Low + Impact=HIGH → depth=full → all 5 phases run. Missing confidence/impact → depth defaults to full.
    - Failure modes: Depth matrix key missing → defaults to "full" (safe default).
    - Contract invariants: Depth is resolved BEFORE coder spawns. Phase skip messages are printed for each skipped phase.
    
    Feature Area: Verdict Propagation
    - Happy path: BLOCKED verdict from TL → run_post_pipeline sets continue_loop=False. APPROVED verdict → roadmap marked done.
    - Edge cases: CODER_FAILED → roadmap reverted to pending. VET_FAILED → roadmap reverted to pending. NM produces no PR URL → TL still runs with branch reference.
    - Failure modes: TL output has no VERDICT line → defaults to UNKNOWN. Two VERDICT lines (NM quoted + TL final) → last one wins.
    - Contract invariants: Only APPROVED verdict marks feature as done. FAILED/TIMED_OUT/UNKNOWN verdicts revert to pending.
    
    Feature Area: Failure Recovery
    - Happy path: Coder produces valid output → vet verifies and passes → pipeline continues.
    - Edge cases: Coder returns empty output → coder_failed=True. vet checkout fails → halt_and_revert called, VET_FAILED returned. nm script not found → pipeline continues with warning.
    - Failure modes: spawn_agent raises exception → captured, pipeline degrades gracefully. gh CLI unavailable → PR creation skipped, pipeline continues.
    - Contract invariants: Pipeline never crashes — all exceptions are caught and degrade gracefully. halt_and_revert() is only called for unrecoverable failures (checkout failure, all coders failed).
    
    
    
    Task Breakdown
    
    Task 1: Full pipeline — all 5 phases execute in correct order
    Files: tests/test_main_integration.py
    Dependencies: [none]
    Parallelizable: no
    Description: Mock strategist output to produce a full-depth spec (Confidence=High, Impact=HIGH, ### Task headers), then verify spawn_agent is called in exact order (strategist → coder → vet → nm → tech-lead), each phase receives output from the previous phase, and the pipeline completes with verdict propagation through run_post_pipeline.
    
    Task 2: Depth gating — LOW impact skips nm+TL
    Files: tests/test_main_integration.py
    Dependencies: [none]
    Parallelizable: no
    Description: Mock strategist output with Confidence=High + Impact=LOW, verify only phases 1-3 run (strategist → coder → vet), spawn_agent is NOT called with profile='nm' or 'tech-lead', and the pipeline exits with depth=vet verdict handling.
    
    Task 3: Strategist interview mode — exit code 2, no coder spawned
    Files: tests/test_main_integration.py
    Dependencies: [none]
    Parallelizable: no
    Description: Mock strategist output containing line-start CLARIFICATION markers (interview mode), verify the pipeline exits with code 2, spawn_agent is only called once (strategist only, no coder), and no spec file is created.
    
    Task 4: vet retry loop — coder fix on verification failure
    Files: tests/test_main_integration.py
    Dependencies: [none]
    Parallelizable: no
    Description: Mock coder to produce a branch, then mock vet's test run to fail on first attempt, verify a second coder call (fix attempt) fires, vet re-runs, and after 3 total failures (2 retries max) the VET_FAILED verdict is returned without calling nm or TL.
    
    Task 5: Coder failure — pipeline degrades gracefully, no crash
    Files: tests/test_main_integration.py
    Dependencies: [none]
    Parallelizable: no
    Description: Mock coder spawn_agent to return empty output (simulating timeout/crash), verify coder_failed=True is propagated, subsequent phases (vet, nm, TL) are skipped with clear messages, run_post_pipeline receives CODER_FAILED verdict, and the pipeline exits without throwing.
    
    Task 6: Verdict propagation — BLOCKED stops continuous loop
    Files: tests/test_main_integration.py
    Dependencies: [none]
    Parallelizable: no
    Description: Mock TL output with VERDICT: BLOCKED, verify run_post_pipeline sets continue_loop=False, roadmap feature is NOT marked as done, and the spec is NOT archived (only APPROVED triggers archival).
    
    
    
    Panel Split: All 6 tasks modify tests/test_main_integration.py — same file constraint forces sequential execution. 1 coder agent.
    
    Build & Deploy: N/A — test-only change. Run with python3 -m pytest tests/test_main_integration.py -v.
    
    Risk Register:
    Risk: Mocked output diverges from real Hermes format
    Severity: MEDIUM
    Mitigation: Use realistic mock output matching actual DeepSeek format
      observed in F002 run
    Trigger: Tests pass, real pipeline fails
    ────────────────────────────────────────
    Risk: Test pollution from exec-loaded module globals
    Severity: LOW
    Mitigation: conftest panel fixture is fresh per test
    Trigger: Intermittent failures
    ────────────────────────────────────────
    Risk: test_main_integration.py exceeds 600 lines
    Severity: LOW
    Mitigation: Split into separate files if needed (192 current + ~300 new =
      ~500)
    Trigger: File > 600 lines
    ────────────────────────────────────────
    Risk: Mocked git/gh mask real CLI breakage
    Severity: LOW
    Mitigation: Real git init in _setup_test_project, only destructive ops
      mocked
    Trigger: gh CLI update breaks undetected
    
    Anti-Creep:
    - NOT in scope: Testing real Hermes Agent invocations (needs API keys, network).
    - NOT in scope: Testing parallel coder worktree isolation (F010 territory).
    - NOT in scope: Testing model fallback logic (F005 territory).
    - NOT in scope: Testing --continuous loop (known bug in continue_loop propagation — F020).
    - NOT in scope: Modifying dokima to make it testable. If untestable, skip and document.
    - NOT in scope: Duplicating regression tests already in test_root_cause_regressions.py.
    
    Sign-Off Checklist:
    - [ ] All 6 tasks have ### Task N: headers with all 5 required fields
    - [ ] Existing 7 tests in test_main_integration.py preserved and still pass
    - [ ] New tests use _patch_and_run() + _setup_test_project() pattern (no new test infrastructure)
    - [ ] Mocked strategist output includes ### Task N: headers (not DeepSeek indented format — test the DAG parser's happy path)
    - [ ] Depth gating test (Task 2) verifies nm+TL are NOT called, not just lower spawn count
    - [ ] Interview mode test (Task 3) verifies exit code 2, not just early return
    - [ ] All tests use fresh panel fixture (conftest provides this automatically)
    - [ ] All 319 existing tests still pass after F002 changes
    - [ ] Test file stays under 600 lines