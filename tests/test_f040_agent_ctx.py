"""Tests for agent.py ctx parameter migration — F040 Task 4.

Tests that agent.py functions accept a PipelineContext-like object
via ctx parameter, using ctx attributes instead of module-level globals.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock


# ── Helpers ────────────────────────────────────────

def _make_ctx(**overrides):
    """Create a minimal ctx-like object for testing agent functions."""
    defaults = {
        "API_KEY": "ctx-api-key",
        "HERMES_BIN": "/fake/path/hermes",
        "OUTPUT_LOG": "/tmp/fake-output.log",
        "PANEL_PORT": {"strategist": 8647, "tech-lead": 8644, "coder": 8645, "nm": 8648},
        "FALLBACK_MODELS": {},
        "PROJECT_DIR": "/tmp/fake-project",
        "REPO": "fake/fake",
        "DEFAULT_BRANCH": "main",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── call_agent with ctx ────────────────────────────

def test_call_agent_accepts_ctx_keyword():
    """call_agent accepts ctx keyword argument."""
    import agent
    ctx = _make_ctx()

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = (
            b'{"choices":[{"message":{"content":"ok"}}],"usage":{"completion_tokens":1}}'
        )
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # ctx is accepted — should not raise TypeError
        result = agent.call_agent(
            port=18647, system_prompt="sys", user_prompt="usr", ctx=ctx
        )
        assert result["content"] == "ok"


def test_call_agent_uses_ctx_api_key():
    """call_agent uses ctx.API_KEY in Authorization header when ctx provided."""
    import agent
    ctx = _make_ctx(API_KEY="ctx-specific-key-42")

    mock_response_data = (
        b'{"choices":[{"message":{"content":"test response"}}],"usage":{"completion_tokens":5}}'
    )

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response_data
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # This will fail with TypeError before fix (ctx not accepted)
        agent.call_agent(
            port=18647, system_prompt="sys", user_prompt="usr", ctx=ctx
        )

        # Verify the request was made with ctx.API_KEY
        call_args = mock_urlopen.call_args
        assert call_args is not None
        req = call_args[0][0]
        headers = dict(req.headers)
        assert "ctx-specific-key-42" in headers.get("Authorization", ""), (
            "Expected Authorization header to contain ctx.API_KEY value"
        )


# ── _run_agent with ctx ────────────────────────────

def test_run_agent_accepts_ctx_keyword():
    """_run_agent accepts ctx keyword argument."""
    import agent
    ctx = _make_ctx()

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout = []
        mock_proc.stderr = []
        mock_proc.returncode = 0
        mock_proc.wait.return_value = None
        mock_popen.return_value = mock_proc

        # ctx is accepted — should not raise TypeError
        result, rc = agent._run_agent(
            "test-profile", [], "test prompt", 30, None, None, ctx=ctx
        )
        assert rc == 0


def test_run_agent_uses_ctx_hermes_bin():
    """_run_agent uses ctx.HERMES_BIN instead of module global when ctx provided."""
    import agent
    ctx = _make_ctx(HERMES_BIN="/custom/path/to/hermes")

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout = []
        mock_proc.stderr = []
        mock_proc.returncode = 0
        mock_proc.wait.return_value = None
        mock_popen.return_value = mock_proc

        # Will fail with TypeError before fix
        agent._run_agent("test-profile", [], "test prompt", 30, None, None, ctx=ctx)

        # Verify HERMES_BIN from ctx was used in command
        call_args = mock_popen.call_args
        assert call_args is not None
        cmd = call_args[0][0]
        assert cmd[0] == "/custom/path/to/hermes", (
            f"Expected /custom/path/to/hermes as first cmd arg, got {cmd[0]}"
        )


# ── spawn_agent with ctx ───────────────────────────

def test_spawn_agent_accepts_ctx_keyword():
    """spawn_agent accepts ctx keyword argument."""
    import agent
    ctx = _make_ctx()

    with patch("agent._run_agent", return_value=("ok output", 0)):
        # ctx is accepted — should not raise TypeError
        result = agent.spawn_agent("test-profile", [], "test prompt", ctx=ctx)
        assert result == "ok output"


# ── Backward compatibility (no ctx) ────────────────

def test_call_agent_backward_compat_no_ctx():
    """call_agent works without ctx (uses module-level globals)."""
    import agent

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = (
            b'{"choices":[{"message":{"content":"ok"}}],"usage":{"completion_tokens":1}}'
        )
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        result = agent.call_agent(port=18647, system_prompt="sys", user_prompt="usr")
        assert result["content"] == "ok"


def test_run_agent_backward_compat_no_ctx():
    """_run_agent works without ctx (uses module-level globals)."""
    import agent

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdout = []
        mock_proc.stderr = []
        mock_proc.returncode = 0
        mock_proc.wait.return_value = None
        mock_popen.return_value = mock_proc

        result, rc = agent._run_agent("test", [], "prompt", 10, None, None)
        assert rc == 0


def test_spawn_agent_backward_compat_no_ctx():
    """spawn_agent works without ctx (uses module-level globals)."""
    import agent

    with patch("agent._run_agent", return_value=("ok output", 0)):
        result = agent.spawn_agent("test", [], "prompt", timeout=10)
        assert result == "ok output"
