"""Tests for fix mode: BLOCKED PR discovery, blocker extraction, subcommand, dispatch."""
import os
import sys
import pytest
from unittest.mock import patch

from conftest import _load_panel as _load


# ═══════════════════════════════════════════════════════════════════
# Task 3: discover_blocked_pr()
# ═══════════════════════════════════════════════════════════════════


def test_discover_blocked_pr_none(panel):
    """No BLOCKED PRs → returns None."""
    mock_stdout = ""
    with patch.object(panel, 'gh', return_value=(mock_stdout, "", 0)):
        result = panel.discover_blocked_pr()
        assert result is None


def test_discover_blocked_pr_found(panel):
    """One BLOCKED PR detected by title [BLOCKED] → returns dict."""
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
    """PR has VERDICT: BLOCKED in body → detected."""
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
    """PR has ### Blockers section → detected as BLOCKED."""
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
    """Multiple BLOCKED PRs → picks most recent (first in sorted array)."""
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
# Task 4: extract_blockers_from_pr()
# ═══════════════════════════════════════════════════════════════════


def test_extract_blockers_standard_section(panel):
    """### Blockers section → extracts list items."""
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
    """No blockers found → returns empty list."""
    pr_body = "## Review\n**Verdict:** BLOCKED\n"
    result = panel.extract_blockers_from_pr(pr_body)
    assert result == []


def test_extract_blockers_no_blockers_section(panel):
    """No ### Blockers section → returns empty (caller handles)."""
    pr_body = "Just some PR description."
    result = panel.extract_blockers_from_pr(pr_body)
    assert result == []


def test_extract_blockers_returns_all_including_architectural(panel):
    """H1: extract_blockers_from_pr returns ALL blockers including architectural.

    The ARCHITECTURAL filter should NOT be in extract_blockers_from_pr —
    it should be in run_fix_mode as the single filtering point.
    This prevents the triple-pass filtering that silently drops real blockers.
    """
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- Login test fails
- ARCHITECTURAL: Need to restructure DB schema
- Function missing error handling
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert len(result) == 3, (
        f"H1 regression: expected 3 blockers (including ARCHITECTURAL), got {len(result)}: {result}"
    )
    assert "Login test fails" in result[0]
    assert "ARCHITECTURAL" in result[1]


def test_extract_blockers_returns_architectural_even_when_only(panel):
    """H1: extract_blockers_from_pr returns architectural blockers even when alone."""
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- ARCHITECTURAL: Redesign the whole system
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert len(result) == 1, (
        f"H1 regression: expected 1 architectural blocker, got {len(result)}: {result}"
    )
    assert "ARCHITECTURAL" in result[0]


def test_extract_blockers_architectural_filtered(panel):
    """ARCHITECTURAL blockers are now INCLUDED in extract_blockers_from_pr result.

    H1 fix: extract_blockers_from_pr returns ALL blockers. The architectural
    filter is consolidated in run_fix_mode as the single filtering point.
    """
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- Login test fails
- ARCHITECTURAL: Need to restructure DB schema
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert len(result) == 2  # Both blockers returned — includes ARCHITECTURAL
    assert "Login test fails" in result


def test_extract_blockers_all_architectural(panel):
    """All architectural → returns all items (caller filters separately).

    H1 fix: extract_blockers_from_pr no longer removes ARCHITECTURAL.
    The caller (run_fix_mode) is now the single filtering point.
    """
    pr_body = """## Review
**Verdict:** BLOCKED

### Blockers
- ARCHITECTURAL: Redesign the whole system
"""
    result = panel.extract_blockers_from_pr(pr_body)
    assert len(result) == 1
    assert "ARCHITECTURAL" in result[0]


# ═══════════════════════════════════════════════════════════════════
# Task 1+2: fix subcommand parsing and dispatch to run_fix_mode
# ═══════════════════════════════════════════════════════════════════


def test_fix_flag_dispatches_to_run_fix_mode(panel, tmpdir):
    """fix subcommand should dispatch to run_fix_mode()."""
    import subprocess
    import json as _json
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
    old_cwd = os.getcwd
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

        # Track if auto-archive block runs
        with patch.object(panel, 'acquire_lock', return_value=(None, None)):
            with patch.object(panel._pipeline, 'run_fix_mode'):
                with patch.object(panel, 'load_key', return_value="test-key"):
                    with patch.object(panel, 'detect_repo', return_value="t/t"):
                        with patch.object(panel, '_set_gh_token'):
                            with patch.object(panel, 'detect_commands', return_value=("echo test", "echo build", "echo lint")):
                                # Monkey-patch os.listdir to detect if auto-archive runs
                                original_listdir = os.listdir
                                def tracking_listdir(path):
                                    if 'specs' in path:
                                        archive_called[0] = True
                                    return original_listdir(path)
                                with patch('os.listdir', side_effect=tracking_listdir):
                                    panel.main()
        # Archive should NOT have been called for fix mode
        assert not archive_called[0], "Auto-archive should be skipped in fix mode"
    finally:
        sys.argv = old_argv


