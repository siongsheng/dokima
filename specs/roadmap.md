# Dokima Roadmap

## Phase 1: Core Stability & Test Coverage

### F002: Pipeline Integration Tests
**Priority:** P0
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a contributor, I run one command and a full pipeline executes against a test repo — strategist reads AGENTS.md, produces a spec, coder implements it, vet runs the build, nm reviews, TL delivers verdict. All 5 phases verified end-to-end. Failures at any phase produce clear diagnostics, not silent exits.

### F003: Edge Case & Robustness Tests
**Priority:** P0
**Dependencies:** F002
**Status:** [x] Done
**User Story:** As a panel operator, the pipeline handles every known failure mode gracefully: strategist returns interview mode (exit 2), strategist produces zero ### Task headers (DAG re-prompt fires), coder times out (partial results captured), coder produces only RED commits (vet catches it), nm model provider is down (fallback fires), TL detects BLOCKED verdict (auto-fix loop triggers), concurrent pipelines don't fight over lock files, stop/kill signals clean up worktrees, feature description contains special characters (slugify doesn't crash).

### F004: Deterministic Quality Gates
**Priority:** P1
**Dependencies:** F002
**Status:** [x] Done
**User Story:** As a contributor, running the same feature through the pipeline twice produces comparable output quality — same spec structure, same task granularity (5-15 min each), same DAG format, PR body has real Impact/What Changed (not placeholders). Quality regressions are caught by CI — if a panel change causes the strategist to output 14K-char specs for High-confidence features, the test fails.

### F005: Model Family Fallback
**Priority:** P1
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a panel operator, if the primary model provider is down, the panel auto-falls-back to a configured alternative (e.g. deepseek → openrouter → anthropic).

### F001: Security Hardening
**Priority:** P0
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a panel operator, I trust that shell injection, hardcoded secrets, and agent prompt injection are systematically blocked.

### F006: Error Recovery & Resume
**Priority:** P1
**Dependencies:** F002
**Status:** [x] Done
**User Story:** As a panel operator, if a pipeline crashes mid-run, I can resume from the last completed phase instead of restarting from scratch. Partial state (spec file, task extract, feature branch, open PR) is not lost.

---

## Phase 2: Pipeline Intelligence

### F008: Strategist Respects Existing Specs
**Priority:** P0
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a panel operator, if I write a spec at `specs/<feature>-spec.md` before running the panel, the strategist uses it as the authoritative source — validating and enhancing, not rewriting from scratch.

### F007: Strategist Read the Actual Product
**Priority:** P0
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a panel operator, the strategist reads the AGENTS.md header for GitHub links to the product being documented, finds the local repo, and treats its AGENTS.md as truth — never deriving architecture from the docs site itself.

### F009: Depth Gating Tuning
**Priority:** P1
**Dependencies:** F007, F008
**Status:** [x] Done
**User Story:** As a panel operator, the confidence × impact matrix reliably selects the right depth — docs changes don't run full nm+TL, novel features get full vetting.

### F010: Parallel Coder Robustness
**Priority:** P1
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a panel operator, parallel coders never conflict on the same file, worktree cleanup is reliable, and timeout/dead agents don't block the wave.

### F019: Data-Driven Execution Mode (Orchestrator Computes)
**Priority:** P1
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a panel operator, the orchestrator auto-selects batch coder (single session, no worktrees) for small additive features and per-task spawn for complex/refactor features — derived from existing DAG signals (task count, file count, parallelizability). No strategist changes needed.

### F023: Pipeline Self-Healing
**Priority:** P1
**Dependencies:** F010
**Status:** [x] Done
**User Story:** As a panel operator, the pipeline detects and recovers from common failure patterns without human intervention — auto-fix infinite loops (nm fix already applied), partial coder output (truncated agent), and stale lock files from killed pipelines.

### F022: Modular Architecture
**Priority:** P1
**Dependencies:** F010, F023
**Status:** [x] Done
**User Story:** As a contributor, the 5,400-line monolith is split into modules (agent.py, pipeline.py, roadmap.py, tasks.py, utils.py) with clear interfaces — agents can read and modify one module without loading the entire codebase. Same behavior, same tests, smaller context windows.

### F022b: Modular Architecture — Pipeline, Roadmap, Tasks
**Priority:** P1
**Dependencies:** F022
**Status:** [x] Done
**User Story:** As a contributor, the remaining 3 modules (pipeline.py, roadmap.py, tasks.py) are extracted from the monolith. Pipeline phase coordination, DAG task execution, roadmap parsing, and task management each live in their own module. Agents working on pipeline logic read ~300 lines instead of 5000+. Builds on F022's agent.py and utils.py extraction. Same 640 tests, same behavior.

