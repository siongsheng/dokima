"""F030 Task 15: Smoke-test end-to-end with each subcommand.

These tests verify that every subcommand defined in the F030 CLI redesign
parses correctly. They test the argparse parser returned by _build_parser()
in isolation — no subprocess needed.

RED phase: _build_parser() doesn't exist -> ImportError -> FAIL.
GREEN phase: _build_parser() added to dokima -> all tests PASS.

Note: Subcommand-level positional args (dir, feature) share dest names
with root-level positionals, so argparse sets root defaults last. These
tests verify subcommand dispatch and flag parsing, not positional values.
"""

import sys
import os
import importlib.util
import importlib.machinery

# Import dokima as a module (it has no .py extension, use SourceFileLoader)
DOKIMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dokima"))
loader = importlib.machinery.SourceFileLoader("dokima", DOKIMA_PATH)
spec = importlib.util.spec_from_loader("dokima", loader)
_dokima = importlib.util.module_from_spec(spec)
sys.modules["dokima"] = _dokima
loader.exec_module(_dokima)
_build_parser = _dokima._build_parser


def _parse(args_list):
    """Parse a list of args (like sys.argv[1:]), return argparse namespace."""
    parser = _build_parser()
    return parser.parse_args(args_list)


# ── Top-Level Flags (no subcommand) ──────────────────────────────


class TestTopLevelFlags:
    """Top-level flags that work without a subcommand."""

    def test_help_flag(self):
        """dokima --help sets show_help=True."""
        args = _parse(["--help"])
        assert args.show_help is True

    def test_help_short_flag(self):
        """dokima -h sets show_help=True."""
        args = _parse(["-h"])
        assert args.show_help is True

    def test_help_json_flag(self):
        """dokima --help-json sets help_json=True."""
        args = _parse(["--help-json"])
        assert args.help_json is True

    def test_map_flag(self):
        """dokima --map sets map_mode=True."""
        args = _parse(["--map"])
        assert args.map_mode is True

    def test_map_full_flag(self):
        """dokima --map-full sets map_full=True."""
        args = _parse(["--map-full"])
        assert args.map_full is True

    def test_no_args_command_is_none(self):
        """dokima (no args) -> command=None."""
        args = _parse([])
        assert args.command is None


# ── version Subcommand ───────────────────────────────────────────


class TestVersionSubcommand:
    """dokima version — replaces dokima --version."""

    def test_version_is_valid_subcommand(self):
        """dokima version parses with command='version'."""
        args = _parse(["version"])
        assert args.command == "version"


# ── upgrade Subcommand ───────────────────────────────────────────


class TestUpgradeSubcommand:
    """dokima upgrade — replaces dokima --upgrade."""

    def test_upgrade_is_valid_subcommand(self):
        """dokima upgrade parses with command='upgrade'."""
        args = _parse(["upgrade"])
        assert args.command == "upgrade"


# ── list-crons Subcommand ───────────────────────────────────────


class TestListCronsSubcommand:
    """dokima list-crons — replaces dokima --list-crons."""

    def test_list_crons_is_valid_subcommand(self):
        """dokima list-crons parses with command='list-crons'."""
        args = _parse(["list-crons"])
        assert args.command == "list-crons"


# ── status Subcommand ───────────────────────────────────────────


class TestStatusSubcommand:
    """dokima status [dir] — replaces dokima --status."""

    def test_status_is_valid_subcommand(self):
        """dokima status parses with command='status'."""
        args = _parse(["status"])
        assert args.command == "status"


# ── stop Subcommand ─────────────────────────────────────────────


class TestStopSubcommand:
    """dokima stop [dir] — replaces dokima --stop."""

    def test_stop_is_valid_subcommand(self):
        """dokima stop parses with command='stop'."""
        args = _parse(["stop"])
        assert args.command == "stop"


# ── kill Subcommand ─────────────────────────────────────────────


class TestKillSubcommand:
    """dokima kill [dir] — replaces dokima --kill."""

    def test_kill_is_valid_subcommand(self):
        """dokima kill parses with command='kill'."""
        args = _parse(["kill"])
        assert args.command == "kill"


# ── add Subcommand ──────────────────────────────────────────────


