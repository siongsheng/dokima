"""Tests for extract_agent_messages() — session transcript parsing."""
import pytest

BOX_MSG = "\u256d\u2500 \u2695 Hermes \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\nhello world\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f"

def test_hermes_box_format(panel):
    result = panel.extract_agent_messages(BOX_MSG)
    assert "hello world" in result

def test_no_box_markers_fallback(panel):
    result = panel.extract_agent_messages("plain text output")
    assert result == "plain text output"

def test_multiple_boxes(panel):
    msg = BOX_MSG + "\n\n" + BOX_MSG.replace("hello world", "second message")
    result = panel.extract_agent_messages(msg)
    assert "hello world" in result
    assert "second message" in result

def test_empty_box_skipped(panel):
    empty_box = "\u256d\u2500 \u2695 Hermes \u2500\u2500\u256e\n   \n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f"
    result = panel.extract_agent_messages(empty_box)
    assert result.strip() == "" or result == empty_box

def test_partial_box_no_match(panel):
    # Only opening marker, no closing
    partial = "\u256d\u2500 \u2695 Hermes \u2500\u2500\u256e\ncontent"
    result = panel.extract_agent_messages(partial)
    # Should fall through to raw since no closing marker
    assert result == partial

def test_last_only_returns_final_message(panel):
    """last_only=True returns only the LAST agent message — skips intermediate chatter."""
    msg1 = BOX_MSG.replace("hello world", "exploring codebase... reading AGENTS.md")
    msg2 = BOX_MSG.replace("hello world", "# F010: SEO — Spec\n\n## Decision Table\n\nSINGLE APPROACH")
    combined = msg1 + "\n\n" + msg2
    result = panel.extract_agent_messages(combined, last_only=True)
    assert "exploring codebase" not in result
    assert "# F010: SEO — Spec" in result
    assert "## Decision Table" in result

def test_last_only_with_single_message(panel):
    """last_only=True with one message returns that message."""
    result = panel.extract_agent_messages(BOX_MSG, last_only=True)
    assert "hello world" in result

def test_last_only_fallback_no_boxes(panel):
    """last_only=True with no boxes falls through to raw output."""
    result = panel.extract_agent_messages("plain text", last_only=True)
    assert result == "plain text"

def test_last_false_still_concatenates(panel):
    """last_only=False (default) still concatenates all messages."""
    msg1 = BOX_MSG.replace("hello world", "first")
    msg2 = BOX_MSG.replace("hello world", "second")
    combined = msg1 + "\n\n" + msg2
    result = panel.extract_agent_messages(combined, last_only=False)
    assert "first" in result
    assert "second" in result
