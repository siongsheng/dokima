# F012: Profile Templates

**Priority:** P2
**Dependencies:** F011 (Installer Script — Done)
**User Story:** As a new developer, `dokima init` creates agent profiles (`strategist`, `coder`, `tech-lead`, `nm`) with sensible defaults — I only need to add my API keys.

## Acceptance Criteria

1. **Profile creation**: When `dokima init "description"` runs, it checks if profiles `strategist`, `coder`, `tech-lead`, `nm` exist under `~/.hermes/profiles/`. Missing profiles are created via `hermes profile create <name>`.

2. **Sensible defaults**: Each profile is configured with:
   - Model: `deepseek-v4-pro`, Provider: `deepseek`
   - `agent.max_turns: 150`
   - `terminal.env_passthrough: [GH_TOKEN, GITHUB_TOKEN, HERMES_HOME, HOME]`
   - Strategist gets `agent.reasoning_effort: high`

3. **Skill deployment**: Each profile's skill directory gets the appropriate skills deployed from `dokima/skills/`:
   - `strategist`: `spec-strategist-lite`, `ponytail-guard`
   - `coder`: `ai-coding-best-practices-lite`
   - `tech-lead`: `adversarial-review-lite`, `ponytail-guard`
   - `nm`: `no-mistakes` (deployed to global skills dir `~/.hermes/skills/software-development/`)

4. **Idempotent**: Re-running `dokima init` does not overwrite existing profiles or skills. Reports "already exists" and skips.

5. **Non-interactive safe**: When no TTY is available (cron, piped), profile creation uses defaults without prompting.

## Out of Scope
- API key collection (handled separately)
- Provider/model switching (F013)
- nm script portability (F014)
- README/quickstart (F015)
