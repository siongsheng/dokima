# Hermes Panel — Multi-Agent Orchestration Engine v1.5

`hermes-panel` routes feature development through a specialist panel of AI agents: **Strategist → Coder → vet → nm → Tech Lead**, with automated depth-gating, interview pause-and-resume, and parallel execution.

> **New here?** Start with [panel-setup.md](panel-setup.md) for deployment instructions.

---

## Quick Start

```bash
# Basic: run on any project with AGENTS.md + git remote
hermes-panel "Add rate limiting middleware" ~/atlas

# Force all 5 phases (even for low-risk changes)
PANEL_FORCE_FULL=1 hermes-panel "Add payment webhook handler" ~/atlas

# High-quality spec for complex features
PANEL_REASONING=high hermes-panel "Design OAuth2 integration" ~/atlas

# Resume after strategist interview
hermes-panel --answers /tmp/hermes-panel-interview.json "Add API key auth" ~/atlas
```

---

## Pipeline Phases

```
Strategist ──▶ Coder ──▶ vet ──▶ nm ──▶ Tech Lead
  v4-pro      v4-flash   shell   fresh    v4-pro
   58%          8%        0%      15%      19%
                          │       │
                          │       └─ different model family
                          └─ zero AI tokens
```

### Phase 1: Strategist (always runs)
Full Hermes session exploring the codebase. Reads `AGENTS.md`, searches for relevant code, understands existing patterns. Produces:
- Decision table comparing ≥2 approaches
- Impact assessment (files/tables/routes affected)
- Confidence + Impact markers (for depth gating)
- API/interface proposal
- Security considerations
- Numbered task list with `Parallelizable: yes/no` flags (5-15 min each, TDD-ready)

**Output:** Cleaned spec saved to `specs/<feature>-spec.md`. Session noise (prompt echo, tool calls, init markers) stripped — spec is 45-58% smaller than raw session.

### Orchestrator Gate
Reads confidence × impact from the strategist's spec and decides pipeline depth:

| Impact ↓ / Confidence → | HIGH | MEDIUM | LOW |
|---|---|---|---|
| **LOW** (tests/docs) | **vet (1+2+3)** | vet+nm (1-4) | full (1-5) |
| **MEDIUM** (API/DB/UI) | vet+nm (1-4) | full (1-5) | full (1-5) |
| **HIGH** (auth/payments) | full (1-5) | full (1-5) | full (1-5) |

**vet is the minimum.** No change ships without build + tests. Only HIGH confidence + LOW impact skips adversarial review.

| Depth | Stages | Meaning |
|-------|--------|---------|
| **vet** | 1+2+3 | Strategist + Coder + vet. Panel creates basic PR. No adversarial review. |
| **vet+nm** | 1+2+3+4 | + nm fresh-session adversarial review from different model family. nm creates PR. |
| **full** | 1-5 | All stages. nm creates PR, TL reviews and signs off. |

**Mode:** High confidence = PASSIVE (auto-pilot). Medium/Low = ACTIVE (orchestrator reviews each phase, may loop back).

`PANEL_FORCE_FULL=1` overrides → all 5 phases.

### Phase 2: Coder
Implements the spec on a `feat/<slug>` branch with TDD (RED→GREEN two-commit discipline):
- Panel schedules coders in waves based on the dependency DAG — independent tasks run in parallel (up to 5 worktrees), dependent tasks queue behind.
- Each coder gets 1-2 small tasks per wave. v4-flash handles this comfortably.
- Uses `deepseek-v4-flash` (3.1× cheaper than v4-pro) with `ai-coding-best-practices-lite` skill.
- Before push: runs lint + full test suite. Fixes failures in-session.
- At `depth=vet`: creates PR directly. Otherwise pushes branch for downstream phases.

**Parallel mode** (default, `PANEL_PARALLEL=1`): Tasks with no file collisions run in parallel worktrees. Waves computed from task DAG. `PANEL_PARALLEL=0` forces sequential.

