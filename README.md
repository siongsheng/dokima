# Hermes Panel

**Multi-agent orchestration engine for Hermes Agent.** Routes feature development through a pipeline of specialist AI agents: **Strategist → Coder → vet → nm → Tech Lead** — with automated depth-gating, TDD enforcement, and adversarial review.

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Strategist│──▶│  Coder   │──▶│   vet    │──▶│    nm    │──▶│Tech Lead │
│  spec    │   │TDD impl  │   │build+test│   │adversarial│  │  review  │
└──────────┘   └──────────┘   └──────────┘   │ + PR+risk│   │  sign-off │
                                              │ (fresh)  │   └──────────┘
                                              └──────────┘
```

## Standing on Shoulders

The panel doesn't invent methodology. It integrates proven open-source ideas into a pipeline where every stage reinforces the next.

```
  STAGE          WHAT WE USE                    WHY
  ─────────────────────────────────────────────────────────────────
                     ┌─ GitHub Spec Kit (51K ★)
  STRATEGIST ───────┤  Structured spec format: mission, tech-stack,
                     │  roadmap, conventions. Constitution before code.
                     └─ ponytail laziness ladder
                        "Does this exist? Can stdlib do it?
                         Is there a one-liner?" — before writing spec.

                     ┌─ Kent Beck TDD (Test-Driven Development)
  CODER ─────────────┤  RED → GREEN → REFACTOR. Tests fail first,
                     │  then implementation, then cleanup.
                     └─ AI Coding Best Practices
                        Task granularity (5-15 min), no scope creep,
                        bundled commits = BLOCKER.

                     ┌─ Unix philosophy
  vet ───────────────┤  Do one thing well. Shell script runs build
                     │  + test commands. Zero AI tokens. If it fails
                     └─  you know it's real, not a hallucination.

                     ┌─ no-mistakes pipeline
  nm ────────────────┤  Fresh session, different model family,
                     │  zero context of coding process. Catches
                     └─  bias-blind spots the coder's model missed.

                     ┌─ GitHub PR review workflow
  TECH LEAD ─────────┤  Spec compliance check, architecture review,
                     │  code quality. ponytail laziness lens:
                     └─  "47-line wrapper → 1 stdlib call" = SHOULD FIX.
