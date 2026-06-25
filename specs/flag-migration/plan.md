# Flag Migration Spec

## Goal

Move per-invocation behavior toggles from env vars to CLI flags. Keep env vars as fallbacks for CI/CD.

## Migration Table

| Current (env var) | New (flag) | Env fallback | Type |
|----|----|----|----|
| `PANEL_FIX_ALL=1` | `--fix-all` | ✅ `PANEL_FIX_ALL` | bool |
| `PANEL_SKIP_AUTOFIX=1` | `--skip-autofix` | ✅ `PANEL_SKIP_AUTOFIX` | bool |
| `PANEL_FORCE_FULL=1` | `--force-full` | ✅ `PANEL_FORCE_FULL` | bool |
| `PANEL_SKIP_AUTO_ARCHIVE=1` | `--skip-auto-archive` | ✅ `PANEL_SKIP_AUTO_ARCHIVE` | bool |
| `PANEL_MAX_PARALLEL=5` | `--max-parallel=N` | ✅ `PANEL_MAX_PARALLEL` | int |
| `PANEL_SKIP_HUMAN_GATE=1` | `--skip-human-gate` | ✅ `PANEL_SKIP_HUMAN_GATE` | bool |
| `PANEL_AGENT` | `--agent=<name>` | ✅ `PANEL_AGENT` | str |

**Keep as env var only (no flag):**
- `PANEL_IN_AUTOMATION=1` — CI mode, never toggled by humans
- Any future secrets/tokens

## Priority: argparse native, env fallback manual

Python's argparse has no built-in env var support like click. Fallback pattern:

```python
parser.add_argument("--fix-all", action="store_true", default=None)
args = parser.parse_args()
fix_all = args.fix_all if args.fix_all is not None else os.environ.get("PANEL_FIX_ALL") == "1"
```

Or use a helper:

```python
def _flag(name, default=False):
    """Resolve flag + env var with flag priority."""
    env_val = os.environ.get(name.replace("-", "_").upper())
    return default if env_val is None else env_val == "1"
```

## Edge Cases

### EC1: Flag conflicts with positional args
- `dokima --fix-all` has no positional (project dir optional, feature description N/A)
- `dokima "feature desc" --force-full ~/project` — fine, argparse handles mixed

### EC2: Boolean flags must handle "not set" vs "set to false"
- `default=None` in argparse, then merge: flag takes priority, then env var, then hardcoded default
- This way `--no-skip-autofix` (if we add negated flags later) or unsetting env var both work

### EC3: Cron jobs using env vars
- Existing crons using `PANEL_SKIP_AUTOFIX=1` in their command strings will continue to work via env fallback
- Update cron skill templates to use flags going forward

### EC4: `--help` must document both flag and env var
```
--fix-all              Fix SHOULD FIX items too (env: PANEL_FIX_ALL=1)
--skip-autofix         Disable auto-fix loopback (env: PANEL_SKIP_AUTOFIX=1)
--force-full           Run all 5 phases regardless of depth (env: PANEL_FORCE_FULL=1)
--skip-auto-archive    Don't auto-archive merged specs (env: PANEL_SKIP_AUTO_ARCHIVE=1)
--max-parallel N       Max parallel coder worktrees (env: PANEL_MAX_PARALLEL, default: 5)
--skip-human-gate      Skip Human Gate prompt (env: PANEL_SKIP_HUMAN_GATE=1)
```

### EC5: Non-interactive mode detection
- `--skip-human-gate` already exists as implicit (detects `sys.stdin.isatty()`)
- New flag makes it explicit: `--skip-human-gate` overrides TTY detection
- Keep the existing auto-detection as a convenience

## Implementation Plan

### Phase 1: Add flags (backward compatible)
1. Add argparse definitions for all 7 flags
2. Implement resolve helper (`_flag()`)
3. Replace all `os.environ.get("PANEL_...")` with flag calls
4. Update `--help` output

### Phase 2: Deprecation warnings
1. If env var is set but flag also exists, print deprecation notice: "⚠ PANEL_FIX_ALL is deprecated — use --fix-all"
2. Give 1 sprint cycle (2 weeks) of warnings before removing env var support

### Phase 3: Remove env var reads (later)
1. Remove env var fallbacks
2. Remove deprecation warnings
3. Cron jobs updated to use flags

## Files Changed
- `dokima` — main script: argparse additions, env var replacement (~30 lines changed)
- `scripts/setup-linux.sh` — example commands updated
- `scripts/setup-windows.ps1` — same
- `skills/autonomous-ai-agents/dokima/SKILL.md` — skill docs
- `skills/autonomous-ai-agents/dokima/templates/` — cron templates
- `docs/pipeline.md` — env var references → flag references
- `cron` — existing cron jobs (env vars still work via fallback in Phase 1)
