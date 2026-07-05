"""Tests for fix mode: BLOCKED PR discovery, blocker extraction, subcommand dispatch,
--issue mode: extract_issue_sections(), run_fix_mode_issue(), branch creation, edge cases.
"""

import os
import sys
import json as _json_mod
from unittest.mock import patch

import pytest
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ═══════════════════════════════════════════════════════════════════
# BLOCKED PR discovery tests
# ═══════════════════════════════════════════════════════════════════


def test_discover_blocked_pr_none(panel):
    """No BLOCKED PRs -> returns None."""
    mock_stdout = ""
    with patch.object(panel, 'gh', return_value=(mock_stdout, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is None


def test_discover_blocked_pr_found(panel):
    """One BLOCKED PR detected by title [BLOCKED] -> returns dict."""
    import json as _json
    pr = {"number": 42, "title": "[BLOCKED] Fix login bug", "body": "PR body",
          "headRefName": "feat/fix-login", "updatedAt": "2026-06-25T10:00:00Z"}
    stdout = _json.dumps([pr])
    with patch.object(panel, 'gh', return_value=(stdout, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is not None
        assert result["number"] == 42
        assert result["headRefName"] == "feat/fix-login"


def test_discover_blocked_pr_detects_verdict(panel):
    """PR has VERDICT: BLOCKED in body -> detected."""
    import json as _json
    pr_data = {"number": 7, "title": "Some feature",
               "body": "## Review\n**Verdict:** BLOCKED",
               "headRefName": "feat/some", "updatedAt": "2026-06-25T09:00:00Z"}
    stdout = _json.dumps([pr_data])
    with patch.object(panel, 'gh', return_value=(stdout, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is not None
        assert result["number"] == 7


def test_discover_blocked_pr_detects_blockers_section(panel):
    """PR has ### Blockers section -> detected as BLOCKED."""
    import json as _json
    pr_data = {"number": 13, "title": "Some feature",
               "body": "### Blockers\n- Bug here",
               "headRefName": "feat/some", "updatedAt": "2026-06-25T08:00:00Z"}
    stdout = _json.dumps([pr_data])
    with patch.object(panel, 'gh', return_value=(stdout, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is not None
        assert result["number"] == 13


def test_discover_blocked_pr_multiple(panel):
    """Multiple BLOCKED PRs -> picks most recent (first in sorted array)."""
    import json as _json
    pr_list = [
        {"number": 11, "title": "[BLOCKED] New one", "body": "",
         "headRefName": "feat/new", "updatedAt": "2026-06-25T10:00:00Z"},
        {"number": 10, "title": "[BLOCKED] Old one", "body": "",
         "headRefName": "feat/old", "updatedAt": "2026-06-24T10:00:00Z"},
    ]
    stdout = _json.dumps(pr_list)
    with patch.object(panel, 'gh', return_value=(stdout, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is not None
        assert result["number"] == 11  # First in sorted array = most recent


# ═══════════════════════════════════════════════════════════════════
# Blocker extraction tests
# ═══════════════════════════════════════════════════════════════════


def test_extract_blockers_standard_section(panel):
    """### Blockers section -> extracts list items."""
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- Login test fails
- Missing error handling
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert len(result) == 2
    assert "Login test fails" in result


def test_extract_blockers_empty(panel):
    """No blockers found -> returns empty list."""
    pr_body = "## Review\n**Verdict:** BLOCKED\n"
    result = panel.extract_blockers_from_pr(pr_body)
    assert result == []


def test_extract_blockers_no_blockers_section(panel):
    """No ### Blockers section -> returns empty (caller handles)."""
    pr_body = "Just some PR description."
    result = panel.extract_blockers_from_pr(pr_body)
    assert result == []


def test_extract_blockers_architectural_filtered(panel):
    """ARCHITECTURAL blockers are excluded from result."""
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- Login test fails
- ARCHITECTURAL: Need to restructure DB schema
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert len(result) == 1
    assert "Login test fails" in result


def test_extract_blockers_all_architectural(panel):
    """All architectural -> returns empty list (caller checks separately)."""
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- ARCHITECTURAL: Redesign the whole system
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert result == []


# ═══════════════════════════════════════════════════════════════════
# fix subcommand parsing and dispatch to run_fix_mode
# ═══════════════════════════════════════════════════════════════════


def test_fix_flag_dispatches_to_run_fix_mode(panel, tmpdir):
    """fix subcommand should dispatch to run_fix_mode()."""
    import subprocess
    project_dir = os.path.join(str(tmpdir), "proj")
    os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
    with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
        f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")
    subprocess.run(["git", "init", project_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
    subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
    subprocess.run(["git", "-C", project_dir, "add", "-A"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "remote", "add", "origin", "https://github.com/t/t.git"])

    old_argv = sys.argv
    run_fix_args = []
    try:
        sys.argv = ['dokima', 'fix', project_dir]

        def mock_run_fix(**kwargs):
            run_fix_args.append(kwargs.get('project_dir', ''))

        with patch.object(panel, 'acquire_lock', return_value=(None, None)):
            with patch.object(panel._pipeline, 'run_fix_mode', side_effect=mock_run_fix):
                with patch.object(panel, 'load_key', return_value="test-key"):
                    with patch.object(panel, 'detect_repo', return_value="t/t"):
                        with patch.object(panel, '_set_gh_token'):
                            with patch.object(panel, 'detect_commands', return_value=("echo test", "echo build", "echo lint")):
                                panel.main()

        assert len(run_fix_args) == 1
        assert run_fix_args[0] == project_dir
    finally:
        sys.argv = old_argv


def test_fix_mode_skips_auto_archive(panel, tmpdir):
    """fix should skip auto-archive block."""
    import subprocess
    project_dir = os.path.join(str(tmpdir), "proj2")
    os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
    with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
        f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")
    subprocess.run(["git", "init", project_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
    subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
    subprocess.run(["git", "-C", project_dir, "add", "-A"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "remote", "add", "origin", "https://github.com/t/t.git"])

    old_argv = sys.argv
    archive_called = [False]
    try:
        sys.argv = ['dokima', 'fix', project_dir]

        with patch.object(panel, 'acquire_lock', return_value=(None, None)):
            with patch.object(panel._pipeline, 'run_fix_mode'):
                with patch.object(panel, 'load_key', return_value="test-key"):
                    with patch.object(panel, 'detect_repo', return_value="t/t"):
                        with patch.object(panel, '_set_gh_token'):
                            with patch.object(panel, 'detect_commands', return_value=("echo test", "echo build", "echo lint")):
                                original_listdir = os.listdir
                                def tracking_listdir(path):
                                    if 'specs' in path:
                                        archive_called[0] = True
                                    return original_listdir(path)
                                with patch('os.listdir', side_effect=tracking_listdir):
                                    panel.main()
        assert not archive_called[0], "Auto-archive should be skipped in fix mode"
    finally:
        sys.argv = old_argv


def test_fix_answers_warning(panel):
    """fix + --answers should warn and ignore answers file."""
    from io import StringIO
    old_argv = sys.argv
    captured = []
    try:
        sys.argv = ['dokima', 'fix', '--answers', '/nonexistent/answers.json']
        with patch.object(panel, 'acquire_lock', return_value=(None, None)):
            with patch.object(panel._pipeline, 'run_fix_mode'):
                with patch.object(panel, 'load_key', return_value="test-key"):
                    with patch.object(panel, 'detect_repo', return_value="t/t"):
                        with patch.object(panel, '_set_gh_token'):
                            with patch.object(panel, 'detect_commands', return_value=("echo test", "echo build", "echo lint")):
                                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                    panel.main()
                                    captured.append(mock_stdout.getvalue())
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv

    output = "".join(captured)
    assert "ERROR" not in output or "answers" not in output


# ═══════════════════════════════════════════════════════════════════
# run_fix_mode() orchestrator tests (BLOCKED PR discovery path)
# ═══════════════════════════════════════════════════════════════════


def test_run_fix_mode_discover_none(panel):
    """No BLOCKED PR -> prints message, returns."""
    with patch.object(panel, 'discover_blocked_pr', return_value=None):
        with patch.object(panel, 'gh'):
            panel.run_fix_mode("/tmp/test")
            panel.gh.assert_not_called()


def test_run_fix_mode_extracts_blockers(panel):
    """Happy path: discovers PR, extracts blockers, proceeds."""
    mock_pr = {"number": 42, "title": "[BLOCKED] Fix bug", "headRefName": "feat/fix-bug",
               "body": "## Review\n**Verdict:** BLOCKED\n\n### Blockers\n- Login fails\n- Tests broken", "updatedAt": "2026-06-25T10:00:00Z"}
    def mock_gh(*args, **kwargs):
        if "view" in args and "--json" in args:
            return ('{"state": "OPEN", "merged": false}', "", 0)
        return ("", "", 0)
    with patch.object(panel, 'discover_blocked_pr', return_value=mock_pr):
        with patch.object(panel, 'gh', side_effect=mock_gh):
            with patch.object(panel, 'git'):
                with patch.object(panel._pipeline, 'run_phase2_coder', return_value={"coder_failed": False, "pr_url": "https://github.com/t/t/pull/42"}):
                    with patch.object(panel._pipeline, 'run_phase3_vet', return_value={"nm_output": "", "pr_url": "", "coder_failed": False, "verdict": "APPROVED"}):
                        with patch.object(panel._pipeline, 'run_phase4_nm', return_value={"nm_ok": True, "pr_url": "", "risk": "LOW"}):
                            with patch.object(panel._pipeline, 'run_phase5_tech_lead', return_value={"verdict": "APPROVED", "tl_output": "All good"}):
                                with patch.dict(os.environ, {"PANEL_SKIP_HUMAN_GATE": "1"}):
                                    with patch('sys.stdout'):
                                        panel.run_fix_mode("/tmp/test")


def test_run_fix_mode_merged_pr(panel):
    """PR is already merged -> exits with message."""
    mock_pr = {"number": 42, "title": "[BLOCKED] Merged PR", "headRefName": "feat/merged",
               "body": "", "updatedAt": "2026-06-25T10:00:00Z"}
    def mock_gh(*args, **kwargs):
        if "view" in args and "--json" in args:
            return ('{"state": "OPEN", "merged": true}', "", 0)
        return ("", "", 0)
    with patch.object(panel, 'discover_blocked_pr', return_value=mock_pr):
        with patch.object(panel, 'gh', side_effect=mock_gh):
            with patch.dict(os.environ, {"PANEL_SKIP_HUMAN_GATE": "1"}):
                with patch('sys.stdout'):
                    panel.run_fix_mode("/tmp/test")


def test_run_fix_mode_no_blockers(panel):
    """PR has no blockers -> prints message."""
    mock_pr = {"number": 42, "title": "[BLOCKED] No blockers", "headRefName": "feat/none",
               "body": "## Review\n**Verdict:** BLOCKED", "updatedAt": "2026-06-25T10:00:00Z"}
    def mock_gh(*args, **kwargs):
        if "view" in args and "--json" in args:
            return ('{"state": "OPEN", "merged": false}', "", 0)
        return ("", "", 0)
    with patch.object(panel, 'discover_blocked_pr', return_value=mock_pr):
        with patch.object(panel, 'gh', side_effect=mock_gh):
            with patch.dict(os.environ, {"PANEL_SKIP_HUMAN_GATE": "1"}):
                with patch('sys.stdout'):
                    panel.run_fix_mode("/tmp/test")


def test_run_fix_mode_architectural_only(panel):
    """All blockers are architectural -> exits."""
    mock_pr = {"number": 42, "title": "[BLOCKED] Architectural",
               "headRefName": "feat/arch",
               "body": "## Review\n**Verdict:** BLOCKED\n\n### Blockers\n- ARCHITECTURAL: Redesign everything",
               "updatedAt": "2026-06-25T10:00:00Z"}
    def mock_gh(*args, **kwargs):
        if "view" in args and "--json" in args:
            return ('{"state": "OPEN", "merged": false}', "", 0)
        return ("", "", 0)
    with patch.object(panel, 'discover_blocked_pr', return_value=mock_pr):
        with patch.object(panel, 'gh', side_effect=mock_gh):
            with patch.dict(os.environ, {"PANEL_SKIP_HUMAN_GATE": "1"}):
                with patch('sys.stdout'):
                    panel.run_fix_mode("/tmp/test")


# ═══════════════════════════════════════════════════════════════════
# fix in help text
# ═══════════════════════════════════════════════════════════════════


def test_help_text_includes_fix(panel):
    """fix should appear in HELP_TEXT."""
    assert "fix" in panel.HELP_TEXT or "dokima fix" in panel.HELP_TEXT


# ──────────────────────────────────────────────────────────────
# --issue mode: extract_issue_sections() tests
# ──────────────────────────────────────────────────────────────

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
The problem is in `utils.py:42` -- internal functions use wrong naming

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
Fix `src/core/auth.py:L128` -- missing validation

### Fix
Add input validation

### Verify
Run auth tests
"""

# Multiple backtick paths -- should extract first one
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

# Backtick inside code block (triple-backtick fence) -- should NOT extract
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
        assert result["file_path"] == "pipeline.py"

    def test_malformed_unclosed_backtick(self, panel):
        result = panel.extract_issue_sections(WHAT_MALFORMED_BACKTICK)
        assert result["file_path"] == "broken.py"


# ──────────────────────────────────────────────────────────────
# --issue mode: run_fix_mode_issue() tests
# ──────────────────────────────────────────────────────────────

STRUCTURED_ISSUE_JSON = _json_mod.dumps({
    "body": "### What\n[RELIABILITY] Fix `utils.py:42` naming conventions\n\n### Fix\nRename internal functions to use _ prefix\n\n### Verify\n- [ ] Run: python3 -m pytest tests/ -q\n",
    "title": "Fix naming convention",
    "labels": []
})


class TestRunFixModeIssue:
    """Tests for run_fix_mode_issue() -- fetch issue, spawn coder, vet + nm."""

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
        """gh returns non-zero -> prints error, returns without spawning coder."""
        gh_calls = []

        def _mock_gh_fail(*args):
            gh_calls.append(args)
            return ("", "not found", 1)

        _orig_gh = panel.gh
        try:
            panel.gh = _mock_gh_fail
            result = panel.run_fix_mode_issue("/tmp/test-project", 999)
            assert result is None
        finally:
            panel.gh = _orig_gh

    def test_no_structured_sections_prints_error(self, panel):
        """Issue body without ### headings -> error message, no coder spawn."""
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
            assert result is None
        finally:
            panel.gh = _orig_gh

    # ── Additional --issue mode tests (Task 5) ──

    def test_branch_creation_pattern(self, panel):
        """Verify git is called to create fix/issue-{N} branch."""
        git_calls = []

        def _mock_git(*args):
            git_calls.append(args)
            return ("", "", 0)

        def _mock_gh(*args):
            return (STRUCTURED_ISSUE_JSON, "", 0)

        coder_result = {"coder_failed": False, "pr_url": "https://github.com/t/t/pull/99"}
        vet_result = {"coder_failed": False}
        nm_result = {"pr_url": "https://github.com/t/t/pull/99", "nm_stdout": ""}

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
            panel.git = _mock_git
            _pipeline.run_phase2_coder = lambda *a, **kw: coder_result
            _pipeline.run_phase3_vet = lambda *a, **kw: vet_result
            _pipeline.run_phase4_nm = lambda *a, **kw: nm_result

            panel.run_fix_mode_issue("/tmp/test-project", 42)

            # Verify git was called to create fix/issue-42 branch
            checkout_calls = [c for c in git_calls if "checkout" in str(c)]
            assert len(checkout_calls) > 0, f"git checkout not called: {git_calls}"
            assert any("fix/issue-42" in str(c) for c in checkout_calls), \
                f"fix/issue-42 branch not in git calls: {checkout_calls}"
        finally:
            _pipeline._make_map_hint = _orig_map_hint
            panel.gh = _orig_gh
            panel.git = _orig_git
            _pipeline.run_phase2_coder = _orig_p2
            _pipeline.run_phase3_vet = _orig_p3
            _pipeline.run_phase4_nm = _orig_p4

    def test_coder_failure_skips_vet_nm(self, panel):
        """When coder returns coder_failed=True, vet and nm are skipped."""
        vet_called = [False]
        nm_called = [False]

        def _mock_gh(*args):
            return (STRUCTURED_ISSUE_JSON, "", 0)

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
            # Coder fails
            _pipeline.run_phase2_coder = lambda *a, **kw: {"coder_failed": True, "pr_url": ""}

            def _vet_wrapper(*a, **kw):
                vet_called[0] = True
                return {"coder_failed": False}
            def _nm_wrapper(*a, **kw):
                nm_called[0] = True
                return {"pr_url": "", "nm_stdout": ""}

            _pipeline.run_phase3_vet = _vet_wrapper
            _pipeline.run_phase4_nm = _nm_wrapper

            panel.run_fix_mode_issue("/tmp/test-project", 42)

            # vet and nm should NOT be called when coder fails
            assert not vet_called[0], "vet should be skipped when coder fails"
            assert not nm_called[0], "nm should be skipped when coder fails"
        finally:
            _pipeline._make_map_hint = _orig_map_hint
            panel.gh = _orig_gh
            panel.git = _orig_git
            _pipeline.run_phase2_coder = _orig_p2
            _pipeline.run_phase3_vet = _orig_p3
            _pipeline.run_phase4_nm = _orig_p4

    def test_json_parse_failure_returns_none(self, panel):
        """Invalid JSON from gh -> returns None gracefully."""
        def _mock_gh_bad_json(*args):
            return ("not valid json {{{", "", 0)

        _orig_gh = panel.gh
        try:
            panel.gh = _mock_gh_bad_json
            result = panel.run_fix_mode_issue("/tmp/test-project", 44)
            assert result is None
        finally:
            panel.gh = _orig_gh

    def test_branch_already_exists_fallback(self, panel):
        """When git checkout -b fails, falls back to git checkout branch."""
        git_calls = []

        def _mock_git(*args):
            git_calls.append(args)
            # checkout -b fails (rc=128 = already exists)
            if "checkout" in args and "-b" in args:
                return ("", "already exists", 128)
            return ("", "", 0)

        def _mock_gh(*args):
            return (STRUCTURED_ISSUE_JSON, "", 0)

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
            panel.git = _mock_git
            _pipeline.run_phase2_coder = lambda *a, **kw: {"coder_failed": False, "pr_url": "https://github.com/t/t/pull/99"}
            _pipeline.run_phase3_vet = lambda *a, **kw: {"coder_failed": False}
            _pipeline.run_phase4_nm = lambda *a, **kw: {"pr_url": "https://github.com/t/t/pull/99", "nm_stdout": ""}

            panel.run_fix_mode_issue("/tmp/test-project", 42)

            # First call: checkout -b fix/issue-42 (fails)
            # Second call: checkout fix/issue-42 (fallback)
            checkout_calls = [c for c in git_calls if "checkout" in str(c) and "fix/issue-42" in str(c)]
            assert len(checkout_calls) >= 2, \
                f"Expected 2 checkout calls, got {len(checkout_calls)}: {git_calls}"
            # Verify the fallback call was made (without -b)
            fallback = [c for c in checkout_calls if "-b" not in c]
            assert len(fallback) >= 1, f"No fallback checkout call found: {checkout_calls}"
        finally:
            _pipeline._make_map_hint = _orig_map_hint
            panel.gh = _orig_gh
            panel.git = _orig_git
            _pipeline.run_phase2_coder = _orig_p2
            _pipeline.run_phase3_vet = _orig_p3
            _pipeline.run_phase4_nm = _orig_p4

    def test_prompt_includes_what_fix_verify(self, panel):
        """Verify the coder prompt includes What/Fix/Verify sections."""
        coder_prompts = []

        def _mock_gh(*args):
            return (STRUCTURED_ISSUE_JSON, "", 0)

        _pipeline = getattr(panel, '_pipeline', panel)
        _orig_map_hint = _pipeline._make_map_hint
        _orig_gh = panel.gh
        _orig_git = panel.git
        _orig_p2 = _pipeline.run_phase2_coder

        def _capture_p2(*a, spec="", **kw):
            coder_prompts.append(spec)
            return {"coder_failed": False, "pr_url": "https://github.com/t/t/pull/99"}

        try:
            _pipeline._make_map_hint = lambda *a, **kw: ""
            panel.gh = _mock_gh
            panel.git = lambda *a, **kw: ("", "", 0)
            _pipeline.run_phase2_coder = _capture_p2
            _pipeline.run_phase3_vet = lambda *a, **kw: {"coder_failed": False}
            _pipeline.run_phase4_nm = lambda *a, **kw: {"pr_url": "", "nm_stdout": ""}

            panel.run_fix_mode_issue("/tmp/test-project", 42)

            assert len(coder_prompts) == 1
            prompt = coder_prompts[0]
            assert "FIX MODE" in prompt
            assert "### What" in prompt
            assert "### Fix" in prompt
            assert "### Verify" in prompt
            assert "### Constraints" in prompt
            assert "Fix issue #42" in prompt
            assert "Rename internal functions" in prompt
        finally:
            _pipeline._make_map_hint = _orig_map_hint
            panel.gh = _orig_gh
            panel.git = _orig_git
            _pipeline.run_phase2_coder = _orig_p2

    def test_empty_body_from_gh_returns_none(self, panel):
        """gh returns JSON with empty body -> should return None."""
        issue_json_empty_body = _json_mod.dumps({
            "body": "",
            "title": "Empty issue",
            "labels": []
        })

        def _mock_gh(*args):
            return (issue_json_empty_body, "", 0)

        _orig_gh = panel.gh
        try:
            panel.gh = _mock_gh
            result = panel.run_fix_mode_issue("/tmp/test-project", 45)
            assert result is None
        finally:
            panel.gh = _orig_gh


# ──────────────────────────────────────────────────────────────
# CLI metadata: --issue flag must be documented
# ──────────────────────────────────────────────────────────────


def test_fix_cli_metadata_includes_issue_flag(panel):
    """CLI_METADATA fix command syntax must include --issue N."""
    cli_meta = panel._utils.CLI_METADATA
    fix_cmd = None
    for cmd in cli_meta.get("commands", []):
        if cmd.get("name") == "fix":
            fix_cmd = cmd
            break
    assert fix_cmd is not None, "fix command not found in CLI_METADATA"
    syntax = fix_cmd.get("syntax", "")
    desc = fix_cmd.get("description", "")
    # --issue N must appear in syntax or description
    has_issue = "--issue" in syntax or "--issue" in desc
    assert has_issue, (
        f"fix command must document --issue N flag. "
        f"syntax={syntax!r}, description={desc!r}"
    )
