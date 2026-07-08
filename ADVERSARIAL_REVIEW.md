# Adversarial Review Report — Dokima Codebase

**Reviewed:** 2026-07-06
**Reviewer:** DeepSeek v4-pro (different model family from coder: qwen/qwen3-coder-next)
**Scope:** All 7 Python source files (~10,700 LOC), specs/roadmap.md, specs/conventions.md
**Test suite:** 50 test files (~1,000 tests), all reported passing

---

## Pass 1: Code Quality

### BLOCKER

#### B1: `run_fix_mode_issue()` called but never defined — `dokima fix --issue N` broken

- **Location:** `dokima:657` calls `_pipeline.run_fix_mode_issue()`; no definition exists anywhere
- **Impact:** `dokima fix --issue N` raises `AttributeError` at runtime. The CLI path is dead.
- **Root cause:** F034 was marked Done but the function body was never written. Tests mock it with `create=True` (bypass), so pytest never caught it.
- **Recommendation:** Implement the function in `pipeline.py` per F034 spec:
  - Fetch issue via `gh issue view N --json body,title`
  - Call `extract_issue_sections(body)` from utils
  - Construct fix prompt with `### What`/`### Fix`/`### Verify`
  - Spawn coder via existing `run_phase2_coder(mode="fix")`
  - This is the pattern described in the pipeline-enforcement skill: "A function only tested in isolation that has zero production callers is a dead function." Here it's worse — the production caller exists but the callee doesn't.

#### B2: `_supplement_pr_sections` catches exception that `subprocess.run` never raises

- **Location:** `utils.py:897` — `except (subprocess.CalledProcessError, ...)`
- **Impact:** The `CalledProcessError` branch is dead code. This exception is only raised by `subprocess.run(check=True)`, but the call at line 887 uses `check=False` (the default). If `subprocess.run` truly fails (e.g. git not found), it raises `FileNotFoundError`, which IS caught by the `OSError` clause. The `CalledProcessError` clause is a no-op that suggests the author expected `check=True` behavior.
- **Recommendation:** Remove `subprocess.CalledProcessError` from the except clause or change the subprocess call to `check=True` if you want to catch non-zero return codes as exceptions.

### HIGH

#### H1: Double-filtering of ARCHITECTURAL blockers — silently drops real blockers

- **Location:** `pipeline.py:297` (in `extract_blockers_from_pr`) AND `pipeline.py:369-370` (in `run_fix_mode`)
- **Impact:** Blockers containing the word "architectural" are filtered in TWO places. Worse: `run_fix_mode` line 369-370 does a second pass that filters items NOT in `code_blockers` — but `code_blockers` was already filtered at line 297 from the same set. Then at lines 377-383, a THIRD pass drops blockers without explicit `🔴 BLOCKER` markers. A legitimate BLOCKER about architecture that happens to use bold formatting without the emoji marker would be silently dropped at all three filters.
- **Recommendation:** Consolidate blocker filtering into a single function with clear rules. Only filter once. The `extract_blockers_from_pr` function should return all blockers; the caller decides which are code-fixable.

#### H2: `_cleanup_lock` has a TOCTOU race on lock file removal

- **Location:** `utils.py:817-829`
- **Function:** `_cleanup_lock()` closes `_LOCK_FD` (line 819-821), then calls `os.remove(_lock_path())` (line 827). Between the close and the remove, another process could create a new lock file at the same path. The remove would then delete the OTHER process's lock.
- **Impact:** Concurrent `dokima next` runs could wipe each other's lock files, allowing two pipelines to run simultaneously against the same project.
- **Recommendation:** Don't remove the lock file in `_cleanup_lock`. The file descriptor close + process exit is sufficient — the next `acquire_lock` call will detect the stale PID and clean up. Alternatively, store the inode of the lock file at acquisition and only delete if the inode matches.

#### H3: Module-level mutable globals + `_sync_modules` pattern is fragile under import ordering

- **Location:** `utils.py:16-36`, `agent.py:13-15`, `tasks.py:33`, `pipeline.py:10`, `dokima:758-772`
- **Impact:** Each module file defines its own copy of `PROJECT_DIR`, `REPO`, `DEFAULT_BRANCH`, etc. as module-level globals. These are set to defaults (e.g. `PROJECT_DIR = ""`) and later overwritten by `_sync_modules()` in the main `dokima` entry point. If ANY function in utils.py or pipeline.py is called before `_sync_modules()` fires — including during import-time execution — it sees stale defaults.
- **Evidence:** `pipeline.py:10` defines `_IMPORTING_PANEL = None`, which is the CORRECT pattern (set once, checked at function-entry). The globals pattern (`PROJECT_DIR = ""`) is NOT the correct pattern — it assumes single-assignment after initialization, but there's no enforcement.
- **Recommendation:** Migrate remaining mutable globals to either (a) the `_IMPORTING_PANEL` pattern (function-entry lookup), or (b) a `get_config()` accessor that reads from a module-level dict set once at startup.

