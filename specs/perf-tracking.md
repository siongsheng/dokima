# Pipeline Performance Tracking

## Current Run: --fix mode implementation
- **Feature:** Add --fix mode
- **Started:** 2026-06-25 ~11:25 SGT
- **Process:** proc_fe0139b0301f
- **Result:** ❌ VET_FAILED

| Phase | Duration | Notes |
|-------|----------|-------|
| Strategist | ~1m | ⚠ Skill resolution failed — 168 chars |
| TL Pre-Review | ~1m | |
| Coder | ~37m | Fixed AGENTS.md, pushed 4277c6f, 196 tests |
| vet | FAILED | npm fallback — detect_commands() cached stale |
| nm | SKIPPED | |
| TL | SKIPPED | |

**Bugs found this run:**
- `spec-strategist-lite` and `ponytail-guard` not accessible (external_dirs empty) ✅ FIXED
- AGENTS.md missing Build:/Lint: entries → npm defaults on Python project ✅ FIXED (484b2c6)
- `detect_commands()` caches from main at startup — coder AGENTS.md changes invisible ⚠ ARCHITECTURAL
- One test timeout at 61s (exit 124) during coder exploration

## Historical Runs
| Date | Feature | Total | Strat | Coder | vet | nm | TL | Notes |
|------|---------|-------|-------|-------|-----|-----|-----|-------|
| Jun 25 | F001 Site Shell | ~8m | — | — | — | — | — | dokima-docs, --next flow |
| Jun 25 | F002 Home Page | ~6m | — | — | — | — | — | dokima-docs, auto-advanced |
| Jun 24 | Init (failed) | — | stuck | — | — | — | — | Clarification timeout |
| Jun 24 | Init (success) | ~5m | ~3m | — | — | — | — | 585 lines of specs |
