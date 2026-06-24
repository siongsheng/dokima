# Hermes Panel — Multi-Agent Orchestration Engine

Python script that routes feature development through a pipeline of AI agents.
This repo IS the panel — you don't run the panel on itself.

## Tech Stack
- Python 3.6+ (single script, no dependencies)
- Bash for companion scripts (nm, vet)
- Hermes Agent for profile spawning
- GitHub CLI for PR/issue management

## Commands
- Syntax check: `python3 -c "compile(open('hermes-panel').read(), 'hermes-panel', 'exec')"`
- Verify nm script: `bash -n ~/bin/nm`
- Verify vet script: `bash -n ~/bin/vet`

## Testing
This repo has no automated test suite (the panel orchestrates TDD but has none itself).
To verify the panel works:
```bash
# Syntax check the main script
python3 -c "compile(open('hermes-panel').read(), 'hermes-panel', 'exec')"

# Run a smoke test on a real project
PANEL_FORCE_FULL=1 hermes-panel "add a comment" ~/huat
```

## Conventions
- No hardcoded 'master' branch — detected from origin/HEAD
- No absolute dollar amounts in docs — provider-agnostic percentages only
- Skills are SKILL.md files with YAML frontmatter
- Panel spawns agents via `hermes --profile <role> --yolo -s <skill> chat -q "..."`
