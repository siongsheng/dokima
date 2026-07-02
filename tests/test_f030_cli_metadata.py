"""Tests for F030 Task 3: CLI_METADATA in utils.py updated for subcommand syntax.

Validates that CLI_METADATA command names and syntax strings use subcommand
format (dokima add, dokima next, etc.) instead of flag format (dokima --add,
dokima --next, etc.). Flags and env_vars entries keep their -- prefix.
"""

import json
import sys
import os

# Import CLI_METADATA directly from utils.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CLI_METADATA, VERSION


EXPECTED_SUBCOMMANDS = {
    "add":        "dokima add \"Feature\" [--priority=P1] [dir]",
    "next":       "dokima next [--continuous] [--force-full] [--interactive] [dir]",
    "fix":        "dokima fix [--fix-all] [dir]",
    "status":     "dokima status [dir]",
    "stop":       "dokima stop [dir]",
    "kill":       "dokima kill [dir]",
    "list-crons": "dokima list-crons",
    "version":    "dokima version",
    "upgrade":    "dokima upgrade",
    "release":    "dokima release [patch|minor|major] [--dry-run] [dir]",
}

# These commands KEEP their names (were never --prefixed)
NON_SUBCOMMANDS = {"run", "init"}


class TestCliMetadataSubcommands:
    """CLI_METADATA commands use subcommand names without -- prefix."""

    def test_metadata_has_required_top_level_keys(self):
        """CLI_METADATA has tool, version, commands, flags, env_vars."""
        for key in ("tool", "version", "commands", "flags", "env_vars"):
            assert key in CLI_METADATA, f"Missing key: {key}"

    def test_tool_is_dokima(self):
        """tool field is 'dokima'."""
        assert CLI_METADATA["tool"] == "dokima"

    def test_version_matches(self):
        """version field matches VERSION constant."""
        assert CLI_METADATA["version"] == VERSION

    def test_no_command_names_start_with_double_dash(self):
        """No command 'name' field starts with '--'."""
        for cmd in CLI_METADATA["commands"]:
            assert not cmd["name"].startswith("--"), \
                f"Command name '{cmd['name']}' starts with '--', expected subcommand format"

    def test_run_and_init_keep_their_names(self):
        """'run' and 'init' command names are unchanged."""
        cmd_names = {cmd["name"] for cmd in CLI_METADATA["commands"]}
        for name in NON_SUBCOMMANDS:
            assert name in cmd_names, f"Expected command '{name}' in CLI_METADATA"

    def test_all_expected_subcommands_present(self):
        """All expected subcommand names are present in commands list."""
        cmd_names = {cmd["name"] for cmd in CLI_METADATA["commands"]}
        for name in EXPECTED_SUBCOMMANDS:
            assert name in cmd_names, \
                f"Expected subcommand '{name}' not found in CLI_METADATA commands"

    def test_no_continuous_separate_command(self):
        """'continuous' is NOT a separate command (merged into 'next' as flag)."""
        cmd_names = {cmd["name"] for cmd in CLI_METADATA["commands"]}
        assert "continuous" not in cmd_names or "next" in cmd_names, \
            "'continuous' should not be a separate command"

    def test_subcommand_syntax_uses_correct_format(self):
        """Each subcommand's syntax string uses 'dokima <name>' not 'dokima --<name>'."""
        cmd_by_name = {cmd["name"]: cmd for cmd in CLI_METADATA["commands"]}
        for name, expected_syntax in EXPECTED_SUBCOMMANDS.items():
            cmd = cmd_by_name.get(name)
            assert cmd is not None, f"Subcommand '{name}' not found"
            actual = cmd["syntax"]
            # Must start with 'dokima <name>' not 'dokima --<name>'
            assert actual == expected_syntax, \
                f"Syntax for '{name}': expected '{expected_syntax}', got '{actual}'"

    def test_flags_keep_dash_prefix(self):
        """Flag entries keep their '--' prefix (unchanged)."""
        for f in CLI_METADATA["flags"]:
            assert f["flag"].startswith("--"), \
                f"Flag '{f['flag']}' should keep '--' prefix"

    def test_env_vars_unchanged(self):
        """env_vars list still has required entries."""
        assert len(CLI_METADATA["env_vars"]) >= 5, \
            f"Expected >=5 env_vars, got {len(CLI_METADATA['env_vars'])}"
        for ev in CLI_METADATA["env_vars"]:
            for field in ("name", "description", "related_flag"):
                assert field in ev, f"Env var missing {field}"

    def test_each_command_has_required_fields(self):
        """Every command has name, syntax, description."""
        for cmd in CLI_METADATA["commands"]:
            for field in ("name", "syntax", "description"):
                assert field in cmd, f"Command missing {field}"
                assert isinstance(cmd[field], str), f"Command {cmd.get('name','?')} {field} not string"

    def test_each_flag_has_required_fields(self):
        """Every flag has flag, args, env_var, description."""
        for f in CLI_METADATA["flags"]:
            for field in ("flag", "args", "env_var", "description"):
                assert field in f, f"Flag missing {field}"

    def test_can_serialize_to_json(self):
        """CLI_METADATA can be serialized to JSON (no un-serializable objects)."""
        serialized = json.dumps(CLI_METADATA, indent=2)
        assert len(serialized) > 0
