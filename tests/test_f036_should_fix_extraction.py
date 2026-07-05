"""Tests for extract_should_fix_from_text() — all extraction formats, edge cases, dedup.

Covers: table format, prose format, bullet format, integration scenarios,
edge cases (empty, None, whitespace, no SHOULD FIX), and deduplication.
"""

import pytest
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ── Sample inputs for extraction testing ──

# Table format: single row with all columns
TABLE_SINGLE = """### SHOULD FIX (1)

| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions for internal functions |
"""

# Table format: multi-row with mixed severities
TABLE_MULTI = """### Findings

| ID | DIMENSION | LOCATION | SEVERITY | DETAIL |
|---|---|---|---|---|
| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions |
| B1 | SECURITY | auth.py:15 | BLOCKER | Missing auth check |
| R2 | MAINTAINABILITY | pipeline.py:100 | SHOULD FIX | Extract long method |
| N1 | STYLE | app.py:5 | NIT | Whitespace trailing |
"""

# Table format: missing columns (3 columns — id, severity, detail only)
TABLE_MISSING_COLS = """| R1 | SHOULD FIX | Use snake_case |"""

# Table format: extra columns (6+ columns)
TABLE_EXTRA_COLS = """| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming | extra1 | extra2 |"""

# Table format: escaped pipes in detail
TABLE_ESCAPED_PIPES = """| R1 | RELIABILITY | utils.py | SHOULD FIX | Use pipe \\| symbol for separator |"""

# Table format: no SHOULD FIX rows
TABLE_NO_MATCH = """### Findings

| ID | DIMENSION | LOCATION | SEVERITY | DETAIL |
| B1 | SECURITY | auth.py:15 | BLOCKER | Missing auth |
| N1 | STYLE | app.py:5 | NIT | Whitespace |
"""

# Prose format: em-dash separator
PROSE_EM_DASH = "SHOULD FIX — Update AGENTS.md with new command"

# Prose format: colon separator
PROSE_COLON = "SHOULD FIX: Add type hints to public functions"

# Prose format: mixed case
PROSE_LOWERCASE = "should fix — rename variable to follow convention"

# Prose format: SHOULD FIX in middle of sentence (context-only, NOT extracted)
PROSE_CONTEXT_ONLY = "the BLOCKER requires changes that we SHOULD FIX in next sprint phase"

# Prose format: SHOULD FIX with no description
PROSE_NO_DESC = "SHOULD FIX:"

# Prose format: SHOULD FIX with no separator (no colon or em-dash)
PROSE_NO_SEPARATOR = "SHOULD FIX this later"

# Bullet format: dash prefix
BULLET_DASH = "- SHOULD FIX: Add type annotations"

# Bullet format: asterisk prefix
BULLET_STAR = "* SHOULD FIX — Rename internal functions to use _ prefix"

# Integration: full TL output with table-format findings (real-world scenario)
FULL_TL_WITH_TABLE = """### BLOCKERS (2 — must fix before merge)

**1. Missing error handling**
dokima:276: Unconditionally replaces output.

**2. Spec violation in phase 3**
pipeline.py:450: Skip logic doesn't respect depth gating.

### SHOULD FIX (1)

| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions for internal functions |

### NIT (1)

| N1 | STYLE | app.py:10 | NIT | Format with black |

VERDICT: BLOCKED
RISK: HIGH"""

# Integration: prose-only TL output (current format)
FULL_TL_PROSE = """VERDICT: CHANGES REQUESTED
RISK: MEDIUM

SHOULD FIX: rename variable in utils.py:42
SHOULD FIX — update AGENTS.md with new command

RELEASE: YES minor"""


# ── extract_should_fix_from_text() unit tests ──

