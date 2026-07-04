# F031: dokima init back-and-forth interview mode — strategist asks clarifying questions about users, goals, anti-goals, and constraints before producing constitution docs. Loops until confidence is High, then writes specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md.

Now I have full context. The F031 feature was previously implemented (PR #71), merged, then reverted. The original spec from git was complete. Let me produce the COMPLETE corrected spec with all required sections and proper ### Task N: headers.
    
    
    
    F031: dokima init back-and-forth interview mode
    
    Version: 1.1.0
    Status: Ready for implementation
    Confidence: High — implementation pattern proven in codebase, previously merged then reverted
    Feature ID: F031
    Roadmap priority: P2
    
    1. Executive Summary
    
    dokima init currently spawns the strategist once and accepts whatever constitution docs it produces — one-shot, no iteration. F031 adds a structured back-and-forth interview loop: the strategist asks clarifying questions about users, goals, anti-goals, and constraints. The loop repeats until confidence is High (max 3 rounds), then writes specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md. The interview loop infrastructure already exists in run_phase1_strategist() (pipeline.py lines 1598-1703) — this feature ports that proven pattern to run_init() in roadmap.py. Previously implemented in PR #71 (9 files, +1159/-17 LOC), reverted at v1.2.9.
    
    2. Constitution Check
    
    Axiom: Solves user pain?
    Status: Yes
    Notes: dokima init produces surface-level constitution docs without deep
      probing. Users get docs that don't reflect real needs.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: Yes
    Notes: Interview loop infrastructure already exists. Port + enhance, not
      greenfield.
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A
    Notes: Internal tooling improvement.
    ────────────────────────────────────────
    Axiom: Boring tech stack?
    Status: Yes
    Notes: Python 3.6+, same patterns as existing interview loop.
    ────────────────────────────────────────
    Axiom: Avoids AI hype?
    Status: Yes
    Notes: No "AI-powered" categorization — terminal loop + agent spawn.
    
    No constitutional violations.
    
    3. Ponytail Guard — Pre-Spec Review
    
    
    Feature: dokima init interview mode
    Rung: 5 — Installed dependency can do it (existing interview loop in pipeline.py)
    Existing solution: run_phase1_strategist() interview loop (pipeline.py:1598-1703) —
      same pattern: spawn, detect CLARIFICATION, collect answers, re-spawn.
      Port to run_init() + enhance for init-specific needs (max_rounds, --answers flag).
    Spec needed: Yes — the port + enhancement is ~130 LOC across roadmap.py, utils.py.
    Spec scope: Extract shared interview helpers, add interview loop to run_init(),
      enhance prompt, add --answers flag, max_turns restore on all exit paths.
    
    
    4. Decision Table
    
    Option: Port existing interview loop to run_init()
    Complexity: Medium
    Risk: Low — proven in pipeline
    Reuse: High
    Verdict: Accept
    ────────────────────────────────────────
    Option: Rewrite interview from scratch
    Complexity: High
    Risk: High — different bugs
    Reuse: Zero
    Verdict: Reject
    ────────────────────────────────────────
    Option: Skip interview, keep one-shot
    Complexity: Low
    Risk: High — bad constitution
    Reuse: N/A
    Verdict: Reject
    
    Approach: Port the interview loop from run_phase1_strategist() (pipeline.py:1598-1703) into run_init() (roadmap.py:559-820), adapting the save/interview/re-prompt pattern to the init context. Extract shared answer-collection logic into utils.py.
    
    5. Impact Assessment
    
    Affected files (grounded in prior implementation, PR #71):
    
    
    roadmap.py  (+131/-0)  — Interview loop, prompt enhancement, max_turns restore
    pipeline.py (+33/-17)  — Refactor to use shared collect_interview_answers()
    utils.py    (+50/-0)   — INTERVIEW_SAVE_PATH, has_init_interview_triggers(),
                             save_init_interview_state(), collect_interview_answers()
    tests/      (+718/-0)  — 5 new test files
    
    
    dokima init becomes a multi-turn conversation producing higher-quality constitution docs. Users who previously got generic output now get docs tailored to their specific project goals, anti-goals, and constraints. The interview loop dramatically reduces the "throwaway init" problem. Non-interactive usage (cron/Telegram) saves state and exits code 2 with clear re-run instructions.
    
    Dependency map: roadmap.py → pipeline.py → utils.py. pipeline.py changes are extract-then-refactor (same behavioral path). No new external dependencies.
    
    6. What Changed
    
    - roadmap.py run_init(): Added interview loop after strategist spawn — detect CLARIFICATION/INTERVIEW MODE in output using has_init_interview_triggers(), call collect_interview_answers() for interactive stdin collection (60s timeout per question), inject answers into re-spawn prompt. Loop until High confidence and no CLARIFICATION blocks, max 3 rounds. If non-interactive (no tty): save state via save_init_interview_state(), sys.exit(2) with instructions. Added --answers file loading in the init path to accept pre-filled answers.
    
    - roadmap.py init strategist prompt: Enhanced to explicitly instruct: "When confidence is NOT High, enter INTERVIEW MODE — output DECISION: INTERVIEW MODE followed by CLARIFICATION N: <question> blocks. Max 4 questions per round. When confidence IS High, write the full constitution docs without CLARIFICATION blocks."
    
    - roadmap.py max_turns restore: Moved config restore to a try/finally block so it fires on interview-mode exit(2) and timeout paths, not just the happy path.
    
    - utils.py: Added INTERVIEW_SAVE_PATH = "/tmp/dokima-init-interview.json", has_init_interview_triggers(text) -> bool (detects CLARIFICATION/INTERVIEW MODE line-start matches), save_init_interview_state(feature, project_dir, questions, prompt) -> str (persists interview JSON, chmod 0o600), collect_interview_answers(clarification_lines, timeout=60) -> list (extracted from pipeline.py).
    
    - pipeline.py run_phase1_strategist(): Replaced inline answer-collection code (lines 1660-1703) with call to utils.collect_interview_answers(). Zero behavioral change — same timeout, same tty check, same empty-input semantics.
    
    - tests/test_f031_init_interview.py: Happy-path interview loop, 3-round termination, non-interactive exit(2), --answers flag pre-fill, backward compatibility (one-shot preserved).
    - tests/test_f031_utils_helpers.py: Interview detection helpers — line-start CLARIFICATION trigger, non-trigger on prose mention, empty input.
    - tests/test_f031_collect_answers.py: Answer collection: tty path, non-tty fallback, empty clarifications, timeout returns partial.
    - tests/test_f031_pipeline_refactor.py: Pipeline refactored to use shared helper, behavior preserved.
    - tests/test_f031_init_loop.py: Loop structure tests: run_init has interview loop, max rounds guard, non-interactive exit.
    
    7. Feature Breakdown
    
    Task 1: Add interview detection helpers to utils.py
    Files: utils.py
    Dependencies: none
    Parallelizable: yes
    Description: Add INTERVIEW_SAVE_PATH = "/tmp/dokima-init-interview.json" constant, has_init_interview_triggers(text: str) -> bool that detects line-start CLARIFICATION N: or DECISION: INTERVIEW MODE patterns in strategist output, and save_init_interview_state(feature: str, project_dir: str, questions: list, prompt: str) -> str that writes interview JSON with chmod 0o600.
    
    Task 2: Extract interview answer loop into shared helper
    Files: utils.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Extract interactive answer-collection logic from pipeline.py run_phase1_strategist() (lines 1660-1703) into collect_interview_answers(clarification_lines: list, timeout: int = 60) -> list. Handles non-tty fallback (return empty list), select-based timeout per question, empty-input termination. Returns list of (question, answer) tuples.
    
    Task 3: Refactor pipeline.py to use shared interview helper
    Files: pipeline.py
    Dependencies: [Task 2]
    Parallelizable: yes
    Description: Replace inline answer-collection code in run_phase1_strategist() with call to utils.collect_interview_answers(). Verify zero behavioral change — same timeout (60s), same tty check via sys.stdin.isatty(), same empty-input semantics (accept assumptions).
    
    Task 4: Enhance init strategist prompt for interview mode
    Files: roadmap.py
    Dependencies: none
    Parallelizable: yes
    Description: Update the init strategist prompt text in run_init() to explicitly instruct: "When confidence is NOT High, enter INTERVIEW MODE — output DECISION: INTERVIEW MODE followed by CLARIFICATION N: <question> blocks. Max 4 questions per round. When confidence IS High, write the full constitution docs without CLARIFICATION blocks." Keep all existing PHASE 1-4 content intact.
    
    Task 5: Add interview loop to run_init() — core loop
    Files: roadmap.py
    Dependencies: [Task 2, Task 4]
    Parallelizable: no
    Description: After strategist spawn in run_init(), add interview detection using has_init_interview_triggers(). If detected AND stdin is tty: call collect_interview_answers(), inject answers into re-spawn prompt text. Loop until High confidence in output AND no CLARIFICATION blocks, max 3 rounds total (initial spawn + up to 2 re-spawns). If non-interactive (no tty): call save_init_interview_state(), print re-run instructions, sys.exit(2).
    
    Task 6: Add --answers flag support to init
    Files: roadmap.py, utils.py
    Dependencies: [Task 5]
    Parallelizable: no
    Description: Parse --answers <file> flag in the init subcommand path (dokima entry point). If provided, read interview JSON, extract answers, and prefill into strategist prompt. Use same pattern as user_answers_prefill in run_phase1_strategist(). Skip interactive interview when answers are pre-filled.
    
    Task 7: Add max_turns restore on all exit paths
    Files: roadmap.py
    Dependencies: [Task 5]
    Parallelizable: no
    Description: Move the existing max_turns bump+restore logic in run_init() into a try/finally block. Config restore must fire on: (1) interview-mode sys.exit(2), (2) strategist timeout, (3) successful completion, (4) any exception. Currently it only restores after a successful strategist spawn.
    
    Task 8: Write tests for init interview loop
    Files: tests/test_f031_init_interview.py
    Dependencies: [Task 5, Task 6]
    Parallelizable: yes
    Description: Test (a) strategist returns INTERVIEW MODE → answers collected → strategist re-spawned → High confidence → docs written, (b) loop terminates after 3 rounds even if still in interview mode, (c) non-interactive mode saves state and exits(2), (d) --answers flag pre-fills and skips interview, (e) existing one-shot behavior preserved when strategist returns High confidence immediately.
    
    Task 9: Write tests for interview utility helpers
    Files: tests/test_f031_utils_helpers.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Test has_init_interview_triggers(): returns True for line-start CLARIFICATION 1:, True for DECISION: INTERVIEW MODE, False for CLARIFICATION mentioned in prose mid-line, False for empty string, False for no triggers. Test save_init_interview_state(): writes valid JSON, chmod 0o600, includes all fields.
    
    Task 10: Write tests for collect_interview_answers
    Files: tests/test_f031_collect_answers.py
    Dependencies: [Task 2]
    Parallelizable: yes
    Description: Test collect_interview_answers(): (a) tty path collects answers via StringIO mock, (b) non-tty returns empty list, (c) empty clarifications list returns empty list, (d) timeout during question returns partial results with remaining questions as accepted assumptions.
    
    Task 11: Write tests for pipeline refactor
    Files: tests/test_f031_pipeline_refactor.py
    Dependencies: [Task 3]
    Parallelizable: yes
    Description: Test that (a) run_phase1_strategist() uses utils.collect_interview_answers() (import check), (b) interview behavior preserved — same prompt pattern, same answer injection, same exit(2) on non-tty.
    
    Task 12: Write tests for init loop structure
    Files: tests/test_f031_init_loop.py
    Dependencies: [Task 5]
    Parallelizable: yes
    Description: Test (a) run_init function source contains interview loop structure (while loop with CLARIFICATION detection), (b) max_runs guard capped at 3, (c) non-interactive tty check and exit(2) path exists.
    
    8. Data Model
    
    No new persistent entities beyond the interview state JSON file:
    
    json
    {
      "feature": "trading dashboard for SGX options",
      "project_dir": "/home/user/my-project",
      "timestamp": "2026-07-04T20:05:00",
      "round": 2,
      "questions": [
        {
          "id": 1,
          "question": "Who are the primary users?",
          "assumption": "Professional options traders",
          "impact_if_wrong": "Wrong UX decisions",
          "answer": "Retail investors in Singapore"
        }
      ],
      "original_prompt": "<full strategist prompt for replay>"
    }
    
    
    File location: INTERVIEW_SAVE_PATH = "/tmp/dokima-init-interview.json". Permissions: os.chmod(path, 0o600). Transient — not committed to git.
    
    9. API Routes
    
    N/A — CLI-only feature, no HTTP surface.
    
    10. Component Tree
    
    
    dokima init "description" [dir]
      └── roadmap.py:run_init()
           ├── API key + GH token loading (existing)
           ├── Project state detection (existing)
           ├── Profile setup: ensure_profiles(), deploy_profile_skills() (existing)
           ├── max_turns bump: 300 for init (existing, now wrapped in try/finally)
           ├── [NEW] Interview loop (max 3 rounds):
           │    ├── Spawn strategist with interview-enhanced prompt
           │    ├── Detect CLARIFICATION/INTERVIEW MODE via has_init_interview_triggers()
           │    ├── IF interview mode AND tty:
           │    │    └── collect_interview_answers() — stdin, 60s timeout
           │    │    └── Inject answers into re-spawn prompt
           │    │    └── Loop: repeat spawn+detect
           │    ├── IF interview mode AND NOT tty:
           │    │    └── save_init_interview_state() → /tmp/dokima-init-interview.json
           │    │    └── sys.exit(2) with re-run instructions
           │    └── IF High confidence AND no CLARIFICATION blocks: break loop
           ├── max_turns restore (finally — all exit paths)
           ├── Greenfield AGENTS.md creation (existing)
           ├── GitHub remote prompt (existing)
           └── STATUS.md initialization (existing)
    
    
    11. COTS Build-vs-Buy
    
    Everything is built. No external services. The interview is a terminal loop + Hermes agent spawn — no Clerk, no Stripe, no AI API beyond what's already configured. Same stack: Python 3.6+, select.select for stdin timeout, json for state serialization.
    
    12. Test Plan (MANDATORY)
    
    Happy path
    1. User runs dokima init "trading dashboard" /tmp/test-project
    2. Strategist returns CLARIFICATION 1: "Who are the primary users?"
    3. User types answer at stdin prompt
    4. Strategist re-spawns with answer injected, returns CLARIFICATION 2: "What does 'done' look like?"
    5. User types answer
    6. Strategist re-spawns, returns full spec with High confidence, no CLARIFICATION blocks
    7. Four constitution docs written to specs/
    
    Edge cases
    - Empty answers: User presses Enter with no text → accept assumptions noted in question, re-spawn strategist with note that assumptions were accepted
    - Single interview round: Strategist returns High confidence immediately → no interview loop, straight to doc writing (backward compatible)
    - No stdin available (cron/Telegram): Exit code 2, save interview state to JSON, print "Re-run with: dokima init --answers /tmp/dokima-init-interview.json"
    - Timeout during answer prompt: 60-second select timeout → accept remaining questions as assumptions, re-spawn
    - Partial answers: User answers 2 of 4 questions → inject only answered questions, strategist may re-ask remaining
    - Existing AGENTS.md in project: Strategist reads and respects existing AGENTS.md, interview questions adapt
    - Very short description: Single-word "trading" → strategist must ask more clarifying questions
    - max_turns already at default: Bump to 300, restore to whatever the original was (even if not default)
    - Interview JSON file exists from prior run: Overwrite — latest state wins
    
    Failure modes
    - Strategist times out (20 min): Catch timeout marker, print error, save any partial output, exit 1
    - Strategist never reaches High confidence: Max 3 interview rounds → exit with warning, produce best-effort constitution docs, note "Low confidence — review carefully"
    - Strategist returns garbage output: No headers, no CLARIFICATION, no task format → detect, print warning, exit 1 with suggestion to re-run
    - /tmp full: Interview JSON save fails with OSError → print warning to stderr, continue without saved state
    - Hermes agent spawn failure: spawn_agent() raises → catch, print error, exit 1
    - max_turns config parse failure: Config file has no max_turns line → skip bump, print warning, proceed
    - --answers file is invalid JSON: Print parse error, exit 1 with format guidance
    - --answers file from different project: Detect project_dir mismatch, warn user, proceed anyway
    
    Contract invariants
    - After dokima init completes successfully: all four files (mission.md, tech-stack.md, roadmap.md, conventions.md) exist at specs/ with non-empty content
    - Interview state file (if created) is always chmod 0o600
    - max_turns MUST be restored to original value regardless of success/failure/exit(2)/exception
    - AGENTS.md NEVER overwritten if it already exists
    - Confidence marker in output MUST contain "High" without "NOT High" or "Low" for loop to terminate naturally
    - Any other confidence level triggers another interview round (up to max_rounds=3)
    - Non-interactive exit(2) MUST print the exact command to resume: dokima init --answers /tmp/dokima-init-interview.json "description" dir
    
    13. Build & Deploy
    
    - Build: python3 -m py_compile dokima + python3 -m py_compile utils.py + python3 -m py_compile roadmap.py + python3 -m py_compile pipeline.py
    - Test: python3 -m pytest tests/test_f031_*.py -v
    - Integration smoke test: dokima init "test project" /tmp/dokima-f031-test in a temp dir (requires API key)
    - Deploy: Same as existing — tag release via dokima --release patch
    - No new env vars, no new infrastructure, no new dependencies.
    
    14. Risk Register
    
    #: R1
    Risk: Interview loop infinite — strategist never reaches High confidence
    Severity: MEDIUM
    Mitigation: Max 3 rounds hard cap, then best-effort output with warning
    Trigger: 3 consecutive rounds all return CLARIFICATION blocks
    ────────────────────────────────────────
    #: R2
    Risk: Strategist prompt exceeds context window after N rounds of injected
      answers
    Severity: LOW
    Mitigation: Truncate injected answers to 2000 chars total per round
    Trigger: Round 3 prompt approaches model context limit
    ────────────────────────────────────────
    #: R3
    Risk: Breaking existing dokima init one-shot behavior
    Severity: HIGH
    Mitigation: Guard: if no CLARIFICATION blocks in output, skip interview
      loop entirely — identical to pre-F031
    Trigger: Strategist returns High confidence on first try
    ────────────────────────────────────────
    #: R4
    Risk: Interview JSON file collision with pipeline interview
    Severity: LOW
    Mitigation: Use separate path: /tmp/dokima-init-interview.json vs
      /tmp/dokima-interview.json
    Trigger: Both init and pipeline run simultaneously
    ────────────────────────────────────────
    #: R5
    Risk: max_turns not restored after interview-mode exit(2)
    Severity: MEDIUM
    Mitigation: try/finally block around strategist spawn; restore in finally
    Trigger: Any exit path between config bump and restore
    ────────────────────────────────────────
    #: R6
    Risk: stdin timeout causes hang on platforms without select support
    Severity: LOW
    Mitigation: select.select with 60s timeout; fallback to input() if select
      unavailable. If timeout, accept assumptions and proceed
    Trigger: User walks away during init interview
    ────────────────────────────────────────
    #: R7
    Risk: --answers from a different feature causes misleading strategist
      output
    Severity: LOW
    Mitigation: Store project_dir in interview JSON; print warning on
      mismatch, proceed anyway
    Trigger: User accidentally reuses wrong answers file
    ────────────────────────────────────────
    #: R8
    Risk: Strategist output parsing false-positive: CLARIFICATION in prose
      triggers interview mode
    Severity: MEDIUM
    Mitigation: has_init_interview_triggers() anchors to line start (^) — same
      pattern as production interview detection (fixed in Bug 7 of
      test_root_cause_regressions.py)
    Trigger: Strategist mentions "CLARIFICATION" mid-paragraph
    
    15. Anti-Creep
    
    Features explicitly NOT in scope for F031:
    
    - Do NOT build a web UI, TUI, or any visual interface. Terminal stdin/stdout only.
    - Do NOT add voice/ChatGPT-style streaming interview. Text prompts only.
    - Do NOT modify run_phase1_strategist() beyond extracting the shared helper — its behavior must not change.
    - Do NOT add persistence beyond /tmp/dokima-init-interview.json. No database, no file storage beyond tmp.
    - Do NOT add project templates or "start from template" functionality.
    - Do NOT change the constitution doc format or add new doc types (ARCHITECTURE.md, ADRs, etc.).
    - Do NOT add a --skip-interview flag. One-shot behavior is preserved automatically when confidence is High.
    - Do NOT add confirmation prompts ("Are you sure you want to proceed?"). The interview loop itself is the confirmation.
    - Do NOT add progress bars, spinners, or rich formatting. Plain terminal output only.
    
    16. Sign-Off Checklist
    
    - [ ] Interview loop handles non-interactive mode (cron/Telegram) by saving state and exiting(2)
    - [ ] Max 3 interview rounds; best-effort output on round 3 even if confidence is not High
    - [ ] max_turns restored on ALL exit paths (success, interview exit(2), timeout, exception)
    - [ ] Existing dokima init one-shot behavior preserved when strategist returns High confidence immediately
    - [ ] Shared answer collection code extracted from pipeline.py into utils.py without behavioral change
    - [ ] --answers flag loads saved interview state and pre-fills strategist prompt
    - [ ] Interview JSON saved with chmod 0o600
    - [ ] Tests cover: happy path loop, 3-round termination, non-interactive exit(2), --answers flag, backward compatibility
    - [ ] AGENTS.md preserved (never overwritten) when running init on existing project
    - [ ] Strategist prompt explicitly instructs INTERVIEW MODE protocol (DECISION: INTERVIEW MODE + CLARIFICATION N: blocks)
    - [ ] No new dependencies added
    - [ ] dokima init --help text reflects interview mode behavior
    - [ ] Codebase-map.md regenerated after implementation to include new F031 test files