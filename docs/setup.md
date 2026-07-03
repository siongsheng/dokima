# Dokima — Deployment & Setup Guide

Bring the multi-agent panel to a new repository or a fresh machine. One-time setup takes ~5 minutes per machine; per-project setup takes 60 seconds.

---

## Architecture

```
Human Gate ──▶ Strategist ──▶ Coder ──▶ vet ──▶ nm ──▶ Tech Lead
  (you)         v4-pro      v4-pro   shell   fresh    v4-pro
                 58%          8%        0%      15%      19%
                                     │       │
                                     │       └─ different model family
                                     └─ zero AI tokens
```

**5 phases + Human Gate.** Depth matrix auto-selects how many stages run based on confidence × impact. `PANEL_FORCE_FULL=1` runs all 6 stages. Full pipeline reference: [pipeline.md](pipeline.md).

---

## 1. Prerequisites

### On every machine

| Requirement | Check |
|-------------|-------|
| Hermes Agent installed | `hermes --version` |
| Python 3.6+ | `python3 --version` |
| `gh` CLI (GitHub) | `gh --version` |
| `git` 2.25+ | `git --version` |
| DeepSeek API access | API key configured |
| One additional model family (for nm) | Anthropic or OpenAI API key |
| [adr-tools](https://github.com/npryce/adr-tools) (for ADR lifecycle) | `adr version` |

### Per-project

| Requirement | Why |
|-------------|-----|
| `AGENTS.md` at repo root | Panel reads test/build/lint commands |
| GitHub remote configured | `git remote get-url origin` returns a GitHub URL |
| Existing test suite | Phase 2 (TDD) needs a test runner |
| `docs/adr/` directory (optional) | `adr init docs/adr` — enables ADR lifecycle |

---

## 2. One-Time Machine Setup

### 2.1 Install the panel

```bash
git clone https://github.com/siongsheng/dokima.git ~/dokima
ln -sf ~/dokima/dokima ~/bin/dokima
```

### 2.2 Create the 3 agent profiles

The panel spawns agents by profile name: `strategist`, `coder`, `tech-lead`.

> **Recommended:** Run the setup script (`scripts/setup-linux.sh` or `scripts/setup-windows.ps1`) instead — it handles profiles, API keys, and GitHub tokens interactively in one step. See [Quick Start](../README.md#quick-start).

```bash
# Create profiles (generates full default configs)
hermes profile create strategist
hermes profile create coder
hermes profile create tech-lead

# Override specific values
hermes --profile strategist config set model.default deepseek-v4-pro
hermes --profile strategist config set model.provider deepseek
hermes --profile strategist config set agent.max_turns 150
hermes --profile strategist config set agent.reasoning_effort high
hermes --profile strategist config set terminal.env_passthrough '[GH_TOKEN, GITHUB_TOKEN, HERMES_HOME, HOME]'

hermes --profile coder config set model.default deepseek-v4-pro
hermes --profile coder config set model.provider deepseek
hermes --profile coder config set agent.max_turns 150
hermes --profile coder config set terminal.env_passthrough '[GH_TOKEN, GITHUB_TOKEN, HERMES_HOME, HOME]'

hermes --profile tech-lead config set model.default deepseek-v4-pro
hermes --profile tech-lead config set model.provider deepseek
hermes --profile tech-lead config set agent.max_turns 150
hermes --profile tech-lead config set terminal.env_passthrough '[GH_TOKEN, GITHUB_TOKEN, HERMES_HOME, HOME]'
```

> **Provider-agnostic:** Replace `deepseek-v4-pro` / `deepseek` with any model and provider. The panel works with Anthropic, OpenAI, DeepSeek, or OpenRouter. Just set the matching API key in `~/.hermes/shared.env`.

> **Why v4-pro for coder?** v4-flash (3.1× cheaper) ignored file hints and read entire codebases for small changes — false economy. v4-pro follows instructions, cutting total pipeline time by 50%+ despite higher per-token cost.

### 2.3 Deploy the panel skills

The panel ships four lite skills in `~/dokima/skills/`. Install them into each profile:

```bash
# Strategist skills
mkdir -p ~/.hermes/profiles/strategist/skills/software-development
cp -r ~/dokima/skills/spec-strategist-lite ~/.hermes/profiles/strategist/skills/software-development/
cp -r ~/dokima/skills/ponytail-guard ~/.hermes/profiles/strategist/skills/software-development/

# Coder skills
mkdir -p ~/.hermes/profiles/coder/skills/software-development
cp -r ~/dokima/skills/ai-coding-best-practices-lite ~/.hermes/profiles/coder/skills/software-development/

# Tech Lead skills
mkdir -p ~/.hermes/profiles/tech-lead/skills/software-development
cp -r ~/dokima/skills/adversarial-review-lite ~/.hermes/profiles/tech-lead/skills/software-development/
cp -r ~/dokima/skills/ponytail-guard ~/.hermes/profiles/tech-lead/skills/software-development/

# nm skill (global — used by Phase 4)
mkdir -p ~/.hermes/skills/software-development
cp -r ~/dokima/skills/no-mistakes ~/.hermes/skills/software-development/
```

### 2.4 Set GitHub token

```bash
# Add to shared env
echo 'GH_TOKEN=ghp_...' >> ~/.hermes/shared.env
echo 'GITHUB_TOKEN=ghp_...' >> ~/.hermes/shared.env
```

Token needs: `repo` scope (for `gh pr create`, `gh issue create`, `gh pr review`). Both `GH_TOKEN` and `GITHUB_TOKEN` are required — `gh` CLI checks `GITHUB_TOKEN` first.

### 2.5 Verify

```bash
# Check panel is executable
dokima help 2>&1 | head -5

# Verify profiles start
hermes --profile strategist -q "echo ok" --yolo
hermes --profile coder -q "echo ok" --yolo
hermes --profile tech-lead -q "echo ok" --yolo
```

### 2.6 Claude Code Setup (alternative)

The panel can use [Claude Code](https://claude.ai) instead of Hermes Agent. Claude Code doesn't have profiles or skills; instead, instructions are inlined into the prompt and tools are enabled via `--allowedTools`.

```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run the panel with Claude Code as the agent runtime
PANEL_AGENT=claude dokima "Add rate limiting middleware" ~/project
```

**Model mapping with Claude Code:**

| Panel Phase | Claude Code Model | Flag |
|-------------|-----------------|------|
| Strategist | Claude Opus 4 | `--model claude-opus-4-20250514` |
| Coder | Claude Sonnet 4 | `--model claude-sonnet-4-20250514` |
| nm | Different provider (e.g. DeepSeek via OpenRouter) | `--model openrouter/deepseek/deepseek-chat` |
| Tech Lead | Claude Opus 4 | `--model claude-opus-4-20250514` |

**How skills work:** Hermes skills (SKILL.md files) are inlined into the prompt as system instructions when using Claude Code. The panel reads the relevant skill files and prepends them to the agent prompt. No manual translation needed.

**How nm works with Claude Code:** When `PANEL_AGENT=claude`, the `~/bin/nm` script delegates to Claude Code instead of Hermes. The adversarial review still uses a different model family (DeepSeek vs Claude).

> **Current status:** Claude Code support is documented and the `PANEL_AGENT` env var is reserved. The agent provider abstraction in the panel script is the next implementation milestone. See [the issue tracker](https://github.com/siongsheng/dokima/issues) for progress.

---

## 3. Per-Project Setup

### 3.1 AGENTS.md

The panel reads test/build/lint commands from `AGENTS.md` at the project root. Minimum content:

```markdown
# Project Name

Brief description of what this project does.

## Commands

Unit tests: `npm test`
Full build: `npm run build`
Lint: `npm run lint`
```

**Supported patterns** (any will be matched):

| Pattern | Example |
|---------|---------|
| `Unit test: \`cmd\`` | `npx vitest run` |
| `Tests: \`cmd\`` | `cargo test --lib` |
| `Full build: \`cmd\`` | `npx next build` |
| `Lint: \`cmd\`` | `npx eslint .` |

If no pattern matches, defaults to `npm test` / `npm run build` / `npm run lint`.

### 3.2 Project requires specs directory

Panel writes specs to `<project>/specs/`. The directory is auto-created — no setup needed.

### 3.3 Git remote must be GitHub

The panel auto-detects `owner/repo` from `git remote get-url origin`. Supports HTTPS and SSH formats:

```
https://github.com/owner/repo.git     ✓
git@github.com:owner/repo.git         ✓
```

---

## 4. Smoke Test

Verify the pipeline works with a trivial feature:

```bash
cd ~/your-project

# Quick test: add a comment to a file
dokima "Add a JSDoc comment to the main function" .

# Force all phases (for testing)
PANEL_FORCE_FULL=1 dokima "Add a health check endpoint" .
```

**Expected output:**
```
═══ HERMES PANEL — Multi-Agent Orchestration ═══
── Phase 1: Strategist (full session) ──
...
✓ Spec saved: specs/<feature>/spec.md
── Orchestrator Gate ──
  Confidence: High, Impact: LOW → Depth: vet
── Phase 2: Coder (feature branch) ──
...
✓ Coder finished
── Phase 3: vet ──
  ✅ Tests: 42 passed, 0 failed
  ✅ Build: passed
  ✅ PR created: https://github.com/owner/repo/pull/1
✓ Pipeline complete.
```

---

## 5. Advanced: Cron Integration

Run the panel on a schedule for autonomous feature work:

```bash
hermes cron create \
  --schedule "0 14 * * 1-5" \
  --prompt "Run the panel for the next feature in the sprint backlog. Read ~/.hermes/sprints/12-week-plan.md to find the next unstarted feature." \
  --name "panel-daily-feature"
```

> When run from cron, the panel uses non-interactive mode. Human Gate auto-skips. If the strategist needs clarification, panel exits code 2 and saves questions to `/tmp/dokima-interview.json`. The orchestrator must pick these up and re-run with `--answers`.

---

## 6. Environment Variables

| Variable | Effect | Default |
|----------|--------|---------|
| `PANEL_REASONING=high` | Bump strategist reasoning effort | `medium` |
| `PANEL_PARALLEL=0` | Force sequential coder mode | `1` |
| `PANEL_FORCE_FULL=1` | Run all 5 stages regardless of depth matrix | off |
| `PANEL_SKIP_HUMAN_GATE=1` | Skip the human gate even in interactive mode | off |
| `PANEL_SKIP_AUTOFIX=1` | Disable nm+TL auto-fix loopbacks | off |
| `PANEL_SKIP_ORCHESTRATOR_REVIEW=1` | Skip orchestrator spec review loopback | off |
| `PANEL_AGENT` | Agent runtime: `hermes` (default), `claude`, `codex` | `hermes` |
| `GH_TOKEN` | GitHub auth for PR/issue creation | from `.env` |

```bash
# High-quality spec for complex features
PANEL_REASONING=high dokima "Add OAuth2 integration" ~/project

# Force all stages even for low-risk changes
PANEL_FORCE_FULL=1 dokima "Add unit test for helper" ~/project

# Sequential mode (simpler debugging)
PANEL_PARALLEL=0 dokima "Refactor database layer" ~/project

# Skip auto-fix (human reviews all findings)
PANEL_SKIP_AUTOFIX=1 dokima "Refactor auth middleware" ~/project
```

---

## 7. Interview Flow (Non-Interactive)

When the strategist can't proceed with high confidence, it enters interview mode:

1. Panel exits with code 2, saves questions to `/tmp/dokima-interview.json`
2. Orchestrator (you or a cron handler) reads the JSON
3. Presents questions to the user, collects answers
4. Writes answers back to the JSON file
5. Re-runs: `dokima --answers /tmp/dokima-interview.json "feature" ~/project`

**Interview JSON format:**
```json
{
    "feature": "Add API key authentication",
    "project": "/home/user/project",
    "questions": [
        "CLARIFICATION 1: Should API keys be per-user or per-project?",
        "CLARIFICATION 2: Where should keys be stored?"
    ],
    "answers": [
        "Per-user keys",
        "In the users table, hashed"
    ]
}
```

---

## 8. Depth Matrix

| Confidence → / Impact ↓ | HIGH | MEDIUM | LOW |
|---|---|---|---|
| **LOW** (tests/docs/typos) | vet | vet+nm | full |
| **MEDIUM** (API/DB/UI) | vet+nm | full | full |
| **HIGH** (auth/payments) | full | full | full |

| Depth | Stages | When |
|-------|--------|------|
| **vet** | Human Gate + Strategist + Coder + vet | Trivial changes. Panel creates PR directly. |
| **vet+nm** | + nm adversarial review | Medium-risk. nm creates PR with risk assessment. |
| **full** | + Tech Lead sign-off | Anything impactful or uncertain. Two independent reviews. |

Only HIGH confidence + LOW impact skips adversarial review. `PANEL_FORCE_FULL=1` overrides → all stages.

---

## 9. Token Optimization Summary

| Optimization | Savings |
|-------------|---------|
| Spec noise extraction | Significantly smaller spec (strips transcript noise) |
| Task-extract for coder | Coder reads condensed task breakdown, not the full spec |
| Coder v4-pro model | Pro model for focused, instruction-following implementation |
| Phase 3 pure shell (vet) | Zero AI tokens |
| Lite skills | Compressed skill files (~84% smaller than full equivalents) |
| Different model family (nm) | Catches bias-blind spots — costs tokens but prevents bugs |

**Substantially cheaper than running all phases at maximum model level.** Savings come from: shell-based verification (zero tokens), flash model for coding, compressed skills, and noise extraction. No dollar amounts — provider pricing changes; the architecture is the savings.

---

## 10. Troubleshooting

### "No AGENTS.md found"
Create one at project root. Minimum:
```markdown
## Commands
Unit tests: `npm test`
Full build: `npm run build`
```

### "Could not detect GitHub repo"
Ensure `git remote get-url origin` returns a valid GitHub URL. The panel supports both HTTPS and SSH formats.

### "gh pr create fails with 401"
Both `GH_TOKEN` and `GITHUB_TOKEN` must be set. `gh` CLI checks `GITHUB_TOKEN` first. Verify `~/.hermes/shared.env` has both. Token needs `repo` scope.

### "Strategist produces zero-byte spec"
Interview mode triggered but `--answers` was not provided. Check `/tmp/dokima-interview.json` for questions. Re-run with `--answers`.

### "Coder times out with no branch"
The coder profile may be hitting API rate limits or the feature is too large. Try:
- `PANEL_PARALLEL=0` for sequential mode
- Break the feature into smaller sub-features
- Check `~/.hermes/profiles/coder/config.yaml` for model and provider config

### "nm fails with model not found"
nm requires a different model family from the coder. If coder uses DeepSeek, configure an Anthropic or OpenAI model in the profile nm uses. Check `~/bin/nm` script and ensure the second model provider has a valid API key.

### "Verification fails after 2 retries"
The coder pushed broken code. Check the test/build failure output in the panel log (`/tmp/dokima-output.txt`). Fix manually, then re-run with the same feature description.