class TestExtractShouldFixFromTextTableFormat:
    """Table format: pipe-delimited rows with SHOULD FIX severity."""

    def test_single_table_row(self, panel):
        result = panel.extract_should_fix_from_text(TABLE_SINGLE)
        assert len(result) == 1
        assert result[0]["id"] == "R1"
        assert result[0]["dimension"] == "RELIABILITY"
        assert result[0]["location"] == "utils.py:42"
        assert result[0]["detail"] == "Naming conventions for internal functions"

    def test_multi_row_mixed_severity(self, panel):
        result = panel.extract_should_fix_from_text(TABLE_MULTI)
        assert len(result) == 2
        ids = [r["id"] for r in result]
        assert "R1" in ids
        assert "R2" in ids
        # BLOCKER and NIT rows should NOT be extracted
        assert "B1" not in ids
        assert "N1" not in ids

    def test_missing_columns(self, panel):
        result = panel.extract_should_fix_from_text(TABLE_MISSING_COLS)
        assert len(result) == 1
        assert result[0]["id"] == "R1"
        assert result[0]["detail"] == "Use snake_case"
        # Missing columns get empty string
        assert result[0]["dimension"] == ""

    def test_extra_columns_appended_to_detail(self, panel):
        result = panel.extract_should_fix_from_text(TABLE_EXTRA_COLS)
        assert len(result) == 1
        assert result[0]["id"] == "R1"
        # Extra columns are appended to detail
        assert "extra1" in result[0]["detail"]
        assert "extra2" in result[0]["detail"]

    def test_escaped_pipes_in_detail(self, panel):
        result = panel.extract_should_fix_from_text(TABLE_ESCAPED_PIPES)
        assert len(result) == 1
        # The backslash-escaped pipe should be preserved in detail
        assert "|" in result[0]["detail"]

    def test_no_matching_rows_empty(self, panel):
        result = panel.extract_should_fix_from_text(TABLE_NO_MATCH)
        assert result == []

    def test_shoULD_fix_case_insensitive_in_table(self, panel):
        text = "| R1 | SECURITY | auth.py | should fix | lowercase severity |"
        result = panel.extract_should_fix_from_text(text)
        assert len(result) == 1
        assert result[0]["detail"] == "lowercase severity"

    def test_should_fix_in_non_severity_column(self, panel):
        """SHOULD FIX in detail column, not severity column — should NOT match."""
        text = "| R1 | RELIABILITY | utils.py | NIT | consider SHOULD FIX here |"
        result = panel.extract_should_fix_from_text(text)
        assert result == []

    def test_table_with_spacing_variants(self, panel):
        """SHOULD FIX with extra spaces."""
        text = "| R1 | RELIABILITY | utils.py:42 | SHOULD   FIX | Use snake_case |"
        result = panel.extract_should_fix_from_text(text)
        assert len(result) == 1
        assert result[0]["detail"] == "Use snake_case"


class TestExtractShouldFixFromTextProseFormat:
    """Prose format: keyword + separator patterns."""

    def test_em_dash_separator(self, panel):
        result = panel.extract_should_fix_from_text(PROSE_EM_DASH)
        assert len(result) == 1
        assert result[0]["detail"] == "Update AGENTS.md with new command"
        assert result[0]["id"] == ""

    def test_colon_separator(self, panel):
        result = panel.extract_should_fix_from_text(PROSE_COLON)
        assert len(result) == 1
        assert result[0]["detail"] == "Add type hints to public functions"

    def test_lowercase_should_fix(self, panel):
        result = panel.extract_should_fix_from_text(PROSE_LOWERCASE)
        assert len(result) == 1
        assert result[0]["detail"] == "rename variable to follow convention"

    def test_context_only_not_extracted(self, panel):
        """SHOULD FIX in middle of sentence with no separator — NOT extracted."""
        result = panel.extract_should_fix_from_text(PROSE_CONTEXT_ONLY)
        assert result == []

    def test_empty_detail_skipped(self, panel):
        """SHOULD FIX with colon but empty detail."""
        result = panel.extract_should_fix_from_text(PROSE_NO_DESC)
        assert result == []

    def test_no_separator_not_extracted(self, panel):
        """SHOULD FIX followed by content but no colon or em-dash — NOT extracted."""
        result = panel.extract_should_fix_from_text(PROSE_NO_SEPARATOR)
        assert result == []

    def test_quoted_description_preserved(self, panel):
        text = 'SHOULD FIX: "use named exports throughout"'
        result = panel.extract_should_fix_from_text(text)
        assert len(result) == 1
        assert '"use named exports throughout"' == result[0]["detail"]

    def test_multiple_em_dashes_first_splits(self, panel):
        """First em-dash is the separator; rest stays in detail."""
        text = "SHOULD FIX — conventions — naming — internal"
        result = panel.extract_should_fix_from_text(text)
        assert len(result) == 1
        # First em-dash splits, rest stays
        assert "conventions" in result[0]["detail"]
        assert "internal" in result[0]["detail"]


class TestExtractShouldFixFromTextBulletFormat:
    """Bullet format: dash/asterisk prefix before SHOULD FIX."""

    def test_dash_bullet(self, panel):
        result = panel.extract_should_fix_from_text(BULLET_DASH)
        assert len(result) == 1
        assert result[0]["detail"] == "Add type annotations"

    def test_asterisk_bullet(self, panel):
        result = panel.extract_should_fix_from_text(BULLET_STAR)
        assert len(result) == 1
        assert result[0]["detail"] == "Rename internal functions to use _ prefix"