def test_fix_answers_warning(panel):
    """fix + --answers should warn and ignore answers file."""
    from io import StringIO
    import contextlib
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
    # Should not crash — at minimum no "ERROR: Feature description required" from fix mode path
    assert "ERROR" not in output or "answers" not in output


# ═══════════════════════════════════════════════════════════════════
# Task 5+6+7: run_fix_mode() orchestrator
# ═══════════════════════════════════════════════════════════════════


def test_run_fix_mode_discover_none(panel):
    """No BLOCKED PR → prints message, returns."""
    with patch.object(panel, 'discover_blocked_pr', return_value=None):
        with patch.object(panel, 'gh'):
            panel.run_fix_mode("/tmp/test")
            panel.gh.assert_not_called()


def test_run_fix_mode_extracts_blockers(panel):
    """Happy path: discovers PR, extracts blockers, proceeds."""
    mock_pr = {"number": 42, "title": "[BLOCKED] Fix bug", "headRefName": "feat/fix-bug",
               "body": "## Review\n**Verdict:** BLOCKED\n\n### Blockers\n- Login fails\n- Tests broken", "updatedAt": "2026-06-25T10:00:00Z"}
    # Mock gh for PR view (not merged, not closed) and git
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
    """PR is already merged → exits with message."""
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
    # Should not crash


def test_run_fix_mode_no_blockers(panel):
    """PR has no blockers → prints message."""
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
    # Should not crash


def test_run_fix_mode_architectural_only(panel):
    """All blockers are architectural → exits."""
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
    # Should not crash


# ═══════════════════════════════════════════════════════════════════
# Task 8: fix in help text
# ═══════════════════════════════════════════════════════════════════


def test_help_text_includes_fix(panel):
    """fix should appear in HELP_TEXT."""
    assert "fix" in panel.HELP_TEXT or "dokima fix" in panel.HELP_TEXT


# ═══════════════════════════════════════════════════════════════════
# F034: --issue N flag for fix mode
# ═══════════════════════════════════════════════════════════════════


def test_fix_with_issue_dispatches_to_run_fix_mode_issue(panel, tmpdir):
    """fix --issue 42 dispatches to run_fix_mode_issue, not run_fix_mode."""
    import subprocess
    project_dir = os.path.join(str(tmpdir), "proj3")
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
    fix_mode_issue_args = []
    fix_mode_args = []
    did_exit = [False]
    try:
        sys.argv = ['dokima', 'fix', '--issue', '42', project_dir]

        def mock_run_fix_mode_issue(**kwargs):
            fix_mode_issue_args.append(kwargs)

        def mock_run_fix_mode(**kwargs):
            fix_mode_args.append(kwargs)

        with patch.object(panel, 'acquire_lock', return_value=(None, None)):
            with patch.object(panel._pipeline, 'run_fix_mode_issue', side_effect=mock_run_fix_mode_issue, create=True):
                with patch.object(panel._pipeline, 'run_fix_mode', side_effect=mock_run_fix_mode):
                    with patch.object(panel, 'load_key', return_value="test-key"):
                        with patch.object(panel, 'detect_repo', return_value="t/t"):
                            with patch.object(panel, '_set_gh_token'):
                                with patch.object(panel, 'detect_commands', return_value=("echo test", "echo build", "echo lint")):
                                    panel.main()

        assert len(fix_mode_issue_args) == 1
        assert fix_mode_issue_args[0].get("issue_number") == 42
        assert fix_mode_issue_args[0].get("project_dir") == project_dir
        assert len(fix_mode_args) == 0
    except SystemExit:
        did_exit[0] = True
    finally:
        sys.argv = old_argv

    if did_exit[0]:
        pytest.fail("panel.main() exited with SystemExit — --issue arg not recognized")


# ═══════════════════════════════════════════════════════════════════
# F034: extract_issue_sections() — unit tests
# ═══════════════════════════════════════════════════════════════════

