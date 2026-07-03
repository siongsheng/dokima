"""RED tests for Task 3 — CLI_METADATA uses subcommand names (will FAIL until updated)."""
import json
import subprocess
import os
import sys

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")


def _run(*args):
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=10,
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def test_cli_metadata_commands_use_subcommand_names():
    """--help-json command names use 'version' not '--version', 'add' not '--add'."""
    rc, out, err = _run("--help-json")
    assert rc == 0, f"rc={rc}, err={err}"
    data = json.loads(out)
    cmd_names = {c["name"] for c in data["commands"]}
    # Subcommand names (no -- prefix)
    for name in ("add", "next", "fix", "status", "stop", "kill",
                 "list-crons", "version", "upgrade", "release"):
        assert name in cmd_names, f"Expected '{name}' in commands, got {cmd_names}"
    # Old flag names should NOT appear
    for old_name in ("--add", "--next", "--fix", "--status", "--stop",
                     "--kill", "--list-crons", "--version", "--upgrade", "--release"):
        assert old_name not in cmd_names, f"Old flag '{old_name}' should NOT appear: {cmd_names}"


def test_cli_metadata_syntax_uses_subcommand_format():
    """--help-json syntax strings use 'dokima add' not 'dokima --add'."""
    rc, out, err = _run("--help-json")
    assert rc == 0
    data = json.loads(out)
    for cmd in data["commands"]:
        syntax = cmd.get("syntax", "")
        name = cmd.get("name", "")
        if name in ("add", "next", "fix", "status", "stop", "kill",
                     "list-crons", "version", "upgrade", "release"):
            assert not syntax.startswith("dokima --"), \
                f"Command '{name}' has old flag syntax: {syntax}"
