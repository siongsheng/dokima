# F024: Auto-Release — Tagging, Changelog, and GitHub Releases

Now I have the full picture. Let me produce the complete corrected spec.
    
    Position: F024 is a CLI-only feature (no APIs, no data model changes) — it adds a --release command to the existing VERSION/upgrade infra. The existing code has well-established patterns (show_help, check_upgrade, CLI_METADATA, HELP_TEXT, flag scanning in main()) that the implementation must follow. (High confidence)
    
    
    
    F024: Auto-Release — Tagging, Changelog, and GitHub Releases
    
    Status: Spec — Awaiting Approval  
    Confidence: High  
    Impact: MEDIUM  
    Dependencies: F021 (Complete — VERSION file, --version, --upgrade all exist)
    
    
    
    Executive Summary
    
    Add a dokima --release [patch|minor|major] command that releases Dokima itself. One command bumps the VERSION file, auto-generates a changelog from merged PRs grouped by conventional commit prefix (feat:, fix:, chore:), commits the bump, creates a vX.Y.Z git tag, and publishes a GitHub Release — all with pre-flight validations (clean tree, default branch, synced with origin). This is maintainer tooling — it does not touch the panel pipeline or user-facing agent flows. The existing --version and --upgrade infrastructure provides the version read-path and tag-discovery pattern that --release extends.
    
    
    
    Constitution Check
    
    Axiom: Solves user's own pain?
    Answer: YES
    Evidence: Manual releases are error-prone — Shaun runs dokima releases
      himself
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Answer: YES
    Evidence: ~200 LOC, one session
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Answer: N/A — internal tooling, no monetization
    Evidence:
    ────────────────────────────────────────
    Axiom: Boring tech stack?
    Answer: YES
    Evidence: Python + gh CLI + git — same stack as existing check_upgrade()
    ────────────────────────────────────────
    Axiom: Avoid AI hype?
    Answer: YES
    Evidence: No AI involved, pure CLI release automation
    
    No constitution violations.
    
    
    
    Impact
    
    Maintainers get a single-command release workflow instead of manually editing VERSION, reading git log for changelogs, running git tag, and running gh release create. Users of --upgrade benefit from consistent, well-formed GitHub Releases.
    
    What Changed
    
    - utils.py: +handle_release(level) function — bumps VERSION, generates changelog, tags, creates GitHub Release. +HELP_TEXT gets --release entry. +CLI_METADATA gets --release command.
    - dokima: +is_release flag in main(), + flag scanning for --release [patch|minor|major], + early dispatch to handle_release().
    - VERSION: Modified by handle_release() (bumped in-place, committed).
    - tests/test_f024_release.py: ~8 tests — happy path per bump level, validation rejections, changelog format, GH Release CLI args, edge cases.
    
    
    
    Decision Table
    
    Option: Single handle_release() in utils.py, dispatched from main()
    Simplicity: High — follows check_upgrade pattern exactly
    Risk: Low — bounded scope
    Reuse of existing infra: Reuses VERSION, git helpers, _safe_run, gh()
    Verdict: Accept
    ────────────────────────────────────────
    Option: Separate release.py module
    Simplicity: Lower — adds module wiring overhead
    Risk: Low
    Reuse of existing infra: Would duplicate git/gh wrappers or add
      cross-module deps
    Verdict: Reject (violates ponytail rung 5 — utils.py already has all the
      primitives)
    ────────────────────────────────────────
    Option: Shell script wrapper
    Simplicity: Medium — different toolchain
    Risk: Medium — no test coverage
    Reuse of existing infra: None
    Verdict: Reject (inconsistent with Python-only codebase)
    
    
    
    API/Interface Proposal
    
    N/A — this is a CLI command, not an API. No routes, no data structures, no protocol changes.
    
    Security Considerations
    
    N/A — no attack surface change. handle_release() uses existing _safe_run() (list-arg subprocess, no shell=True). No user input reaches gh release create beyond the auto-generated changelog (derived from git log). The command is maintainer-only — not exposed to agents.
    
    Documentation Impact
    
    README: Add --release to CONTROL section (copy from HELP_TEXT).  
    CLI help: HELP_TEXT and CLI_METADATA updated by this feature.  
    Agent docs: No change — agents don't release.
    
    
    
    Task Breakdown
    
    Task 1: Add is_release flag scanning and early dispatch in main()
    - Files: dokima
    - Dependencies: [none]
    - Parallelizable: yes
    - Description: Add is_release = False and release_level = None to flag scanning loop; detect --release flag and capture next arg as patch|minor|major; add early dispatch if is_release: handle_release(release_level) in the control flags section (after is_upgrade, before is_version).
    
    Task 2: Implement handle_release(level) — validations and VERSION bump
    - Files: utils.py
    - Dependencies: [Task 1]
    - Parallelizable: no
    - Description: Validate clean working tree (git status --porcelain empty), on default branch, synced with origin (git fetch && git diff origin/<branch> empty); bump VERSION file in-place; validate level arg is patch|minor|major; compute new version from _version_newer-compatible logic.
    
    Task 3: Implement changelog generation from merged PRs
    - Files: utils.py
    - Dependencies: [Task 2]
    - Parallelizable: no
    - Description: In handle_release(), run git log v<prev>..HEAD --oneline to find commits since last tag; map each to merged PR via gh pr list --search <sha>; group by conventional commit prefix (feat:, fix:, chore:); format as ## What's Changed\n### Features\n- ...\n### Fixes\n- ...\n### Chores\n- ...; fall back to git log v<prev>..HEAD --oneline --no-merges if gh PR search fails.
    
    Task 4: Implement git tag and GitHub Release creation
    - Files: utils.py
    - Dependencies: [Task 3]
    - Parallelizable: no
    - Description: After VERSION bump, git add VERSION, git commit -m "chore: bump version to v<new>", git tag v<new>, git push origin <branch> --tags; then gh release create v<new> --title "v<new>" --notes "<changelog>"; print confirmation with tag and URL.
    
    Task 5: Update HELP_TEXT and CLI_METADATA
    - Files: utils.py
    - Dependencies: [Task 1]
    - Parallelizable: yes
    - Description: Add dokima --release [patch|minor|major]  Bump version, generate changelog, tag, and publish GitHub Release to HELP_TEXT CONTROL section; add corresponding entry to CLI_METADATA commands list; add --release to short usage line.
    
    Task 6: Write test file — happy path and validations
    - Files: tests/test_f024_release.py
    - Dependencies: [Task 2, Task 3, Task 4]
    - Parallelizable: yes (can write test stubs against expected interface while impl is in progress)
    - Description: Create tests/test_f024_release.py with tests: (1) --release patch bumps patch version; (2) --release minor resets patch to 0; (3) --release major resets minor and patch; (4) dirty tree exits non-zero with message; (5) wrong branch exits non-zero; (6) invalid level arg exits non-zero; (7) --release with no arg exits non-zero; (8) changelog section headers present in generated notes.
    
    
    
    Test Plan
    
    Happy path:
    - dokima --release patch on a clean, synced default branch: VERSION bumped 1.2.1→1.2.2, tag v1.2.2 created, GitHub Release published with changelog.
    - dokima --release minor: 1.2.1→1.3.0.
    - dokima --release major: 1.2.1→2.0.0.
    
    Edge cases:
    - No prior semver tag exists (first release): changelog covers all commits since repo init, tag is v<version> directly.
    - No merged PRs between tags: changelog uses raw commit log as fallback.
    - VERSION file missing (how?): handle_release exits with clear error, exits non-zero.
    - --release with extra args (e.g., --release patch /some/path): ignored, same as --version pattern.
    
    Failure modes:
    - Dirty working tree: exits non-zero, message "Working tree is not clean. Commit or stash changes first."
    - Not on default branch: exits non-zero, message "Must be on <branch> to release."
    - Not synced with origin: exits non-zero, message "Branch is behind origin. Pull first."
    - gh CLI not authenticated: error from gh release create surfaces.
    - Network timeout during gh release create: exits non-zero with message.
    - Invalid level arg: exits non-zero, message "Release level must be patch, minor, or major."
    
    Contract invariants:
    - VERSION file is only modified if all pre-flight validations pass.
    - The git tag and GitHub Release are always in sync (same version string).
    - Changelog is always generated from git history before the bump commit (so the bump commit itself doesn't appear in this release's changelog).
    - --release exits 0 only after tag is pushed and release is created; any partial failure leaves no tag unpushed.
    
    
    
    COTS Build-vs-Buy
    
    Component: Git operations
    Build/Buy: Built (existing git() + _safe_run() wrappers)
    Justification: Already in utils.py, ponytail rung 2
    ────────────────────────────────────────
    Component: GitHub Release
    Build/Buy: Buy (gh release create)
    Justification: Already a project dependency, ponytail rung 5
    ────────────────────────────────────────
    Component: Changelog generation
    Build/Buy: Built
    Justification: Trivial regex grouping, no external lib needed, ponytail
      rung 7
    ────────────────────────────────────────
    Component: Semver math
    Build/Buy: Built
    Justification: ~15 lines of integer math, ponytail rung 6
    
    No new dependencies. No new pip packages.
    
    
    
    Risk Register
    
    #: 1
    Risk: Changelog PR-mapping fails silently (empty changelog)
    Severity: Low
    Mitigation: Fallback to raw git log --oneline; test verifies both paths
    Trigger: gh pr list --search fails or returns nothing
    ────────────────────────────────────────
    #: 2
    Risk: git push --tags succeeds but gh release create fails
    Severity: Medium
    Mitigation: Print clear error, tell maintainer to run gh release create
      manually with the generated notes (already printed)
    Trigger: Network error after push
    ────────────────────────────────────────
    #: 3
    Risk: Version bump computed incorrectly for prerelease tags
    Severity: Low
    Mitigation: Filter to strict vX.Y.Z pattern (same regex as check_upgrade)
    Trigger: Non-semver tags exist in repo
    ────────────────────────────────────────
    #: 4
    Risk: --release runs on a repo that isn't dokima
    Severity: Low
    Mitigation: No guard — accept it; it's a general-purpose release tool.
      Only harm is wrong changelog.
    Trigger: Maintainer runs in wrong directory
    
    
    
    Anti-Creep
    
    - NOT building: --release --dry-run flag. KISS — if the maintainer wants to preview, they read git log manually.
    - NOT building: Conventional commit enforcement. Dokima doesn't require conventional commits — grouping is best-effort, unmatched PRs go under "Other".
    - NOT building: --release for target projects (e.g., dokima --release patch ~/huat). This is dokima self-release only.
    - NOT building: Release notes templating. The format is fixed: ## What's Changed\n### Features\n...
    - NOT building: GPG signing of tags. Not needed for a panel tool.
    - NOT building: --release in the panel pipeline. This is a manual maintainer command, not an agent operation.
    
    
    
    Sign-Off Checklist
    
    - [ ] dokima --release patch bumps patch version and creates tag + release
    - [ ] dokima --release minor resets patch to 0
    - [ ] dokima --release major resets minor and patch to 0
    - [ ] Dirty tree rejected with clear message
    - [ ] Wrong branch rejected with clear message
    - [ ] Behind-origin rejected with clear message
    - [ ] Invalid level arg rejected with clear message
    - [ ] Changelog contains ## What's Changed header
    - [ ] --help shows --release in CONTROL section
    - [ ] --help-json includes --release in commands array
    - [ ] All 8 tests pass in tests/test_f024_release.py
    - [ ] Existing tests unaffected (F021 version tests, F020 help-json tests)