# F010: Parallel Coder Robustness

Now I have full context. Let me produce the complete corrected F010 spec.
    
    Spec: F010 — Parallel Coder Robustness
    Feature: F010
    Status: In Progress
    Version: 1.0 (initial)
    Confidence: High
    Impact: MEDIUM
    
    Executive Summary
    
    The parallel coder path in dokima (lines 1709-1834) has three robustness gaps: worktrees leak on pipeline halt (halt_and_revert doesn't clean them), proc.communicate() in _reap_completed can hang on zombie children, and file-collision detection misses path-variant conflicts (./src/a.py vs src/a.py). Additionally, overflow tasks run sequentially instead of batched, stale lock files persist after crashes, and task branches accumulate on failure. Six targeted fixes, ~80 net LOC, zero new dependencies. After this feature, parallel coder pipelines are safe for --continuous operation.
    
    Ponytail Guard — Pre-Spec Review
    
    Feature: F010: Parallel Coder Robustness
    Rung: 6-7 — Targeted bugfixes to existing code. No stdlib replacement possible (these are logic gaps, not feature gaps). The worktree manager, task lock, and wave poller already exist — this just hardens them.
    Existing solution: validate_parallel_files, _poll_until_wave_done, WorktreeManager.create stale-pruning (all partial)
    Spec needed: Yes — covering the 6 gaps not handled by existing code.
    
    Constitution Check
    
    Axiom: Does it solve the user's own pain?
    Status: YES — Shaun runs dokima --continuous; leaked worktrees accumulate and block future pipelines
    ────────────────────────────────────────
    Axiom: Is it weekend-buildable?
    Status: YES — 7 tasks, ~80 LOC, one session
    ────────────────────────────────────────
    Axiom: Is there evidence people will pay?
    Status: N/A — internal tool. Evidence: known bug 11 (merge assembly fails on same-file branches) and worktree leak documented in MAINTAINERS.md cleanup section
    ────────────────────────────────────────
    Axiom: Is the tech stack boring and proven?
    Status: YES — pure Python try/finally, os.path.normpath, subprocess patterns already in codebase
    ────────────────────────────────────────
    Axiom: Does it avoid AI hype categories?
    Status: YES — no AI, just robustness hardening
    
    Verdict: PASS. Aligned with F006 (Error Recovery) and F023 (Pipeline Self-Healing) which depends on F010.
    
    Robustness Gaps — Inventory
    
    Gap                          Line(s)       Severity   Blocks --continuous?
    ── ──────────────────────────── ───────────── ────────   ──────────────────
    1  Worktree leak on halt        1830-1834     HIGH      YES — accumulates .dokima/worktrees/
    2  proc.communicate() hang      1616          MEDIUM    YES — blocks wave reaping forever
    3  File collision path variance 897-909       MEDIUM    NO — false negative on same-file conflicts
    4  Stale lock file persistence  778-787       LOW       YES — blocks future task claiming
    5  Overflow tasks sequential    1798-1816     LOW       NO — wastes parallelism
    6  Task branch leak on failure  4949-4962     MEDIUM    YES — accumulates stale branches
    
    Decision Table
    
    Approach: SINGLE APPROACH: Targeted fixes to existing functions
    Cost: ~80 LOC across 1 file (dokima) + tests
    Risk: Low — all changes are additive hardenings; existing behavior preserved
    Speed: Immediate
    
    No alternative needed — these are bugfixes to production code. The patterns (try/finally, normpath, batch spawning) already exist elsewhere in the codebase.
    
    Impact
    
    Parallel coder pipelines survive halt/hung-agents without worktree leaks, file-collision detection catches all path-variant conflicts, and stale lock files are cleaned at pipeline start. Operators can run --continuous without manual cleanup between iterations.
    
    What Changed
    
    - dokima lines 1709-1834: run_parallel_coders() — wrap in try/finally for guaranteed worktree cleanup on exception/halt
    - dokima lines 577-593: halt_and_revert() — accept optional task_ids parameter, delete task branches + worktrees on parallel coder failures
    - dokima lines 1608-1633: _reap_completed() — drain pipes with non-blocking read before communicate(), add SIGKILL escalation for hung children
    - dokima lines 897-909: validate_parallel_files() — apply os.path.normpath() to normalize ./src/a.py → src/a.py
    - dokima lines 1798-1816: overflow tasks — batch into sub-waves of up to max_parallel instead of sequential
    - tests/test_parallel_robustness.py: new test file — worktree leak, communicate hang, path collision, lock cleanup, overflow batching, branch cleanup
    
    Data Model
    
    No new entities. Existing classes affected:
    - WorktreeManager.cleanup_all(): already exists, now guaranteed to run (try/finally)
    - TaskLock: new cleanup_stale() method to purge .dokima/tasks/*.lock at init
    - Task.status: new "orphaned" status for tasks whose agents were killed (SIGKILL after SIGTERM timeout)
    
    API / Interface Proposal
    
    N/A — internal pipeline robustness change only. halt_and_revert() signature gains optional task_ids parameter (backward-compatible). No CLI flags, env vars, or user-facing API changes.
    
    Security Considerations
    
    N/A — no attack surface change. These changes only affect cleanup behavior after pipeline failure.
    
    Documentation Impact
    
    MAINTAINERS.md: Update pipeline cleanup section (lines 127-143) to note that worktree cleanup is now automatic, and remove the manual rm -rf .dokima/worktrees/ step. Add new "Parallel Coder Robustness" gotcha section.
    
    Impact Assessment (Grounded)
    
    
    $ git log --oneline -5 -- dokima
    ecc83a4 chore: mark F010 as in progress [panel]
    06c4291 feat: F009: Depth Gating Tuning (#24)
    4a3641b feat: harden confidence parser with word-boundary check
    f6570e9 chore: mark F009 as in progress [panel]
    a83d479 fix: --fix-all must set is_fix=True to dispatch to fix mode
    
    
    
    $ grep -n "halt_and_revert\|run_parallel_coders\|_reap_completed\|validate_parallel_files\|TaskLock" dokima | head -20
    577: def halt_and_revert(reason, phase, branch):
    772: class TaskLock:
    897: def validate_parallel_files(self, wave):
    1608: def _reap_completed(running, tasks, locks):
    1709: def run_parallel_coders(tasks, waves, project_dir, spec_path, tasks_extract_path):
    
    
    Affected code: dokima lines 577-593 (halt_and_revert), 772-804 (TaskLock), 897-909 (validate_parallel_files), 1608-1633 (_reap_completed), 1709-1834 (run_parallel_coders), 4938-4963 (caller site in run_pipeline). Tests: new file tests/test_parallel_robustness.py. No other files touch these functions directly except test mocks.
    
    Test Plan (MANDATORY)
    
    Feature Area: Worktree Cleanup on Halt
    
    Happy path: 
    - run_parallel_coders() completes normally → cleanup_all() runs, all worktrees removed, all task branches deleted.
    - run_parallel_coders() raises exception mid-wave → finally block runs cleanup_all(), no worktrees left behind.
    
    Edge cases:
    - What if cleanup_all() itself raises? (Nested exception in finally — log and continue, don't mask original.)
    - What if some worktrees were already cleaned manually? (cleanup() handles FileNotFoundError via try/except — already resilient.)
    - What if halt_and_revert is called with task_ids=None? (Backward-compatible: skip task branch cleanup, keep current behavior.)
    
    Failure modes:
    - Disk full preventing git worktree remove → log warning, don't crash
    - git command timeout during cleanup → force-delete directory with shutil.rmtree as fallback (already in cleanup())
    
    Contract invariants:
    - After run_parallel_coders() returns (success or exception), .dokima/worktrees/ is empty
    - After halt_and_revert() with task_ids, all task branches are deleted
    - No task branch leak on any exit path from run_parallel_coders()
    
    Feature Area: proc.communicate() Hang Prevention
    
    Happy path:
    - Process exits normally → _reap_completed drains stdout/stderr pipes, captures output, releases lock.
    
    Edge cases:
    - Process has zombie children holding pipe open → non-blocking read drains available data, then SIGTERM children, then SIGKILL escalation after 2s.
    - Process already exited but pipe buffer full → read in chunks of 4096 bytes, concatenate.
    - Process exited with signal (SIGSEGV) → proc.returncode is negative, mark task as failed.
    
    Failure modes:
    - Popen.stdout is None (shouldn't happen with universal_newlines=True, but guard)
    - communicate() raises TimeoutExpired → fall back to non-blocking read + proc.kill()
    - read() raises BrokenPipeError → catch, return whatever we have
    
    Contract invariants:
    - _reap_completed always releases the task lock before returning
    - Task status is always set (completed/failed/timed_out/orphaned)
    - Task.output always set (partial output is better than none)
    
    Feature Area: File Collision Path Normalization
    
    Happy path:
    - Task 1 claims "src/utils.py", Task 2 claims "./src/utils.py" → collision detected.
    - Task 1 claims "a/b/c.py", Task 2 claims "d/e/f.py" → no collision.
    
    Edge cases:
    - What about "../src/utils.py" escaping the repo root? (normpath resolves it; then verify it starts with project_dir — if not, reject/report invalid path.)
    - What about backslashes on Windows? (os.path.normpath handles platform separators.)
    - What about trailing slashes in directory paths? (normpath strips them.)
    
    Failure modes:
    - Empty file list for one task → skip that task in collision check
    - Very long path (os.path.normpath doesn't overflow)
    
    Contract invariants:
    - Same physical file never claimed by two tasks in the same wave
    - Path normalization is deterministic and idempotent
    
    Feature Area: Stale Lock File Cleanup
    
    Happy path:
    - Pipeline starts, stale .dokima/tasks/*.lock files from previous crashed run are deleted.
    - TaskLock.init cleans stale locks (process owner PID no longer alive).
    
    Edge cases:
    - Lock file owner PID is alive but not a dokima process → keep lock (defensive).
    - Lock file is corrupt (can't read owner PID) → delete (treat as stale).
    - Multiple pipeline instances running concurrently → don't touch locks owned by the other instance (different agent_id prefix).
    
    Failure modes:
    - Permission denied on lock file → log warning, skip (don't block pipeline start).
    - Directory doesn't exist yet → create it.
    
    Contract invariants:
    - No stale lock blocks a fresh pipeline run
    - Active locks (current pipeline) never deleted
    - TaskLock.claim() still uses O_EXCL for atomicity
    
    Feature Area: Overflow Task Batching
    
    Happy path:
    - Wave has 12 tasks, max_parallel=5 → first 5 spawn in parallel, then next 5 spawn in parallel, then last 2 spawn in parallel. 3 sub-waves instead of 1 + 7 sequential.
    
    Edge cases:
    - max_parallel=1 → all tasks sequential (degenerate case, correct).
    - max_parallel larger than remaining tasks → all remaining in one batch.
    - Overflow batching respects file collision within sub-wave (validate_parallel_files called per sub-wave).
    
    Failure modes:
    - One task in overflow batch fails → continue with remaining tasks (current behavior, keep).
    - max_parallel_override is None → default to 5.
    
    Contract invariants:
    - Total tasks spawned = wave size
    - No sub-wave exceeds max_parallel
    - File collision check runs per sub-wave
    
    Feature Area: Task Branch Leak on Failure
    
    Happy path:
    - halt_and_revert("All parallel coders failed", ..., branch, task_ids=["1","2","3"]) → deletes feat/<slug>-t1, feat/<slug>-t2, feat/<slug>-t3 branches before deleting main branch.
    
    Edge cases:
    - task_ids contains tasks that were never created (crashed before worktree creation) → git branch -D silently fails for non-existent branches (already handled).
    - task_ids parameter omitted → skip task branch cleanup (backward-compatible).
    
    Failure modes:
    - git branch -D fails (disk full, git corruption) → log warning, continue with main branch cleanup.
    
    Contract invariants:
    - After halt_and_revert with task_ids, git branch --list shows no task branches for this feature
    - Main feature branch still deleted (existing behavior preserved)
    
    Task Breakdown
    
    Task 1: Wrap run_parallel_coders in try/finally for worktree cleanup
    Files: dokima
    Dependencies: none
    Parallelizable: no
    Description: Wrap existing cleanup_all() call and halt paths in run_parallel_coders() (lines 1709-1834) with try/finally to guarantee WorktreeManager.cleanup_all() runs on every exit path — normal completion, exception, or halt_and_revert.
    
    Task 2: Extend halt_and_revert to clean task branches + worktrees
    Files: dokima
    Dependencies: none
    Parallelizable: yes (with Task 3)
    Description: Add optional task_ids parameter to halt_and_revert() (line 577). When provided, iterate task branches (feat/<slug>-tN) and delete them via git branch -D before deleting the main feature branch. Also accept optional worktrees manager reference to call cleanup_all().
    
    Task 3: Harden _reap_completed against proc.communicate() hang
    Files: dokima
    Dependencies: none
    Parallelizable: yes (with Task 2)
    Description: Replace blocking proc.communicate(timeout=5) in _reap_completed() (line 1616) with non-blocking pipe drain: read proc.stdout in 4096-byte chunks after poll() confirms exit, then call proc.wait(timeout=2) to reap. If wait times out, escalate to SIGKILL and mark task as "orphaned". Catch BrokenPipeError.
    
    Task 4: Normalize file paths in validate_parallel_files
    Files: dokima
    Dependencies: none
    Parallelizable: yes (with Task 5)
    Description: Apply os.path.normpath() to each file before case-normalized comparison in validate_parallel_files() (line 897-909). This catches ./src/a.py ≡ src/a.py and a//b.py ≡ a/b.py. Add rejection for paths that normpath resolves outside project_dir.
    
    Task 5: Clean stale lock files at TaskLock init
    Files: dokima
    Dependencies: none
    Parallelizable: yes (with Task 4)
    Description: Add cleanup_stale() method to TaskLock (line 772). On init, scan .dokima/tasks/*.lock, read owner PID, check if PID alive. Delete locks with dead PIDs. Skip locks with unparseable owner field. Skip locks with different agent_id prefix (different pipeline instance).
    
    Task 6: Batch overflow tasks into sub-waves
    Files: dokima
    Dependencies: none
    Parallelizable: yes (with Task 5)
    Description: Replace sequential single-task spawning for overflow (lines 1798-1816) with batched sub-wave spawning: split overflow list into chunks of max_parallel, spawn each chunk as a mini-wave with _poll_until_wave_done. Run validate_parallel_files per sub-wave for safety.
    
    Task 7: Wire halt_and_revert task_ids at caller sites + add tests
    Files: dokima, tests/test_parallel_robustness.py
    Dependencies: Task 1, Task 2, Task 3, Task 4, Task 5, Task 6
    Parallelizable: no
    Description: Update the three halt_and_revert() call sites in run_pipeline (lines 4949, 4956, 4961) to pass task_ids from dag.tasks. Create tests/test_parallel_robustness.py with pytest tests covering: (a) worktree cleanup on exception, (b) halt_and_revert task branch deletion, (c) proc.communicate hang via mock zombie process, (d) path collision normalization, (e) stale lock cleanup, (f) overflow batching, (g) backward compatibility of halt_and_revert without task_ids.
    
    Panel Split
    
    Wave 1 (parallel — no shared files):
      Task 2: halt_and_revert extension (dokima lines 577-593)
      Task 3: _reap_completed hardening (dokima lines 1608-1633)
      Task 4: validate_parallel_files normpath (dokima lines 897-909)
      Task 5: TaskLock stale cleanup (dokima lines 772-804)
      Task 6: overflow batching (dokima lines 1798-1816)
    
    Wave 2 (sequential — depends on Task 1 completing first, needs all changes in place):
      Task 1: run_parallel_coders try/finally (dokima lines 1709-1834)
    
    Wave 3 (sequential — depends on all code changes):
      Task 7: Wire halt_and_revert + add tests
    
    2 coder agents. Wave 1 is the parallel opportunity — Tasks 2-6 touch different functions in different line ranges with no overlap. Task 1 runs after (needs to wrap the full function body, conflicts with other changes if parallel). Task 7 runs last (needs all code settled).
    
    Build & Deploy
    
    - Deploy: git push origin feat/f010-parallel-coder-robustness → PR merge to main
    - CI: python3 -m pytest tests/ -q must pass (495+ tests)
    - Env vars: None new. Existing PANEL_MAX_PARALLEL continues to work
    - No new dependencies
    
    Risk Register
    
    #: 1
    Risk: try/finally in run_parallel_coders double-cleans worktrees if halt_and_revert also cleans them
    Severity: LOW
    Mitigation: cleanup_all() and cleanup() are idempotent — removing already-removed worktrees is a no-op (FileNotFoundError caught)
    Trigger: halt_and_revert called with task_ids + finally block also fires
    ────────────────────────────────────────
    #: 2
    Risk: proc.communicate() replacement changes output capture behavior
    Severity: MEDIUM
    Mitigation: Existing tests mock Popen.poll/communicate; new approach uses same interfaces. Test with real subprocess to verify output completeness
    Trigger: Output truncation on large coder output (>50KB)
    ────────────────────────────────────────
    #: 3
    Risk: normpath on attacker-crafted "../" path resolves outside repo
    Severity: LOW
    Mitigation: After normpath, verify path stays within project_dir. Reject and log warning if it doesn't.
    Trigger: Spec with crafted file paths
    ────────────────────────────────────────
    #: 4
    Risk: Stale lock cleanup deletes active lock from concurrent pipeline instance
    Severity: LOW
    Mitigation: PID check is per-process; two pipeline instances have different PIDs. agent_id prefix check as second line of defense.
    Trigger: PID reuse by OS between crash and cleanup
    ────────────────────────────────────────
    #: 5
    Risk: Overflow batching introduces file collision between sub-waves
    Severity: LOW
    Mitigation: validate_parallel_files runs per sub-wave. Sequential sub-waves guarantee no concurrent file access.
    Trigger: Tasks incorrectly marked parallelizable with shared files
    ────────────────────────────────────────
    #: 6
    Risk: Task branch deletion on halt deletes branches from a different feature (slug collision)
    Severity: LOW
    Mitigation: Branches are scoped by feature slug: feat/<slug>-tN. Different features have different slugs.
    Trigger: Feature slug change between pipeline runs (slugify is deterministic)
    
    Anti-Creep
    
    - Do NOT add a heartbeat/keepalive mechanism for coder agents. Dead agent detection via timeout is sufficient for F010 scope.
    - Do NOT add per-task timeout overrides. The global 900s timeout is adequate.
    - Do NOT change wave scheduling algorithm (TaskDAG.compute_waves). That's F019 territory.
    - Do NOT add worktree quota limits or disk space checks. Operator responsibility.
    - Do NOT add retry logic for failed parallel tasks. That's F023 (Pipeline Self-Healing) scope.
    - Do NOT refactor run_parallel_coders into multiple functions. Targeted hardening only.
    - Do NOT change the coder prompt template used in parallel mode. Prompt changes are out of scope.
    - Do NOT add telemetry or metrics for worktree count / lock staleness.
    
    Sign-Off Checklist
    
    - [ ] run_parallel_coders() has try/finally wrapping cleanup_all()
    - [ ] halt_and_revert() optionally accepts task_ids and cleans task branches
    - [ ] _reap_completed() drains pipes with non-blocking read before wait()
    - [ ] _reap_completed() escalates to SIGKILL if SIGTERM doesn't work within 2s
    - [ ] validate_parallel_files() calls os.path.normpath() on every file
    - [ ] TaskLock.init cleans stale locks with dead PIDs
    - [ ] Overflow tasks batch into sub-waves of up to max_parallel
    - [ ] pytest tests/test_parallel_robustness.py -v passes (all 7 test cases)
    - [ ] pytest tests/ -q — full suite green (495+ tests, no regressions)
    - [ ] halt_and_revert() called with task_ids at all 3 caller sites (lines 4949, 4956, 4961)
    - [ ] halt_and_revert() without task_ids preserves backward-compatible behavior
    - [ ] No worktree leak after simulated exception in run_parallel_coders()
    - [ ] No task branch leak after simulated parallel coder failure
    
    That is the complete corrected spec for F010. All three quality issues resolved:
    1. Added Impact section — one sentence on operator experience and --continuous safety
    2. Added What Changed section — 6 bullet points with exact line ranges and changes
    3. All 7 tasks use ### Task N: headers with all five required fields (Files, Dependencies, Parallelizable, Description)