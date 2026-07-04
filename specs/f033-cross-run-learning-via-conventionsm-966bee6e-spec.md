# F033: Cross-run learning via conventions.md: when TL blocks a PR for a pattern violation, append a one-line rule to conventions.md. Next strategist reads it. No vector DB, no pattern extraction — human-readable rules that compound.

I have full context now. Here's the complete corrected F033 spec:
    
    
    
    F033: Cross-run learning via conventions.md
    
    Feature ID: F033
    Priority: P2
    Dependencies: None
    Status: In Progress
    Branch: feat/f033-cross-run-learning-via-conventionsm-a639b200
    Project: /home/opc/dokima
    
    
    
    1. Executive Summary
    
    When the Tech Lead blocks a PR for a pattern violation — a rule that would also catch future similar issues — the panel appends a one-line rule to specs/conventions.md. The strategist already reads this file in Phase 1 (pipeline.py line 1455). The next pipeline run picks up accumulated rules automatically. No vector DB, no ML pattern extraction, no "smart" categorization — just append + deduplicate. Human-readable rules compound across runs.
    
    Confidence: High. The strategist already reads conventions.md. The hook point is clear (post-TL verdict in run_phase5_tech_lead). The code change is ~60 LOC in pipeline.py with a ~30-line helper in utils.py.
    
    
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Status: YES
    Notes: Shaun watches the pipeline repeat the same TL feedback across PRs —
      "missing guard clause," "TDD violation," "bundled commits." This
      compounds.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: YES
    Notes: ~90 LOC total. Hook is two function calls.
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A (internal tool, not SaaS)
    Notes: —
    ────────────────────────────────────────
    Axiom: Tech stack boring and proven?
    Status: YES
    Notes: File append + Python set dedup. No new deps.
    ────────────────────────────────────────
    Axiom: Avoid AI hype categories?
    Status: YES
    Notes: Explicitly NOT "AI pattern extraction" or vector DB. Just file I/O.
    
    Verdict: PASS. No misalignments.
    
    
    
    3. Impact
    
    Files affected: pipeline.py (+35/-2), utils.py (+45/-0), tests/test_f033_conventions.py (+60/-0)
    
    Dependencies touched:
    - run_phase5_tech_lead() — new call to _append_convention_rules() after verdict extraction
    - _extract_tl_blockers() — no change; output is consumed by new function
    - specs/conventions.md — written to (append-only), read by strategist (existing, no change)
    
    Upstream impact:
    - Strategist prompt in run_phase1_strategist() — no code change needed; already reads conventions.md at line 1455
    - No API changes, no DB changes, no CLI changes
    
    Downstream impact:
    - Future pipeline runs benefit from accumulated rules
    - conventions.md grows linearly — anti-creep section prevents bloat
    
    
    
    4. What Changed
    
    This is a net-new feature. No existing behavior is modified:
    
    - NEW: _extract_convention_candidates(tl_output: str) -> list[str] in utils.py — parses TL blocker output for generalizable rules
    - NEW: _append_convention_rules(rules: list[str], conventions_path: str) in utils.py — deduplicates against existing rules, appends new ones
    - NEW: Hook call in run_phase5_tech_lead() — after verdict extraction (line 1307), before PR body update (line 1310)
    - NEW: tests/test_f033_conventions.py — test suite for extraction, dedup, and append logic
    
    No existing functions are modified. The hook is additive.
    
    
    
    5. Decision Table
    
    Option: A: Vector DB + semantic embedding
    Simplicity: Low — adds pgvector/milvus dep
    Maintainability: Low — operational overhead
    Learning Quality: High
    Verdict: Reject — violates "boring" axiom
    ────────────────────────────────────────
    Option: B: LLM-based pattern extraction (spawn agent to re-read PR + TL
      review)
    Simplicity: Medium — one more agent call
    Maintainability: Medium — prompt engineering fragile
    Learning Quality: Medium
    Verdict: Reject — latency, token cost, hallucination risk
    ────────────────────────────────────────
    Option: C: Regex extraction from TL BLOCKER output + append to
      conventions.md
    Simplicity: High — pure Python, no new deps
    Maintainability: High — file append, testable
    Learning Quality: Medium — only catches what TL explicitly labels
    Verdict: Accept
    
    Rationale: Option C is the only approach that satisfies the "no new deps, no AI hype" constraints. The TL already writes structured blocker output (severity + category + file:line + rule). We parse that, filter for pattern-like rules, and append.
    
    Accepted risk: We won't catch every learnable pattern — only those the TL explicitly labels as BLOCKERs with convention-like phrasing. This is acceptable because the TL is the authority on what matters.
    
    
    
    6. Feature Breakdown (Task Plan)
    
    Task 1: Add _extract_convention_candidates() to utils.py
    Files: utils.py
    Dependencies: [none]
    Parallelizable: yes
    Estimated LOC: ~30
    Description: Parse TL output for BLOCKER lines containing convention-like patterns (phrases like "no", "never", "always", "must", "all X must Y", "every PR should"). Return deduplicated list of one-line rules. Filter out one-off blocker descriptions (e.g., "missing test for function foo()") — only capture rules that would apply to future PRs.
    
    Task 2: Add _append_convention_rules() to utils.py
    Files: utils.py
    Dependencies: [Task 1]
    Parallelizable: no
    Estimated LOC: ~15
    Description: Read existing conventions.md Anti-Patterns section, deduplicate new rules against existing bullet points, append only genuinely new rules. Handle missing file (create with header). Handle empty file. Never modify existing rules — append-only. Return count of rules added.
    
    Task 3: Wire hook into run_phase5_tech_lead() in pipeline.py
    Files: pipeline.py
    Dependencies: [Task 2]
    Parallelizable: no
    Estimated LOC: ~15
    Description: After _extract_tl_verdict() (line 1307) and before PR body update (line 1310), add call: when verdict is BLOCKED or CHANGES_REQUESTED, call _extract_convention_candidates() on tl_output, then _append_convention_rules() to specs/conventions.md. Log how many rules were added ("F033: appended 2 convention rules"). Best-effort — if it fails, log warning and continue (never block the pipeline on a learning hook).
    
    Task 4: Import new functions in pipeline.py
    Files: pipeline.py
    Dependencies: [Task 2]
    Parallelizable: no
    Estimated LOC: ~2
    Description: Add _extract_convention_candidates and _append_convention_rules to the import block at the top of pipeline.py. These are already imported from utils.py — just add the names.
    
    Task 5: Write tests for convention extraction
    Files: tests/test_f033_conventions.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Estimated LOC: ~30
    Description: Test _extract_convention_candidates() with: (a) TL output containing "BLOCKER: No hardcoded paths in module code" → extracts rule, (b) TL output with "BLOCKER: missing test for handle_timeout()" → filtered out (one-off), (c) empty TL output → empty list, (d) TL output with mixed one-off and pattern blockers → only patterns extracted.
    
    Task 6: Write tests for convention append + dedup
    Files: tests/test_f033_conventions.py
    Dependencies: [Task 2, Task 5]
    Parallelizable: no
    Estimated LOC: ~30
    Description: Test _append_convention_rules() with: (a) new rules + empty conventions.md → creates file with rules, (b) new rules + existing conventions.md with no overlap → appends, (c) new rules where some already exist → only appends genuinely new ones, (d) all rules already exist → no writes (return 0), (e) conventions.md missing Anti-Patterns section → creates it.
    
    Task 7: Update AGENTS.md conventions section
    Files: AGENTS.md
    Dependencies: [Task 4]
    Parallelizable: yes
    Estimated LOC: ~2
    Description: Add convention: "F033: TL-blocked pattern violations append to specs/conventions.md — check it before designing." This ensures human contributors also know about the learning mechanism.
    
    
    
    7. Data Model
    
    No new entities. Data flows:
    
    
    TL BLOCKER output (string)
      → _extract_convention_candidates() → list[str] (one-line rules)
      → _append_convention_rules()        → int (count appended)
      → specs/conventions.md              (file append, existing format)
    
    Existing conventions.md format preserved:
    Anti-Patterns
    - No hardcoded 'master' branch — detected from origin/HEAD
    - No absolute dollar amounts in docs — provider-agnostic percentages only
    - ... (new rules appended here)
    
    
    Persistence: File-based. conventions.md is already tracked in git.
    Transient: The list of extracted candidates is ephemeral — only the file write persists.
    
    
    
    8. API / Interface
    
    No API changes. Internal interface:
    
    python
    NEW in utils.py
    def _extract_convention_candidates(tl_output: str) -> list[str]:
        """Parse TL BLOCKER output for convention-like rules.
        Returns deduplicated list of one-line rule strings.
        Filters out one-off blocker descriptions."""
    
    def _append_convention_rules(rules: list[str], conventions_path: str) -> int:
        """Append new convention rules to specs/conventions.md.
        Deduplicates against existing rules. Returns count of rules added.
        Best-effort — logs warnings, never raises."""
    
    In pipeline.py, run_phase5_tech_lead(), after verdict extraction:
    conventions_path = os.path.join(PROJECT_DIR, "specs", "conventions.md")
    candidates = _extract_convention_candidates(tl_output)
    if candidates:
        added = _append_convention_rules(candidates, conventions_path)
        print(f"  F033: appended {added} convention rule(s) to conventions.md")
    
    
    
    
    9. Security
    
    - File writes: specs/conventions.md is within PROJECT_DIR — already validated as a git repo (F001 hardening). No path traversal risk.
    - Input sanitization: TL output is agent-generated text. _extract_convention_candidates() strips control characters and limits rule length to 200 chars to prevent log injection or file corruption.
    - Atomicity: Use open(path, 'a') with a single write call. If interrupted mid-write, the partial line won't parse but won't corrupt earlier rules.
    - No secrets exposure: rules are human-readable anti-pattern descriptions. No tokens, no credentials.
    
    
    
    10. Documentation
    
    - AGENTS.md: Updated (Task 7) to mention F033 convention
    - No new docs pages: This is a pipeline-internal mechanism
    - No README change: Feature is invisible to end users of dokima's target projects
    
    
    
    11. Test Plan (MANDATORY)
    
    Happy Path
    - TL blocks PR with "BLOCKER: No shell=True in subprocess calls — use list args always"
    - Pipeline calls _extract_convention_candidates() → extracts rule
    - Pipeline calls _append_convention_rules() → appends to conventions.md
    - Next pipeline run: strategist reads conventions.md and sees the new rule
    
    Edge Cases
    - conventions.md doesn't exist: Create it with ## Anti-Patterns header + new rules
    - conventions.md has no Anti-Patterns section: Append ## Anti-Patterns header before rules
    - Rule already exists (exact match): Skip, return 0 added
    - Rule exists with different phrasing but same intent: Simplified approach — only deduplicate exact string matches. Close-enough is fine; duplicates are harmless.
    - conventions.md is empty: Same as "doesn't exist"
    - conventions.md is very large (10K+ lines): Read only the Anti-Patterns section for dedup, not the whole file
    - TL output has no convention-like blockers (all one-off): Returns empty list, no file write
    - TL output is empty or malformed: Returns empty list, no file write
    - File write permission denied: Log warning, don't crash the pipeline
    
    Failure Modes
    - Disk full during append: open('a') may succeed but write may fail — catch IOError, log warning
    - conventions.md has non-UTF8 content: Fallback to latin-1 decode, log warning
    - PROJECT_DIR is None: Skip entirely, log debug
    - Concurrent pipeline runs writing simultaneously: Lock file at /tmp/dokima-<project>.lock already prevents concurrent runs — this is a non-issue
    
    Contract Invariants
    - Before append: conventions.md is a valid markdown file (or doesn't exist)
    - After append: conventions.md is still a valid markdown file with Anti-Patterns section intact
    - Before append: existing rules are unchanged
    - After append: only new rules were added; existing rules are byte-identical
    - Pipeline invariant: convention learning failure NEVER blocks the pipeline — it's always best-effort
    
    
    
    12. Build & Deploy
    
    No build or deploy changes. Feature is purely Python code within existing pipeline module.
    
    CI: Existing pytest suite picks up tests/test_f033_conventions.py automatically.
    No env vars needed.
    No new pip dependencies.
    
    
    
    13. Risk Register
    
    #: 1
    Risk: conventions.md grows unbounded (TL flags the same pattern class
      repeatedly with slight wording variations)
    Severity: LOW
    Mitigation: Dedup is exact-match only but duplicates are harmless; user
      can manually prune
    Trigger: conventions.md exceeds 200 anti-pattern lines
    ────────────────────────────────────────
    #: 2
    Risk: False positives — TL output contains BLOCKER text that isn't a
      convention ("BLOCKER: function foo() returns wrong type")
    Severity: MEDIUM
    Mitigation: _extract_convention_candidates() filters for convention-like
      phrasing (never/always/must/no X should Y)
    Trigger: One-off bugs get appended as "rules"
    ────────────────────────────────────────
    #: 3
    Risk: File corruption if PID killed mid-write
    Severity: LOW
    Mitigation: Single write() call is atomic at OS level for lines <
      PIPE_BUF; worst case is a partial last line
    Trigger: SIGKILL during append
    ────────────────────────────────────────
    #: 4
    Risk: TL output format changes, regex stops matching
    Severity: LOW
    Mitigation: Best-effort — if extraction returns empty, nothing is written.
      Pipeline continues.
    Trigger: TL prompt format change in future feature
    ────────────────────────────────────────
    #: 5
    Risk: conventions.md location differs across projects
    Severity: LOW
    Mitigation: Always uses os.path.join(PROJECT_DIR, "specs",
      "conventions.md") — same path strategist reads
    Trigger: Non-dokima project with different spec layout
    
    
    
    14. Anti-Creep (NOT in scope)
    
    - No vector database or semantic similarity for dedup — exact string match only
    - No LLM-based pattern extraction — no additional agent calls
    - No meta-analysis of accumulated rules (clustering, categorization, frequency tracking)
    - No automatic rule retirement — rules are never deleted by the panel
    - No rule suggestions for the TL — TL remains the sole authority on what's a pattern violation
    - No cross-project rule sharing — each project's conventions.md is independent
    - No convention enforcement — F033 is passive (append + next-run-read). It does NOT add automated linting or pre-commit hooks
    - No modification of existing rules — append-only, never edit or reorder
    
    
    
    15. Sign-Off Checklist
    
    - [ ] _extract_convention_candidates() correctly filters one-off blockers from pattern rules
    - [ ] _append_convention_rules() handles missing file, empty file, existing rules, and duplicates
    - [ ] Hook in run_phase5_tech_lead() is best-effort — failures log warnings, never block pipeline
    - [ ] All 6 test cases in test_f033_conventions.py pass
    - [ ] Existing test suite (673 tests) passes with zero regressions
    - [ ] conventions.md remains valid markdown after append
    - [ ] AGENTS.md updated with F033 convention
    - [ ] Manual verification: run pipeline on a feature, TL blocks with pattern violation, check conventions.md has new rule
    - [ ] Security review: no path traversal, no injection, no secrets exposure
    - [ ] No new pip dependencies
    - [ ] No CLI or API changes