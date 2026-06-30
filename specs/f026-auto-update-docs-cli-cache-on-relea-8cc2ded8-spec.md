# F026: Auto-Update Docs CLI Cache on Release

Now I have the full picture. Let me produce the corrected spec. Here is the COMPLETE corrected spec:
    
    ───
    
    F026: Auto-Update Docs CLI Cache on Release
    
    Priority: P2
    Dependencies: F021 (--version), F024 (--release, --help-json generation), dokima-docs repo
    Status: In Progress (2026-07-01)
    Branch: feat/f026-auto-update-docs-cli-cache-on-relea-08bdf821
    
    User Story
    
    As a maintainer running dokima --release patch, the docs site at https://dokima-docs.vercel.app automatically reflects the new version and any new/changed CLI flags without manual intervention.
    
    Current State
    
    
    dokima --release patch
      → bumps VERSION to 1.2.5
      → tags v1.2.5
      → creates GitHub Release
    
    dokima-docs site
      → CLI page shows v1.2.4 (stale)
      → new flags from v1.2.5 missing
    
    
    Desired State
    
    
    dokima --release patch
      → bumps VERSION to 1.2.5
      → tags v1.2.5
      → creates GitHub Release
      → clones dokima-docs repo (shallow)
      → runs dokima --help-json > scripts/cli-help.json
      → commits + pushes to dokima-docs main
      → Vercel auto-deploys → CLI page shows v1.2.5 ✅
    
    
    Design
    
    Approach
    Update do_release() in utils.py to push the updated --help-json output to the docs repo after release. Use a temp directory for shallow clone, avoid credentials in code. SINGLE APPROACH — the existing gh CLI and git() helpers are already available; no new dependencies needed.
    
    Files Changed
    File: utils.py
    Change: Add _update_docs_cache() helper + wire into do_release() step 17
    ────────────────────────────────────────
    File: tests/test_f024_release.py
    Change: Add dry_run assertion for docs cache mention
    ────────────────────────────────────────
    File: tests/test_f026_docs_cache.py
    Change: New test file — unit tests for _update_docs_cache()
    ────────────────────────────────────────
    File: VERSION
    Change: No change
    
    Flow
    
    
    do_release(bump, project_dir, dry_run):
      1-16. [existing] validate, bump, commit, tag, push, create release
      17.  [NEW] If not dry_run and gh CLI available:
           a. Clone dokima-docs to /tmp with gh repo clone siongsheng/dokima-docs -- --depth=1
           b. Run dokima --help-json > <clone>/scripts/cli-help.json
           c. cd clone && git add scripts/cli-help.json
           d. git commit -m "chore: update CLI reference for v{new_version}"
           e. git push
           f. rm -rf clone
      18. Print summary (existing)
    
    
    Edge Cases
    - docs clone fails → warn, continue release (non-blocking)
    - git push to docs fails → warn, continue release (non-blocking)
    - dry_run mode → skip docs update, print "[DRY RUN] Would update docs cache"
    - gh CLI not installed → skip docs update, warn
    - dokima-docs repo doesn't exist → skip, warn
    - merge conflict on docs push → skip, warn (docs maintainers resolve)
    - dokima --help-json not on PATH → skip, warn (non-blocking)
    
    Non-Goals
    - Does NOT auto-add new pages for new features — only updates CLI reference cache
    - Does NOT require GitHub credentials beyond gh CLI (already required by do_release)
    - Does NOT run on every merge — only on --release
    
    Impact
    
    Maintainers run one command and everything stays in sync. No manual "oh I forgot to update the docs" moments. The docs site always reflects the actual CLI, version-accurate, within 60 seconds of a release. Developers reading the docs see the exact flags and commands available in their installed version — no version drift, no stale screenshots, no "works on my machine but not in docs" confusion. Vercel auto-deploys on push so the pipeline is fully hands-off.
    
    What Changed
    
    - utils.py: New function _update_docs_cache(new_version) — clones dokima-docs, writes --help-json output to scripts/cli-help.json, commits, pushes, cleans up. Called from do_release() after GitHub Release creation. ~40 LOC.
    - utils.py:do_release(): After existing step 16 (GitHub Release), insert docs cache update call before step 17 (print summary). ~5 LOC.
    - tests/test_f026_docs_cache.py: New test file — unit tests for _update_docs_cache() covering happy path, dry-run skip, clone failure, push failure, and gh-missing paths. ~90 LOC.
    - tests/test_f024_release.py: One new assertion — verify --release patch --dry-run output includes "[DRY RUN] Would update docs cache" when gh CLI is available. ~10 LOC.
    
    Confidence
    
    High — single well-bounded change in an existing function. Non-blocking on failure. Uses gh CLI already available. ~50-60 lines of new code. Existing git(), gh(), and _safe_run() helpers handle all subprocess needs.
    
    Constitution Check
    
    Axiom: Solves user's own pain
    Status: ✅
    Notes: Dokima maintainer currently updates docs manually
    ────────────────────────────────────────
    Axiom: Weekend-buildable
    Status: ✅
    Notes: 4 tasks, ~50 LOC, 45 min estimate
    ────────────────────────────────────────
    Axiom: Evidence people will pay
    Status: N/A
    Notes: Internal tool — value is maintainer time saved
    ────────────────────────────────────────
    Axiom: Boring/proven tech stack
    Status: ✅
    Notes: Bash gh CLI + Python stdlib — zero new deps
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories
    Status: ✅
    Notes: Pure CLI automation — no AI involved
    
    Feature Breakdown
    
    Task 1: Create _update_docs_cache() helper in utils.py
    Files: utils.py
    Dependencies: none
    Parallelizable: no
    Description: Add a new function _update_docs_cache(new_version, project_dir) that shallow-clones siongsheng/dokima-docs to a temp dir, runs dokima --help-json piped into scripts/cli-help.json, commits with message chore: update CLI reference for v{new_version}, pushes, and cleans up. All failures are non-blocking — log warnings and return. Use existing git(), _safe_run(), shutil (already imported in do_release()), and tempfile. Handle edge cases: clone fail, help-json fail, push fail, merge conflict — each warns and returns without raising.
    
    Task 2: Wire _update_docs_cache() into do_release()
    Files: utils.py
    Dependencies: Task 1
    Parallelizable: no
    Description: In do_release(), after the GitHub Release creation step (step 16) and before the print summary step (step 17), insert: _update_docs_cache(new_version, project_dir). In the dry_run branch (step 8), add: print(f"  [DRY RUN] Would update docs cache in siongsheng/dokima-docs") to existing print block. The function is non-blocking — failures inside _update_docs_cache() do not abort the release.
    
    Task 3: Write unit tests for _update_docs_cache()
    Files: tests/test_f026_docs_cache.py
    Dependencies: Task 2
    Parallelizable: yes
    Description: Create new test file with tests for: (a) dry_run=True skips entirely and prints plan, (b) clone failure warns and continues without raising, (c) push failure warns and continues, (d) happy path with mocked gh/git/subprocess verifies correct commands are issued with expected version in commit message, (e) gh CLI not on PATH warns and skips. Use unittest.mock.patch for subprocess, git, gh, and tempfile to avoid actual network calls. Follow existing test patterns in test_f024_release.py.
    
    Task 4: Add dry-run assertion to test_f024_release.py
    Files: tests/test_f024_release.py
    Dependencies: Task 2
    Parallelizable: yes
    Description: In the existing test_release_patch_dry_run test (or equivalent), add an assertion that the output includes "[DRY RUN] Would update docs cache in siongsheng/dokima-docs" when gh CLI is available on PATH. If gh is not on PATH in CI, the test verifies that absence is handled gracefully (no crash, no misleading output). ~10 LOC addition to existing test method.
    
    Panel Split
    
    | Wave   | Tasks          | Parallel              |
    |--------|----------------|-----------------------|
    | Wave 1 | Task 1         | —                     |
    | Wave 2 | Task 2         | —                     |
    | Wave 3 | Task 3, Task 4 | yes (different files) |
    
    Tasks 1 and 2 are sequential — both touch utils.py. Tasks 3 and 4 touch different test files and can run in parallel. Two coder agents for Wave 3.
    
    Build & Deploy
    
    - No new deploy steps — this is a modification to the existing release flow
    - dokima --release already requires gh CLI authenticated
    - Vercel auto-deploys on push to dokima-docs main (existing setup)
    - Env vars: none new. GH_TOKEN already set for release steps.
    
    Test Plan
    
    Happy Path
    - dokima --release patch on clean tree, default branch, synced with origin → bumps version, tags, creates GitHub Release, clones dokima-docs, writes updated cli-help.json, commits "chore: update CLI reference for vX.Y.Z", pushes, prints summary with ✓
    - dokima --release patch --dry-run → prints plan including "[DRY RUN] Would update docs cache in siongsheng/dokima-docs"
    
    Edge Cases
    - Clone destination already exists — gh repo clone will fail. Temp dirs use unique names (mkdtemp). Non-blocking: warn and continue.
    - docs repo has unstaged changes — git add should pick up only cli-help.json. Commit is explicit. If commit is empty (no changes), skip push and warn.
    - Empty cli-help.json — if dokima --help-json produces empty output, warn and skip commit (don't push an empty/broken file).
    - Version string contains special characters — inserted into commit message via f-string. Git commit messages handle any printable ASCII. Safe.
    - Concurrent release — dokima-docs push may conflict if two releases happen simultaneously. Merge conflict is caught by git push failure → warn, non-blocking.
    - Large help-json — cli-help.json is ~5KB currently. No size concern.
    
    Failure Modes
    - Network down for clone — gh repo clone times out/fails → warn, continue
    - Network down for push — git push times out/fails → warn, continue
    - Permission denied on push — gh not authenticated or lacks write access to dokima-docs → warn, continue
    - dokima --help-json crashes — if the new version has a bug that breaks --help-json, catch subprocess error → warn, continue
    
    Contract Invariants
    - do_release() must not fail because of docs update — all _update_docs_cache() exceptions are caught internally
    - Original release flow is unchanged when docs update is skipped — dry_run, missing gh, and all failure paths preserve existing behavior
    - Temp dirs are always cleaned up — finally: shutil.rmtree(tmpdir) regardless of success/failure
    - Version in commit message matches the version just released — new_version is passed directly from do_release()
    
    Risk Register
    
    Risk: gh CLI not authenticated for dokima-docs push
    Severity: MEDIUM
    Mitigation: Non-blocking warn; release succeeds regardless. Dokima repo
      access already required.
    Trigger: First release after F026 merge if token lacks docs-repo scope
    ────────────────────────────────────────
    Risk: Cloned docs repo wastes disk on failed cleanup
    Severity: LOW
    Mitigation: finally: shutil.rmtree() in temp dir. /tmp is tmpfs on most
      systems — reboot clears.
    Trigger: OSError during rmtree (rare)
    ────────────────────────────────────────
    Risk: Vercel deploy fails due to malformed cli-help.json
    Severity: LOW
    Mitigation: cli-help.json is generated by dokima --help-json which is
      tested in CI (F020 tests). Malformed output would be caught.
    Trigger: Breaking change to --help-json shape without updating
      generate-cli-ref.ts
    ────────────────────────────────────────
    Risk: Race condition: release while docs build is running
    Severity: LOW
    Mitigation: Vercel queues builds. Second push within build window is
      harmless — Vercel uses latest.
    Trigger: Two releases <60s apart
    
    Anti-Creep
    
    Features explicitly NOT in scope:
    - Do NOT regenerate the MDX page — only update scripts/cli-help.json. The generate-cli-ref.ts script runs during Vercel build. Do not call it from do_release().
    - Do NOT add new pages or sections to docs — this is a single-file cache update, not a docs CMS.
    - Do NOT add a --skip-docs flag — the docs update is already non-blocking on failure. No new CLI flag needed.
    - Do NOT add a release webhook — push to dokima-docs main already triggers Vercel deploy. No new integration.
    - Do NOT modify Vercel config — existing auto-deploy setup is sufficient.
    - Do NOT change the release version format — version string already comes from do_release(). No new parsing.
    
    Sign-Off Checklist
    
    - [ ] _update_docs_cache() is non-blocking — all failures are warnings, never sys.exit(1)
    - [ ] Dry-run mode prints docs cache plan without executing
    - [ ] Temp directory cleaned up in finally block
    - [ ] Commit message includes exact version string: "chore: update CLI reference for v{new_version}"
    - [ ] Existing do_release() behavior unchanged when gh CLI is absent
    - [ ] tests/test_f026_docs_cache.py covers: happy path, dry-run skip, clone fail, push fail, gh-missing
    - [ ] tests/test_f024_release.py dry-run assertion passes
    - [ ] python3 -m pytest tests/test_f024_release.py tests/test_f026_docs_cache.py -q passes
    - [ ] Manual test: dokima --release patch --dry-run output includes docs cache line
    - [ ] gh CLI --repo matching pattern same as existing in the codebase (siongsheng/dokima-docs)