# Task Breakdown: F030: CLI redesign: replace --add/--next/--fix/--status/--stop/--kill/--list-crons/--version/--upgrade/--release with proper subcommands (dokima add, dokima next, etc). Flags (--force-full, --max-parallel) keep -- prefix. Update all tests, scripts, AGENTS.md, roadmap, and docs.

### Task 1: Replace flag-scanning loop with argparse subparsers in dokima entry point
**Files:** dokima
**Dependencies:** [none]
**Description:** Replace flag-scanning loop with argparse subparsers in dokima entry point

### Task 2: Update HELP_TEXT and CLI_METADATA in utils.py for subcommand syntax
**Files:** utils.py
**Dependencies:** 1
**Description:** Update HELP_TEXT and CLI_METADATA in utils.py for subcommand syntax

### Task 3: Update test_f021_version.py for subcommand dispatch
**Files:** tests/test_f021_version.py
**Dependencies:** 1
**Description:** Update test_f021_version.py for subcommand dispatch

### Task 4: Update test_f020_help_json.py for subcommand names
**Files:** tests/test_f020_help_json.py
**Dependencies:** 2
**Description:** Update test_f020_help_json.py for subcommand names

### Task 5: Update test_control_panel.py for subcommand handler names
**Files:** tests/test_control_panel.py
**Dependencies:** 1
**Description:** Update test_control_panel.py for subcommand handler names

### Task 6: Update test_f024_release.py for dokima release subcommand
**Files:** tests/test_f024_release.py
**Dependencies:** 1
**Description:** Update test_f024_release.py for dokima release subcommand

### Task 7: Update test_main_integration.py for dokima next subcommand
**Files:** tests/test_main_integration.py
**Dependencies:** 1
**Description:** Update test_main_integration.py for dokima next subcommand

### Task 8: Update test_fix_mode.py for dokima fix subcommand
**Files:** tests/test_fix_mode.py
**Dependencies:** 1
**Description:** Update test_fix_mode.py for dokima fix subcommand

### Task 9: Update test_edge_cases.py for dokima next subcommand
**Files:** tests/test_edge_cases.py
**Dependencies:** 1
**Description:** Update test_edge_cases.py for dokima next subcommand

### Task 10: Update test_final_edge.py and test_final_coverage.py for --continuous → next --continuous
**Files:** tests/test_final_edge.py, tests/test_final_coverage.py
**Dependencies:** 1
**Description:** Update test_final_edge.py and test_final_coverage.py for --continuous → next --continuous

### Task 11: Update remaining test files (rich_pipeline, pipeline_integration, continuous, installer)
**Files:** tests/test_rich_pipeline.py, tests/test_pipeline_integration.py, tests/test_continuous.py, tests/test_installer.py
**Dependencies:** 1
**Description:** Update remaining test files (rich_pipeline, pipeline_integration, continuous, installer)

### Task 12: Update README.md examples
**Files:** README.md
**Dependencies:** 1
**Description:** Update README.md examples

### Task 13: Update MAINTAINERS.md command references
**Files:** MAINTAINERS.md
**Dependencies:** 1
**Description:** Update MAINTAINERS.md command references

### Task 14: Update docs/ references (setup.md, pipeline.md) and install.sh
**Files:** docs/setup.md, docs/pipeline.md, install.sh
**Dependencies:** 1
**Description:** Update docs/ references (setup.md, pipeline.md) and install.sh

### Task 15: Update AGENTS.md (verify clean)
**Files:** AGENTS.md
**Dependencies:** 1
**Description:** Update AGENTS.md (verify clean)

### Task 16: Update specs/roadmap.md F030 description
**Files:** specs/roadmap.md
**Dependencies:** 1
**Description:** Update specs/roadmap.md F030 description

### Task 17: Run full test suite and fix failures
**Files:** (any failing test file)
**Dependencies:** 1, 16
**Description:** Run full test suite and fix failures
