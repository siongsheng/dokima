# F035: GitLab support: swap gh CLI for glab or abstract VCS layer

F035: GitLab VCS Support — Abstract VCS Layer
    
    Confidence: Medium (1 unverified assumption — glab JSON output format)  
    Impact: MEDIUM
    
    
    
    1. Executive Summary
    
    Dokima currently hard-depends on gh CLI for all VCS operations (PRs, issues, releases, repo cloning). This feature adds a vcs.py module that abstracts VCS operations behind semantic functions, auto-detects GitHub vs GitLab from the git remote URL, and supports an explicit --vcs github|gitlab override flag. All 14 gh() call sites in pipeline.py, roadmap.py, and utils.py are migrated to vcs.*() calls. The release workflow (dokima --release) and docs cache update remain GitHub-only for now. This unblocks GitLab-hosted projects from using dokima's full pipeline.
    
    CLARIFICATION: Assumption that glab mr view outputs valid JSON by default (no --json flag needed). The gh pr view --json flag has no direct glab equivalent — glab may use --output json or default to JSON. Impact if wrong: vcs_pr_view() returns unparseable output, breaking PR state checks, auto-repair, and archive logic. Mitigation: test against real glab v1.x output before merging Task 2.
    
    
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Status: ✅ YES
    Evidence: Shaun is actively migrating repos between GitLab instances
      (Anzen GitLab → Internet GitLab)
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: ✅ YES
    Evidence: ~300 LOC new code + ~200 LOC call-site migrations
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: ✅ YES
    Evidence: GitLab is the #2 VCS after GitHub; glab CLI has 10k+ stars
    ────────────────────────────────────────
    Axiom: Tech stack boring/proven?
    Status: ✅ YES
    Evidence: Python module pattern, subprocess shell-out to existing CLIs —
      same pattern as gh()
    ────────────────────────────────────────
    Axiom: Avoids AI hype?
    Status: ✅ YES
    Evidence: Pure CLI abstraction, zero AI component
    
    No misalignments flagged.
    
    
    
    3. Decision Table
    
    Option: A: Rename gh() to detect backend inline, keep raw CLI args
    Complexity: Low
    Testability: Medium (mocks tied to CLI args)
    Future-proof: Low (new VCS = more branches)
    Agent Prompt Impact: Minimal
    Verdict: Reject
    ────────────────────────────────────────
    Option: B: vcs.py module with semantic functions, auto-detect, --vcs flag
    Complexity: Medium
    Testability: High (mock one module)
    Future-proof: High (add backend = one file)
    Agent Prompt Impact: Medium (prompt text updated)
    Verdict: Accept
    ────────────────────────────────────────
    Option: C: Full OOP class hierarchy (VcsBackend, GitHubBackend,
      GitLabBackend)
    Complexity: High
    Testability: High
    Future-proof: High
    Agent Prompt Impact: Medium
    Verdict: Reject (over-engineering for 2 backends)
    
    Rejected: Option A — raw CLI args differ between gh and glab (e.g., --head vs --source-branch, --body vs --description), so inline dispatch would need args rewriting anyway. Option C — Python class hierarchy for 2 backends is premature; module-level functions match existing gh()/git() pattern.
    
    Ponytail Guard: Rung 7 — no existing VCS abstraction exists. The gh() function is a single-CLI hardcoded wrapper. A dispatch layer is the minimum that works.
    
    
    
    4. Impact
    
    Dokima becomes VCS-agnostic. Projects hosted on GitLab (or GitLab self-managed) can run full pipelines — PR/MR creation, issue management, auto-merge. The panel auto-detects the VCS from the git remote URL. Existing GitHub workflows are unaffected. Release and docs-cache workflows remain GitHub-only (they operate on dokima itself).
    
    Affected files (actual — from codebase audit):
    
    File: vcs.py
    Change: New — VCS abstraction module with backend detection and all 9 VCS
      operations
    LOC: +270
    Column 4:
    ────────────────────────────────────────
    File: utils.py
    Change: detect_repo() extended for GitLab URLs; _set_gh_token() →
      _set_vcs_token(); _redact_secrets() adds GLAB_TOKEN/GITLAB_TOKEN;
      replace gh() calls in release/docs-cache
    LOC: +80/-15
    Column 4:
    ────────────────────────────────────────
    File: pipeline.py
    Change: Replace 8 gh() call sites with vcs.(); update TL prompt to mention
      both gh/glab; update PR URL regex for GitLab MR URLs
    LOC: +35/-25
    Column 4:
    ────────────────────────────────────────
    File: roadmap.py
    Change: Replace 2 gh() call sites with vcs.(); update imports
    LOC: +5/-3
    Column 4:
    ────────────────────────────────────────
    File: dokima
    Change: Add --vcs github
    LOC: gitlab flag parsing and dispatch
    Column 4: +15
    ────────────────────────────────────────
    File: tests/test_vcs.py
    Change: New — platform detection, operation mapping, token handling,
      fallback
    LOC: +180
    Column 4:
    ────────────────────────────────────────
    File: tests/conftest.py
    Change: Add vcs.*() mock fixtures alongside existing gh/git mocks
    LOC: +20
    Column 4:
    ────────────────────────────────────────
    File: AGENTS.md
    Change: Update tech stack section for GitLab support and --vcs flag
    LOC: +5/-3
    Column 4:
    ────────────────────────────────────────
    File: README.md
    Change: Document GitLab usage, prerequisites, env var setup
    LOC: +15/-0
    Column 4:
    
    Total: ~625 LOC added, ~46 LOC removed, 0 new Python dependencies.
    
    
    
    5. What Changed
    
    - vcs.py — NEW: vcs_pr_create(), vcs_pr_merge(), vcs_pr_view(), vcs_pr_list(), vcs_pr_diff(), vcs_issue_create(), vcs_issue_view(), vcs_release_create(), vcs_repo_clone(), detect_vcs_backend(), parse_vcs_flag(), module-level VCS_BACKEND, VCS_TOKEN_ENV
    - utils.py — detect_repo() matches GitLab URLs (incl. subgroups); _set_gh_token() renamed to _set_vcs_token() (old name alias kept); _redact_secrets() covers GLAB_TOKEN/GITLAB_TOKEN; release/docs-cache gh() calls replaced with vcs.*()
    - pipeline.py — All 8 gh() call sites migrated to vcs.*(); TL agent prompt lists both gh pr review and glab mr review; PR URL regex matches gitlab.com/.../merge_requests/N
    - roadmap.py — 2 gh() call sites (pr_list, pr_diff) migrated to vcs_pr_list(), vcs_pr_diff()
    - dokima — New --vcs flag in arg parser, wired to VCS_BACKEND override
    - tests/test_vcs.py — NEW: VCS detection, operation mapping, token handling, glab-not-installed fallback
    - tests/conftest.py — Mock fixtures extended for vcs.*() functions
    - AGENTS.md, README.md — Documentation updates for GitLab support
    
    
    
    6. API / Interface Proposal
    
    python
    vcs.py — module-level state (set once at startup)
    VCS_BACKEND = "github"  # or "gitlab"
    VCS_TOKEN_ENV = "***"  # or "GLAB_TOKEN"
    REPO = ""  # owner/repo or namespace/project
    
    Core operations (all return (stdout, stderr, returncode))
    def vcs_pr_create(base, head, title, body) -> tuple
    def vcs_pr_merge(pr_num, auto=False) -> tuple
    def vcs_pr_view(pr_num, fields="state,merged") -> tuple  # returns JSON
    def vcs_pr_list(state="open", head=None, json_fields="url,number") -> tuple
    def vcs_pr_diff(pr_num, stat_only=False) -> tuple
    def vcs_issue_create(title, body, labels=None) -> tuple
    def vcs_issue_view(issue_num, fields="body,title") -> tuple
    def vcs_release_create(tag, title, target, generate_notes=True) -> tuple
    def vcs_repo_clone(repo_slug, target_dir) -> tuple
    
    Detection and config
    def detect_vcs_backend(project_dir) -> str  # "github" | "gitlab"
    def parse_vcs_flag() -> str | None  # reads --vcs from sys.argv
    
    
    Command mapping (gh → glab):
    
    Operation: Create PR/MR
    gh: pr create --base X --head Y --title Z --body W
    glab: mr create --target-branch X --source-branch Y --title Z
      --description W
    ────────────────────────────────────────
    Operation: Merge
    gh: pr merge N --merge
    glab: mr merge N
    ────────────────────────────────────────
    Operation: Auto-merge
    gh: pr merge N --auto
    glab: mr merge N --when-pipeline-succeeds
    ────────────────────────────────────────
    Operation: View
    gh: pr view N --json fields
    glab: mr view N (JSON is default)
    ────────────────────────────────────────
    Operation: List
    gh: pr list --state X --head Y --json Z
    glab: mr list --state X --source-branch Y --output json
    ────────────────────────────────────────
    Operation: Diff
    gh: pr diff N --stat
    glab: mr diff N (no --stat, post-process)
    ────────────────────────────────────────
    Operation: Issue create
    gh: issue create --title X --body Y
    glab: issue create --title X --description Y
    ────────────────────────────────────────
    Operation: Issue view
    gh: issue view N --json fields
    glab: issue view N
    ────────────────────────────────────────
    Operation: Release
    gh: release create TAG --generate-notes
    glab: release create TAG --description NOTES
    ────────────────────────────────────────
    Operation: Clone
    gh: repo clone owner/repo dir
    glab: repo clone namespace/project dir
    
    
    
    7. Data Model
    
    VCS state (module-level, set once at init):
    
    VCS_BACKEND: "github" | "gitlab"
    VCS_TOKEN_ENV: str  # e.g. "***" or "GLAB_TOKEN"
    REPO: str  # "owner/repo" (GitHub) or "namespace/project" (GitLab, may include subgroup: "group/subgroup/project")
    
    
    detect_vcs_backend() return:
    
    "github" | "gitlab" | None (unknown remote)
    
    
    No new persistent entities. VCS detection is computed at startup from git remote URL, cached as module-level variable.
    
    
    
    8. Security Considerations
    
    - _redact_secrets() extended to cover GLAB_TOKEN and GITLAB_TOKEN — same pattern as existing GH_TOKEN/GITHUB_TOKEN handling
    - VCS_TOKEN_ENV passed through to agent subprocess environments (same as current GH_TOKEN)
    - No new injection surfaces — vcs.*() functions use same subprocess.run([cli] + list(args)) pattern as existing gh()
    - GitLab token never appears in logs or PR bodies
    
    
    
    9. Documentation Impact
    
    - AGENTS.md line 10: Change "GitHub CLI for PR/issue management" to "GitHub CLI (gh) or GitLab CLI (glab) for PR/issue management — auto-detected from git remote"
    - README.md: Add GitLab usage section: glab installation prerequisite, --vcs flag, environment variable setup (GITLAB_TOKEN or GLAB_TOKEN)
    - docs/setup.md: Add GitLab section with glab auth login instructions (if this file exists)
    
    
    
    10. Anti-Creep
    
    Features explicitly NOT in scope:
    - ❌ No Bitbucket/Gitea/Gogs support — add when users ask
    - ❌ No release abstraction — dokima --release stays GitHub-only, errors on GitLab
    - ❌ No docs cache GitLab support — _update_docs_cache() stays GitHub-only
    - ❌ No auto-install of glab — users install glab CLI themselves (same as gh)
    - ❌ No GitLab CI integration — pipeline stays Hermes-driven
    - ❌ No webhook support changes — unchanged
    - ❌ No multi-VCS per project — one repo, one backend
    - ❌ No gh() function name change — kept as backward-compat wrapper
    
    
    
    11. Risk Register
    
    #: 1
    Risk: glab JSON output format differs from gh — callers that parse JSON
      break
    Severity: HIGH
    Mitigation: Test against real glab v1.x output. Add JSON field
      normalization in vcs.py. Wrap glab output to normalize keys.
    Trigger: First GitLab pipeline run
    ────────────────────────────────────────
    #: 2
    Risk: glab CLI missing on user's system
    Severity: MEDIUM
    Mitigation: Detect and print clear error: "glab not found. Install:
      https://gitlab.com/gitlab-org/cli". Dokima doctor should detect this.
    Trigger: User has GitLab remote but no glab
    ────────────────────────────────────────
    #: 3
    Risk: GitLab subgroup repo names break REPO detection (e.g.
      group/subgroup/project)
    Severity: MEDIUM
    Mitigation: Extend detect_repo() regex for
      gitlab.com[:/]namespace/subgroup/project. Test with 3+ path segments.
    Trigger: Deeply nested GitLab groups
    ────────────────────────────────────────
    #: 4
    Risk: MR auto-merge equivalent differs (gh pr merge --auto vs glab mr
      merge --when-pipeline-succeeds)
    Severity: MEDIUM
    Mitigation: Map flag correctly. Document that GitLab CI must be configured
      for this to work.
    Trigger: GitLab project without CI pipelines
    ────────────────────────────────────────
    #: 5
    Risk: Agent prompt text references gh pr review — TL breaks on GitLab
    Severity: MEDIUM
    Mitigation: Update TL prompt to list both gh and glab commands. TL agent
      picks correct one based on output instruction.
    Trigger: TL phase on GitLab project
    ────────────────────────────────────────
    #: 6
    Risk: glab mr view / glab mr list --stat equivalent doesn't exist
    Severity: LOW
    Mitigation: Post-process diff output in Python. No --stat flag in glab —
      pipe through diffstat or Python line counting.
    Trigger: Diff-based operations
    ────────────────────────────────────────
    #: 7
    Risk: Test suite mocks gh() directly — 44 test locations
    Severity: LOW
    Mitigation: gh() kept as backward-compat wrapper. New vcs.*() mock
      fixtures added alongside. Existing tests pass unchanged.
    Trigger: First test run after migration
    
    
    
    12. Test Plan (MANDATORY)
    
    Platform Detection (Task 1)
    - Happy path: git@github.com:owner/repo.git → ("github", "owner/repo")
    - Happy path: https://gitlab.com/group/project.git → ("gitlab", "group/project")
    - Happy path: git@gitlab.com:group/subgroup/project.git → ("gitlab", "group/subgroup/project")
    - Happy path: https://gitlab.internal.company.com/team/proj.git → ("gitlab", "team/proj") (with host override)
    - Edge case: Trailing .git absent → still matches
    - Edge case: HTTPS with .git suffix → correctly stripped
    - Edge case: GitLab subgroup with 3+ path segments → REPO captures full path
    - Failure mode: No git remote → None, print warning
    - Failure mode: Bitbucket/Gitea remote → None, print "Unsupported VCS" error
    - Contract invariant: detect_vcs_backend() never raises — returns backend str or None
    
    VCS Dispatch / Operation Mapping (Tasks 1-2)
    - Happy path: GitHub remote → vcs_pr_create(...) calls gh pr create ... with original args
    - Happy path: GitLab remote → vcs_pr_create(...) calls glab mr create ... with --base→--target-branch, --head→--source-branch, --body→--description
    - Edge case: vcs_release_create() on GitLab → prints error, returns rc=1 (release GitHub-only)
    - Edge case: Empty args → returns error tuple
    - Failure mode: glab not in PATH → returns ("", "glab not found...", 1)
    - Failure mode: subprocess timeout (30s) → returns rc=124
    - Contract invariant: Every vcs_*() returns (stdout, stderr, returncode) — same shape as gh()
    
    Token and Redaction (Task 3)
    - Happy path: GLAB_TOKEN env var set → loaded by _set_vcs_token()
    - Happy path: GITLAB_TOKEN env var set → loaded as fallback
    - Happy path: GitHub remote → _set_vcs_token() loads GH_TOKEN as before
    - Edge case: Neither token set but CLI handles auth natively → passthrough (glab has its own auth config)
    - Failure mode: Token appears in subprocess output → _redact_secrets() strips it before printing
    - Contract invariant: _redact_secrets() env_name list includes all 4 variants: GH_TOKEN, GITHUB_TOKEN, GLAB_TOKEN, GITLAB_TOKEN
    
    Pipeline Call-Site Migration (Tasks 4-5)
    - Happy path: vcs_pr_create() called in pipeline → PR/MR created on correct platform
    - Happy path: vcs_pr_view() returns JSON → parsed same way as gh pr view --json output
    - Edge case: MR URL format differs from PR URL → PR URL regex updated to match both github.com/.../pull/N and gitlab.com/.../merge_requests/N
    - Edge case: TL agent prompt text references wrong CLI → updated to list both gh pr review and glab mr review
    - Failure mode: glab subprocess fails → rc != 0 handled by existing error-checking code
    - Contract invariant: All existing pipeline error-handling code works unchanged — vcs_*() returns same (stdout, stderr, rc) tuple
    
    --vcs CLI Flag (Task 7)
    - Happy path: --vcs gitlab overrides auto-detection
    - Happy path: --vcs github forces GitHub even on GitLab remote
    - Edge case: --vcs bitbucket → error message, exit 1
    - Edge case: --vcs flag absent → auto-detect from remote
    - Contract invariant: parse_vcs_flag() returns None when flag absent, valid string when present
    
    Backward Compatibility (Task 9)
    - Happy path: gh() wrapper still functions — all 42 existing gh() mock tests pass
    - Happy path: Full test suite (679 tests) passes without modification
    - Edge case: Direct gh() call without VCS init → lazy-detects backend, delegates to vcs()
    - Contract invariant: gh() signature unchanged: (*args, **kwargs) → (str, str, int)
    
    
    
    13. Feature Breakdown — Tasks
    
    Task 1: Create vcs.py module with backend detection and PR operations
    Files: vcs.py
    Dependencies: none
    Parallelizable: yes
    Description: Create vcs.py with module-level state (VCS_BACKEND, VCS_TOKEN_ENV, REPO), detect_vcs_backend() function scanning git remote URL for github.com/gitlab.com, parse_vcs_flag() reading --vcs from sys.argv, and vcs_pr_create/vcs_pr_merge/vcs_pr_view/vcs_pr_list/vcs_pr_diff functions with gh/glab dispatch (~150 LOC).
    
    Task 2: Add issue, release, and repo operations to vcs.py
    Files: vcs.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Add vcs_issue_create, vcs_issue_view, vcs_release_create (GitHub-only, errors on gitlab), vcs_repo_clone, and a _run_vcs() internal helper that runs right CLI with right token env. Wire module-level VCS_BACKEND and VCS_TOKEN_ENV from detect_vcs_backend() output (~120 LOC).
    
    Task 3: Extend detect_repo() for GitLab URLs and add VCS token utilities
    Files: utils.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Extend detect_repo() regex to match gitlab.com[:/] URLs including subgroups like group/subgroup/project. Rename _set_gh_token() to _set_vcs_token() with GitLab token fallback — keep old name as alias. Extend _redact_secrets() env_name list with GLAB_TOKEN and GITLAB_TOKEN (~60 LOC).
    
    Task 4: Migrate pipeline.py gh() calls to vcs.*()
    Files: pipeline.py
    Dependencies: [Task 1, Task 2]
    Parallelizable: no
    Description: Replace 8 gh() call sites in pipeline.py with vcs.*() equivalents: pr_create (2 sites), pr_list (4 sites), pr_view (5 sites), issue_create (1 site), issue_view (1 site). Update PR URL regex to also match gitlab.com/.../merge_requests/N. Update TL agent prompt text to mention both gh pr review and glab mr review (~80 LOC).
    
    Task 5: Migrate roadmap.py gh() calls and release/docs-cache in utils.py
    Files: roadmap.py, utils.py
    Dependencies: [Task 2, Task 3]
    Parallelizable: no
    Description: Replace gh() call sites in roadmap.py (pr_list at line 232, pr_diff at line 246) and utils.py (pr_merge at lines 844/857, pr_view at line 2574, release_create at line 2870, repo_clone at line 2670) with vcs.*() equivalents. Update imports in both files (~60 LOC).
    
    Task 6: Update agent profile config and env passthrough for VCS tokens
    Files: utils.py
    Dependencies: [Task 3, Task 5]
    Parallelizable: no
    Description: Update agent profile default configs (strategist/coder/tech-lead/nm) to include GLAB_TOKEN and GITLAB_TOKEN in terminal.env_passthrough arrays. Update _set_vcs_token() to load correct token based on VCS_BACKEND. Add VCS detection to main() startup sequence (~50 LOC).
    
    Task 7: Add --vcs flag to CLI and update help text
    Files: dokima, utils.py
    Dependencies: [Task 1, Task 3, Task 6]
    Parallelizable: no
    Description: Add --vcs github|gitlab flag to arg parsing in dokima entry point (passes through to set VCS_BACKEND). Update HELP_TEXT to document --vcs. Add to CLI_METADATA flags list. Wire parse_vcs_flag() into main() before VCS operations begin (~40 LOC).
    
    Task 8: Write tests for vcs.py and integration
    Files: tests/test_vcs.py
    Dependencies: [Task 1, Task 2, Task 3]
    Parallelizable: yes
    Description: Create tests/test_vcs.py with: detect_vcs_backend() for github/gitlab/unknown/subgroup URLs, vcs_pr_create() args for both backends, vcs_pr_merge() for both, vcs_issue_create() for both, vcs_release_create() error on gitlab, VCS token env handling, parse_vcs_flag() parsing, glab-not-installed fallback. Mock subprocess.run to verify correct CLI and args (~180 LOC).
    
    Task 9: Update conftest.py mock fixtures for backward compat
    Files: tests/conftest.py
    Dependencies: [Task 4, Task 5]
    Parallelizable: yes
    Description: Add vcs.() mock patches to mock_orchestrator fixture alongside existing gh/git mocks. Ensure existing tests continue to pass — gh() wrapper still works, new vcs.() functions get mocked. Verify: run existing test suite, confirm all 679 tests pass (~30 LOC).
    
    Task 10: Update AGENTS.md and README for GitLab support
    Files: AGENTS.md, README.md
    Dependencies: [Task 7]
    Parallelizable: yes
    Description: Update AGENTS.md tech stack section to mention GitLab CLI support and --vcs flag. Update README to document GitLab usage: glab installation prerequisite, --vcs flag, environment variable setup (GITLAB_TOKEN or GLAB_TOKEN). Update docs/setup.md if it exists (~30 LOC).
    
    
    
    14. Panel Split — Parallelization
    
    
    Wave 1: Task 1 (vcs.py) — 1 coder
            [no other parallel tasks — only one unblocked at start]
    
    Wave 2: Task 2 (vcs.py) — 1 coder, sequential after Task 1
            + Task 4 (pipeline.py) — 1 coder, depends on Task 1,2 → starts in Wave 2
            [Task 2 and Task 4 share no files — vcs.py vs pipeline.py]
    
    Wave 3: Task 3 (utils.py) — 1 coder, depends on Task 1
            + Task 8 (tests/test_vcs.py) — 1 coder, depends on Task 1,2,3 → starts here
            [Task 3 and Task 8 share no files — utils.py vs new test file]
    
    Wave 4: Task 5 (roadmap.py, utils.py) — 1 coder, depends on Task 3
            [no parallel — Task 5 touches utils.py, next task also does]
    
    Wave 5: Task 6 (utils.py) — 1 coder, depends on Task 5
            [sequential — shares utils.py with Task 5 and Task 7]
    
    Wave 6: Task 7 (dokima, utils.py) — 1 coder, depends on Task 6
            + Task 9 (tests/conftest.py) — 1 coder, depends on Task 4,5
            + Task 10 (AGENTS.md, README.md) — 1 coder, depends on Task 7… but Task 7 starts in same wave!
    
                Wait — Task 10 depends on Task 7 and they run in same wave? No.
                Task 7 starts in Wave 6, Task 10 must start in Wave 7.
    
    Wave 6: Task 7 (dokima, utils.py) — 1 coder, depends on Task 6
            + Task 9 (tests/conftest.py) — 1 coder, depends on Task 4,5 → no file overlap with Task 7
    
    Wave 7: Task 10 (AGENTS.md, README.md) — 1 coder, depends on Task 7
            [final docs wave]
    
    
    Total: 7 waves, 1-3 coders per wave, 10 tasks. Estimated wall-clock: ~35-45 minutes (Wave 1: ~5 min, Wave 2: ~8 min, Wave 3: ~8 min, Wave 4: ~5 min, Wave 5: ~5 min, Wave 6: ~8 min, Wave 7: ~3 min).
    
    
    
    15. Build & Deploy
    
    - Build: python3 -c "compile(open('dokima').read(), 'dokima', 'exec')" — no change
    - Test: python3 -m pytest tests/ -q — must pass all 679 existing tests plus ~15 new tests
    - New test file: python3 -m pytest tests/test_vcs.py -v
    - CI: No CI changes needed — same GitHub Actions workflow
    - Env vars: New optional GLAB_TOKEN or GITLAB_TOKEN (existing GH_TOKEN/GITHUB_TOKEN unchanged)
    - No new PyPI dependencies: glab is a system-level CLI, not a Python package
    - glab prerequisite: Users must install glab CLI: brew install glab (macOS) or documented Linux equivalent
    
    
    
    16. Sign-Off Checklist
    
    - [ ] vcs.py module created with all 9 operation functions and backend detection
    - [ ] detect_vcs_backend() handles github.com, gitlab.com, self-hosted GitLab, subgroups, SSH, HTTPS
    - [ ] GitHub backend calls gh with original args — zero behavior change
    - [ ] GitLab backend calls glab with correctly mapped args (target-branch, source-branch, description)
    - [ ] detect_repo() regex matches GitLab URLs including subgroups (group/subgroup/project)
    - [ ] _redact_secrets() covers GLAB_TOKEN and GITLAB_TOKEN — no credential leaks
    - [ ] _set_vcs_token() loads correct token for detected backend
    - [ ] Agent profile env_passthrough includes GLAB_TOKEN and GITLAB_TOKEN
    - [ ] All 14 gh() call sites in pipeline.py/roadmap.py/utils.py migrated to vcs.*()
    - [ ] --vcs flag parsed, documented in --help, included in CLI_METADATA
    - [ ] TL agent prompt lists both gh pr review and glab mr review
    - [ ] vcs_release_create() errors clearly on GitLab (release is GitHub-only)
    - [ ] glab not installed → clear error message with install link
    - [ ] All 679 existing tests pass without modification (gh() backward compat)
    - [ ] New tests/test_vcs.py covers: platform detection, operation mapping, token handling, fallback
    - [ ] AGENTS.md updated: tech stack mentions multi-VCS support and --vcs flag
    - [ ] README.md updated: GitLab usage, prerequisites, env var setup
    - [ ] docs/setup.md updated with GitLab section (if file exists)