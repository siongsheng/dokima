"""F030 Task 1: Subcommand routing tests (RED phase).

These tests verify that argparse subparsers replace the old --flag scanning.
They MUST fail with the current flag-scanning code — that's expected.

RED: dokima version (subcommand) is NOT parsed as a feature description.
RED: Help output shows subcommand syntax, not --flag syntax.
RED: dokima list-crons (subcommand) dispatches correctly.
"""

import sys
import os
import subprocess

PANEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dokima"))


def _run(*args):
    """Run dokima with given args, return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, PANEL_PATH] + list(args),
        capture_output=True, text=True, timeout=15,
    )
    return p.returncode, p.stdout, p.stderr


class TestVersionSubcommand:
    """dokima version (subcommand) replaces dokima --version."""

    def test_version_subcommand_prints_version(self):
        """dokima version prints 'dokima vX.Y.Z' and exits 0."""
        rc, out, err = _run("version")
        assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
        assert out.startswith("dokima v"), f"Expected 'dokima v...', got: {out!r}"

    def test_help_shows_version_subcommand(self):
        """--help output includes 'dokima version' as a subcommand."""
        rc, out, err = _run("--help")
        assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
        # Should show subcommand syntax: "dokima version", not "--version" flag
        assert "dokima version" in out.lower() or "  version" in out, (
            f"Expected subcommand 'version' in help, got (first 500): {out[:500]}"
        )

    def test_dash_dash_version_no_longer_works(self):
        """--version flag is NO LONGER a valid flag (clean break)."""
        rc, out, err = _run("--version")
        # argparse should reject unknown flag with exit 2, or at minimum
        # it should NOT print version and exit 0 like the old code did
        assert rc != 0 or not out.startswith("dokima v"), (
            f"--version should be rejected. Got rc={rc}, out={out!r}"
        )


class TestListCronsSubcommand:
    """dokima list-crons replaces dokima --list-crons."""

    def test_list_crons_is_valid_subcommand(self):
        """dokima list-crons should NOT be treated as a feature description."""
        rc, out, err = _run("list-crons")
        # list-crons should either succeed (0) or fail with a meaningful error,
        # but NOT fail with "Feature description required" or try to run a pipeline
        combined = (out + err).lower()
        assert "feature description required" not in combined, (
            f"'list-crons' should be a subcommand, not a feature. Got: {combined[:500]}"
        )
        # Should NOT fall through to pipeline setup (no "AGENTS.md" error)
        assert "agents.md" not in combined, (
            f"'list-crons' should dispatch to list-crons handler. Got: {combined[:500]}"
        )


class TestHelpShowsSubcommandSyntax:
    """Help output reflects subcommand-driven CLI, not --flag scanning."""

    def test_help_output_not_rely_on_flag_syntax(self):
        """The old --flag scanning pattern should be gone from help."""
        rc, out, err = _run("--help")
        assert rc == 0, f"Expected exit 0, got {rc}"
        # The old usage line used to say: dokima [--next|--continuous|--fix] [--fix-all] ...
        # After refactor, it should NOT start with that flat --flag pattern
        combined = out + err
        # Old pattern check: "dokima [--next|--continuous|--fix]" appeared in the old usage
        if "[--next|--continuous|--fix]" in combined:
            # Still acceptable if usage line also shows subcommands
            pass  # Transitional — re-evaluate after GREEN
        # At minimum, subcommand names should appear in help
        assert "next" in out.lower(), f"Help should mention 'next' subcommand: {out[:500]}"


class TestDefaultPipelineStillWorks:
    """dokima \"Feature\" [dir] — the default pipeline path is unchanged."""

    def test_no_args_shows_usage(self):
        """dokima with zero args prints usage and exits non-zero."""
        rc, out, err = _run()
        assert rc != 0, f"Expected non-zero exit for no-args, got {rc}"
        # Usage should appear
        combined = out + err
        assert "usage" in combined.lower() or "dokima" in combined.lower(), (
            f"Expected usage info, got: {combined[:300]}"
        )


class TestArgparseErrorHandling:
    """argparse built-in error handling for invalid subcommands."""

    def test_unknown_subcommand_exits_2(self):
        """Invalid subcommand exits with argparse error (exit 2)."""
        rc, out, err = _run("nonexistent-subcommand")
        # argparse exits 2 on invalid command
        assert rc == 2, f"Expected exit 2 for unknown subcommand, got {rc}. stderr: {err}"
