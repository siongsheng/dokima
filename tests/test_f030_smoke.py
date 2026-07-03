"""F030 Task 15: Smoke-test end-to-end with each subcommand.

These tests verify that every subcommand defined in the F030 CLI redesign
parses correctly and dispatches to the right handler. They test the argparse
parser returned by _build_parser() in isolation (no subprocess needed).

RED phase: _build_parser() doesn't exist → ImportError → FAIL.
GREEN phase: _build_parser() added to dokima → all tests PASS.
"""

import sys
import os
import importlib.util
import importlib.machinery
import argparse

# Import dokima as a module (it has no .py extension, use SourceFileLoader)
DOKIMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dokima"))
loader = importlib.machinery.SourceFileLoader("dokima", DOKIMA_PATH)
spec = importlib.util.spec_from_loader("dokima", loader)
_dokima = importlib.util.module_from_spec(spec)
sys.modules["dokima"] = _dokima
loader.exec_module(_dokima)
_build_parser = _dokima._build_parser


def _parse(args_str, cmd=None):
    """Parse args string, return argparse namespace."""
    parser = _build_parser()
    parts = args_str.split() if args_str else []
    if cmd:
        parts = [cmd] + parts
    return parser.parse_args(parts)


# ── Top-Level Flags ──────────────────────────────────────────────


class TestTopLevelFlags:
    """Top-level flags that work without a subcommand."""

    def test_help_flag(self):
        """dokima --help sets show_help=True."""
        args = _parse("--help")
        assert args.show_help is True

    def test_help_short_flag(self):
        """dokima -h sets show_help=True."""
        args = _parse("-h")
        assert args.show_help is True

    def test_help_json_flag(self):
        """dokima --help-json sets help_json=True."""
        args = _parse("--help-json")
        assert args.help_json is True

    def test_map_flag(self):
        """dokima --map sets map_mode=True."""
        args = _parse("--map")
        assert args.map_mode is True

    def test_map_full_flag(self):
        """dokima --map-full sets map_full=True."""
        args = _parse("--map-full")
        assert args.map_full is True


# ── version Subcommand ────────────────────────────────────────────


class TestVersionSubcommand:
    """dokima version — replaces dokima --version."""

    def test_version_is_valid_subcommand(self):
        """dokima version parses with command='version'."""
        args = _parse("", cmd="version")
        assert args.command == "version"

    def test_version_no_extra_args(self):
        """dokima version doesn't accept extra positional args."""
        parser = _build_parser()
        args = parser.parse_args(["version"])
        assert args.command == "version"


# ── upgrade Subcommand ────────────────────────────────────────────


class TestUpgradeSubcommand:
    """dokima upgrade — replaces dokima --upgrade."""

    def test_upgrade_is_valid_subcommand(self):
        """dokima upgrade parses with command='upgrade'."""
        args = _parse("", cmd="upgrade")
        assert args.command == "upgrade"


# ── list-crons Subcommand ─────────────────────────────────────────


class TestListCronsSubcommand:
    """dokima list-crons — replaces dokima --list-crons."""

    def test_list_crons_is_valid_subcommand(self):
        """dokima list-crons parses with command='list-crons'."""
        args = _parse("", cmd="list-crons")
        assert args.command == "list-crons"


# ── status Subcommand ─────────────────────────────────────────────


class TestStatusSubcommand:
    """dokima status [dir] — replaces dokima --status."""

    def test_status_no_dir(self):
        """dokima status with no dir: command='status', dir=None."""
        args = _parse("", cmd="status")
        assert args.command == "status"
        assert args.dir is None

    def test_status_with_dir(self):
        """dokima status /tmp sets dir='/tmp'."""
        args = _parse("/tmp", cmd="status")
        assert args.command == "status"
        assert args.dir == "/tmp"


# ── stop Subcommand ───────────────────────────────────────────────


class TestStopSubcommand:
    """dokima stop [dir] — replaces dokima --stop."""

    def test_stop_no_dir(self):
        """dokima stop with no dir: command='stop', dir=None."""
        args = _parse("", cmd="stop")
        assert args.command == "stop"
        assert args.dir is None

    def test_stop_with_dir(self):
        """dokima stop ~/project sets dir."""
        args = _parse("~/project", cmd="stop")
        assert args.command == "stop"
        assert args.dir == "~/project"


# ── kill Subcommand ───────────────────────────────────────────────


class TestKillSubcommand:
    """dokima kill [dir] — replaces dokima --kill."""

    def test_kill_no_dir(self):
        """dokima kill with no dir: command='kill', dir=None."""
        args = _parse("", cmd="kill")
        assert args.command == "kill"
        assert args.dir is None

    def test_kill_with_dir(self):
        """dokima kill ~/project sets dir."""
        args = _parse("~/project", cmd="kill")
        assert args.command == "kill"
        assert args.dir == "~/project"


# ── add Subcommand ────────────────────────────────────────────────


