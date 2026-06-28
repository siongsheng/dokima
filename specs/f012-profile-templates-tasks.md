# F012: Profile Templates — Task Breakdown

## Task 1: `ensure_profiles()` function
**Description:** Add `ensure_profiles()` to dokima that creates missing agent profiles via `hermes profile create` and configures sensible defaults.
**Files:** `dokima`
**Tests:** `tests/test_profile_templates.py` — test that missing profiles are created, existing profiles skipped, idempotency, non-TTY fallback.
**Acceptance Criteria:**
- On first run: creates profiles `strategist`, `coder`, `tech-lead`, `nm` if missing
- Configures each with model/provider/turns/env_passthrough
- Strategist gets `agent.reasoning_effort: high`
- On re-run: skips existing profiles with "already exists" message
- When `not sys.stdin.isatty()`: runs non-interactively with defaults

## Task 2: `deploy_profile_skills()` function
**Description:** Add `deploy_profile_skills()` that copies skills from `dokima/skills/` to appropriate profile and global skill directories.
**Files:** `dokima`
**Tests:** `tests/test_profile_templates.py` — test skill deployment to correct dirs, idempotency, missing source skill handling.
**Acceptance Criteria:**
- Copies `spec-strategist-lite` and `ponytail-guard` to strategist profile skills
- Copies `ai-coding-best-practices-lite` to coder profile skills
- Copies `adversarial-review-lite` and `ponytail-guard` to tech-lead profile skills
- Copies `no-mistakes` to global `~/.hermes/skills/software-development/`
- On re-run: skips existing skill directories
- Warns if source skill directory missing

## Task 3: Integrate into `run_init()`
**Description:** Call `ensure_profiles()` and `deploy_profile_skills()` from `run_init()` before strategist spawn.
**Files:** `dokima`
**Tests:** Update existing init tests or integration test.
**Acceptance Criteria:**
- `dokima init "description"` creates profiles before strategist phase
- Profile/skill creation output appears before "Phase: Strategist (init)"
- Does not block init if profile creation fails (warns, continues)