### F020: Structured CLI Output (`--help-json`)
**Priority:** P2
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a docs maintainer, `dokima --help-json` outputs all commands, flags, and env vars as structured JSON — consumed by the docs site to auto-generate the CLI reference page. No more manual sync between code and docs.

### F021: Semantic Versioning + GitHub Releases
**Priority:** P2
**Dependencies:** F020
**Status:** [x] Done
**User Story:** As a user, `dokima --version` prints the current version. Releases are tagged and published on GitHub with auto-generated changelogs from merged PRs. `dokima --upgrade` checks for newer versions.

### F024: Auto-Release — Tagging, Changelog, and GitHub Releases
**Priority:** P2
**Dependencies:** F021
**Status:** [x] Done
**User Story:** As a maintainer, `dokima --release [patch|minor|major]` bumps the version, auto-generates a changelog from merged PRs grouped by conventional commit prefix, creates a git tag, and publishes a GitHub Release — all in one command. Validates clean tree, default branch, and git sync before releasing.

### F026: Auto-Update Docs CLI Cache on Release
**Priority:** P2
**Dependencies:** F021, F024, dokima-docs repo
**Status:** [x] Done
**User Story:** Running `dokima --release` auto-updates the docs site's CLI reference cache. No manual `--help-json > scripts/cli-help.json` step needed.

---

## Phase 3: Distribution & Portability


### F027: Upgrade codebase-map.md to domain-aware format with Start Here, Domain Map, Impact Map, and Test Map sections. Inject map into strategist, coder-worktree, and tech-lead prompts.
**Priority:** P2
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a user, I can upgrade codebase-map.md to domain-aware format with start here, domain map, impact map, and test map sections. inject map into strategist, coder-worktree, and tech-lead prompts.



### F030: CLI redesign: replace --add/--next/--fix/--status/--stop/--kill/--list-crons/--version/--upgrade/--release with proper subcommands (dokima add, dokima next, etc). Flags (--force-full, --max-parallel) keep -- prefix. Update all tests, scripts, AGENTS.md, roadmap, and docs.
**Priority:** P2
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a user, I can cli redesign: replace --add/--next/--fix/--status/--stop/--kill/--list-crons/--version/--upgrade/--release with proper subcommands (dokima add, dokima next, etc). flags (--force-full, --max-parallel) keep -- prefix. update all tests, scripts, agents.md, roadmap, and docs.



### F036: Fix SHOULD FIX issue creation: extract from PR review text (not just nm_stdout), handle table-format findings (R1 | RELIABILITY | ... | SHOULD FIX). Add tests for all extraction formats.
**Priority:** P2
**Dependencies:** F034
**Status:** [x] Done
**User Story:** As a user, I can fix should fix issue creation: extract from pr review text (not just nm_stdout), handle table-format findings (r1 | reliability | ... | should fix). add tests for all extraction formats.

### F037: Blocker Resolution Tracking — cross-reference fix PRs to the original blocker PR they resolve. After `dokima fix` completes and TL approves, auto-update the original PR's `### Blockers` section with strikethrough + link to the resolution PR. Optionally create GitHub issues from blockers (matching SHOULD FIX pattern) and auto-close them when the fix PR merges.
**Priority:** P2
**Dependencies:** F034
**Status:** [x] Done
**User Story:** As a developer, when I run `dokima fix` to resolve TL blockers, I know exactly which blockers were fixed and where — no manual cross-referencing between PRs. The original PR's blocker section links to the resolution PR, and GitHub issues (if created) auto-close on merge.

### F038: Surface nm and TL findings in PR body — when nm runs (Phase 4) or TL reviews (Phase 5), inject their findings into the PR body as `### nm Review` and `### TL Review` sections. At depth=vet+nm (no TL), nm findings still appear. Currently nm output is invisible (37K chars logged but never surfaced); TL findings only appear via a separate PR comment. SHOULD FIX items from both nm and TL are extracted as GitHub issues regardless of depth.
**Priority:** P2
**Dependencies:** F036, F037
**Status:** [x] Done Progress
**User Story:** As a developer reviewing a pipeline PR, I see all review findings directly in the PR body — nm adversarial review and TL review each have their own section with risk assessment, blockers, and SHOULD FIX items. I don't need to dig through pipeline logs or click through to separate comments to know what was found.

