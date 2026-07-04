# F031: dokima init back-and-forth interview mode — strategist asks clarifying questions about users, goals, anti-goals, and constraints before producing constitution docs. Loops until confidence is High, then writes specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md.

Now I have full context. The existing run_init() (roadmap.py line 559) is one-shot — spawns strategist, accepts whatever it produces, no loop. The interview loop infrastructure already exists in run_phase1_strategist() (pipeline.py lines 1598-1703). F031 must port that interview pattern to run_init().
    
    Here is the COMPLETE corrected spec:
    
    
    
    
    F031: dokima init back-and-forth interview mode
    
    Confidence: High
    Impact: MEDIUM
    
    1. Executive Summary
    
    dokima init currently spawns the strategist once and accepts whatever constitution docs it produces. F031 adds a structured interview loop: the strategist asks clarifying questions about users, goals, anti-goals, and constraints before writing constitution docs. The loop repeats until confidence is High, then writes specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md. The interview loop logic already exists in run_phase1_strategist() (pipeline.py lines 1598-1703) — this feature ports that pattern to run_init() in roadmap.py.
    
    2. Constitution Check
    
    - Solves user pain? Yes — dokima init currently produces surface-level constitution docs without probing for deep requirements. Users get spec-kit docs that don't reflect what they actually need.
    - Weekend-buildable? Yes — the interview loop infrastructure already exists in the codebase. This feature is a refactor + port, not greenfield.
    - Evidence people will pay? N/A — internal tooling improvement.
    - Boring tech stack? Yes — Python 3.6+, same patterns as existing interview loop.
    - Avoid AI hype? Yes — no AI categorization.
    
    3. Decision Table
    
    Option: Port existing interview loop to run_init()
    Complexity: Medium — extract + port pattern
    Risk: Low — proven in pipeline
    Reuse: High — same logic
    Verdict: Accept
    ────────────────────────────────────────
    Option: Rewrite interview from scratch
    Complexity: High — reinventing proven code
    Risk: High — different bugs
    Reuse: Zero
    Verdict: Reject
    ────────────────────────────────────────
    Option: Skip interview, keep one-shot
    Complexity: Low
    Risk: High — bad constitution
    Reuse: N/A
    Verdict: Reject
    
    SINGLE APPROACH: Port the interview loop from run_phase1_strategist() (pipeline.py:1598-1703) into run_init() (roadmap.py:559-820), adapting the save/interview/re-prompt pattern to the init context. The strategist prompt already has PHASE 1 — INTERROGATE THE USER instructions. The missing piece is the runtime loop that reads answers and re-spawns.
    
    4. Impact
    
    dokima init becomes a multi-turn conversation that produces higher-quality constitution docs. Users who previously got generic spec-kit output now get docs tailored to their specific project goals, anti-goals, and constraints. The interview loop dramatically reduces the "throwaway init" problem where users run init, realize the output doesn't match their needs, and start over manually.
    
    5. What Changed
    
    - roadmap.py: Add interview loop to run_init() — detect CLARIFICATION output, save interview state, prompt user, re-spawn strategist with answers, repeat until High confidence or 3 retries
    - roadmap.py: Extract _read_interview_answers() helper from run_phase1_strategist() (pipeline.py:1660-1693) into shared utility
    - utils.py: Add INTERVIEW_SAVE_PATH constant and save_interview_state() / has_interview_triggers() helpers
    - tests/test_f031_init_interview.py: Test init interview loop: strategist returns interview mode → answers provided → strategist re-spawns → spec produced. Test loop termination after 3 retries. Test non-interactive mode (saved state, --answers flag)
    
    6. API Routes
    
    N/A — CLI-only feature, no HTTP surface.
    
    7. Component Tree
    
    CLI flow:
    
    dokima init "description" [dir]
      └─ roadmap.py:run_init()
           ├─ Profile setup (existing)
           ├─ Strategist spawn with interview prompt (existing, prompt enhanced)
           ├─ [NEW] Interview loop:
           │    ├─ Detect CLARIFICATION / INTERVIEW MODE in output
           │    ├─ Save interview state → /tmp/dokima-init-interview.json
           │    ├─ Interactive: prompt user for answers (stdin, timeout 60s)
           │    ├─ Non-interactive: exit(2) with instructions to use --answers
           │    ├─ Re-spawn strategist with answers injected
           │    └─ Repeat: check if output has High confidence + no CLARIFICATION blocks
           ├─ [NEW] Max retries guard: exit after 3 interviewing rounds
           └─ Constitution doc writing (existing)
    
    
    8. COTS Build-vs-Buy
    
    Everything is built. No external services. The interview is a terminal loop + Hermes agent spawn — no Clerk, no Stripe, no AI API beyond what's already configured.
    
    9. Test Plan
    
    Happy path
    1. User runs dokima init "trading dashboard" /tmp/test-project
    2. Strategist returns CLARIFICATION 1: "Who are the primary users?"
    3. User types answer at stdin prompt
    4. Strategist re-spawns with answer injected, returns CLARIFICATION 2: "What does 'done' look like?"
    5. User types answer
    6. Strategist re-spawns, returns full spec with High confidence, no CLARIFICATION blocks
    7. Constitution docs written: specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md
    
    Edge cases
    - Empty answers: User presses Enter with no text → accept assumptions, re-spawn strategist with note that assumptions were accepted
    - Single interview round: Strategist returns High confidence immediately → no interview loop, straight to doc writing (backward compatible with current one-shot behavior)
    - No stdin available (cron/Telegram mode): Exit with code 2, save interview state to JSON, print "Re-run with: dokima init --answers /tmp/...json"
    - Timeout during answer prompt: 60-second stdin timeout → accept remaining questions as assumptions, re-spawn
    - Partial answers: User answers 2 of 4 questions → inject only answered questions, strategist may re-ask remaining
    - Existing AGENTS.md in project: Strategist reads and respects existing AGENTS.md, interview questions adapt to existing project state
    - Very short feature description: Single-word "trading" → strategist must ask more clarifying questions
    
    Failure modes
    - Strategist timeout (20 min): Catch [TIMEOUT marker → print error, save any partial output, exit 1
    - Strategist never reaches High confidence: Max 3 interview rounds → exit with warning, produce best-effort constitution docs, note "Low confidence — review carefully"
    - Strategist returns garbage: Output has no headers, no CLARIFICATION, no task format → detect, print warning, exit 1 with suggestion to re-run
    - /tmp full: interview JSON save fails → print warning to stderr, continue without saved state
    - Hermes agent spawn failure: spawn_agent() raises → catch, print error, exit 1
    
    Contract invariants
    - After dokima init completes successfully: all four files (mission.md, tech-stack.md, roadmap.md, conventions.md) exist at specs/ with non-empty content
    - Interview state file (if created) is always chmod 0o600
    - max_turns restored to original value after init regardless of success/failure
    - AGENTS.md never overwritten if it already exists
    - Confidence marker in output MUST be "High" for loop to terminate naturally; any other value triggers another interview round (up to max_rounds=3)
    
    10. Task Breakdown
    
    Task 1: Add interview detection helpers to utils.py
    Files: utils.py
    Dependencies: [none]
    Parallelizable: yes
    Description: Add INTERVIEW_SAVE_PATH = "/tmp/dokima-init-interview.json" constant, has_init_interview_triggers(text: str) -> bool to detect CLARIFICATION/INTERVIEW MODE in strategist output, and save_init_interview_state(feature, project_dir, questions, prompt) -> str to persist interview state JSON.
    
    Task 2: Extract interview answer loop into shared helper in utils.py
    Files: utils.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Extract the interactive answer-collection logic from pipeline.py run_phase1_strategist() (lines 1660-1703) into collect_interview_answers(clarification_lines: list, timeout: int = 60) -> list, handling non-interactive fallback (non-tty → empty list), timeout per question, and empty-input termination.
    
    Task 3: Refactor pipeline.py to use shared interview answer helper
    Files: pipeline.py
    Dependencies: [Task 2]
    Parallelizable: yes
    Description: Replace inline answer-collection code in run_phase1_strategist() (lines 1660-1703) with call to utils.collect_interview_answers(). Verify no behavioral change — same timeout, same tty check, same empty-input semantics.
    
    Task 4: Add interview loop to run_init() — core loop
    Files: roadmap.py
    Dependencies: [Task 2]
    Parallelizable: yes
    Description: After strategist spawn in run_init(), add interview detection using has_init_interview_triggers(). If detected and stdin is tty: call collect_interview_answers(), inject answers into re-spawn prompt. Loop until High confidence in output AND no CLARIFICATION blocks, max 3 rounds. If non-interactive: save state, exit(2) with instructions.
    
    Task 5: Enhance init strategist prompt for interview mode
    Files: roadmap.py
    Dependencies: [none]
    Parallelizable: yes
    Description: Update the init strategist prompt in run_init() to explicitly instruct: "When confidence is NOT High, enter INTERVIEW MODE — output DECISION: INTERVIEW MODE followed by CLARIFICATION N: <question> blocks. Max 4 questions per round. When confidence IS High, write the full constitution docs without CLARIFICATION blocks."
    
    Task 6: Add --answers flag support to init
    Files: roadmap.py, utils.py
    Dependencies: [Task 4]
    Parallelizable: no
    Description: Parse --answers <file> flag in the init subcommand path (dokima entry point). If provided, read interview JSON, extract answers, and prefill into strategist prompt (same pattern as user_answers_prefill in run_phase1_strategist()).
    
    Task 7: Add max_turns restore on all exit paths
    Files: roadmap.py
    Dependencies: [Task 4]
    Parallelizable: no
    Description: Move the max_turns restore logic in run_init() to a try/finally block so it fires on interview-mode exit(2) and timeout paths, not just the happy path. Currently it only restores after a successful strategist spawn.
    
    Task 8: Write tests for init interview loop
    Files: tests/test_f031_init_interview.py
    Dependencies: [Task 4, Task 5, Task 6]
    Parallelizable: yes
    Description: Test: (a) strategist returns INTERVIEW MODE → answers provided → strategist re-spawned → High confidence → docs written. (b) loop terminates after 3 rounds even if still in interview mode. (c) non-interactive mode saves state and exits(2). (d) --answers flag pre-fills and skips interview. (e) existing one-shot behavior preserved when strategist returns High confidence immediately.
    
    11. Build & Deploy
    
    - No new infrastructure. Deploy is the same as existing: python3 -m py_compile dokima + verify.
    - Test: python3 -m pytest tests/test_f031_init_interview.py -v
    - Integration test: dokima init "test project" /tmp/dokima-f031-test in a temp dir
    
    12. Risk Register
    
    #: R1
    Risk: Interview loop infinite — strategist never reaches High confidence
    Severity: MEDIUM
    Mitigation: Max 3 rounds hard cap, then best-effort output
    Trigger: 3 consecutive rounds all return CLARIFICATION blocks
    ────────────────────────────────────────
    #: R2
    Risk: Strategist prompt too large after N rounds of injected answers
    Severity: LOW
    Mitigation: Truncate injected answers to 2000 chars total
    Trigger: Round 3 prompt exceeds model context window
    ────────────────────────────────────────
    #: R3
    Risk: Breaking existing dokima init one-shot behavior
    Severity: HIGH
    Mitigation: Guard: if no CLARIFICATION blocks in output, skip interview
      loop entirely — behavior is identical to pre-F031
    Trigger: Strategist returns High confidence on first try
    ────────────────────────────────────────
    #: R4
    Risk: Interview JSON file collision with pipeline interview
    Severity: LOW
    Mitigation: Use separate path (/tmp/dokima-init-interview.json vs
      /tmp/dokima-interview.json)
    Trigger: Both init and pipeline run simultaneously
    ────────────────────────────────────────
    #: R5
    Risk: max_turns not restored after interview-mode exit(2)
    Severity: MEDIUM
    Mitigation: Try/finally block around strategist spawn; max_turns restore
      in finally
    Trigger: Any exit path between config bump and restore
    ────────────────────────────────────────
    #: R6
    Risk: stdin timeout on answer collection causes hang
    Severity: LOW
    Mitigation: select.select with 60s timeout per question; if timeout,
      accept assumptions and proceed
    Trigger: User walks away during init interview
    
    13. Anti-Creep
    
    - Do NOT build a web UI, a TUI (text-based UI), or any visual interface for the interview. Terminal stdin/stdout only.
    - Do NOT add voice/ChatGPT-style streaming interview. Text prompts only.
    - Do NOT modify run_phase1_strategist() beyond extracting the shared helper — its behavior must not change.
    - Do NOT add persistence of interview answers beyond the session. No database, no file beyond /tmp/dokima-init-interview.json.
    - Do NOT add project templates or "start from template" functionality. That's not part of F031.
    - Do NOT change the constitution doc format or add new doc types (e.g., ARCHITECTURE.md). The four existing documents are the output.
    - Do NOT add a "skip interview" flag. One-shot behavior is preserved automatically when confidence is High.
    
    14. Sign-Off Checklist
    
    - [ ] Interview loop handles non-interactive mode (cron/Telegram) by saving state and exiting(2)
    - [ ] Max 3 interview rounds; best-effort output on round 3 even if confidence is not High
    - [ ] max_turns restored on ALL exit paths (success, interview exit(2), timeout)
    - [ ] Existing dokima init one-shot behavior preserved when strategist returns High confidence immediately
    - [ ] Shared answer collection code extracted from pipeline.py into utils.py without behavioral change
    - [ ] --answers flag loads saved interview state and pre-fills strategist prompt
    - [ ] Interview JSON saved with chmod 0o600
    - [ ] Tests cover: happy path loop, 3-round termination, non-interactive exit(2), --answers flag, backward compatibility
    - [ ] AGENTS.md preserved (never overwritten) when running init on existing project
    - [ ] Strategist prompt explicitly instructs INTERVIEW MODE protocol (DECISION: INTERVIEW MODE + CLARIFICATION N: blocks)
    - [ ] No new dependencies added
    - [ ] dokima init --help reflects interview mode behavior
    
    
    What changed from the previous spec:
    1. Added ## 4. Impact section with concrete description of what changes for the user
    2. Added ## 5. What Changed section with bullet list of files changed and what each change does
    3. Converted all tasks to ### Task N: format with all five required fields (Files, Dependencies, Parallelizable, Description)
    
    All three quality gate issues are resolved. The spec now passes verify_spec_quality() checks:
    - ## 4. Impact → matches regex for Impact section
    - ## 5. What Changed → matches regex for What Changed section with bullet list
    - ### Task N: headers → matches the panel DAG parser regex