# --fix Mode — Implementation Spec

**Status:** Awaiting Approval
**Confidence:** High
**Impact:** MEDIUM
**Version:** 1.0.0
**Based on:** specs/archive/fix-mode/plan.md (16 edge cases)

---

## 1. Executive Summary

Add `dokima --fix [project_dir]` — a pipeline mode that detects the most recent BLOCKED PR, extracts the blocker list from its TL review section, feeds them to the coder as a targeted fix task, and runs the full vet→nm→TL verification pipeline. The strategist is **not** re-run — the spec already exists, and the blockers are the requirements. This closes the gap where fixing a BLOCKED PR currently requires manually crafting a feature description and re-running the full pipeline including strategist.

Confidence: **High** — the design is a thin orchestration layer over existing phase functions (`run_phase2_coder`, `run_phase3_vet`, `run_phase4_nm`, `run_phase5_tech_lead`). The only NEW logic is BLOCKED PR discovery + blocker extraction + the abbreviated human gate.

---

## 2. Constitution Check

| Axiom | Status | Detail |
|-------|--------|--------|
| Solves user's own pain? | YES | User hits BLOCKED PRs and has no shortcut to trigger a fix cycle |
| Weekend-buildable? | YES | ~300-400 LOC, reuses existing phase functions |
| Evidence people will pay? | N/A | Part of dokima core — not a paid feature |
| Tech stack boring/proven? | YES | Python 3.6+, gh CLI, same subprocess pattern as rest of dokima |
| Avoids AI hype? | YES | Pure orchestration — no new AI capabilities |

No constitutional violations.

---

## 3. Ponytail Guard (Pre-Spec)

**Rung 7** — genuine new orchestration. The existing TL auto-fix loopback (lines 2331-2391) handles objective BLOCKERs during the same pipeline run, but it cannot be invoked standalone on an already-BLOCKED PR. An independent CLI entry point and BLOCKED PR discovery are genuinely new.

---

## 4. Feature Breakdown

### Task 1: Add `--fix` flag to argparse in `main()`
**Files:** dokima
**Dependencies:** [none]
**Parallelizable:** no (shared file with Task 2)
**Estimated LOC:** ~15
**Description:** Add `is_fix = False` boolean and `if arg == "--fix": is_fix = True; continue` in the flag-scanning loop (lines 3059-3091). Update usage output strings to include `dokima --fix [project_dir]`. Update `--answers` interaction: if `--answers` passed with `--fix`, print warning and ignore.

### Task 2: Add `--fix` dispatch path in `main()`
**Files:** dokima
**Dependencies:** [Task 1]
**Parallelizable:** no
**Estimated LOC:** ~30
**Description:** After lock acquisition and project setup (after line 3192), insert an early dispatch: if `is_fix`, call `run_fix_mode(project_dir=PROJECT_DIR)`. Must come AFTER API_KEY, REPO, DEFAULT_BRANCH, TEST_CMD/BUILD_CMD detection (those are needed by the pipeline), but BEFORE the auto-archive block and --next setup (those are for normal features). Skip auto-archive for fix mode. Fix mode acquires the lock but must NOT advance the roadmap.

### Task 3: Implement `discover_blocked_pr()` — detect most recent BLOCKED PR
**Files:** dokima
**Dependencies:** [none]
**Parallelizable:** yes
**Estimated LOC:** ~45
**Description:** New function. Calls `gh pr list --state open --json number,title,body,headRefName,updatedAt` (sorted by updatedAt desc). Iterates results: checks for `[BLOCKED]` in title OR `VERDICT: BLOCKED` (case-insensitive) in body OR `### Blockers` section in body. Returns dict `{number, title, headRefName, body}` of first match, or `None` if no BLOCKED PR found. Prints "No BLOCKED PRs found." and returns None (caller exits 0). If multiple BLOCKED PRs, prints "Found N BLOCKED PRs. Fixing #X (most recent)." before returning the newest.

