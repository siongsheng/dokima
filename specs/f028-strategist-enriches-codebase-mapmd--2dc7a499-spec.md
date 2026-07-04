# F028: Strategist enriches codebase-map.md during normal feature planning — appends architecture decisions and agent guidance discovered during exploration. Map accumulates real-world rationale across features with zero extra LLM calls.

Now I have full context on the dokima project. Let me produce the complete corrected spec for F028.
    
    Position: F028 is a mechanism to persist strategist architectural discoveries into codebase-map.md during normal feature planning — same session, same token budget, zero extra calls. (High confidence)
    
    
    
    
    
    feature: F028
    title: Strategist enriches codebase-map.md during normal feature planning
    status: spec-complete
    confidence: High
    impact: LOW
    
    
    Executive Summary
    
    The strategist currently reads codebase-map.md to understand the codebase, but
    the architectural discoveries it makes during exploration are lost after the
    spec is written. F028 extends the codebase-map.md format with two persistent
    sections — ## Architecture Decisions and ## Agent Guidance — that the strategist
    appends to during its normal exploration. generate_codebase_map() preserves
    these sections across regenerations. The knowledge accretes across features
    organically, improving agent context for every subsequent pipeline run, with
    zero additional LLM calls — the strategist writes down what it already learns.
    
    Constitution Check
    
    Axiom: Solves user's own pain?
    Status: YES — Shaun runs dokima on multiple repos; agents re-discover the
      same architecture each time
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: YES — ~120 LOC, 4 tasks, one session
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A — internal tool improvement
    ────────────────────────────────────────
    Axiom: Tech stack boring and proven?
    Status: YES — Python stdlib, file I/O, no new dependencies
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories?
    Status: YES — no AI buzzwords, pure engineering
    
    1. Decision Table
    
    Option: A: Separate enrichment file
    Mechanism: Strategist writes to specs/codebase-map-enriched.md; map hint
      links both
    Preservation: Trivial — separate file, never overwritten
    Complexity: Medium — two files to maintain, agents must read both
    Verdict: Reject
    ────────────────────────────────────────
    Option: B: Append-only log (ADR-like)
    Mechanism: New section in codebase-map.md; strategist appends;
      generate_codebase_map preserves it
    Preservation: Requires preservation logic in generate_codebase_map
    Complexity: Low — single file, single preservation pass
    Verdict: Accept
    ────────────────────────────────────────
    Option: C: Inline annotations in Domain Map
    Mechanism: Strategist adds comments after file descriptions in Domain Map
    Preservation: Nearly impossible — generate_codebase_map rewrites every
      line
    Complexity: High — fragile, parsing nightmare
    Verdict: Reject
    
    Decision: Option B — append-only sections preserved across map regeneration.
    Single file, minimal code change, zero ambiguity about what's machine-generated vs
    agent-discovered.
    
    2. Impact
    
    LOW — no change to pipeline execution, no new subprocess calls, no API surface
    changes. The strategist already reads codebase-map.md (lines 1433-1435 of
    pipeline.py). F028 only adds write-back instructions and a preservation pass in
    generate_codebase_map. Existing tests continue to pass. The map file grows by
    ~200-500 bytes per feature with architectural notes — negligible.
    
    Affected files (from git diff analysis):
    - utils.py (+25/-3): generate_codebase_map preserves enrichment sections
    - pipeline.py (+8/-2): strategist prompt gains enrichment instructions
    - tests/test_codebase_map.py (+60/-0): preservation + enrichment tests
    
    3. What Changed
    
    - utils.py — generate_codebase_map() reads existing ## Architecture Decisions
      and ## Agent Guidance sections before regeneration, appends them after the ##
      Test Map section in the new output. New helper _extract_enrichments().
    - pipeline.py — _make_map_hint() mentions enrichment sections when they
      exist. Strategist prompt (lines 1431-1527) gains EXISTING KNOWLEDGE
      ENRICHMENT block instructing the strategist to append discoveries.
    - tests/test_codebase_map.py — new tests: enrichment preservation across
      full/incremental regeneration, empty enrichment sections, malformed
      enrichment passthrough, strategist append format validation.
    
    4. Confidence
    
    (High) — the mechanism is purely additive: preserve two sections during
    file regeneration. The existing codebase-map.md format (4 sections) is stable
    (F027, PR #60). The strategist already has read access to codebase-map.md —
    adding write-back is a prompt change plus a preservation pass.
    
    5. API/Interface
    
    N/A — no API, no CLI flags, no data structure changes. This is internal behavior:
    the codebase-map.md file gains two optional sections that persist across
    regenerations.
    
    6. Security
    
    N/A — no attack surface change. The strategist writes to a file it already has
    access to (project directory). No new credentials, network calls, or user input
    surfaces. The preservation logic reads and writes the same file it always has.
    
    7. Documentation
    
    AGENTS.md: add one sentence about codebase-map.md enrichment sections ("The
    Architecture Decisions and ## Agent Guidance sections persist across map
    regeneration — agents append discoveries during exploration").
    
    8. Feature Breakdown — Task Breakdown
    
    Task 1: Implement enrichment preservation in generate_codebase_map
    Files: utils.py
    Dependencies: [none]
    Parallelizable: yes
    Description: Add _extract_enrichments() helper that reads existing codebase-map.md and extracts ## Architecture Decisions and ## Agent Guidance sections. Modify generate_codebase_map() to call it before writing and append preserved sections after ## Test Map. Handle: no existing map, sections missing, sections empty, malformed markdown.
    
    Task 2: Update strategist prompt with enrichment instructions
    Files: pipeline.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Add EXISTING KNOWLEDGE ENRICHMENT block to run_phase1_strategist() prompt (after line 1435, before FIRST step). Block instructs: as you explore, if you discover non-obvious architecture (e.g., "pipeline.py _IMPORTING_PANEL is set by conftest, not main()"), append it under ## Agent Guidance. Format: ### <discovery title>, then one sentence. Do not duplicate existing entries. Keep under 80 chars per line.
    
    Task 3: Update _make_map_hint to mention enrichments
    Files: pipeline.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Extend _make_map_hint() to check for ## Agent Guidance and ## Architecture Decisions sections. When present, extend the hint string to mention "and agent-discovered architecture notes" so strategists know to read those sections. Keep hint compact — under 400 chars total.
    
    Task 4: Write enrichment preservation tests
    Files: tests/test_codebase_map.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Add tests: (1) enrichment sections survive full regeneration, (2) enrichment sections survive incremental regeneration, (3) empty enrichment sections don't crash, (4) missing enrichment sections produce valid map, (5) strategist can append new entries without duplicating existing ones, (6) malformed markdown in enrichment sections is preserved verbatim.
    
    9. Data Model
    
    codebase-map.md format (extended)
    
    
    Project: dokima
    Tech: Python 3.6+
    Generated: 2026-07-04 14:35:53 (incremental | 86 files)
    
    Start Here
    ...existing...
    
    Domain Map
    ...existing...
    
    Impact Map
    ...existing...
    
    Test Map
    ...existing...
    
    Architecture Decisions
    > Machine-generated. Strategists: append new decisions below. Do NOT edit
    > existing entries — future strategists need to see the full history.
    
    AD-001: Pipeline module uses conftest._load_panel() for test injection
    pipeline.py sets _IMPORTING_PANEL = None at module level. Tests call
    conftest._load_panel() which sets it to the imported dokima module. Never
    import pipeline._IMPORTING_PANEL directly — always go through conftest.
    
    AD-002: _safe_run uses shlex.split(), not shell=True
    All subprocess calls MUST use list-based argument syntax. shell=True and
    os.system() are banned. See conventions.md.
    
    Agent Guidance
    > Machine-generated. Strategists: append guidance below. One sentence per entry.
    > Format: ### <topic> — <guidance>
    
    HERMES_BIN — always use --yolo flag
    Spawn commands need --yolo to skip interactive confirmation on the agent side.
    
    GitHub token — never passed as CLI flag
    GH_TOKEN is set via environment variable. Never use gh auth login or pass
    tokens as command-line arguments.
    
    
    .map-cache.json (unchanged)
    
    No changes. The cache only tracks file hashes and descriptions for the
    auto-generated sections. Enrichment sections are text-based and preserved
    by reading the old map before writing the new one.
    
    10. COTS Build-vs-Buy
    
    Component: Markdown parsing
    Decision: Build
    Justification: Trivial regex — re.search(r'^## Architecture
      Decisions\n(.*?)(?=\n##
    Column 4: \Z)', content, re.DOTALL)
    ────────────────────────────────────────
    Component: File I/O
    Decision: Stdlib
    Justification: open(), os.path.exists() — already used throughout
    Column 4:
    ────────────────────────────────────────
    Component: Hash comparison
    Decision: Stdlib
    Justification: hashlib.md5 — already used in generate_codebase_map
    Column 4:
    
    Everything is build. Zero new dependencies. All Python stdlib.
    
    11. Test Plan
    
    Happy Path
    - Enrichment preservation across full regeneration: Write a codebase-map.md
      with ## Architecture Decisions and ## Agent Guidance sections. Run
      generate_codebase_map(full=True). Assert both sections appear verbatim in
      the output, after ## Test Map.
    - Enrichment preservation across incremental regeneration: Same as above but
      full=False with no file changes. Assert map is NOT regenerated (returns False),
      so enrichments are untouched.
    - Strategist appends new entry: Write a codebase-map.md with one entry in
    Agent Guidance. Simulate strategist appending a second entry. Run
      generate_codebase_map(full=True). Assert BOTH entries appear.
    
    Edge Cases
    - No enrichment sections exist: Current behavior — map works fine without them.
    - Empty enrichment sections: ## Architecture Decisions followed by
      ## Test Map with nothing in between. Preservation picks up empty string,
      still writes it.
    - Enrichment section is first/last section: Parsing should handle sections
      at any position in the file.
    - Very large enrichment sections: A single entry can be up to 500 chars.
      Multiple entries across many features could be 5KB+. Regex + string concatenation
      handles this fine.
    
    Failure Modes
    - Corrupted map file (not valid markdown): _extract_enrichments() returns
      empty string. Map regenerates without enrichments. Non-fatal — enrichments
      are lost but pipeline continues.
    - File read permission error: _extract_enrichments() catches OSError,
      returns empty string. Map regenerates without enrichments.
    - Unicode in enrichment sections: Python 3 handles UTF-8 natively. No
      special handling needed — read and write as-is.
    
    Contract Invariants
    - generate_codebase_map() MUST produce valid markdown with exactly these
      sections in order: Start Here, Domain Map, Impact Map, Test Map, [Architecture
      Decisions], [Agent Guidance]. Last two are optional.
    - Enrichment sections are preserved VERBATIM — no parsing, no reformatting, no
      truncation. The strategist owns the content.
    - If _extract_enrichments() fails, the map regenerates WITHOUT enrichment
      sections — it never crashes or produces partial content.
    - The map hint in _make_map_hint() is best-effort — if the map is corrupted,
      it returns empty string (existing behavior).
    
    12. Panel Split
    
    All 4 tasks share no files in their primary modifications:
    - Task 1: utils.py (new helper + preservation logic)
    - Task 2: pipeline.py (strategist prompt)
    - Task 3: pipeline.py (map hint) — shares pipeline.py with Task 2 but touches
      different function (_make_map_hint vs run_phase1_strategist prompt string)
    - Task 4: tests/test_codebase_map.py (tests)
    
    Wave 1 (parallel): Tasks 1, 2, 3 can run simultaneously. Tasks 2 and 3
    touch different functions in pipeline.py with minimal overlap risk.
    Wave 2 (sequential): Task 4 after Task 1 — needs the implementation to
    test against.
    
    Coder count: 2 — Wave 1 with 2 coders (one on utils.py, one on pipeline.py),
    Wave 2 with 1 coder (tests).
    
    13. Build & Deploy
    
    No new deployment steps. Existing pipeline:
    bash
    python3 -m py_compile dokima        # Lint
    python3 -m pytest tests/ -q         # Test (679 tests, 6 skipped)
    
    
    The codebase-map.md is a project artifact, not a deployed file. No CI changes.
    
    14. Risk Register
    
    Risk: Strategist writes malformed markdown that breaks map parsing
    Severity: LOW
    Mitigation: _extract_enrichments() preserves verbatim — no parsing.
      generate_codebase_map() writes enrichments AFTER all auto-generated
      sections, so broken enrichments don't break the structured sections.
    Trigger: Human review of map shows garbled sections
    ────────────────────────────────────────
    Risk: Enrichment sections grow unboundedly
    Severity: LOW
    Mitigation: No enforcement in F028. Future feature could add "keep last N
      entries" or timestamp-based pruning.
    Trigger: Map exceeds 50KB
    ────────────────────────────────────────
    Risk: Strategy prompt change causes DAG format regression
    Severity: MEDIUM
    Mitigation: The prompt change is additive — it appends an instruction
      block, doesn't modify existing format instructions. Tests for DAG format
      already exist (test_dag_format.py).
    Trigger: DAG re-prompt fires on next pipeline run
    ────────────────────────────────────────
    Risk: generate_codebase_map() preservation conflicts with incremental
      no-change detection
    Severity: LOW
    Mitigation: The changed flag is set by file hash comparison. Enrichment
      preservation is a post-processing step on the output string — it doesn't
      affect the change detection logic.
    Trigger: Map regenerates when it shouldn't
    
    15. Anti-Creep
    
    Features explicitly NOT in scope:
    - ❌ No enrichment entry deduplication — the strategist is told "do not duplicate"
      but the code doesn't enforce it
    - ❌ No pruning/expiry of old enrichment entries
    - ❌ No enrichment entries in .map-cache.json (cache tracks source files only)
    - ❌ No enrichment during coder or tech-lead phases — strategist only
    - ❌ No enrichment for non-dokima projects — generate_codebase_map() is
      project-agnostic, enrichment preservation works everywhere, but the prompt
      instruction only ships for dokima's strategist
    - ❌ No ADR integration — enrichment sections are markdown text in codebase-map.md,
      not linked to the ADR directory or tool
    - ❌ No metrics/dashboard showing enrichment count or growth rate
    
    16. Sign-Off Checklist
    
    - [ ] Constitution check passes all 5 axioms
    - [ ] Impact section specifies affected files with line counts
    - [ ] What Changed lists every modified file with what changes
    - [ ] Task breakdown uses ### Task N: format with all 5 required fields
    - [ ] Test plan covers happy path, edge cases, failure modes, and invariants
    - [ ] No new dependencies — all Python stdlib
    - [ ] No API surface changes
    - [ ] Security section confirms no attack surface change
    - [ ] Anti-creep lists what NOT to build
    - [ ] Build & Deploy section confirms existing pipeline unchanged
    - [ ] Risk register covers top 4 risks with triggers
    - [ ] Ponytail guard: rung 7 — all built, no overengineering