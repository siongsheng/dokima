"""Tests for F041 Task 7: agent.py imports from git_ops.py.

Verify that agent.py imports load_key and load_github_token from
git_ops.py instead of utils.py, per the domain module split.
"""
import pytest


class TestAgentImportsFromGitOps:
    """Verify agent.py imports from git_ops.py per Task 7."""

    def test_agent_load_key_is_from_git_ops(self):
        """agent.load_key should be the same object as git_ops.load_key."""
        import agent
        from git_ops import load_key as git_ops_load_key
        assert agent.load_key is git_ops_load_key, (
            "agent.load_key should be git_ops.load_key, not utils.load_key"
        )

    def test_agent_load_github_token_is_from_git_ops(self):
        """agent.load_github_token should be the same object as
        git_ops.load_github_token."""
        import agent
        from git_ops import load_github_token as git_ops_gh_token
        assert agent.load_github_token is git_ops_gh_token, (
            "agent.load_github_token should be git_ops.load_github_token, "
            "not utils.load_github_token"
        )

    def test_agent_still_has_utils_symbols(self):
        """agent should still have _redact_secrets, _write_log_line,
        HERMES_BIN, OUTPUT_LOG (from utils, not from git_ops)."""
        import agent
        assert hasattr(agent, '_redact_secrets'), (
            "agent should have _redact_secrets"
        )
        assert hasattr(agent, '_write_log_line'), (
            "agent should have _write_log_line"
        )
        assert hasattr(agent, 'HERMES_BIN'), (
            "agent should have HERMES_BIN"
        )
        assert hasattr(agent, 'OUTPUT_LOG'), (
            "agent should have OUTPUT_LOG"
        )

    def test_agent_imports_cleanly(self):
        """agent.py should import without errors."""
        import agent
        assert hasattr(agent, 'spawn_agent'), (
            "agent should have spawn_agent after import"
        )
        assert hasattr(agent, 'call_agent'), (
            "agent should have call_agent after import"
        )
