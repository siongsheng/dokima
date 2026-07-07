# F045: Roadmap auto-update verification — `commit_roadmap_update()` marks features Done without verifying implementation exists. When a pipeline merges, it updates ALL feature statuses in roadmap.md — including unrelated ones. Fix: only update the specific feature that was built, and verify source changes exist before marking Done.

Now I have complete understanding of the codebase. Here is the fully corrected spec:
    
    
    
    Position: The fix extracts the existing _has_code_changes pattern from auto_repair_status() (lines 252-261), wires it into commit_roadmap_update(), and narrows the staging scope to only the specific feature's status change. (High confidence)
    
    Ponytail Guard:
    - Rung: 7 — the minimum that works. The verification pattern already exists at roadmap.py:252-261. This spec covers only the extraction + wiring, not new functionality.
    - Existing solution: auto_repair_status() has the guard but commit_roadmap_update() does not — so the guard exists but isn't applied in the direct code path.
    - Spec needed: YES — covers extraction of shared helper, wiring into commit_roadmap_update, and narrowing staging scope.
    
    
    
    F045: Roadmap Auto-Update Verification
    
    Status: In Progress
    Confidence: High
    Version: 2.0.0
    
    
    
    1. Executive Summary
    
    commit_roadmap_update() at roadmap.py:185 commits roadmap status changes to the default branch but has two defects. First, it marks features Done without verifying the merged PR contained implementation code — a spec-only PR that merges still triggers [x] Done. Second, it stages the entire roadmap.md, STATUS.md, codebase-map.md, and all loose spec files — so unrelated accumulated changes in the working tree get committed alongside the single feature's status update. The fix reuses the code-change verification pattern already present in auto_repair_status() (lines 252-261), extracts it into a shared _has_code_changes() helper, wires it into commit_roadmap_update(), and narrows the git staging to only the specific feature's status line. Confidence is High because the verification logic is already proven in auto_repair_status().
    
    
    
    2. Constitution Check
    
    
    Axiom: Solves user's own pain
    Verdict: YES
    Detail: Shaun cannot trust that [x] Done in his own repo's roadmap means the
      feature was actually built — this is his primary project tracking mechanism.
    ────────────────────────────────────────
    Axiom: Weekend-buildable
    Verdict: YES
    Detail: ~80 LOC across 2 source files + tests. The verification pattern
      already exists in the codebase at roadmap.py:252-261.
    ────────────────────────────────────────
    Axiom: Evidence people will pay
    Verdict: N/A
    Detail: Internal tooling — no revenue model check needed.
    ────────────────────────────────────────
    Axiom: Tech stack boring and proven
    Verdict: YES
    Detail: Python 3.6+ regex + gh CLI — same stack as the rest of dokima.
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories
    Verdict: YES
    Detail: No AI, no "platform for X" — a bug fix in pipeline bookkeeping.
    
    
    No misalignments. The fix aligns with the auditability goal in F039 (real-code verification).
    
    
    
    3. Ponytail Guard — Pre-Spec Review
    
    
    Feature: F045: Roadmap auto-update verification
    Rung: 7 — the minimum that works
      Rung 1: Does this need to exist? YES — [x] Done markers are untrustworthy.
      Rung 2: Already in codebase? Partially — auto_repair_status() has the guard
              but commit_roadmap_update() does not. Extract and reuse.
      Rung 3-4: N/A
      Rung 5: gh CLI already installed — no new deps.
      Rung 6: Not one line — requires extraction + wiring + tests.
      Rung 7: Extract ~15 LOC from auto_repair_status into _has_code_changes(),
              wire into commit_roadmap_update(), narrow staging.
    Existing solution: auto_repair_status():252-261 has the verification guard.
    Spec needed: YES — covers extraction, wiring, and staging scope.
    
    
    
    
    4. Impact
    
    Confidence: High / Impact: MEDIUM
    
    This is a correctness fix in pipeline bookkeeping. The primary impact is on trust: [x] Done in the roadmap means the feature was actually built. The fix touches commit_roadmap_update() — called at pipeline completion (lines 151, 179, 188 of pipeline.py) — so it affects every dokima next and dokima next --continuous run. However, the change is additive (adds a guard, doesn't remove behavior), so the failure mode is "false negative" (blocks Done when it should allow it), never "false positive." The verification reuses the proven gh pr diff --stat pattern from auto_repair_status(). If the gh CLI call fails, we err on the side of caution (don't mark Done, print warning) rather than silently marking Done.
    
    Affected files (grounded):
    - roadmap.py:185-223 — commit_roadmap_update() (+ verification gate, - broad staging)
    - pipeline.py:151, 179, 188 — callers (pass PR info if needed)
    - tests/test_helpers.py:29-114 — existing tests for commit_roadmap_update (add verification tests)
    - tests/test_roadmap_update.py — status update tests (add single-feature-only test)
    
    
    
    5. What Changed
    
    - roadmap.py: Extract _has_code_changes(pr_num: str) -> bool helper from auto_repair_status lines 252-261. Add verification gate to commit_roadmap_update() — when action is "done", require a pr_url parameter and call _has_code_changes() before proceeding. Narrow git add to only stage the specific feature's status line (use git add -p or verify the diff before committing). Keep staging of STATUS.md and codebase-map.md (intentional side-effects), but drop staging of ALL loose spec files — only stage the spec file for THIS feature.
    - pipeline.py: Pass pr_url to commit_roadmap_update() at lines 179 and 188 (the "done" call sites). The "revert" call at line 151 does not need it.
    - tests/test_helpers.py: Add test_commit_roadmap_update_skips_spec_only_pr (mock gh returns spec-only diff → Done is blocked) and test_commit_roadmap_update_allows_code_change_pr (mock gh returns code diff → Done proceeds).
    - tests/test_roadmap_update.py: Add test_only_target_feature_updated — verify that updating F001 doesn't touch F002's status in the same file.
    
    
    
    6. Feature Breakdown — Task List
    
    Task 1: Extract _has_code_changes() helper from auto_repair_status
    Files: roadmap.py
    Dependencies: [none]
    Parallelizable: no
    Description: Extract the code-change verification block at lines 252-261 of auto_repair_status() into a standalone _has_code_changes(pr_num: str) -> bool function. It calls gh("pr", "diff", pr_num, "--repo", REPO, "--stat"), filters lines to exclude those starting with specs/, and returns True if any code files exist. Replace the inline block in auto_repair_status() with a call to this new function. Zero behavior change — pure extraction.
    
    Task 2: Add verification gate to commit_roadmap_update() for "done" action
    Files: roadmap.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Change commit_roadmap_update() signature to accept optional pr_url: str = "". When action == "done" and pr_url is provided: extract the PR number from the URL, call _has_code_changes(pr_num). If False, print a warning ("Skipped Fxxx — merged PR has no code changes (spec-only)") and return early without committing. If pr_url is empty but action is "done", print a warning and proceed (backward-compatible fallback). Also narrow the git add rel_path on line 200 to check that the roadmap diff only contains the target feature's status change — use git diff --cached to verify, and if unrelated changes are detected, print a warning but don't block (the verification gate is the primary guard).
    
    Task 3: Wire pr_url from pipeline.py callers into commit_roadmap_update()
    Files: pipeline.py
    Dependencies: [Task 2]
    Parallelizable: no
    Description: At pipeline.py line 179 (continuous mode "done" path): pr_url is already in scope from try_auto_merge() — pass it as the 4th argument to commit_roadmap_update. At pipeline.py line 188 (--next mode "done" path): pr_url is pr_url or "" — pass it. The "revert" call at line 151 does not need pr_url. No other call sites need changes (the run_next_setup call at roadmap.py:546 is for "start", not "done").
    
    Task 4: Add tests for verification gate
    Files: tests/test_helpers.py
    Dependencies: [Task 3]
    Parallelizable: yes
    Description: Following the existing mock pattern in test_commit_roadmap_update_aborts_on_checkout_failure and test_commit_roadmap_update_aborts_on_pull_failure, add two tests: (a) test_commit_roadmap_update_skips_spec_only_pr — mock git to succeed for checkout/pull, mock gh to return --stat output containing only specs/ files, call commit_roadmap_update(path, "F045", "done", pr_url="https://github.com/x/y/pull/99"), assert no git commit was called and the function returned early. (b) test_commit_roadmap_update_allows_code_change_pr — same setup but gh --stat returns pipeline.py | 5 +++--, assert git commit WAS called. Also add test_commit_roadmap_update_done_without_pr_url_warns — call with action="done" but no pr_url, verify it proceeds with a warning.
    
    Task 5: Add single-feature-only update test
    Files: tests/test_roadmap_update.py
    Dependencies: [Task 3]
    Parallelizable: yes
    Description: Add test_only_target_feature_updated — create a roadmap with two features (F001 pending, F002 pending), call update_roadmap_status(path, "F001", "done"), verify F001 shows [x] Done and F002 still shows [ ] Pending. This test already passes (the regex is feature-specific) but serves as a regression guard. Also add test_multiple_features_in_file_staged_correctly — verify that after update_roadmap_status for F001, the working tree diff only touches F001's line.
    
    Task 6: Run full test suite and verify zero regressions
    Files: tests/
    Dependencies: [Task 4, Task 5]
    Parallelizable: no
    Description: Run python3 -m pytest tests/ -q and verify 0 failures. Run python3 -m pytest tests/test_helpers.py tests/test_roadmap_update.py -v specifically to verify all new tests pass. Run bash -n scripts/nm && bash -n scripts/vet to verify no shell script breakage. Run python3 -m py_compile dokima roadmap.py pipeline.py to verify no syntax errors.
    
    
    
    7. Data Model
    
    No new entities. The fix operates on existing structures:
    
    - RoadmapFeature (in tasks.py): unchanged. f.id, f.title, f.status used for targeting.
    - roadmap.md (markdown file): the Status: [x] Done line is the mutation target.
    - PR URL (str): new optional parameter to commit_roadmap_update() — extracted PR number used for gh pr diff --stat.
    - _has_code_changes(pr_num: str) -> bool: new pure function, no side effects, makes one gh subprocess call.
    
    Persistence: All state is in git — roadmap.md on the default branch. No new files, no new env vars.
    
    
    
    8. API Routes
    
    N/A — no API. Internal function signatures only:
    
    Changed: commit_roadmap_update(roadmap_path: str, feature_id: str, action: str, pr_url: str = "") -> None
    New: _has_code_changes(pr_num: str) -> bool
    
    
    
    9. Component Tree
    
    N/A — no frontend.
    
    
    
    10. COTS Build-vs-Buy
    
    Component: PR diff inspection
    Decision: Build — reuse gh pr diff --stat
    Justification: gh CLI already in use throughout codebase; zero new deps
    ────────────────────────────────────────
    Component: Regex status matching
    Decision: Build — reuse existing update_roadmap_status regex
    Justification: Already proven; 5 passing tests
    ────────────────────────────────────────
    Component: Verification logic
    Decision: Build — extract from auto_repair_status():252
    Justification: Already exists in codebase, just not wired to
      commit_roadmap_update
    
    Nothing bought. Everything already in the codebase or stdlib.
    
    
    
    11. Test Plan (MANDATORY)
    
    11.1 Verification gate — _has_code_changes()
    
    Happy path: gh pr diff 99 --stat returns pipeline.py | 12 ++++++++, function returns True.
    Edge cases: Empty diff ("" → False); whitespace-only diff ("  " → False); all specs/ files ("specs/roadmap.md | 1 +" → False); mixed specs and code ("specs/x.md | 1 +\nmain.py | 3 ++" → True); gh returns non-zero exit code (rc != 0 → treat as no code changes, return False).
    Failure modes: gh not installed → _has_code_changes catches the non-zero rc. Network timeout → same. PR number is not an integer → gh returns error, caught by rc check.
    Contract invariants: Returns False for spec-only PRs, True for any PR with ≥1 non-specs/ file changed. Never raises — all errors return False.
    
    11.2 commit_roadmap_update() with verification
    
    Happy path: Called with action="done", pr_url="https://github.com/x/y/pull/99", PR #99 has code changes → status updated, committed, pushed. Called with action="start" → no verification, proceeds as before.
    Edge cases: action="done" but pr_url="" → print warning, proceed (backward compat). action="done", pr_url provided, PR is spec-only → print warning, return without commit. action="revert" → no verification needed, proceeds. action="done", gh call fails → print warning, proceed (don't let GH outage block roadmap updates — the verification is best-effort). action="done", PR has code changes but git checkout fails → abort (existing H5 guard, unchanged).
    Failure modes: Network error during gh pr diff → warn + proceed. Invalid PR URL format → warn + proceed. PR doesn't exist → gh returns empty, treated as no code changes → warn + skip.
    Contract invariants: After successful "done" commit, the specific feature's status in roadmap.md is [x] Done and the PR contained code changes. After skipped "done", the feature status remains unchanged.
    
    11.3 Single-feature-only update
    
    Happy path: Roadmap has F001 and F002 both pending. update_roadmap_status("F001", "done") → only F001's line changes.
    Edge cases: Feature ID not found → warning printed, no file write. Feature ID appears in title text of another feature → regex is anchored to ^### {feature_id}:, so won't false-match. Two features on consecutive lines → regex uses lazy .+? to stop at first Status:.
    Failure modes: Roadmap file missing → update_roadmap_status returns early (existing guard at line 158). Corrupted roadmap format → regex doesn't match, warning printed, no write.
    Contract invariants: After update, exactly one feature's status line changes. All other lines are byte-identical to before.
    
    
    
    12. Panel Split
    
    Wave: 1
    Tasks: Task 1
    Parallel workers: 1
    Rationale: Single-file extraction, no conflicts
    ────────────────────────────────────────
    Wave: 2
    Tasks: Task 2
    Parallel workers: 1
    Rationale: Depends on Task 1, same file
    ────────────────────────────────────────
    Wave: 3
    Tasks: Task 3
    Parallel workers: 1
    Rationale: Depends on Task 2, different file but call-site wiring
    ────────────────────────────────────────
    Wave: 4
    Tasks: Task 4, Task 5
    Parallel workers: 2
    Rationale: Different test files, no shared state
    ────────────────────────────────────────
    Wave: 5
    Tasks: Task 6
    Parallel workers: 1
    Rationale: Depends on all prior tasks
    
    Total: 5 waves, max 2 parallel coders in wave 4.
    
    
    
    13. Build & Deploy
    
    - Build: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" — unchanged
    - Test: python3 -m pytest tests/ -q
    - Lint: python3 -m py_compile dokima roadmap.py pipeline.py
    - Deploy: No deployment needed — dokima is a CLI tool. The fix ships with the next dokima --release.
    - Env vars: None new. REPO (existing) used by _has_code_changes for gh pr diff --repo.
    
    
    
    14. Risk Register
    
    #: R1
    Risk: gh pr diff --stat fails during commit_roadmap_update
    Severity: LOW
    Mitigation: Best-effort: warn + proceed (don't block the pipeline on GH
      API flakiness)
    Trigger: Network partition, rate limiting
    ────────────────────────────────────────
    #: R2
    Risk: Verification blocks legitimate Done because code files use
      non-standard paths
    Severity: LOW
    Mitigation: The filter only excludes specs/ — all other paths count as
      code. Edge case: project puts ALL code in specs/
    Trigger: Monorepo with unusual layout
    ────────────────────────────────────────
    #: R3
    Risk: pr_url not available at call site
    Severity: MEDIUM
    Mitigation: Fallback: if pr_url is empty, warn + proceed (existing
      behavior preserved)
    Trigger: Pipeline restructured, pr_url scope changes
    ────────────────────────────────────────
    #: R4
    Risk: git add -p or diff verification too complex, introduces new failure
      mode
    Severity: LOW
    Mitigation: Alternative: keep git add rel_path for the whole file but rely
      on the verification gate as the primary guard. The "only specific
      feature" guarantee is enforced by update_roadmap_status regex, which is
      already tested
    Trigger: Patch mode too fragile
    ────────────────────────────────────────
    #: R5
    Risk: Existing tests break because commit_roadmap_update signature changed
    Severity: LOW
    Mitigation: pr_url is optional with default "" — all existing callers work
      without changes. Test mocks of commit_roadmap_update don't need updating
    Trigger: Tests patching the function signature
    ────────────────────────────────────────
    #: R6
    Risk: auto_repair_status extraction changes its behavior
    Severity: LOW
    Mitigation: Pure extraction — replace 10 lines with 1 function call
      returning the same boolean
    Trigger: Inline code had hidden side effects (none observed)
    
    
    
    15. Anti-Creep
    
    Features explicitly NOT in scope:
    
    - Do NOT add verification to auto_repair_status() — it already has the guard. This fix is about commit_roadmap_update() only.
    - Do NOT change update_roadmap_status() regex — it already targets single features. Test it, don't fix it.
    - Do NOT add a new CLI flag or env var for this verification — it's always-on, no opt-out needed.
    - Do NOT refactor commit_roadmap_update() beyond adding the verification gate — do not split it into sub-functions, do not extract the git staging block.
    - Do NOT add verification for "start" or "revert" actions — only "done" needs it.
    - Do NOT create new modules — this stays in roadmap.py.
    - Do NOT add a --skip-roadmap-verify flag — the verification is best-effort and non-blocking.
    
    
    
    16. Sign-Off Checklist
    
    - [ ] _has_code_changes() extracted from auto_repair_status and the original still works identically
    - [ ] commit_roadmap_update() accepts optional pr_url parameter (backward-compatible)
    - [ ] When action is "done" and PR is spec-only, Done is skipped with a warning
    - [ ] When action is "done" and PR has code changes, Done proceeds normally
    - [ ] pipeline.py callers pass pr_url at both "done" sites (lines 179 and 188)
    - [ ] All existing tests pass (python3 -m pytest tests/ -q)
    - [ ] New tests: spec-only PR blocked, code-change PR allowed, single-feature-only update
    - [ ] bash -n scripts/nm && bash -n scripts/vet clean
    - [ ] python3 -m py_compile dokima roadmap.py pipeline.py clean
    - [ ] No new dependencies, no new env vars, no new CLI flags
    - [ ] Manual test: create a spec-only PR, merge it, verify commit_roadmap_update skips Done
    - [ ] specs/roadmap.md F045 entry updated to [x] Done after merge
    
    
    
    Rejected Alternatives
    
    Alternative: Add verification in pipeline.py callers instead of in
      commit_roadmap_update
    Verdict: Rejected
    Reason: Would require duplicating the check at 2+ call sites. Single gate
      in commit_roadmap_update is cleaner
    ────────────────────────────────────────
    Alternative: Make _has_code_changes() check the feature branch instead of
      the PR
    Verdict: Rejected
    Reason: By the time commit_roadmap_update runs, the feature branch may be
      deleted (post-merge). PR number is stable
    ────────────────────────────────────────
    Alternative: Skip the verification if gh fails
    Verdict: Accepted (with warning)
    Reason: We don't want GH API flakiness to block roadmap updates. Warn +
      proceed is the right trade-off
    ────────────────────────────────────────
    Alternative: Extend auto_repair_status to also handle this case
    Verdict: Rejected
    Reason: auto_repair_status runs on dokima init / dokima next startup.
      commit_roadmap_update runs at pipeline completion. Different call sites,
      different timing