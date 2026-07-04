# F028: Strategist enriches codebase-map.md during normal feature planning — appends architecture decisions and agent guidance discovered during exploration. Map accumulates real-world rationale across features with zero extra LLM calls.

Now I have full context. Let me produce the complete corrected F028 spec with all three missing sections added. Here's the complete spec:
    
    
    
    F028: Strategist enriches codebase-map.md during normal feature planning — appends architecture decisions and agent guidance discovered during exploration. Map accumulates real-world rationale across features with zero extra LLM calls.
    
    Position: SINGLE APPROACH — Add a preserved "Agent Guidance" section to codebase-map.md that survives regeneration. Strategist outputs architecture discoveries inline in its spec; pipeline's phase 1 extracts them and writes to codebase-map.md. Zero extra LLM calls — enrichment is a byproduct of existing codebase exploration. (High confidence)
    
    Version: 1.0
    Status: Ready for Implementation
    Feature ID: F028
    Dependencies: F027 (done — generate_codebase_map() at utils.py:1490 produces 4-section format; map injected into strategist prompt at pipeline.py:1435)
    
    Confidence: (High)
    Impact: (MEDIUM)
    
    
    
    1. Executive Summary
    
    Add a persisted Agent Guidance section to codebase-map.md that accumulates architecture decisions, gotchas, patterns, and file-relationship insights discovered by the strategist during normal feature planning. The section survives full regeneration of the map — generate_codebase_map() preserves it between <!-- BEGIN PERSISTENT --> and <!-- END PERSISTENT --> markers. The strategist already reads this map as step 0 of planning (pipeline.py:1437); now it also writes back discoveries. The pipeline's run_phase1_strategist() extracts an ## Agent Guidance block from the strategist's spec output and appends it to codebase-map.md. Zero extra LLM calls — enrichment is a natural byproduct of the existing codebase exploration step. Estimated 3 tasks, ~180 LOC, 1 wave.
    
    
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Result: ✓ — Agents waste tokens re-discovering the same architecture patterns on every feature. utils.py is imported by all modules (Impact Map already shows this, but the IMPLICATIONS aren't captured). Strategist currently explores codebase in Phase 1 and then discards all its insights.
    
    Axiom: Weekend-buildable?
    Result: ✓ — ~180 LOC. One new function in utils.py (preserve + append), one new extraction step in pipeline.py, one test file update.
    
    Axiom: Boring and proven?
    Result: ✓ — HTML-comment markers for persistent sections is the oldest templating pattern (WordPress shortcodes, Jekyll frontmatter, Hugo shortcodes). String extraction from LLM output already exists in extract_file_paths(). No new frameworks.
    
    Axiom: Avoids AI hype?
    Result: ✓ — No AI features. Pure string templating + pipeline plumbing.
    
    Axiom: Evidence people will pay?
    Result: N/A — internal tooling. Payoff: each subsequent feature runs faster because the strategist has richer context without re-exploring.
    
    Verdict: PASS. No misalignments.
    
    
    
    3. Ponytail Guard — Pre-Spec Review
    
    Rung 1: Does this need to exist?
    Check: grep -rl "Agent Guidance\|PERSISTENT\|survives regeneration" utils.py pipeline.py
    → Zero matches. Current codebase-map.md is fully regenerated every time — all non-structured content is lost. The strategist explores the codebase on every feature and then discards insights.
    Result: Yes.
    
    Rung 2: Already in codebase?
    Check: generate_codebase_map() at utils.py:1490 writes map_content as a single f-string at line 1625. No preservation logic. run_phase1_strategist() at pipeline.py:1381 spawns strategist, captures output, writes spec file — no extraction of architecture insights.
    Result: No.
    
    Rung 3: Stdlib does it?
    Check: re (marker extraction), os (file IO), string (templating). All stdlib.
    Result: Rung 7 — build it, but minimal.
    
    Spec needed: Yes.
    Spec scope: Preservation logic in generate_codebase_map(), extraction logic in run_phase1_strategist(), test updates.
    
    
    
    4. Decision Table
    
    Option: A: Strategist writes directly to codebase-map.md via tool call
    Complexity: Medium — strategist needs file-write tool, fragile
    Persistence: Good
    LLM Cost: Extra tool call = extra LLM cost
    Verdict: Reject
    ────────────────────────────────────────
    Option: B: Pipeline extracts Agent Guidance from strategist spec output,
      appends to codebase-map.md
    Complexity: Low — pipeline already writes files
    Persistence: Good — same file
    LLM Cost: Zero — inline in spec output
    Verdict: Accept
    ────────────────────────────────────────
    Option: C: Separate .map-notes.md file
    Complexity: Medium — new file, new injection points
    Persistence: Good
    LLM Cost: Zero
    Verdict: Reject — fragments map into multiple files
    
    Decision: Option B. The strategist already produces a spec with sections. Adding an ## Agent Guidance section to its output costs nothing. The pipeline already reads and writes the spec file — extracting one more section is trivial. The generate_codebase_map() function already writes the map — preserving a marked section is a 20-line addition.
    
    
    
    5. ## 3. Impact
    
    All subsequent feature pipelines benefit from accumulated architecture knowledge without re-exploring the codebase. The strategist, coder, and tech-lead all read codebase-map.md as step 0 — the Agent Guidance section gives them:
    
    - File relationship gotchas (e.g., "utils.py is imported by EVERY module — changes require full test suite")
    - Architecture patterns (e.g., "Pipeline phases are 1→2→5 with phases 3-4 as deep-gating variants")
    - Anti-patterns (e.g., "Never add shell=True to subprocess calls — banned by conventions.md, enforced by security tests")
    - Module coupling warnings (e.g., "agent.py and pipeline.py share spawn_agent() — changes to the signature must update both")
    
    These insights are currently lost after every strategist session. With F028, they accumulate across features, making each subsequent pipeline faster and more accurate. The map becomes a living document of the codebase's real-world behavior — not just its static structure.
    
    Measurable impact: Strategist codebase exploration step shrinks over time as the Agent Guidance section grows — fewer files to re-read because prior strategists already captured the non-obvious patterns.
    
    
    
    6. ## 4. What Changed
    
    - utils.py:generate_codebase_map() (+30/-5) — Read old map's Agent Guidance section before regeneration, append it to new map between <!-- BEGIN PERSISTENT --> / <!-- END PERSISTENT --> markers. Helpers: _extract_persistent_guidance(old_content) and _append_guidance(map_content, guidance).
    - pipeline.py:run_phase1_strategist() (+25/-2) — After strategist produces spec at specs/<feature-slug>-spec.md, extract the ## Agent Guidance section (if present) and call _enrich_codebase_map() to append it to codebase-map.md.
    - pipeline.py (new helper) (+35) — _enrich_codebase_map(project_dir, guidance_text) reads existing codebase-map.md, finds the <!-- BEGIN PERSISTENT --> / <!-- END PERSISTENT --> markers, appends new entries with date+feature stamps, writes back.
    - tests/test_codebase_map.py (+60/-0) — Tests: guidance survives full regeneration, multi-feature guidance accumulation, empty guidance handled gracefully, marker integrity.
    - specs/codebase-map.md (structure change) — New ## Agent Guidance section with persistent markers. Auto-generated on first F028 run; thereafter preserved.
    
    
    
    7. Feature Breakdown
    
    Task 1: Add persistent guidance section preservation to generate_codebase_map()
    Files: utils.py
    Dependencies: [none]
    Parallelizable: yes
    Description: Add _extract_persistent_guidance(old_content) helper that reads the old codebase-map.md and extracts content between <!-- BEGIN PERSISTENT --> and <!-- END PERSISTENT --> markers in the ## Agent Guidance section. Modify generate_codebase_map() to call this before regenerating, then append the preserved guidance to the new output after the Test Map section. Add ## Agent Guidance section header before markers on first generation. If old map doesn't exist or has no markers, guidance is empty — no error.
    
    Task 2: Extract Agent Guidance from strategist spec output and append to codebase-map.md in run_phase1_strategist()
    Files: pipeline.py
    Dependencies: [none]
    Parallelizable: yes
    Description: After strategist writes spec file (line ~1407 in run_phase1_strategist), parse the spec for a ## Agent Guidance section. If found, extract the bullet items. Call new _enrich_codebase_map(project_dir, guidance_items) helper that reads codebase-map.md, finds the persistent markers, appends new items with - [F###] <date>: <guidance> stamp format, deduplicates against existing items (exact match), and writes back. If spec has no Agent Guidance section, skip silently — not an error. Helper also validates that markers exist (recovery: if map has no markers, add them around existing content).
    
    Task 3: Add test coverage for guidance preservation and extraction
    Files: tests/test_codebase_map.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Add tests: (a) guidance survives full regeneration — write map with Agent Guidance section, regenerate full=True, verify guidance preserved, (b) multi-feature accumulation — simulate two features writing guidance, verify both appear deduplicated, (c) empty guidance on first generation — no old map, verify guidance section created with empty markers, (d) no markers recovery — map without markers gets markers added, (e) deduplication — same guidance written twice only appears once. Use existing tmp_project fixture.
    
    
    
    8. Data Model
    
    codebase-map.md gains a 5th section:
    
    
    Agent Guidance
    <!-- BEGIN PERSISTENT -->
    - [F028] 2026-07-04: utils.py is imported by ALL modules (pipeline, agent, roadmap, tasks) — changes require full test suite; python3 -m pytest tests/ -q minimum
    - [F028] 2026-07-04: pipeline.py _make_map_hint() at line 50 checks for codebase-map.md existence — removing the file won't crash the pipeline but agents lose context
    - [F029] 2026-07-05: scripts/cli-help.json is the single source of truth for CLI docs — changes to argparse must update this file or Vercel build shows stale docs
    <!-- END PERSISTENT -->
    
    
    Format rules:
    - Each entry: - [F###] YYYY-MM-DD: <single sentence of guidance>
    - The [F###] stamp comes from the feature being planned
    - Date is the pipeline run date (UTC)
    - Content is one sentence — actionable, specific, grounded in file paths
    - Deduplication: exact match on the content after - [F###] YYYY-MM-DD: 
    - Markers <!-- BEGIN PERSISTENT --> and <!-- END PERSISTENT --> define the preserved region
    - Everything between markers survives full regeneration
    - Everything outside markers is regenerated by generate_codebase_map()
    
    No new files. No new cache entries. The persistence lives entirely in codebase-map.md's marker-delimited section.
    
    
    
    9. API Routes
    
    N/A — CLI tool, no API surface.
    
    
    
    10. Component Tree
    
    N/A — Python CLI, no frontend.
    
    
    
    11. COTS Build-vs-Buy
    
    Component: Marker-based persistence
    Decision: Build
    Justification: HTML comments + regex — 20 lines, stdlib only
    ────────────────────────────────────────
    Component: Guidance extraction
    Decision: Build
    Justification: Existing extract_file_paths() pattern at utils.py:1365 —
      same approach for ## Agent Guidance
    ────────────────────────────────────────
    Component: Deduplication
    Decision: Build
    Justification: set() comparison on guidance content strings — 5 lines
    ────────────────────────────────────────
    Component: Strategist guidance output
    Decision: Build
    Justification: Prompt addition: "Include ## Agent Guidance section with
      architecture insights" — no new tool calls
    
    All build. Zero new dependencies.
    
    
    
    12. Test Plan (MANDATORY)
    
    Task 1 — Map Preservation
    
    Happy path: Generate map with Agent Guidance section containing 2 entries and markers. Run generate_codebase_map(full=True). Verify output contains both guidance entries intact between markers. Other sections (Domain Map, Impact Map, Test Map) are regenerated with fresh data.
    
    Edge cases: 
    - Old map has no ## Agent Guidance section → new map creates one with empty guidance between markers
    - Old map has markers but no content between them → preserved as-is (empty)
    - Old map has malformed markers (only BEGIN, no END) → treat everything after BEGIN as preserved until EOF; add END marker before new content
    - Old map doesn't exist at all (first run) → create fresh map with empty Agent Guidance section
    - Guidance content contains special regex characters (*, [, ], () → escaped correctly, preserved literally
    
    Failure modes:
    - File read error on old map → skip preservation, generate fresh (graceful degradation)
    - File write error on new map → raise, pipeline handles via existing error recovery
    - Unicode in guidance content → preserved correctly (UTF-8)
    
    Contract invariants:
    - After regeneration: <!-- BEGIN PERSISTENT --> and <!-- END PERSISTENT --> always present in ## Agent Guidance section
    - Content between markers is never modified by generate_codebase_map()
    - Content outside markers is always regenerated
    
    Task 2 — Spec Extraction
    
    Happy path: Strategist outputs spec with ## Agent Guidance section containing 2 bullet items. Pipeline extracts items, writes to codebase-map.md with [F028] 2026-07-04: prefix stamps. Verify both items appear in map between markers.
    
    Edge cases:
    - Strategist spec has no ## Agent Guidance section → skip extraction silently (not an error)
    - Strategist spec has ## Agent Guidance with zero bullets → skip (empty section)
    - Guidance item is identical to existing entry → deduplicated, not appended
    - Guidance item differs only in date prefix but same content → deduplicated (compare content after date stamp)
    - codebase-map.md doesn't exist when enrichment runs → create it via generate_codebase_map() first, then append
    - codebase-map.md exists but has no markers → inject markers around existing ## Agent Guidance or add section with markers
    
    Failure modes:
    - Spec file not found after strategist run → skip enrichment (strategist may have failed)
    - Spec file is empty → skip enrichment
    - codebase-map.md is write-locked → log warning, don't crash pipeline
    - Guidance extraction regex doesn't match → skip silently (strategist used wrong format)
    
    Contract invariants:
    - Enrichment is ALWAYS best-effort — never blocks pipeline completion
    - Each enrichment appends, never overwrites existing preserved guidance
    - Enrichment always includes feature stamp and date
    
    Task 3 — Test Coverage
    
    Happy path: All 5 tests pass with python3 -m pytest tests/test_codebase_map.py -v -k guidance. Existing 14 tests still pass.
    
    Edge cases:
    - test_guidance_survives_full_regeneration: Set up map with guidance, run full=True regeneration, assert guidance present + other sections regenerated
    - test_multi_feature_accumulation: Simulate 3 features writing guidance, verify all 3 appear, verify deduplication of repeats
    - test_empty_guidance_first_generation: Fresh project, generate map, verify markers exist with empty content
    - test_no_markers_recovery: Write map without markers, run enrichment, verify markers added
    - test_deduplication_exact_match: Write same guidance twice, verify only one copy
    
    Failure modes: None expected — deterministic string operations.
    
    Contract invariants: New tests don't break existing tests. Test count increases by 5.
    
    
    
    13. Panel Split
    
    
    Wave 1 (parallel): Task 1 (utils.py) + Task 2 (pipeline.py)
      → 2 coders, 2 different files, zero overlap
    Wave 2 (sequential): Task 3 (tests/test_codebase_map.py)
      → depends on Task 1 for stable format; Task 2 doesn't affect test codebase_map tests
    
    
    2 waves, up to 2 parallel coders in wave 1.
    
    
    
    14. Build & Deploy
    
    - CI: python3 -m pytest tests/test_codebase_map.py -v covers all changes; full python3 -m pytest tests/ -q for regression
    - Deploy: No deployment — this is a dev tool improvement. Takes effect on next dokima next or dokima --release
    - Env vars: None new
    - Backward compatibility: Full. Old codebase-map.md without Agent Guidance section gets it added on first F028-enriched pipeline run. Old map without markers gets markers injected. If F028 code is reverted, the Agent Guidance section is simply regenerated away on next full map build — data loss but no crash.
    - Skill update: The spec-strategist-lite SKILL.md needs a new instruction: "Include ## Agent Guidance section with architecture insights discovered during exploration." This is a separate follow-up change — the strategist prompt in pipeline.py:1433 already includes instructions we can extend inline.
    
    
    
    15. Risk Register
    
    #: 1
    Risk: Strategist fills Agent Guidance with low-quality/noisy entries that
      bloat the map
    Severity: MEDIUM
    Mitigation: Prompt constraint: "Max 5 bullets. Each must cite a specific
      file + line number + actionable insight. Skip obvious patterns."
      Pipeline truncates guidance section at 50 entries (FIFO eviction).
    Trigger: Strategist runs on >50 features
    ────────────────────────────────────────
    #: 2
    Risk: Marker corruption (manual edit breaks <!-- BEGIN PERSISTENT -->)
    Severity: LOW
    Mitigation: Marker check on every write — if markers missing, inject them.
      If malformed (only one marker), repair by adding the missing one.
    Trigger: User manually edits codebase-map.md
    ────────────────────────────────────────
    #: 3
    Risk: Guidance section grows too large for agent context windows
    Severity: LOW
    Mitigation: The map is referenced by path, not inlined — agents read it as
      a file, not as prompt text. Context window not affected. If map >100KB,
      truncate guidance section in _make_map_hint() to last 20 entries.
    Trigger: Map exceeds 100KB
    ────────────────────────────────────────
    #: 4
    Risk: Spec extraction regex misses Agent Guidance section due to format
      variations
    Severity: LOW
    Mitigation: Use flexible regex: match ## Agent Guidance header, then
      capture all - bullet lines until next ## section header. Fall through
      gracefully — no crash, just skip.
    Trigger: Strategist uses non-standard bullet format
    ────────────────────────────────────────
    #: 5
    Risk: generate_codebase_map() writes map while _enrich_codebase_map() is
      reading it
    Severity: LOW
    Mitigation: Both operations are sequential in the pipeline — map
      generation finishes before phase 1 enrichment. No concurrency risk.
    Trigger: Future parallel pipeline changes
    
    
    
    16. Anti-Creep
    
    Explicitly NOT in scope:
    
    - ❌ Agent Guidance for coder or tech-lead phases — strategist-only enrichment. Coder and TL are consumers, not producers
    - ❌ LLM-based guidance summarization or curation — zero extra LLM calls is the design constraint
    - ❌ Guidance quality scoring or voting — entries are append-only, oldest evicted first
    - ❌ Cross-project guidance sharing — guidance is per-project, scoped to codebase-map.md
    - ❌ Guidance search or indexing — agents read the file directly
    - ❌ Auto-pruning stale guidance (e.g., "this was fixed in F035") — human cleanup via normal map regeneration
    - ❌ Guidance import/export or migration between machines
    - ❌ Real-time guidance updates during coder phase — map is written once per pipeline at phase 1
    - ❌ Guidance section in coder worktree copies — worktree copies use the parent repo's map; no sync needed
    
    
    
    17. Sign-Off Checklist
    
    - [ ] Constitution check passed — all 5 axioms YES
    - [ ] Decision table reviewed — Option B (pipeline extraction) selected, Option A (direct write) and Option C (separate file) rejected
    - [ ] ## N. Impact section present and grounded in actual file paths
    - [ ] ## N. What Changed section present with specific files + estimated LOC
    - [ ] All 3 tasks have ### Task N: headers with ALL five fields (Files, Dependencies, Parallelizable, Description)
    - [ ] Panel Split shows 2 waves with file isolation verified: Task 1 (utils.py) + Task 2 (pipeline.py) = no overlap
    - [ ] Test Plan covers happy path, edge cases, and failure modes for each of 3 tasks
    - [ ] Risk Register covers 5 risks with severity + mitigation + trigger
    - [ ] Anti-Creep lists 9 exclusions
    - [ ] No new dependencies — re, os, string are all stdlib
    - [ ] Backward compatibility confirmed — old maps without markers get them injected; old maps without Agent Guidance section get it added
    - [ ] Zero extra LLM calls confirmed — strategist outputs Agent Guidance inline in its spec; pipeline extracts and writes
    
    
    
    Confidence: (High)
    Impact: (MEDIUM) — All 3 agent roles benefit from accumulated architecture knowledge. Each subsequent feature pipeline has richer context without re-exploring the codebase. No breaking changes, no new dependencies.