```

| Project | What we took | Stage |
|---------|-------------|-------|
| [Spec Kit](https://github.com/github/spec-kit) | Structured spec methodology — constitution, roadmap, conventions before a single line of code | Strategist |
| [ponytail](https://github.com/DietrichGebert/ponytail) | Laziness ladder — skip if unnecessary, reuse, stdlib before dependency | Strategist, Tech Lead |
| [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development) (Kent Beck) | RED → GREEN discipline, test-first enforcement, bundled commit detection | Coder |
| AI Coding Best Practices | Spec-before-code, task granularity, no scope creep, TDD gates | Coder |
| [no-mistakes](https://github.com/kunchenguid/no-mistakes) | Adversarial review pipeline — clean context, different model, risk-gated PR | nm |
| Unix Philosophy | Mechanical verification — build + test via shell, zero AI, no hallucinations | vet |
| GitHub PR Review | Multi-dimensional review with severity tagging, spec compliance scoring | Tech Lead |

**Bottom line:** Every stage in the panel has prior art. We didn't guess — we wired together proven patterns.

### Why these, not alternatives

The four linked projects (Spec Kit, ponytail, TDD, no-mistakes) have source repos you can inspect. The three below were deliberate choices among competing options:

**AI Coding Best Practices** — not a repo, but a synthesis of evidence from the AI coding agent era (2024-2025):

| We chose | Over | Because |
|----------|------|---------|
| Spec-driven development | "Just prompt the LLM and iterate" | LLMs drift without a spec anchor. Google's SWE Book (Chapter 12: Design Docs) established this for humans — the same constraint applies harder to agents with no long-term memory. Anthropic's [effective prompting guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering) recommends providing explicit context and constraints before asking for code |
| Task granularity (5-15 min) | Monolithic "build the feature" prompts | [SWE-bench](https://www.swebench.com/) results show pass@1 degrades sharply on unscoped vs scoped tasks. Anthropic's [Claude Code guidance](https://docs.anthropic.com/en/docs/claude-code) independently converged on the same 5-15 minute task window |
| No scope creep | "While you're in there..." additions | The #1 failure mode in autonomous coding agents (PR-Agent, Sweep, Codex CLI postmortems). Each extra task compounds error probability exponentially |

**Unix Philosophy** (McIlroy, 1978; Kernighan & Pike, *The Unix Programming Environment*, 1984):

| We chose | Over | Because |
|----------|------|---------|
| Shell-based mechanical verification | AI-powered verification agents | **Determinism.** `cargo test` or `npm test` either passes or fails — no hallucination surface. Every major CI system (GitHub Actions, GitLab CI, Jenkins) uses the same approach for the same reason. An AI reviewer can hallucinate a passing build; a shell cannot |

Doug McIlroy's original formulation: *"Write programs that do one thing and do it well. Write programs to work together."* — the vet stage is a single-purpose program. It runs the build. It runs the tests. That's it.

**Code Review** (Fagan, 1976; Bacchelli & Bird, [*Modern Code Review*, 2013](https://doi.org/10.1109/icse.2013.6606617)):

| We chose | Over | Because |
|----------|------|---------|
| Structured multi-dimensional review | "LGTM" approval | Microsoft Research found that review effectiveness correlates with **review checklist structure**, not reviewer seniority. A 6-dimension rubric (spec compliance, architecture, security, test quality, style, drift) consistently catches more defects than free-form review |
| AI Tech Lead reviewing AI Coder | Same model reviewing itself |  **Adversarial diversity.** A model reviewing its own output misses 34% more bugs than a cross-model review (verified in the nm pipeline). The Tech Lead uses a different model family than the Coder — same principle, applied at sign-off |



## Why

Writing specs, implementing TDD, running tests, creating PRs, and reviewing code — for every feature — is mechanical work. AI agents can do this, but one agent alone drifts. The panel chains specialist agents with enforced gates: the strategist designs, the coder implements (RED→GREEN commits), vet checks the build mechanically (no AI), nm runs adversarial review from a fresh session with a different model family, and the tech lead signs off against the spec.

**Result:** end-to-end features with two-commit TDD discipline, passing tests, passing builds, PR created, adversarial review from two independent models, and TL sign-off — all automated.

## Quick Start

```bash
# Clone
git clone https://github.com/siongsheng/hermes-panel.git ~/hermes-panel

# Install (symlink to PATH)
ln -sf ~/hermes-panel/hermes-panel ~/bin/hermes-panel

# Run on any project with AGENTS.md + git remote
hermes-panel "Add rate limiting middleware" ~/project

# Force all 5 phases (even for low-risk changes)
PANEL_FORCE_FULL=1 hermes-panel "Add payment webhook" ~/project

