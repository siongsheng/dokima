"""F005: Model Family Fallback — Tests.

Tests cover:
  - PANEL_FALLBACK_MODEL env-var parsing (Task 1)
  - _detect_provider_failure helper (Task 2)
  - spawn_agent fallback retry logic (Task 3)
  - No false-positive on legitimate output (Task 6)
"""
import os
import sys
import subprocess
import pytest
from unittest.mock import patch

from conftest import _load_panel as _load


# ── Task 1: FALLBACK_MODEL env-var constant ──────────────────────────

class TestFallbackModelConstant:
    """FALLBACK_MODEL global is read from PANEL_FALLBACK_MODEL at module init."""

    def test_reads_from_env_var(self):
        """FALLBACK_MODEL matches PANEL_FALLBACK_MODEL env var."""
        model = "openrouter/anthropic/claude-sonnet-4"
        os.environ["PANEL_FALLBACK_MODEL"] = model
        try:
            panel = _load()
            assert panel.FALLBACK_MODEL == model
        finally:
            os.environ.pop("PANEL_FALLBACK_MODEL", None)

    def test_defaults_to_empty_string(self):
        """When PANEL_FALLBACK_MODEL is unset, FALLBACK_MODEL is empty string."""
        os.environ.pop("PANEL_FALLBACK_MODEL", None)
        panel = _load()
        assert panel.FALLBACK_MODEL == ""

    def test_does_not_crash_on_missing_var(self):
        """Module loads cleanly even without the env var."""
        os.environ.pop("PANEL_FALLBACK_MODEL", None)
        panel = _load()
        assert hasattr(panel, "FALLBACK_MODEL")


# ── Task 2: Provider failure detection helper ─────────────────────────

class TestDetectProviderFailure:
    """_detect_provider_failure detects known provider error patterns."""

    def setup_method(self):
        self.panel = _load()

    # True positives — each pattern variant

    def test_detects_rate_limit(self):
        assert self.panel._detect_provider_failure("rate limit exceeded")

    def test_detects_http_503(self):
        assert self.panel._detect_provider_failure("503 Service Unavailable")

    def test_detects_connection_refused(self):
        assert self.panel._detect_provider_failure("Connection refused")

    def test_detects_provider_error(self):
        assert self.panel._detect_provider_failure("provider.error: upstream timeout")

    def test_detects_model_not_found(self):
        assert self.panel._detect_provider_failure("model 'deepseek-v4-pro' not found")

    def test_detects_unavailable_in_stderr(self):
        assert self.panel._detect_provider_failure("Service Unavailable")

    # True negatives — legitimate output

    def test_legitimate_output_returns_false(self):
        assert not self.panel._detect_provider_failure(
            "## Impact\nThis adds rate limiting to the API endpoint."
        )

    def test_output_with_error_handling_returns_false(self):
        assert not self.panel._detect_provider_failure(
            "def handle_error(): pass"
        )

    def test_normal_agent_response(self):
        assert not self.panel._detect_provider_failure(
            "[strategist] Here is the spec for F005."
        )

    # Edge cases

    def test_empty_string_returns_false(self):
        assert not self.panel._detect_provider_failure("")

    def test_none_returns_false(self):
        assert not self.panel._detect_provider_failure(None)


# ── Task 3: Fallback retry logic ──────────────────────────────────

class _MockProcess:
    """A minimal mock subprocess.Popen result."""
    def __init__(self, stdout_lines, stderr_text="", returncode=0):
        self._stdout_lines = stdout_lines
        self._stderr_text = stderr_text
        self.returncode = returncode
        self.stdout = iter(stdout_lines)
        self.stderr = type('_Stderr', (), {'read': lambda self: stderr_text})()

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        pass

    def terminate(self):
        pass

    def communicate(self, timeout=None):
        return ("", "")


class TestFallbackRetry:
    """spawn_agent retries with FALLBACK_MODEL on provider failure."""

    @staticmethod
    def _make_panel_with_fallback(model):
        os.environ["PANEL_FALLBACK_MODEL"] = model
        try:
            return _load()
        finally:
            os.environ.pop("PANEL_FALLBACK_MODEL", None)

    def test_fallback_fires_on_provider_error(self):
        """When primary fails (error in stderr), fallback model is used and result returned."""
        panel = self._make_panel_with_fallback("deepseek-v4-pro")
        calls = []

        def mock_popen(cmd, **kwargs):
            calls.append(cmd)
            if len(calls) == 1:
                # First call: provider failure
                return _MockProcess(
                    stdout_lines=["[strategist] some output\n"],
                    stderr_text="503 Service Unavailable",
                    returncode=1,
                )
            # Second call (fallback): success
            return _MockProcess(
                stdout_lines=["[strategist] fallback succeeded\n"],
                stderr_text="",
                returncode=0,
            )

        with patch.object(subprocess, "Popen", mock_popen):
            result = panel.spawn_agent("strategist", ["some-skill"], "prompt")

        assert "fallback succeeded" in result
        assert len(calls) == 2, f"Expected 2 Popen calls, got {len(calls)}"
        # Verify fallback cmd includes the fallback model
        fb_cmd = calls[1]
        fb_cmd_str = " ".join(fb_cmd)
        assert "deepseek-v4-pro" in fb_cmd_str

    def test_no_fallback_when_output_is_valid(self):
        """When primary output is valid (no provider error), no fallback occurs."""
        panel = self._make_panel_with_fallback("deepseek-v4-pro")
        calls = []

        def mock_popen(cmd, **kwargs):
            calls.append(cmd)
            return _MockProcess(
                stdout_lines=["[strategist] completed successfully\n"],
                stderr_text="",
                returncode=0,
            )

        with patch.object(subprocess, "Popen", mock_popen):
            result = panel.spawn_agent("strategist", ["some-skill"], "prompt")

        assert "completed successfully" in result
        assert len(calls) == 1, f"Expected 1 Popen call, got {len(calls)}"

    def test_no_fallback_when_fallback_model_unset(self):
        """When PANEL_FALLBACK_MODEL is empty, no fallback even on provider error."""
        os.environ.pop("PANEL_FALLBACK_MODEL", None)
        panel = _load()
        calls = []

        def mock_popen(cmd, **kwargs):
            calls.append(cmd)
            return _MockProcess(
                stdout_lines=["[strategist] some output\n"],
                stderr_text="503 Service Unavailable",
                returncode=1,
            )

        with patch.object(subprocess, "Popen", mock_popen):
            result = panel.spawn_agent("strategist", ["some-skill"], "prompt")

        assert "some output" in result
        assert len(calls) == 1, f"Expected 1 Popen call, got {len(calls)}"
