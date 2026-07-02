"""Tests for HELP_TEXT completeness and F030 subcommand syntax migration."""
import json


def test_help_text_documents_panel_max_parallel(panel):
    """PANEL_MAX_PARALLEL env var should be documented in HELP_TEXT
    alongside --max-parallel=N."""
    assert "PANEL_MAX_PARALLEL" in panel.HELP_TEXT, (
        "PANEL_MAX_PARALLEL should be documented in HELP_TEXT "
        "since --max-parallel=N already is"
    )


# ── F030: Subcommand syntax migration ───────────────────────────────

class TestHelpTextSubcommandSyntax:
    """HELP_TEXT must use subcommand syntax (dokima <cmd>), not old --flag forms."""

    def test_add_is_subcommand_not_flag(self, panel):
        """dokima add, not dokima --add."""
        ht = panel.HELP_TEXT
        assert "dokima add" in ht, "HELP_TEXT must show 'dokima add' subcommand"
        assert "dokima --add" not in ht, "HELP_TEXT must NOT show old 'dokima --add'"

    def test_next_is_subcommand_not_flag(self, panel):
        """dokima next, not dokima --next."""
        ht = panel.HELP_TEXT
        assert "dokima next" in ht, "HELP_TEXT must show 'dokima next' subcommand"
        assert "dokima --next" not in ht, "HELP_TEXT must NOT show old 'dokima --next'"

    def test_fix_is_subcommand_not_flag(self, panel):
        """dokima fix, not dokima --fix."""
        ht = panel.HELP_TEXT
        assert "dokima fix" in ht, "HELP_TEXT must show 'dokima fix' subcommand"
        assert "dokima --fix" not in ht, "HELP_TEXT must NOT show old 'dokima --fix'"

    def test_continuous_is_flag_not_command(self, panel):
        """dokima --continuous should not appear as a standalone command.
        The --continuous flag now attaches to 'dokima next'."""
        ht = panel.HELP_TEXT
        assert "dokima --continuous" not in ht, (
            "HELP_TEXT must NOT show 'dokima --continuous' as standalone command"
        )
        assert "--continuous" in ht, (
            "HELP_TEXT should still reference the --continuous flag"
        )

    def test_status_is_subcommand_not_flag(self, panel):
        """dokima status, not dokima --status."""
        ht = panel.HELP_TEXT
        assert "dokima status" in ht, "HELP_TEXT must show 'dokima status' subcommand"
        assert "dokima --status" not in ht, "HELP_TEXT must NOT show old 'dokima --status'"

    def test_stop_is_subcommand_not_flag(self, panel):
        """dokima stop, not dokima --stop."""
        ht = panel.HELP_TEXT
        assert "dokima stop" in ht, "HELP_TEXT must show 'dokima stop' subcommand"
        assert "dokima --stop" not in ht, "HELP_TEXT must NOT show old 'dokima --stop'"

    def test_kill_is_subcommand_not_flag(self, panel):
        """dokima kill, not dokima --kill."""
        ht = panel.HELP_TEXT
        assert "dokima kill" in ht, "HELP_TEXT must show 'dokima kill' subcommand"
        assert "dokima --kill" not in ht, "HELP_TEXT must NOT show old 'dokima --kill'"

    def test_list_crons_is_subcommand_not_flag(self, panel):
        """dokima list-crons, not dokima --list-crons."""
        ht = panel.HELP_TEXT
        assert "dokima list-crons" in ht, "HELP_TEXT must show 'dokima list-crons' subcommand"
        assert "dokima --list-crons" not in ht, "HELP_TEXT must NOT show old 'dokima --list-crons'"

    def test_version_is_subcommand_not_flag(self, panel):
        """dokima version, not dokima --version."""
        ht = panel.HELP_TEXT
        assert "dokima version" in ht, "HELP_TEXT must show 'dokima version' subcommand"
        assert "dokima --version" not in ht, "HELP_TEXT must NOT show old 'dokima --version'"

    def test_upgrade_is_subcommand_not_flag(self, panel):
        """dokima upgrade, not dokima --upgrade."""
        ht = panel.HELP_TEXT
        assert "dokima upgrade" in ht, "HELP_TEXT must show 'dokima upgrade' subcommand"
        assert "dokima --upgrade" not in ht, "HELP_TEXT must NOT show old 'dokima --upgrade'"

    def test_release_is_subcommand_not_flag(self, panel):
        """dokima release, not dokima --release. Already correct but verify."""
        ht = panel.HELP_TEXT
        assert "dokima release" in ht, "HELP_TEXT must show 'dokima release' subcommand"