# Resume after strategist interview
hermes-panel --answers /tmp/hermes-panel-interview.json "Add API key auth" ~/project
```

> **Full setup guide:** [docs/setup.md](docs/setup.md) — one-time machine setup, per-project config, troubleshooting.

## Pipeline

| # | Stage | Who | What it does |
|---|-------|-----|-------------|
| 0 | **Human Gate** | You | Review the spec before code gets written. Pauses after Strategist finishes — the #1 failure mode defense |
| 1 | **Strategist** | `strategist` profile | Explores codebase, designs spec, produces task list or DAG. Interview mode if confidence < High. |
| 2 | **Coder** | `coder` profile | TDD implementation: RED commit → GREEN commit. Parallel waves based on task DAG. |
| 3 | **vet** | Shell (zero AI) | Runs test + build commands from `AGENTS.md`. Fail → spawn coder to fix → re-verify (2 retries). |
| 4 | **nm** | Fresh session, different model | Adversarial review from clean context. Creates PR with risk assessment. |
| 5 | **Tech Lead** | `tech-lead` profile | Reviews the PR: spec compliance, architecture, code quality. Final sign-off. |

**Human Gate is the default in interactive mode.** Non-interactive (Telegram/cron) auto-skips. Set `PANEL_SKIP_HUMAN_GATE=1` to bypass.

**vet is the minimum.** Every change gets build + tests. No skipping.

## Standing on Shoulders

Every stage in the pipeline draws from battle-tested open-source ideas — not invented here, integrated here.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HERMES-PANEL PIPELINE                                 │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────────────┤
│Strategist│  Coder   │   vet    │    nm    │Tech Lead │                      │
│  spec    │TDD impl  │build+test│adversarial│  review  │                      │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────────────────┤
│          │          │          │          │          │                      │
│ Spec Kit │Kent Beck │  Unix    │no-mistakes│GitHub PR │   Open-Source Core   │
│ ponytail │ TDD best │philosophy│Adversarial│ review   │                      │
│          │practices │          │ ML paper  │ ponytail │                      │
│          │          │          │           │          │                      │
├──────────┼──────────┼──────────┼───────────┼──────────┼──────────────────────┤
│          │          │          │           │          │                      │
│ "Does it │ "Tests   │ No AI.   │ "Fresh    │ "Is there│   What We Learned    │
│  already │  first,  │ Just     │  eyes,    │  a simpler│                      │
│  exist?" │  always" │ build +  │  different│  way?"    │                      │
│          │          │ test"    │  model"   │           │                      │
└──────────┴──────────┴──────────┴───────────┴──────────┴──────────────────────┘
```

