"""Tests for MAINTAINERS.md — CLI references use subcommand format.

F030: CLI redesign: replace --add/--next/--fix/--status/--stop/--kill/--list-crons/
--version/--upgrade/--release with proper subcommands.
Flags (--force-full, --max-parallel, etc.) keep -- prefix.
"""

import os
import re
import pytest


MAINTAINERS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "MAINTAINERS.md"
)


@pytest.fixture(scope="module")
def content():
    with open(MAINTAINERS_PATH) as f:
        return f.read()


# ── Subcommand presence: new format must appear ───────────────────

def test_common_commands_uses_subcommands(content):
    """Common Commands section uses `dokima next/add/fix/status` not `--flag`."""
    common_commands = content.split("## Common Commands")[1].split("\n##")[0]
    # Must use subcommand form for these operations
    assert "dokima next" in common_commands, "dokima next missing in Common Commands"
    assert "dokima add" in common_commands, "dokima add missing in Common Commands"
    assert "dokima fix" in common_commands, "dokima fix missing in Common Commands"
    assert "dokima status" in common_commands, "dokima status missing in Common Commands"


def test_common_commands_no_deprecated_flag_form(content):
    """Common Commands must NOT contain deprecated `dokima --flag` form."""
    common_commands = content.split("## Common Commands")[1].split("\n##")[0]
    # Code blocks only (between triple-backtick fences)
    code_blocks = re.findall(r"```(?:bash)?\n(.*?)```", common_commands, re.DOTALL)
    for block in code_blocks:
        for line in block.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # These flags that became subcommands must NOT appear as bare `dokima --flag`
            deprecated_flags = [
                "dokima --next",
                "dokima --add",
                "dokima --fix",
                "dokima --status",
                "dokima --stop",
                "dokima --kill",
                "dokima --list-crons",
                "dokima --version",
                "dokima --upgrade",
                "dokima --release",
            ]
            for df in deprecated_flags:
                assert df not in line, (
                    f"Deprecated flag form '{df}' found in Common Commands: '{line}'"
                )


def test_pipeline_cleanup_uses_subcommands(content):
    """Pipeline Cleanup section uses new CLI format."""
    cleanup_section = content.split("## Pipeline Cleanup")[1].split("\n##")[0]
    # Must not use `dokima --next`
    assert "dokima --next" not in cleanup_section, (
        "Pipeline Cleanup still uses deprecated `dokima --next`"
    )
    # Must use subcommand
    assert "dokima next" in cleanup_section, (
        "Pipeline Cleanup missing `dokima next` subcommand"
    )


# ── Flag references: -- force-full and other flags must stay ─────

def test_force_full_flag_in_depth_gating(content):
    """Depth Gating section still references --force-full flag."""
    depth_section = content.split("## Depth Gating Matrix")[1].split("\n##")[0]
    assert "--force-full" in depth_section, (
        "--force-full flag reference lost in Depth Gating section"
    )


def test_flags_not_converted_to_subcommands(content):
    """Flags that should remain as --flags are NOT converted to subcommands."""
    # --force-full, --fix-all, --max-parallel --skip-human-gate are flags, not subcommands
    assert "--force-full" in content, "Lost --force-full flag reference"
    assert "--max-parallel" in content, "Lost --max-parallel flag reference"


# ── Environment Variables table ───────────────────────────────────

def test_env_vars_table_has_flag_column(content):
    """Environment Variables table must mention both flag and env var."""
    env_section = content.split("## Environment Variables")[1].split("\n---")[0]
    # Must mention flag names alongside env vars
    assert "skip-human-gate" in env_section, (
        "Env var table missing --skip-human-gate flag reference"
    )
    assert "force-full" in env_section, (
        "Env var table missing --force-full flag reference"
    )
    assert "max-parallel" in env_section, (
        "Env var table missing --max-parallel flag reference"
    )


def test_env_vars_table_no_deprecated_panel_skip_orchestrator_review(content):
    """PANEL_SKIP_ORCHESTRATOR_REVIEW is deprecated — use PANEL_SKIP_HUMAN_GATE + --skip-human-gate."""
    env_section = content.split("## Environment Variables")[1].split("\n---")[0]
    assert "PANEL_SKIP_ORCHESTRATOR_REVIEW" not in env_section, (
        "Deprecated PANEL_SKIP_ORCHESTRATOR_REVIEW still in env vars table. "
        "Use --skip-human-gate / PANEL_SKIP_HUMAN_GATE instead."
    )


# ── Structural integrity ─────────────────────────────────────────

def test_maintainers_has_all_sections(content):
    """All expected sections are still present."""
    required_sections = [
        "Architecture at a Glance",
        "Key Functions by Phase",
        "Data Structures",
        "Model Profiles",
        "DeepSeek Model Quirks",
        "Regex Gotchas",
        "Pipeline Cleanup",
        "Key Files",
        "Test Suite Map",
        "Common Commands",
        "Depth Gating Matrix",
        "PR Conventions",
        "Known Bugs",
        "Environment Variables",
    ]
    for section in required_sections:
        assert f"## {section}" in content, f"Lost section: {section}"