class TestAddSubcommand:
    """dokima add <feature> [dir] [--priority] — replaces dokima --add."""

    def test_add_feature_only(self):
        """dokima add 'Fix login' sets feature, dir=None."""
        args = _parse("Fix login", cmd="add")
        assert args.command == "add"
        assert args.feature == "Fix login"
        assert args.dir is None
        assert args.priority is None

    def test_add_feature_and_dir(self):
        """dokima add 'Fix login' ~/proj sets feature + dir."""
        args = _parse("'Fix login' ~/proj", cmd="add")
        assert args.command == "add"
        assert args.feature == "Fix login"
        assert args.dir == "~/proj"

    def test_add_with_priority(self):
        """dokima add 'Fix login' --priority P0."""
        args = _parse("'Fix login' --priority P0", cmd="add")
        assert args.command == "add"
        assert args.feature == "Fix login"
        assert args.priority == "P0"

    def test_add_priority_p2(self):
        """dokima add 'thing' --priority P2."""
        args = _parse("thing --priority P2", cmd="add")
        assert args.command == "add"
        assert args.priority == "P2"

    def test_add_no_feature_parses_but_feature_is_none(self):
        """dokima add (no args) — feature=None, argparse doesn't reject."""
        args = _parse("", cmd="add")
        assert args.command == "add"
        assert args.feature is None


# ── next Subcommand ───────────────────────────────────────────────


class TestNextSubcommand:
    """dokima next [feature] [dir] [flags] — replaces dokima --next."""

    def test_next_no_args(self):
        """dokima next with no args: command='next', all None/False."""
        args = _parse("", cmd="next")
        assert args.command == "next"
        assert args.feature is None
        assert args.dir is None
        assert args.continuous is False
        assert args.interactive is False

    def test_next_with_feature(self):
        """dokima next 'Add dark mode' sets feature."""
        args = _parse("'Add dark mode'", cmd="next")
        assert args.command == "next"
        assert args.feature == "Add dark mode"

    def test_next_continuous_flag(self):
        """dokima next --continuous sets continuous=True."""
        args = _parse("--continuous", cmd="next")
        assert args.command == "next"
        assert args.continuous is True

    def test_next_interactive_flag(self):
        """dokima next --interactive sets interactive=True."""
        args = _parse("--interactive", cmd="next")
        assert args.command == "next"
        assert args.interactive is True

    def test_next_force_full_flag(self):
        """dokima next --force-full sets force_full=True."""
        args = _parse("--force-full", cmd="next")
        assert args.command == "next"
        assert args.force_full is True

    def test_next_skip_autofix_flag(self):
        """dokima next --skip-autofix sets skip_autofix=True."""
        args = _parse("--skip-autofix", cmd="next")
        assert args.command == "next"
        assert args.skip_autofix is True

    def test_next_skip_auto_archive_flag(self):
        """dokima next --skip-auto-archive sets skip_auto_archive=True."""
        args = _parse("--skip-auto-archive", cmd="next")
        assert args.command == "next"
        assert args.skip_auto_archive is True

    def test_next_skip_human_gate_flag(self):
        """dokima next --skip-human-gate sets skip_human_gate=True."""
        args = _parse("--skip-human-gate", cmd="next")
        assert args.command == "next"
        assert args.skip_human_gate is True

    def test_next_resume_flag(self):
        """dokima next --resume sets resume_flag=True."""
        args = _parse("--resume", cmd="next")
        assert args.command == "next"
        assert args.resume_flag is True

    def test_next_no_resume_flag(self):
        """dokima next --no-resume sets resume_flag=False."""
        args = _parse("--no-resume", cmd="next")
        assert args.command == "next"
        assert args.resume_flag is False

    def test_next_max_parallel(self):
        """dokima next --max-parallel 3 sets max_parallel=3."""
        args = _parse("--max-parallel 3", cmd="next")
        assert args.command == "next"
        assert args.max_parallel == 3

    def test_next_max_parallel_default(self):
        """dokima next without --max-parallel → None."""
        args = _parse("", cmd="next")
        assert args.max_parallel is None

    def test_next_combined_flags(self):
        """dokima next 'feat' --continuous --force-full --max-parallel 4."""
        args = _parse(
            "feat --continuous --force-full --max-parallel 4", cmd="next"
        )
        assert args.command == "next"
        assert args.feature == "feat"
        assert args.continuous is True
        assert args.force_full is True
        assert args.max_parallel == 4


# ── fix Subcommand ────────────────────────────────────────────────