### Phase 3: vet (shell — zero AI tokens)
Pure shell script. No AI agent. No tokens. No model.

1. Checkout feature branch
2. Run test command from `AGENTS.md`
3. Run build command from `AGENTS.md`
4. Report pass/fail

**Verification retry loop:** On test/build failure → spawn coder with failure output → fix → re-verify (up to 2 retries). BLOCKED if still failing after max retries.

**Note:** vet does NOT create a PR. At `depth=vet`, the panel creates a basic PR after vet passes. For deeper depths, nm handles PR creation.

### Phase 4: nm (adversarial review — fresh session, different model family)
The panel invokes `~/bin/nm --skip-tests` (tests already passed in vet):

1. Captures git diff from `HEAD~1`
2. Spawns a fresh Hermes session loading `no-mistakes` + `ai-coding-best-practices` skills
3. The spawned session runs the 7-stage nm pipeline:
   - Intent analysis (what was built and why)
   - Branch naming (conventional commit)
   - Rebase (onto latest main)
   - Fresh-context adversarial review (different model family — no memory of coding process)
   - Test rerun (skipped via `--skip-tests`)
   - Doc lint (stale references, missing updates)
   - Push + PR creation (with risk assessment: LOW/MEDIUM/HIGH)

**Why a different model family?** If the coder used DeepSeek, nm uses Anthropic or OpenAI. A model that didn't see the code being written catches bias-blind spots — the same model reviewing its own work misses edge cases.

The panel extracts the PR URL and risk level from nm's output for the Tech Lead phase.

### Phase 5: Tech Lead (depth=full only)
Three-part adversarial review against the spec using `deepseek-v4-pro` + `adversarial-review-lite` skill:

1. **Spec Compliance** — Approach matches decision table? API/interface matches? ALL tasks done? Scope creep?
2. **Architectural Impact** — New deps/coupling? Breaking changes? Deployment impact?
3. **Code Quality** — TDD, correctness, security, error handling, performance

**Severity:** BLOCKER (fix before merge) | SHOULD FIX (auto-creates GitHub Issues) | NIT (optional)

**Verdict:** APPROVED / CHANGES REQUESTED / BLOCKED

The TL reviews the PR created by nm. Verdict + risk + release type are appended to the PR body via `gh api PATCH`. Final sign-off before user merge.

---

## Interview Flow (Pause-and-Resume)

When the strategist cannot proceed with high confidence, it enters interview mode:

```
1. Panel exits with code 2
2. Saves questions + context to /tmp/hermes-panel-interview.json
3. Orchestrator reads JSON, presents questions to user
4. User answers → orchestrator writes answers back to JSON
5. Re-run: hermes-panel --answers /tmp/hermes-panel-interview.json "feature" ~/project
```

The interview JSON captures full context (assumption, impact if wrong) for each question. This keeps the panel stateless and replayable — perfect for Telegram/cron workflows.

```
┌─ Q1: Should API keys be per-user or per-project?
│  Assumption: Per-project keys (simpler implementation)
│  Impact: If wrong, multi-user projects share keys → security issue
└────────────────────────────────────────
```

---

## Environment Variables

| Variable | Effect | Default |
|----------|--------|---------|
| `PANEL_REASONING` | Override strategist reasoning effort (`high`/`medium`) | `medium` (config) |
| `PANEL_PARALLEL` | Force sequential (`0`) or parallel (`1`) coders | `1` |
| `PANEL_FORCE_FULL` | Run all 5 phases regardless of depth matrix | off |
| `GH_TOKEN` | GitHub auth for PR/issue creation | from `.env` |

---

## Token Optimizations

The panel has been systematically optimized to reduce cost while preserving quality:

