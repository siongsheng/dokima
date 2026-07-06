# F033: Cross-run learning via conventions.md: when TL blocks a PR for a pattern violation, append a one-line rule to conventions.md. Next strategist reads it. No vector DB, no pattern extraction — human-readable rules that compound.

Good. Now I have full context. The spec was written as the target for full implementation. The utils.py functions exist and 26 tests pass, but 3 pipeline wiring tests fail because the wiring isn't connected yet. The spec describes the desired end state.
    
    Here is the complete corrected spec with all three fixes applied:
    
    
    F033: Cross-run learning via conventions.md: when TL blocks a PR for a pattern violation, append a one-line rule to conventions.md. Next strategist reads it. No vector DB, no pattern extraction — human-readable rules that compound.
    
    Status: In Progress — utils.py complete (26/29 tests pass), pipeline wiring pending (3 tests fail)
    Version: 1.1.0 (2026-07-06 — corrected: Impact Assessment, What Changed, ### Task N: headers)
    Ponytail Guard: Rung 7 — custom logic, no existing rule-extraction or conventions-append existed. Strategist already reads conventions.md (pipeline.py:1659).
    
    
    
    Executive Summary
    
    When the Tech Lead blocks a PR for a pattern violation — e.g., "all subprocess calls MUST use list args" — append a one-line rule to specs/conventions.md. The next strategist session already reads conventions.md (pipeline.py:1659) and inherits the learned rule. No vector DB, no ML pattern extraction. Human-readable rules that compound across pipeline runs. Confidence: High (feature builds on existing TL-review and conventions infrastructure — both already tested and stable).
    
    Constitution Check
    
    Axiom: Solves user's own pain?
    Status: ✅ YES
    Evidence: TL blockers repeat across runs — this closes the loop
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: ✅ YES
    Evidence: ~140 LOC across 3 files, <2 hours
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A
    Evidence: Internal tool feature, not a paid product
    ────────────────────────────────────────
    Axiom: Tech stack boring/proven?
    Status: ✅ YES
    Evidence: Python file I/O + regex, same patterns as existing
      _extract_tl_blockers
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories?
    Status: ✅ YES
    Evidence: No vector DB, no embeddings, no pattern extraction ML
    
    No misalignments flagged.
    
    Decision Table
    
    Option: Append to conventions.md
    Verdict: Accept
    Rationale: Simplest — read path (pipeline.py:1659) already wired
    ────────────────────────────────────────
    Option: Separate learned-rules.md
    Verdict: Reject
    Rationale: Atomizes conventions, reader must load two files
    ────────────────────────────────────────
    Option: GitHub Issue per rule
    Verdict: Reject
    Rationale: Issues pile up, no programmatic consumption
    
    Impact Assessment (Grounded)
    
    Based on current codebase state (git log + grep):
    
    Files affected (implementation):
    - utils.py (+140 LOC): _extract_convention_rules() at line 2518, _append_convention_rules() at line 2576 — both implemented and tested
    - pipeline.py (+24 LOC stubs, ~15 LOC pending): Import at line 28 (_extract_convention_rules), import of _append_convention_rules missing; wiring into run_phase5_tech_lead() at line 1379 NOT YET DONE
    - tests/test_f033_cross_run_learning.py (+330 LOC): 29 tests — 26 pass (extraction + append unit tests), 3 fail (pipeline wiring tests)
    
    What already references conventions.md:
    - pipeline.py:1659 — Strategist prompt reads specs/conventions.md as step 1
    - roadmap.py:734 — Creates {PROJECT_DIR}/specs/conventions.md template
    - roadmap.py:1012 — Lists conventions.md among constitution docs
    - test_task_dag.py:166 — Classifies under docs task group
    
    What already references TL blocker extraction:
    - pipeline.py:1517 — blocker_lines = _extract_tl_blockers(tl_output) (the injection point)
    - utils.py:2074 — _extract_tl_blockers() definition
    - tests/test_tl_extraction.py — 10 tests, all pass
    
    Dependency chain: _extract_tl_blockers() → _extract_convention_rules() → _append_convention_rules(). All in utils.py. Pipeline wiring is the only missing piece.
    
    What Changed
    
    File: utils.py
    Change: Add _extract_convention_rules() (line 2518-2573)
    LOC: +56
    Status: ✅ Done, tested
    ────────────────────────────────────────
    File: utils.py
    Change: Add _append_convention_rules() (line 2576-2654)
    LOC: +79
    Status: ✅ Done, tested
    ────────────────────────────────────────
    File: pipeline.py
    Change: Add _extract_convention_rules import (line 28)
    LOC: +1
    Status: ✅ Done
    ────────────────────────────────────────
    File: pipeline.py
    Change: Add _append_convention_rules import
    LOC: +1
    Status: ❌ Missing
    ────────────────────────────────────────
    File: pipeline.py
    Change: Wire convention extraction into run_phase5_tech_lead() after line
      1517
    LOC: ~+15
    Status: ❌ Missing
    ────────────────────────────────────────
    File: tests/test_f033_cross_run_learning.py
    Change: New: extraction + append + pipeline wiring tests
    LOC: +330
    Status: ✅ Done (26/29 pass)
    
    Remaining work: Import _append_convention_rules in pipeline.py, add ~15 lines of wiring into run_phase5_tech_lead() after _extract_tl_blockers() call at line 1517. Once wired, all 29 tests should pass.
    
    Feature Breakdown
    
    Task 1: Add _extract_convention_rules() and _append_convention_rules() to utils.py
    Files: utils.py
    Dependencies: [none]
    Parallelizable: yes
    Description: Implement two functions: (1) _extract_convention_rules(blocker_lines: list[str]) -> list[str] — filter TL blocker lines to pattern-violation rules, skip file-specific one-time fixes (file extensions, "line N", "file:/path:/directory:" patterns), keep convention-type patterns only (e.g., "subprocess must use list args" kept, "missing null check in foo.py line 42" filtered). (2) _append_convention_rules(project_dir: str, rules: list[str]) -> int — read specs/conventions.md, create ## Cross-Run Learning section if absent, append new rules with <!-- auto: YYYY-MM-DD --> comment, deduplicate case-insensitively, write back. Return count of newly appended rules. Defensive: None input → 0/[], empty strings filtered, specs/ dir created if absent.
    
    Task 2: Wire convention rule extraction into run_phase5_tech_lead() in pipeline.py
    Files: pipeline.py
    Dependencies: [Task 1]
    Parallelizable: no (depends on Task 1 — needs the functions)
    Description: After blocker_lines = _extract_tl_blockers(tl_output) (pipeline.py ~line 1517), when blocker_lines is non-empty and verdict is BLOCKED or CHANGES REQUESTED: (a) call _extract_convention_rules(blocker_lines), (b) call _append_convention_rules(PROJECT_DIR, rules), (c) print 📋 Appended N convention rule(s) to specs/conventions.md. Wrap in try/except — best-effort, pipeline continues on failure. Import _extract_convention_rules and _append_convention_rules in the utils import block at the top of pipeline.py.
    
    Task 3: Add tests for convention rule extraction and append
    Files: tests/test_f033_cross_run_learning.py
    Dependencies: [Task 1]
    Parallelizable: yes (no file overlap with Task 2)
    Description: Test _extract_convention_rules: empty list → empty, file-specific blockers filtered (file extensions, "line N", "file:" pattern), convention patterns kept, mixed list → only conventions returned, None → empty, no separator → skipped, output <= input. Test _append_convention_rules: empty rules → 0, new rule appended, section created when absent, case-insensitive dedup, duplicates return 0, batch internal dedup, specs/ dir creation, trailing newline invariant, section header appears once, pipeline imports both functions (hasattr), run_phase5_tech_lead source contains both function calls, convention summary print line present. Use tempfile.mkdtemp + specs/conventions.md for file tests.
    
    Data Model
    
    No new database entities. conventions.md extends with:
    
    
    Cross-Run Learning
    
    <!-- auto: 2026-07-04 -->
    - All subprocess calls MUST use list args — never shell=True or string commands.
    <!-- auto: 2026-07-04 -->
    - No hardcoded 'master' branch — always detect from origin/HEAD.
    
    
    Rules are plain bullet points. The <!-- auto: DATE --> comment is non-semantic — human-readable provenance, not machine-parsed.
    
    API/Interface Proposal
    
    N/A — no new API, no route changes. Internal function calls within the pipeline.
    
    Security Considerations
    
    N/A — no attack surface change. File writes restricted to specs/conventions.md in PROJECT_DIR (already validated by _validate_project_dir). No user input flows directly into file content — rules are extracted from TL agent output using the same _extract_tl_blockers pipeline already trusted for PR body injection.
    
    COTS Build-vs-Buy
    
    Component: Rule dedup
    Decision: Build
    Justification: set() + casefold — 3 lines, no dependency needed
    ────────────────────────────────────────
    Component: File I/O
    Decision: Build
    Justification: stdlib open(), existing conventions.md format
    ────────────────────────────────────────
    Component: TL blocker extraction
    Decision: COTS (reuse)
    Justification: Existing _extract_tl_blockers() from utils.py
    ────────────────────────────────────────
    Component: Strategist reading
    Decision: COTS (reuse)
    Justification: Already reads conventions.md at pipeline.py:1659 step 1
    
    Test Plan (MANDATORY)
    
    Feature Area: _extract_convention_rules()
    
    - Happy path: Input: ["1. Missing null check — src/foo.py line 42", "2. List args — all subprocess calls must use list args"] → Output: ["all subprocess calls must use list args"]
    - Edge cases: Empty list → empty list. All file-specific blockers → empty list. All convention patterns → all returned. None input → empty list (defensive). Single rule with mixed "—" separator → correctly parsed. File reference via "file:", "path:", "directory:" → filtered. "line N" pattern without file extension → filtered. Malformed line (no "—") → skipped. Blank/whitespace lines → skipped.
    - Failure modes: Non-string items in list → TypeError caught by type hint; caller guarantees list[str].
    - Contract invariants: Output list length ≤ input list length. Every output item is a clean one-line string without bullet markers, severity labels, or number prefixes.
    
    Feature Area: _append_convention_rules()
    
    - Happy path: conventions.md without ## Cross-Run Learning section, one new rule → section created, rule appended, returns 1.
    - Edge cases: Section already exists → rule appended after existing rules. Empty rules list → returns 0, file unchanged. None input → returns 0 (defensive). Duplicate rule (case-insensitive) → not appended. Batch internal duplicate → appended once. 10 rules, 8 duplicates → returns 2. No specs/ directory → created. No conventions.md file → created fresh. File ends with trailing newline.
    - Failure modes: conventions.md is read-only → permission error surfaced (no silent fail).
    - Contract invariants: File always ends with trailing newline. Section header appears exactly once. Each appended rule has exactly one <!-- auto: ... --> comment on preceding line. New rules appear after existing rules within the section.
    
    Feature Area: Pipeline wiring
    
    - Happy path: TL returns BLOCKED verdict with 3 blockers, 1 convention pattern → 1 rule appended, 📋 Appended 1 convention rule(s) to specs/conventions.md printed.
    - Edge cases: APPROVED verdict → no rules extracted (skip entirely). Empty blocker_lines → skip. TL output has zero convention patterns → print count (0) or silence. _append_convention_rules raises exception → caught, pipeline continues (best-effort).
    - Failure modes: PROJECT_DIR undefined → pre-existing guard catches before reaching this code.
    - Contract invariants: Pipeline never fails due to convention-append failure. The _append_convention_rules call is best-effort only.
    
    Panel Split
    
    | Wave   | Tasks          | Parallel?              | Coder agents |
    |--------|----------------|------------------------|--------------|
    | Wave 1 | Task 1, Task 3 | Yes (different files)  | 2            |
    | Wave 2 | Task 2         | No (depends on Task 1) | 1            |
    
    2 coder agents, 2 waves. Estimated wall-clock: ~15 minutes.
    
    Build & Deploy
    
    - Deploys as part of the dokima panel (single Python script + modules)
    - No new dependencies, no CI changes
    - Test command: python3 -m pytest tests/test_f033_cross_run_learning.py -v
    - Convention file: specs/conventions.md in PROJECT_DIR (standard path, already tracked in git)
    
    Documentation Impact
    
    MAINTAINERS.md: Update specs/conventions.md row to note the ## Cross-Run Learning section and its auto-population behavior. No README change needed.
    
    Risk Register
    
    #: 1
    Risk: TL outputs noise that looks like convention rules
    Severity: LOW
    Mitigation: _extract_convention_rules filters file-specific and one-time
      patterns; only generic pattern-violation lines pass
    Trigger: False rule appended to conventions.md
    ────────────────────────────────────────
    #: 2
    Risk: conventions.md grows unboundedly
    Severity: LOW
    Mitigation: Dedup prevents exact duplicates; human curates during PR
      review naturally
    Trigger: conventions.md exceeds reasonable size (~500 lines)
    ────────────────────────────────────────
    #: 3
    Risk: Convention append fails silently
    Severity: LOW
    Mitigation: Print line confirms append count; best-effort is correct — TL
      review is authoritative, conventions are supplementary
    Trigger: Append exception swallowed
    ────────────────────────────────────────
    #: 4
    Risk: Race condition: two pipelines append simultaneously
    Severity: LOW
    Mitigation: Same lock file (/tmp/dokima-<project>.lock) prevents
      concurrent pipeline runs
    Trigger: N/A — lock prevents concurrency
    
    Anti-Creep
    
    Explicitly OUT OF SCOPE:
    - No vector database, no embeddings, no ML pattern extraction
    - No automated rule enforcement — conventions.md is human-readable guidance, not lint rules
    - No rule expiration or staleness detection
    - No cross-project rule sharing — rules stay in the project they were learned in
    - No modification of the strategist prompt to "prioritize" learned rules — the strategist already reads conventions.md
    - No retry-until-no-blockers loop — that's dokima fix, not this feature
    - No GitHub Issue creation for learned rules — blockers already get issues (SHOULD FIX path)
    
    Sign-Off Checklist
    
    - [ ] _extract_convention_rules() correctly filters file-specific vs convention patterns
    - [ ] _extract_convention_rules() handles None, blank lines, file:/path:/directory: patterns defensively
    - [ ] _append_convention_rules() deduplicates case-insensitively (cross-batch and internal)
    - [ ] _append_convention_rules() creates specs/ dir and conventions.md when absent
    - [ ] _append_convention_rules() returns correct count (0 for all-duplicates, N for new)
    - [ ] Pipeline imports BOTH _extract_convention_rules AND _append_convention_rules
    - [ ] Pipeline wires into run_phase5_tech_lead() after blocker extraction (line ~1517)
    - [ ] Append is best-effort — pipeline continues on failure (try/except)
    - [ ] ## Cross-Run Learning section created automatically on first use
    - [ ] Each appended rule has <!-- auto: YYYY-MM-DD --> provenance
    - [ ] No imports or function calls added to the strategist code path (read side unchanged)
    - [ ] All 29 tests pass: python3 -m pytest tests/test_f033_cross_run_learning.py -v
    - [ ] No regression: existing 679 tests still pass
    - [ ] MAINTAINERS.md updated to document the new conventions.md section
    
    
    
    
    Corrections made:
    
    1. Impact Assessment — New section grounded in actual tool output: git log shows 4 commits for this feature, grep confirms 6 references to conventions.md across the codebase, test output shows 26/29 pass. Cites specific line numbers (pipeline.py:1659, utils.py:2518, pipeline.py:1517).
    
    2. What Changed — New section with file-level change table: utils.py (+140 LOC done), pipeline.py (+24 stubs done, ~15 LOC + 1 import pending), tests/test_f033_cross_run_learning.py (+330 LOC done). Status column marks each as ✅ or ❌ per current codebase state.
    
    3. Task N: headers — All three tasks now use ### Task N: format with all five required fields (Files:, Dependencies:, Parallelizable:, Description:). No wave groupings inside task blocks.