# F034: dokima fix --issue N: pull GitHub issue body, extract file/line/fix/verify from structured format, spawn coder to implement. Also upgrade SHOULD FIX issue creation to include What/Fix/Verify sections for coder-readability.

Now I have full context. Let me produce the complete corrected F034 spec.
    
    
    F034: dokima fix --issue N — pull GitHub issue body, extract What/Fix/Verify, spawn coder to implement. Upgrade SHOULD FIX issue creation to include structured sections.
    
    Status: In Progress | Confidence: Medium (1 unverified assumption) | Impact: MEDIUM
    
    
    
    1. Executive Summary
    
    This feature adds dokima fix --issue N — a new mode that pulls a specific GitHub issue by number, extracts a structured fix instruction from its body (file paths, fix description, verification steps), and spawns a coder agent to implement the fix. This complements the existing dokima fix mode (which discovers BLOCKED PRs automatically) with a direct-to-issue workflow. Additionally, the SHOULD FIX issue creation in the TL review phase is upgraded from a generic ### Finding / ### Context format to a coder-actionable ### What / ### Fix / ### Verify structured format, so that issues created by the panel are immediately consumable by dokima fix --issue N. Confidence: Medium — the extraction parsing from issue body is straightforward, but one assumption needs validation: whether --issue mode should create a new branch or work on the existing feature branch. Fallback: create a fix/issue-N branch.
    
    
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Verdict: ✅ YES
    Evidence: User manually copy-pastes TL review findings into coder prompts today. dokima fix --issue N automates this loop — pull issue, extract structured instruction, spawn coder.
    ────────────────────────
    
    Axiom: Weekend-buildable?
    Verdict: ✅ YES
    Evidence: ~200 LOC across 3 files, ~4 hours. Leverages existing run_fix_mode, spawn_agent, and gh infrastructure.
    ────────────────────────
    
    Axiom: Evidence people will pay?
    Verdict: N/A
    Evidence: Internal tool feature.
    ────────────────────────
    
    Axiom: Tech stack boring/proven?
    Verdict: ✅ YES
    Evidence: Python regex + stdlib, same gh CLI patterns already used in discover_blocked_pr() and run_fix_mode(). No new dependencies.
    ────────────────────────
    
    Axiom: Avoids AI hype categories?
    Verdict: ✅ YES
    Evidence: No AI/ML — pure text parsing and subprocess orchestration.
    
    No misalignments flagged.
    
    
    
    3. Decision Table
    
    Option: Add --issue N flag to existing fix subcommand; issue body contains
      ### What / ### Fix / ### Verify sections
    Verdict: Accept
    Reasoning: Reuses existing fix-mode coder spawning + vet + nm pipeline.
      Structured issue format enables reliable extraction
    ────────────────────────────────────────
    Option: Create separate dokima issue-fix subcommand
    Verdict: Reject
    Reasoning: Fragments the CLI — fix already means "fix something broken."
      Adding --issue is a natural extension
    ────────────────────────────────────────
    Option: Extract file/line/fix from free-text issue body (no structured
      format)
    Verdict: Reject
    Reasoning: Unreliable parsing — regex extraction of file paths from free
      text is fragile. Structured format is the contract
    ────────────────────────────────────────
    Option: Have coder read the entire issue body with no extraction
    Verdict: Reject
    Reasoning: Coder prompt would be bloated with issue metadata (timestamps,
      labels, assignee). Extracted structured prompt is cleaner
    ────────────────────────────────────────
    Option: Keep current issue body format (no What/Fix/Verify upgrade)
    Verdict: Reject
    Reasoning: Issues created by TL would not be consumable by --issue mode —
      breaks the feedback loop
    
    Ponytail Guard: Rung 7 — new feature that doesn't exist yet. The existing run_fix_mode() provides the coder-spawning template; gh issue view is one CLI call. The extraction logic is new but minimal (~60 LOC).
    
    CLARIFICATION: When --issue N targets an issue on a feature branch that already exists (the issue was created by TL review of a PR), should the coder work on the existing feature branch, or create a new fix/issue-N branch?
    Assumption: Create a new fix/issue-{N} branch off the default branch. This avoids merge conflicts with the existing feature branch and follows the existing fix-mode pattern where blockers are fixed and pushed separately.
    Impact if wrong: Would need to switch to branch-from-issue-PR logic — minor change (<10 LOC in branch selection).
    
    
    
    4. Impact
    
    This feature adds a new entry point to the fix subcommand that bypasses the BLOCKED PR discovery loop and instead targets a specific GitHub issue. Affects files:
    - dokima (CLI entry point): +10 LOC — add --issue argument to fix subparser, pass issue_number to run_fix_mode()
    - pipeline.py: +80 LOC, -5 LOC — new run_fix_mode_issue(project_dir, issue_number) function that pulls issue body, extracts structured sections, spawns coder; upgrade SHOULD FIX issue body template in run_phase5_tech_lead() (lines 1396-1419)
    - tests/test_fix_mode.py: +120 LOC — new tests for --issue mode: issue body extraction, structured format parsing, coder prompt construction, edge cases (missing sections, malformed body, non-existent issue)
    - tests/test_f036_should_fix_extraction.py: +40 LOC — verify upgraded issue body format includes What/Fix/Verify sections
    
    No API change. No deployment change. One new gh subcommand call: gh issue view N --repo REPO --json body,title,labels,comments.
    
    
    
    5. What Changed
    
    CLI (dokima):
    - Add --issue N argument to the fix subparser (type=int). When --issue is provided, route to run_fix_mode_issue() instead of run_fix_mode().
    
    Pipeline (pipeline.py):
    - New function: run_fix_mode_issue(project_dir, issue_number) — (a) fetch issue body via gh issue view, (b) extract ### What, ### Fix, ### Verify sections via regex, (c) construct fix-only coder prompt from extracted sections, (d) create fix/issue-{N} branch off default branch, (e) spawn coder via existing run_phase2_coder(mode="fix"), (f) run vet + nm phases same as existing fix mode.
    - New function: extract_issue_sections(issue_body) -> dict — returns {"what": str, "fix": str, "verify": str, "file_path": str | None}. Uses regex ### (What|Fix|Verify)\s\n(.?)(?=\n### |\Z) to extract sections. Extracts file path from ### What section via backtick-pattern matching ( path/file.py:NN ).
    - Upgrade SHOULD FIX issue body template: Replace current ### Finding / ### Context sections with ### What / ### Fix / ### Verify. The ### What section includes location and finding description. The ### Fix section provides an actionable instruction (derived from the finding). The ### Verify section specifies the test command or check. Add a ### Source section with PR link and branch for traceability.
    
    Tests (tests/test_fix_mode.py):
    - test_run_fix_mode_issue_happy_path — mock gh to return structured issue body, verify coder is spawned with correct prompt.
    - test_extract_issue_sections_all_fields — parses full structured body, returns dict with all four keys populated.
    - test_extract_issue_sections_missing_verify — Verify section is optional, returns empty string.
    - test_extract_issue_sections_missing_fix — Fix section is required, raises error.
    - test_extract_issue_sections_free_text — unstructured issue body returns best-effort extraction (full body as "what", empty fix/verify).
    - test_extract_issue_sections_file_path_backtick — extracts  utils.py:42  from What section.
    - test_run_fix_mode_issue_nonexistent — gh returns non-zero, prints error, exits cleanly.
    - test_run_fix_mode_issue_no_sections — issue body has no ### What / ### Fix, prints error.
    
    Tests (tests/test_f036_should_fix_extraction.py):
    - test_should_fix_issue_body_has_structured_sections — verify newly created issue bodies contain ### What, ### Fix, ### Verify headings.
    - test_should_fix_issue_body_what_includes_location — verify ### What section includes file path when available from table format.
    
    
    
    6. Feature Breakdown
    
    Task 1: Add --issue N argument to fix subparser in CLI entry point
    Files: dokima
    Dependencies: [none]
    Parallelizable: yes
    Description: Add fix_p.add_argument("--issue", type=int, default=None) to the fix subparser (after line 197). In the elif cmd == "fix": block (line 323), extract issue_number = getattr(args, "issue", None). In the fix dispatch block (line 612), if issue_number is set, call _pipeline.run_fix_mode_issue(project_dir=PROJECT_DIR, issue_number=issue_number) instead of _pipeline.run_fix_mode(...). Also update help text in utils.py _build_cli_help_json() to document the new --issue flag.
    
    Task 2: Implement extract_issue_sections() in utils.py
    Files: utils.py
    Dependencies: [none]
    Parallelizable: yes
    Description: Add extract_issue_sections(issue_body: str) -> dict near the existing extract_should_fix_from_text() (~line 2157). Implement regex-based extraction: ### What, ### Fix, ### Verify sections using re.search(r'### (What|Fix|Verify)\s\n(.?)(?=\n### |\Z)', text, re.DOTALL). Extract file path from ### What using  re.search(r'([^]+\.[a-z]+(?::\d+)?)', what_section) . Return {"what": "...", "fix": "...", "verify": "...", "file_path": "..."}. Raise ValueError if fix section is missing (required). Return empty string for missing verify or file_path`. Handle edge cases: empty body, sections with only whitespace, backtick code blocks within sections (strip them), sections in wrong order.
    
    Task 3: Implement run_fix_mode_issue() in pipeline.py
    Files: pipeline.py
    Dependencies: [Task 2]
    Parallelizable: no (depends on Task 2)
    Description: Add run_fix_mode_issue(project_dir, issue_number) function near run_fix_mode() (~line 271). Steps: (1) Fetch issue: gh issue view {issue_number} --repo {REPO} --json body,title,labels --jq '{body, title}'. Handle fetch failure gracefully (print error, return). (2) Call extract_issue_sections(issue_body) from utils. (3) Construct coder prompt: ### What\n{what}\n\n### Fix\n{fix}\n\n### Verify\n{verify} plus standard fix-mode constraints (TDD, single commit, don't add features). Include target file path if extracted. (4) Create branch: fix/issue-{N} off default branch. Use git checkout -b pattern from existing code. (5) Spawn coder via run_phase2_coder(mode="fix") with constructed prompt. (6) If coder succeeds, run run_phase3_vet and run_phase4_nm. (7) Print summary: branch, PR URL, verification steps for user. Reuse existing fix-mode patterns for git operations and agent spawning.
    
    Task 4: Upgrade SHOULD FIX issue body template in run_phase5_tech_lead()
    Files: pipeline.py
    Dependencies: [Task 2]
    Parallelizable: no (depends on Task 2, but different section of pipeline.py — no file conflict with Task 3 if Task 3 is in a different function)
    Description: In run_phase5_tech_lead(), replace the issue body template (lines 1396-1419) with structured sections. New format:
    
    What
    [{dimension}] {location}: {detail}
    
    Fix
    {actionable instruction derived from finding}
    
    Verify
    - [ ] Run: {TEST_CMD}
    - [ ] Confirm: {specific check from detail}
    
    Source
    - PR: {pr_url}
    - Branch: {branch}
    - Spec: {spec_path}
    
    For the ### Fix section, generate a reasonable action from the finding: convention violations → "Update code to follow {convention}", missing tests → "Add test for {scenario}", stale docs → "Update {doc file} to reflect current behavior". For the ### Verify section, include the test command and a finding-specific check. Remove old ### Finding and ### Context sections.
    
    Task 5: Add tests for --issue mode
    Files: tests/test_fix_mode.py
    Dependencies: [Task 2, Task 3]
    Parallelizable: yes (no file overlap with Task 4)
    Description: Add comprehensive tests for issue-based fix mode. Test categories: (a) Happy path — mock gh issue view with structured body, verify run_phase2_coder called with correct prompt. (b) extract_issue_sections — all three sections present, missing optional Verify, missing required Fix (ValueError), file path extraction from backticks, multiple file paths, no file paths. (c) Edge cases — issue not found (gh returns non-zero), empty body, sections with only whitespace, code blocks in sections. (d) Branch creation — verify fix/issue-{N} branch name pattern. Use conftest._load_panel for import access. Mock gh, git, and coder spawns.
    
    Task 6: Add tests for upgraded SHOULD FIX issue body format
    Files: tests/test_f036_should_fix_extraction.py
    Dependencies: [Task 4]
    Parallelizable: yes (no file overlap with Task 5)
    Description: Add tests verifying the new issue body format. (a) Verify ### What heading exists in generated body. (b) Verify ### Fix heading exists. (c) Verify ### Verify heading exists. (d) Verify ### What includes file location when available from table format extraction. (e) Verify ### Source section includes PR link. Use _load_panel to access run_phase5_tech_lead internals, or test the body construction helper function directly.
    
    
    
    7. Data Model
    
    Issue body structure (new format for SHOULD FIX issues):
    markdown
    What
    [RELIABILITY] utils.py:42: Naming conventions for internal functions
    
    Fix
    Rename internal functions to use _ prefix per conventions.md
    
    Verify
    - [ ] Run: python3 -m pytest tests/ -q
    - [ ] Confirm: All internal functions use _ prefix, no naming lint warnings
    
    Source
    - PR: https://github.com/owner/repo/pull/42
    - Branch: feat/f033-cross-run-learning
    - Spec: specs/f033-cross-run-learning/spec.md
    
    
    Extraction result (returned by extract_issue_sections):
    python
    {
        "what": "[RELIABILITY] utils.py:42: Naming conventions for internal functions",
        "fix": "Rename internal functions to use _ prefix per conventions.md",
        "verify": "- [ ] Run: python3 -m pytest tests/ -q\n- [ ] Confirm: All internal functions use _ prefix, no naming lint warnings",
        "file_path": "utils.py"  # Extracted from backticks in What section
    }
    
    
    No new persistent entities. The extraction function returns transient dicts. No new database schema.
    
    
    
    8. API Routes
    
    N/A — no API changes. Internal function calls within the pipeline.
    
    
    
    9. COTS Build-vs-Buy
    
    Component: GitHub issue fetch
    Decision: COTS
    Justification: Existing gh CLI — one call: gh issue view N --json
      body,title
    ────────────────────────────────────────
    Component: Issue body section extraction
    Decision: Build
    Justification: stdlib re — ~30 lines, three regex patterns
    ────────────────────────────────────────
    Component: File path extraction from backticks
    Decision: Build
    Justification: stdlib re — one pattern, 5 lines
    ────────────────────────────────────────
    Component: Coder agent spawning
    Decision: COTS
    Justification: Existing run_phase2_coder() — reused as-is
    ────────────────────────────────────────
    Component: Vet + nm phases
    Decision: COTS
    Justification: Existing run_phase3_vet(), run_phase4_nm() — reused as-is
    
    Everything is built or reused. No new dependencies.
    
    
    
    10. Test Plan (MANDATORY)
    
    Feature Area: extract_issue_sections() — Happy path
    - Happy path: Input contains all three sections (### What, ### Fix, ### Verify) — returns dict with all keys populated.
    - Edge cases: Sections in different order (What, Verify, Fix) — still matches by heading, not position. Extra whitespace between sections — stripped. Sections with leading/trailing blank lines — trimmed.
    - Failure modes: Empty string input → ValueError. None input → ValueError. Input with no ### headings → ValueError. Input with ### What but no ### Fix → ValueError.
    - Contract invariants: Returned dict always has keys what, fix, verify, file_path. fix is never empty — raises if extractable fix is empty.
    
    Feature Area: extract_issue_sections() — File path extraction
    - Happy path:  utils.py:42  in What section → file_path="utils.py".
    - Edge cases:  src/core/auth.py:L128  → file_path="src/core/auth.py".  README.md  (no line number) → file_path="README.md". Multiple backtick paths → first one. No backtick paths → file_path=None. Backtick in code block (triple-backtick fence) → NOT extracted as file path.
    - Failure modes: Malformed backticks (unclosed) → fallback to content after opening backtick. Backtick with no file extension → ignored, file_path=None.
    - Contract invariants: file_path is either None or a string containing a file extension. It never contains line numbers (stripped at :).
    
    Feature Area: run_fix_mode_issue() — Issue fetch
    - Happy path: gh issue view 42 --json body,title returns valid JSON → parsed, sections extracted, coder spawned.
    - Edge cases: Issue has labels (ignored). Issue has comments (not fetched — only body is used). Issue number is valid but body has no structured sections → error message, return.
    - Failure modes: Issue not found (gh returns non-zero) → prints error, returns. Network timeout → caught by subprocess timeout (15s), prints error, returns. JSON parse failure → prints error with raw output excerpt, returns.
    - Contract invariants: Function returns None on failure — never crashes the panel. The coder is only spawned if both issue body is fetched AND sections are successfully extracted.
    
    Feature Area: run_fix_mode_issue() — Branch and coder
    - Happy path: Creates fix/issue-42 branch, checks out, spawns coder with constructed prompt, coder succeeds → vet + nm run.
    - Edge cases: Branch already exists → git checkout -b fails → switch to existing branch with warning. Coder fails → skip vet and nm, print failure summary.
    - Failure modes: Git checkout fails (dirty working tree) → print error, return. Coder spawn fails (agent unavailable) → existing error handling from run_phase2_coder applies.
    - Contract invariants: The coder prompt always includes ### Fix section. The ### Verify section is appended as a checklist at end of prompt. Standard fix-mode constraints (TDD, single commit, no feature additions) are always included.
    
    Feature Area: SHOULD FIX issue body upgrade
    - Happy path: SH FIX issue created via pipeline → body contains ### What, ### Fix, ### Verify, ### Source headings.
    - Edge cases: Table-format finding with all dimensions → ### What includes dimension, ID, location, detail. Prose-format finding (no location) → ### What includes only the detail text.
    - Failure modes: Fix description generation produces empty string for unrecognized finding → falls back to "Address the finding described above."
    - Contract invariants: Every created issue has ### What and ### Fix sections. ### Verify is optional (empty if no specific verification can be derived). ### Source always includes PR link and branch.
    
    
    
    11. Panel Split
    
    - Wave 1: [Task 1, Task 2, Task 6] — parallel (3 agents: dokima CLI, utils.py, tests/test_f036_should_fix_extraction.py — no file overlap)
    - Wave 2: [Task 3, Task 4, Task 5] — parallel (3 agents: pipeline.py Task 3 function is different section from Task 4 upgrade — but they share pipeline.py so must be sequential OR merged tasks)
    
    Correction: Task 3 and Task 4 BOTH touch pipeline.py — they cannot run in the same wave. Revised:
    
    - Wave 1: [Task 1, Task 2, Task 5, Task 6] — parallel (4 agents: dokima, utils.py, tests/test_fix_mode.py, tests/test_f036_should_fix_extraction.py — zero file overlap)
    - Wave 2: [Task 3] — sequential (touches pipeline.py, depends on Task 2)
    - Wave 3: [Task 4] — sequential (touches pipeline.py, depends on Task 2, cannot run parallel with Task 3 due to file overlap)
    
    4 coder agents, 3 waves, estimated wall-clock: ~20 minutes (Wave 1: ~8 min, Wave 2: ~6 min, Wave 3: ~6 min).
    
    
    
    12. Build & Deploy
    
    - Deploys as part of the dokima panel (single Python script + modules)
    - No new dependencies, no CI changes
    - Test commands:
      - python3 -m pytest tests/test_fix_mode.py -v (existing + new issue-mode tests)
      - python3 -m pytest tests/test_f036_should_fix_extraction.py -v (new format tests)
      - python3 -m pytest tests/ -q (full regression)
    - No new env vars needed
    - Existing gh CLI authentication reused (GH_TOKEN from environment)
    
    
    
    13. Risk Register
    
    #: 1
    Risk: Issue body format changes break section extraction
    Severity: MEDIUM
    Mitigation: Regex is heading-based (### What), not position-based. If
      headings change, extraction fails gracefully with clear error message —
      doesn't crash
    Trigger: ValueError on extraction, user sees "Could not extract sections
      from issue #N"
    ────────────────────────────────────────
    #: 2
    Risk: gh issue view API rate limit during fix mode
    Severity: LOW
    Mitigation: Single API call per fix — rate limit is 5000/hour. Fallback:
      print error, suggest manual fix
    Trigger: gh returns 403/429
    ────────────────────────────────────────
    #: 3
    Risk: ### Fix section has ambiguous instructions the coder can't act on
    Severity: MEDIUM
    Mitigation: Human-readable — the issue creator (TL agent or human) writes
      the Fix section. Coder gets the full Fix text verbatim. If coder fails,
      it reports ⚠ CODER UNABLE TO FIX: <reason>
    Trigger: Coder returns coder_failed=True
    ────────────────────────────────────────
    #: 4
    Risk: Branch fix/issue-N conflicts with existing branch
    Severity: LOW
    Mitigation: git checkout -b fails → switch to existing branch with
      warning. If branch has uncommitted changes → error, return
    Trigger: Git checkout failure
    ────────────────────────────────────────
    #: 5
    Risk: File path extracted from backticks is wrong/nonexistent
    Severity: LOW
    Mitigation: File path is a hint for the coder — the coder still reads the
      codebase to confirm. Wrong hint wastes 1-2 coder turns
    Trigger: Coder reads nonexistent file, gets FileNotFoundError, then
      discovers actual files
    ────────────────────────────────────────
    #: 6
    Risk: SHOULD FIX issue body upgrade breaks existing issue parsing
    Severity: LOW
    Mitigation: The upgrade only changes new issues — existing issues are not
      retroactively modified. No existing parser depends on issue body format
    Trigger: Not triggered
    
    
    
    14. Anti-Creep
    
    Explicitly OUT OF SCOPE:
    - No retroactive upgrade of existing SHOULD FIX issues — only new issues get the structured format. Existing issues keep their ### Finding / ### Context format.
    - No --issue for non-SHOULD-FIX issues — the --issue flag only works with issues that have ### What / ### Fix / ### Verify sections. General-purpose issue fixing is out of scope.
    - No issue comment extraction — only the issue body is processed. Comments are not fetched or parsed.
    - No BLOCKER auto-fix via --issue — BLOCKER auto-fix remains exclusive to dokima fix (PR discovery mode). --issue is for manual, structured issue targeting.
    - No mutation of the source issue after fix — the coder does not close or comment on the issue. The user verifies and closes manually.
    - No multi-issue batching — --issue takes exactly one number. No --issue 42,43,44.
    - No --issue without --repo override — REPO is detected from git remote, same as all other pipeline phases.
    - No change to discover_blocked_pr() — that function is untouched. --issue mode bypasses it entirely.
    
    
    
    15. Sign-Off Checklist
    
    - [ ] dokima fix --issue 42 fetches issue #42 body from GitHub
    - [ ] extract_issue_sections() parses ### What, ### Fix, ### Verify from issue body
    - [ ] extract_issue_sections() extracts file path from backticks in ### What section
    - [ ] extract_issue_sections() raises ValueError when ### Fix is missing
    - [ ] extract_issue_sections() returns empty string for optional ### Verify
    - [ ] run_fix_mode_issue() creates fix/issue-{N} branch off default branch
    - [ ] run_fix_mode_issue() spawns coder with structured prompt containing What/Fix/Verify
    - [ ] run_fix_mode_issue() runs vet + nm after successful coder fix
    - [ ] run_fix_mode_issue() prints clear error when issue not found
    - [ ] run_fix_mode_issue() prints clear error when issue body has no structured sections
    - [ ] SHOULD FIX issue body template includes ### What, ### Fix, ### Verify, ### Source
    - [ ] gh issue view fallback handles network/auth errors gracefully
    - [ ] All 6 tasks have passing tests: python3 -m pytest tests/test_fix_mode.py tests/test_f036_should_fix_extraction.py -v
    - [ ] No regression: full test suite python3 -m pytest tests/ -q (679 tests) still passes
    - [ ] Help text and CLI JSON metadata include --issue flag documentation
    
    
    
    
    Quality correction summary:
    
    1. Impact section (Section 4): Added — covers files affected (dokima +10, pipeline.py +80/-5, tests/test_fix_mode.py +120, tests/test_f036_should_fix_extraction.py +40), no API/deployment change, new gh call pattern.
    
    2. What Changed section (Section 5): Added — concrete per-file breakdown: CLI argument wiring, new run_fix_mode_issue() function, new extract_issue_sections() helper, upgraded SHOULD FIX issue body template, test additions for both issue mode and format upgrade.
    
    3. Task N: headers (Section 6): All six tasks use the mandated ### Task N: format with all five required fields — Files:, Dependencies:, Parallelizable:, Description:. Zero file overlap between parallel tasks in each wave: Wave 1 runs Task 1 (dokima), Task 2 (utils.py), Task 5 (tests/test_fix_mode.py), Task 6 (tests/test_f036_should_fix_extraction.py) — four agents, four different files. Wave 2 runs Task 3 (pipeline.py). Wave 3 runs Task 4 (pipeline.py — cannot parallelize with Task 3 due to file overlap).