| Optimization | Mechanism | Saving |
|-------------|-----------|---------|
| Spec noise extraction | Strip session transcript (prompt echo, tool calls) from strategist output | 45-58% smaller |
| Task-extract for coder | Generate `specs/<feature>-tasks.md` — coder reads ~800 chars, not ~12K | ~93% smaller read |
| Coder flash model | `deepseek-v4-flash` instead of v4-pro for implementation | 3.1× cheaper |
| Phase 3 pure shell (vet) | No AI agent — `git checkout`, test, build | Zero AI tokens |
| Phase 4 fresh nm session | Different model family catches bias-blind spots — costs tokens but prevents bugs | ~15% of pipeline |
| `adversarial-review-lite` | 2.2K vs 13.8K for full `adversarial-review` + `ai-coding-best-practices` | ~11.5K system tokens saved |

**54% cheaper than an unoptimized pipeline.**

Cost distribution by phase (approximate):

| Phase | % of total |
|---|---|
| Strategist | 58% |
| Coder | 8% |
| vet | 0% |
| nm | 15% |
| Tech Lead | 19% |

---

## Project Detection

The panel auto-detects from the project directory:
- **GitHub repo:** parsed from `git remote get-url origin` (supports HTTPS and SSH URLs)
- **Test command:** parsed from `AGENTS.md` matching patterns like `Unit tests: \`npx vitest run\``
- **Build command:** parsed from `AGENTS.md` matching patterns like `Full build: \`npm run build\``
- **Lint command:** parsed from `AGENTS.md` matching patterns like `Lint: \`npx eslint .\``

Falls back to `npm test` / `npm run build` / `npm run lint` if AGENTS.md patterns not found.

---

## Failure Handling

When any phase fails, the panel:
1. Reverts ALL changes (deletes branch, `git checkout master`, clears stash)
2. Prints a `PIPELINE HALTED` summary with phase and reason
3. Prints "Orchestrator Action Required" checklist
4. Exits cleanly — **no automatic retry** without user approval

Per-phase timeout fallbacks:

| Phase | Timeout Response |
|-------|-----------------|
| Strategist | If output < 500 chars → abort pipeline |
| Coder | If branch exists → continue with partial output. If not → abort |
| vet | Fail → spawn coder to fix → re-verify (up to 2 retries). BLOCKED if still failing |
| nm | If nm exits non-zero → warn but continue (TL can review branch directly) |
| Tech Lead | Use partial output for verdict. Partial review > no review |

---

## File Structure

```
~/.hermes/scripts/hermes-panel              → canonical source
<project>/specs/<feature>-spec.md           → cleaned strategist spec
<project>/specs/<feature>-tasks.md          → task-extract for coder
<project>/.hermes-panel/worktrees/          → parallel coder sandboxes
/tmp/hermes-panel-output.txt               → full pipeline log
/tmp/hermes-panel-interview.json           → interview state (exit code 2)
```

---

## Companion Scripts

| Script | Purpose |
|--------|---------|
| `nm` | Panel Phase 4 (adversarial review + PR) and standalone manual validation |
| `vet` | Standalone shell verification (build+test) for manual pre-commit checks |
| `daily-cleanup.sh` | Cron-driven cleanup |
| `github-monitor.sh` | GitHub activity monitoring |

---

## Setup & Deployment

See [panel-setup.md](panel-setup.md) for:
- One-time machine setup (profiles, skills, GH token)
- Per-project setup (AGENTS.md, git remote)
- Smoke test instructions
- Cron integration
- Troubleshooting

---

## Requirements

- Python 3.6+ (compatible with Oracle Linux 8 system Python)
- Hermes Agent installed with 3 profiles (strategist, coder, tech-lead)
- `gh` CLI (GitHub) installed and authenticated
- DeepSeek API access (strategist/coder/TL) + one additional model family (nm adversarial review)
- `AGENTS.md` at project root with test, build, and lint commands
- GitHub remote configured (`git remote get-url origin`)
- `GH_TOKEN` in `~/.hermes/profiles/work/.env`