### F032: Agent-as-Judge self-assessment: coder answers 3 questions before pushing — does every spec requirement have code, what am I least confident about, what would TL flag. Catches empty PRs at source.
**Priority:** P2
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a user, I can agent-as-judge self-assessment: coder answers 3 questions before pushing — does every spec requirement have code, what am i least confident about, what would tl flag. catches empty prs at source.


### F033: Cross-run learning via conventions.md: when TL blocks a PR for a pattern violation, append a one-line rule to conventions.md. Next strategist reads it. No vector DB, no pattern extraction — human-readable rules that compound.
**Priority:** P2
**Dependencies:** None
**Status:** [x] Done Progress
**User Story:** As a user, I can cross-run learning via conventions.md: when tl blocks a pr for a pattern violation, append a one-line rule to conventions.md. next strategist reads it. no vector db, no pattern extraction — human-readable rules that compound.


### F034: dokima fix --issue N: pull GitHub issue body, extract file/line/fix/verify from structured format, spawn coder to implement. Also upgrade SHOULD FIX issue creation to include What/Fix/Verify sections for coder-readability.
**Priority:** P2
**Dependencies:** F032
**Status:** [x] Done
**User Story:** As a user, I can dokima fix --issue n: pull github issue body, extract file/line/fix/verify from structured format, spawn coder to implement. also upgrade should fix issue creation to include what/fix/verify sections for coder-readability.

### F029: Auto-generate CLI reference page from cli-help.json during Vercel build instead of hand-written MDX. New flags and commands appear in docs automatically on every release.
**Priority:** P2
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a user, I can auto-generate cli reference page from cli-help.json during vercel build instead of hand-written mdx. new flags and commands appear in docs automatically on every release.


### F031: dokima init back-and-forth interview mode — strategist asks clarifying questions about users, goals, anti-goals, and constraints before producing constitution docs. Loops until confidence is High, then writes specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md.
**Priority:** P2
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a user, I can dokima init back-and-forth interview mode — strategist asks clarifying questions about users, goals, anti-goals, and constraints before producing constitution docs. loops until confidence is high, then writes specs/mission.md, specs/tech-stack.md, specs/roadmap.md, specs/conventions.md.

### F011: Installer Script
**Priority:** P2
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a new developer, I run `curl -sSL https://get.dokima.dev | bash` and get a working Dokima installation — script symlinks into PATH, checks dependencies (Python 3.6+, gh CLI, Hermes Agent), and prints next steps.

### F012: Profile Templates
**Priority:** P2
**Dependencies:** F011
**Status:** [x] Done
**User Story:** As a new developer, `dokima init` creates agent profiles (`strategist`, `coder`, `tech-lead`, `nm`) with sensible defaults — I only need to add my API keys.

### F013: Vendor-Agnostic Model Config
**Priority:** P2
**Dependencies:** F005, F012
**Status:** [x] Done
**User Story:** As a developer using Anthropic, I configure `ANTHROPIC_API_KEY` and the panel maps strategist→claude-sonnet, coder→claude-haiku, TL→claude-opus — no deepseek dependency.

### F014: nm Script Portability
**Priority:** P2
**Dependencies:** F011
**Status:** [x] Done
**User Story:** As a new developer, the adversarial review script (`nm`) is installed with the panel — same behavior, same model diversity requirement, no manual `~/bin/nm` symlink needed.

### F015: README & Quickstart Guide
**Priority:** P2
**Dependencies:** F011, F012, F013, F014
**Status:** [x] Done
**User Story:** As a new developer, I clone dokima, follow a 5-minute quickstart, and run my first pipeline on a demo repo — no tribal knowledge required.

### F016: Config Validation (`dokima doctor`)
**Priority:** P2
**Dependencies:** F012
**Status:** [x] Done
**User Story:** As a developer, `dokima doctor` checks: Hermes Agent running, profiles configured, API keys valid, gh CLI authenticated, nm script present — and tells me exactly what to fix.

---

## Icebox (Post-Stable)

### F017: Dokima-as-Service
**Priority:** P3
**Dependencies:** Full Phase 3 (F011-F016)
**Status:** [x] Done
**User Story:** As a team lead, I point Dokima at a GitHub webhook and it auto-reviews every PR — no CLI needed, no local machine dependency.

### F018: Multi-Repo Orchestration
**Priority:** P3
**Dependencies:** F017
**Status:** [x] Done
**User Story:** As a platform team, Dokima manages features across a monorepo with cross-cutting specs, shared ADRs, and parallel pipelines per sub-project.

