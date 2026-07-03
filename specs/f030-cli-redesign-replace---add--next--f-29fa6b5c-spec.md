# F030: CLI redesign: replace --add/--next/--fix/--status/--stop/--kill/--list-crons/--version/--upgrade/--release with proper subcommands (dokima add, dokima next, etc). Flags (--force-full, --max-parallel) keep -- prefix. Update all tests, scripts, AGENTS.md, roadmap, and docs.

    SPEC: F030 — CLI Subcommand Redesign
    
    Version: 1.2.0 (corrected — converted Task N: → ### Task N: headers, Impact grounded in codebase evidence, test count updated to 755)
    Status: Awaiting Sign-Off
    Confidence: High
    
    
    
    1. Executive Summary
    
    Replace Dokima's flat --flag CLI interface with proper argparse subcommands (dokima add, dokima next, dokima fix, dokima status, dokima stop, dokima kill, dokima list-crons, dokima version, dokima upgrade, dokima release). Boolean flags that modify subcommand behaviour (--force-full, --max-parallel, --interactive, --skip-autofix, etc.) retain their -- prefix. dokima "Feature description" (no subcommand) remains the default pipeline trigger. This is a P2 quality-of-life change — no new functionality, just ergonomic CLI restructuring. Impacts ~2,500 LOC across 21+ files. 755 tests must still pass (749 passed + 6 skipped as of 2026-07-03).
    
    2. Constitution Check
    
    Axiom: Solves user's own pain?
    Status: YES
    Notes: Shaun has complained about --flag confusion vs proper subcommands
    ────────────────────────────────────────
    Axiom: Weekend-buildable?
    Status: YES
    Notes: Pure refactor — no new logic, ~2,500 LOC touched (most mechanical)
    ────────────────────────────────────────
    Axiom: Evidence people will pay?
    Status: N/A
    Notes: Internal tool — user is the beneficiary
    ────────────────────────────────────────
    Axiom: Tech stack boring and proven?
    Status: YES
    Notes: Python argparse — stdlib, zero dependencies
    ────────────────────────────────────────
    Axiom: Avoids AI hype categories?
    Status: YES
    Notes: Pure CLI ergonomics
    ────────────────────────────────────────
    Axiom: Existing assets reused?
    Status: YES
    Notes: All handler functions (handle_status, do_release, etc.) stay — only
      dispatch path changes
    
    3. Impact Assessment — Grounded in Codebase Evidence
    
    Verified against the live codebase at /home/opc/dokima on 2026-07-03 (749 passed, 6 skipped, 755 total tests).
    
    Core files affected (verified):
    
    
    dokima              +150/-100  (replace flag-scanning loop L87-231 with argparse subparsers)
    utils.py             +60/-30  (update HELP_TEXT L87-95 and CLI_METADATA L97-142)
    
    
    Test files with --flag references to update (verified by rg search):
    
    
    tests/test_f021_version.py      ~40 lines  (--version → version, --upgrade → upgrade)
    tests/test_f024_release.py      ~40 lines  (--release → release, help text assertions)
    tests/test_f020_help_json.py    ~30 lines  (command name assertions)
    tests/test_control_panel.py     ~20 lines  (--status/--stop/--kill → subcommands)
    tests/test_fix_mode.py           ~5 lines  (--fix assertion in HELP_TEXT check)
    tests/test_main_integration.py  ~15 lines  (4x sys.argv with --next)
    tests/test_edge_cases.py        ~30 lines  (6x sys.argv with --next)
    tests/test_final_edge.py         ~5 lines  (2x sys.argv with --continuous)
    tests/test_final_coverage.py     ~3 lines  (--continuous/--next flag variable)
    tests/test_rich_pipeline.py      ~5 lines  (2x sys.argv with --next)
    tests/test_pipeline_integration.py ~20 lines  (5x sys.argv with --next)
    tests/test_continuous.py          ~3 lines  (1x sys.argv with --continuous)
    tests/test_installer.py           ~3 lines  (--version in shell test string)
    
    
    Documentation files with --flag references (verified by rg search):
    
    
    README.md              ~30 lines  (--help, --fix, --answers examples + --fix mode section)
    MAINTAINERS.md         ~25 lines  (Common Commands: --next, --add, --fix, --status, --continuous, --next --force-full)
    docs/setup.md            ~5 lines  (--help, --answers references)
    docs/pipeline.md         ~3 lines  (--answers reference)
    install.sh               ~1 line   (--help reference L121)
    
    
    Files confirmed CLEAN (no CLI flag references, verified by rg):
    
    
    AGENTS.md             — no dokima CLI flag references (verified)
    docs/pipeline.md       — only --answers reference (mode flag, stays as --flag)
    
    
    Total affected: 2 core files + 13 test files + 5 doc files = ~20 files, ~450-550 LOC changed.
    
    Not affected (verified):
    
    
    tests/test_f022_utils.py  — references git --version (not dokima --version), no change needed
    
    
    4. What Changed (from current behavior)
    
    
    Before (F029):     dokima --add "Feature"
    After (F030):      dokima add "Feature"
    
    Before (F029):     dokima --next [dir]
    After (F030):      dokima next [dir]
    
    Before (F029):     dokima --continuous [dir]
    After (F030):      dokima next --continuous [dir]   (alias: dokima continuous [dir])
    
    Before (F029):     dokima --fix [dir]
    After (F030):      dokima fix [dir]
    
    Before (F029):     dokima --status [dir]
    After (F030):      dokima status [dir]
    
    Before (F029):     dokima --stop [dir]
    After (F030):      dokima stop [dir]
    
    Before (F029):     dokima --kill [dir]
    After (F030):      dokima kill [dir]
    
    Before (F029):     dokima --list-crons
    After (F030):      dokima list-crons
    
    Before (F029):     dokima --version
    After (F030):      dokima version
    
    Before (F029):     dokima --upgrade
    After (F030):      dokima upgrade
    
    Before (F029):     dokima --release patch
    After (F030):      dokima release patch
    
    Before (F029):     dokima "Feature" [dir]
    After (F030):      dokima "Feature" [dir]           (UNCHANGED)
    
    Before (F029):     dokima init "desc" [dir]
    After (F030):      dokima init "desc" [dir]         (UNCHANGED)
    
    Before (F029):     dokima --help / -h
    After (F030):      dokima --help / dokima -h        (UNCHANGED)
    
    Before (F029):     dokima --help-json
    After (F030):      dokima --help-json               (UNCHANGED)
    
    Before (F029):     dokima --map [dir]
    After (F030):      dokima --map [dir]               (UNCHANGED — not in scope)
    
    Before (F029):     dokima --answers <json> "Feature" [dir]
    After (F030):      dokima --answers <json> "Feature" [dir]  (UNCHANGED — mode flag)
    
    Before (F029):     dokima --max-parallel=3 next [dir]
    After (F030):      dokima next --max-parallel=3 [dir]        (flag moves to subcommand)
    
    Before (F029):     dokima --force-full "Feature" [dir]
    After (F030):      dokima --force-full "Feature" [dir]       (UNCHANGED — flag on default path)
    
    
    Key design decision: --continuous becomes a flag on dokima next (dokima next --continuous) rather than a separate subcommand, since it's a mode modifier, not a distinct operation. The bare dokima continuous is accepted as shorthand via argparse alias.
    
    Backward compatibility: NOT provided. This is a clean break. Users update their muscle memory. The dokima "Feature" default path is unchanged — that's the 95% case.
    
    5. Feature Breakdown
    
    Task 1: Replace flag-scanning loop with argparse subparsers in dokima entry point
    Files: dokima
    Dependencies: [none]
    Parallelizable: no
    Description: Replace the manual for arg in sys.argv[1:] flag-scanning loop (lines 87-231 of dokima) with argparse subparsers. Each former --flag becomes a subcommand: add, next, fix, status, stop, kill, list-crons, version, upgrade, release. Boolean flags (--force-full, --max-parallel, --interactive, --skip-autofix, --skip-auto-archive, --skip-human-gate, --resume, --no-resume, --fix-all, --dry-run) attach to their respective subcommands as optional args. The default positional "Feature" [dir] remains the no-subcommand path. --continuous becomes --continuous flag on the next subcommand. --priority becomes --priority flag on add. --map stays as --map flag on the default path (not subcommand-ized in this feature). --help-json stays as top-level flag. The --answers flag stays on default and fix subcommands. Estimated LOC: ~150 added, ~100 removed.
    
    Task 2: Update HELP_TEXT and CLI_METADATA in utils.py for subcommand syntax
    Files: utils.py
    Dependencies: [Task 1]
    Parallelizable: no
    Description: Rewrite HELP_TEXT (lines 54-95) to show subcommand syntax instead of --flag syntax. The COMMANDS section becomes: dokima add, dokima next, dokima fix, dokima status, dokima stop, dokima kill, dokima list-crons, dokima version, dokima upgrade, dokima release. Keep dokima "Feature" [dir] and dokima init "desc" [dir] as-is. Add a MODIFIER FLAGS section for flags that apply across subcommands. Update CLI_METADATA dict (lines 97-142) to rename command entries: "--add" → "add", "--next" → "next", etc. Update syntax strings: "dokima --add" → "dokima add". Keep flag and env_var entries unchanged (they stay with -- prefix). Both HELP_TEXT and CLI_METADATA are in utils.py — merged into one task to avoid sequential file conflict.
    
    Task 3: Update test_f021_version.py for subcommand dispatch
    Files: tests/test_f021_version.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Change all _run("--version") calls to _run("version"). Change _run("--upgrade") to _run("upgrade"). Update command name assertions: "name": "--version" → "name": "version", "name": "--upgrade" → "name": "upgrade". The handler function behavior is unchanged — only the CLI invocation changes. Affects lines 17, 50, 52, 58, 82, 92, 101.
    
    Task 4: Update test_f020_help_json.py for subcommand names
    Files: tests/test_f020_help_json.py
    Dependencies: [Task 2]
    Parallelizable: yes
    Description: Update assertions that check command names: "name": "--version" → "name": "version", "name": "--upgrade" → "name": "upgrade", etc. The run_help_json() helper stays — --help-json is not subcommand-ized. Assertions about flag/env_var entries remain unchanged.
    
    Task 5: Update test_control_panel.py for subcommand handler names
    Files: tests/test_control_panel.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: The handler functions (show_help, handle_status, handle_stop, handle_kill, handle_list_crons) are NOT renamed — only their dispatch path changes. Tests that call these directly via panel.show_help() etc. require no changes. Tests that run the full script with subprocess need updating: any _run("--status") → _run("status"), etc. Review the file — most tests here call handlers directly; confirm no subprocess invocations need updating.
    
    Task 6: Update test_f024_release.py for dokima release subcommand
    Files: tests/test_f024_release.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Change _run("--release", "patch") to _run("release", "patch"). Change _run("--release", "invalid") to _run("release", "invalid"). Change _run("--release", "patch", "--dry-run") to _run("release", "patch", "--dry-run"). Update help-text assertions: "--release" → "release" in help output checks (lines 252, 258, 262, 269, 278). The do_release() function itself is unchanged.
    
    Task 7: Update test_main_integration.py for dokima next subcommand
    Files: tests/test_main_integration.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Change sys.argv = ["dokima", "--next", project_dir] to sys.argv = ["dokima", "next", project_dir]. All 4 occurrences at lines 142, 161, 183, 202. The run_next_setup() function is unchanged — only the argv dispatch changes.
    
    Task 8: Update test_fix_mode.py for dokima fix subcommand
    Files: tests/test_fix_mode.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Update the HELP_TEXT assertion at line 337: "--fix" in panel.HELP_TEXT or "dokima --fix" in panel.HELP_TEXT → "fix" in panel.HELP_TEXT or "dokima fix" in panel.HELP_TEXT. Review for any other --fix flag references in subprocess calls or sys.argv manipulation.
    
    Task 9: Update test_edge_cases.py for dokima next subcommand
    Files: tests/test_edge_cases.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Replace all sys.argv = ["dokima", "--next", project_dir] with sys.argv = ["dokima", "next", project_dir]. 6 occurrences at lines 182, 229, 270, 333, 389, 462. Functions called directly need no changes.
    
    Task 10: Update test_final_edge.py and test_final_coverage.py for --continuous → next --continuous
    Files: tests/test_final_edge.py, tests/test_final_coverage.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: test_final_edge.py: Replace sys.argv = ["dokima", "--continuous", project_dir] (lines 109, 153) with sys.argv = ["dokima", "next", "--continuous", project_dir]. test_final_coverage.py: Update the flag = "--continuous" if is_continuous else "--next" (line 56) to use subcommand-variant dispatch.
    
    Task 11: Update remaining test files (rich_pipeline, pipeline_integration, continuous, installer)
    Files: tests/test_rich_pipeline.py, tests/test_pipeline_integration.py, tests/test_continuous.py, tests/test_installer.py
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Mechanical sys.argv updates: test_rich_pipeline.py lines 161, 222 (--next → next); test_pipeline_integration.py lines 164, 218, 378, 457, 533 (--next → next); test_continuous.py line 70 (--continuous → next --continuous); test_installer.py line 36 (--version in shell heredoc test → version subcommand, unless it's testing git --version). Review each — some may be testing git commands not dokima.
    
    Task 12: Update README.md examples
    Files: README.md
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Update all CLI examples at lines 34, 74, 80, 165: dokima --fix → dokima fix, dokima --answers stays (mode flag), dokima --help stays. The --fix mode documentation paragraph updates to "fix mode". All "dokima --flag" examples become "dokima subcommand" where applicable.
    
    Task 13: Update MAINTAINERS.md command references
    Files: MAINTAINERS.md
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Update Common Commands section at lines 147, 201, 204, 207, 210, 213, 216: python3 dokima --next . → python3 dokima next ., python3 dokima --add "..." → python3 dokima add "...", python3 dokima --fix --fix-all . → python3 dokima fix --fix-all ., python3 dokima --status . → python3 dokima status ., python3 dokima --continuous . → python3 dokima next --continuous ., python3 dokima --next --force-full . → python3 dokima next --force-full ..
    
    Task 14: Update docs/ references (setup.md, pipeline.md) and install.sh
    Files: docs/setup.md, docs/pipeline.md, install.sh
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: docs/setup.md line 128: dokima --help stays (--help is not subcommand-ized). Line 298: dokima --answers stays (mode flag). Verify both. docs/pipeline.md line 200: --answers stays. install.sh line 121: dokima --help stays. Verify all and skip if clean — only --help/--answers references which are unchanged.
    
    Task 15: Update AGENTS.md (verify clean)
    Files: AGENTS.md
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Verified: AGENTS.md has zero dokima CLI flag references. Skip if confirmed clean on re-read.
    
    Task 16: Update specs/roadmap.md F030 description
    Files: specs/roadmap.md
    Dependencies: [Task 1]
    Parallelizable: yes
    Description: Update F030 entry (line 130) description to reflect subcommand syntax if the description contains old --flag references. Currently it already says "replace --add/--next/..." which is accurate as the "before" description — verify and update User Story line if needed.
    
    Task 17: Run full test suite and fix failures
    Files: (any failing test file)
    Dependencies: [Tasks 1-16]
    Parallelizable: no
    Description: Run python3 -m pytest tests/ -q and fix any remaining assertion failures. Expected pattern: tests that do string-matching on help output or CLI metadata may fail on subcommand name format. Target: 755 tests (749 passed + 6 skipped). All handler logic is unchanged — only dispatch path and help text changes.
    
    6. Data Model
    
    No new entities. No schema changes. The argparse Namespace object replaces the manual boolean flags, but this is transient — no persistence change.
    
    Affected global variables in dokima (NOT removed, only their assignment path changes):
    - FORCE_FULL — now set from args.force_full instead of flag scan
    - SKIP_AUTOFIX — now set from args.skip_autofix
    - SKIP_HUMAN_GATE — now set from args.skip_human_gate
    - RESUME — now set from args.resume
    - max_parallel_override — now set from args.max_parallel
    - DEFAULT_BRANCH — unchanged (set from env)
    
    7. API Routes
    
    N/A — this is a CLI tool, not a web service.
    
    8. Component Tree
    
    
    dokima (entry point)
    ├── argparse.ArgumentParser
    │   ├── Default path (no subcommand): positional "feature" + optional "dir" + flags
    │   ├── Subparser: init  → run_init()
    │   ├── Subparser: add   → run_add_to_roadmap()
    │   ├── Subparser: next  → run_next_setup() [+ --continuous flag]
    │   ├── Subparser: fix   → run_fix_mode() [+ flags]
    │   ├── Subparser: status → handle_status()
    │   ├── Subparser: stop   → handle_stop()
    │   ├── Subparser: kill   → handle_kill()
    │   ├── Subparser: list-crons → handle_list_crons()
    │   ├── Subparser: version   → print(VERSION); sys.exit(0)
    │   ├── Subparser: upgrade   → check_upgrade()
    │   └── Subparser: release   → do_release()
    ├── Top-level flags: --help, -h, --help-json, --map, --map-full
    └── Handler functions (unchanged, in utils.py/roadmap.py/pipeline.py)
    
    
    9. COTS Build-vs-Buy
    
    Component: argparse
    Decision: Buy (stdlib)
    Justification: Python 3.6+ stdlib — already available, zero deps
    ────────────────────────────────────────
    Component: click/typer
    Decision: Reject
    Justification: Adds dependency; argparse is sufficient for this CLI
      complexity
    ────────────────────────────────────────
    Component: docopt
    Decision: Reject
    Justification: Unmaintained; argparse is the standard
    
    10. Test Plan (MANDATORY)
    
    Happy Path
    - dokima version prints dokima vX.Y.Z and exits 0
    - dokima status /path/to/repo shows pipeline state and exits 0
    - dokima add "Feature desc" adds to roadmap and exits 0
    - dokima next /path/to/repo starts pipeline and runs
    - dokima next --continuous /path/to/repo starts continuous loop
    - dokima fix /path/to/repo detects blocked PR and fixes
    - dokima release patch --dry-run prints plan without committing
    - dokima --help-json outputs valid JSON with subcommand names
    - dokima add --priority=P0 "Urgent" sets priority on roadmap entry
    
    Edge Cases
    - dokima with no args: prints usage (same as before)
    - dokima --help: prints help text with subcommand syntax
    - dokima -h: same as --help
    - dokima next --max-parallel=3 /path: flag on subcommand works
    - dokima version --help: shows version subcommand help
    - dokima version extra-arg: should ignore or error clearly (argparse default: error)
    - dokima release: missing bump type → argparse error message
    - dokima --help-json version: --help-json wins (same behavior as before)
    - Hyphenated subcommand: dokima list-crons — argparse handles this naturally
    - dokima "Feature with --add in the name": positional, not parsed as subcommand
    - dokima unknown-subcommand: argparse error with "invalid choice" message
    - dokima "Feature" --map: map flag on default path still works
    - dokima fix --skip-autofix: fix subcommand accepts its flags correctly
    
    Failure Modes
    - argparse parse failure: exits 2 with usage message (argparse default)
    - Subcommand handler raises exception: crash is identical to before — handlers are unchanged
    - dokima next without AGENTS.md: same error as before
    - dokima release in non-git dir: same error as before
    - Ctrl-C during subcommand: SIGINT handling unchanged
    - dokima list-crons with extra arg: argparse rejects cleanly
    
    Contract Invariants
    - All handler functions (handle_status, handle_stop, handle_kill, handle_list_crons, show_help, show_help_json, check_upgrade, do_release, run_add_to_roadmap, run_next_setup, run_fix_mode, run_init) retain identical signatures and behavior
    - FORCE_FULL, SKIP_AUTOFIX, SKIP_HUMAN_GATE, RESUME, max_parallel_override globals are set identically — only the assignment source changes
    - --help-json output format: same structure, only command name and syntax fields change
    - dokima "Feature" [dir] default path: completely unchanged behavior
    - Test count: 755 tests must still pass (749 passed + 6 skipped, same count)
    
    11. Panel Split
    
    Wave 1 (serial bottleneck):
    - Task 1: argparse refactor in dokima
    
    Wave 2 (all parallel — each task touches different files):
    - Task 2: HELP_TEXT + CLI_METADATA in utils.py (merged, sequential to avoid file conflict)
    - Tasks 3-16: all test/doc/roadmap updates — each touches different files, fully parallelizable
    
    Wave 3 (serial — final verification):
    - Task 17: Run full test suite and fix failures
    
    Coder agents needed: 2-4 (Wave 1: 1 agent, Wave 2: up to 4 parallel agents for test/doc files, Wave 3: 1 agent)
    
    12. Build & Deploy
    
    - Deploy: No deployment — dokima is a local script. install.sh unchanged (only --help reference, stays).
    - CI: python3 -m pytest tests/ -q must pass with 755 tests (749 passed + 6 skipped)
    - Env vars: No new env vars. All existing PANEL_* vars continue to work as env fallbacks.
    - Release: dokima release patch (the new invocation) must still work for releasing this change.
    
    13. Risk Register
    
    Risk 1: argparse changes argv parsing order — --help-json before subcommand may break
    Severity: MEDIUM
    Mitigation: Test dokima --help-json version explicitly; argparse parent parser handles this
    Trigger: Test failure
    
    Risk 2: Hyphenated subcommand list-crons may confuse argparse dest naming
    Severity: LOW
    Mitigation: Argparse converts list-crons → list_crons dest; verify with explicit dest=
    Trigger: Test failure
    
    Risk 3: dokima "Feature with --flags" positional overlapping subcommand parsing
    Severity: LOW
    Mitigation: Argparse stops at first positional or subcommand; test confirms
    Trigger: User report
    
    Risk 4: CI scripts / cron jobs using old --flag syntax break silently
    Severity: HIGH
    Mitigation: Search all cron jobs, CI configs, and scripts BEFORE merge; document migration
    Trigger: Cron job failure
    
    Risk 5: dokima --continuous as separate flag breaks — now dokima next --continuous
    Severity: MEDIUM
    Mitigation: Document migration prominently; consider alias/backcompat for 1 release cycle
    Trigger: User confusion
    
    Risk 6: Test assertions about help text format fail on subcommand syntax
    Severity: LOW
    Mitigation: All test updates included in tasks 3-16; final test run catches stragglers
    Trigger: Test failure
    
    Risk 7: MAINTAINERS.md test suite map references old flag syntax in test file descriptions
    Severity: LOW
    Mitigation: Task 13 covers MAINTAINERS.md updates; verify test file names and descriptions
    Trigger: Documentation drift
    
    14. Anti-Creep
    
    Features explicitly NOT in scope:
    - NO backward compatibility shims (--add aliases). Clean break.
    - NO new subcommands beyond the 10 listed. --map stays a flag, not a subcommand.
    - NO plugin system or dynamic subcommand discovery.
    - NO shell completion generation (that's a separate feature).
    - NO changes to handler function internals — pure dispatch refactor.
    - NO changes to install.sh beyond updating --help references (if any). Verified: only --help which stays.
    - NO changes to dokima init — it's already a positional argument, stays that way.
    - NO nested subcommands (dokima release create vs dokima release). Flat structure only.
    - NO dokima --map → dokima map — map stays as a flag per scope.
    - NO changes to the Hermes Agent profile spawning or skill loading — pure CLI dispatch.
    
    15. Sign-Off Checklist
    
    - [ ] argparse subparser design reviewed — all 10 subcommands accounted for
    - [ ] --continuous decision confirmed: flag on next subcommand, not standalone
    - [ ] --help-json confirmed as top-level flag (not subcommand)
    - [ ] --map confirmed staying as flag (not subcommand-ized)
    - [ ] ALL cron job references searched and migration plan ready
    - [ ] CI scripts (GitHub Actions, if any) searched for old flag syntax
    - [ ] Backward compatibility decision: CLEAN BREAK, no aliases — confirmed
    - [ ] Test plan reviewed — 755 tests (749 passed + 6 skipped) must pass after changes
    - [ ] README/MAINTAINERS.md update scope confirmed (lines documented in Tasks 12-13)
    - [ ] docs/setup.md and docs/pipeline.md verified — only --help/--answers references, both unchanged
    - [ ] install.sh verified — only --help reference at L121, unchanged
    - [ ] Release plan: this feature itself will be released with dokima release patch (new syntax)
    - [ ] No shell injection risk from argparse (stdlib, proven safe)
    - [ ] All handler function signatures confirmed unchanged