#### H4: Inconsistent test override detection — `sys.modules` vs `_IMPORTING_PANEL`

- **Location:** `tasks.py:513-519` uses `sys.modules.get('tasks')`; all other modules use `_IMPORTING_PANEL`
- **Impact:** `run_parallel_coders` in tasks.py uses `sys.modules` to find overrides, which contradicts the `_IMPORTING_PANEL` pattern documented in F022b. Tests that patch `dokima.run_parallel_coders` won't be picked up by this override detection path. The `_RPC_ORIGINAL` reference at line 666 also checks against a stale name.
- **Recommendation:** Convert `run_parallel_coders` override detection to use `_IMPORTING_PANEL` pattern, consistent with `utils.py:258` (`git`), `utils.py:271` (`gh`), etc.

#### H5: No error checking on git checkout/pull before sensitive operations

- **Location:** `roadmap.py:192-194` in `commit_roadmap_update`
- **Code:**
  ```python
  git("checkout", DEFAULT_BRANCH)       # returncode ignored
  git("pull", "origin", DEFAULT_BRANCH)  # returncode ignored
  git("add", rel_path)                   # continues regardless
  ```
- **Impact:** If the network is down, `git pull` fails silently, and the local tree is behind origin. The subsequent `git push` will fail with a non-fast-forward error, but only AFTER the roadmap status has been updated locally. The local roadmap is now desynchronized from the remote.
- **Recommendation:** Check return codes from `git("checkout", ...)` and `git("pull", ...)`. On failure, abort the operation and report the error.

### MEDIUM

#### M1: Duplicate interview-mode non-TTY save logic

- **Location:** `pipeline.py:1678-1718` and `utils.py:3294-3310`
- **Impact:** The non-TTY exit path for interview mode (`exit 2`) exists in TWO places with slightly different logic. `run_phase1_strategist` saves to `/tmp/dokima-interview.json`; `collect_init_interview_answers` saves to `INTERVIEW_SAVE_PATH` (`/tmp/dokima-init-interview.json`). Two different files, two different formats. If the init interview and feature interview use different save paths, the resume instructions are inconsistent.
- **Recommendation:** Extract a shared `save_interview_exit_state()` function that both callers use.

#### M2: `do_release` is a 160-line god function

- **Location:** `utils.py:3017-3176`
- **Impact:** 18 sequential steps with no logical grouping. Hard to test individual steps. Validation (steps 1-6), version bumping (7-11), tagging (12-13), pushing (14-15), release creation (16), and docs update (17) are all in one function.
- **Recommendation:** Extract:
  - `_validate_release_preconditions(bump, project_dir)` → returns (current_version, new_version, default_branch)
  - `_bump_version_file(project_dir, new_version)` → commits new VERSION
  - `_tag_and_push(project_dir, tag_name, default_branch)` → tags + pushes

#### M3: `run_phase1_strategist` is a ~650-line god function

- **Location:** `pipeline.py:1451-2107`
- **Impact:** Contains interview mode, DAG enforcement, quality gating, garbage detection, ADR creation, human gating, and spec saving — all in one function. Makes the pipeline hard to reason about.
- **Recommendation:** Extract sub-functions: `_handle_interview_mode()`, `_enforce_dag_format()`, `_run_quality_gate()`, `_detect_garbage_output()`, `_create_adr()`, `_human_gate()`.

#### M4: Atomic write inconsistency

- **Location:** `utils.py:2647-2652` (`_append_convention_rules`) uses non-atomic `open+write`
- **Contrast:** `utils.py:1583-1587` (`save_map_enrichments`) uses atomic `tempfile + os.rename`; `utils.py:3105-3109` (`do_release`) uses atomic `tempfile + os.replace`
- **Impact:** If the process crashes mid-write in `_append_convention_rules`, `conventions.md` is left truncated or corrupted.
- **Recommendation:** Use the same atomic write pattern everywhere.

#### M5: `_update_docs_cache` hardcodes repo name

