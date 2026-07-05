"""Tests for Task 6: VCS token env passthrough in agent profiles."""
import os
import sys


class TestAgentProfileEnvPassthrough:
    """Agent profile configs include GLAB_TOKEN and GITLAB_TOKEN."""

    def test_profiles_include_glab_token(self):
        """All 4 agent profiles have GLAB_TOKEN in env_passthrough."""
        import utils
        for profile in ("strategist", "coder", "tech-lead", "nm"):
            config = utils._PROFILE_CONFIGS.get(profile, {})
            passthrough = config.get("terminal.env_passthrough", "")
            assert "GLAB_TOKEN" in passthrough, \
                f"Profile '{profile}' missing GLAB_TOKEN: {passthrough}"

    def test_profiles_include_gitlab_token(self):
        """All 4 agent profiles have GITLAB_TOKEN in env_passthrough."""
        import utils
        for profile in ("strategist", "coder", "tech-lead", "nm"):
            config = utils._PROFILE_CONFIGS.get(profile, {})
            passthrough = config.get("terminal.env_passthrough", "")
            assert "GITLAB_TOKEN" in passthrough, \
                f"Profile '{profile}' missing GITLAB_TOKEN: {passthrough}"