### Task 4: Implement `extract_blockers_from_pr(pr_body)` — parse blocker list
**Files:** dokima
**Dependencies:** [none]
**Parallelizable:** yes (different function signature, no shared code path)
**Estimated LOC:** ~35
**Description:** New function. Parses PR body for `### Blockers` section (the format written by `run_phase5_tech_lead` at lines 2425-2428). Extract lines matching `- ...` under that section. Fallback: if no `### Blockers` section, search body for lines containing `🔴 BLOCKER` (from TL output pattern) or `BLOCKER:` anywhere. Returns list of blocker description strings. Edge case: if no blockers found, try parsing PR comments via `gh pr view --comments` for TL review content. If STILL nothing, return empty list — caller handles "Cannot extract blockers automatically."

### Task 5: Implement `run_fix_mode(project_dir)` — orchestrator function
**Files:** dokima
**Dependencies:** [Task 2, Task 3, Task 4]
**Parallelizable:** no
**Estimated LOC:** ~120
**Description:** The main fix-mode orchestrator. Flow:

1. Call `discover_blocked_pr()`. If None: print "No BLOCKED PRs found." exit(0) with suggestion to run `--next`.
2. Check PR state: `gh pr view <num> --json state,merged`. If merged: "PR is already merged. Nothing to fix." exit(0). If closed: "PR is closed." exit(1).
3. Call `extract_blockers_from_pr(pr_body)`. If empty and no fallback sources: print "Cannot extract blockers automatically. Review PR manually: <url>" exit(1).
4. Filter out ARCHITECTURAL blockers: lines matching `ARCHITECTURAL` or `ARCHITECTURE VIOLATION` (case-insensitive). Track count. Print architectural blockers with ⚠ warning. Remove from fix task list. If ALL blockers are architectural: "All blockers are architectural. Human review required." exit(1).
5. Check `PANEL_FIX_ALL=1` env var: if set, also extract SHOULD FIX items from PR body and append to fix list. Print count: "Fixing N BLOCKERs. M SHOULD FIX items included." If not set, print: "Fixing N BLOCKERs. M SHOULD FIX items skipped (set PANEL_FIX_ALL=1 to include)."
6. **Abbreviated Human Gate:** Show blocker list and fix plan. Options: `[y]` proceed, `[e]` edit blocker list (open temp file in vim), `[q]` abort. Skip if non-interactive (Telegram/cron) — if architectural blockers exist, abort with message; if purely code blockers, auto-proceed. Skip if `PANEL_SKIP_HUMAN_GATE=1`.
7. **Coder phase (fix-only):** Construct a fix-only prompt (see Task 6). Spawn coder on the BLOCKED PR's branch (`headRefName`). No new branch creation. Coder commits: `fix: address TL review blockers`. Force TDD (RED→GREEN, single commit per fix acceptable since scope is narrow).
8. **vet phase:** Run `run_phase3_vet()` — but note: vet currently expects `feature`, `branch`, `pr_sections`, `impact`, `spec_path`. For fix mode, use the PR's title as feature, `headRefName` as branch, dummy pr_sections (or extract from PR body), impact="MEDIUM", and attempt to locate the original spec file if it still exists.
9. **nm phase:** Run `run_phase4_nm()` — same adaptation: pass PR title as feature, branch as `headRefName`, impact as "MEDIUM". If the PR has an existing URL, pass it as `pr_url_in` so nm reviews the updated PR.
10. **TL re-review:** Run `run_phase5_tech_lead()` — this already handles: extracting verdict, injecting review section into PR body with BLOCKERs, updating PR body via `gh api`. The branch is the existing PR's head branch. If the original spec file exists, pass its path; otherwise, pass a note "original spec not found — review against PR blockers." The TL compares: were original blockers actually resolved? Did the fix introduce new issues?
11. **Report:** Print outcome. If still BLOCKED: print remaining blockers + "Run --fix again or review manually." If APPROVED: print PR URL + verdict. If NEW blockers (different from originals): print "Fix introduced N new blockers" (do NOT auto-loop).

### Task 6: Construct fix-only coder prompt
**Files:** dokima (inline in `run_fix_mode`)
**Dependencies:** [Task 5]
**Parallelizable:** no
**Estimated LOC:** ~30 (prompt string)
**Description:** The coder prompt for fix mode differs from the normal coder prompt:
- No tasks_extract_path — blockers ARE the tasks (inlined).
- No new branch — `git checkout <existing_branch> && git pull origin <existing_branch>`.
- Explicit constraint: "FIX MODE: only fix the listed blockers. Do NOT add features. Do NOT refactor unrelated code. Do NOT change architecture."
- TDD: write failing test first (confirm it fails on unpatched code), then fix, then confirm test passes.
- Single commit: `fix: address TL review blockers` (with individual blocker descriptions in body).
- Run BUILD_CMD + TEST_CMD before pushing.
- Report: what each fix changed, test results, commit hash.

