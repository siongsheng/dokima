# init — Project Discovery & Constitution Phase

## Overview

Add `dokima init "description" [project_dir]` — a discovery mode that runs BEFORE
any feature pipeline. The strategist conducts deep project discovery and produces the
four spec-kit constitution documents. No code is written. No pipeline phases run after.

## CLI changes

```
dokima init "trading dashboard for SGX options" [project_dir]
```

The word `init` as the first argument triggers init mode. Remaining args are the project
description and optional project directory (defaults to cwd).

## Two paths

### Greenfield (no AGENTS.md, no git remote)

1. Validate project_dir exists or create it
2. Skip AGENTS.md check, skip GitHub remote check
3. Strategist runs with `spec-kit` + `saas-ideation` skills, `max_turns=300`
4. Strategist interrogates user, researches domain, produces:
   - `specs/mission.md`
   - `specs/tech-stack.md`
   - `specs/roadmap.md`
   - `specs/conventions.md`
5. Creates minimal `AGENTS.md` from detected tech stack
6. If no git repo: `git init` + prompt user for GitHub remote URL
7. Initialize `specs/STATUS.md`

### Existing project (has AGENTS.md + git remote)

1. Same strategist run with spec-kit + saas-ideation
2. Strategist adds full codebase audit to its workflow:
   - Read all source files, map architecture
   - Catalog tech debt, measure test coverage
   - Find duplicated logic, undocumented behavior
3. Constitution reflects audit findings
4. Does NOT overwrite existing AGENTS.md unless user confirms
5. Updates `specs/STATUS.md`

## Strategist config changes

Init temporarily bumps strategist profile:
- `max_turns`: 150 → 300
- Skills injected: `spec-kit`, `saas-ideation` (not `spec-strategist-lite`, not `ponytail-guard`)
- `reasoning_effort`: stays high (already default)

Restored after init completes.

## Strategist prompt requirements

The init prompt must instruct the strategist to:

1. Interrogate the user adversarially — who, what, why, success criteria, anti-goals, "what does done look like?"
2. Research the domain — competitors, existing solutions, common pitfalls, market/regulatory constraints
3. For existing codebases: audit everything before designing anything
4. Produce the 4 spec-kit docs with every tech choice justified
5. Every roadmap feature must trace to a user need
6. Anti-goals must be explicit in mission.md
7. Self-review constitution, find gaps, present to user before exiting

## Validation loop

After producing the constitution, the strategist must:
1. Review its own output for gaps
2. Flag anything that needs user clarification
3. Present the gap analysis
4. Exit cleanly — user takes it from here

## Exit behavior

Init exits with code 0 after strategist finishes. No coder, no vet, no nm, no TL.
Output message showing what was created and next steps.

## Non-goals (NOT in this feature)

- Continuous mode integration (comes after `--next` is built)
- Extracting features from roadmap into individual panel runs (comes after `--next`)
- Re-running init on an initialized project (update mode — separate feature)
- `--manual` flag (struck — user just marks roadmap)
