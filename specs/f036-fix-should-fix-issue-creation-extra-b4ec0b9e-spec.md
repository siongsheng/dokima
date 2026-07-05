# F036: Fix SHOULD FIX issue creation: extract from PR review text (not just nm_stdout), handle table-format findings (R1 | RELIABILITY | ... | SHOULD FIX). Add tests for all extraction formats.

Now I have full context on the project and the feature. Let me produce the complete corrected spec.
    
    Here is the complete corrected spec for F036:
    
    
    F036: Fix SHOULD FIX issue creation — extract from PR review text, handle table-format findings
    
    Status: In Progress | Confidence: High | Impact: LOW
    
    1. Executive Summary
    
    The current SHOULD FIX issue creation (pipeline.py:1371) only extracts from raw TL agent output (tl_output) and only handles the SHOULD FIX — description prose format. It misses table-format findings like | R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions | that TL agents produce. Additionally, it does not extract from the structured PR review text (the ## Review section injected into the PR body, or the PR review comment), which is where properly formatted findings live. This fix adds a unified extraction function in utils.py that parses all formats from all review-text sources, wires it into the pipeline, and adds exhaustive tests. Confidence: High — straightforward parsing change on existing infrastructure.
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Verdict: ✅ YES
    Evidence: SHOULD FIX issues are silently skipped when TL uses table format
      — user reports missing issues
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Verdict: ✅ YES
    Evidence: ~150 LOC across 3 files, <3 hours
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Verdict: N/A
    Evidence: Internal tool feature
    ────────────────────────────────────────
    Axiom: Tech stack boring/proven?
    Verdict: ✅ YES
    Evidence: Python regex + stdlib, same patterns as existing
      _extract_tl_blockers
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories?
    Verdict: ✅ YES
    Evidence: No AI/ML — pure text parsing
    
    No misalignments flagged.
    
    3. Decision Table
    
    Option: Add extract_should_fix() in utils.py, replace inline extraction at
      pipeline.py:1371
    Verdict: Accept
    Reasoning: Centralized parsing, testable independently
    ────────────────────────────────────────
    Option: Extract from tl_output only (no change)
    Verdict: Reject
    Reasoning: Misses PR review text and table format
    ────────────────────────────────────────
    Option: Extract from PR body + PR review comment via separate functions
    Verdict: Reject
    Reasoning: Duplication — single function with source parameter is cleaner
    ────────────────────────────────────────
    Option: Post-process nm_stdout separately
    Verdict: Reject
    Reasoning: nm findings are supplementary — TL review is authoritative
    
    Ponytail Guard: Rung 7 (new parsing logic required — no existing table-format SHOULD FIX extraction exists. The current extract_blockers_from_pr does a different job: it extracts BLOCKER lines, not SHOULD FIX, and uses different patterns.)
    
    4. Impact
    
    SHOULD FIX issues are currently created from raw TL agent output only, missing table-format findings and PR review text. After this fix, the pipeline will extract SHOULD FIX findings from the PR review comment (the TL's posted review, which is the structured, authoritative source), falling back to the raw TL output when the review comment is unavailable. The extraction handles three formats: table rows ( | ID | DIMENSION | LOCATION | SEVERITY | DETAIL | ), em-dash prose ( SHOULD FIX — description ), and colon prose ( SHOULD FIX: description ). Affects ~3 files: utils.py (+70 LOC), pipeline.py (+20 LOC, -10 LOC replaced), tests/test_f036_should_fix_extraction.py (new, +120 LOC). No API change, no deployment change.
    
    5. What Changed
    
    - utils.py: Add extract_should_fix_from_text(text: str) -> list[dict] — unified parser for table, prose, and bullet formats. Each dict has keys: id (str), dimension (str), location (str), detail (str). Table format detection via pipe-delimited regex; prose format via keyword + separator detection. Deduplicates by detail text.
    - pipeline.py: Replace lines 1370-1371 (should_fix_lines = [l for l in tl_output.split("\n") if "SHOULD FIX" in l.upper() and "—" in l]) with a call to the new unified extractor. Source: PR review comment body (fetched via gh pr view --comments), falling back to tl_output if the review comment is unavailable. Clean up the extraction to use structured dicts instead of raw line strings.
    - tests/test_f036_should_fix_extraction.py (NEW): Tests for all three extraction formats, edge cases (empty text, no SHOULD FIX lines, mixed BLOCKER/SHOULD FIX/NIT in table, escaped pipes), deduplication, and the pipeline integration point.
    
    6. Feature Breakdown
    
    Task 1: Add extract_should_fix_from_text() to utils.py
    Files: utils.py
    Dependencies: [none]
    Parallelizable: yes
    Description: Implement a unified SHOULD FIX extraction function that accepts any text source and returns structured dicts. Handle three formats: (a) Table rows with pipe delimiters — detect via regex \|\sSHOULD\sFIX\s*\|, extract columns; (b) Prose format SHOULD FIX: description or SHOULD FIX — description via keyword + separator matching; (c) Bullet format - SHOULD FIX: description. Return list[dict] with keys id, dimension, location, detail. Skip lines where SHOULD FIX appears only in context (e.g., "BLOCKER: ... SHOULD FIX next sprint" — no extraction). Deduplicate by normalizing detail text (lowercase, strip punctuation). Handle edge cases: empty text returns [], table rows with fewer/more columns, escaped pipes in detail text. Place near _extract_tl_blockers() (~line 1920) for colocation with related parsing logic.
    
    Task 2: Wire unified extractor into pipeline.py SHOULD FIX issue creation
    Files: pipeline.py
    Dependencies: [Task 1]
    Parallelizable: no (depends on Task 1)
    Description: Replace the inline extraction at lines 1370-1371 with a call to the new function. Source priority: (1) Fetch the TL review comment body via gh pr view <num> --repo REPO --comments --json reviews --jq '.[-1].body' — this is the authoritative structured output the TL posted. (2) Fall back to tl_output if the review comment is unavailable. Call extract_should_fix_from_text(source_text) to get structured findings. Adapt the issue creation loop (lines 1374-1394) to use dict fields: desc = finding['detail'], enhanced title with dimension prefix (e.g., "SHOULD FIX [RELIABILITY]: {desc[:72]}"), and enhanced body with table data when available. Keep the [:5] cap. Import the new function. Remove the old regex-only extraction logic.
    
    Task 3: Add tests for all SHOULD FIX extraction formats
    Files: tests/test_f036_should_fix_extraction.py
    Dependencies: [Task 1]
    Parallelizable: yes (no file overlap with Task 2)
    Description: Create comprehensive tests for extract_should_fix_from_text(). Test categories: (a) Table format — single row, multi-row, missing columns, extra columns, escaped pipes, mixed severity rows (only SHOULD FIX extracted), no matching rows → empty; (b) Prose format — em-dash separator, colon separator, mixed case should fix, SHOULD FIX within a sentence (context-only, should NOT extract); (c) Bullet format — - SHOULD FIX: desc, * SHOULD FIX — desc; (d) Integration — full TL output with table-finding blocks, the real-world scenario from the bug report; (e) Edge cases — empty string, None passed (graceful), only whitespace, text with no SHOULD FIX at all, duplicate findings deduped; (f) Pipeline wiring — mock gh to verify the review comment fetch path and the tl_output fallback path. Use conftest._load_panel fixture for import access.
    
    7. Data Model
    
    No new persistent entities. The extraction function returns transient dicts:
    
    
    {
        "id": "R1",              # from table col 1, or "" for prose
        "dimension": "RELIABILITY",  # from table col 2, or "" for prose  
        "location": "utils.py:42",   # from table col 3, or "" for prose
        "detail": "Naming convention for internal functions"  # the human-readable finding
    }
    
    
    Table format parsing: | R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming convention | → dict above.
    Prose format parsing: SHOULD FIX — Naming convention for internal functions → {"id": "", "dimension": "", "location": "", "detail": "Naming convention for internal functions"}.
    
    8. API Routes
    
    N/A — no API changes. Internal function calls within the pipeline.
    
    9. COTS Build-vs-Buy
    
    Component: Table parsing
    Decision: Build
    Justification: stdlib re — ~15 lines, no dependency needed
    ────────────────────────────────────────
    Component: Text dedup
    Decision: Build
    Justification: set() with normalized keys — 3 lines
    ────────────────────────────────────────
    Component: GitHub API for PR comments
    Decision: COTS
    Justification: Existing gh pr view --comments infrastructure — already
      used in extract_blockers_from_pr
    
    Everything is built. No new dependencies.
    
    10. Test Plan (MANDATORY)
    
    Feature Area: extract_should_fix_from_text() — Table format
    
    - Happy path: Input contains | R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Use snake_case | → one result with all fields populated.
    - Edge cases: Table with 3 columns (missing dimension/location) → gracefully parsed with empty strings for missing fields. Table with 6+ columns → extra columns appended to detail. Double-pipe || in detail → not split as a new column (non-greedy match). Table row with SHOULD FIX in a different column position → detected by content, not column index.
    - Failure modes: Empty table cell string → empty string in dict, no crash. Malformed table (no pipes) → falls through to prose parser. Unicode/emoji in detail → preserved.
    - Contract invariants: Every returned dict has all four keys. Only rows where SHOULD FIX is in the severity column are extracted (BLOCKER and NIT rows are skipped).
    
    Feature Area: extract_should_fix_from_text() — Prose format
    
    - Happy path: Input contains SHOULD FIX: Update AGENTS.md with new command → one result with detail "Update AGENTS.md with new command".
    - Edge cases: should fix (lowercase) → matched case-insensitively. SHOULD FIX — conventions — naming (multiple em-dashes) → first em-dash splits. SHOULD FIX: "quoted description" → quotes preserved. Line with SHOULD FIX in middle of sentence (like "the BLOCKER … SHOULD FIX in next phase") → NOT extracted (no separator after SHOULD FIX keyword).
    - Failure modes: Empty detail after separator → skipped (no issue created for empty description). Line with only SHOULD FIX and no description → skipped.
    - Contract invariants: Extracted only when SHOULD FIX is followed by : or  —  within the same line. The detail text is stripped of leading/trailing whitespace.
    
    Feature Area: Pipeline wiring — source selection
    
    - Happy path: PR exists with TL review comment → fetches comment body via gh pr view --comments, extracts SHOULD FIX, creates issues.
    - Edge cases: PR exists but no TL review comment yet → falls back to tl_output. No PR at all (pr_url is None) → uses tl_output directly. Review comment fetch fails (gh error) → logs warning, falls back to tl_output.
    - Failure modes: gh not authenticated → caught by existing guards. Network timeout on gh pr view → falls back to tl_output (best-effort).
    - Contract invariants: Pipeline never fails due to SHOULD FIX extraction failure. The extraction is best-effort only — if it produces zero findings, the pipeline proceeds normally.
    
    Feature Area: Deduplication
    
    - Happy path: Two identical findings → only one issue created.
    - Edge cases: "Naming convention" and "naming convention." → treated as duplicate (lowercase + strip punctuation). "Update docs" and "Update docs in AGENTS.md" → NOT duplicates (text differs).
    - Contract invariants: No more than 5 issues created per run (existing cap).
    
    11. Panel Split
    
    - Wave 1: [Task 1, Task 3] — parallel (different files: utils.py vs test file)
    - Wave 2: [Task 2] — sequential (depends on Task 1 — needs the function to exist)
    
    2 coder agents, 2 waves, estimated wall-clock: ~15 minutes.
    
    12. Build & Deploy
    
    - Deploys as part of the dokima panel (single Python script + modules)
    - No new dependencies, no CI changes
    - Test command: python3 -m pytest tests/test_f036_should_fix_extraction.py -v
    - No new env vars needed
    - Existing gh pr view --comments API is already authenticated (reuses existing token)
    
    13. Risk Register
    
    #: 1
    Risk: Table regex too greedy — matches BLOCKER rows as SHOULD FIX
    Severity: LOW
    Mitigation: Regex explicitly requires SHOULD FIX (or SHOULD\s*FIX for
      spacing variants) in the matched row
    Trigger: BLOCKER issue created with SHOULD FIX title
    ────────────────────────────────────────
    #: 2
    Risk: PR review comment fetch adds latency
    Severity: LOW
    Mitigation: gh pr view --comments is a single API call — adds <2s.
      Fallback to tl_output on failure
    Trigger: Pipeline phase 5 runs 2s longer
    ────────────────────────────────────────
    #: 3
    Risk: TL output format change breaks all parsers
    Severity: LOW
    Mitigation: Three format branches (table, prose, bullet) provide
      redundancy. If ALL fail, zero findings → pipeline proceeds normally
    Trigger: No SHOULD FIX issues created for a run
    ────────────────────────────────────────
    #: 4
    Risk: Duplicate detection misses near-duplicates
    Severity: LOW
    Mitigation: Exact text match after normalization is conservative (false
      negative for near-dupes > false positive for distinct findings merged)
    Trigger: Two similar-but-not-identical issues created
    ────────────────────────────────────────
    #: 5
    Risk: gh pr view --comments returns empty [] for PRs with no reviews
    Severity: LOW
    Mitigation: Handled — empty → fallback to tl_output
    Trigger: Silent fallback, no user impact
    
    14. Anti-Creep
    
    Explicitly OUT OF SCOPE:
    - No extraction from nm output (nm_stdout) — nm is supplementary, not authoritative for SHOULD FIX
    - No auto-fix for SHOULD FIX items — only BLOCKER items get auto-fixed
    - No modification of the TL review prompt — doesn't change what TL produces, only how we parse it
    - No GitHub Issue template change — issue format stays the same
    - No change to extract_blockers_from_pr() — that function handles BLOCKERs, not SHOULD FIX
    - No SHOULD FIX aggregation across runs — each run handles its own findings
    - No severity-based issue labeling — all SHOULD FIX issues use the same label structure
    
    15. Sign-Off Checklist
    
    - [ ] extract_should_fix_from_text() handles table format: | R1 | RELIABILITY | file:line | SHOULD FIX | detail |
    - [ ] extract_should_fix_from_text() handles prose format: SHOULD FIX: detail and SHOULD FIX — detail
    - [ ] extract_should_fix_from_text() handles bullet format: - SHOULD FIX: detail
    - [ ] BLOCKER and NIT rows in table format are NOT extracted
    - [ ] Empty/missing fields in table rows don't crash
    - [ ] Pipeline wires extraction to use PR review comment as primary source, tl_output as fallback
    - [ ] Fallback path works when PR review comment is unavailable
    - [ ] Duplicate findings (case-insensitive, punctuation-stripped) produce at most one issue
    - [ ] Issue cap of 5 is preserved
    - [ ] Tests pass: python3 -m pytest tests/test_f036_should_fix_extraction.py -v
    - [ ] No regression: existing 679 tests still pass
    
    
    The corrected spec is now complete with all required sections. Key fixes applied:
    
    1. Impact section (Section 4): Added with specific impact analysis covering files affected, formats handled, and scope boundaries.
    
    2. What Changed section (Section 5): Added with concrete file-by-file breakdown of additions/changes.
    
    3. Task N: headers (Section 6): All three tasks use the mandated ### Task N: format with all five required fields (Files, Dependencies, Parallelizable, Description). Zero file overlap between parallel tasks — Task 1 touches utils.py, Task 3 touches tests/test_f036_should_fix_extraction.py, so they run in the same wave.
    
    4. All other sections preserved and enhanced: Executive Summary, Constitution Check, Decision Table, Data Model, API Routes, COTS Build-vs-Buy, Test Plan with concrete edge cases, Panel Split with parallelism, Build & Deploy, Risk Register (5 items), Anti-Creep (7 out-of-scope items), and Sign-Off Checklist (11 items).