### Task 7: Handle edge cases from plan.md
**Files:** dokima
**Dependencies:** [Task 5]
**Parallelizable:** no
**Estimated LOC:** ~60 (scattered conditionals)
**Description:** Implement the 16 edge cases from specs/archive/fix-mode/plan.md. Most are handled by the functions above, but these need explicit verification and possibly additional conditionals:
- EC1 (no BLOCKED PR) → handled in `discover_blocked_pr()` returning None
- EC2 (multiple BLOCKED PRs) → handled by print + pick newest
- EC3 (no traceable blockers) → handled in `extract_blockers_from_pr()` returning empty
- EC4 (architectural blockers) → handled by filter logic in Task 5 step 4
- EC5 (fix introduces new blockers) → handled by TL re-review comparison
- EC6 (coder can't fix) → coder output parsing for "⚠ CODER UNABLE TO FIX"
- EC7 (branch diverged) → `git pull origin <branch>` before coder
- EC8 (merged PR) → `gh pr view --json state,merged` check
- EC9 (non-interactive) → abbreviated human gate auto-proceed logic
- EC10 (lock contention) → reuse existing `acquire_lock()` — no change needed
- EC11 (TDD in fix mode) → enforced by fix-only coder prompt
- EC12 (depth gating — always full) → no depth calculation; always vet+nm+TL
- EC13 (no TL review in PR) → fallback to `gh pr view --comments` in blocker extraction
- EC14 (spec file stale/missing) → attempt lookup by branch name pattern `feat/<slug>`, warn if not found
- EC15 (`--fix` + `--answers`) → print warning, ignore answers file
- EC16 (SHOULD FIX items) → `PANEL_FIX_ALL=1` gating

### Task 8: Update usage and help text
**Files:** dokima
**Dependencies:** [Task 2]
**Parallelizable:** no
**Estimated LOC:** ~10
**Description:** Update `show_help()` to include `--fix` mode. Update error message at line 3041. Add: `dokima --fix [project_dir]` to usage. Update docstring at top of file.

### Task 9: Add tests for new functions
**Files:** tests/test_fix_mode.py
**Dependencies:** [Task 3, Task 4]
**Parallelizable:** yes (separate file)
**Estimated LOC:** ~120
**Description:** New test file with:
- `test_discover_blocked_pr_none()` — mock gh output with no BLOCKED PRs → returns None
- `test_discover_blocked_pr_found()` — mock gh output with BLOCKED PR → returns dict
- `test_discover_blocked_pr_multiple()` — picks most recent
- `test_extract_blockers_from_pr_standard()` — parses `### Blockers\n- ...` format
- `test_extract_blockers_from_pr_fallback()` — parses `🔴 BLOCKER` lines when no `### Blockers`
- `test_extract_blockers_from_pr_empty()` — returns empty list
- `test_extract_blockers_architectural_filter()` — filters out ARCHITECTURAL lines
- `test_extract_blockers_should_fix_gating()` — PANEL_FIX_ALL behavior
- `test_extract_blockers_from_pr_no_tl_section()` — EC13

All tests use monkeypatch on `gh()` helper function (same pattern as `test_pick_next.py`).

### Task 10: Update README.md
**Files:** README.md
**Dependencies:** [Task 5]
**Parallelizable:** yes (docs only)
**Estimated LOC:** ~25
**Description:** Add `--fix` mode documentation to README:
- New row in pipeline table (or separate fix-mode section)
- Usage example: `dokima --fix ~/project`
- One-sentence description of what it does
- Note: PANEL_FIX_ALL and PANEL_SKIP_HUMAN_GATE env vars
- Note: fix mode always runs full pipeline

---

## 5. Data Model

No new persistent state. All data is transient:

| Entity | Source | Lifetime | Fields |
|--------|--------|----------|--------|
| Blocked PR info | `gh pr list --json` | Single invocation | number, title, headRefName, body, updatedAt |
| Blocker list | PR body parsing | Single invocation | list of description strings |
| Fix tasks | Extracted from blocker list | Single invocation | list of strings fed to coder prompt |

The PR body already has the `## Review` / `### Blockers` section injected by `run_phase5_tech_lead` (lines 2424-2438).

---

## 6. API/Interface Proposal

### Function Signatures

```python
def discover_blocked_pr() -> Optional[dict]:
    """Returns {number, title, headRefName, body} or None if no BLOCKED PR found."""
    ...

def extract_blockers_from_pr(pr_body: str, pr_number: str | None = None) -> list[str]:
    """Returns list of blocker description strings. Falls back to PR comments if pr_number provided."""
    ...

def run_fix_mode(project_dir: str) -> None:
    """Orchestrate the fix-mode pipeline. Exits on completion or failure."""
    ...
```

### CLI Interface

```
dokima --fix [project_dir]
```

- `project_dir` defaults to cwd
- No feature description argument — blockers are extracted from the PR
- `--answers` is ignored with a warning

### Environment Variables

| Variable | Effect | Default |
|----------|--------|---------|
| `PANEL_FIX_ALL=1` | Also include SHOULD FIX items in fix task list | BLOCKERs only |
| `PANEL_SKIP_HUMAN_GATE=1` | Skip the abbreviated human gate | Show gate if TTY |
| `PANEL_SKIP_AUTOFIX=1` | Skip auto-fix loopback in TL re-review | Honored (same as main pipeline) |

---

## 7. Security Considerations

- **No new external inputs:** Blockers are extracted from the PR body which was written by our own TL agent. The PR body is trusted content.
- **No new GitHub permissions:** Uses existing `gh pr list`, `gh pr view`, `gh api` — all already authorized.
- **Branch safety:** Coder works on the existing PR's head branch, not a new one. `git pull` before coder to avoid divergence.
- **Lock contention:** Reuses existing `acquire_lock()` — only one fix-mode or pipeline per project at a time.
- **No credential exposure:** All gh calls use the same `GH_TOKEN` path as the rest of dokima.
- **Architectural blocker guard:** The filter explicitly skips architectural blockers — these require human decision and must not be fed to the coder.

---

## 8. Test Plan (MANDATORY)

### Feature Area: BLOCKED PR Discovery

- **Happy path:** One BLOCKED PR exists → `discover_blocked_pr()` returns its number, title, headRefName, body.
- **Edge case — no BLOCKED PR:** `gh pr list` returns empty or no BLOCKED matches → returns None.
- **Edge case — multiple BLOCKED PRs:** Picks most recently updated. Prints notification about others.
- **Edge case — blocked marker in title only:** Detects `[BLOCKED]` in title even if body lacks `VERDICT: BLOCKED`.
- **Edge case — blocked marker in body only:** Detects `### Blockers` section even if title lacks `[BLOCKED]`.
- **Edge case — race with merge:** PR is open but `gh pr view` shows merged=true → exits "already merged."

### Feature Area: Blocker Extraction

- **Happy path:** PR body has `### Blockers` section with `-` list items → extracted as list.
- **Edge case — fallback pattern:** No `### Blockers` section but `🔴 BLOCKER` lines exist → extracted.
- **Edge case — empty PR body:** No blockers found, PR comments also empty → returns empty list.
- **Edge case — PR comments fallback:** Body lacks blockers, `gh pr view --comments` has TL review → extracted from comments.
- **Edge case — architectural filter:** `ARCHITECTURE VIOLATION` or `ARCHITECTURAL` in blocker line → excluded from fix list.
- **Edge case — all architectural:** All blockers are architectural → function signals "all architectural" via special return.
- **Failure mode — gh pr view timeout:** Network error during comments fallback → return partial results from body only, warn user.
- **Contract invariant:** After extraction, every returned blocker string is non-empty and does not contain "ARCHITECTURAL".

### Feature Area: Fix-Mode Coder

- **Happy path:** Coder receives blocker list, writes failing test, fixes code, test passes, pushes.
- **Edge case — no blockers to fix (coder receives empty list):** Coder should report "no blockers to fix" and exit cleanly.
- **Edge case — coder can't fix a specific blocker:** Coder reports "⚠ CODER UNABLE TO FIX: <reason>" for that blocker. Remaining blockers still processed.
- **Edge case — branch force-pushed while coder works:** `git pull --rebase` before coder starts. If pull fails, abort with message.
- **Failure mode — build breaks after fix:** vet phase catches it → coder retry loop (same 2-retry limit as main pipeline).
- **Failure mode — coder adds new features:** TL re-review catches scope creep → new BLOCKER.
- **Contract invariant:** After fix, original BLOCKED tests must pass AND pre-existing tests must still pass.

### Feature Area: TL Re-Review

- **Happy path:** TL confirms all blockers resolved → VERDICT: APPROVED.
- **Edge case — fix introduces new blockers:** TL finds new issues → new BLOCKERs added to PR, old ones cleared.
- **Edge case — partial fix:** Some blockers resolved, some remain → VERDICT: BLOCKED with remaining blockers.
- **Edge case — spec file missing:** TL runs without spec → reviews against PR blocker list only.
- **Edge case — no TL review in original PR (EC13):** Original PR has no TL section → nm output becomes primary review source.
- **Contract invariant:** The PR body is ALWAYS updated with the new TL review section, regardless of verdict.

---

## 9. COTS Build-vs-Buy

| Component | Decision | Justification |
|-----------|----------|---------------|
| BLOCKED PR detection | **Built** — `gh pr list --json` | Already used throughout dokima; `gh` is a hard dependency |
| PR body parsing | **Built** — regex/split | Trivial string parsing, no library needed |
| Blocker extraction | **Built** — markdown section parsing | Format is controlled (we write it in `run_phase5_tech_lead`) |
| Coder invocation | **Built** — `spawn_agent("coder", ...)` | Existing function, used by all phases |
| vet, nm, TL phases | **Built** — reuse `run_phase3_vet`, `run_phase4_nm`, `run_phase5_tech_lead` | Already tested, handles PR update + verdict injection |
| Lock acquisition | **Built** — reuse `acquire_lock()` | Project-scoped, works with `--next` and `--continuous` |

Nothing to buy. Everything is integration of existing building blocks.

---

## 10. Panel Split

**Single-feature, no parallelization needed.** The fix-mode pipeline is inherently sequential:
1. Discover BLOCKED PR (depends on gh)
2. Extract blockers (depends on PR body)
3. Human Gate (depends on blocker list)
4. Coder (depends on blocker list + gate pass)
5. vet (depends on coder)
6. nm (depends on vet)
7. TL (depends on nm)

However, **Tasks 3, 4, 9 can run in parallel** during implementation (they touch different code sections: `discover_blocked_pr` is independent from `extract_blockers_from_pr`, and tests are in a separate file).

Recommended implementation order:
- **Wave 1:** Tasks 1, 3, 4 (parallel: flag + discover + extract)
- **Wave 2:** Tasks 2, 9 (parallel: dispatch + tests)
- **Wave 3:** Tasks 5, 6, 7 (sequential: orchestrator + coder prompt + edge cases — share same function)
- **Wave 4:** Tasks 8, 10 (parallel: help text + README)

---

## 11. Build & Deploy

- **No new dependencies.** Pure Python 3.6+ with existing gh CLI.
- **No build changes.** Single-file script (`dokima`).
- **No new env vars required.** `PANEL_FIX_ALL` is optional.
- **Deployment:** Same as current — copy/symlink `dokima` to `~/bin/dokima`.
- **No CI changes needed.** `python3 -m pytest tests/ -q` already covers all test files.

---

## 12. Risk Register

| # | Risk | Severity | Mitigation | Trigger |
|---|------|----------|------------|---------|
| 1 | TL re-review creates new BLOCKERs endlessly (fix→block→fix→block cycle) | MEDIUM | Do NOT auto-loop. One fix attempt per `--fix` invocation. Print "Run --fix again" if still BLOCKED. | New BLOCKERs appear in second TL review |
| 2 | Coder misinterprets blocker and changes unrelated code | HIGH | Fix-only prompt with strong constraints. TL re-review catches scope creep. | TL finds "scope creep" BLOCKERs |
| 3 | Branch deleted while fix is running (EC7) | LOW | `git pull` before coder + error check. Abort with message if branch missing. | `git pull` returns non-zero |
| 4 | Architectural blocker fed to coder accidentally | HIGH | Explicit filter in `extract_blockers_from_pr()`. Test verifies architectural lines are excluded. | BLOCKER line contains "ARCHITECTURAL" |
| 5 | `gh pr list` rate-limited on large repos | LOW | Same gh API calls as existing code. No new rate-limit risk. | gh returns rate-limit error |
| 6 | Fix-mode runs on wrong PR (user expects different BLOCKED PR) | LOW | Print "Fixing #X" before human gate. User can quit. | Human Gate shows wrong PR number |
| 7 | `run_phase3_vet` / `run_phase4_nm` / `run_phase5_tech_lead` have hard dependencies on `spec_path` | MEDIUM | Pass original spec path if it exists (lookup: `specs/<slug>/spec.md` from branch name). If missing, pass a note. Phase functions already handle missing files gracefully (they print warnings). | spec file doesn't exist at expected path |

---

## 13. Anti-Creep

**Explicitly NOT in scope:**

- Auto-looping fix cycles (`--fix` → fix → block → `--fix` again — manual invocation only)
- Fixing MERGED or CLOSED PRs (not applicable)
- Automatic SHOULD FIX inclusion (gated behind `PANEL_FIX_ALL=1`)
- Creating new branches or PRs (works on existing BLOCKED PR)
- Fixing non-TL blockers (e.g., nm-only blockers — only BLOCKED PRs from TL review)
- Auto-merging after fix (even in `--continuous` — manual merge only for fixes)
- Running strategist for fix-mode (spec already exists)
- Interactive blocker editing beyond the abbreviated human gate's `[e]` option
- Fixing multiple BLOCKED PRs in one invocation (pick most recent, user re-runs for others)

---

## 14. Sign-Off Checklist

- [ ] `--fix` flag parses correctly and does not conflict with `--next`/`--continuous`
- [ ] `discover_blocked_pr()` returns correct PR when BLOCKED PRs exist
- [ ] `extract_blockers_from_pr()` correctly parses `### Blockers` section
- [ ] Architectural blockers are excluded from fix task list
- [ ] Abbreviated human gate works in interactive mode (y/e/q)
- [ ] Non-interactive mode auto-proceeds for code blockers
- [ ] Non-interactive mode aborts for architectural-only blockers
- [ ] Coder receives fix-only prompt with blocker list (not spec)
- [ ] Coder works on existing PR's branch (no new branch)
- [ ] Full pipeline (vet → nm → TL) runs after fix
- [ ] TL re-review updates PR body with new verdict + blockers
- [ ] `PANEL_FIX_ALL=1` includes SHOULD FIX items
- [ ] `PANEL_SKIP_HUMAN_GATE=1` skips the gate
- [ ] All 16 edge cases from plan.md are handled
- [ ] README.md updated with --fix mode documentation
- [ ] 9+ new tests pass in `tests/test_fix_mode.py`

---

## 15. Impact Assessment

**Files changed:**
- `dokima` — main script: ~250-300 LOC added (flag parsing + 3 new functions + orchestrator)
- `tests/test_fix_mode.py` — new file: ~120 LOC
- `README.md` — ~25 LOC

**Files NOT changed:**
- `run_phase2_coder()` — reused as-is
- `run_phase3_vet()` — reused as-is
- `run_phase4_nm()` — reused as-is
- `run_phase5_tech_lead()` — reused as-is (its PR body update logic already handles BLOCKED/APPROVED injection)
- `spawn_agent()`, `gh()`, `git()` — no changes

**Cascading effects:** None. Fix mode is a parallel path in `main()` that branches BEFORE the normal pipeline flow.

**Estimated total LOC:** ~370-420 lines (net new, excluding tests)

**Risk level:** LOW. The fix mode is an additive code path. It does not modify any existing pipeline function. If it fails, the existing pipeline (normal/--next/--continuous) is completely unaffected.

---

## 16. Documentation Impact

README: YES — need to add `--fix` mode to the Usage section and pipeline table.

**Section to update:** "Usage" (add `dokima --fix [project_dir]` example). "Features" (add bullet: `--fix` mode re-runs coder→vet→nm→TL on BLOCKED PRs). "When NOT to Use" (no change needed).

**New content:** ~5 lines in Usage, ~4 lines in Features list.