STRUCTURED_ISSUE_BODY = """### What
[RELIABILITY] utils.py:42: Naming conventions for internal functions

### Fix
Rename internal functions to use _ prefix per conventions.md

### Verify
- [ ] Run: python3 -m pytest tests/ -q
- [ ] Confirm: All internal functions use _ prefix, no naming lint warnings
"""


def test_extract_issue_sections_all_fields(panel):
    """Parses full structured body, returns dict with all four keys populated."""
    from utils import extract_issue_sections
    result = extract_issue_sections(STRUCTURED_ISSUE_BODY)
    assert result["what"] == "[RELIABILITY] utils.py:42: Naming conventions for internal functions"
    assert result["fix"] == "Rename internal functions to use _ prefix per conventions.md"
    assert "Run: python3 -m pytest tests/ -q" in result["verify"]
    assert result["file_path"] == "utils.py"


def test_extract_issue_sections_missing_verify(panel):
    """Verify section is optional, returns empty string."""
    from utils import extract_issue_sections
    body = "### What\nSome finding\n\n### Fix\nDo something\n"
    result = extract_issue_sections(body)
    assert result["what"] == "Some finding"
    assert result["fix"] == "Do something"
    assert result["verify"] == ""


def test_extract_issue_sections_missing_fix(panel):
    """Fix section is required, raises ValueError."""
    from utils import extract_issue_sections
    import pytest as _pytest
    with _pytest.raises(ValueError):
        extract_issue_sections("### What\nSome finding\n\n### Verify\nCheck it\n")


def test_extract_issue_sections_file_path_backtick(panel):
    """Extracts path.py:42 from What section."""
    from utils import extract_issue_sections
    body = "### What\n`src/core/auth.py:L128`\n\n### Fix\nUpdate auth\n"
    result = extract_issue_sections(body)
    assert result["file_path"] == "src/core/auth.py"


def test_extract_issue_sections_no_backtick_path(panel):
    """No backtick path → file_path is None."""
    from utils import extract_issue_sections
    body = "### What\nSome plain text finding\n\n### Fix\nDo it\n"
    result = extract_issue_sections(body)
    assert result["file_path"] is None


def test_extract_issue_sections_empty_body(panel):
    """Empty issue body → ValueError."""
    from utils import extract_issue_sections
    import pytest as _pytest
    with _pytest.raises(ValueError):
        extract_issue_sections("")


def test_extract_issue_sections_no_sections(panel):
    """Issue body has no ### headings → ValueError."""
    from utils import extract_issue_sections
    import pytest as _pytest
    with _pytest.raises(ValueError):
        extract_issue_sections("Just some free text without headings.")


def test_extract_issue_sections_none_input(panel):
    """None input → ValueError (spec Section 10: Failure modes)."""
    from utils import extract_issue_sections
    import pytest as _pytest
    with _pytest.raises(ValueError):
        extract_issue_sections(None)


# ═══════════════════════════════════════════════════════════════════
# F034: run_fix_mode_issue() — unit tests
# ═══════════════════════════════════════════════════════════════════


def test_run_fix_mode_issue_happy_path(panel):
    """Mock gh to return structured issue body, verify coder is spawned."""
    from unittest.mock import patch, ANY
    import json as _json
    import pipeline as _pipeline

    issue_body = _json.dumps({
        "body": "### What\n[RELIABILITY] utils.py:42: Naming issue\n\n### Fix\nRename function\n\n### Verify\nRun tests\n",
        "title": "SHOULD FIX: Naming conventions"
    })

    gh_calls = []
    git_calls = []

    def mock_gh(*args, **kwargs):
        gh_calls.append(args)
        if "view" in args and "--json" in args:
            return (issue_body, "", 0)
        if "issue" in args and "create" in args:
            return ("https://github.com/t/t/issues/99", "", 0)
        return ("", "", 0)

    def mock_git(*args, **kwargs):
        git_calls.append(args)
        return ("", "", 0)

    with patch.object(_pipeline, 'gh', side_effect=mock_gh):
        with patch.object(_pipeline, 'git', side_effect=mock_git):
            with patch.object(_pipeline, 'run_phase2_coder', return_value={"coder_failed": False, "pr_url": "https://github.com/t/t/pull/99"}):
                with patch.object(_pipeline, 'run_phase3_vet', return_value={"coder_failed": False}):
                    with patch.object(_pipeline, 'run_phase4_nm', return_value={"nm_ok": True, "pr_url": "https://github.com/t/t/pull/99"}):
                        with patch.object(_pipeline, '_set_gh_token'):
                            with patch.object(_pipeline, 'detect_repo', return_value="t/t"):
                                with patch('sys.stdout'):
                                    _pipeline.run_fix_mode_issue("/tmp/test", 42)

    # Verify gh issue view was called with issue 42
    view_calls = [c for c in gh_calls if "view" in c and "42" in map(str, c)]
    assert len(view_calls) >= 1, "Expected gh issue view for #42"

    # Verify fix/issue-42 branch was created
    branch_calls = [c for c in git_calls if "fix/issue-42" in " ".join(map(str, c))]
    assert len(branch_calls) >= 1, "Expected fix/issue-42 branch checkout"


