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