class TestExtractShouldFixFromTextEdgeCases:
    """Edge cases: empty, None, whitespace, dedup."""

    def test_empty_string(self, panel):
        assert panel.extract_should_fix_from_text("") == []

    def test_none_input(self, panel):
        assert panel.extract_should_fix_from_text(None) == []

    def test_whitespace_only(self, panel):
        assert panel.extract_should_fix_from_text("   \n  \n  ") == []

    def test_no_should_fix_at_all(self, panel):
        assert panel.extract_should_fix_from_text("VERDICT: APPROVED\nAll good.") == []

    def test_unicode_emoji_in_detail(self, panel):
        text = "SHOULD FIX: add 🚀 emoji support to output ✨"
        result = panel.extract_should_fix_from_text(text)
        assert len(result) == 1
        assert "🚀" in result[0]["detail"]
        assert "✨" in result[0]["detail"]

    def test_all_four_keys_present(self, panel):
        """Every returned dict must have all four keys."""
        result = panel.extract_should_fix_from_text(PROSE_EM_DASH)
        for r in result:
            for key in ("id", "dimension", "location", "detail"):
                assert key in r, f"Missing key '{key}' in result dict"

    def test_deduplication_case_insensitive(self, panel):
        """Two identical findings differing only in case → one result."""
        text = (
            "SHOULD FIX: naming convention for internal functions\n"
            "SHOULD FIX: Naming Convention for Internal Functions"
        )
        result = panel.extract_should_fix_from_text(text)
        assert len(result) == 1

    def test_deduplication_punctuation_stripped(self, panel):
        """Two findings where one has trailing period → one result."""
        text = (
            "SHOULD FIX: naming convention\n"
            "SHOULD FIX: naming convention."
        )
        result = panel.extract_should_fix_from_text(text)
        assert len(result) == 1

    def test_non_duplicates_not_merged(self, panel):
        """Different detail text → separate results."""
        text = (
            "SHOULD FIX: Update docs\n"
            "SHOULD FIX: Update docs in AGENTS.md"
        )
        result = panel.extract_should_fix_from_text(text)
        assert len(result) == 2

    def test_mixed_table_and_prose(self, panel):
        """Both table and prose formats in same input."""
        text = (
            "| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions |\n"
            "SHOULD FIX: add type hints to public functions\n"
        )
        result = panel.extract_should_fix_from_text(text)
        assert len(result) >= 1  # at least one extracted


class TestExtractShouldFixFromTextIntegration:
    """Integration scenarios — full TL output."""

    def test_full_tl_with_table_findings(self, panel):
        """Real-world: TL output with table-format SHOULD FIX block."""
        result = panel.extract_should_fix_from_text(FULL_TL_WITH_TABLE)
        assert len(result) == 1
        assert result[0]["id"] == "R1"
        assert result[0]["dimension"] == "RELIABILITY"
        assert result[0]["detail"] == "Naming conventions for internal functions"
        # BLOCKER rows should NOT be extracted as SHOULD FIX
        details = [r["detail"] for r in result]
        assert "Missing error handling" not in details

    def test_full_tl_prose_format(self, panel):
        """Real-world: TL output with prose SHOULD FIX lines."""
        result = panel.extract_should_fix_from_text(FULL_TL_PROSE)
        assert len(result) >= 1
        details = [r["detail"] for r in result]
        assert any("rename variable" in d for d in details)
        assert any("update agents.md" in d.lower() for d in details)

    def test_nm_stdout_style(self, panel):
        """nm-style output with table findings — should extract SHOULD FIX rows."""
        text = """| ID | DIMENSION | LOCATION | SEVERITY | DETAIL |
| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions |
| R2 | MAINTAINABILITY | pipeline.py | SHOULD FIX | Extract long method |"""
        result = panel.extract_should_fix_from_text(text)
        assert len(result) == 2
        assert result[0]["id"] == "R1"
        assert result[1]["id"] == "R2"


# ── Pipeline wiring tests ──

# TL output with table-format SHOULD FIX for pipeline integration testing
PIPELINE_TL_OUTPUT = """### BLOCKERS (1 — must fix before merge)

**1. Missing error handling**
dokima:276: Unconditionally replaces output.

### SHOULD FIX (2)

| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Use snake_case for internal functions |
| R2 | MAINTAINABILITY | pipeline.py:100 | SHOULD FIX | Extract long method |

VERDICT: BLOCKED
RISK: MEDIUM"""


