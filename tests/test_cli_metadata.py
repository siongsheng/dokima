"""Tests for CLI_METADATA subcommand structure (F030 Task 3)."""
import sys
import os
import json

# Ensure the project root is on the path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils


# ═══════════════════════════════════════════════════════════════════
# CLI_METADATA structure tests
# ═══════════════════════════════════════════════════════════════════

def test_cli_metadata_is_dict():
    """CLI_METADATA should be a dict."""
    assert isinstance(utils.CLI_METADATA, dict)


def test_cli_metadata_has_required_keys():
    """CLI_METADATA should have expected top-level keys."""
    assert "tool" in utils.CLI_METADATA
    assert "version" in utils.CLI_METADATA
    assert "commands" in utils.CLI_METADATA
    assert "flags" in utils.CLI_METADATA
    assert "env_vars" in utils.CLI_METADATA
    assert utils.CLI_METADATA["tool"] == "dokima"


def test_cli_metadata_commands_is_list():
    """CLI_METADATA commands should be a list."""
    assert isinstance(utils.CLI_METADATA["commands"], list)


# ═══════════════════════════════════════════════════════════════════
# Subcommand structure: no -- prefix on command names
# ═══════════════════════════════════════════════════════════════════

EXPECTED_SUBCOMMANDS = {
    "run", "init", "add", "next", "continuous", "fix", "status",
    "stop", "kill", "list-crons", "version", "upgrade", "release",
    "map", "help",
}


def test_all_commands_are_subcommands_no_flag_prefix():
    """No command name should start with '--' — they are now subcommands."""
    for cmd in utils.CLI_METADATA["commands"]:
        name = cmd["name"]
        assert not name.startswith("--"), (
            f"Command '{name}' should not start with '--'; "
            f"F030 subcommand redesign removes -- prefix from commands"
        )


def test_all_expected_subcommands_present():
    """All expected subcommands should be in CLI_METADATA.commands."""
    names = {cmd["name"] for cmd in utils.CLI_METADATA["commands"]}
    missing = EXPECTED_SUBCOMMANDS - names
    assert not missing, f"Missing subcommands: {missing}"


def test_no_extra_unknown_subcommands():
    """CLI_METADATA.commands should not contain unexpected entries."""
    names = {cmd["name"] for cmd in utils.CLI_METADATA["commands"]}
    unexpected = names - EXPECTED_SUBCOMMANDS
    assert not unexpected, f"Unexpected subcommands: {unexpected}"


def test_all_commands_have_subcommand_field_true():
    """Every command entry should have 'subcommand': true."""
    for cmd in utils.CLI_METADATA["commands"]:
        assert "subcommand" in cmd, (
            f"Command '{cmd['name']}' missing 'subcommand' field"
        )
        assert cmd["subcommand"] is True, (
            f"Command '{cmd['name']}' should have 'subcommand': true, "
            f"got {cmd['subcommand']!r}"
        )


def test_each_command_has_name_syntax_description():
    """Every command entry should have name, syntax, and description."""
    for cmd in utils.CLI_METADATA["commands"]:
        assert "name" in cmd
        assert "syntax" in cmd
        assert "description" in cmd
        assert isinstance(cmd["name"], str)
        assert isinstance(cmd["syntax"], str)
        assert isinstance(cmd["description"], str)
        assert len(cmd["name"]) > 0
        assert len(cmd["syntax"]) > 0
        assert len(cmd["description"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Flags: still -- prefixed (unchanged)
# ═══════════════════════════════════════════════════════════════════

def test_flags_still_have_flag_prefix():
    """Flags should still use -- prefix (F030 only converts operations to subcommands)."""
    for flag in utils.CLI_METADATA["flags"]:
        assert flag["flag"].startswith("--"), (
            f"Flag '{flag['flag']}' should start with '--'"
        )


# ═══════════════════════════════════════════════════════════════════
# show_help_json tests
# ═══════════════════════════════════════════════════════════════════

def test_show_help_json_exists():
    """show_help_json should be defined in utils."""
    assert hasattr(utils, "show_help_json")
    assert callable(utils.show_help_json)


def test_cli_metadata_is_valid_json():
    """CLI_METADATA should be JSON-serializable (exercises show_help_json path)."""
    serialized = json.dumps(utils.CLI_METADATA, indent=2)
    assert isinstance(serialized, str)
    assert len(serialized) > 0


# ═══════════════════════════════════════════════════════════════════
# KEEP IN SYNC comment check
# ═══════════════════════════════════════════════════════════════════

def test_sync_comment_present():
    """The KEEP IN SYNC comment must be present above CLI_METADATA."""
    import inspect
    source = inspect.getsource(utils)
    # The comment should appear near CLI_METADATA
    assert "KEEP IN SYNC" in source, (
        "KEEP IN SYNC comment missing from utils.py"
    )
