"""Tests for extract_issue_sections() — parse ### What / ### Fix / ### Verify sections.

Covers: happy path, missing sections, edge cases (empty, None, whitespace),
file path extraction from backticks, code block handling, section ordering.
"""

import pytest
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ── Sample inputs for extraction testing ──

# Happy path: all three sections present
STRUCTURED_ISSUE = """### What
[RELIABILITY] utils.py:42: Naming conventions for internal functions

### Fix
Rename internal functions to use _ prefix per conventions.md

### Verify
- [ ] Run: python3 -m pytest tests/ -q
- [ ] Confirm: All internal functions use _ prefix
"""

# Missing optional Verify section (should still work)
NO_VERIFY = """### What
[STYLE] Missing docstring on public function

### Fix
Add docstring to the function
"""

# Only What section, no Fix (should raise ValueError)
NO_FIX = """### What
Something is broken

### Verify
Run the tests
"""

# Sections in different order: Verify before Fix
REVERSED_ORDER = """### Verify
- [ ] Run: npm test

### Fix
Update the config

### What
The config needs updating
"""

# Empty body
EMPTY_BODY = ""

# None body  
NONE_BODY = None

# Only whitespace
WHITESPACE_BODY = "   \n  \n  "

# No ### headings at all
NO_HEADINGS = "This is just some free text about an issue.\nNo structured sections here."

# Fix section with only whitespace
FIX_WHITESPACE = """### What
Something to fix

### Fix
   

### Verify
Test it
"""

# File path in backticks in What section
WHAT_WITH_FILE = """### What
The problem is in `utils.py:42` — internal functions use wrong naming

### Fix
Rename internal functions with _ prefix

### Verify
Run tests
"""

# File path without line number
WHAT_WITH_FILE_NO_LINE = """### What
Update `README.md` with new instructions

### Fix
Add the new section to README

### Verify
Review the rendered markdown
"""

# File path with L prefix
WHAT_WITH_FILE_L = """### What
Fix `src/core/auth.py:L128` — missing validation

### Fix
Add input validation

### Verify
Run auth tests
"""

# Multiple backtick paths — should extract first one
WHAT_MULTIPLE_FILES = """### What
The issue spans `frontend/app.js` and `backend/api.py:55`

### Fix
Update both files

### Verify
Integration tests pass
"""

# Backtick with no file extension
WHAT_NO_EXTENSION = """### What
See `some_script` for details

### Fix
Update the script

### Verify
Run the command
"""

# Backtick inside code block (triple-backtick fence) — should NOT extract
WHAT_CODE_BLOCK = """### What
The issue is in this code:

```python
# fix `utils.py:42` here
x = 1
```

The real fix is in `pipeline.py:100`

### Fix
Fix the pipeline

### Verify
Run tests
"""

# Sections with leading/trailing whitespace
WHAT_WITH_WHITESPACE = """### What

   [CLEANUP] Remove dead code from `cleanup.py`

### Fix


   Delete unused functions

### Verify


   No import errors
"""

# Malformed backtick (unclosed)
WHAT_MALFORMED_BACKTICK = """### What
The file `broken.py is missing a closing backtick

### Fix
Fix the formatting

### Verify
Check syntax
"""


# ── Happy path tests ──

class TestExtractIssueSectionsHappyPath:
    def test_all_sections_present(self, panel):
        result = panel.extract_issue_sections(STRUCTURED_ISSUE)
        assert result["what"] == "[RELIABILITY] utils.py:42: Naming conventions for internal functions"
        assert result["fix"] == "Rename internal functions to use _ prefix per conventions.md"
        assert "- [ ] Run:" in result["verify"]
        assert "file_path" in result

    def test_optional_verify_missing(self, panel):
        result = panel.extract_issue_sections(NO_VERIFY)
        assert result["fix"] == "Add docstring to the function"
        assert result["verify"] == ""
        assert result["what"] == "[STYLE] Missing docstring on public function"

    def test_sections_reversed_order(self, panel):
        result = panel.extract_issue_sections(REVERSED_ORDER)
        assert result["what"] == "The config needs updating"
        assert result["fix"] == "Update the config"
        assert "- [ ] Run: npm test" in result["verify"]

    def test_whitespace_sections_trimmed(self, panel):
        result = panel.extract_issue_sections(WHAT_WITH_WHITESPACE)
        assert result["what"] == "[CLEANUP] Remove dead code from `cleanup.py`"
        assert result["fix"] == "Delete unused functions"
        assert result["verify"] == "No import errors"

    def test_return_dict_has_all_keys(self, panel):
        result = panel.extract_issue_sections(STRUCTURED_ISSUE)
        assert set(result.keys()) == {"what", "fix", "verify", "file_path"}


# ── Error case tests ──

class TestExtractIssueSectionsErrors:
    def test_empty_body_raises_valueerror(self, panel):
        with pytest.raises(ValueError):
            panel.extract_issue_sections(EMPTY_BODY)

    def test_none_body_raises_valueerror(self, panel):
        with pytest.raises(ValueError):
            panel.extract_issue_sections(NONE_BODY)

    def test_whitespace_body_raises_valueerror(self, panel):
        with pytest.raises(ValueError):
            panel.extract_issue_sections(WHITESPACE_BODY)

    def test_no_headings_raises_valueerror(self, panel):
        with pytest.raises(ValueError):
            panel.extract_issue_sections(NO_HEADINGS)

    def test_missing_fix_raises_valueerror(self, panel):
        with pytest.raises(ValueError):
            panel.extract_issue_sections(NO_FIX)

    def test_fix_whitespace_only_raises_valueerror(self, panel):
        with pytest.raises(ValueError):
            panel.extract_issue_sections(FIX_WHITESPACE)


