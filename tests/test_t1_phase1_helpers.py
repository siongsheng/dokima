"""Verify Task 1 helpers are importable and callable after extraction.

These are smoke tests — the existing 1123-test suite is the real safety net.
"""
import os
import tempfile


def test_configure_strategist_reasoning_no_env():
    """_configure_strategist_reasoning returns None triple when PANEL_REASONING not set."""
    from pipeline import _configure_strategist_reasoning
    # Unset env var to ensure clean state
    old = os.environ.pop("PANEL_REASONING", None)
    try:
        with tempfile.TemporaryDirectory() as td:
            orig, orig_yaml, cfg = _configure_strategist_reasoning(td)
            assert orig is None
            assert orig_yaml is None
            assert cfg.endswith("config.yaml")
    finally:
        if old is not None:
            os.environ["PANEL_REASONING"] = old


def test_check_existing_spec_no_spec():
    """_check_existing_spec returns empty string when no spec exists."""
    from pipeline import _check_existing_spec
    with tempfile.TemporaryDirectory() as td:
        result = _check_existing_spec(td, "test feature")
        assert result == ""


def test_restore_strategist_config_noop():
    """_restore_strategist_config does nothing when orig_reasoning is None."""
    from pipeline import _restore_strategist_config
    with tempfile.TemporaryDirectory() as td:
        cfg = os.path.join(td, "nonexistent.yaml")
        _restore_strategist_config(None, "fake yaml", cfg)
        # Should not raise, should not create the file


def test_helpers_importable():
    """All 5 Task 1 helpers are importable from pipeline module."""
    from pipeline import (
        _configure_strategist_reasoning,
        _check_existing_spec,
        _build_strategist_prompt,
        _handle_dag_reprompt,
        _restore_strategist_config,
    )
    assert callable(_configure_strategist_reasoning)
    assert callable(_check_existing_spec)
    assert callable(_build_strategist_prompt)
    assert callable(_handle_dag_reprompt)
    assert callable(_restore_strategist_config)


def test_build_strategist_prompt_returns_string():
    """_build_strategist_prompt returns a non-empty string prompt."""
    from pipeline import _build_strategist_prompt
    prompt = _build_strategist_prompt("/tmp/testproj", "test feature", "", "", "")
    assert isinstance(prompt, str)
    assert len(prompt) > 100
    assert "test feature" in prompt
    assert "/tmp/testproj" in prompt