- **Location:** `utils.py:2956` — `gh repo clone siongsheng/dokima-docs`
- **Impact:** The docs repo is not configurable. If the project is forked or the docs repo moves, the release workflow breaks.
- **Recommendation:** Make the docs repo configurable via `DOCS_REPO` env var, falling back to the hardcoded default.

#### M6: `extract_file_paths` requires `/` in path — drops single-file refs

- **Location:** `utils.py:1433` — `if '/' in path:`
- **Impact:** Bare filenames like `pipeline.py:4583` (referenced in task descriptions) are dropped because they have no directory component. This forces the coder to explore the full codebase instead of reading the specific file.
- **Recommendation:** If the file exists in the project directory (check `os.path.exists`), include it even without a `/`.

#### M7: Dead code: `_supplement_pr_sections` impact fallback generates "Minimal — see What Changed"

- **Location:** `utils.py:893-894`
- **Impact:** When `## Impact` is missing from the spec, the fallback text "Minimal — see What Changed" is injected. This is precisely the thin fallback that the quality gate at `_check_pr_body_quality` (line 542) is designed to detect. The system generates its own quality gate failure.
- **Recommendation:** Instead of injecting "Minimal", leave the section out when it's genuinely empty. Better to have no Impact section than a misleading one.

### LOW

#### L1: `_redact_secrets` TOCTOU — token snapshot vs. real-time env

- **Location:** `utils.py:192-208`
- **Impact:** Tokens are read from the environment at redaction time. If a token was logged BEFORE it was set in the environment, it won't be redacted. (Mitigated by the fact that tokens are typically set before the pipeline starts.)
- **Recommendation:** Accept this as a design trade-off. Document that redaction is best-effort, not a security boundary.

#### L2: Unnecessary MD5 hashing in `slugify`

- **Location:** `utils.py:316-322`
- **Impact:** Uses MD5 for collision avoidance in slug generation. While MD5 collisions don't matter for slugs (not a security context), the hashlib import and computation are unnecessary — a simple counter or the first 8 chars of the text would suffice.
- **Recommendation:** Replace with: `f"{base}-{len(text) % 10000:04d}"` — deterministic, fast, no crypto import.

#### L3: `discover_blocked_pr` fetches full PR list then filters in-memory

- **Location:** `pipeline.py:200-254`
- **Impact:** For repos with hundreds of open PRs, this fetches all of them and filters locally. `gh pr list --search "BLOCKED in:title"` would push filtering to the server.
- **Recommendation:** Add a `--search` flag to the gh command.

#### L4: `spawn_coder_in_worktree` duplicates coder prompt template from `run_phase2_coder`

- **Location:** `tasks.py:331-346` vs `pipeline.py:670-690`
- **Impact:** Same feature logic (TDD rules, RED/GREEN commits, build constraints) in two places. If one is updated, the other may not be.
- **Recommendation:** Extract the coder prompt template into a shared function.

#### L5: Agent.py `_run_agent` swallows all exceptions in stdout loop

- **Location:** `agent.py:168-178`
- **Impact:** The `except Exception: pass` at line 177 silently discards any error reading from the agent's stdout pipe. If the pipe breaks mid-output, the remaining agent output is lost with no warning.
- **Recommendation:** Log the exception or at minimum set a flag so the orchestrator knows output may be incomplete.

---

## Pass 2: Goal Alignment

### What Is Dokima's Mission?

The mission is defined in `specs/roadmap.md` and implied by the codebase: **Dokima is a multi-agent pipeline orchestrator** that routes feature development through AI agents (Strategist → Coder → vet → nm → Tech Lead). The stated mission from `AGENTS.md`: "Python script that routes feature development through a pipeline of AI agents."

### Does The Code Serve The Mission?

**Yes, overwhelmingly.** All 34 features trace to concrete pipeline reliability improvements. No major scope creep detected. The codebase is self-hosting (dokima builds dokima) which is the strongest validation.

### Dead Code / Unused Features

1. **`run_fix_mode_issue()` — BLOCKER** (see B1). Exists in spec, tests, and CLI wiring, but the function body was never implemented. This is a shipped-but-broken feature.

2. **`_supplement_pr_sections` `CalledProcessError` branch — dead code** (see B2).

3. **`extract_blockers_from_pr` PR comments fallback** (pipeline.py:286-292) — the fallback fetches PR comments but the `extract_blockers_from_pr(stdout)` recursive call passes only one arg, making the `pr_number` parameter `None` on the recursive call. The second call's comment-fallback is therefore unreachable without a second `pr_number`.

### Over-Engineering Detection