### F028: Strategist enriches codebase-map.md during normal feature planning — appends architecture decisions and agent guidance discovered during exploration. Map accumulates real-world rationale across features with zero extra LLM calls.
**Priority:** P3
**Dependencies:** F027
**Status:** [x] Done
**User Story:** As a user, I can strategist enriches codebase-map.md during normal feature planning — appends architecture decisions and agent guidance discovered during exploration. map accumulates real-world rationale across features with zero extra llm calls.


### F035: GitLab support: swap gh CLI for glab or abstract VCS layer
**Priority:** P3
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a user, I can gitlab support: swap gh cli for glab or abstract vcs layer.

### F039: Real-code verification in vet phase — after tests pass, verify that functions referenced in tests actually exist in source modules. Mock-based tests (autospec=True, create=True) can pass even when the real implementation is missing (F032, F033, F034, F038 all shipped with this bug). The vet phase should grep test files for function names and verify they're importable from the source modules. Blocks pipeline if tests pass but implementation is missing.
**Priority:** P0
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a developer, I trust that when tests pass and vet approves, the implementation actually exists. Mock-based passing tests that hide missing functions are caught and blocked before merge.


### F040: PipelineContext dataclass — replace 20+ module-level globals (PROJECT_DIR, REPO, DEFAULT_BRANCH, etc.) with a single PipelineContext dataclass passed to each phase function. Eliminates conftest __setattr__ override hack. Makes testing trivial — create a context, pass it in. All 1,029 tests protect this refactor.
**Priority:** P1
**Dependencies:** None
**Status:** [~] In Progress Progress Progress Progress Progress Progress
**User Story:** As a contributor, I can write a test by creating a PipelineContext instead of monkey-patching 20+ module globals through conftest.

### F041: Split utils.py into domain modules — git_ops.py (git, gh wrappers), spec_extract.py (extract_pr_sections, extract_issue_sections, clean_spec_content), codebase_map.py (generate_codebase_map, _build_domain_map, _build_impact_map), control_panel.py (handle_status, handle_stop, handle_kill). 3,351 lines → ~4 × 800-line modules.
**Priority:** P1
**Dependencies:** F040
**Status:** [x] Done Progress
**User Story:** As a contributor, I open the right module for the task instead of scrolling past 83 functions in one file.

### F042: CI pipeline — add .github/workflows/test.yml running pytest on push/PR. Add complexity gates (max CC=30), lint (pyflakes), and type checking (mypy --strict for new modules).
**Priority:** P1
**Dependencies:** None
**Status:** [~] In Progress
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a contributor, tests run automatically on every push and PR — no manual python3 -m pytest needed.

### F043: Phase function decomposition — split run_phase1_strategist (656 lines, CC=125), run_phase2_coder (277, CC=77), run_pipeline (280, CC=79), run_fix_mode (281, CC=67), run_init (455, CC=60) into sub-operations. Target: max 150 lines, CC < 30 per function.
**Priority:** P2
**Dependencies:** F040
**Status:** [x] Done
**User Story:** As a contributor, I can understand and modify a phase function without tracing 125 branching paths.

### F044: PR body quality — `extract_pr_sections()` currently dumps the strategist's full spec into Why/Impact instead of extracting concise summaries. Fix: trim Why to first 2 sentences (max 200 chars), Impact to product-value-only (strip meta-commentary and internal thinking), strip nm Review of shell commands and reasoning noise.
**Priority:** P1
**Dependencies:** F038
**Status:** [~] In Progress
**User Story:** As a reviewer, I open a PR and immediately understand what changed and why — no walls of strategist text, no shell commands in review sections.

### F045: Roadmap auto-update verification — `commit_roadmap_update()` marks features Done without verifying implementation exists. When a pipeline merges, it updates ALL feature statuses in roadmap.md — including unrelated ones. Fix: only update the specific feature that was built, and verify source changes exist before marking Done.
**Priority:** P1
**Dependencies:** F039
**Status:** [~] In Progress
**User Story:** As a developer, I trust that [x] Done in the roadmap means the feature was actually implemented — not that an unrelated merge touched the file.

### F046: Fix mode branch isolation — `dokima fix --issue` coder commits directly to main instead of the fix branch. The coder prompt says "switch to branch fix/issue-N" but the coder ignores it or the pipeline doesn't enforce it. Fix: verify coder is on the correct branch before vet phase, or make the branch checkout mandatory in the prompt.
**Priority:** P1
**Dependencies:** None
**Status:** [~] In Progress
**User Story:** As a developer, `dokima fix --issue N` creates a proper fix branch with isolated changes, never commits to main directly.
