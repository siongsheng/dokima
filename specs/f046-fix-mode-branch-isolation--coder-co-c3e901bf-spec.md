# F046: Fix mode branch isolation — coder commits directly to main instead of the fix branch. The coder prompt says "switch to branch fix/issue-N" but the coder ignores it or the pipeline doesn't enforce it. Fix: verify coder is on the correct branch before vet phase, or make the branch checkout mandatory in the prompt.
    
    
    
    
    F046: Fix Mode Branch Isolation
    
    Status: Awaiting Implementation
    Confidence: High
    Version: 1.1.0 — quality correction (added Impact, What Changed, proper Task headers, fixed parallelism)
    
    
    
    Executive Summary
    
    dokima fix --issue N creates a fix/issue-N branch but the coder prompt only
    suggests switching — it doesn't enforce. The coder can (and does) commit directly
    to main. This is a two-part gap: (a) the fix/issue-N branch is never pushed to
    origin so the coder's git fetch origin fix/issue-N fails, and (b) the vet phase
    doesn't verify what branch it's testing. Fix: push the branch to origin before
    spawning the coder, add a _verify_branch() pre-flight check, and add vet-phase
    guard that refuses to test main. Three tasks, ~100 LOC, one test file.
    
    
    
    Impact
    
    What Breaks (before): dokima fix --issue 42 creates branch locally, coder
    cannot fetch it from origin, coder stays on main, commits go to main. Fixes
    contaminate the default branch.
    
    What Changes (after): Each fix lands on fix/issue-N and only
    fix/issue-N. Vet phase refuses to proceed if on main/master. Coder prompt
    enforces checkout with pre-flight verification.
    
    Files touched:
    - pipeline.py — run_fix_mode_issue() (+12/-2), run_phase2_coder() (+8/-2), run_phase3_vet() (+6/-0)
    - tests/test_fix_mode.py — new tests (+80/-0)
    
    Regression risk: Low. Changes are additive guards in fix-mode paths. Normal
    feature pipeline (dokima next) unchanged.
    
    
    
    What Changed (from v1.0)
    
    This is a quality-corrected version of the initial spec (commit 6c8559f). Fixes:
    
    1. Added Impact section — files touched, regression risk, before/after behavior.
    2. Added What Changed section — documents corrections from the initial truncated spec.
    3. Fixed Task N: headers — all five fields present per panel parse format.
    4. Fixed Task 3+4 parallelism — Task 3 (vet guard) and Task 4 (coder prompt
       enforcement) now touch different files. Task 3 is in pipeline.py, Task 4 is
       in the coder prompt (same file but can be done in parallel with safeguards).
       Actually — they both touch pipeline.py, so they remain sequential but now
       properly labeled with clear dependency chains.
    
    
    
    Constitution Check
    
    Axiom: User's own pain?
    Verdict: Yes — Shaun runs dokima fix and finds commits on main. Blocking
      dogfooding.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Verdict: Yes — ~100 LOC, 3 small changes, 1 test file.
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Verdict: N/A — internal tool, not SaaS. Value is operational correctness.
    ────────────────────────────────────────
    Axiom: Tech stack boring/proven?
    Verdict: Yes — Python + git, same stack as all of dokima.
    ────────────────────────────────────────
    Axiom: Avoids AI hype?
    Verdict: Yes — pure engineering fix, no AI.
    
    No constitution violations. Aligned.
    
    
    
    Feature Breakdown
    
    Task 1: Push fix/issue branch to origin before spawning coder
    - Files: pipeline.py
    - Dependencies: [none]
    - Parallelizable: no (blocked by Task 2 — same file region)
    - Estimated LOC: ~12
    - Description: In run_fix_mode_issue() (line 383-384): after git checkout -b branch, add git push -u origin branch so the coder can git fetch origin fix/issue-N. Without this push, the coder's git fetch origin fix/issue-N && git checkout fix/issue-N fails silently and the coder stays on main.
    
    Task 2: Add _verify_branch() helper function
    - Files: pipeline.py
    - Dependencies: [none]
    - Parallelizable: no (shares pipeline.py with Task 1)
    - Estimated LOC: ~25
    - Description: Add a _verify_branch(branch) function that: (1) runs git rev-parse --abbrev-ref HEAD to get current branch, (2) if current != branch, runs git checkout branch and re-verifies, (3) if still not on branch, raises a clear error: "FATAL: Not on branch {branch} — refusing to proceed." Return True on success. This is called before vet and before coder spawn in fix mode.
    
    Task 3: Add branch guard in vet phase (run_phase3_vet)
    - Files: pipeline.py
    - Dependencies: [Task 2]
    - Parallelizable: no (sequential: needs _verify_branch)
    - Estimated LOC: ~8
    - Description: In run_phase3_vet() (before line 993): call _verify_branch(branch). If it returns False or the current branch matches DEFAULT_BRANCH, halt with "FATAL: vet phase must run on feature branch, not main." This catches any case where the coder ignored the branch switch and committed to main.
    
    Task 4: Harden coder prompt — mandatory branch checkout with pre-flight
    - Files: pipeline.py
    - Dependencies: [Task 2]
    - Parallelizable: no (sequential: needs _verify_branch — also shares pipeline.py with Task 3, so strict ordering)
    - Estimated LOC: ~10
    - Description: In run_phase2_coder() fix-mode branch setup prompt (lines 723-728): replace the suggestion with a mandatory instruction. Instead of "FIRST: Switch to the existing branch", write: "MANDATORY PRE-FLIGHT — Before writing ANY code, run: git fetch origin {branch} && git checkout {branch} && echo 'BRANCH VERIFIED: {branch}'. If the checkout fails, STOP immediately and report the error. Do NOT write any code until you confirm you are on branch '{branch}'." This enforces branch isolation before the coder writes a single line.
    
    Task 5: Add tests for branch isolation
    - Files: tests/test_fix_mode.py
    - Dependencies: [Task 1, Task 2, Task 3, Task 4]
    - Parallelizable: no (needs all implementation to exist first)
    - Estimated LOC: ~80
    - Description: Add 4 new tests: (a) test_fix_mode_issue_pushes_branch_to_origin — verify git push -u origin is called after branch creation, (b) test_verify_branch_on_correct_branch — _verify_branch returns True when already on branch, (c) test_verify_branch_fails_and_halts — _verify_branch on wrong branch triggers halt, (d) test_vet_refuses_default_branch — run_phase3_vet refuses to test main/master.
    
    
    
    Data Model
    
    No new persistent data. The fix/issue-N branch is a transient git artifact. The
    only new entity is the _verify_branch() function return value (boolean).
    
    Entity: fix/issue-N branch
    Fields: name: str
    Storage: git repository
    Lifecycle: Created during fix, deleted after merge
    ────────────────────────────────────────
    Entity: _verify_branch() result
    Fields: bool
    Storage: In-memory only
    Lifecycle: Per-pipeline-run
    
    
    
    API Routes
    
    None. This is an internal pipeline fix, not an API.
    
    
    
    Component Tree
    
    N/A — dokima is CLI-only. No frontend.
    
    
    
    COTS Build-vs-Buy
    
    Component: Branch verification
    Build/Buy: Build
    Justification: 5 lines of git rev-parse --abbrev-ref HEAD — no dependency
      needed
    ────────────────────────────────────────
    Component: Git push to origin
    Build/Buy: Build
    Justification: Already using git() wrapper — no new dependency
    ────────────────────────────────────────
    Component: Branch name detection
    Build/Buy: Reuse
    Justification: _detect_default_branch() already exists in git_ops.py
    
    All build. No new dependencies.
    
    
    
    Test Plan (MANDATORY)
    
    Feature area: Branch push to origin (Task 1)
    
    - Happy path: run_fix_mode_issue("/tmp/test", 42) → git push -u origin fix/issue-42
      is called immediately after git checkout -b fix/issue-42.
    - Edge cases:
      - Push fails (no network, no remote) — function should log warning but not crash. Coder
        will then fail to fetch, which is a coder-level error — acceptable.
      - Branch already exists on origin (from prior failed run) — git push -u will fail
        with "failed to push some refs." Must catch this and use git push origin fix/issue-42
        without -u.
    - Failure modes: No remote configured, network timeout, auth failure.
    - Contract invariants: After Task 1 completes, origin/fix/issue-N must exist (or a
      clear warning must be logged).
    
    Feature area: _verify_branch() helper (Task 2)
    
    - Happy path: _verify_branch("fix/issue-42") called while on fix/issue-42 → returns True.
    - Edge cases:
      - Detached HEAD state — git rev-parse --abbrev-ref HEAD returns "HEAD". Must detect
        this and refuse.
      - Branch name has special characters — git handles this natively, no escaping needed.
      - Empty branch name passed — raise ValueError.
      - Branch doesn't exist locally or remotely — git checkout will fail, function
        should return False.
    - Failure modes: Git not installed (should never happen in dokima context), disk full
      (cannot write .git/HEAD).
    - Contract invariants: _verify_branch() never raises uncaught exceptions. Always
      returns True or halts the pipeline.
    
    Feature area: Vet phase branch guard (Task 3)
    
    - Happy path: run_phase3_vet called with branch="fix/issue-42", currently on
      fix/issue-42 → proceeds to tests.
    - Edge cases:
      - Current branch is main or master — halt immediately with clear error.
      - Current branch is feat/something-else (not the expected branch) — halt.
      - Branch matches but is a substring of another branch name — git rev-parse returns
        exact match, no substring ambiguity.
    - Failure modes: Git state corrupted — _verify_branch should raise, vet phase halts.
    - Contract invariants: Vet phase NEVER runs tests on DEFAULT_BRANCH. The branch
      being tested must exactly match the expected branch name.
    
    Feature area: Coder prompt enforcement (Task 4)
    
    - Happy path: Coder reads prompt, runs `git fetch origin fix/issue-42 && git checkout
      fix/issue-42`, confirms branch, begins coding.
    - Edge cases:
      - Coder ignores prompt — vet phase guard (Task 3) catches this. Two-layer defense.
      - Coder creates a NEW branch instead of switching — vet guard catches this too since
        the branch name won't match.
      - Branch not on origin yet (race with Task 1) — git fetch will fail, coder should
        STOP per prompt instructions.
    - Failure modes: Coder cannot reach origin (network), coder's git state is dirty —
      prompt instructs to report error and stop.
    - Contract invariants: Coder prompt is the first line of defense. Vet phase guard
      is the second. Both must fail for a main-commit to slip through.
    
    
    
    Panel Split
    
    All 5 tasks are sequential — they share pipeline.py and Task 2 is a dependency
    for Tasks 3 and 4. Task 5 (tests) must run last since it depends on all
    implementation.
    
    Wave: 1
    Tasks: Task 1 + Task 2
    Coders: 1 (Task 1 → Task 2 sequential within one coder session)
    ────────────────────────────────────────
    Wave: 2
    Tasks: Task 3 + Task 4
    Coders: 1 (Task 3 → Task 4 sequential within one coder session)
    ────────────────────────────────────────
    Wave: 3
    Tasks: Task 5
    Coders: 1
    
    3 waves, 1 coder. Total estimated time: ~45 minutes.
    
    
    
    Build & Deploy
    
    No CI changes needed. Standard dokima pipeline:
    bash
    python3 -m pytest tests/test_fix_mode.py -v  # verify new tests pass
    python3 -m pytest tests/ -q                   # full regression suite (1033 tests)
    python3 -m py_compile dokima                  # lint
    
    
    Deploy: merge PR to main. No infrastructure changes.
    
    
    
    Risk Register
    
    #: R1
    Risk: Push fix/issue-N to origin pollutes remote with stale branches
    Severity: Low
    Mitigation: fix branches are cleaned up on merge. Already convention.
    Trigger: Branch left after merge
    ────────────────────────────────────────
    #: R2
    Risk: _verify_branch() false-positive halts valid pipeline
    Severity: Medium
    Mitigation: Test both happy path and edge cases thoroughly. Make error
      message actionable.
    Trigger: Detached HEAD, race with branch creation
    ────────────────────────────────────────
    #: R3
    Risk: Coder ignores mandatory prompt language (same as current)
    Severity: Medium
    Mitigation: Vet guard (Task 3) is the kill-switch. Two-layer defense.
    Trigger: Vet guard removed in future refactor
    ────────────────────────────────────────
    #: R4
    Risk: git push -u fails silently on some git versions
    Severity: Low
    Mitigation: Check return code. Log warning. Proceed — coder will fail
      fetch.
    Trigger: Old git version (<2.0)
    ────────────────────────────────────────
    #: R5
    Risk: DEFAULT_BRANCH detection fails (detached HEAD, shallow clone)
    Severity: Low
    Mitigation: Already handled in _detect_default_branch() — falls back to
      'master'.
    Trigger: Corrupted git metadata
    
    
    
    Anti-Creep
    
    Features explicitly NOT in scope:
    
    - Do NOT add branch verification for the non-fix feature pipeline (dokima next).
      The feature pipeline already pushes branches and checks out correctly.
    - Do NOT add branch cleanup (deleting stale fix/issue-N branches). Existing cleanup
      mechanisms handle this.
    - Do NOT add worktree branch isolation. This is fix-mode only — worktrees already
      create their own branches.
    - Do NOT add GitLab (glab) support for push in this feature. That's F035 territory.
    - Do NOT refactor run_fix_mode() for the BLOCKED-PR path (lines 419+). That path
      already does git checkout pr_branch at line 583 and is not the bug. Only
      run_fix_mode_issue() (lines 306+) has the gap.
    
    
    
    Sign-Off Checklist
    
    - [ ] Branch fix/issue-N is pushed to origin BEFORE coder spawn in run_fix_mode_issue()
    - [ ] _verify_branch() helper exists and handles: correct branch, wrong branch, detached HEAD, empty input
    - [ ] Vet phase calls _verify_branch() and refuses DEFAULT_BRANCH
    - [ ] Coder prompt says "MANDATORY PRE-FLIGHT" with explicit STOP instruction
    - [ ] Tests cover all 4 new test cases
    - [ ] Full regression suite passes (1033 tests)
    - [ ] dokima fix --issue 42 end-to-end tested manually
    - [ ] No new dependencies added
    - [ ] No changes to non-fix pipeline paths
    - [ ] Commit message: fix: enforce branch isolation in fix mode — push branch, verify checkout, guard vet phase
    
    
    
    Open Questions
    
    None. All assumptions verified against existing codebase. Confidence: High.