class TestPipelineWiringShouldFix:
    """Pipeline-level tests: review comment fetch, tl_output fallback, issue creation."""

    def test_should_fix_issues_created_from_tl_output(self, panel):
        """When tl_output has SHOULD FIX items, issues are created."""
        from unittest.mock import patch
        import types

        # Mock gh to capture issue creation calls
        issue_calls = []
        def gh_se(*args, **kwargs):
            if len(args) >= 2:
                cmd = args[0]
                # gh api PATCH (PR body update) — succeed silently
                if cmd == "api":
                    return ("", "", 0)
                # gh issue create — capture and succeed
                if cmd == "issue" and args[1] == "create":
                    issue_calls.append({"args": args, "kwargs": kwargs})
                    return ("https://github.com/t/t/issues/99", "", 0)
                # gh pr view --comments (review comment fetch — no comment available)
                if cmd == "pr":
                    return ("", "", 1)  # fail → fallback to tl_output
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        # Mock call_agent so phase 5 doesn't try to spawn a real TL
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            result = panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        # Verify issues were created for SHOULD FIX items
        assert len(issue_calls) >= 1, "Expected at least 1 SHOULD FIX issue"
        # Check that structured dict fields are used in issue creation
        created_titles = []
        for call in issue_calls:
            title = None
            args = call["args"]
            for i, a in enumerate(args):
                if a == "--title" and i + 1 < len(args):
                    title = args[i + 1]
            if title:
                created_titles.append(title)
        assert any("SHOULD FIX" in t for t in created_titles), \
            f"Issue titles should contain SHOULD FIX, got: {created_titles}"

    def test_review_comment_fetch_primary_source(self, panel):
        """When PR review comment is available, it should be used as primary source."""
        from unittest.mock import patch

        review_comment_body = (
            "### SHOULD FIX (1)\n\n"
            "| R1 | RELIABILITY | utils.py:42 | SHOULD FIX | Naming conventions |\n"
        )

        issue_calls = []
        pr_view_calls = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                pr_view_calls.append(args)
                return (review_comment_body, "", 0)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                issue_calls.append(args)
                return ("https://github.com/t/t/issues/100", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        # Verify gh pr view was called to fetch review comment
        assert len(pr_view_calls) >= 1, "Expected gh pr view --comments call"
        # Verify issues were created from review comment
        assert len(issue_calls) >= 1, "Expected issues from review comment"

    def test_tl_output_fallback_when_review_fails(self, panel):
        """When gh pr view fails, fall back to tl_output for SHOULD FIX extraction."""
        from unittest.mock import patch

        issue_calls = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "gh: Not Found", 1)  # Simulate failure
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                issue_calls.append(args)
                return ("https://github.com/t/t/issues/101", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        # Issues should still be created from tl_output fallback
        assert len(issue_calls) >= 1, \
            "Expected SHOULD FIX issues from tl_output fallback when review fetch fails"

    def test_dimension_prefix_in_issue_title(self, panel):
        """Table-format findings should include dimension prefix in issue title."""
        from unittest.mock import patch

        issue_calls = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)  # fallback to tl_output
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                issue_calls.append(args)
                return ("https://github.com/t/t/issues/102", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_calls) >= 1
        # Check for dimension prefix in title (e.g., "SHOULD FIX [RELIABILITY]: ...")
        for call_args in issue_calls:
            title = None
            for i, a in enumerate(call_args):
                if a == "--title" and i + 1 < len(call_args):
                    title = call_args[i + 1]
            if title:
                # Table-format findings should have dimension prefix
                assert "SHOULD FIX" in title, f"Title should have SHOULD FIX: {title}"

    def test_issue_cap_of_five_preserved(self, panel):
        """No more than 5 SHOULD FIX issues should be created per run."""
        from unittest.mock import patch

        # Generate TL output with 8 SHOULD FIX items
        many_sf_lines = []
        for i in range(1, 9):
            many_sf_lines.append(
                f"| R{i} | RELIABILITY | file{i}.py:{i * 10} | SHOULD FIX | Issue {i} detail |"
            )
        tl_output_with_many = (
            "### SHOULD FIX (8)\n\n" + "\n".join(many_sf_lines) +
            "\n\nVERDICT: BLOCKED\nRISK: LOW"
        )

        issue_calls = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                issue_calls.append(args)
                return ("https://github.com/t/t/issues/999", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=tl_output_with_many):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_calls) <= 5, \
            f"Should create at most 5 issues, got {len(issue_calls)}"