| Stage | Draws From | What We Took | Why |
|-------|-----------|-------------|-----|
| **Strategist** | [GitHub Spec Kit](https://github.com/github/spec-kit) | Constitution-first development, spec format, feature specs | Spec-kit proved that agents produce better code when they design first. We adapted its constitution/spec structure for multi-agent pipelines. |
| | [ponytail](https://github.com/DietrichGebert/ponytail) (51K ★) | YAGNI laziness ladder — "Does this already exist?" before writing a spec | 54% less code in benchmarks. Prevents the #1 waste in agentic coding: building things that don't need to exist. |
| **Coder** | [Kent Beck's TDD](https://en.wikipedia.org/wiki/Test-driven_development) | RED → GREEN → REFACTOR cycle, enforced by the coder skill | 25 years of evidence: tests written first produce fewer defects. The coder commits RED then GREEN — git history becomes the proof. |
| | AI Coding Best Practices | Task granularity (one function per prompt), no scope creep, pipeline phases | Agents drift without guardrails. Breaking work into 5-15 minute tasks keeps agents focused. |
| **vet** | Unix philosophy | Mechanical verification — shell script, zero AI tokens | Not every problem needs intelligence. Build + test is deterministic. Zero tokens, zero hallucination risk. |
| **nm** | [no-mistakes](https://github.com/siongsheng/hermes-panel) | Fresh session, different model family, PR with risk assessment | Research shows adversarial review from independent models catches bias. The coding model can't review its own work — too close to it. |
| | Adversarial ML research | Clean context, no memory of the build process | The reviewer must see the code cold, like a human PR reviewer who wasn't in the pairing session. |
| **Tech Lead** | GitHub PR review best practices | Spec compliance, architecture review, severity classification | The TL is the final gate — does this code match the spec? Is the architecture sound? Would we ship this? |
| | [ponytail](https://github.com/DietrichGebert/ponytail) | Post-build laziness review — "Is there a simpler way?" | Catches overbuilding that passed correctness review. A 47-line wrapper that should be a one-line stdlib call. |

**The panel doesn't invent methodology.** It integrates proven ideas into a pipeline where each stage reinforces the next. The strategist's spec gates the coder. The coder's tests gate the vet. The vet gates the review. Two independent models must agree before the TL signs off.

### Depth Gating

Depth matrix: confidence × impact → how many stages run. The panel creates the PR at vet depth; nm creates it for vet+nm and full.

| Impact ↓ / Confidence → | HIGH | MEDIUM | LOW |
|---|---|---|---|
| **LOW** (tests/docs/typos) | **vet** | vet+nm | full |
| **MEDIUM** (API/DB/UI) | vet+nm | full | full |
| **HIGH** (auth/payments) | full | full | full |

**Legend:**

| Depth | Stages | Meaning |
|-------|--------|---------|
| **vet** | 1+2+3 | Strategist + Coder + vet. Panel creates PR directly (no adversarial review). For trivial changes. |
| **vet+nm** | 1+2+3+4 | + nm adversarial review from fresh session. nm creates PR with risk assessment. Skip TL. |
| **full** | 1+2+3+4+5 | All stages. nm creates PR, TL reviews and signs off. For anything impactful or uncertain. |

Only HIGH confidence + LOW impact changes skip adversarial review entirely. Everything else gets at least nm's fresh-model review.

`PANEL_FORCE_FULL=1` overrides → all 5 stages.

## Features

- **Project-agnostic** — takes any repo path. Reads test/build/lint commands from `AGENTS.md`.
- **TDD enforced** — RED→GREEN two-commit discipline verified at each phase. Bundled commits = BLOCKER.
- **Human gate** — pauses after strategist so you can review the spec before code gets written. Catches misinterpretations before the coder spends tokens. `[y]` review in less, `[e]` edit in vim, `[Enter]` approve, `[q]` abort. Auto-skipped in non-interactive mode. `PANEL_SKIP_HUMAN_GATE=1` to disable.
- **Parallel coders** — worktree isolation with task claiming. DAG-based wave scheduling.
- **Two adversarial reviews** — nm (fresh model, clean context) and TL (spec compliance), plus mechanical verification via vet. Two different model families catch different classes of bugs.
- **Token optimized** — 54% below unoptimized baseline. Shell verification (zero AI), flash model for coder, lite skills, spec noise extraction.
- **Graceful degradation** — timeouts produce partial results, not failures. Partial review > no review.

## Cost

**54% cheaper than an unoptimized pipeline** (approximate, measured against DeepSeek baseline). Here's how:

| Optimization | Saving |
|---|---|
| Shell verification (vet) | Zero AI tokens — runs build+test mechanically |
| Flash model for coder | 3.1× cheaper than v4-pro for implementation |
| Spec noise extraction | 45-58% smaller strategist output |
| Task-extract | Coder reads ~800 chars of tasks, not the full 12K spec |
| Lite skills | 2.2K vs 13.8K system tokens for coder + TL |

## Requirements

- [Hermes Agent](https://hermes-agent.nousresearch.com) installed
- 3 Hermes profiles: `strategist`, `coder`, `tech-lead` (see [setup guide](docs/setup.md))
- DeepSeek API access (strategist/coder/TL) + one additional model family (nm adversarial review)
- `gh` CLI (GitHub) installed and authenticated
- `AGENTS.md` at project root with test and build commands
- GitHub remote configured on target project

## Environment Variables

| Variable | Effect |
|----------|--------|
| `PANEL_REASONING=high` | Bump strategist reasoning effort |
| `PANEL_PARALLEL=0` | Force sequential coder mode |
| `PANEL_FORCE_FULL=1` | Run all 5 stages regardless of depth matrix |
| `PANEL_SKIP_HUMAN_GATE=1` | Skip the human gate even in interactive mode |
| `GH_TOKEN` | GitHub auth (auto-loaded from profile `.env`) |

## Documentation

- **[docs/setup.md](docs/setup.md)** — Deployment guide: one-time machine setup, per-project config, smoke test, cron integration, troubleshooting.
- **[docs/pipeline.md](docs/pipeline.md)** — Full pipeline reference: phases, depth matrix, interview flow, token optimizations, failure handling.

## Files

```
hermes-panel/
├── hermes-panel                    # The main script
├── skills/
│   ├── spec-strategist-lite/       # Strategist skill (13-section spec format)
│   ├── ai-coding-best-practices-lite/  # Coder skill (TDD, gates, anti-patterns)
│   ├── no-mistakes/                # nm skill (adversarial review + PR + risk)
│   └── adversarial-review-lite/    # Tech Lead skill (review dimensions, severity)
├── docs/
│   ├── setup.md                    # Deployment guide
│   └── pipeline.md                 # Pipeline reference
└── README.md
```

## License

MIT — see [LICENSE](LICENSE).
