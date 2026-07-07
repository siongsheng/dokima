"""Tests for spec_extract.py — spec extraction functions extracted from utils.py.

Verifies:
- spec_extract module exists with expected functions
- utils.py re-exports spec_extract functions (backward compat)
"""

import pytest

from conftest import _load_panel as _load


class TestSpecExtractModule:
    """Verify spec_extract.py module structure."""

    def test_module_importable(self):
        """spec_extract module can be imported."""
        import spec_extract

        assert spec_extract is not None

    def test_has_extract_pr_sections(self):
        """spec_extract exports extract_pr_sections()."""
        import spec_extract

        assert hasattr(spec_extract, "extract_pr_sections")
        assert callable(spec_extract.extract_pr_sections)

    def test_has_clean_spec_content(self):
        """spec_extract exports clean_spec_content()."""
        import spec_extract

        assert hasattr(spec_extract, "clean_spec_content")
        assert callable(spec_extract.clean_spec_content)

    def test_has_verify_spec_quality(self):
        """spec_extract exports verify_spec_quality()."""
        import spec_extract

        assert hasattr(spec_extract, "verify_spec_quality")
        assert callable(spec_extract.verify_spec_quality)

    def test_has_extract_should_fix_from_text(self):
        """spec_extract exports extract_should_fix_from_text()."""
        import spec_extract

        assert hasattr(spec_extract, "extract_should_fix_from_text")
        assert callable(spec_extract.extract_should_fix_from_text)

    def test_has_extract_nm_summary(self):
        """spec_extract exports _extract_nm_summary()."""
        import spec_extract

        assert hasattr(spec_extract, "_extract_nm_summary")
        assert callable(spec_extract._extract_nm_summary)

    def test_has_extract_issue_sections(self):
        """spec_extract exports extract_issue_sections()."""
        import spec_extract

        assert hasattr(spec_extract, "extract_issue_sections")
        assert callable(spec_extract.extract_issue_sections)

    def test_has_extract_agent_messages(self):
        """spec_extract exports extract_agent_messages()."""
        import spec_extract

        assert hasattr(spec_extract, "extract_agent_messages")
        assert callable(spec_extract.extract_agent_messages)

    def test_has_extract_file_paths(self):
        """spec_extract exports extract_file_paths()."""
        import spec_extract

        assert hasattr(spec_extract, "extract_file_paths")
        assert callable(spec_extract.extract_file_paths)

    def test_has_extract_tl_verdict(self):
        """spec_extract exports _extract_tl_verdict()."""
        import spec_extract

        assert hasattr(spec_extract, "_extract_tl_verdict")
        assert callable(spec_extract._extract_tl_verdict)

    def test_has_extract_tl_blockers(self):
        """spec_extract exports _extract_tl_blockers()."""
        import spec_extract

        assert hasattr(spec_extract, "_extract_tl_blockers")
        assert callable(spec_extract._extract_tl_blockers)

    def test_has_format_blocker_cross_reference(self):
        """spec_extract exports format_blocker_cross_reference()."""
        import spec_extract

        assert hasattr(spec_extract, "format_blocker_cross_reference")
        assert callable(spec_extract.format_blocker_cross_reference)

    def test_has_extract_convention_rules(self):
        """spec_extract exports _extract_convention_rules()."""
        import spec_extract

        assert hasattr(spec_extract, "_extract_convention_rules")
        assert callable(spec_extract._extract_convention_rules)

    def test_has_append_convention_rules(self):
        """spec_extract exports _append_convention_rules()."""
        import spec_extract

        assert hasattr(spec_extract, "_append_convention_rules")
        assert callable(spec_extract._append_convention_rules)


class TestUtilsReExport:
    """Verify utils.py re-exports spec_extract functions for backward compat."""

    def test_utils_has_extract_pr_sections(self):
        import utils

        assert hasattr(utils, "extract_pr_sections")
        assert callable(utils.extract_pr_sections)

    def test_utils_has_clean_spec_content(self):
        import utils

        assert hasattr(utils, "clean_spec_content")
        assert callable(utils.clean_spec_content)

    def test_utils_has_verify_spec_quality(self):
        import utils

        assert hasattr(utils, "verify_spec_quality")
        assert callable(utils.verify_spec_quality)

    def test_utils_has_extract_should_fix_from_text(self):
        import utils

        assert hasattr(utils, "extract_should_fix_from_text")
        assert callable(utils.extract_should_fix_from_text)

    def test_utils_has_extract_nm_summary(self):
        import utils

        assert hasattr(utils, "_extract_nm_summary")
        assert callable(utils._extract_nm_summary)

    def test_utils_has_extract_issue_sections(self):
        import utils

        assert hasattr(utils, "extract_issue_sections")
        assert callable(utils.extract_issue_sections)

    def test_utils_has_extract_agent_messages(self):
        import utils

        assert hasattr(utils, "extract_agent_messages")
        assert callable(utils.extract_agent_messages)

    def test_utils_has_extract_file_paths(self):
        import utils

        assert hasattr(utils, "extract_file_paths")
        assert callable(utils.extract_file_paths)

    def test_utils_has_extract_tl_verdict(self):
        import utils

        assert hasattr(utils, "_extract_tl_verdict")
        assert callable(utils._extract_tl_verdict)

    def test_utils_has_extract_tl_blockers(self):
        import utils

        assert hasattr(utils, "_extract_tl_blockers")
        assert callable(utils._extract_tl_blockers)

    def test_utils_has_format_blocker_cross_reference(self):
        import utils

        assert hasattr(utils, "format_blocker_cross_reference")
        assert callable(utils.format_blocker_cross_reference)


