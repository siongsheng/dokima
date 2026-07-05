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