def test_run_fix_mode_issue_nonexistent(panel):
    """gh returns non-zero for issue fetch → prints error, exits cleanly."""
    from unittest.mock import patch
    import pipeline as _pipeline

    def mock_gh(*args, **kwargs):
        if "view" in args and "--json" in args:
            return ("", "not found", 1)
        return ("", "", 0)

    with patch.object(_pipeline, 'gh', side_effect=mock_gh):
        with patch.object(_pipeline, '_set_gh_token'):
            with patch.object(_pipeline, 'detect_repo', return_value="t/t"):
                with patch('sys.stdout'):
                    # Should not raise — exits cleanly
                    _pipeline.run_fix_mode_issue("/tmp/test", 999)


def test_run_fix_mode_issue_no_sections(panel):
    """Issue body has no ### What / ### Fix → prints error."""
    from unittest.mock import patch
    import json as _json
    import pipeline as _pipeline

    issue_body = _json.dumps({
        "body": "Just some free-form text without structured sections.",
        "title": "Random issue"
    })

    def mock_gh(*args, **kwargs):
        if "view" in args and "--json" in args:
            return (issue_body, "", 0)
        return ("", "", 0)

    with patch.object(_pipeline, 'gh', side_effect=mock_gh):
        with patch.object(_pipeline, '_set_gh_token'):
            with patch.object(_pipeline, 'detect_repo', return_value="t/t"):
                with patch('sys.stdout'):
                    # Should not raise — exits cleanly
                    _pipeline.run_fix_mode_issue("/tmp/test", 77)


def test_run_fix_mode_issue_branch_created(panel):
    """Verify fix/issue-{N} branch name pattern is created."""
    from unittest.mock import patch
    import json as _json
    import pipeline as _pipeline

    issue_body = _json.dumps({
        "body": "### What\nFix something\n\n### Fix\nDo it\n",
        "title": "Test issue"
    })

    git_calls = []

    def mock_gh(*args, **kwargs):
        if "view" in args and "--json" in args:
            return (issue_body, "", 0)
        return ("", "", 0)

    def mock_git(*args, **kwargs):
        git_calls.append(args)
        return ("", "", 0)

    with patch.object(_pipeline, 'gh', side_effect=mock_gh):
        with patch.object(_pipeline, 'git', side_effect=mock_git):
            with patch.object(_pipeline, 'run_phase2_coder', return_value={"coder_failed": False, "pr_url": "https://github.com/t/t/pull/99"}):
                with patch.object(_pipeline, 'run_phase3_vet', return_value={"coder_failed": False}):
                    with patch.object(_pipeline, 'run_phase4_nm', return_value={"nm_ok": True, "pr_url": "https://github.com/t/t/pull/99"}):
                        with patch.object(_pipeline, '_set_gh_token'):
                            with patch.object(_pipeline, 'detect_repo', return_value="t/t"):
                                with patch('sys.stdout'):
                                    _pipeline.run_fix_mode_issue("/tmp/test", 55)

    branch_names = []
    for call in git_calls:
        for i, arg in enumerate(call):
            if arg == "-b" and i + 1 < len(call):
                branch_names.append(call[i + 1])
    assert "fix/issue-55" in branch_names, f"Expected fix/issue-55 branch, got: {branch_names}"


def test_extract_issue_sections_multiple_file_paths(panel):
    """Multiple backtick paths → first one returned."""
    from utils import extract_issue_sections
    body = "### What\n`src/a.py` and also `src/b.py`\n\n### Fix\nFix both\n"
    result = extract_issue_sections(body)
    assert result["file_path"] == "src/a.py"


def test_extract_issue_sections_code_block_not_extracted(panel):
    """Backtick in triple-backtick code block → NOT extracted as file path."""
    from utils import extract_issue_sections
    body = "### What\n```\nnot_a_real_file.py\n```\nReal finding\n\n### Fix\nDo it\n"
    result = extract_issue_sections(body)
    # The code block should be stripped from content
    assert "not_a_real_file.py" not in result["what"]
