"""Tests for Task 7: --vcs flag in CLI and help text."""
import sys
import re


class TestVcsFlagCli:
    """--vcs flag is parsed from CLI and documented in help."""

    def test_vcs_flag_in_help_text(self):
        """HELP_TEXT includes --vcs flag documentation."""
        import utils
        assert "--vcs" in utils.HELP_TEXT, \
            "HELP_TEXT missing --vcs flag documentation"

    def test_vcs_flag_in_cli_metadata(self):
        """CLI_METADATA flags include --vcs."""
        import utils
        flags = utils.CLI_METADATA.get("flags", [])
        flag_names = [f.get("flag") for f in flags]
        assert "--vcs" in flag_names, \
            f"CLI_METADATA flags missing --vcs. Found: {flag_names}"

    def test_parse_vcs_flag_via_sys_argv(self):
        """parse_vcs_flag() reads --vcs from sys.argv."""
        import vcs
        with patch.object(sys, 'argv', ['dokima', '--vcs', 'gitlab', 'next']):
            assert vcs.parse_vcs_flag() == "gitlab"


# Need import at module level
from unittest.mock import patch