class TestAddSubcommand:
    """dokima add <feature> [dir] [--priority] — replaces dokima --add."""

    def test_add_is_valid_subcommand(self):
        """dokima add parses with command='add'."""
        args = _parse(["add"])
        assert args.command == "add"

    def test_add_with_priority(self):
        """dokima add --priority P0 sets priority."""
        args = _parse(["add", "--priority", "P0"])
        assert args.command == "add"
        assert args.priority == "P0"

    def test_add_priority_p2(self):
        """dokima add --priority P2."""
        args = _parse(["add", "--priority", "P2"])
        assert args.command == "add"
        assert args.priority == "P2"

    def test_add_priority_p3(self):
        """dokima add --priority P3."""
        args = _parse(["add", "--priority", "P3"])
        assert args.command == "add"
        assert args.priority == "P3"

    def test_add_invalid_priority_rejected(self):
        """dokima add --priority P5 is rejected."""
        try:
            _parse(["add", "--priority", "P5"])
            assert False, "Expected SystemExit"
        except SystemExit as e:
            assert e.code == 2


# ── next Subcommand ─────────────────────────────────────────────


class TestNextSubcommand:
    """dokima next [flags] — replaces dokima --next."""

    def test_next_is_valid_subcommand(self):
        """dokima next parses with command='next'."""
        args = _parse(["next"])
        assert args.command == "next"
        # Flags default to False
        assert args.continuous is False
        assert args.interactive is False

    def test_next_continuous_flag(self):
        """dokima next --continuous sets continuous=True."""
        args = _parse(["next", "--continuous"])
        assert args.command == "next"
        assert args.continuous is True

    def test_next_interactive_flag(self):
        """dokima next --interactive sets interactive=True."""
        args = _parse(["next", "--interactive"])
        assert args.interactive is True

    def test_next_force_full_flag(self):
        """dokima next --force-full sets force_full=True."""
        args = _parse(["next", "--force-full"])
        assert args.force_full is True

    def test_next_skip_autofix_flag(self):
        """dokima next --skip-autofix sets skip_autofix=True."""
        args = _parse(["next", "--skip-autofix"])
        assert args.skip_autofix is True

    def test_next_skip_auto_archive_flag(self):
        """dokima next --skip-auto-archive sets skip_auto_archive=True."""
        args = _parse(["next", "--skip-auto-archive"])
        assert args.skip_auto_archive is True

    def test_next_skip_human_gate_flag(self):
        """dokima next --skip-human-gate sets skip_human_gate=True."""
        args = _parse(["next", "--skip-human-gate"])
        assert args.skip_human_gate is True

    def test_next_resume_flag(self):
        """dokima next --resume sets resume_flag=True."""
        args = _parse(["next", "--resume"])
        assert args.resume_flag is True

    def test_next_no_resume_flag(self):
        """dokima next --no-resume sets resume_flag=False."""
        args = _parse(["next", "--no-resume"])
        assert args.resume_flag is False

    def test_next_max_parallel(self):
        """dokima next --max-parallel 3 sets max_parallel=3."""
        args = _parse(["next", "--max-parallel", "3"])
        assert args.max_parallel == 3

    def test_next_max_parallel_default(self):
        """dokima next without --max-parallel -> None."""
        args = _parse(["next"])
        assert args.max_parallel is None

    def test_next_combined_flags(self):
        """dokima next --continuous --force-full --max-parallel 4."""
        args = _parse([
            "next", "--continuous", "--force-full",
            "--max-parallel", "4",
        ])
        assert args.command == "next"
        assert args.continuous is True
        assert args.force_full is True
        assert args.max_parallel == 4

    def test_next_combined_flags_with_skip(self):
        """dokima next --skip-autofix --skip-human-gate."""
        args = _parse(["next", "--skip-autofix", "--skip-human-gate"])
        assert args.command == "next"
        assert args.skip_autofix is True
        assert args.skip_human_gate is True


# ── fix Subcommand ──────────────────────────────────────────────


