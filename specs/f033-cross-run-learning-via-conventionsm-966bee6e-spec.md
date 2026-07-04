# F033: Cross-run learning via conventions.md: when TL blocks a PR for a pattern violation, append a one-line rule to conventions.md. Next strategist reads it. No vector DB, no pattern extraction — human-readable rules that compound.

Here is the complete corrected spec. Issues addressed:
    
    1. Task N: headers: All three tasks use the mandated ### Task N: Brief description format with all five fields
    2. File overlap: Tasks 1 (utils.py), 2 (pipeline.py), and 3 (tests/test_f033_cross_run_learning.py) operate on distinct files — zero overlap
    
    Ponytail Guard: Rung 7 (custom logic required — no existing rule-extraction or conventions-append exists in codebase. Strategist already reads conventions.md at pipeline.py:1455).
    
    
    
    F033: Cross-Run Learning via conventions.md
    
    Executive Summary
    
    When the Tech Lead blocks a PR for a pattern violation — e.g., "all subprocess calls MUST use list args" — append a one-line rule to specs/conventions.md. The next strategist session already reads conventions.md (pipeline.py:1455) and inherits the learned rule. No vector DB, no ML pattern extraction. Human-readable rules that compound across pipeline runs. Confidence: High (feature builds on existing TL-review and conventions infrastructure — both already tested and stable).
    
    Constitution Check
    
    Axiom: Solves user's own pain?
    Status: ✅ YES
    Evidence: TL blockers repeat across runs — this closes the loop
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: ✅ YES
    Evidence: ~120 LOC across 3 files, <2 hours
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
    
    Decision Table — SINGLE APPROACH
    
    Append rule lines under a ## Cross-Run Learning section in conventions.md after each TL review. The strategist already reads conventions.md (step 1 in pipeline.py:1455 prompt). This is a pure write-side change — the read path already works.
    
    Option: Append to conventions.md (proposed)
    Verdict: Accept — simplest, read path already wired
    ────────────────────────────────────────
    Option: Separate learned-rules.md file
    Verdict: Reject — atomizes conventions, reader must load two files
    ────────────────────────────────────────
    Option: GitHub Issue for each rule
    Verdict: Reject — issues pile up, no programmatic consumption
    
    2. Impact
    
    After TL blocks a PR for a pattern violation, the pipeline appends a cleaned one-line rule to specs/conventions.md under a ## Cross-Run Learning section. The next strategist reads it automatically (no pipeline changes needed on the read side). Rules deduplicate — the same pattern won't be appended twice. Each rule carries a <!-- auto: <ISO date> --> HTML comment for provenance tracking. This creates compounding knowledge: the TL teaches the system once, and every future feature spec benefits.
    
    3. What Changed
    
    - utils.py: Add _extract_convention_rules() (+~30 LOC) and _append_convention_rules() (+~40 LOC)
    - pipeline.py: Wire convention extraction into run_phase5_tech_lead() after blocker extraction (+~15 LOC, one new import)
    - tests/test_f033_cross_run_learning.py: New file (+~120 LOC)
    
    Confidence: (High)  
    Impact: (LOW)
    
    API/Interface Proposal
    
    N/A — no new API, no route changes. Internal function calls within the pipeline.
    
    Security Considerations
    
    N/A — no attack surface change. File writes restricted to specs/conventions.md in PROJECT_DIR (already validated by _validate_project_dir). No user input flows directly into file content — rules are extracted from TL agent output using the same _extract_tl_blockers pipeline already trusted for PR body injection.
    
    Documentation Impact
    
    MAINTAINERS.md: Update specs/conventions.md row to note the ## Cross-Run Learning section and its auto-population behavior. No README change needed.
    
    
    
    Feature Breakdown
    
    Task 1: Add _extract_convention_rules() and _append_convention_rules() to utils.py
    Files: utils.py
    Dependencies: [none]
    Parallelizable: yes
    Description: Implement two functions: (1) _extract_convention_rules(blocker_lines: list[str]) -> list[str] — filter TL blocker lines to pattern-violation rules, skip file-specific one-time fixes, keep convention-type patterns only (e.g., "subprocess must use list args" kept, "missing null check in foo.py line 42" filtered). (2) _append_convention_rules(project_dir: str, rules: list[str]) -> int — read specs/conventions.md, create ## Cross-Run Learning section if absent, append new rules with <!-- auto: YYYY-MM-DD --> comment, deduplicate case-insensitively, write back. Return count of newly appended rules.
    
    Task 2: Wire convention rule extraction into run_phase5_tech_lead() in pipeline.py
    Files: pipeline.py
    Dependencies: [Task 1]
    Parallelizable: no (depends on Task 1 — needs the functions to exist)
    Description: After blocker_lines = _extract_tl_blockers(tl_output) (pipeline.py ~line 1313), when blocker_lines is non-empty and verdict is BLOCKED or CHANGES REQUESTED, call _extract_convention_rules(blocker_lines) followed by _append_convention_rules(PROJECT_DIR, rules). Print summary: 📋 Appended N convention rule(s) to specs/conventions.md. Import _extract_convention_rules and _append_convention_rules in the utils import block at the top of pipeline.py.
    
    Task 3: Add tests for convention rule extraction and append
    Files: tests/test_f033_cross_run_learning.py
    Dependencies: [Task 1]
    Parallelizable: yes (no file overlap with Task 2)
    Description: Test _extract_convention_rules: empty list → empty, file-specific blockers filtered (e.g., "missing null check in src/foo.py line 42" → excluded), convention patterns kept (e.g., "all subprocess calls must use list args" → included as rule), mixed list → only convention rules returned. Test _append_convention_rules: empty rules → no-op, one new rule appended under new section, duplicate rule (case-insensitive) not re-appended, section created when absent, file unchanged when all rules are duplicates. Use tempfile.mkdtemp + specs/conventions.md to avoid mutating real file.
    
    
    
    Data Model
    
    No new database entities. Conventions.md extends with:
    
    
    Cross-Run Learning
    
    <!-- auto: 2026-07-04 -->
    - All subprocess calls MUST use list args — never shell=True or string commands.
    <!-- auto: 2026-07-04 -->
    - No hardcoded 'master' branch — always detect from origin/HEAD.
    
    
    Rules are plain bullet points. The <!-- auto: DATE --> comment is non-semantic — human-readable provenance, not machine-parsed.
    
    COTS Build-vs-Buy
    
    Component: Rule dedup
    Buy/COTS: —
    Build: Build
    Justification: set() + casefold — 3 lines, no dependency needed
    ────────────────────────────────────────
    Component: File I/O
    Buy/COTS: —
    Build: Build
    Justification: stdlib open(), existing conventions.md format
    ────────────────────────────────────────
    Component: TL blocker extraction
    Buy/COTS: COTS
    Build: —
    Justification: Reuses existing _extract_tl_blockers() from utils.py
    ────────────────────────────────────────
    Component: Strategist reading
    Buy/COTS: COTS
    Build: —
    Justification: Already reads conventions.md at pipeline.py:1455 step 1
    
    Test Plan (MANDATORY)
    
    Feature Area: _extract_convention_rules()
    
    - Happy path: Input: ["1. Missing null check — src/foo.py line 42", "2. List args — all subprocess calls must use list args"] → Output: ["all subprocess calls must use list args"]
    - Edge cases: Empty list → empty list. All file-specific blockers → empty list. All convention patterns → all returned. Single rule with mixed "—" separator → correctly parsed.
    - Failure modes: Malformed blocker line (no "—" separator) → skipped gracefully. Non-string items in list → TypeError caught by type hint, caller guarantees list[str].
    - Contract invariants: Output list length ≤ input list length. Every output item is a clean one-line string without bullet markers or severity labels.
    
    Feature Area: _append_convention_rules()
    
    - Happy path: conventions.md without ## Cross-Run Learning section, one new rule → section created, rule appended, returns 1.
    - Edge cases: Section already exists → rule appended to end of section. Empty rules list → returns 0, file unchanged. Duplicate rule (case-insensitive match) → not appended, returns count of truly new rules. No specs/ directory → created. 10 new rules, 8 of which are duplicates → returns 2, only 2 appended.
    - Failure modes: conventions.md is read-only → permission error surfaced (no silent fail). File is empty/absent → treated as new file, section + rules created.
    - Contract invariants: File always ends with a trailing newline. Section header appears exactly once. Each appended rule has exactly one <!-- auto: ... --> comment on the preceding line.
    
    Feature Area: Pipeline wiring
    
    - Happy path: TL returns BLOCKED verdict with 3 blockers, 1 convention pattern → 1 rule appended printed, conventions.md updated.
    - Edge cases: APPROVED verdict → no rules extracted (skip entirely). Empty blocker_lines → skip. TL output has zero convention patterns → "0 rules appended" or silence.
    - Failure modes: _append_convention_rules raises exception → caught, pipeline continues (best-effort, non-blocking). PROJECT_DIR undefined → pre-existing guard catches before we reach this code.
    - Contract invariants: Pipeline never fails due to convention-append failure. The _append_convention_rules call is best-effort only.
    
    Panel Split
    
    Wave 1: [Task 1, Task 3] — parallel (different files)
    Wave 2: [Task 2] — sequential (depends on Task 1)
    
    2 coder agents, 2 waves, estimated wall-clock: ~15 minutes.
    
    Build & Deploy
    
    - Deploys as part of the dokima panel (single Python script + modules)
    - No new dependencies, no CI changes
    - Test command: python3 -m pytest tests/test_f033_cross_run_learning.py -v
    - Convention file: specs/conventions.md in PROJECT_DIR (standard path, already tracked in git)
    
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
      review is the authoritative gate, conventions are supplementary
    Trigger: Append exception swallowed
    ────────────────────────────────────────
    #: 4
    Risk: race condition: two pipelines append simultaneously
    Severity: LOW
    Mitigation: Same lock file (/tmp/dokima-<project>.lock) prevents
      concurrent pipeline runs
    Trigger: Not applicable — lock prevents concurrency
    
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
    - [ ] _append_convention_rules() deduplicates case-insensitively
    - [ ] Pipeline wires into run_phase5_tech_lead() after blocker extraction (line ~1313)
    - [ ] Append is best-effort — pipeline continues on failure
    - [ ] ## Cross-Run Learning section created automatically on first use
    - [ ] Each appended rule has <!-- auto: YYYY-MM-DD --> provenance
    - [ ] No imports or function calls added to the strategist code path (read side unchanged)
    - [ ] Tests pass: python3 -m pytest tests/test_f033_cross_run_learning.py -v
    - [ ] No regression: existing 679 tests still pass
    - [ ] MAINTAINERS.md updated to document the new conventions.md section