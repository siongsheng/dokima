# .

Now I understand. The existing spec at specs/-spec.md is the project overview ("Feature: .") and needs these corrections:
    
    1. Impact and What Changed section headers need ## markdown prefix so the panel parser recognizes them
    2. Task format needs ### Task N: h3 headers with the exact 5-field template the panel regex expects: ### Task N:, Files:, Dependencies:, Parallelizable:, Description:
    
    Here is the COMPLETE corrected spec:
    
    
    
    . — Dokima Project Overview Spec
    
    Status: Active (living document)
    Confidence: High
    Version: 2.1 (2026-06-29 — verified vs codebase: 5378 lines, 488 tests, branch feat/f006-error-recovery--resume)
    
    Executive Summary
    
    Dokima is a lightweight (~5400-line), zero-dependency Python script that routes feature development through a pipeline of specialist AI agents — enforcing TDD, adversarial review, and depth-gated execution. It spawns Hermes Agent subprocesses with role-specific profiles and skills, parses their output for spec compliance, and auto-remediates common failures. The project is self-hosting: Dokima builds Dokima. 488 tests verify the pipeline end-to-end. F006 (Error Recovery & Resume) is currently in progress on branch feat/f006-error-recovery--resume.
    
    Constitution Check
    
    Axiom: Solves the developer's own pain?
    Verdict: YES
    Evidence: Shaun runs this on dokima itself — the panel builds the panel.
      Every feature since F001 was built via dokima.
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Verdict: YES (core)
    Evidence: Single Python file, zero pip dependencies, runs on Oracle Linux
      8 system Python 3.6+.
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Verdict: N/A
    Evidence: Internal tool — not a SaaS. Value is time saved per feature
      cycle (strategist → coder → vet → nm → TL takes minutes, not hours).
    ────────────────────────────────────────
    Axiom: Boring/Proven tech stack?
    Verdict: YES
    Evidence: Python 3.6+ stdlib, bash subprocesses, Hermes Agent CLI — no
      frameworks, no ORM, no build step.
    ────────────────────────────────────────
    Axiom: Avoids AI hype?
    Verdict: YES
    Evidence: Dokima is the orchestration layer, not an "AI-powered platform."
      It shells out to existing AI agents; it doesn't reinvent them.
    
    Verdict: All axioms pass. Proceed.
    
    Mission
    
    A lightweight, stateless Python script that routes feature development through a pipeline of specialist AI agents — enforcing TDD, adversarial review, and depth-gated execution — while requiring zero non-Python dependencies beyond the agents and tools it orchestrates.
    
    Tech Stack
    
    - Runtime: Python 3.6+ (single file, ~5400 lines, no pip dependencies, compatible with Oracle Linux 8 system Python)
    - Orchestration: Hermes Agent (hermes --profile <role> --yolo -s <skill>)
    - Version control: Git + GitHub CLI (gh) for branch management and PR creation
    - Verification: Shell scripts (~/bin/vet, ~/bin/nm) for deterministic build/test/adversarial review
    - ADRs: adr-tools CLI for architectural decision records (optional — not yet adopted in this repo)
    - Agent provider: DeepSeek (primary), OpenRouter (fallback), Google (nm fallback)
    - Test framework: pytest (488 tests collected)
    
    Pipeline Stages
    
    #: 0
    Stage: Human Gate
    Agent: User
    What it produces: Spec approval before code
    ────────────────────────────────────────
    #: 1
    Stage: Strategist
    Agent: strategist profile
    What it produces: Spec + task list + decision table
    ────────────────────────────────────────
    #: 1b
    Stage: TL Spec Pre-Review
    Agent: tech-lead profile
    What it produces: Architecture + test plan review
    ────────────────────────────────────────
    #: 2
    Stage: Coder
    Agent: coder profile
    What it produces: RED→GREEN commits on feature branch
    ────────────────────────────────────────
    #: 3
    Stage: vet
    Agent: Shell (zero AI)
    What it produces: Build + test verification, PR at depth=vet
    ────────────────────────────────────────
    #: 4
    Stage: nm
    Agent: ~/bin/nm
    What it produces: Adversarial review + PR with risk assessment
    ────────────────────────────────────────
    #: 5
    Stage: Tech Lead
    Agent: tech-lead profile
    What it produces: Spec compliance + code quality verdict
    
    Feature Set
    
    Core Pipeline
    - [x] Depth-gated execution (vet / vet+nm / full) based on confidence × impact
    - [x] Human gate with spec review (interactive: less/vim; non-interactive: auto-skip)
    - [x] Strategist codebase exploration → spec generation → interview mode (exit code 2)
    - [x] TDD-enforced coder (RED→GREEN two-commit discipline)
    - [x] Shell-based verification (vet) with coder fix loopback (up to 2 retries)
    - [x] Adversarial review (nm) with risk assessment and PR creation
    - [x] Tech Lead spec-compliance and architecture review
    - [x] Filtered auto-fix loopbacks (nm→coder, TL→coder) for objective issues only
    - [x] Pipeline halt + revert on unrecoverable failures
    - [x] Full output log to /tmp/dokima-output.txt
    
    Parallel Execution
    - [x] DAG-based task scheduling with dependency resolution
    - [x] Parallel coder worktrees (up to 5 via git worktree)
    - [x] Task claiming with file-collision detection
    - [x] Sequential fallback via PANEL_PARALLEL=0
    
    Cost Optimizations
    - [x] Spec noise extraction (strip tool calls + prompt echo from agent output: 45-58% smaller)
    - [x] Task-extract for coder (~800 chars instead of ~12K full spec)
    - [x] Flash model (deepseek-v4-flash) for coder phase
    - [x] Pure shell verification (zero AI tokens)
    - [x] Lite skills (2.2K vs 13.8K system tokens)
    
    ADR Lifecycle
    - [x] Strategist reads existing ADRs before designing
    - [x] Panel creates new ADR from decision table after Human Gate
    - [x] TL pre-review checks spec against existing ADRs
    - [x] Spec↔ADR cross-references
    
    Spec Archive
    - [x] Auto-archive merged PR specs on startup
    - [x] specs/STATUS.md regeneration
    - [x] Manual archive support
    
    Continuous Mode
    - [x] --next builds next feature from roadmap
    - [x] --continuous loop with auto-merge when safe
    - [x] --status / --stop / --kill control
    - [x] Cron integration with --list-crons
    
    Error Recovery (IN PROGRESS — F006)
    - [~] --resume / --no-resume flags added (2026-06-28)
    - [~] Checkpoint JSON at /tmp/dokima-<slug>-checkpoint.json
    - [~] Phase-level granularity — resume at phase boundary, never mid-task
    - [~] Stale checkpoint detection via branch + spec file existence validation
    
    Model Family Fallback (DONE — F005)
    - [x] Primary model provider down → auto-fallback to configured alternative
    - [x] Cross-family adversarial review (coder ≠ nm model family)
    
    Quality Gates (DONE — F004)
    - [x] Spec structure validation (all 17 sections present)
    - [x] Task format validation (### Task N: headers with 5 fields)
    - [x] DAG re-prompt on malformed task output
    - [x] PR body validation (real Impact/What Changed, no placeholders)
    
    Execution Mode Selection (DONE — F019)
    - [x] Auto-selects batch coder (single session) for small additive features
    - [x] Auto-selects per-task spawn for complex/refactor features
    - [x] Derived from DAG signals: task count, file count, parallelizability
    
    Impact
    
    What changes for the developer adopting Dokima:
    
    Dimension: Spec quality
    Before: Varies by developer discipline
    After: Enforced by strategist DAG format + TL review
    ────────────────────────────────────────
    Dimension: Test discipline
    Before: Optional, often skipped
    After: Mandatory — TDD enforced (RED→GREEN, two-commit)
    ────────────────────────────────────────
    Dimension: Code review depth
    Before: Same-team blind spots
    After: Cross-family adversarial review (different model family)
    ────────────────────────────────────────
    Dimension: Pipeline speed
    Before: Hours (manual review cycles)
    After: Minutes (5-phase automated pipeline)
    ────────────────────────────────────────
    Dimension: Failure recovery
    Before: Manual restart
    After: --resume from last checkpoint (F006)
    ────────────────────────────────────────
    Dimension: Cost
    Before: Full AI tokens for every phase
    After: ~87% token reduction via spec noise extraction + flash coder
    ────────────────────────────────────────
    Dimension: Consistency
    Before: Developer-dependent
    After: Deterministic quality gates enforceable by CI
    
    Operator-facing impact: A single dokima <feature-description> invocation runs 5 phases across 3+ AI agents with zero manual intervention. Failures surface as structured verdicts (BLOCKED/APPROVED) with auto-fix loopbacks where appropriate.
    
    What Changed
    
    Since last spec revision (2026-06-28):
    
    - dokima (+223/-34): F006 resume/checkpoint logic — commits 87b2b81, 725cd00, 1580250. PR in progress.
    - dokima: F006 resume flag and help text — commit 87b2b81. PR in progress.
    - tests/test_f006_recovery.py (+304): F006 checkpoint helper tests — commit a87c806. PR in progress.
    - dokima: F005 Model Family Fallback — commit 674da2d. PR #17.
    - dokima: TL extraction fix (blocker filter) — commit 2e7f6b8. N/A.
    - dokima: compute_execution_mode fix — commits 0da89a9, 92b8d99. N/A.
    - specs/roadmap.md: F020 + F021 roadmap entries — commits f543cb0, 23622d4. N/A.
    - tests/: Test suite growth — 488 tests (was 196).
    
    Key architectural decisions made:
    1. Checkpoint state stored in separate JSON file (not embedded in lock file) — avoids lock contention on reads
    2. Phase-level resume granularity — never resume mid-task (simpler, more predictable)
    3. Stale checkpoint detection via git branch + spec file existence check — no TTL-based expiry
    
    Feature Breakdown
    
    Task 1: Human Gate — Spec Approval
    Files: No code changes — user reviews spec in less/vim
    Dependencies: [none]
    Parallelizable: no
    Description: User reviews the generated spec before code is written. In non-interactive mode (CI/cron), auto-skips. In interactive mode, opens spec in configured editor. Exit code signals: 0 = approved, 1 = rejected (pipeline halts), 2 = interview mode (strategist re-runs with clarifications).
    
    Task 2: Strategist — Spec Generation
    Files: dokima (spawn_agent + spec parser), specs/<feature>-spec.md, specs/<feature>-tasks.md
    Dependencies: [none]
    Parallelizable: no
    Description: Spawns hermes --profile strategist --yolo -s spec-strategist-lite chat -q "<feature>". Parses output for ### Task N: headers, DAG dependencies, and quality gate compliance. If DAG format invalid, fires re-prompt (up to 1 retry). Extracts task list to <feature>-tasks.md for coder consumption (~800 chars).
    
    Task 3: TL Spec Pre-Review — Architecture + Test Plan Review
    Files: dokima (TL spawn, verdict extraction)
    Dependencies: [Task 2]
    Parallelizable: no
    Description: Spawns tech-lead agent with the generated spec before any code is written. Checks architectural impact, test plan completeness, and ADR compliance. Catches over-engineering and missing edge cases BEFORE the coder commits. BLOCKED verdict returns to strategist for refinement.
    
    Task 4: Coder — RED→GREEN Implementation
    Files: dokima (spawn_agent_with_fallback, TDD enforcement, worktree management), feature branch files
    Dependencies: [Task 3]
    Parallelizable: no
    Description: For each unblocked task in the DAG: creates git worktree, spawns coder agent with task-extract prompt, enforces RED commit (failing test) before GREEN commit (passing implementation). Monitors for timeout (15 min default). Merges worktrees back on success. Max 2 retries per task on failure. Flash model (deepseek-v4-flash) for token efficiency. Individual tasks within this phase are parallelizable (up to 5 worktrees via DAG scheduling).
    
    Task 5: vet — Build + Test Verification
    Files: ~/bin/vet, dokima (vet spawn, retry loop)
    Dependencies: [Task 4]
    Parallelizable: no
    Description: Shell script verification — zero AI tokens. Runs python3 -m py_compile dokima, python3 -m pytest tests/ -q. If any test fails, triggers coder fix loopback (Task 4 re-run, max 2 retries). At depth=vet, creates PR and exits. At depth=full, proceeds to nm.
    
    Task 6: nm — Adversarial Review
    Files: ~/bin/nm, dokima (nm spawn, PR creation)
    Dependencies: [Task 5]
    Parallelizable: no
    Description: Spawns adversarial reviewer using a different model family than the coder (e.g., coder=DeepSeek, nm=Qwen via OpenRouter). Reviews the diff for: logic errors, missing edge cases, security issues, spec non-compliance. Produces risk assessment (LOW/MEDIUM/HIGH/CRITICAL). Creates PR with review summary. Auto-fix loopback to coder for objective issues (not subjective style feedback).
    
    Task 7: Tech Lead — Spec Compliance + Quality Verdict
    Files: dokima (verdict extraction, blocker parser, status update)
    Dependencies: [Task 6]
    Parallelizable: no
    Description: Spawns tech-lead agent with full spec + PR diff. Extracts structured verdict (APPROVED/BLOCKED/APPROVED_WITH_SUGGESTIONS). Parses blockers into actionable items. BLOCKED verdicts with objective issues trigger auto-fix loopback to coder (max 2 retries). Final verdict logged to /tmp/dokima-output.txt. On APPROVED: archives spec, updates STATUS.md, marks feature done.
    
    Data Model
    
    Runtime State (transient — filesystem-backed)
    
    Entity: Pipeline lock
    Location: /tmp/dokima-<project>.lock
    Format: Plain file (PID inside)
    Persists?: Until pipeline exit
    ────────────────────────────────────────
    Entity: Checkpoint
    Location: /tmp/dokima-<slug>-checkpoint.json
    Format: JSON
    Persists?: Until completion or --no-resume
    ────────────────────────────────────────
    Entity: Interview answers
    Location: /tmp/dokima-<slug>-interview.json
    Format: JSON
    Persists?: Until spec generated
    ────────────────────────────────────────
    Entity: Output log
    Location: /tmp/dokima-output.txt
    Format: Plain text
    Persists?: Append-only, session-scoped
    ────────────────────────────────────────
    Entity: Stop signal
    Location: /tmp/dokima-<project>.stop
    Format: Empty file
    Persists?: Until pipeline exit
    
    Persistent State
    
    Entity: Spec
    Location: specs/<feature>-spec.md
    Format: Markdown
    Persists?: Permanent (archived post-merge)
    ────────────────────────────────────────
    Entity: Task extract
    Location: specs/<feature>-tasks.md
    Format: Markdown
    Persists?: Until PR merged
    ────────────────────────────────────────
    Entity: ADR
    Location: docs/adr/<NNNN>-<title>.md
    Format: Markdown
    Persists?: Permanent
    ────────────────────────────────────────
    Entity: PR
    Location: GitHub (via gh pr create)
    Format: Git remote
    Persists?: Permanent
    ────────────────────────────────────────
    Entity: Feature branch
    Location: feat/<feature-slug>
    Format: Git branch
    Persists?: Until merged or cleaned
    
    In-Memory State (not persisted)
    - DAG: parsed task dependencies (dict {task_id: [dep_ids]})
    - Execution mode: per_task_spawn or single_session (derived from DAG signals)
    - Phase tracking: current phase number, retry count per phase
    
    API Routes
    
    Dokima has no network API. All interaction is CLI:
    
    
    dokima <feature-description>              # Full pipeline
    dokima --depth=vet <feature-description>  # Strategist + Coder + vet only
    dokima --depth=full <feature-description> # All 5 phases
    dokima --next                             # Next feature from roadmap
    dokima --continuous                       # Loop through roadmap
    dokima --status                           # Show current pipeline state
    dokima --stop / --kill                    # Signal pipeline
    dokima --resume / --no-resume             # Resume control (F006)
    dokima --list-crons                       # Show cron jobs
    dokima archive <feature>                  # Manual spec archive
    
    
    Environment variables (no CLI flags for secrets):
    - GH_TOKEN — GitHub CLI auth (redacted in logs)
    - PANEL_PARALLEL=0 — force sequential execution
    - PANEL_DEBUG=1 — verbose output
    
    Component Tree
    
    N/A — Dokima is a CLI orchestration script, not a web application. No UI components, no pages, no layouts. The pipeline runs as a single Python process spawning subprocesses.
    
    COTS Build-vs-Buy
    
    Component: AI agent runtime
    Buy/COTS: Hermes Agent (COTS)
    Justification: Battle-tested agent CLI. Building our own agent runtime is
      out of scope.
    ────────────────────────────────────────
    Component: Git hosting
    Buy/COTS: GitHub (COTS)
    Justification: Standard. Self-hosting GitLab adds zero value for this
      tool.
    ────────────────────────────────────────
    Component: Shell verification
    Buy/COTS: Built (vet script)
    Justification: Must be deterministic — no AI tokens, no hallucination
      surface. No COTS equivalent exists.
    ────────────────────────────────────────
    Component: Adversarial review
    Buy/COTS: Built (nm script)
    Justification: Cross-family model review is the key innovation. No COTS
      product does this.
    ────────────────────────────────────────
    Component: Spec format
    Buy/COTS: Built (spec-strategist-lite skill)
    Justification: Proprietary DAG format. Must integrate with panel parsing.
    ────────────────────────────────────────
    Component: ADR tooling
    Buy/COTS: adr-tools (COTS, MIT)
    Justification: Standard CLI for architectural decision records.
      Well-maintained, zero integration cost.
    ────────────────────────────────────────
    Component: Test framework
    Buy/COTS: pytest (COTS, MIT)
    Justification: Industry standard. 488 tests already depend on it.
    
    Test Plan
    
    Happy Path
    - Full pipeline: dokima "add a --version flag" → strategist produces DAG spec → coder implements with RED/GREEN commits → vet passes build+tests → nm reviews and creates PR → TL approves with APPROVED verdict.
    - Depth=vet: Pipeline exits after vet phase with PR created. nm and TL not invoked.
    - Parallel execution: Feature with 5 parallelizable tasks spawns 5 worktrees simultaneously. All complete and merge cleanly.
    - Resume (F006): Pipeline killed at phase 3. dokima --resume restarts from phase 3 checkpoint, skips phases 0-2.
    
    Edge Cases
    - Empty feature description: Strategist enters interview mode (exit code 2) — not a crash.
    - Feature description with special characters: dokima "fix 'quoted' & special / chars" → slugify produces safe branch name, no shell injection.
    - Zero parallelizable tasks: All tasks depend on previous → falls back to sequential single-session execution.
    - Coder produces only RED commit (no GREEN): vet catches it (tests still failing after "implementation"). Triggers coder retry loop.
    - Strategist output with 0 ### Task headers: DAG re-prompt fires. After retry exhaustion, pipeline halts with clear error.
    - Concurrent pipelines on same project: Lock file at /tmp/dokima-<project>.lock blocks the second invocation.
    - Stale checkpoint: Branch deleted but checkpoint exists → --resume detects missing branch, starts fresh.
    
    Failure Modes
    - Model provider down: hermes call fails with auth/network error. F005 fallback chain activates. If all providers fail, pipeline halts with "all providers exhausted" error.
    - Coder timeout (15 min): Worktree cleaned up, retry scheduled. After 2 retries, task marked failed, pipeline halts.
    - vet build failure: python3 -m py_compile dokima fails → coder fix loop triggered. After 2 retries, pipeline halts.
    - nm model unavailable: Falls back to configured nm fallback provider (must be different model family from coder).
    - Disk full during log write: /tmp exhaustion → pipeline halts with clear error (not silent data loss).
    - GitHub CLI not authenticated: gh pr create fails → pipeline halts at PR creation phase with actionable error message.
    
    Contract Invariants
    - Before pipeline: Working directory is clean (no uncommitted changes on feature branch, if resuming).
    - After strategist phase: specs/<feature>-spec.md exists with valid ### Task N: headers. specs/<feature>-tasks.md exists with extracted task list.
    - After coder phase: Feature branch has RED commit before GREEN commit. All tests pass (pytest -q exit 0).
    - After nm phase: PR exists on GitHub. nm verdict (LOW/MEDIUM/HIGH/CRITICAL risk) is recorded.
    - After TL phase: Final verdict (APPROVED/BLOCKED/APPROVED_WITH_SUGGESTIONS) is logged. On APPROVED: spec archived to specs/archive/, STATUS.md updated.
    - On pipeline halt: All worktrees cleaned up. Lock file removed. Partial state preserved in checkpoint (if F006 enabled).
    - Security invariant: No secret value appears verbatim in /tmp/dokima-output.txt — verified by grep for configured secret patterns.
    
    Panel Split
    
    All 7 tasks are sequential (pipeline phases must run in order). No task-level parallelism at this level — parallelism exists WITHIN Task 4 (Coder phase) where individual DAG tasks fan out across up to 5 parallel worktrees. Recommended: 1 coder agent for sequential phases, with up to 5 parallel sub-coders during the implementation phase.
    
    Build & Deploy
    
    - CI: python3 -m py_compile dokima && python3 -m pytest tests/ -q
    - Deploy: ln -sf ~/dokima/dokima ~/bin/dokima (symlink to PATH)
    - No build step: Single Python file, no compilation, no bundling
    - Env vars needed: GH_TOKEN for GitHub CLI; per-profile Hermes Agent config for model providers
    - Companion scripts: ~/bin/nm, ~/bin/vet must be present on PATH
    
    Risk Register
    
    #: R1
    Risk: Model provider outage mid-pipeline
    Severity: HIGH
    Mitigation: F005 fallback chain (deepseek→openrouter→anthropic). Pipeline
      halts with clear error if all providers down.
    Trigger: hermes exits non-zero with auth/network error
    ────────────────────────────────────────
    #: R2
    Risk: Coder produces plausible but wrong code
    Severity: MEDIUM
    Mitigation: vet phase catches build/test failures. nm adversarial review
      catches logic errors via cross-family review.
    Trigger: vet test failures or nm BLOCKED verdict
    ────────────────────────────────────────
    #: R3
    Risk: git worktree leak on crash
    Severity: MEDIUM
    Mitigation: Signal handler (SIGTERM/SIGINT) cleans worktrees. --resume
      (F006) detects stale worktrees.
    Trigger: Pipeline killed mid-phase without cleanup
    ────────────────────────────────────────
    #: R4
    Risk: Spec noise extraction strips real content
    Severity: LOW
    Mitigation: Parser validates task count post-extraction. If 0 tasks found,
      uses raw output.
    Trigger: DAG parse returns 0 tasks
    ────────────────────────────────────────
    #: R5
    Risk: Parallel coders conflict on same file
    Severity: LOW
    Mitigation: Task claiming system with file path hashing prevents overlaps.
      Sequential fallback via PANEL_PARALLEL=0.
    Trigger: Two tasks claim overlapping file sets
    ────────────────────────────────────────
    #: R6
    Risk: Checkpoint corruption (F006)
    Severity: LOW
    Mitigation: JSON parse with validation. Corrupt checkpoint → clean start
      (same as --no-resume).
    Trigger: json.load() raises on checkpoint file
    ────────────────────────────────────────
    #: R7
    Risk: Prompt injection through feature description
    Severity: MEDIUM
    Mitigation: _sanitize_prompt() strips backtick commands, code blocks,
      SYSTEM:/OVERRIDE: prefixes. Logs WARNING to stderr.
    Trigger: Feature description contains shell metacharacters or
      prompt-injection patterns
    ────────────────────────────────────────
    #: R8
    Risk: Token leak through output log
    Severity: HIGH
    Mitigation: _redact_secrets() replaces
      GH_TOKEN/GITHUB_TOKEN/API_SERVER_KEY values with [REDACTED] before log
      output. Strict umask (0o077) on all /tmp/dokima-* files.
    Trigger: Log file written before redaction applied
    
    Anti-Creep — Explicitly Out of Scope
    
    1. No web UI / dashboard — Dokima is CLI-only. No Flask, no FastAPI, no React admin panel.
    2. No persistent database — State is filesystem-only (JSON files, git branches). No SQLite, no Redis, no Postgres.
    3. No multi-user auth — Single-operator tool. No login, no RBAC, no teams.
    4. No plugin system — Pipeline stages are fixed. No dynamic agent registration, no hook points.
    5. No non-Git VCS — Git only. No Mercurial, no SVN, no Perforce.
    6. No hosted SaaS — Dokima runs locally. Dokima-as-Service (F017) is Phase 3 Icebox, not current scope.
    7. No code generation beyond the feature branch — Dokima doesn't manage releases, changelogs (F021 pending), or deployment.
    8. No real-time monitoring — Pipeline runs to completion. No websockets, no progress bar API, no streaming status.
    
    Key Files
    
    | File             | Purpose                                            |
    |------------------|----------------------------------------------------|
    | dokima           | Main script (single file, 5378 lines)              |
    | ~/bin/nm         | Adversarial review companion script                |
    | ~/bin/vet        | Shell verification companion script                |
    | docs/pipeline.md | Full pipeline reference                            |
    | docs/setup.md    | Deployment guide                                   |
    | specs/           | Generated specs per feature                        |
    | tests/           | 488 pytest tests (unit + integration + edge cases) |
    
    Conventions
    
    - No hardcoded 'master' branch — detected from origin/HEAD
    - No hardcoded model names in documentation — provider-agnostic
    - State is in the filesystem (specs, branches, worktrees, log files) — not in memory
    - Single-entry-point design: all orchestration flows through dokima
    - All subprocess calls use list-based args (no shell=True, no os.system())
    - All /tmp/dokima-* files created with umask 0o077 + explicit chmod 0o600
    - Secrets (GH_TOKEN, GITHUB_TOKEN, API_SERVER_KEY) redacted from all log output
    - Feature descriptions sanitized for shell metacharacters and prompt injection before entering agent prompts
    - Cross-family adversarial review: nm model family ≠ coder model family
    
    Sign-Off Checklist
    
    - [ ] Pipeline stages documented and match dokima implementation
    - [ ] Feature Set checkboxes match current STATUS.md (F001 done, F002 done, F003 done, F004 done, F005 done, F006 in progress, F019 done)
    - [ ] Task N: headers exist for all 7 pipeline stages with Files, Dependencies, Parallelizable, Description fields
    - [ ] Impact section describes operator-facing changes (7 dimensions, before/after table)
    - [ ] What Changed section matches git log --oneline -10 (verified 2026-06-29: 5378 lines, 488 tests)
    - [ ] Risk register covers model outage, worktree leaks, token leaks, prompt injection (8 risks)
    - [ ] Anti-Creep explicitly excludes: web UI, persistent DB, multi-user auth, plugins, non-Git VCS, SaaS, code generation beyond branches, real-time monitoring
    - [ ] Test plan covers: happy path (4 scenarios), edge cases (7 items), failure modes (6 items), contract invariants (8 items)
    - [ ] Data model documents all 5 transient + 4 persistent entities
    - [ ] Constitution check passes all 5 axioms
    - [ ] Test count verified: 488 collected (not stale 196 from AGENTS.md)
    - [ ] F006 status reflects current branch feat/f006-error-recovery--resume