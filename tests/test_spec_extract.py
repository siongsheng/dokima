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
