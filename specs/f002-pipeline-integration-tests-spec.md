# F002: Pipeline Integration Tests

All 7 bugs fixed and verified (45 regression tests pass). The F002 run's discovered bugs are resolved. The actual refactoring + integration tests remain undone.
    
    Here is the updated F002 spec:
    
    
    
    SINGLE APPROACH: Extract main() into an Orchestrator class with injectable I/O dependencies (stdin, lock, subprocess runner, gh CLI). The conftest already loads dokima via exec() with globals pre-set — build on that pattern. Write integration tests for all 5 pipeline phases using mock agents. No alternative approaches needed — this is the standard "humble object" refactoring.
    
    Impact: Every future Dokima change is verified against a real pipeline run. pytest proves all 5 phases work end-to-end with mock agents. The 45 existing regression tests provide the safety net for the refactoring.
    
    What Changed:
    - dokima: Extract Orchestrator class (~120 lines refactored, ~60 net new). main() becomes a thin shell: parse argv → construct Orchestrator with real deps → call .run(). Inject stdin, lock_fn, subprocess_run_fn, gh_cli_fn via constructor.
    - tests/conftest.py: Add test_repo fixture (minimal git repo with AGENTS.md) and mock_orchestrator fixture (Orchestrator with StringIO stdin, mock lock, mock subprocess, mock gh).
    - tests/test_pipeline_integration.py (NEW): Mock-agent integration tests for all 5 phases + DAG re-prompt + coder/nmd/TL failure paths.
    - tests/test_main.py (NEW): Flag parsing, lock behavior, stdin timeout, signal handling.
    
    Confidence: High
    Impact: MEDIUM — internal refactoring, no CLI change, no user-facing breakage.
    
    API/Interface Proposal: N/A — internal refactoring only. No CLI change. No new flags. No breaking changes. Orchestrator is not a public API.
    
    Security Considerations: N/A — no attack surface change. This is test infrastructure + internal refactoring.
    
    Documentation Impact: README: No change needed. specs/tech-stack.md: Add note that main() is now a thin shell over Orchestrator (for future contributors).
    
    
    
    Task 1: Extract _read_stdin_with_timeout() helper
    Files: dokima
    Dependencies: [none]
    Parallelizable: yes
    Description: Extract the select.select([sys.stdin], [], [], 60.0) + sys.stdin.readline() pattern (used at ~2 call sites) into a standalone _read_stdin_with_timeout(prompt="", timeout=60, stdin=None) function. Replace both inline call sites with this helper. Pure extraction — zero behavior change.
    
    Task 2: Create Orchestrator class with injectable dependencies
    Files: dokima
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Extract core pipeline dispatch from main() into an Orchestrator class. Constructor accepts: project_dir, feature, flags dict, stdin, lock_fn, safe_run_fn, gh_cli_fn. main() becomes: parse argv → detect repo → construct Orchestrator with real deps → call orchestrator.run(). Verify by running python3 dokima --help — output must be identical to pre-refactor.
    
    Task 3: Add test_repo and mock_orchestrator fixtures
    Files: tests/conftest.py
    Dependencies: [Task 2]
    Parallelizable: no
    Description: Add test_repo fixture: creates a temp git repo with AGENTS.md (test/build/lint commands), a .py source file, and a test file. Add mock_orchestrator fixture: constructs Orchestrator with StringIO stdin, mock lock (always succeeds), mock safe_run_fn returning pre-configured results keyed by command prefix, and mock gh_cli_fn returning pre-configured JSON. Tests configure responses via fixture parameters.
    
    Task 4: Phase 1-2 integration test — Strategist → Coder
    Files: tests/test_pipeline_integration.py
    Dependencies: [Task 3]
    Parallelizable: no
    Description: Test Orchestrator.run() with mock strategist returning a valid spec (DAG tasks). Verify: tasks extracted correctly, coder agent spawned (mocked), feature branch created, spec committed. Test interview mode: strategist returns exit code 2 with clarifications → orchestrator prompts stdin → re-prompts strategist with answers. Test DAG re-prompt: strategist returns no ### Task N: headers → re-prompt fires → corrected output accepted. All Hermes spawns mocked.
    
    Task 5: Phase 3-5 integration test — Vet → nm → TL
    Files: tests/test_pipeline_integration.py
    Dependencies: [Task 4]
    Parallelizable: no
    Description: Test pipeline continuation: vet phase (mock returns pass) → nm review (mock returns APPROVED) → TL verdict (mock returns APPROVED). Test BLOCKED path: TL returns BLOCKED → auto-fix loop triggers → fix applied → re-review passes. Test coder failure paths: timeout (partial results), zero commits (empty branch), only RED commits (vet catches). Test nm fallback: nm provider down → fallback model fires. All Hermes spawns mocked.
    
    Task 6: Flag parsing and CLI argument tests
    Files: tests/test_main.py
    Dependencies: [Task 2]
    Parallelizable: yes
    Description: Test main() parses all flag combos: --next, --continuous, --fix, --fix-all, --skip-autofix, --force-full, --skip-human-gate, --max-parallel=N, --interactive, --answers, --add, positional feature + dir. Verify correct global flags set, correct dispatch. Edge cases: --fix + --skip-autofix together, empty feature string, missing directory, --help output.
    
    Task 7: Lock, signal, and stdin edge case tests
    Files: tests/test_main.py
    Dependencies: [Task 3]
    Parallelizable: yes
    Description: Test lock acquisition: first call succeeds, second exits with code 2. Test stale lock removal (dead PID). Test SIGINT/SIGTERM handlers clean up worktrees and unlock. Test _read_stdin_with_timeout: returns input when available, empty on timeout, handles EOF. Test interview mode with mock stdin providing answers.
    
    Task 8: Final validation and F002 closure
    Files: specs/roadmap.md, specs/STATUS.md
    Dependencies: [Task 4, Task 5, Task 6, Task 7]
    Parallelizable: no
    Description: Run python3 -m pytest tests/ -q. Verify 0 failures across all tests including existing 45 regression tests + new integration tests. Update specs/roadmap.md: mark F002 [x] Done. Update specs/STATUS.md: add F002 entry with test counts. Commit with message: feat: F002 pipeline integration tests — Orchestrator refactor, 8 tasks, mock-agent pipeline tests.