class TestCliMetadataSubcommandNames:
    """CLI_METADATA command names must be bare subcommands, no -- prefix."""

    SUBCOMMAND_NAMES = [
        ("add", "Add feature to roadmap"),
        ("next", "Build next feature from roadmap"),
        ("fix", "Fix BLOCKED PR"),
        ("status", "Show pipeline state"),
        ("stop", "Graceful stop"),
        ("kill", "Emergency kill"),
        ("list-crons", "List all scheduled pipelines"),
        ("version", "Print version and exit"),
        ("upgrade", "Check for newer version"),
        ("release", "Bump version"),
    ]

    @staticmethod
    def _get_commands_dict():
        """Return a dict mapping command name -> command entry."""
        import utils
        cmds = utils.CLI_METADATA.get("commands", [])
        return {c["name"]: c for c in cmds}

    def test_no_dash_prefix_in_command_names(self, panel):
        """No CLI_METADATA command name should start with '--'."""
        cmd_dict = self._get_commands_dict(panel)
        bad = [name for name in cmd_dict if name.startswith("--")]
        assert not bad, (
            f"CLI_METADATA command names must not use -- prefix: {bad}"
        )

    def test_all_subcommands_present(self, panel):
        """All 10 subcommands must be in CLI_METADATA by bare name."""
        cmd_dict = self._get_commands_dict(panel)
        for name, desc_hint in self.SUBCOMMAND_NAMES:
            assert name in cmd_dict, (
                f"CLI_METADATA must include '{name}' command"
            )

    def test_init_is_subcommand(self, panel):
        """init should already be a bare subcommand name in CLI_METADATA."""
        cmd_dict = self._get_commands_dict(panel)
        assert "init" in cmd_dict, "CLI_METADATA must include 'init' command"

    def test_run_is_subcommand(self, panel):
        """Default pipeline run should be a bare name in CLI_METADATA."""
        cmd_dict = self._get_commands_dict(panel)
        assert "run" in cmd_dict, "CLI_METADATA must include 'run' command"


class TestHelpTextExamples:
    """EXAMPLES section should use new subcommand syntax."""

    def test_examples_use_add_not_flag(self, panel):
        """Example must use 'dokima add' not 'dokima --add'."""
        ht = panel.HELP_TEXT
        assert "dokima add" in ht, "EXAMPLES must use 'dokima add'"
        assert "dokima --add" not in ht, "EXAMPLES must NOT use 'dokima --add'"

    def test_examples_use_next_not_flag(self, panel):
        """Example must use 'dokima next' not 'dokima --next'."""
        ht = panel.HELP_TEXT
        assert "dokima next" in ht, "EXAMPLES must use 'dokima next'"
        assert "dokima --next" not in ht, "EXAMPLES must NOT use 'dokima --next'"

    def test_examples_use_fix_not_flag(self, panel):
        """Example must use 'dokima fix' not 'dokima --fix'."""
        ht = panel.HELP_TEXT
        assert "dokima fix" in ht, "EXAMPLES must use 'dokima fix'"
        assert "dokima --fix" not in ht, "EXAMPLES must NOT use 'dokima --fix'"

    def test_examples_use_status_not_flag(self, panel):
        """Example must use 'dokima status' not 'dokima --status'."""
        ht = panel.HELP_TEXT
        assert "dokima status" in ht, "EXAMPLES must use 'dokima status'"
        assert "dokima --status" not in ht, "EXAMPLES must NOT use 'dokima --status'"