# ── File path extraction tests ──

class TestExtractIssueSectionsFilePath:
    def test_backtick_with_line_number(self, panel):
        result = panel.extract_issue_sections(WHAT_WITH_FILE)
        assert result["file_path"] == "utils.py"

    def test_backtick_without_line_number(self, panel):
        result = panel.extract_issue_sections(WHAT_WITH_FILE_NO_LINE)
        assert result["file_path"] == "README.md"

    def test_backtick_with_L_prefix(self, panel):
        result = panel.extract_issue_sections(WHAT_WITH_FILE_L)
        assert result["file_path"] == "src/core/auth.py"

    def test_multiple_backtick_paths_returns_first(self, panel):
        result = panel.extract_issue_sections(WHAT_MULTIPLE_FILES)
        assert result["file_path"] == "frontend/app.js"

    def test_no_backtick_paths_returns_none(self, panel):
        result = panel.extract_issue_sections(REVERSED_ORDER)
        assert result["file_path"] is None

    def test_backtick_no_extension_ignored(self, panel):
        result = panel.extract_issue_sections(WHAT_NO_EXTENSION)
        assert result["file_path"] is None

    def test_backtick_in_code_block_not_extracted(self, panel):
        result = panel.extract_issue_sections(WHAT_CODE_BLOCK)
        # Should extract pipeline.py:100 (outside code block), not utils.py:42 (inside)
        assert result["file_path"] == "pipeline.py"

    def test_malformed_unclosed_backtick(self, panel):
        result = panel.extract_issue_sections(WHAT_MALFORMED_BACKTICK)
        # Should get "broken.py" from unclosed backtick
        assert result["file_path"] == "broken.py"


# ──────────────────────────────────────────────────────────────
# Tests for run_fix_mode_issue() — Task 3 TDD (RED phase)
# ──────────────────────────────────────────────────────────────

import json as _json_mod
from unittest.mock import patch as _mock_patch

STRUCTURED_ISSUE_JSON = _json_mod.dumps({
    "body": "### What\n[RELIABILITY] Fix `utils.py:42` naming conventions\n\n### Fix\nRename internal functions to use _ prefix\n\n### Verify\n- [ ] Run: python3 -m pytest tests/ -q\n",
    "title": "Fix naming convention",
    "labels": []
})


class TestRunFixModeIssue:
    """Tests for run_fix_mode_issue() — fetch issue, spawn coder, vet + nm."""

    def test_function_exists(self, panel):
        """run_fix_mode_issue must be callable on the panel."""
        assert hasattr(panel, 'run_fix_mode_issue')
        assert callable(panel.run_fix_mode_issue)

    def test_happy_path_spawns_coder(self, panel):
        """Happy path: fetch structured issue, spawn coder, run vet + nm."""
        gh_calls = []

        def _mock_gh(*args):
            gh_calls.append(args)
            return (STRUCTURED_ISSUE_JSON, "", 0)

        coder_result = {"coder_failed": False, "pr_url": "https://github.com/t/t/pull/99"}
        vet_result = {"coder_failed": False}
        nm_result = {"pr_url": "https://github.com/t/t/pull/99", "nm_stdout": ""}

        # Patch _make_map_hint on the pipeline module (via panel._pipeline)
        # and the phase functions so internal calls go through mocks
        _pipeline = getattr(panel, '_pipeline', panel)

        _orig_map_hint = _pipeline._make_map_hint
        _orig_gh = panel.gh
        _orig_git = panel.git
        _orig_p2 = _pipeline.run_phase2_coder
        _orig_p3 = _pipeline.run_phase3_vet
        _orig_p4 = _pipeline.run_phase4_nm

        try:
            _pipeline._make_map_hint = lambda *a, **kw: ""
            panel.gh = _mock_gh
            panel.git = lambda *a, **kw: ("", "", 0)
            _pipeline.run_phase2_coder = lambda *a, **kw: coder_result
            _pipeline.run_phase3_vet = lambda *a, **kw: vet_result
            _pipeline.run_phase4_nm = lambda *a, **kw: nm_result

            panel.run_fix_mode_issue("/tmp/test-project", 42)

            # Verify gh was called with issue number 42
            assert any("42" in str(c) for c in gh_calls), \
                f"gh not called with issue 42: {gh_calls}"
        finally:
            _pipeline._make_map_hint = _orig_map_hint
            panel.gh = _orig_gh
            panel.git = _orig_git
            _pipeline.run_phase2_coder = _orig_p2
            _pipeline.run_phase3_vet = _orig_p3
            _pipeline.run_phase4_nm = _orig_p4

    def test_issue_fetch_failure_returns_gracefully(self, panel):
        """gh returns non-zero → prints error, returns without spawning coder."""
        gh_calls = []

        def _mock_gh_fail(*args):
            gh_calls.append(args)
            return ("", "not found", 1)

        _orig_gh = panel.gh
        try:
            panel.gh = _mock_gh_fail
            result = panel.run_fix_mode_issue("/tmp/test-project", 999)
            # Should not raise, and should return None or similar
            assert result is None
        finally:
            panel.gh = _orig_gh

    def test_no_structured_sections_prints_error(self, panel):
        """Issue body without ### headings → error message, no coder spawn."""
        issue_json_no_sections = _json_mod.dumps({
            "body": "This is just free text with no structured format.",
            "title": "Some issue",
            "labels": []
        })

        def _mock_gh(*args):
            return (issue_json_no_sections, "", 0)

        _orig_gh = panel.gh
        try:
            panel.gh = _mock_gh
            result = panel.run_fix_mode_issue("/tmp/test-project", 43)
            # Should not raise, should return None
            assert result is None
        finally:
            panel.gh = _orig_gh