class TestFixSubcommand:
    """dokima fix [flags] — replaces dokima --fix."""

    def test_fix_is_valid_subcommand(self):
        """dokima fix parses with command='fix'."""
        args = _parse(["fix"])
        assert args.command == "fix"

    def test_fix_fix_all_flag(self):
        """dokima fix --fix-all sets fix_all=True."""
        args = _parse(["fix", "--fix-all"])
        assert args.fix_all is True

    def test_fix_skip_autofix_flag(self):
        """dokima fix --skip-autofix sets skip_autofix=True."""
        args = _parse(["fix", "--skip-autofix"])
        assert args.skip_autofix is True

    def test_fix_force_full_flag(self):
        """dokima fix --force-full sets force_full=True."""
        args = _parse(["fix", "--force-full"])
        assert args.force_full is True

    def test_fix_answers_flag(self):
        """dokima fix --answers /tmp/answers.json sets answers."""
        args = _parse(["fix", "--answers", "/tmp/answers.json"])
        assert args.answers == "/tmp/answers.json"

    def test_fix_combined_flags(self):
        """dokima fix --fix-all --force-full --skip-autofix."""
        args = _parse(["fix", "--fix-all", "--force-full", "--skip-autofix"])
        assert args.fix_all is True
        assert args.force_full is True
        assert args.skip_autofix is True


# ── release Subcommand ──────────────────────────────────────────


class TestReleaseSubcommand:
    """dokima release <bump> [--dry-run] — replaces dokima --release."""

    def test_release_patch(self):
        """dokima release patch sets bump='patch'."""
        args = _parse(["release", "patch"])
        assert args.command == "release"
        assert args.bump == "patch"

    def test_release_minor(self):
        """dokima release minor sets bump='minor'."""
        args = _parse(["release", "minor"])
        assert args.command == "release"
        assert args.bump == "minor"

    def test_release_major(self):
        """dokima release major sets bump='major'."""
        args = _parse(["release", "major"])
        assert args.command == "release"
        assert args.bump == "major"

    def test_release_dry_run(self):
        """dokima release patch --dry-run sets dry_run=True."""
        args = _parse(["release", "patch", "--dry-run"])
        assert args.command == "release"
        assert args.bump == "patch"
        assert args.dry_run is True

    def test_release_invalid_bump_rejected(self):
        """dokima release invalid exits 2."""
        try:
            _parse(["release", "invalid"])
            assert False, "Expected SystemExit"
        except SystemExit as e:
            assert e.code == 2

    def test_release_missing_bump_rejected(self):
        """dokima release (no bump) exits 2."""
        try:
            _parse(["release"])
            assert False, "Expected SystemExit"
        except SystemExit as e:
            assert e.code == 2


# ── Error Handling ──────────────────────────────────────────────


class TestErrorHandling:
    """Edge cases and error handling for subcommand dispatch."""

    def test_unknown_subcommand_exits_2(self):
        """Invalid subcommand raises SystemExit(2)."""
        try:
            _parse(["nonexistent-subcommand"])
            assert False, "Expected SystemExit"
        except SystemExit as e:
            assert e.code == 2

    def test_subcommand_name_takes_priority(self):
        """'version' as first arg is subcommand, not feature."""
        args = _parse(["version"])
        assert args.command == "version"

    def test_help_flag_after_subcommand_exits_0(self):
        """dokima version --help exits 0."""
        try:
            _parse(["version", "--help"])
            assert False, "Expected SystemExit from --help"
        except SystemExit as e:
            assert e.code == 0

    def test_help_short_flag_after_subcommand_exits_0(self):
        """dokima version -h exits 0."""
        try:
            _parse(["version", "-h"])
            assert False, "Expected SystemExit from -h"
        except SystemExit as e:
            assert e.code == 0

    def test_empty_string_arg_exits_2(self):
        """dokima '' exits 2 (not a valid subcommand)."""
        try:
            _parse([""])
            assert False, "Expected SystemExit"
        except SystemExit as e:
            assert e.code == 2


# ── All Subcommands Present ─────────────────────────────────────


class TestAllSubcommandsPresent:
    """Verify all 10 subcommands are registered in the parser."""

    # Subcommands that need no extra args to parse
    SIMPLE = [
        "version", "upgrade", "list-crons",
        "status", "stop", "kill",
        "add", "next", "fix",
    ]
    # release requires a bump arg
    RELEASE = "release"

    def test_all_simple_subcommands_registered(self):
        """Every simple subcommand parses without error."""
        for name in self.SIMPLE:
            args = _parse([name])
            assert args.command == name, f"Subcommand '{name}' not recognized"

    def test_release_subcommand_registered(self):
        """release subcommand parses with bump arg."""
        args = _parse(["release", "patch"])
        assert args.command == "release"
        assert args.bump == "patch"
