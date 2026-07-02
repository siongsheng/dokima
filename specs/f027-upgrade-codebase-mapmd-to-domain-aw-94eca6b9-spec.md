# F027: Upgrade codebase-map.md to domain-aware format with Start Here, Domain Map, Impact Map, and Test Map sections. Inject map into strategist, coder-worktree, and tech-lead prompts.

Now I have full understanding. Let me output the complete corrected spec. The spec-strategist-lite skill mandates all 13 sections, plus the strategist prompt's required sections (Impact, What Changed, Confidence/Impact markers, etc.).
    
    
    
    Position: SINGLE APPROACH — inline format change in generate_codebase_map() + prompt injection in 3 pipeline phases. No new module needed. (High confidence)
    
    F027: Upgrade codebase-map.md to Domain-Aware Format + Prompt Injection
    
    1. Executive Summary
    
    Upgrade specs/codebase-map.md from a flat file tree to a domain-aware 4-section format (Start Here, Domain Map, Impact Map, Test Map) that agents can use to understand the codebase without reading every file. Inject the map into strategist, coder-worktree, and tech-lead prompts so all 3 roles share the same codebase understanding. This is a format change + prompt injection — no new architecture, no new dependencies. Estimated: 4 tasks, ~350 LOC, 1 wave of parallel work.
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Result: ✓ — agents currently waste tokens re-discovering codebase
      structure on every feature. 547-line coder prompt already hints at map;
      this extends it to all roles.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Result: ✓ — P0 ships in one session: format change + 3 injection points.
    ────────────────────────────────────────
    Axiom: Evidence of need?
    Result: ✓ — F026 already auto-generates codebase-map on release. F027 is
      the logical next step: make the map actually useful.
    ────────────────────────────────────────
    Axiom: Boring/Proven stack?
    Result: ✓ — Python string templating, no new frameworks.
    ────────────────────────────────────────
    Axiom: Avoids AI hype?
    Result: ✓ — No AI features. Pure format change + prompt engineering.
    
    3. Decision Table
    
    SINGLE APPROACH: Modify generate_codebase_map() output format to 4 sections. Inject map path into strategist, coder, and tech-lead prompts. No new functions, no new files. Tests update to match new format.
    
    4. Impact
    
    Agents (strategist, coder, tech-lead) share a common codebase map that categorizes files by domain, shows impact relationships, and maps tests to source. Reduces token waste from redundant codebase exploration. Strategist gains architectural context for better task decomposition. Tech Lead gains domain map for faster adversarial review. Coder already had map hint — format upgrade makes it more useful.
    
    5. What Changed
    
    - utils.py:generate_codebase_map() — output 4-section format (Start Here, Domain Map, Impact Map, Test Map) instead of flat Tree + Commands
    - pipeline.py:run_phase1_strategist() — inject codebase-map.md path reference into strategist prompt
    - pipeline.py:run_phase2_coder() — update existing map_hint to reference new sections
    - pipeline.py:run_phase5_tech_lead() — inject codebase-map.md path reference into tech-lead prompt
    - tests/test_codebase_map.py — update format expectations + new domain-section tests
    
    6. Feature Breakdown
    
    Task 1: Upgrade codebase-map.md format to 4 domain-aware sections
    - Files: utils.py
    - Dependencies: none
    - Parallelizable: yes
    - Estimated LOC: ~120
    - Description: Replace the flat Tree + Commands format in generate_codebase_map() with 4 sections: Start Here (project summary + commands), Domain Map (files grouped by purpose — Pipeline, Agent, Tasks, Utils, Roadmap, Status), Impact Map (which files affect which — derived from import analysis), Test Map (test files matched to source modules). Keep all existing features: incremental mode, cache, tech detection, file descriptions.
    
    Task 2: Inject codebase map into strategist, coder, and tech-lead prompts
    - Files: pipeline.py
    - Dependencies: none
    - Parallelizable: yes
    - Estimated LOC: ~80
    - Description: Add codebase-map.md reference to strategist prompt (run_phase1_strategist, line ~1416) — tell strategist to read it as step 0 before codebase exploration. Update existing coder map hint (run_phase2_coder, line ~547) to reference new section names. Add map hint to tech-lead prompt (run_phase5_tech_lead, line ~1168) — tell TL to read map for domain context before adversarial review. All three injections use same pattern: check file exists, emit hint with path + byte size.
    
    Task 3: Update existing test expectations for new format
    - Files: tests/test_codebase_map.py
    - Dependencies: none
    - Parallelizable: yes
    - Estimated LOC: ~80
    - Description: Update all existing generate_codebase_map tests to expect the new 4-section format instead of ## Tree and ## Commands headers. Tests to update: test_map_tech_detection, test_map_commands_from_agents, test_map_includes_mdx, test_map_file_count, test_map_no_agents_md. Assert new section headers exist (## Start Here, ## Domain Map, ## Impact Map, ## Test Map). Preserve all existing assertions about content.
    
    Task 4: Add domain-aware section tests
    - Files: tests/test_codebase_map.py
    - Dependencies: Task 1, Task 3
    - Parallelizable: no
    - Estimated LOC: ~90
    - Description: Add tests for: (a) Domain Map groups files under correct domain headers (Pipeline Orchestration, Agent Management, etc.), (b) Impact Map lists file dependencies, (c) Test Map matches test files to source modules, (d) Start Here includes project description and commands, (e) backward compatibility — incremental mode regenerates all sections, (f) empty project produces valid 4-section map. Use the existing tmp_project fixture.
    
    7. Data Model
    
    No persistent data changes. specs/codebase-map.md format changes from:
    
    
    Project: dokima
    Tech: Python
    Generated: ...
    
    Tree
    ├── file.py  — description
    Commands
    - test: ...
    
    
    To:
    
    
    Project: dokima
    Tech: Python
    Generated: ...
    
    Start Here
    dokima is a multi-agent orchestration engine...
    - Test: ...
    - Build: ...
    - Lint: ...
    Key files: dokima, pipeline.py, utils.py
    
    Domain Map
    Pipeline Orchestration
    - pipeline.py  — 5-phase pipeline + fix mode
    Agent Management
    - agent.py  — spawn_agent, call_agent, fallback
    ...
    
    Impact Map
    pipeline.py → imports from utils, agent, tasks, roadmap, status
    utils.py → standalone (stdlib only)
    If you change utils.py: affects ALL modules — run full test suite
    ...
    
    Test Map
    tests/test_codebase_map.py → utils.py:generate_codebase_map
    tests/test_f022_pipeline.py → pipeline.py:run_phase*
    ...
    
    
    Domain Map groups are deterministic — derived from module docstrings and import patterns. Impact Map is derived from import analysis of Python files. Test Map matches test_<module>.py to <module>.py.
    
    8. API Routes
    
    N/A — CLI tool, no API surface.
    
    9. Component Tree
    
    N/A — Python CLI, no frontend.
    
    10. COTS Build-vs-Buy
    
    Component: Map generation
    Decision: Build
    Justification: Already have generate_codebase_map() — extending is cheaper
      than replacing
    ────────────────────────────────────────
    Component: Import analysis
    Decision: Build
    Justification: Use Python ast module (stdlib) to extract imports — no dep
      needed
    ────────────────────────────────────────
    Component: Prompt injection
    Decision: Build
    Justification: 3 string concatenations in existing pipeline code
    
    All build. Zero new dependencies.
    
    11. Test Plan (MANDATORY)
    
    Task 1 — Map Format
    - Happy path: generate_codebase_map(project_dir, full=True) produces a file with all 4 section headers (## Start Here, ## Domain Map, ## Impact Map, ## Test Map). Domain Map groups files by purpose. Impact Map shows dependency arrows. Test Map pairs test files to source.
    - Edge cases: Empty project (no source files) → still produces valid 4-section structure with "No source files detected" in each section. Project with only test files → Test Map populated, Domain Map has tests-only section. Single-file project → all sections valid.
    - Failure modes: Corrupt .map-cache.json → full rebuild works. File read error during import analysis → skip that file, continue. package.json unparseable → tech detection falls back to "detected at runtime".
    - Contract invariants: After generation: (a) map file exists at specs/codebase-map.md, (b) cache exists at specs/.map-cache.json, (c) file count in header matches analyzed files, (d) all 4 sections present.
    
    Task 2 — Prompt Injection
    - Happy path: After map generation, strategist prompt includes "Read specs/codebase-map.md FIRST". Coder prompt includes updated section reference. Tech-lead prompt includes "Read specs/codebase-map.md for domain context".
    - Edge cases: Map file doesn't exist → no hint injected (no crash). Map file is 0 bytes → hint omitted. Project with no specs/ directory → hint omitted.
    - Failure modes: Strategist ignores map hint → no functional impact (best-effort). Map file too large → truncated in prompt (cap at 4K chars for inline injection).
    - Contract invariants: Hint injection is always best-effort — never blocks pipeline. Map path is absolute to avoid cwd confusion.
    
    Task 3 — Existing Tests
    - Happy path: All 14 existing test_codebase_map.py tests pass with updated format expectations.
    - Edge cases: Tests that assert on ## Tree or ## Commands string literals → updated to assert on new section headers.
    - Failure modes: Missed a hardcoded string → test fails, fix and retry.
    - Contract invariants: Same test count as before. Same coverage. No test deletions — only assertion updates.
    
    Task 4 — New Tests
    - Happy path: test_domain_map_groups_files — verifies pipeline.py appears under "Pipeline Orchestration". test_impact_map_has_dependencies — verifies "pipeline.py → imports from utils" appears. test_test_map_pairs_modules — verifies test file to source mapping. test_start_here_has_commands — verifies test/build/lint commands. test_empty_project_valid_map — empty project produces all 4 sections.
    - Edge cases: Project with nested source dirs (src/core/) → Domain Map reflects hierarchy. Module with no imports → Impact Map shows "no imports detected".
    - Failure modes: Import analysis crashes on syntax error → skip file gracefully, document in map.
    - Contract invariants: New tests don't break existing tests. All tests pass with python3 -m pytest tests/test_codebase_map.py -v.
    
    12. Panel Split
    
    
    Wave 1 (parallel): Task 1 (utils.py) + Task 2 (pipeline.py) + Task 3 (tests/test_codebase_map.py)
      → 3 coders, 3 different files, zero overlap
    Wave 2 (sequential): Task 4 (tests/test_codebase_map.py)
      → depends on Task 1 + Task 3 for stable format
    
    
    2 waves, up to 3 parallel coders in wave 1.
    
    13. Build & Deploy
    
    - CI: Existing python3 -m pytest tests/ -q covers all changes
    - Deploy: No deployment — this is a format change in the dev tool itself
    - Env vars: None new
    - Backward compat: Full — old codebase-map.md is regenerated on next pipeline run or --release
    
    14. Risk Register
    
    Risk: Import analysis crashes on non-Python files
    Severity: LOW
    Mitigation: Try/except per file; skip and document
    Trigger: Corrupt .py file in project
    ────────────────────────────────────────
    Risk: Strategist prompt too long with map inline
    Severity: LOW
    Mitigation: Reference path, don't inline content
    Trigger: Map > 4K chars
    ────────────────────────────────────────
    Risk: Existing tests break on format change
    Severity: MEDIUM
    Mitigation: Task 3 updates all assertions; Task 4 adds coverage
    Trigger: Manual format deviation
    ────────────────────────────────────────
    Risk: Domain Map groups wrong for unfamiliar projects
    Severity: LOW
    Mitigation: Fallback to "Other" group for unmatched files
    Trigger: Novel project structure
    ────────────────────────────────────────
    Risk: Coder ignores new section names in prompt
    Severity: LOW
    Mitigation: Best-effort hint — coder reads file regardless
    Trigger: Agent doesn't follow instructions
    
    15. Anti-Creep
    
    Explicitly NOT in scope:
    - ❌ Auto-generating Domain Map groups via LLM — deterministic regex/ast only
    - ❌ Impact Map with transitive dependency resolution — direct imports only
    - ❌ Test Map with coverage data — file-name matching only
    - ❌ Caching domain analysis separately — reuse existing .map-cache.json
    - ❌ Injecting map into nm (adversarial reviewer) — nm uses different model family, map adds no value
    - ❌ Live-updating map on file change — incremental mode already covers this
    - ❌ Multi-language import analysis — Python ast only; other languages get filename-based grouping
    
    16. Sign-Off Checklist
    
    - [ ] Constitution check passed — all 5 axioms YES
    - [ ] Decision table reviewed — SINGLE APPROACH justified
    - [ ] What Changed section lists all modified files
    - [ ] Impact section describes user/developer benefit
    - [ ] All 4 tasks have ### Task N: headers with all 5 fields
    - [ ] Panel Split shows 2 waves with file isolation verified
    - [ ] Test Plan covers happy path, edge cases, failure modes for each task
    - [ ] Risk Register covers 5 risks with severity + mitigation
    - [ ] Anti-Creep lists 7 exclusions
    - [ ] No new dependencies — ast is stdlib, zero pip installs
    - [ ] Backward compatibility confirmed — old map regenerated on next run
    - [ ] Existing test count preserved (14 tests in test_codebase_map.py)
    
    Confidence: (High)
    Impact: MEDIUM — all 3 agent roles benefit from shared codebase understanding; no breaking changes.