class TestSpecExtractFunctions:
    """Smoke tests for spec_extract functions."""

    def test_extract_pr_sections_basic(self, panel):
        """extract_pr_sections produces non-empty output for valid spec text."""
        spec = "## 1. Impact\n\nThis changes the pipeline startup.\n\n## 2. What Changed\n- Updated init flow\n- Added config validation\n\n### Task 1: Do the thing\n**Files:** foo.py\n**Dependencies:** none\n**Parallelizable:** no\n"
        result = panel.extract_pr_sections(spec, "Fix startup bug")
        assert "## Why" in result
        assert "Fix startup bug" in result
        assert "## Impact" in result
        assert "## What Changed" in result

    def test_clean_spec_content_strips_noise(self, panel):
        """clean_spec_content removes thinking/chatter."""
        raw = "Some chatter before spec.\n# The Spec\n\n## Impact\n\nReal content.\n\nDo you want me to proceed?\n"
        cleaned = panel.clean_spec_content(raw)
        assert "# The Spec" in cleaned
        assert "chatter" not in cleaned
        assert "Do you want me to" not in cleaned

    def test_verify_spec_quality_passes_valid_spec(self, panel):
        """verify_spec_quality passes a well-formed spec."""
        spec = """## Impact
This is the impact section.

## What Changed
- Added foo
- Fixed bar

### Task 1: Do thing A
**Files:** a.py
**Dependencies:** none
**Parallelizable:** no

### Task 2: Do thing B
**Files:** b.py
**Dependencies:** Task 1
**Parallelizable:** no
"""
        passed, failures = panel.verify_spec_quality(spec)
        assert passed, f"Expected pass but got failures: {failures}"
        assert len(failures) == 0

    def test_extract_should_fix_from_text_table(self, panel):
        """extract_should_fix_from_text parses table format."""
        text = "| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Handle edge case |"
        results = panel.extract_should_fix_from_text(text)
        assert len(results) == 1
        assert results[0]["detail"] == "Handle edge case"

    def test_extract_nm_summary_returns_dict(self, panel):
        """_extract_nm_summary returns a dict with expected keys."""
        result = panel._extract_nm_summary(None)
        assert isinstance(result, dict)
        assert "risk" in result
        assert "auto_fix_count" in result
        assert "should_fix_items" in result

    def test_extract_issue_sections_parses_issue(self):
        """extract_issue_sections extracts sections from issue body."""
        import utils

        body = "### What\nFix the login bug in `auth.py`.\n\n### Fix\nAdd validation.\n\n### Verify\nRun tests."
        sections = utils.extract_issue_sections(body)
        assert sections["what"] == "Fix the login bug in `auth.py`."
        assert "Add validation" in sections["fix"]
        assert sections["file_path"] == "auth.py"

    # ── F044: _trim_to_sentences tests ──

    def test_trim_to_sentences_two(self):
        """_trim_to_sentences returns first 2 sentences from 3-sentence input."""
        import spec_extract
        text = "First sentence. Second sentence. Third sentence."
        result = spec_extract._trim_to_sentences(text, max_sentences=2, max_chars=500)
        assert "First sentence." in result
        assert "Second sentence." in result
        assert "Third sentence." not in result
        assert result.endswith("...")

    def test_trim_to_sentences_char_cap(self):
        """_trim_to_sentences truncates at max_chars with ellipsis."""
        import spec_extract
        text = "A" * 210 + ". B."
        result = spec_extract._trim_to_sentences(text, max_sentences=2, max_chars=200)
        assert len(result) <= 200 + 3  # text + "..."
        assert result.endswith("...")

    def test_trim_to_sentences_abbreviations(self):
        """_trim_to_sentences does not split on Dr. Mr. Inc. i.e. e.g. etc."""
        import spec_extract
        text = "Visit Dr. Smith then. Meet Mr. Jones later."
        result = spec_extract._trim_to_sentences(text, max_sentences=2, max_chars=500)
        assert "Dr. Smith then." in result
        assert "Mr. Jones later." in result

    # ── F044: _filter_impact_product_only tests ──

    def test_filter_impact_strips_meta(self):
        """_filter_impact_product_only removes meta-commentary phrases."""
        import spec_extract
        text = "Here is the COMPLETE corrected spec for F044.\nThis reduces PR body noise by 80%."
        result = spec_extract._filter_impact_product_only(text)
        assert "Here is the COMPLETE corrected spec" not in result
        assert "reduces PR body noise by 80%" in result

    def test_filter_impact_strips_chatter(self):
        """_filter_impact_product_only removes model sign-off lines."""
        import spec_extract
        text = "This fixes a race condition.\nDo you want me to proceed?\nShall I implement this now?"
        result = spec_extract._filter_impact_product_only(text)
        assert "Do you want me to" not in result
        assert "Shall I" not in result
        assert "fixes a race condition" in result

    def test_filter_impact_preserves_product(self):
        """_filter_impact_product_only preserves product-value text."""
        import spec_extract
        text = "This reduces PR body noise by 80%.\n\nUsers will see cleaner output."
        result = spec_extract._filter_impact_product_only(text)
        assert "reduces PR body noise by 80%" in result
        assert "Users will see cleaner output" in result

    # ── F044: extract_pr_sections trimmed output tests ──

    def test_extract_pr_sections_trimmed_why(self):
        """extract_pr_sections Why section is trimmed to 2 sentences max 200 chars."""
        spec = (
            "Position: Sentence one. Sentence two. Sentence three. Sentence four. "
            "Sentence five which is extra.\n\n"
            "## Impact\n\nThis is the impact section.\n\n"
            "## What Changed\n- Added feature X\n"
        )
        import spec_extract
        result = spec_extract.extract_pr_sections(spec, "Test Feature")
        assert "## Why" in result
        # Should not contain all 5 sentences
        assert "Sentence five" not in result

    def test_extract_pr_sections_clean_impact(self):
        """extract_pr_sections Impact section has meta-commentary stripped."""
        spec = (
            "## Impact\n\n"
            "Here is the COMPLETE corrected spec for F044.\n"
            "This feature improves PR body quality.\n"
            "Do you want me to proceed?\n\n"
            "## What Changed\n- Added trim helpers\n"
        )
        import spec_extract
        result = spec_extract.extract_pr_sections(spec, "Test Feature")
        assert "## Impact" in result
        assert "improves PR body quality" in result
        assert "Here is the COMPLETE corrected spec" not in result
        assert "Do you want me to" not in result

    # ── F044: _strip_nm_noise tests ──

    def test_strip_nm_noise_shell_commands(self):
        """_strip_nm_noise removes shell command blocks."""
        import spec_extract
        text = "Running tests.\n```bash\n$ npm test\n$ cargo build\n```\n\nResult: all pass."
        result = spec_extract._strip_nm_noise(text)
        assert "$ npm test" not in result
        assert "```bash" not in result
        assert "Result: all pass." in result

    def test_strip_nm_noise_reasoning(self):
        """_strip_nm_noise removes reasoning noise lines."""
        import spec_extract
        text = "Let me think about this approach.\nI should check the file first.\n\nRISK: HIGH - possible race condition."
        result = spec_extract._strip_nm_noise(text)
        assert "Let me think" not in result
        assert "I should" not in result
        assert "RISK: HIGH" in result

    def test_strip_nm_noise_preserves_findings(self):
        """_strip_nm_noise preserves risk findings and file references."""
        import spec_extract
        text = "RISK: HIGH\n\nMissing error handling in utils.py:42\n\nLet me check the code.\n"
        result = spec_extract._strip_nm_noise(text)
        assert "RISK: HIGH" in result
        assert "Missing error handling in utils.py:42" in result
        assert "Let me check" not in result

    def test_extract_nm_summary_noise_stripped(self):
        """_extract_nm_summary key_findings is free of noise after filtering."""
        import spec_extract
        nm_output = (
            "You are running adversarial review.\n"
            "STAGE 1: Analyzing code...\n"
            "$ npm test\n"
            "Let me think about the results.\n"
            "RISK: MEDIUM\n"
            "Missing null check in handler.py:88\n"
            "I should verify the fix.\n"
        )
        summary = spec_extract._extract_nm_summary(nm_output)
        kf = summary["key_findings"]
        assert "$ npm test" not in kf
        assert "Let me think" not in kf
        assert "I should" not in kf
        assert "RISK: MEDIUM" in kf
        assert "Missing null check in handler.py:88" in kf
