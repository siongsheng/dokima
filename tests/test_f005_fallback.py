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

    def test_file_not_found_error_not_false_positive(self):
        """'Error: file not found' is a legitimate code error, not provider failure."""
        assert not self.panel._detect_provider_failure(
            "Error: file not found: /path/to/config.json"
        )

    def test_normal_agent_response(self):
        assert not self.panel._detect_provider_failure(
            "[strategist] Here is the spec for F005."
        )

    # False-positive boundary tests — substrings that should NOT match

    def test_503_in_number_does_not_false_positive(self):
        """Number containing '503' as substring (e.g., 15039) should not trigger."""
        assert not self.panel._detect_provider_failure(
            "15039 tests passed, 48 failed"
        )

    def test_503_in_port_number_does_not_false_positive(self):
        """Port number containing 503 should not trigger."""
        assert not self.panel._detect_provider_failure(
            "Listening on port 25030"
        )

    def test_rate_as_word_in_non_limit_context_does_not_false_positive(self):
        """The word 'rate' in normal context should not trigger 'rate limit' pattern."""
        assert not self.panel._detect_provider_failure(
            "The error rate decreased by 50% this sprint"
        )

    def test_model_as_topic_not_false_positive(self):
        """'model' used as a topic word should not trigger if not followed by 'not found/available'."""
        assert not self.panel._detect_provider_failure(
            "The new model was deployed to production"
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

    def test_fallback_passes_model_flags_correctly(self):
        """Verify the fallback call includes --provider and -m from FALLBACK_MODEL."""
        model = "openrouter/anthropic/claude-sonnet-4"
        os.environ["PANEL_FALLBACK_MODEL"] = model
        try:
            panel = _load()
        finally:
            os.environ.pop("PANEL_FALLBACK_MODEL", None)
        calls = []

        def mock_popen(cmd, **kwargs):
            calls.append(cmd)
            if len(calls) == 1:
                return _MockProcess(
                    stdout_lines=["Error output\n"],
                    stderr_text="connection refused\n",
                    returncode=1,
                )
            return _MockProcess(
                stdout_lines=["ok\n"],
                stderr_text="",
                returncode=0,
            )

        with patch.object(subprocess, "Popen", mock_popen):
            panel.spawn_agent("strategist", ["some-skill"], "prompt")

        assert len(calls) == 2, f"Expected 2 calls, got {len(calls)}"
        fb_cmd = calls[1]
        fb_cmd_str = " ".join(fb_cmd)
        assert "--provider" in fb_cmd_str, f"Expected --provider in fallback cmd: {fb_cmd_str}"
        assert "openrouter" in fb_cmd_str
        assert "-m" in fb_cmd_str or "--model" in fb_cmd_str
        assert "claude-sonnet-4" in fb_cmd_str


# ── Task 6: No false-positive on legitimate output ────────────────────

class TestFallbackNotFiredOnLegitimateOutput:
    """spawn_agent does NOT trigger fallback on legitimate agent output
    containing words that look like provider-failure substrings."""

    def test_number_503_in_output_does_not_trigger_fallback(self):
        """Output containing '503' embedded in a larger number should not trigger fallback."""
        os.environ["PANEL_FALLBACK_MODEL"] = "deepseek-v4-pro"
        try:
            panel = _load()
        finally:
            os.environ.pop("PANEL_FALLBACK_MODEL", None)
        calls = []

        def mock_popen(cmd, **kwargs):
            calls.append(cmd)
            return _MockProcess(
                stdout_lines=["15039 tests passed, 0 failed\n"],
                stderr_text="",
                returncode=0,
            )

        with patch.object(subprocess, "Popen", mock_popen):
            result = panel.spawn_agent("strategist", ["some-skill"], "prompt")

        assert "15039 tests passed" in result
        assert len(calls) == 1, (
            f"Expected 1 call (no fallback), got {len(calls)}. "
            "Fallback incorrectly fired on legitimate output containing '503' as substring."
        )

    def test_app_error_nonzero_exit_does_not_trigger_fallback(self):
        """Non-zero exit with app error in stderr should not trigger fallback."""
        os.environ["PANEL_FALLBACK_MODEL"] = "deepseek-v4-pro"
        try:
            panel = _load()
        finally:
            os.environ.pop("PANEL_FALLBACK_MODEL", None)
        calls = []

        def mock_popen(cmd, **kwargs):
            calls.append(cmd)
            return _MockProcess(
                stdout_lines=["Task failed: file not found\n"],
                stderr_text="ModuleNotFoundError: No module named 'requests'\n",
                returncode=2,
            )

        with patch.object(subprocess, "Popen", mock_popen):
            result = panel.spawn_agent("strategist", ["some-skill"], "prompt")

        assert "Task failed: file not found" in result
        assert len(calls) == 1, f"Expected 1 call (no fallback), got {len(calls)}"

    def test_stderr_with_generic_error_does_not_trigger_fallback(self):
        """Stderr with generic system errors should not trigger fallback."""
        os.environ["PANEL_FALLBACK_MODEL"] = "deepseek-v4-pro"
        try:
            panel = _load()
        finally:
            os.environ.pop("PANEL_FALLBACK_MODEL", None)
        calls = []

        def mock_popen(cmd, **kwargs):
            calls.append(cmd)
            return _MockProcess(
                stdout_lines=["Done\n"],
                stderr_text="warning: deprecated function called\n",
                returncode=0,
            )

        with patch.object(subprocess, "Popen", mock_popen):
            result = panel.spawn_agent("strategist", ["some-skill"], "prompt")

        assert "Done" in result
        assert len(calls) == 1, f"Expected 1 call (no fallback), got {len(calls)}"

    def test_model_discussion_does_not_trigger_fallback(self):
        """Agent output discussing a model as a topic should not trigger fallback."""
        os.environ["PANEL_FALLBACK_MODEL"] = "deepseek-v4-pro"
        try:
            panel = _load()
        finally:
            os.environ.pop("PANEL_FALLBACK_MODEL", None)
        calls = []

        def mock_popen(cmd, **kwargs):
            calls.append(cmd)
            return _MockProcess(
                stdout_lines=["I recommend using the GPT-4 model for this task\n"],
                stderr_text="",
                returncode=0,
            )

        with patch.object(subprocess, "Popen", mock_popen):
            result = panel.spawn_agent("strategist", ["some-skill"], "prompt")

        assert "GPT-4 model" in result
        assert len(calls) == 1, f"Expected 1 call (no fallback), got {len(calls)}"

    def test_multi_line_agent_code_output_does_not_trigger_fallback(self):
        """Multi-line legitimate code output should not trigger fallback."""
        os.environ["PANEL_FALLBACK_MODEL"] = "deepseek-v4-pro"
        try:
            panel = _load()
        finally:
            os.environ.pop("PANEL_FALLBACK_MODEL", None)
        calls = []

        def mock_popen(cmd, **kwargs):
            calls.append(cmd)
            return _MockProcess(
                stdout_lines=[
                    "Here is the implementation:\n",
                    "def hello():\n",
                    "    print('Hello, world!')\n",
                    "returncode: 0\n",
                ],
                stderr_text="",
                returncode=0,
            )

        with patch.object(subprocess, "Popen", mock_popen):
            result = panel.spawn_agent("strategist", ["some-skill"], "prompt")

        assert "Hello, world!" in result
        assert len(calls) == 1, f"Expected 1 call (no fallback), got {len(calls)}"
