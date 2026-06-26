"""Tests for clean_spec_content() — strips agent chatter from strategist output."""
import pytest

REAL_SPEC = """# F010: SEO + OG Images — Spec

**Status: In Progress** | **Confidence: High** | **Impact: MEDIUM**

## 1. Constitution Check

| Axiom | Verdict |
|--------|---------|
| Solves user's own pain? | YES |
"""


class TestCleanSpecContent:
    def test_preserves_clean_spec(self, panel):
        """A clean spec passes through unchanged."""
        result = panel.clean_spec_content(REAL_SPEC)
        assert "# F010: SEO + OG Images — Spec" in result
        assert "## 1. Constitution Check" in result
        assert result.startswith("#")

    def test_strips_text_before_first_header(self, panel):
        """Agent chatter before the first # header is stripped."""
        raw = (
            "Now I understand the full picture. Let me check the actual spec files.\n"
            "I found the full spec in session 20260627.\n\n"
            + REAL_SPEC
        )
        result = panel.clean_spec_content(raw)
        assert "Now I understand" not in result
        assert result.startswith("# F010:")

    def test_strips_session_resume_text(self, panel):
        """'Resume this session with:' and everything after is removed."""
        raw = REAL_SPEC + "\n\nResume this session with: hermes --profile strategist..."
        result = panel.clean_spec_content(raw)
        assert "Resume this session" not in result
        assert "# F010:" in result

    def test_strips_ponytail_guard_verdict(self, panel):
        """Ponytail Guard blocks are removed."""
        raw = (
            REAL_SPEC
            + "\n\nPonytail Guard verdict: PASS — no scope creep detected.\n\n"
        )
        result = panel.clean_spec_content(raw)
        assert "Ponytail Guard" not in result
        assert "# F010:" in result

    def test_strips_signoff_lines(self, panel):
        """Agent sign-off lines are removed, spec content is kept."""
        for signoff in [
            "The spec is ready for review.",
            "Do you want me to proceed?",
            "Shall I start implementation?",
            "Let me know if you need changes.",
            "Would you like me to add anything?",
            "I can make changes if needed.",
            "Is there anything else?",
            "Feel free to ask questions.",
        ]:
            raw = REAL_SPEC + f"\n\n{signoff}\n"
            result = panel.clean_spec_content(raw)
            assert signoff not in result, f"Should strip: {signoff}"
            assert "# F010:" in result, f"Spec lost after stripping: {signoff}"

    def test_spec_content_not_destroyed_by_chatter_removal(self, panel):
        """Removing a sign-off line does NOT delete the rest of the spec."""
        raw = (
            "# F010: SEO\n\n"
            "## Decision Table\n\n"
            "SINGLE APPROACH: Standard Next.js patterns.\n\n"
            "## Task Breakdown\n\n"
            "### Task 1: Create metadata lib\n"
            "**Files:** src/lib/metadata.ts\n\n"
            "The spec is ready. Let me know if you need changes.\n"
        )
        result = panel.clean_spec_content(raw)
        assert "The spec is ready" not in result
        assert "Let me know if you need" not in result
        # Verify spec content is preserved
        assert "## Decision Table" in result
        assert "SINGLE APPROACH" in result
        assert "## Task Breakdown" in result
        assert "### Task 1" in result

    def test_empty_input(self, panel):
        """Empty string returns empty."""
        assert panel.clean_spec_content("") == ""
        assert panel.clean_spec_content("   \n  ") == ""
