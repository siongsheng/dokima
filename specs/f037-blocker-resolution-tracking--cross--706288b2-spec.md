# F037: Blocker Resolution Tracking — cross-reference fix PRs to the original blocker PR they resolve. After completes and TL approves, auto-update the original PR's section with strikethrough + link to the resolution PR. Optionally create GitHub issues from blockers (matching SHOULD FIX pattern) and auto-close them when the fix PR merges.

Now I have a thorough understanding of the codebase. Let me produce the corrected F037 spec.
    
    Position: F037 is a natural extension of the existing fix mode pipeline (pipeline.py:run_fix_mode) and SHOULD FIX issue creation (pipeline.py:run_phase5_tech_lead). The existing PR body update pattern (gh api PATCH) and vcs_issue_create provide the infrastructure. New code is needed, but it's ~150-200 LOC spread across 3 files. (High confidence)
    
    Ponytail Guard — Pre-Spec Review
    - Feature: F037: Blocker Resolution Tracking
    - Rung: 7 — Build the minimum that works on top of existing infrastructure
    - Existing solution: vcs_pr_view, gh api PATCH for PR body (line 1525), vcs_issue_create, extract_blockers_from_pr. None of these do cross-reference strikethrough or blocker→issue creation.
    - Spec needed: yes — covers blocker→strikethrough update + optional issue creation + auto-close
    
    Assumptions:
    1. The fix PR number is the SAME as the original PR number (fix mode pushes new commits to the same branch). The "resolution PR" is the same PR after fix commits are pushed.
    2. GitHub auto-close uses "Closes #N" in commit message or PR description — we'll use PR body "Closes #N" references.
    3. Blocker strikethrough uses text markdown.
    
    
    
    F037: Blocker Resolution Tracking
    
    Version: 1.0.0 | Status: Spec | Confidence: High
    
    
    
    1. Executive Summary
    
    F037 closes the loop on dokima fix: after TL approves a fix, the original blocked PR's ### Blockers section is auto-updated with strikethrough + link to the resolution. Optionally, blockers matching SHOULD FIX patterns are created as GitHub issues and auto-closed when the fix merges. This eliminates manual cross-referencing between blocker PRs and their resolutions. Risk is LOW — all operations use existing VCS infrastructure (gh api PATCH, vcs_issue_create) and are best-effort (failures log warnings, never block the pipeline).
    
    
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Status: YES
    Notes: Current fix mode has no traceability — you can't tell which
      blockers were fixed without reading the diff.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: YES
    Notes: ~150-200 LOC, 2-3 hours.
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A (internal tool)
    Notes: Used by the panel itself on every fix run.
    ────────────────────────────────────────
    Axiom: Boring, proven stack?
    Status: YES
    Notes: Python + gh CLI + markdown strikethrough. No new dependencies.
    ────────────────────────────────────────
    Axiom: Avoids AI hype?
    Status: YES
    Notes: Pure pipeline automation, no AI component.
    
    
    
    3. Feature Breakdown
    
    Task 1: Add vcs_pr_update_body() to VCS abstraction layer
    - Files: vcs.py
    - Dependencies: [none]
    - Parallelizable: yes
    - Estimated LOC: ~30
    - Description: Add a vcs_pr_update_body(pr_num, new_body) function that dispatches to gh api repos/{REPO}/pulls/{pr_num} --method PATCH -f body=... (GitHub) or glab mr update {pr_num} --description ... (GitLab). Follows existing _run_vcs pattern. Replace the inline gh("api", ...) call at pipeline.py:1525 with a call to this new function.
    
    Task 2: Add format_blocker_cross_reference() helper to utils.py
    - Files: utils.py
    - Dependencies: [none]
    - Parallelizable: yes
    - Estimated LOC: ~25
    - Description: Create format_blocker_cross_reference(blockers, fix_pr_url, fix_verdict) that takes a list of blocker strings, the fix PR URL, and the TL verdict. If APPROVED, returns a markdown string where each blocker is wrapped with ~~ (strikethrough) and appended with → resolved by fix PR. If BLOCKED, returns blockers annotated with → unresolved. If UNKNOWN, returns blockers unchanged. Uses re.sub to match existing bullet/numbered format.
    
    Task 3: Add create_blocker_issues() to pipeline.py
    - Files: pipeline.py
    - Dependencies: [Task 1]
    - Parallelizable: yes (different section of file from Task 4)
    - Estimated LOC: ~45
    - Description: Create create_blocker_issues(blockers, pr_num, pr_url, feature, branch, spec_path) that mirrors the SHOULD FIX issue creation pattern in run_phase5_tech_lead (lines 1534-1632). For each blocker, create a GitHub issue with title "BLOCKER: {desc[:72]}", body containing What/Fix/Verify sections, and label "blocker". Returns list of issue URLs created. Uses vcs_issue_create from vcs.py. Best-effort — logs warnings on failure, never blocks pipeline. Guard: skip if no --create-blocker-issues flag is set (off by default, matching "optionally" in requirements).
    
    Task 4: Add post-fix PR body update to run_fix_mode()
    - Files: pipeline.py
    - Dependencies: [Task 1, Task 2]
    - Parallelizable: no (depends on Task 1)
    - Estimated LOC: ~35
    - Description: After the TL re-review block in run_fix_mode() (lines 681-710), when fix_verdict == "APPROVED":
      1. Fetch the current PR body via vcs_pr_view() to avoid stale data
      2. Locate the ### Blockers section in the body
      3. Replace blocker descriptions with format_blocker_cross_reference() output
      4. Append a ### Resolution subsection with fix PR link and timestamp
      5. Call vcs_pr_update_body() to persist the update
      6. If --create-blocker-issues, call create_blocker_issues() and append "Closes #N" references to the PR body so issues auto-close on merge
      Best-effort: failures log ⚠ Could not update PR body but do NOT block the pipeline.
    
    Task 5: Add auto_close_referenced_issues() to pipeline.py
    - Files: pipeline.py
    - Dependencies: [Task 3]
    - Parallelizable: yes (different function, no file overlap with Task 4's specific section)
    - Estimated LOC: ~25
    - Description: Create auto_close_referenced_issues(pr_body, pr_num) that scans the PR body for Closes #N or Fixes #N references, verifies those issues exist via vcs_issue_view(), and adds a closing comment "Resolved by PR #{pr_num}: {pr_url}" to each. Called from run_post_pipeline() when verdict is APPROVED and the PR is merged. Best-effort — failures are logged, not raised.
    
    Task 6: Wire flag parsing for --create-blocker-issues
    - Files: utils.py (HELP_TEXT, CLI_METADATA), dokima entry point
    - Dependencies: [none]
    - Parallelizable: yes
    - Estimated LOC: ~10
    - Description: Register --create-blocker-issues as a modifier flag for dokima fix. Add to HELP_TEXT under both fix line and MODIFIER FLAGS section. Add to CLI_METADATA flags list. Parse in main() dispatch and pass through to run_fix_mode().
    
    Task 7: Add test file tests/test_f037_blocker_resolution.py
    - Files: tests/test_f037_blocker_resolution.py
    - Dependencies: [Task 1, Task 2, Task 3, Task 4, Task 5, Task 6]
    - Parallelizable: no (needs all implementation tasks done)
    - Estimated LOC: ~120
    - Description: Test all new behavior:
      - test_format_blocker_cross_reference_approved — approved blockers get strikethrough + link
      - test_format_blocker_cross_reference_blocked — blocked blockers get "→ unresolved"
      - test_format_blocker_cross_reference_unknown — unknown verdict returns unchanged
      - test_format_blocker_cross_reference_empty — empty list returns empty string
      - test_vcs_pr_update_body_github — gh API PATCH called correctly
      - test_vcs_pr_update_body_gitlab — glab mr update called correctly
      - test_create_blocker_issues_creates_issues — issues created with correct title/body/label
      - test_create_blocker_issues_skips_when_flag_off — no issues when flag not set
      - test_auto_close_referenced_issues — "Closes #N" triggers issue close comment
      - test_post_fix_update_body_integration — mock full fix mode flow, verify PR body updated with strikethrough
      - test_flag_create_blocker_issues_parsed — flag appears in help/parsing
    
    
    
    4. Data Model
    
    No new persistent entities. All state is transient (PR body string manipulation, GitHub issue references).
    
    PR Body Mutation (transient):
    
    Blockers
    - Login test fails → resolved by https://github.com/t/t/pull/42
    - Missing error handling → resolved by https://github.com/t/t/pull/42
    
    Resolution
    Fix PR: https://github.com/t/t/pull/42
    Verdict: APPROVED
    Resolved at: 2026-07-06T10:30:00Z
    
    
    Blocker Issue (created on GitHub, optional):
    
    Title: BLOCKER: Login test fails
    Body:
    What
      Blocker identified during TL review of PR #42
    Fix
      [blocker description]
    Verify
      - [ ] Run: TEST_CMD
    Source
      - PR: https://github.com/t/t/pull/42
    Labels: blocker
    
    
    
    
    5. API/VCS Routes
    
    Operation: Update PR body
    Provider: GitHub
    Command: gh api repos/{REPO}/pulls/{N} --method PATCH -f body=...
    ────────────────────────────────────────
    Operation: Update MR body
    Provider: GitLab
    Command: glab mr update {N} --description "..."
    ────────────────────────────────────────
    Operation: Create issue
    Provider: GitHub/GitLab
    Command: vcs_issue_create() (existing)
    ────────────────────────────────────────
    Operation: Close issue comment
    Provider: GitHub
    Command: gh issue comment {N} --body "Resolved by PR #{M}"
    
    No new API routes. All operations use existing VCS CLI tools.
    
    
    
    6. Component Tree
    
    N/A — this is a pipeline enhancement, not a frontend feature.
    
    
    
    7. COTS Build-vs-Buy
    
    Component: PR body update
    Decision: Build (30 LOC)
    Justification: gh api PATCH is a one-liner. Not worth an abstraction
      layer.
    ────────────────────────────────────────
    Component: Markdown strikethrough
    Decision: Build (5 LOC)
    Justification: text is native markdown.
    ────────────────────────────────────────
    Component: GitHub issue creation
    Decision: Build (reuse)
    Justification: vcs_issue_create already exists (vcs.py:194).
    ────────────────────────────────────────
    Component: Issue auto-close
    Decision: Build (25 LOC)
    Justification: "Closes #N" in PR body is a native GitHub feature.
      Comment-based close is a one-liner gh issue comment.
    
    
    
    8. Test Plan (MANDATORY)
    
    Happy Path
    1. dokima fix discovers BLOCKED PR with 2 blockers → fixes them → TL approves → original PR body updated with blocker → resolved by PR #N → issues created if --create-blocker-issues → Closes #N references in PR body auto-close issues on merge.
    
    Edge Cases
    - PR body has no ### Blockers section — update is skipped silently (no-op, logs info).
    - Blockers section contains mixed content (prose, tables, verdict text) — format_blocker_cross_reference only operates on list items (-  or 1.  prefixed lines). Non-list lines are preserved unchanged.
    - PR body update fails (network, auth) — logs warning ⚠, does NOT block pipeline (best-effort).
    - Blocker descriptions contain markdown (bold, backticks) — strikethrough wraps the entire line after stripping the list prefix. Bold/backticks inside strikethrough are valid markdown.
    - Multiple fix runs on the same PR — second run finds existing strikethrough. Resolved blockers are detected (already ...), skip re-processing.
    - TL re-review verdict is BLOCKED (fix didn't resolve everything) — annotate unresolved blockers with → unresolved, do NOT strikethrough, do NOT create issues.
    - --create-blocker-issues not set — no issues created, PR body does NOT contain Closes #N references.
    
    Failure Modes
    - gh api PATCH returns non-zero — log warning, continue pipeline. Do NOT block.
    - vcs_issue_create fails (rate limit, auth) — log warning per-failure, continue to next blocker.
    - PR body is empty/null — skip update (no-op).
    - vcs_pr_view fails (stale token) — log warning, skip update.
    - Blocker list is empty after extraction — skip both update and issue creation (already handled by existing code at line 524).
    
    Contract Invariants
    - Before fix run: Original PR body contains ### Blockers with list items. No strikethrough on blocker lines.
    - After fix run + APPROVED: Each blocker in ### Blockers is either strikethrough-annotated (resolved) or unchanged (unresolved). A ### Resolution subsection exists with verdict + timestamp.
    - After fix run + BLOCKED: Blockers annotated with → unresolved. No strikethrough. No resolution section.
    - Pipeline invariant: PR body update failure NEVER changes the TL verdict. The fix pipeline completes regardless.
    
    
    
    9. Impact Assessment
    
    Grounded in actual file analysis:
    
    File: vcs.py
    Change: +vcs_pr_update_body()
    LOC: +30
    ────────────────────────────────────────
    File: utils.py
    Change: +format_blocker_cross_reference(), +flag in HELP_TEXT/CLI_METADATA
    LOC: +35
    ────────────────────────────────────────
    File: pipeline.py
    Change: +create_blocker_issues(), +auto_close_referenced_issues(),
      +post-fix update in run_fix_mode(), replace inline gh("api",...) with
      vcs_pr_update_body()
    LOC: +95
    ────────────────────────────────────────
    File: dokima (entry)
    Change: flag parsing
    LOC: +5
    ────────────────────────────────────────
    File: tests/test_f037_blocker_resolution.py
    Change: new test file
    LOC: +120
    ────────────────────────────────────────
    File: Total
    Change:
    LOC: ~285 LOC
    
    Dependencies from existing code:
    - run_fix_mode() at pipeline.py:681-710 — insertion point for post-TL update
    - run_phase5_tech_lead() at pipeline.py:1525 — inline gh("api", ...) to replace with vcs_pr_update_body()
    - vcs.py — existing _run_vcs(), vcs_issue_create(), vcs_pr_view()
    - extract_blockers_from_pr() at pipeline.py:245 — blocker parsing (unchanged, consumed as input)
    - format_blocker_cross_reference() referenced by test file test_f037_blocker_resolution.py
    
    
    
    10. What Changed (from current state)
    
    - New: vcs_pr_update_body() in vcs.py — VCS-agnostic PR body update
    - New: format_blocker_cross_reference() in utils.py — strikethrough formatting
    - New: create_blocker_issues() in pipeline.py — blocker→issue creation
    - New: auto_close_referenced_issues() in pipeline.py — issue auto-close on merge
    - Changed: run_fix_mode() — appends blocker cross-reference update after TL approval
    - Changed: run_phase5_tech_lead() — replaces inline gh("api",...) with vcs_pr_update_body()
    - Changed: HELP_TEXT + CLI_METADATA — adds --create-blocker-issues flag
    
    
    
    11. Panel Split
    
    Wave 1 (parallel — no file conflicts):
    - Task 1: vcs_pr_update_body() (vcs.py)
    - Task 2: format_blocker_cross_reference() (utils.py)
    - Task 6: Flag wiring (utils.py, dokima entry) — does NOT conflict with Task 2 (different sections of utils.py: Task 2 is in function area, Task 6 is in HELP_TEXT/CLI_METADATA constants area)
    
    Wave 2 (parallel — no file conflicts with each other):
    - Task 3: create_blocker_issues() (pipeline.py)
    - Task 5: auto_close_referenced_issues() (pipeline.py) — different function, no line overlap with Task 3
    
    Wave 3 (sequential — depends on Wave 1 + Wave 2):
    - Task 4: Post-fix update in run_fix_mode() (pipeline.py) — needs Task 1, Task 2, Task 3
    
    Wave 4 (sequential — depends on all implementation):
    - Task 7: Tests (test_f037_blocker_resolution.py)
    
    Coders needed: Wave 1 = 3 coders, Wave 2 = 2 coders, Wave 3 = 1 coder, Wave 4 = 1 coder.
    
    
    
    12. Build & Deploy
    
    - Deploy: No deploy — this is a dokima pipeline enhancement. Tests validate behavior, merge to main.
    - CI: python3 -m pytest tests/test_f037_blocker_resolution.py -v
    - No new env vars. --create-blocker-issues is a CLI flag only (no env var equivalent initially).
    
    
    
    13. Risk Register
    
    #: R1
    Risk: PR body update corrupts existing content
    Severity: MEDIUM
    Mitigation: Read fresh body before update; only modify ### Blockers
      section; append ### Resolution without touching other sections
    Trigger: Regex misfire on blocker section boundaries
    ────────────────────────────────────────
    #: R2
    Risk: gh api PATCH fails silently on large PR bodies
    Severity: LOW
    Mitigation: Log warning, continue — best-effort pattern
    Trigger: PR body > 10K chars
    ────────────────────────────────────────
    #: R3
    Risk: Already-resolved blockers get double-strikethrough
    Severity: LOW
    Mitigation: Detect existing ... pattern, skip
    Trigger: Second fix run on same PR
    ────────────────────────────────────────
    #: R4
    Risk: Issue auto-close references wrong PR #
    Severity: LOW
    Mitigation: Use pr_num from run_fix_mode() context, validated before use
    Trigger: Cross-contamination between fix runs
    ────────────────────────────────────────
    #: R5
    Risk: GitLab glab mr update doesn't support --description in all versions
    Severity: LOW
    Mitigation: Fall back to glab mr update --description — this flag is
      available since glab 1.22+. If it fails, log warning and skip.
    Trigger: Older glab versions
    
    
    
    14. Anti-Creep (NOT in scope)
    
    - Do NOT build a blocking-resolution dashboard or UI.
    - Do NOT create a database/vector store for blocker history.
    - Do NOT auto-resolve blockers without TL approval (human gate is preserved).
    - Do NOT send notifications (Slack, email, webhook) on blocker resolution.
    - Do NOT modify the extract_blockers_from_pr() function — its output format stays the same.
    - Do NOT support GitHub Projects or issue board automation.
    - Do NOT modify run_phase5_tech_lead() beyond replacing the inline gh("api",...) call — the SHOULD FIX issue flow is unchanged.
    - Do NOT create an env var for --create-blocker-issues initially — CLI flag only.
    
    
    
    15. Sign-Off Checklist
    
    - [ ] vcs_pr_update_body() works for both GitHub (gh api PATCH) and GitLab (glab mr update --description)
    - [ ] format_blocker_cross_reference() handles APPROVED, BLOCKED, and UNKNOWN verdicts correctly
    - [ ] format_blocker_cross_reference() preserves non-list lines in ### Blockers section
    - [ ] create_blocker_issues() is gated behind --create-blocker-issues flag (off by default)
    - [ ] Post-fix PR body update is best-effort (never blocks pipeline on failure)
    - [ ] Existing fix mode tests (test_fix_mode.py) continue to pass
    - [ ] Existing SHOULD FIX extraction tests (test_f036_should_fix_extraction.py) continue to pass
    - [ ] auto_close_referenced_issues() only fires when PR is merged (called from run_post_pipeline)
    - [ ] --create-blocker-issues appears in dokima fix --help and HELP_TEXT
    - [ ] Stripped: no new dependencies, no new files beyond test file
    - [ ] Two ### Blockers section edge cases tested: mixed content, pre-existing strikethrough
    - [ ] Full pipeline tested: dokima fix → blockers discovered → fixed → TL approves → PR body updated → (optional) issues created