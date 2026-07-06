# F038: Surface nm and TL findings in PR body — when nm runs (Phase 4) or TL reviews (Phase 5), inject their findings into the PR body as and sections. At depth=vet+nm (no TL), nm findings still appear. Currently nm output is invisible (37K chars logged but never surfaced); TL findings only appear via a separate PR comment. SHOULD FIX items from both nm and TL are extracted as GitHub issues regardless of depth.

Now I have full understanding. Here is the COMPLETE corrected spec:
    
    
    
    F038: Surface nm and TL Findings in PR Body
    
    Position: nm adversarial review output (37K chars) is completely invisible — it's logged but never reaches the PR body. TL findings appear only as a separate PR comment. F038 injects both as ### nm Review and preserves the existing ## Review (TL) section in the PR body itself, with nm findings surfacing even at depth=vet+nm (no TL). SHOULD FIX extraction from both nm and TL continues as GitHub issues. (High confidence)
    
    1. Executive Summary
    
    Dokima's Phase 4 nm adversarial review produces rich findings (37K chars of output) that are logged to stdout but never reach the PR body. Phase 5 TL review injects a ## Review section with verdict and blockers, but nm findings remain invisible. At depth=vet+nm (no TL phase), nm output disappears entirely from the PR surface. F038 adds a new ### nm Review section injected after Phase 4 completes — a concise summary with risk level, key findings, and SHOULD FIX items. The existing TL ## Review section is updated to preserve the nm section rather than clobbering it. Regardless of depth, SHOULD FIX items from both nm and TL continue to be extracted as GitHub issues.
    
    2. Constitution Check
    
    Axiom: Solves operator pain?
    Verdict: YES — nm findings are the ONLY adversarial review before
      depth=full and are currently invisible. Operators have to grep logs to
      find why a PR was blocked.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Verdict: YES — ~110 LOC across 2 files. Three targeted injection points.
    ────────────────────────────────────────
    Axiom: Evidence operators hit this?
    Verdict: YES — the feature description explicitly states "nm output is
      invisible (37K chars logged but never surfaced)".
    ────────────────────────────────────────
    Axiom: Boring tech?
    Verdict: YES — adds one helper function + regex-based PR body injection
      using existing vcs.vcs_pr_update_body. No new deps.
    ────────────────────────────────────────
    Axiom: Avoids AI hype?
    Verdict: YES — pure pipeline plumbing. No ML/AI surface.
    
    Verdict: PASS. Aligned with F036 (SHOULD FIX extraction from both formats) and F037 (PR body update pattern). Uses the same PR body injection pattern already proven in run_phase5_tech_lead lines 1724-1728.
    
    3. Ponytail Guard — Pre-Spec Review
    
    
    Ponytail Guard — Pre-Spec Review
    Feature: F038: Surface nm and TL findings in PR body
    Rung: 5 — installed dependency can do it (vcs.vcs_pr_update_body already exists; extract_should_fix_from_text already handles nm_stdout)
    Existing solution: TL findings already injected into PR body (## Review section, lines 1675-1728). nm_stdout is returned from run_phase4_nm but never injected.
    Spec needed: YES — covers the nm injection gap and the depth=vet+nm path where nm runs but TL doesn't
    Spec scope: (1) new helper to extract nm summary from raw nm_stdout, (2) inject ### nm Review after Phase 4, (3) ensure TL phase preserves nm section, (4) SHOULD FIX extraction from nm at Phase 4 for depth=vet+nm
    
    
    4. Decision Table
    
    Option: A: Inject raw nm_stdout (37K chars) into PR body
    Complexity: Low
    Coverage: Full nm output
    Risk: HIGH — bloats PR body, unreadable
    Verdict: Reject
    ────────────────────────────────────────
    Option: B: Extract summary + SHOULD FIX, inject ### nm Review
    Complexity: Medium (~110 LOC)
    Coverage: Key findings + risk + SHOULD FIX
    Risk: LOW — bounded size (~3K chars)
    Verdict: Accept
    ────────────────────────────────────────
    Option: C: Post nm as separate PR comment (like TL review comment)
    Complexity: Low
    Coverage: Full output
    Risk: MEDIUM — two places to check
    Verdict: Reject — still not in PR body
    
    Decision: B. Extract a structured summary from nm_stdout (risk level, auto-fixable issues, SHOULD FIX items, key BLOCKER-level findings) and inject as ### nm Review in PR body. TL's existing ## Review section is updated to not clobber nm's section.
    
    5. Impact
    
    Operators no longer need to grep /tmp/dokima-output.txt for 37K chars of nm output. At depth=vet+nm — the most common depth for medium-confidence features — nm findings that previously disappeared now appear directly in the PR body as a ### nm Review section. TL reviews at depth=full show both nm and TL findings in one place. The adversarial value of cross-family nm review is finally visible where decisions are made: in the PR.
    
    Files affected: utils.py (+~60 LOC, new helper), pipeline.py (+~50 LOC, two injection points)
    
    6. What Changed
    
    - utils.py: New _extract_nm_summary(nm_stdout) helper — parses raw nm output to extract risk level, auto-fixable issue count, key BLOCKER/SHOULD FIX findings, and SHOULD FIX items (delegates to existing extract_should_fix_from_text)
    - pipeline.py run_phase4_nm() (line ~1485): After nm completes and before returning, call _extract_nm_summary, inject ### nm Review into PR body via vcs.vcs_pr_update_body. Also extract SHOULD FIX items from nm_stdout and create GitHub issues (mirroring TL's pattern at lines 1746-1831)
    - pipeline.py run_phase5_tech_lead() (line ~1702): Update the regex that strips old ## Review sections to also strip old ### nm Review before rebuilding, then append fresh ### nm Review alongside ## Review. Currently line 1702 only matches ## Review — nm section is preserved by accident; make it explicit.
    - pipeline.py run_pipeline() (line ~2730): For depth=vet+nm path, the nm PR body injection already fires inside run_phase4_nm (Change 2), so no separate injection needed. The code path is: Phase 4 runs → run_phase4_nm → injects nm section → returns. Phase 5 is skipped. No change needed here — Task 2 covers it.
    
    7. Feature Breakdown
    
    Task 1: Add _extract_nm_summary helper in utils.py
    
    - Files: utils.py
    - Dependencies: none
    - Parallelizable: yes
    - Estimated LOC: ~60
    - Description: New function _extract_nm_summary(nm_stdout: str) -> dict that parses raw nm output (up to 37K chars) and returns a structured dict with risk (str), auto_fix_count (int), auto_fix_labels (list[str]), key_findings (str — first ~2500 chars of substantive review content, skipping nm script boilerplate), and should_fix_items (list[dict] — delegated to existing extract_should_fix_from_text). The key_findings extraction skips the nm script setup lines (lines before "STAGE 1" or "You are running") and captures the actual review body. Returns empty dict if nm_stdout is empty/None.
    
    Task 2: Inject ### nm Review into PR body after nm Phase 4
    
    - Files: pipeline.py
    - Dependencies: [Task 1]
    - Parallelizable: no
    - Estimated LOC: ~50
    - Description: In run_phase4_nm(), after the main nm execution and auto-fix loopback complete (after line 1485, before the return at line 1486), add a new block: if pr_url is set, (a) call _extract_nm_summary(nm_stdout) to get structured summary, (b) fetch existing PR body with gh pr view --json body --jq .body, (c) strip any existing ### nm Review section with regex r'\n### nm Review\n.*?(?=\n### |\n## |\Z)', (d) build new ### nm Review markdown with Risk: <risk>, Key Findings: <summary>, auto-fix section if applicable, and SHOULD FIX list, (e) append to PR body, (f) call vcs.vcs_pr_update_body(pr_num, new_body) to update. Also extract SHOULD FIX items from nm_stdout and create GitHub issues using the same pattern as TL's lines 1746-1831 (extract → loop → gh issue create). Gracefully skip if pr_url is None (no PR found).
    
    Task 3: Update TL PR body injection to preserve and refresh nm section
    
    - Files: pipeline.py
    - Dependencies: [Task 2]
    - Parallelizable: no
    - Estimated LOC: ~20
    - Description: In run_phase5_tech_lead(), at line 1702 where the existing regex strips old ## Review sections: add a second regex to also strip old ### nm Review sections before rebuilding (r'\n### nm Review\n.*?(?=\n### |\n## |\Z)'). Then after appending the new ## Review section (line 1724), also call _extract_nm_summary(nm_output) and inject a fresh ### nm Review section. This ensures both sections are always current after TL review. The nm_output variable is already available as a parameter to run_phase5_tech_lead (line 1540: nm_output=""). If nm_output is empty, skip nm section injection. This handles the case where nm ran and TL is now consolidating findings.
    
    8. Data Model
    
    No new persistent entities. The _extract_nm_summary return dict shape:
    
    python
    {
        "risk": "MEDIUM",           # str — extracted from RISK: line in nm_stdout
        "auto_fix_count": 2,        # int — number of auto-fixable patterns matched
        "auto_fix_labels": [        # list[str] — labels like "missing test", "uncaught exception"
            "missing test",
            "uncaught exception"
        ],
        "key_findings": "...",      # str — first ~2500 chars of review body, or empty
        "should_fix_items": [...]   # list[dict] — from extract_should_fix_from_text()
    }
    
    
    PR body section format:
    
    
    nm Review
    Risk: MEDIUM
    Auto-Fix Applied: 2 issue(s) — missing test, uncaught exception
    Key Findings:
    <nm review text — first ~2500 chars of substantive findings>
    
    SHOULD FIX (3):
    - [RELIABILITY] utils.py:42: Naming conventions for internal functions
    - [RELIABILITY] pipeline.py:100: Extract long method
    - [MAINTAINABILITY] tests/: Add missing edge case test
    
    
    9. API Routes
    
    N/A — no API surface. Internal pipeline functions only.
    
    10. Component Tree
    
    N/A — CLI pipeline modification only.
    
    11. Test Plan (MANDATORY)
    
    Happy Path
    - nm injection at depth=full: After Phase 4 nm completes, PR body should contain ### nm Review with risk and findings. After Phase 5 TL completes, PR body should contain BOTH ### nm Review AND ## Review sections.
    - nm injection at depth=vet+nm: After Phase 4 nm completes (TL is skipped), PR body should contain ### nm Review with risk and findings.
    - SHOULD FIX from nm creates issues: nm_stdout containing SHOULD FIX patterns generates GitHub issues with proper What/Fix/Verify structure.
    
    Edge Cases
    - nm_stdout is empty: _extract_nm_summary returns dict with empty strings/empty lists. Injection gracefully produces a minimal ### nm Review ("No findings").
    - nm_stdout has no RISK line: Risk defaults to "UNKNOWN".
    - PR URL is None (no PR found): run_phase4_nm skips nm injection entirely — prints warning, does not crash.
    - PR body fetch fails (gh pr view returns non-zero): Skip nm injection, print warning, continue pipeline.
    - PR body update fails (vcs_pr_update_body non-zero): Print warning, continue pipeline — nm injection is best-effort, not a blocker.
    - nm_stdout contains 37K chars: _extract_nm_summary truncates key_findings to ~2500 chars. SHOULD FIX extraction handles the full text.
    - TL phase runs without nm_output (nm_output=""): run_phase5_tech_lead skips nm section injection without error.
    - nm re-run after auto-fix (line 1475): The re-run produces fresh nm_stdout. _extract_nm_summary is called on the freshest output (the nm_stdout variable at line 1486).
    - Existing PR body already has ### nm Review from a previous run: Stripped before new injection (regex handles it).
    - GitLab backend (VCS_BACKEND="gitlab"): vcs_pr_update_body delegates to glab mr update. Same logic applies — no GitHub-specific code in the injection path.
    
    Failure Modes
    - extract_should_fix_from_text raises on malformed nm_stdout: Should be caught — the function already handles None/empty input. Ensure try/except around the call.
    - Network failure during gh issue create for nm SHOULD FIX: Print warning, continue. Same pattern as TL's line 1830.
    - Concurrent PR body update (race with another process): gh api PATCH is atomic per GitHub. If another process updates between our fetch and our patch, the latest writer wins. Acceptable — nm injection is supplementary, not critical.
    
    Contract Invariants
    - Before _extract_nm_summary: nm_stdout is a non-None string (may be empty).
    - After _extract_nm_summary: Returns a dict with all keys present (no KeyError). Empty values for missing data.
    - Before PR body injection: pr_url is validated as non-None.
    - After PR body injection: The ### nm Review section either exists in the PR body or a warning was printed.
    - After SHOULD FIX extraction from nm: Issues are created OR a warning is printed. Pipeline never halts on issue creation failure.
    
    12. COTS Build-vs-Buy
    
    Component: vcs.vcs_pr_update_body()
    Buy/Build: Build (existing)
    Justification: Already implemented in vcs.py line 239. Uses gh api PATCH
      or glab mr update.
    ────────────────────────────────────────
    Component: extract_should_fix_from_text()
    Buy/Build: Build (existing)
    Justification: Already implemented in utils.py line 2122. Handles table,
      prose, bullet formats.
    ────────────────────────────────────────
    Component: _extract_nm_summary()
    Buy/Build: Build (new)
    Justification: ~60 LOC. No existing library provides nm-specific output
      parsing. Stdlib re suffices.
    ────────────────────────────────────────
    Component: GitHub Issues API
    Buy/Build: Build (existing)
    Justification: gh issue create pattern already used at line 1825. Reuse
      directly.
    
    13. Panel Split
    
    All 3 tasks are sequential due to file overlap:
    
    
    Wave 1: Task 1 (utils.py) — 1 coder
    Wave 2: Task 2 (pipeline.py, depends on Task 1) — 1 coder
    Wave 3: Task 3 (pipeline.py, depends on Task 2) — 1 coder
    
    
    Tasks 2 and 3 touch different line ranges in pipeline.py (~1396 for Task 2, ~1540 for Task 3) but share the same file and Task 3 depends on Task 2's PR body format. Sequential is safest.
    
    14. Build & Deploy
    
    - Build: python3 -m py_compile dokima + python3 -m py_compile utils.py + python3 -m py_compile pipeline.py
    - Test: python3 -m pytest tests/ -q -k "test_nm or test_f038"
    - Deploy: No deployment — dokima is the panel itself. Changes take effect on next dokima --next run.
    - Env vars: None new. Reuses existing REPO, PROJECT_DIR globals.
    
    15. Risk Register
    
    #: R1
    Risk: _extract_nm_summary produces misleading truncated findings (cuts off
      critical context at 2500 chars)
    Severity: LOW
    Mitigation: Key findings are supplementary — full nm_stdout still logged
      to /tmp/dokima-output.txt. TL review at depth=full provides
      authoritative verdict.
    Trigger: nm finding critical detail is in chars 2501+ of output
    ────────────────────────────────────────
    #: R2
    Risk: nm SHOULD FIX extraction duplicates TL SHOULD FIX (same finding
      extracted twice)
    Severity: LOW
    Mitigation: extract_should_fix_from_text deduplicates by normalized detail
      text. Both phases call it but dedup handles cross-phase duplicates.
    Trigger: Identical SHOULD FIX text in nm and TL output
    ────────────────────────────────────────
    #: R3
    Risk: PR body grows too large with both nm + TL sections
    Severity: LOW
    Mitigation: nm section is capped at ~3000 chars total (2500 findings +
      risk header + SHOULD FIX). TL ## Review is similarly bounded. Total
      addition ~5K chars — well within GitHub's 65K char PR body limit.
    Trigger: PR body approaches 60K+ chars from other content
    ────────────────────────────────────────
    #: R4
    Risk: Regex for stripping ### nm Review accidentally strips other ###
      sections
    Severity: LOW
    Mitigation: Regex is anchored to exact ### nm Review header. Non-greedy
      .*? stops at next ### or ##. Only other nm-named section would be
      affected (unlikely naming collision).
    Trigger: Another section named "nm Review" exists
    
    16. Anti-Creep
    
    Features explicitly NOT in scope:
    
    - DO NOT inject raw 37K nm_stdout into PR body — always extract summary
    - DO NOT add nm findings to the PR review comment (the TL review comment posted by the TL agent) — that's a separate surface
    - DO NOT change the nm script (scripts/nm) — nm output format stays as-is
    - DO NOT change TL prompt or TL auto-fix loopback — TL behavior unchanged
    - DO NOT add nm findings to Slack/Telegram/Discord notifications
    - DO NOT create a new ### TL Review section separate from the existing ## Review — the existing ## Review IS the TL section
    - DO NOT change the existing ## Depth or ## Validation sections
    - DO NOT modify run_fix_pipeline (the fix mode nm injection happens through run_phase4_nm which is called from both pipelines)
    - DO NOT truncate nm_stdout at the source — keep full 37K chars in the log
    
    17. Sign-Off Checklist
    
    - [ ] Accept that nm findings are supplementary — TL verdict at depth=full is authoritative?
    - [ ] 2500-char cap on nm key findings acceptable? (Full output still in /tmp/dokima-output.txt)
    - [ ] nm SHOULD FIX issue creation in Phase 4 acceptable? (Currently only TL creates SHOULD FIX issues at Phase 5)
    - [ ] ### nm Review section name acceptable? (vs ### Adversarial Review or ### nm Findings)
    - [ ] Both nm and TL sections in PR body at depth=full — is this clear or cluttered?
    - [ ] Regex r'\n### nm Review\n.*?(?=\n### |\n## |\Z)' for stripping — confirm it won't over-match?
    - [ ] Graceful skip when PR URL is None acceptable? (Pipeline continues without nm injection)
    - [ ] GitLab MR support: no changes needed beyond reusing vcs.vcs_pr_update_body?
    
    18. Impact Assessment (Grounded)
    
    Based on codebase inspection:
    
    - utils.py (+60 LOC): New _extract_nm_summary function near line 2220 (after extract_should_fix_from_text). Imports needed: re (already imported). Calls extract_should_fix_from_text (already in same file).
    - pipeline.py run_phase4_nm() (+45 LOC): Injection block added after line 1485, before return at 1486. Imports needed: _extract_nm_summary from utils (add to line 14-18 import block), extract_should_fix_from_text (already imported at line 14), vcs (already imported at line 7), gh (already imported at line 12).
    - pipeline.py run_phase5_tech_lead() (+15 LOC): Regex + nm injection added around line 1702-1724. No new imports needed — nm_output is already a parameter.
    - pipeline.py run_pipeline() (0 LOC): No change. Phase 4 injection in run_phase4_nm covers depth=vet+nm path at lines 2730-2748.
    
    Dependency analysis: _extract_nm_summary has no callers in codebase currently (new function). run_phase4_nm is called from run_pipeline (line 2732) and run_fix_pipeline (line 860). Both callers already pass pr_url — no signature change needed. run_phase5_tech_lead is called from run_pipeline (line 2752) and run_fix_pipeline (line 878). Both already pass nm_output — no signature change needed.
    
    Test impact: New tests in tests/test_f038_nm_injection.py (or add to existing tests/test_final_edge.py). Tests needed: _extract_nm_summary on real nm output, empty output, output with no RISK line. Integration: verify PR body has ### nm Review after pipeline phases.
    
    Confidence: High — three targeted injection points, all using proven patterns (same vcs.vcs_pr_update_body + gh issue create as F036/F037). No new dependencies, no architectural changes.