1. **`_build_impact_map`** (utils.py:1891-1945) — AST-based import analysis for the codebase map. While useful, it only handles Python and produces a flat list. It classifies stdlib modules via a hardcoded set that will drift. Not wrong, but the maintenance burden may exceed the value.

2. **Map enrichment system** (F028) — Accumulating `> MAP:` hints across features. Currently both the extraction (`extract_map_enrichments`) and generation (`generate_codebase_map` with Agent Guidance section) are fully implemented, but the enrichment file format is JSON (`.map-enrichments.json`) while the map output is Markdown. Two serialization formats for the same concept. The `save_map_enrichments` function uses atomic writes but `generate_codebase_map` merges enrichments as plain text bullets — fragile if the map is re-generated.

3. **ADR integration** (pipeline.py:2051-2091) — Auto-creates ADRs during feature planning. This is a nice-to-have that requires `adr-tools` to be installed and `docs/adr/` to exist. In practice, most dokima users won't have this set up. The code is clean and non-blocking, but it's infrastructure for a workflow the codebase itself doesn't use.

### Simplicity Assessment

The codebase generally favors simple solutions. Good examples:
- `conventions.md` instead of a vector DB for cross-run learning (F033)
- Deterministic codebase map instead of LLM-generated wiki (F027)
- File-based lock files instead of a coordination service
- Shell scripts (nm, vet) instead of more Python

Areas where simplicity could improve:
- Three parallel override-detection patterns (`_IMPORTING_PANEL`, `sys.modules`, and `getattr` chains) — pick one
- Two interview-mode non-TTY exit paths — extract one shared function
- Quality gate, DAG enforcement, and garbage detection are all re-prompt loops with very similar structure — they could share a `_re_prompt_strategist_with_feedback()` helper

### Drift Detection

1. **F038 is marked Done but nm injection only works via string parsing, not structured extraction.** The `_inject_nm_into_pr_body` function (pipeline.py:1070) calls `_extract_nm_summary` which uses regex heuristics to parse the nm output. If the nm script changes its output format, extraction silently degrades. The spec required a "### nm Review" section in the PR body; the implementation delivers this but with fragile parsing.

2. **Roadmap has two features marked "Done Progress" (F033, F036) instead of "Done"** — these show `[x] Done Progress` which suggests a template/parser discrepancy. `update_roadmap_status` uses exact pattern matching for `[ ] Pending` → `[x] Done`, but these entries have a malformed status marker.

### Requirement Coverage

All 34 features traced to `specs/roadmap.md` are marked Done (with the two anomaly entries noted above). The test suite at ~1,000 tests provides broad coverage. However:

- **No integration test for the full `dokima fix --issue N` path exists** — because the function isn't defined (B1).
- **No test verifies that `_cleanup_lock` doesn't delete other processes' locks** (H2).
- **No test for the `--vcs gitlab` path end-to-end** — the VCS abstraction (vcs.py) exists and has unit tests, but no integration test verifies it with a real GitLab instance.

---

## Verdict

**[ ] Pass — merge ready**
**[x] Conditional — fix BLOCKER/HIGH items, re-review**
**[ ] Fail — significant rework needed**

---

## Summary Counts

| Severity | Count | Must Fix Before Merge |
|----------|-------|-----------------------|
| BLOCKER  | 2     | Yes |
| HIGH     | 5     | Yes |
| MEDIUM   | 7     | No (backlog) |
| LOW      | 5     | No (noted) |

### Must Fix (BLOCKER + HIGH)
1. **B1:** Implement `run_fix_mode_issue()` in pipeline.py
2. **B2:** Remove dead `CalledProcessError` exception clause in `_supplement_pr_sections`
3. **H1:** Consolidate blocker filtering — single pass instead of triple-pass
4. **H2:** Fix TOCTOU race in `_cleanup_lock` — don't delete lock by path after fd close
5. **H3:** Add guard-rails for module-level globals accessed before `_sync_modules()`
6. **H4:** Standardize override detection on `_IMPORTING_PANEL` pattern (fix tasks.py)
7. **H5:** Check return codes from `git checkout`/`git pull` in `commit_roadmap_update`

### Backlog (MEDIUM)
M1-M7 as listed. Most are refactoring opportunities, not bugs.

### Noted (LOW)
L1-L5 as listed. Acceptable technical debt.

### Pre-existing Issues (not introduced by recent changes)
- The triple-pattern override detection (H4) has existed since F022b and is consistent across the codebase.
- The `_sync_modules` pattern (H3) is the established convention — changing it is a refactoring project, not a blocker fix.

---

## Blocker/High items fixed: [ ] yes [ ] no
## Human sign-off: _____________