# ══════════════════════════════════════════════════════════════
# Tests for upgraded SHOULD FIX issue body format (Task 6)
# ══════════════════════════════════════════════════════════════

class TestGenerateFixInstruction:
    """Unit tests for _generate_fix_instruction() — each keyword category branch."""

    def test_naming_convention_keywords(self, panel):
        """Keywords like 'naming', 'convention', 'snake_case' trigger naming response."""
        f = panel._pipeline._generate_fix_instruction
        result = f({"detail": "Use snake_case naming", "dimension": "", "location": ""})
        assert "naming conventions" in result.lower()

    def test_convention_dimension(self, panel):
        """CONVENTION/STYLE dimension triggers project conventions response with location."""
        f = panel._pipeline._generate_fix_instruction
        result = f({"detail": "Format with black", "dimension": "STYLE",
                     "location": "app.py:5"})
        assert "project conventions" in result.lower()
        assert "app.py:5" in result

    def test_missing_test_keywords(self, panel):
        """Keywords like 'missing test', 'add test', 'untested' trigger test coverage."""
        f = panel._pipeline._generate_fix_instruction
        result = f({"detail": "Missing test for edge case", "dimension": "",
                     "location": "utils.py:42"})
        assert "test coverage" in result.lower()
        assert "utils.py:42" in result

    def test_doc_keywords(self, panel):
        """Keywords like 'doc', 'stale', 'outdated' trigger documentation update."""
        f = panel._pipeline._generate_fix_instruction
        result = f({"detail": "Documentation is stale", "dimension": "",
                     "location": "README.md"})
        assert "documentation" in result.lower()
        assert "README.md" in result

    def test_redundant_keywords(self, panel):
        """Keywords like 'redundant', 'dead code', 'unused' trigger remove code."""
        f = panel._pipeline._generate_fix_instruction
        result = f({"detail": "Dead code in old module", "dimension": "",
                     "location": "legacy.py"})
        assert "redundant or unused" in result.lower()

    def test_maintainability_dimension(self, panel):
        """MAINTAINABILITY dimension triggers refactor response."""
        f = panel._pipeline._generate_fix_instruction
        result = f({"detail": "Long method needs splitting", "dimension": "MAINTAINABILITY",
                     "location": "pipeline.py:450"})
        assert "maintainability" in result.lower()

    def test_generic_with_location(self, panel):
        """When no keyword matches and location present → 'Address the finding in {loc}'."""
        f = panel._pipeline._generate_fix_instruction
        result = f({"detail": "Review threading model", "dimension": "PERFORMANCE",
                     "location": "agent.py:30"})
        assert "Address the finding in agent.py:30" in result

    def test_generic_no_location(self, panel):
        """When no keyword matches and no location → 'Address the finding: {detail}'."""
        f = panel._pipeline._generate_fix_instruction
        result = f({"detail": "Review threading model", "dimension": "", "location": ""})
        assert result == "Address the finding: Review threading model"


class TestGenerateVerifySection:
    """Unit tests for _generate_verify_section() — each keyword category branch."""

    def test_first_line_is_run_command(self, panel):
        """Verify section always starts with '- [ ] Run: <test_cmd>'."""
        f = panel._pipeline._generate_verify_section
        result = f({"detail": "Some finding", "dimension": ""}, "npm test")
        lines = result.split("\n")
        assert lines[0] == "- [ ] Run: npm test"

    def test_naming_convention_verify(self, panel):
        """Naming keywords → 'All names follow project conventions'."""
        f = panel._pipeline._generate_verify_section
        result = f({"detail": "Use snake_case", "dimension": ""}, "pytest")
        assert "All names follow project conventions" in result

    def test_missing_test_verify(self, panel):
        """Missing test keywords → 'New tests pass and cover the scenario'."""
        f = panel._pipeline._generate_verify_section
        result = f({"detail": "Missing test for parse", "dimension": ""}, "pytest")
        assert "New tests pass and cover the scenario" in result

    def test_doc_verify(self, panel):
        """Doc keywords → 'Documentation accurately reflects current behavior'."""
        f = panel._pipeline._generate_verify_section
        result = f({"detail": "Stale docs in README", "dimension": ""}, "pytest")
        assert "Documentation accurately reflects current behavior" in result

    def test_redundant_verify(self, panel):
        """Redundant keywords → 'No regressions in existing tests'."""
        f = panel._pipeline._generate_verify_section
        result = f({"detail": "Unused variable", "dimension": ""}, "pytest")
        assert "No regressions in existing tests" in result

    def test_maintainability_dimension_verify(self, panel):
        """MAINTAINABILITY dimension → 'Refactored code passes all existing tests'."""
        f = panel._pipeline._generate_verify_section
        result = f({"detail": "Long method", "dimension": "MAINTAINABILITY"}, "pytest")
        assert "Refactored code passes all existing tests" in result

    def test_generic_verify(self, panel):
        """No keyword match → 'Finding resolved per the Fix instruction above'."""
        f = panel._pipeline._generate_verify_section
        result = f({"detail": "Review threading model", "dimension": "PERFORMANCE"}, "cargo test")
        assert "Finding resolved per the Fix instruction above" in result