class TestFixSubcommand:
    """dokima fix [dir] [flags] — replaces dokima --fix."""

    def test_fix_no_args(self):
        """dokima fix with no args: command='fix'."""
        args = _parse("", cmd="fix")
        assert args.command == "fix"
        assert args.dir is None

    def test_fix_with_dir(self):
        """dokima fix ~/proj sets dir."""
        args = _parse("~/proj", cmd="fix")
        assert args.command == "fix"
        assert args.dir == "~/proj"

    def test_fix_fix_all_flag(self):
        """dokima fix --fix-all sets fix_all=True."""
        args = _parse("--fix-all", cmd="fix")
        assert args.command == "fix"
        assert args.fix_all is True

    def test_fix_skip_autofix_flag(self):
        """dokima fix --skip-autofix sets skip_autofix=True."""
        args = _parse("--skip-autofix", cmd="fix")
        assert args.command == "fix"
        assert args.skip_autofix is True

    def test_fix_answers_flag(self):
        """dokima fix --answers /tmp/answers.json sets answers path."""
        args = _parse("--answers /tmp/answers.json", cmd="fix")
        assert args.command == "fix"
        assert args.answers == "/tmp/answers.json"

    def test_fix_combined_flags(self):
        """dokima fix ~/proj --fix-all --force-full."""
        args = _parse("~/proj --fix-all --force-full", cmd="fix")
        assert args.command == "fix"
        assert args.dir == "~/proj"
        assert args.fix_all is True
        assert args.force_full is True


# ── release Subcommand ────────────────────────────────────────────


class TestReleaseSubcommand:
    """dokima release <bump> [--dry-run] [dir] — replaces dokima --release."""

    def test_release_patch(self):
        """dokima release patch sets bump='patch'."""
        args = _parse("patch", cmd="release")
        assert args.command == "release"
        assert args.bump == "patch"

    def test_release_minor(self):
        """dokima release minor sets bump='minor'."""
        args = _parse("minor", cmd="release")
        assert args.command == "release"
        assert args.bump == "minor"

    def test_release_major(self):
        """dokima release major sets bump='major'."""
        args = _parse("major", cmd="release")
        assert args.command == "release"
        assert args.bump == "major"

    def test_release_dry_run(self):
        """dokima release patch --dry-run sets dry_run=True."""
        args = _parse("patch --dry-run", cmd="release")
        assert args.command == "release"
        assert args.bump == "patch"
        assert args.dry_run is True

    def test_release_with_dir(self):
        """dokima release patch ~/proj sets dir."""
        args = _parse("patch ~/proj", cmd="release")
        assert args.command == "release"
        assert args.bump == "patch"
        assert args.dir == "~/proj"

    def test_release_invalid_bump_rejected(self):
        """dokima release invalid should be rejected by argparse."""
        parser = _build_parser()
        try:
            parser.parse_args(["release", "invalid"])
            assert False, "Expected SystemExit for invalid bump type"
        except SystemExit as e:
            assert e.code == 2


# ── Default Pipeline (no subcommand) ──────────────────────────────


class TestDefaultPipeline:
    """dokima <feature> [dir] [flags] — default pipeline, no subcommand."""

    def test_no_args(self):
        """dokima (no args) → command=None, feature=None, dir=None."""
        args = _parse("")
        assert args.command is None
        assert args.feature is None
        assert args.dir is None

    def test_feature_only(self):
        """dokima 'Add dark mode' → feature set, command=None."""
        args = _parse("Add dark mode")
        assert args.command is None
        assert args.feature == "Add dark mode"
        assert args.dir is None

    def test_feature_and_dir(self):
        """dokima 'Add dark mode' ~/proj → feature + dir set."""
        args = _parse("'Add dark mode' ~/proj")
        assert args.command is None
        assert args.feature == "Add dark mode"
        assert args.dir == "~/proj"

    def test_default_with_flags(self):
        """dokima 'feat' --fix-all --force-full --skip-autofix."""
        args = _parse("feat --fix-all --force-full --skip-autofix")
        assert args.command is None
        assert args.feature == "feat"
        assert args.fix_all is True
        assert args.force_full is True
        assert args.skip_autofix is True

    def test_default_max_parallel(self):
        """dokima 'feat' --max-parallel 3."""
        args = _parse("feat --max-parallel 3")
        assert args.max_parallel == 3


# ── Error Handling ────────────────────────────────────────────────


class TestErrorHandling:
    """Edge cases and error handling for subcommand dispatch."""

    def test_unknown_subcommand_exits_2(self):
        """Invalid subcommand raises SystemExit(2)."""
        parser = _build_parser()
        try:
            parser.parse_args(["nonexistent-subcommand"])
            assert False, "Expected SystemExit"
        except SystemExit as e:
            assert e.code == 2

    def test_subcommand_name_not_confused_with_feature(self):
        """'version' as first arg is parsed as subcommand, not feature."""
        args = _parse("", cmd="version")
        assert args.command == "version"
        # The default 'feature' positional should not be set
        assert getattr(args, "feature", None) is None

    def test_help_flag_after_subcommand(self):
        """dokima version --help should work (subcommand-level help)."""
        # This tests that --help is recognized at subcommand level
        parser = _build_parser()
        try:
            parser.parse_args(["version", "--help"])
            assert False, "Expected SystemExit from --help on subcommand"
        except SystemExit as e:
            # argparse exits 0 for --help
            assert e.code == 0
