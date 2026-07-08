# Dokima — Multi-Agent Orchestration Engine

Python script that routes feature development through a pipeline of AI agents.
This repo IS the panel — you don't run the panel on itself.

## Tech Stack
- Python 3.6+ (modular: dokima entry point + utils.py, agent.py, pipeline.py, roadmap.py, tasks.py)
- Bash for companion scripts (nm, vet)
- Hermes Agent for profile spawning
- GitHub CLI (gh) or GitLab CLI (glab) for PR/issue management — auto-detected from git remote

## Commands
- Test: `python3 -m pytest tests/ -q`
- Build: `python3 -c "compile(open('dokima').read(), 'dokima', 'exec')"`
- Lint: `python3 -m py_compile dokima`
- Verify nm script: `bash -n scripts/nm`
- Verify vet script: `bash -n scripts/vet`
- Vet with real-code verification: `scripts/vet --verify-code .` (or `REAL_CODE_VERIFY=1 scripts/vet .`)
- Standalone real-code check: `python3 scripts/verify_imports.py <project-dir>`
- Demo real-code check (src+test fixtures): `python3 vet/real_code_check.py --src-dir src --test-dir tests`
  - Exit 0: all mock.patch targets verified importable
  - Exit 1: at least one mock.patch target is unresolvable (missing module or function)

## Testing
1029 tests pass, 4 skipped, 1033 total (pytest). Coverage: core functions + control panel + edge cases.
```bash
# Quick suite (excludes slow integration tests)
python3 -m pytest tests/ -q --ignore=tests/test_main_integration.py

# Full suite including integration (may be slow)
python3 -m pytest tests/ -q

# Single file
python3 -m pytest tests/test_slugify.py -v
```

## Conventions
- No hardcoded 'master' branch — detected from origin/HEAD
- No absolute dollar amounts in docs — provider-agnostic percentages only
- Skills are SKILL.md files with YAML frontmatter
- Panel spawns agents via `hermes --profile <role> --yolo -s <skill> chat -q "..."`