class TestUpgradedIssueBodyFormat:
    """Verify the upgraded body format (### What / ### Fix / ### Verify / ### Source)
    is used in SHOULD FIX issue creation and old markers are absent."""

    def test_body_has_what_fix_verify_source_sections(self, panel):
        """Issue body must contain ### What, ### Fix, ### Verify, ### Source sections."""
        from unittest.mock import patch

        issue_body = None

        def gh_se(*args, **kwargs):
            nonlocal issue_body
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)  # fallback to tl_output
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                # Capture --body argument
                for i, a in enumerate(args):
                    if a == "--body" and i + 1 < len(args):
                        issue_body = args[i + 1]
                return ("https://github.com/t/t/issues/200", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        tl_out = PIPELINE_TL_OUTPUT

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=tl_out):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert issue_body is not None, "Expected issue body to be captured"
        assert "### What" in issue_body, f"Missing ### What in body:\n{issue_body}"
        assert "### Fix" in issue_body, f"Missing ### Fix in body:\n{issue_body}"
        assert "### Verify" in issue_body, f"Missing ### Verify in body:\n{issue_body}"
        assert "### Source" in issue_body, f"Missing ### Source in body:\n{issue_body}"
        assert "- [ ] Run:" in issue_body, "Verify section must have test command"

    def test_body_has_no_old_format_markers(self, panel):
        """Issue body must NOT contain old format markers."""
        from unittest.mock import patch

        issue_body = None

        def gh_se(*args, **kwargs):
            nonlocal issue_body
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                for i, a in enumerate(args):
                    if a == "--body" and i + 1 < len(args):
                        issue_body = args[i + 1]
                return ("https://github.com/t/t/issues/201", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert issue_body is not None, "Expected issue body to be captured"
        assert "## Tech Lead Review Finding" not in issue_body, \
            f"Old format marker found in body:\n{issue_body}"
        assert "### Finding" not in issue_body, \
            f"Old '### Finding' section found in body:\n{issue_body}"
        assert "### Context" not in issue_body, \
            f"Old '### Context' section found in body:\n{issue_body}"

    def test_what_section_has_dim_loc_prefix(self, panel):
        """When dimension AND location present → [DIM] loc: desc format."""
        from unittest.mock import patch

        issue_bodies = []

        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                for i, a in enumerate(args):
                    if a == "--body" and i + 1 < len(args):
                        issue_bodies.append(args[i + 1])
                return ("https://github.com/t/t/issues/202", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_bodies) >= 1
        # Table-format findings have dimension + location → should have [DIM] loc: desc
        found_dim_loc = any(
            "[RELIABILITY] utils.py:42" in body for body in issue_bodies
        )
        assert found_dim_loc, \
            f"Expected [DIM] loc: desc format in at least one body:\n{issue_bodies}"

    def test_source_section_has_pr_branch_spec(self, panel):
        """Source section must contain PR, Branch, and Spec references."""
        from unittest.mock import patch

        issue_body = None

        def gh_se(*args, **kwargs):
            nonlocal issue_body
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                for i, a in enumerate(args):
                    if a == "--body" and i + 1 < len(args):
                        issue_body = args[i + 1]
                return ("https://github.com/t/t/issues/203", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert issue_body is not None
        assert "- PR:" in issue_body, f"Missing PR ref in Source:\n{issue_body}"
        assert "- Branch:" in issue_body, f"Missing Branch ref in Source:\n{issue_body}"
        assert "- Spec:" in issue_body, f"Missing Spec ref in Source:\n{issue_body}"

    def test_issue_body_has_what_fix_verify_source_headings(self, panel):
        """Issue body must have ### What, ### Fix, ### Verify, ### Source headings."""
        from unittest.mock import patch

        issue_calls = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                issue_calls.append(args)
                return ("https://github.com/t/t/issues/200", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_calls) >= 1, "Expected at least 1 SHOULD FIX issue"
        for call_args in issue_calls:
            body = None
            for i, a in enumerate(call_args):
                if a == "--body" and i + 1 < len(call_args):
                    body = call_args[i + 1]
            assert body is not None, "Issue must have --body"
            assert "### What" in body, f"Missing ### What in body: {body[:200]}"
            assert "### Fix" in body, f"Missing ### Fix in body: {body[:200]}"
            assert "### Verify" in body, f"Missing ### Verify in body: {body[:200]}"
            assert "### Source" in body, f"Missing ### Source in body: {body[:200]}"

    def test_issue_body_what_includes_location(self, panel):
        """### What section must include file location from table-format finding."""
        from unittest.mock import patch

        issue_calls = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                issue_calls.append(args)
                return ("https://github.com/t/t/issues/201", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_calls) >= 1
        # First finding in PIPELINE_TL_OUTPUT is R1 with location utils.py:42
        body = None
        for i, a in enumerate(issue_calls[0]):
            if a == "--body" and i + 1 < len(issue_calls[0]):
                body = issue_calls[0][i + 1]
        assert body is not None
        # The ### What section should mention the location
        what_idx = body.find("### What")
        assert what_idx != -1, "Missing ### What heading"
        what_section = body[what_idx:]
        assert "utils.py" in what_section, \
            f"### What should include utils.py location, got: {what_section[:300]}"

    def test_issue_body_source_has_pr_link(self, panel):
        """### Source section must include PR link."""
        from unittest.mock import patch

        issue_calls = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                issue_calls.append(args)
                return ("https://github.com/t/t/issues/202", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        pr_url = "https://github.com/t/t/pull/1"
        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", pr_url,
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_calls) >= 1
        body = None
        for i, a in enumerate(issue_calls[0]):
            if a == "--body" and i + 1 < len(issue_calls[0]):
                body = issue_calls[0][i + 1]
        assert body is not None
        source_idx = body.find("### Source")
        assert source_idx != -1, "Missing ### Source heading"
        source_section = body[source_idx:]
        assert pr_url in source_section, \
            f"### Source should include PR URL {pr_url}, got: {source_section[:300]}"
        assert "feat/test" in source_section, \
            f"### Source should include branch, got: {source_section[:300]}"

    def test_issue_body_no_old_finding_context_sections(self, panel):
        """Issue body must NOT contain the old ### Finding or ### Context sections."""
        from unittest.mock import patch

        issue_calls = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                issue_calls.append(args)
                return ("https://github.com/t/t/issues/203", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_calls) >= 1
        for call_args in issue_calls:
            body = None
            for i, a in enumerate(call_args):
                if a == "--body" and i + 1 < len(call_args):
                    body = call_args[i + 1]
            assert body is not None
            assert "### Finding" not in body, \
                f"Old ### Finding section should not be in body: {body[:300]}"
            assert "### Context" not in body, \
                f"Old ### Context section should not be in body: {body[:300]}"

    def test_issue_body_fix_has_actionable_content(self, panel):
        """### Fix section must contain actionable instruction, not empty."""
        from unittest.mock import patch

        issue_calls = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                issue_calls.append(args)
                return ("https://github.com/t/t/issues/204", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), \
             patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_calls) >= 1
        body = None
        for i, a in enumerate(issue_calls[0]):
            if a == "--body" and i + 1 < len(issue_calls[0]):
                body = issue_calls[0][i + 1]
        assert body is not None
        fix_idx = body.find("### Fix")
        assert fix_idx != -1, "Missing ### Fix heading"
        # Find the Fix section content (between ### Fix and next ### heading)
        fix_section = body[fix_idx:]
        next_heading = fix_section.find("\n###", 7)  # skip past "### Fix\n"
        fix_content = fix_section[7:next_heading].strip() if next_heading != -1 else fix_section[7:].strip()
        assert len(fix_content) >= 10, \
            f"### Fix should have at least 10 chars of content, got: '{fix_content}'"

class TestWhatLineFormatVariations:
    """what_line construction: [DIM] loc: desc, [DIM] desc, loc: desc, desc-only."""

    def test_dim_and_loc_produces_full_prefix(self, panel):
        """dim + loc -> '[DIM] loc: desc' format in What section."""
        from unittest.mock import patch

        issue_bodies = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                for i, a in enumerate(args):
                    if a == "--body" and i + 1 < len(args):
                        issue_bodies.append(args[i + 1])
                return ("https://github.com/t/t/issues/300", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_bodies) >= 1
        found = any(
            "[RELIABILITY] utils.py:42:" in b for b in issue_bodies
        )
        assert found, f"Expected [DIM] loc: desc format: {issue_bodies}"

    def test_dim_only_produces_dim_prefix(self, panel):
        """dim only (no loc) -> '[DIM] desc' format in What section."""
        from unittest.mock import patch

        issue_bodies = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                for i, a in enumerate(args):
                    if a == "--body" and i + 1 < len(args):
                        issue_bodies.append(args[i + 1])
                return ("https://github.com/t/t/issues/301", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        tl_dim_only = (
            "### SHOULD FIX (1)\n\n"
            "| R1 | SECURITY | | SHOULD FIX | Review auth flow |\n\n"
            "VERDICT: BLOCKED\nRISK: MEDIUM"
        )

        with patch("time.sleep"), patch.object(panel, "spawn_agent", return_value=tl_dim_only):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_bodies) >= 1
        found = any(
            "[SECURITY]" in b and "Review auth flow" in b for b in issue_bodies
        )
        assert found, f"Expected [DIM] desc format: {issue_bodies}"

    def test_loc_only_produces_location_prefix(self, panel):
        """loc only (no dim) -> 'loc: desc' format in What section."""
        from unittest.mock import patch

        issue_bodies = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                for i, a in enumerate(args):
                    if a == "--body" and i + 1 < len(args):
                        issue_bodies.append(args[i + 1])
                return ("https://github.com/t/t/issues/302", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        tl_loc_only = (
            "### SHOULD FIX (1)\n\n"
            "| R1 | | config.py:10 | SHOULD FIX | Update defaults |\n\n"
            "VERDICT: BLOCKED\nRISK: LOW"
        )

        with patch("time.sleep"), patch.object(panel, "spawn_agent", return_value=tl_loc_only):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_bodies) >= 1
        found = any(
            "config.py:10:" in b and "Update defaults" in b for b in issue_bodies
        )
        assert found, f"Expected loc: desc format: {issue_bodies}"

    def test_no_dim_no_loc_uses_plain_desc(self, panel):
        """No dim, no loc -> desc used as-is in What section."""
        from unittest.mock import patch

        issue_bodies = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                for i, a in enumerate(args):
                    if a == "--body" and i + 1 < len(args):
                        issue_bodies.append(args[i + 1])
                return ("https://github.com/t/t/issues/303", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        tl_prose = "SHOULD FIX: add type hints to public functions\nVERDICT: CHANGES REQUESTED\nRISK: LOW"

        with patch("time.sleep"), patch.object(panel, "spawn_agent", return_value=tl_prose):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_bodies) >= 1
        found = any(
            "add type hints to public functions" in b for b in issue_bodies
        )
        assert found, f"Expected plain desc in What: {issue_bodies}"


class TestVerifySectionStructure:
    """Verify that the ### Verify section always has a test command line."""

    def test_verify_starts_with_run_checkbox(self, panel):
        """### Verify must have a '- [ ] Run:' line as first entry."""
        from unittest.mock import patch

        issue_bodies = []
        def gh_se(*args, **kwargs):
            cmd = args[0] if args else ""
            if cmd == "pr":
                return ("", "", 1)
            if cmd == "api":
                return ("", "", 0)
            if cmd == "issue" and len(args) >= 2 and args[1] == "create":
                for i, a in enumerate(args):
                    if a == "--body" and i + 1 < len(args):
                        issue_bodies.append(args[i + 1])
                return ("https://github.com/t/t/issues/304", "", 0)
            return ("", "", 0)

        panel.gh = gh_se
        panel.git = lambda *a, **kw: ("", "", 0)
        panel._set_gh_token = lambda *a, **kw: None
        panel.load_key = lambda: "fk"
        panel.load_github_token = lambda: "ft"
        panel.detect_repo = lambda: "t/t"
        panel.call_agent = lambda *a, **kw: {"content": "Mock", "tokens": 1}

        with patch("time.sleep"), patch.object(panel, "spawn_agent", return_value=PIPELINE_TL_OUTPUT):
            panel.run_phase5_tech_lead(
                "Test Feature", "https://github.com/t/t/pull/1",
                "feat/test", "/tmp/spec.md", "LOW"
            )

        assert len(issue_bodies) >= 1
        for body in issue_bodies:
            verify_idx = body.find("### Verify")
            assert verify_idx != -1
            verify_section = body[verify_idx:]
            next_section = verify_section.find("\n###", 10)
            verify_content = verify_section[:next_section] if next_section != -1 else verify_section
            lines = [l.strip() for l in verify_content.split("\n") if l.strip()]
            assert any(l.startswith("- [ ] Run:") for l in lines), \
                f"### Verify must have '- [ ] Run:' line: {verify_content[:200]}"
