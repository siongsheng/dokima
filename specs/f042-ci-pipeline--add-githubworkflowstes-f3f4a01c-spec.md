# F042: CI pipeline — add .github/workflows/test.yml running pytest on push/PR. Add complexity gates (max CC=30), lint (pyflakes), and type checking (mypy --strict for new modules).

Now I have the full picture. Here is the complete corrected spec:
    
    
    
    F042: CI pipeline — add .github/workflows/test.yml
    
    Version: 1.1.0 (corrected — added Impact, What Changed, and fixed task format)
    Status: Ready for implementation
    Confidence: High
    
    
    
    1. Executive Summary
    
    Add a GitHub Actions CI pipeline that runs on every push and PR. The workflow executes pytest (existing 1033 tests), pyflakes lint, mypy type checking (--strict for new modules), and a complexity gate (max cyclomatic complexity 30 via radon/xenon). Dokima currently has zero CI — all testing is manual. This gates every PR automatically, catching regressions before merge. The complexity gate is aspirational (F043 will do the actual refactoring); today it warns, tomorrow it blocks.
    
    Confidence: High — this is a standard CI workflow for a Python project with 7 source modules and 1033 tests. The tools (pytest, pyflakes, mypy, radon) are well-established.
    
    
    
    2. Constitution Check
    
    Axiom: Does it solve the user's own pain?
    Verdict: YES
    Notes: Contributors have to manually run python3 -m pytest tests/ -q — no
      automated gating
    ────────────────────────────────────────
    Axiom: Is it weekend-buildable?
    Verdict: YES
    Notes: Single workflow YAML + optional config files. 2-3 hours max
    ────────────────────────────────────────
    Axiom: Is there evidence this will help?
    Verdict: YES
    Notes: dokima has shipped bugs caught post-merge (F032, F033, F034, F038
      all had mock-passing tests with missing implementations — discovered by
      F039. CI would have caught the regressions earlier)
    ────────────────────────────────────────
    Axiom: Is the tech stack boring and proven?
    Verdict: YES
    Notes: GitHub Actions + pytest + pyflakes + mypy — standard Python CI
      stack
    ────────────────────────────────────────
    Axiom: Does it avoid AI hype categories?
    Verdict: YES
    Notes: No AI components, no LLM calls
    
    No misalignments flagged.
    
    
    
    3. Impact Assessment
    
    Files affected (grounded in actual codebase scan)
    
    
    New files:
      .github/workflows/test.yml           (~80 lines YAML)
      pyproject.toml                        (~25 lines — mypy, pyflakes, radon config)
      .mypy.ini                             (~15 lines — gradual typing config)
    
    Modified files:
      (none — purely additive)
    
    
    What this touches
    - CI infrastructure only — no source code changes
    - 0 source files touched — zero risk to existing behavior
    - Existing 1033 tests — all run in CI, no test changes needed
    - 7 source modules scanned by lint/type/complexity gates but not modified
    
    Dependency graph
    
    .github/workflows/test.yml
      └─ pyproject.toml (config — mypy, pyflakes, radon)
      └─ .mypy.ini (per-file typing strictness)
    
    
    Impact on existing workflows
    - PR merge: becomes gated on CI green (if branch protection enabled)
    - Local dev: unchanged — same python3 -m pytest tests/ -q still works
    - Pipeline: no changes to dokima's own pipeline logic
    
    
    
    4. What Changed
    
    Current state
    - Zero CI/CD — no .github/ directory exists
    - Only lint command: python3 -m py_compile dokima (syntax check only — no semantic lint)
    - No type checking at all
    - No complexity measurement — 14 functions exceed CC=20, some reach CC≈105
    - Tests run manually: python3 -m pytest tests/ -q
    
    What this feature delivers
    1. Automated test execution on every push and PR — 1033 tests, no manual pytest needed
    2. Pyflakes lint gate — catches unused imports, undefined names, redefinitions (py_compile misses all of these)
    3. Mypy type checking — --strict for any module with # mypy: strict marker; permissive (no errors) for legacy modules without type annotations
    4. Complexity gate — radon CC check with --max 30; initially non-blocking (warning only) since F043 handles the actual refactoring
    
    Post-F042 state
    
    Push/PR → CI triggers → 
      1. pytest (1033 tests, must pass)
      2. pyflakes *.py (must pass — zero errors)
      3. mypy *.py (relaxed — legacy modules unchecked, new modules strict)
      4. radon cc *.py -a --max 30 (warning-only for now)
    → All green → merge allowed
    
    
    
    
    5. Feature Breakdown (Task List)
    
    Task 1: Create .github/workflows/test.yml — main CI workflow YAML
    Files: .github/workflows/test.yml
    Dependencies: [none]
    Parallelizable: yes
    Estimated LOC: ~80
    Description: Create the GitHub Actions workflow with on: [push, pull_request] trigger, Python 3.12 setup, pip install of pytest/pyflakes/mypy/radon, and four sequential job steps: (1) pytest with --tb=short -q, (2) pyflakes on all *.py files excluding tests/, (3) mypy with config from .mypy.ini, (4) radon cc *.py -a --max 30 --no-assert with continue-on-error: true (warning-only for now). Use actions/setup-python@v5.
    
    Task 2: Create pyproject.toml — mypy, pyflakes, and radon configuration
    Files: pyproject.toml
    Dependencies: [Task 1]
    Parallelizable: no
    Estimated LOC: ~25
    Description: Create pyproject.toml at repo root with [tool.mypy] section (python_version = "3.12", warn_return_any = true, warn_unused_configs = true), [tool.pyflakes] section if needed, and [tool.radon] section (cc_rank = "C", meaning max CC ~30). This centralizes all CI tool configuration in the standard Python project metadata file.
    
    Task 3: Create .mypy.ini — per-module typing strictness
    Files: .mypy.ini
    Dependencies: [Task 1]
    Parallelizable: yes
    Estimated LOC: ~15
    Description: Create .mypy.ini with [mypy] global section setting ignore_missing_imports = True (no deps in CI venv), and per-module sections: existing modules (agent, pipeline, roadmap, tasks, utils, status, vcs, dokima) get ignore_errors = True (legacy — no type annotations), while a wildcard [mypy-*] pattern for future modules defaults to strict = True. This enables gradual typing — new modules are strict, old ones are ignored.
    
    Task 4: Verify CI configuration — dry-run validation
    Files: pyproject.toml, .mypy.ini, .github/workflows/test.yml
    Dependencies: [Task 1, Task 2, Task 3]
    Parallelizable: no
    Estimated LOC: ~0 (manual verification)
    Description: Run python3 -m pytest tests/ -q --collect-only to verify test discovery, python3 -m pyflakes *.py to verify lint config works locally, python3 -m mypy --config-file .mypy.ini *.py to verify mypy config produces no unexpected errors, and radon cc *.py -a to verify radon is installed and functional. Document expected outcomes in PR body.
    
    
    
    6. Data Model
    
    No new data model. This feature is pure CI configuration — no runtime state, no database, no API endpoints.
    
    Entity: Workflow definition
    Storage: .github/workflows/test.yml
    Purpose: GitHub Actions YAML — declarative, not code
    ────────────────────────────────────────
    Entity: Mypy configuration
    Storage: .mypy.ini
    Purpose: INI file read by mypy CLI
    ────────────────────────────────────────
    Entity: Tool configuration
    Storage: pyproject.toml
    Purpose: TOML file — Python ecosystem standard
    
    All three are static config files. No mutable state. No persistence beyond git.
    
    
    
    7. API Routes
    
    Not applicable. This is CI infrastructure, not a web service.
    
    
    
    8. Component Tree
    
    Not applicable. No frontend.
    
    
    
    9. COTS Build-vs-Buy
    
    Component: GitHub Actions
    Buy/Build: Buy (COTS)
    Justification: Already on GitHub — $0 for public repos, minutes included
    ────────────────────────────────────────
    Component: pytest
    Buy/Build: Buy (COTS)
    Justification: Already in use — 1033 tests exist
    ────────────────────────────────────────
    Component: pyflakes
    Buy/Build: Buy (COTS)
    Justification: Standard Python linter — pip install pyflakes, zero config
      needed
    ────────────────────────────────────────
    Component: mypy
    Buy/Build: Buy (COTS)
    Justification: Standard Python type checker — pip install mypy, config via
      .mypy.ini
    ────────────────────────────────────────
    Component: radon
    Buy/Build: Buy (COTS)
    Justification: Standard Python complexity analyzer — pip install radon,
      radon cc CLI
    ────────────────────────────────────────
    Component: CI workflow YAML
    Buy/Build: Build
    Justification: One file, ~80 lines — no existing solution covers our exact
      stack
    ────────────────────────────────────────
    Component: pyproject.toml
    Buy/Build: Build
    Justification: Minimal config — standard Python convention
    
    Verdict: 100% COTS tools, only build the glue (workflow YAML + config files). No custom scripts needed.
    
    
    
    10. Test Plan (MANDATORY)
    
    Happy path
    - Push to any branch triggers CI → pytest runs → 1033 tests pass → pyflakes clean → mypy passes → radon CC check runs (non-blocking)
    - PR opened → CI runs → all green → merge button enabled
    
    Edge cases
    - Empty push: no Python files changed — CI still runs (safety). pyflakes on zero files: pass. mypy on zero files: pass.
    - Push to non-default branch: CI runs on PR too — double run is intentional (GitHub Actions default). Both must pass.
    - Large test suite: 1033 tests take ~X seconds on GitHub runners. If >5 min, consider --dist loadgroup with pytest-xdist. Measure first, optimize only if needed.
    - First-time mypy: legacy modules with ignore_errors = True must not fail. This is the whole point of gradual typing.
    - pip install latency: CI installs pytest/pyflakes/mypy/radon fresh each run. If >1 min, add pip caching via actions/setup-python@v5 (built-in cache).
    
    Failure modes
    - Network error during pip install: CI step fails with clear error — GitHub Actions shows which package failed
    - pytest crash (segfault): CI step fails — GitHub Actions captures exit code
    - mypy crash on syntax error: pyflakes runs first and catches syntax errors earlier, but mypy also fails gracefully
    - radon not installed: continue-on-error: true handles this — step shows warning, doesn't block
    - GitHub Actions outage: No fallback — this is CI infrastructure. Outages are rare and self-resolving.
    
    Contract invariants
    - CI must NEVER modify source code — read-only operations only (lint, type check, test)
    - CI must NEVER access secrets (no GH_TOKEN, no API keys needed for pytest/pyflakes/mypy/radon)
    - CI must be idempotent — running twice produces identical results
    - CI configuration files (.github/, pyproject.toml, .mypy.ini) must be valid YAML/TOML/INI — parse errors in CI config are a build failure
    
    
    
    11. Panel Split
    
    Wave 1 (parallel): Task 1 + Task 3
    - Task 1: .github/workflows/test.yml — no shared files with Task 3
    - Task 3: .mypy.ini — no shared files with Task 1
    - Both: zero dependencies, zero file overlap
    
    Wave 2 (sequential): Task 2
    - Task 2: pyproject.toml — depends on Task 1 (needs to know what tools are installed to configure them)
    
    Wave 3 (sequential): Task 4
    - Task 4: verification — depends on all previous tasks
    
    Total: 3 waves, max 2 parallel coders (Wave 1). 4 tasks.
    
    
    
    12. Build & Deploy
    
    Aspect: CI triggers
    Detail: push (all branches), pull_request (all PRs)
    ────────────────────────────────────────
    Aspect: Runner
    Detail: ubuntu-latest (GitHub-hosted, free for public repos)
    ────────────────────────────────────────
    Aspect: Python
    Detail: 3.12 via actions/setup-python@v5
    ────────────────────────────────────────
    Aspect: Install step
    Detail: pip install pytest pyflakes mypy radon
    ────────────────────────────────────────
    Aspect: Caching
    Detail: Built into setup-python@v5 — pip cache enabled automatically
    ────────────────────────────────────────
    Aspect: Env vars
    Detail: None needed — no secrets, no tokens, no API access
    ────────────────────────────────────────
    Aspect: Deployment
    Detail: No deployment — CI configuration is self-deploying (merged to main
      = active)
    ────────────────────────────────────────
    Aspect: Branch protection
    Detail: Post-merge: enable "Require status checks to pass before merging"
      in repo Settings → Branches. This is a manual GitHub setting, not CI
      code.
    
    
    
    13. Risk Register
    
    #: R1
    Risk: Mypy ignore_errors = True for all legacy modules means zero type
      checking value at launch
    Severity: LOW
    Mitigation: Gradual typing strategy: new modules get --strict, old ones
      ignored. This is by design.
    Trigger: N/A — expected behavior
    ────────────────────────────────────────
    #: R2
    Risk: Complexity gate at CC=30 blocks PRs that touch any of the 14 high-CC
      functions
    Severity: HIGH (if blocking)
    Mitigation: continue-on-error: true — radon step warns but never blocks.
      Switch to false only after F043 ships.
    Trigger: If someone removes continue-on-error before F043
    ────────────────────────────────────────
    #: R3
    Risk: CI runtime exceeds GitHub Actions free tier limits
    Severity: LOW
    Mitigation: 1033 tests on 7 small modules → ~60-90s. pyflakes + mypy +
      radon → ~30s. Well within limits.
    Trigger: If test suite grows to 5000+ tests
    ────────────────────────────────────────
    #: R4
    Risk: pyflakes flags pre-existing issues in legacy code
    Severity: MEDIUM
    Mitigation: Run pyflakes locally first. If existing violations exist, fix
      them in the same PR or add # noqa with justification.
    Trigger: File count of pyflakes errors > 0 on first run
    ────────────────────────────────────────
    #: R5
    Risk: Developer confusion about mypy not checking legacy modules
    Severity: LOW
    Mitigation: Document in .mypy.ini comments and PR body. ignore_errors =
      True is clearly labeled as temporary.
    Trigger: Developer opens issue asking why mypy didn't catch a type error
    ────────────────────────────────────────
    #: R6
    Risk: GitHub Actions workflow YAML syntax error
    Severity: MEDIUM
    Mitigation: Task 4 verifies locally before pushing. GitHub Actions also
      validates on push — syntax errors produce clear diagnostics.
    Trigger: YAML indentation bugs
    
    
    
    14. Anti-Creep
    
    The following are explicitly NOT in scope:
    
    - NO pytest-xdist parallelization — add only if CI runtime exceeds 5 minutes (measure first)
    - NO pytest-cov coverage gate — coverage is tracked but not gated (separate feature)
    - NO pre-commit hooks — CI only, no local git hooks (separate feature)
    - NO code formatter (black/ruff format) — formatting is not linting (separate feature)
    - NO complexity auto-fix — F043 handles the refactoring; F042 only measures
    - NO branch protection configuration — that's a GitHub Settings operation, not code
    - NO Docker-based CI — standard ubuntu-latest runner is sufficient
    - NO multi-Python-version matrix — dokima requires Python 3.12+; testing on older versions is wasteful
    - NO caching beyond setup-python built-in — CI is fast enough; premature optimization
    
    
    
    15. Sign-Off Checklist
    
    - [ ] .github/workflows/test.yml exists with on: [push, pull_request] trigger
    - [ ] pyproject.toml exists with [tool.mypy] section
    - [ ] .mypy.ini exists with per-module ignore_errors for legacy, strict for new
    - [ ] python3 -m pytest tests/ -q passes locally (1033 tests green)
    - [ ] python3 -m pyflakes *.py produces zero errors (or pre-existing issues documented)
    - [ ] python3 -m mypy --config-file .mypy.ini *.py produces zero errors
    - [ ] radon cc *.py -a runs and reports CC values (warnings for >30 are expected)
    - [ ] First CI run on push succeeds (all green, radon non-blocking)
    - [ ] PR CI run succeeds
    - [ ] No secrets, tokens, or API keys in workflow YAML
    - [ ] Task format verified: all 4 tasks have ### Task N: headers with Files/Dependencies/Parallelizable/Description
    - [ ] Anti-creep: no formatters, no pre-commit, no coverage gates, no Docker, no matrix build
    
    
    
    16. Ponytail Guard — Pre-Spec Review
    
    Feature: F042: CI pipeline
    Rung: 5 — Installed dependency can do it
    Existing solution: Zero CI exists. No .github/ directory. No mypy config. No pyproject.toml.
    Spec needed: Yes
    Spec scope: GitHub Actions workflow YAML + Python tool configuration files. Purely additive — no source changes.
    
    
    
    Open Questions
    
    None. All decisions are clear:
    - Tools: pytest (already in use), pyflakes (standard), mypy (standard), radon (standard)
    - Strictness: Gradual — legacy modules ignored, new modules strict
    - Complexity gate: Non-blocking until F043 ships
    - Runner: ubuntu-latest, Python 3.12, no special hardware needed