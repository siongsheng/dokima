# init — Requirements & Edge Cases

## Functional requirements

| ID | Requirement | Priority |
|----|------------|----------|
| R1 | `dokima init "description"` runs discovery mode | P0 |
| R2 | `dokima init "description" /path/to/project` targets a specific directory | P0 |
| R3 | Greenfield: creates AGENTS.md from detected tech stack | P0 |
| R4 | Greenfield: `git init` if no repo exists | P0 |
| R5 | Greenfield: prompts user for GitHub remote URL | P0 |
| R6 | Existing: does NOT overwrite AGENTS.md without confirmation | P0 |
| R7 | Existing: codebase audit runs before constitution | P0 |
| R8 | Strategist uses spec-kit + saas-ideation skills | P0 |
| R9 | Strategist max_turns bumped to 300, restored after | P0 |
| R10 | Produces specs/mission.md | P0 |
| R11 | Produces specs/tech-stack.md | P0 |
| R12 | Produces specs/roadmap.md | P0 |
| R13 | Produces specs/conventions.md | P0 |
| R14 | Initializes specs/STATUS.md | P1 |
| R15 | Validation loop: strategist self-reviews before exit | P1 |
| R16 | Exit code 0, no coder/vet/nm/TL phases | P0 |

## Edge cases

| Case | Behavior |
|------|----------|
| Project dir doesn't exist | Create it (greenfield) |
| Project dir exists but empty | Treat as greenfield |
| Project dir has files but no AGENTS.md | Warn, treat as existing codebase without conventions |
| Project dir has specs/ already | Warn, ask if overwrite or merge |
| No git installed | Skip git init, warn user |
| gh CLI not installed | Skip remote setup, warn user |
| User provides empty description | Err: description required |
| Strategist times out (300 turns) | Partial output saved, warn user to re-run or refine |
| `init` followed by regular feature arg | Only the first arg after `init` is the description |
| Project dir has AGENTS.md but no git remote | Treat as existing, skip git init |
| API key missing | Err: same as regular panel run |
| hermes binary not found | Err: same as regular panel run |

## Out of scope

- Re-running init on initialized project (update mode)
- `init --skip-audit` flag for existing projects
- Interactive mode: strategist asks user questions mid-run (relies on strategist's clarify tool)
- Auto-detecting GitHub username for remote URL
