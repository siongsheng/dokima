# F031: dokima init back-and-forth interview mode — strategist asks clarifying questions about users, goals, anti-goals, and constraints before producing constitution docs. Loops until confidence is High, then writes specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md.

Now I have thorough understanding of the codebase. Let me produce the complete corrected F031 spec.
    
    
    
    F031: dokima init back-and-forth interview mode
    
    Status: In Progress | Confidence: High | Impact: MEDIUM
    
    Executive Summary
    
    dokima init currently fires the strategist once with a discovery prompt and hopes for the best. The strategist has no way to ask clarifying questions about users, goals, anti-goals, or constraints. This feature adds the same interview loop that run_phase1_strategist already has — detect DECISION: INTERVIEW MODE + CLARIFICATION lines, loop back with user answers, exit(2) in non-interactive mode, support --answers for resume. Max 3 loops, then produce constitution docs only when confidence is High. Estimated ~300 LOC across roadmap.py + dokima entry point + tests.
    
    Constitution Check
    
    Axiom: Solves user's own pain?
    Status: YES
    Notes: Users currently get vague constitution docs; interview mode
      produces tailored, high-confidence results
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: YES
    Notes: ~300 LOC, reuses existing interview infrastructure from
      run_phase1_strategist
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A
    Notes: Internal tooling feature — no payment gating
    ────────────────────────────────────────
    Axiom: Tech stack boring and proven?
    Status: YES
    Notes: Python 3.6+, reuses existing subprocess/hermes infrastructure
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories?
    Status: YES
    Notes: Not an "AI-powered" feature — it's a CLI UX improvement
    
    Verdict: PASS. All axioms satisfied.
    
    2. Impact
    
    run_init() in roadmap.py gains an interactive interview loop. The strategist can now ask 3-4 clarifying questions and receive user answers before producing constitution docs. In non-interactive (CI/scripted) contexts, questions are saved to /tmp/dokima-interview.json and the process exits with code 2 — resume via dokima init --answers /tmp/dokima-interview.json. The dokima entry point gains --answers flag on the init subcommand. Max 3 interview rounds to prevent infinite loops. All existing init behavior (greenfield detection, profile setup, AGENTS.md creation, STATUS.md init) is preserved — the interview loop is additive.
    
    3. What Changed
    
    - roadmap.py: ~200 lines added to run_init() — interview mode detection, answer parsing, re-spawn loop, --answers resume path
    - dokima: ~10 lines — add --answers flag to init subcommand argparse, pass through to run_init()
    - tests/test_profile_templates.py: Add interview loop tests — non-interactive exit(2), --answers resume, High confidence early exit
    - specs/STATUS.md: Auto-updated by panel post-merge — no manual change needed
    
    4. Feature Breakdown
    
    Task 1: Add interview-mode detection and loop to run_init()
    - Files: roadmap.py
    - Dependencies: [none]
    - Parallelizable: no
    - Estimated LOC: ~150
    - Description: After spawn_agent("strategist", ...) returns, inspect strat_output for DECISION: INTERVIEW MODE and anchored ^CLARIFICATION \d+: patterns. If found and no user answers provided, enter interview loop: parse questions from CLARIFICATION lines, present to user (interactive) or save to JSON and exit(2) (non-interactive). On interactive re-spawn, prefix answers to the strategist prompt and re-invoke. Loop max 3 rounds. Track confidence via Confidence: (High)/(Medium)/(Low) regex — exit loop when High AND no CLARIFICATION lines. Uses same pattern as run_phase1_strategist lines 1581-1686.
    
    Task 2: Add --answers flag to init subcommand in dokima entry point
    - Files: dokima
    - Dependencies: [Task 1]
    - Parallelizable: no
    - Estimated LOC: ~15
    - Description: Add init_p.add_argument("--answers", default=None) to the init subparser (around line 149). Pass answers_path through to run_init() as a third parameter or via environment variable. On resume: read interview JSON, extract previous questions+answers, inject as USER CLARIFICATIONS prefilled context into strategist prompt.
    
    Task 3: Add non-interactive resume path in run_init()
    - Files: roadmap.py
    - Dependencies: [Task 1]
    - Parallelizable: no
    - Estimated LOC: ~50
    - Description: When --answers path is provided, load the interview JSON, extract prompt and any previous answers, inject into strategist prompt as USER CLARIFICATIONS (from previous interview): section. Re-spawn strategist with enriched prompt. Handle corrupted/missing JSON file gracefully — print error, fall back to fresh init.
    
    Task 4: Add interview loop tests
    - Files: tests/test_profile_templates.py
    - Dependencies: [Task 1, Task 2, Task 3]
    - Parallelizable: yes
    - Estimated LOC: ~120
    - Description: Test cases: (a) strategist returns DECISION: INTERVIEW MODE + 2 CLARIFICATION lines, non-interactive → exit(2) and interview JSON saved, (b) --answers resume → strategist produces High confidence spec, (c) strategist returns High confidence immediately → no interview loop, docs written directly, (d) max 3 loops enforced, (e) empty description → error exit, (f) CLARIFICATION in spec prose (not interview mode) → no false positive (uses anchored regex like pipeline interview mode). Reuse existing _load_panel fixture from conftest.py.
    
    5. Data Model
    
    Interview state (persisted to /tmp/dokima-interview.json):
    json
    {
      "feature_description": "trading dashboard",
      "project_dir": "/home/user/project",
      "interview_mode": true,
      "questions": ["CLARIFICATION 1: Who are the primary users?", "CLARIFICATION 2: What are anti-goals?"],
      "answers": ["retail traders", "no real-time streaming"],
      "prompt": "<original strategist prompt>",
      "round": 2,
      "max_rounds": 3
    }
    
    
    All /tmp/dokima-* artifacts get os.chmod(..., 0o600) — existing security convention (F001).
    
    6. API Routes
    
    N/A — CLI-only feature. No new HTTP endpoints.
    
    7. Component Tree
    
    N/A — no frontend components. The init flow is CLI-only:
    
    
    dokima init "description" [dir] [--answers path]
      └── roadmap.run_init(description, dir, answers_path)
           ├── detect project state (greenfield/existing)
           ├── ensure_profiles() + deploy_profile_skills()
           ├── [LOOP] spawn strategist → detect interview mode → ask user → re-spawn
           └── write specs/mission.md, tech-stack.md, roadmap.md, conventions.md, AGENTS.md
    
    
    8. COTS Build-vs-Buy
    
    Component: Interview loop
    Decision: BUILD — adapt from run_phase1_strategist
    Justification: Existing proven pattern in same codebase, 0 deps
    ────────────────────────────────────────
    Component: JSON serialization
    Decision: BUILD — stdlib json
    Justification: Already used for interview state in pipeline
    ────────────────────────────────────────
    Component: stdin reading
    Decision: BUILD — select.select + sys.stdin
    Justification: Same pattern as pipeline interactive interview
    ────────────────────────────────────────
    Component: CLI argv parsing
    Decision: BUILD — argparse (stdlib)
    Justification: Already in use for init subcommand
    
    Nothing to buy. Everything is ~200 lines of Python reusing existing abstractions.
    
    9. Test Plan (MANDATORY)
    
    Happy path
    - dokima init "trading dashboard for retail investors" — interactive: strategist asks 2 questions, user answers, strategist produces High confidence docs, files written to specs/
    - dokima init "..." --answers /tmp/dokima-interview.json — non-interactive resume: reads prior answers, produces docs, exits 0
    - Strategist reaches High confidence on first pass — no interview loop, docs written immediately
    
    Edge cases
    - Empty description: dokima init "" → error "init requires a project description", exit(1)
    - Max rounds exhausted: Strategist still at Medium confidence after 3 rounds → write docs anyway with warning "⚠ Confidence is Medium after 3 rounds — review carefully"
    - Corrupted interview JSON: --answers /tmp/broken.json → print error, fall back to fresh init
    - Missing interview JSON file: --answers /tmp/nonexistent.json → print error, exit(1)
    - CLARIFICATION in spec prose, not interview: "The strategist should output CLARIFICATION 1:..." in strategist output BUT task headers also present → no interview mode (has_tasks guard, same as pipeline line 1589)
    
    Failure modes
    - Strategist times out: 20 min timeout, [TIMEOUT:] in output → print error, exit(1) (existing behavior)
    - Strategist provider down: fallback model fires via existing _detect_provider_failure + FALLBACK_MODELS["strategist"]
    - stdin not a TTY and no --answers: save interview JSON, exit(2), print "Re-run with: dokima init --answers /tmp/dokima-interview.json"
    - User hits Ctrl-C during interview: KeyboardInterrupt → "Interview aborted" message, exit(1)
    
    Contract invariants
    - After run_init() returns successfully: specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md exist and are non-empty
    - specs/STATUS.md exists with header line (existing behavior, unchanged)
    - max_turns config is always restored to original value in finally block (existing behavior, unchanged)
    - Interview JSON at /tmp/dokima-interview.json is always chmod 0o600 (security convention F001)
    - No more than 3 interview rounds — enforced by counter, not by strategist
    
    10. Panel Split
    
    All tasks are sequential (same file: roadmap.py). One coder agent, 4 waves:
    
    
    Wave 1: Task 1 (core loop)
    Wave 2: Task 2 (CLI flag) + Task 3 (resume path) — not parallelizable (shared roadmap.py)
    Wave 3: Task 4 (tests)
    
    
    Coder agents: 1 (single file changes, no parallelism possible)
    
    11. Build & Deploy
    
    No deployment changes. Feature is purely CLI-side. After merge:
    
    bash
    python3 -m pytest tests/test_profile_templates.py -q -k "interview"
    python3 -m pytest tests/ -q  # full suite
    
    
    12. Risk Register
    
    #: 1
    Risk: Interview loop infinite re-spawn
    Severity: HIGH
    Mitigation: Max 3 rounds enforced in code, not dependent on strategist
    Trigger: Counter > 3
    ────────────────────────────────────────
    #: 2
    Risk: --answers flag conflicts with existing argv parsing
    Severity: LOW
    Mitigation: init_p.add_argument("--answers", ...) is additive, doesn't
      conflict with positional description or dir
    Trigger: F030 argparse restructuring complete
    ────────────────────────────────────────
    #: 3
    Risk: Strategist never reaches High confidence
    Severity: MEDIUM
    Mitigation: After 3 rounds, write docs with warning banner. User must
      manually review
    Trigger: Confidence: (Medium) after round 3
    ────────────────────────────────────────
    #: 4
    Risk: False-positive interview mode (CLARIFICATION in spec prose)
    Severity: MEDIUM
    Mitigation: Same guard as pipeline: has_tasks check suppresses interview
      mode when ### Task N: headers present
    Trigger: Strategist output contains both task headers and CLARIFICATION
      text
    ────────────────────────────────────────
    #: 5
    Risk: max_turns not restored on interview loop exception
    Severity: LOW
    Mitigation: Wrap entire interview loop in try/finally — existing pattern
      at lines 761-765 already handles this
    Trigger:
    ────────────────────────────────────────
    #: 6
    Risk: Interview JSON overwrites another project's state
    Severity: LOW
    Mitigation: /tmp/dokima-interview.json is single-instance. Mitigation:
      future enhancement could key by PROJECT_DIR hash
    Trigger:
    
    13. Anti-Creep
    
    Features explicitly NOT in scope:
    - No multi-project interview sessions — one init per call
    - No GUI/web interview interface — CLI-only, same as pipeline interview mode
    - No "suggest answers" AI feature — strategist asks; user answers; no auto-suggest
    - No interview state persistence beyond file — /tmp/dokima-interview.json only, replaced each run
    - No changing run_phase1_strategist interview mode behavior — that already works; this is init-specific
    - No modifying the strategist skill (spec-strategist-lite) — the skill already has interview mode instructions; we're making the coordinator respond to them
    - No new Python dependencies — stdlib only (json, select, os, re, sys)
    
    14. Sign-Off Checklist
    
    - [ ] Does dokima init in interactive mode loop through questions? (3 rounds max)
    - [ ] Does dokima init in non-interactive mode save interview JSON and exit(2)?
    - [ ] Does dokima init --answers /path/to/interview.json resume correctly?
    - [ ] Does High confidence strategist output skip the interview loop entirely?
    - [ ] Does corrupted/missing --answers file fail gracefully?
    - [ ] Does the interview loop guard against false positives (CLARIFICATION in spec prose)?
    - [ ] Is max_turns restored even on interview loop exception?
    - [ ] Are all 4+1 constitution docs written after successful init?
    - [ ] Do existing init tests still pass? (python3 -m pytest tests/test_profile_templates.py -q)
    - [ ] Full test suite passes? (python3 -m pytest tests/ -q)