"""Tests for cross-run learning: _extract_convention_rules and _append_convention_rules.

F033: When TL blocks a PR for a pattern violation, append a one-line rule
to specs/conventions.md under ## Cross-Run Learning section.
"""

import os
import tempfile
import pytest
import inspect
from datetime import date
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ── Sample blocker lines (output from _extract_tl_blockers) ──

# File-specific blockers — should be filtered
FILE_SPECIFIC_BLOCKERS = [
    "1. Missing null check — src/foo.py line 42: no guard for None input",
    "2. Uncaught exception — api/handler.ts line 15: no try/catch",
    "3. Dead code — utils/helpers.js line 88: unreachable function",
    "4. Infinite loop risk — pipeline.py line 1234: missing exit condition",
]

# Convention-pattern blockers — should be kept
CONVENTION_BLOCKERS = [
    "1. List args — all subprocess calls must use list args — never shell=True or string commands",
    "2. Branch detection — no hardcoded 'master' branch — always detect from origin/HEAD",
    "3. Token safety — all token values must be loaded from env, never hardcoded in source",
]

# Mixed: some file-specific, some conventions
MIXED_BLOCKERS = FILE_SPECIFIC_BLOCKERS[:2] + CONVENTION_BLOCKERS[:2]


class TestExtractConventionRules:
    """_extract_convention_rules filters file-specific blockers, keeps conventions."""

    def test_empty_list_returns_empty(self, panel):
        assert panel._extract_convention_rules([]) == []

    def test_all_file_specific_returns_empty(self, panel):
        rules = panel._extract_convention_rules(FILE_SPECIFIC_BLOCKERS)
        assert rules == []

    def test_all_conventions_returned(self, panel):
        rules = panel._extract_convention_rules(CONVENTION_BLOCKERS)
        assert len(rules) == 3

    def test_mixed_returns_only_conventions(self, panel):
        rules = panel._extract_convention_rules(MIXED_BLOCKERS)
        assert len(rules) == 2
        # Verify only convention patterns returned
        for r in rules:
            assert ".py" not in r.lower()
            assert ".ts" not in r.lower()
            assert ".js" not in r.lower()

    def test_rules_are_clean_no_number_prefix(self, panel):
        """Rules should be clean text, not numbered."""
        rules = panel._extract_convention_rules(MIXED_BLOCKERS)
        for r in rules:
            # Should not start with "N. "
            assert not (r[0].isdigit() and r[1] == "."), f"Rule still has number prefix: {r[:30]}"

    def test_output_length_not_exceed_input(self, panel):
        for blockers in (CONVENTION_BLOCKERS, MIXED_BLOCKERS, FILE_SPECIFIC_BLOCKERS):
            rules = panel._extract_convention_rules(blockers)
            assert len(rules) <= len(blockers)

    def test_single_convention_rule(self, panel):
        single = ["1. Subprocess safety — all subprocess calls must use list args"]
        rules = panel._extract_convention_rules(single)
        assert len(rules) == 1
        assert "list args" in rules[0].lower()

    def test_file_ref_with_line_number_filtered(self, panel):
        """Lines with 'line N' pattern (but no file extension) should be filtered as file-specific."""
        blockers = [
            "1. Null check — the method at line 42 has no Option unwrap check",
        ]
        rules = panel._extract_convention_rules(blockers)
        assert rules == []

    def test_no_dash_separator_skipped(self, panel):
        """Malformed line with no separator should be skipped gracefully."""
        blockers = [
            "just some text without em dash separator",
        ]
        rules = panel._extract_convention_rules(blockers)
        assert rules == []

    def test_none_input_returns_empty(self, panel):
        """None input should return empty list (defensive guard)."""
        assert panel._extract_convention_rules(None) == []

    def test_file_path_directory_pattern_filtered(self, panel):
        """Lines with 'file:', 'path:', or 'directory:' should be filtered as file-specific."""
        blockers = [
            "1. Missing guard — file: src/main.py has no null check",
            "2. Bad import — path: lib/helpers uses relative imports",
            "3. Stale ref — directory: config/ references removed schema",
        ]
        rules = panel._extract_convention_rules(blockers)
        assert rules == [], f"Expected empty, got {rules}"

    def test_blank_line_in_blockers_skipped(self, panel):
        """Empty or whitespace-only blocker lines should be skipped."""
        blockers = [
            "   ",
            "",
            "1. Convention pattern — all functions must have type hints",
        ]
        rules = panel._extract_convention_rules(blockers)
        assert len(rules) == 1
        assert "type hints" in rules[0]


class TestAppendConventionRules:
    """_append_convention_rules appends rules to specs/conventions.md."""

    def _setup_conventions(self, tmpdir, content=None):
        """Create a minimal project dir with specs/conventions.md."""
        specs_dir = os.path.join(tmpdir, "specs")
        os.makedirs(specs_dir, exist_ok=True)
        conventions_path = os.path.join(specs_dir, "conventions.md")
        if content is not None:
            with open(conventions_path, "w") as f:
                f.write(content)
        return conventions_path

    def test_empty_rules_noop(self, panel, tmp_path):
        self._setup_conventions(str(tmp_path), "# Test conventions\n")
        count = panel._append_convention_rules(str(tmp_path), [])
        assert count == 0

    def test_one_new_rule_appended(self, panel, tmp_path):
        self._setup_conventions(str(tmp_path), "# Existing conventions\n")
        rules = ["all subprocess calls must use list args"]
        count = panel._append_convention_rules(str(tmp_path), rules)
        assert count == 1

        conventions_path = os.path.join(str(tmp_path), "specs", "conventions.md")
        with open(conventions_path) as f:
            content = f.read()
        assert "## Cross-Run Learning" in content
        assert "all subprocess calls must use list args" in content
        today = date.today().isoformat()
        assert f"<!-- auto: {today}" in content

    def test_section_created_when_absent(self, panel, tmp_path):
        self._setup_conventions(str(tmp_path), "# Just some conventions\nNo cross-run section.\n")
        rules = ["never use hardcoded values"]
        count = panel._append_convention_rules(str(tmp_path), rules)
        assert count == 1
        conventions_path = os.path.join(str(tmp_path), "specs", "conventions.md")
        with open(conventions_path) as f:
            content = f.read()
        assert "## Cross-Run Learning" in content

    def test_duplicate_rule_not_reappended(self, panel, tmp_path):
        self._setup_conventions(str(tmp_path), "# Test\n")
        rules = ["use list-based subprocess args"]
        # First append
        count1 = panel._append_convention_rules(str(tmp_path), rules)
        assert count1 == 1
        # Second append — same rule
        count2 = panel._append_convention_rules(str(tmp_path), rules)
        assert count2 == 0

    def test_case_insensitive_dedup(self, panel, tmp_path):
        self._setup_conventions(str(tmp_path), "# Test\n")
        count1 = panel._append_convention_rules(str(tmp_path), ["Use List-Based Args"])
        assert count1 == 1
        count2 = panel._append_convention_rules(str(tmp_path), ["use list-based args"])
        assert count2 == 0

    def test_multiple_rules_mixed_new_and_dup(self, panel, tmp_path):
        self._setup_conventions(str(tmp_path), "# Test\n")
        # Append first two
        count1 = panel._append_convention_rules(
            str(tmp_path), ["rule alpha", "rule beta"]
        )
        assert count1 == 2
        # Append two more — one dup, one new
        count2 = panel._append_convention_rules(
            str(tmp_path), ["rule alpha", "rule gamma"]
        )
        assert count2 == 1  # only gamma is new
        # Verify file content
        conventions_path = os.path.join(str(tmp_path), "specs", "conventions.md")
        with open(conventions_path) as f:
            content = f.read()
        assert "rule alpha" in content
        assert "rule beta" in content
        assert "rule gamma" in content
        # alpha should only appear once
        assert content.count("rule alpha") == 1

    def test_no_specs_dir_created(self, panel, tmp_path):
        """conventions.md doesn't exist — should create fresh."""
        specs_dir = os.path.join(str(tmp_path), "specs")
        os.makedirs(specs_dir, exist_ok=True)
        # No conventions.md file yet
        rules = ["first learned rule"]
        count = panel._append_convention_rules(str(tmp_path), rules)
        assert count == 1
        conventions_path = os.path.join(specs_dir, "conventions.md")
        assert os.path.exists(conventions_path)
        with open(conventions_path) as f:
            content = f.read()
        assert "## Cross-Run Learning" in content
        assert "first learned rule" in content

    def test_file_ends_with_trailing_newline(self, panel, tmp_path):
        self._setup_conventions(str(tmp_path), "# Test\n")
        panel._append_convention_rules(str(tmp_path), ["a rule"])
        conventions_path = os.path.join(str(tmp_path), "specs", "conventions.md")
        with open(conventions_path) as f:
            content = f.read()
        assert content.endswith("\n")

    def test_section_header_appears_once(self, panel, tmp_path):
        self._setup_conventions(str(tmp_path), "# Test\n")
        panel._append_convention_rules(str(tmp_path), ["rule one"])
        panel._append_convention_rules(str(tmp_path), ["rule two"])
        conventions_path = os.path.join(str(tmp_path), "specs", "conventions.md")
        with open(conventions_path) as f:
            content = f.read()
        assert content.count("## Cross-Run Learning") == 1

    def test_existing_section_appends_to_end(self, panel, tmp_path):
        existing = (
            "# Test\n\n"
            "## Cross-Run Learning\n\n"
            "<!-- auto: 2026-01-01 -->\n"
            "- existing rule\n"
        )
        self._setup_conventions(str(tmp_path), existing)
        count = panel._append_convention_rules(str(tmp_path), ["new rule"])
        assert count == 1
        conventions_path = os.path.join(str(tmp_path), "specs", "conventions.md")
        with open(conventions_path) as f:
            content = f.read()
        # New rule should appear after existing rule
        new_pos = content.index("new rule")
        existing_pos = content.index("existing rule")
        assert new_pos > existing_pos, "New rule should appear after existing rule"

    def test_none_rules_returns_zero(self, panel, tmp_path):
        """None input should return 0 (defensive guard)."""
        self._setup_conventions(str(tmp_path), "# Test\n")
        assert panel._append_convention_rules(str(tmp_path), None) == 0

    def test_empty_string_rule_filtered(self, panel, tmp_path):
        """Empty-string rules in the list should be skipped, not written."""
        self._setup_conventions(str(tmp_path), "# Test\n")
        count = panel._append_convention_rules(
            str(tmp_path), ["valid rule", "", "   ", "another rule"]
        )
        assert count == 2
        conventions_path = os.path.join(str(tmp_path), "specs", "conventions.md")
        with open(conventions_path) as f:
            content = f.read()
        assert "valid rule" in content
        assert "another rule" in content

    def test_internal_batch_dedup(self, panel, tmp_path):
        """Duplicate rules within a single call should only be appended once."""
        self._setup_conventions(str(tmp_path), "# Test\n")
        count = panel._append_convention_rules(
            str(tmp_path), ["same rule", "same rule", "unique rule"]
        )
        assert count == 2  # "same rule" counted once + "unique rule"
        conventions_path = os.path.join(str(tmp_path), "specs", "conventions.md")
        with open(conventions_path) as f:
            content = f.read()
        assert content.count("same rule") == 1

    def test_specs_dir_created_when_absent(self, panel, tmp_path):
        """When specs/ directory does NOT exist, _append_convention_rules creates it."""
        # tmp_path has no specs/ dir at all
        count = panel._append_convention_rules(str(tmp_path), ["learned rule"])
        assert count == 1
        conventions_path = os.path.join(str(tmp_path), "specs", "conventions.md")
        assert os.path.exists(conventions_path)
        with open(conventions_path) as f:
            content = f.read()
        assert "## Cross-Run Learning" in content
        assert "learned rule" in content


class TestConventionRulesPipelineWiring:
    """Verify pipeline.py imports and calls the convention functions."""

    def test_pipeline_imports_convention_functions(self, panel):
        """pipeline module should import _extract_convention_rules and _append_convention_rules."""
        import pipeline
        assert hasattr(pipeline, '_extract_convention_rules'), \
            "pipeline module must import _extract_convention_rules"
        assert hasattr(pipeline, '_append_convention_rules'), \
            "pipeline module must import _append_convention_rules"

    def test_phase5_calls_convention_extraction(self, panel):
        """run_phase5_tech_lead should call _extract_convention_rules after blocker extraction."""
        source = inspect.getsource(panel.run_phase5_tech_lead)
        # Verify the convention extraction call exists
        assert '_extract_convention_rules' in source, \
            "run_phase5_tech_lead must call _extract_convention_rules"
        assert '_append_convention_rules' in source, \
            "run_phase5_tech_lead must call _append_convention_rules"
        # Verify it's called after _extract_tl_blockers
        blocker_pos = source.find('_extract_tl_blockers')
        convention_pos = source.find('_extract_convention_rules')
        assert convention_pos > blocker_pos, \
            "_extract_convention_rules must be called after _extract_tl_blockers"
        # Verify best-effort: try/except wrapping
        assert 'try:' in source[blocker_pos:], \
            "convention extraction must be wrapped in try/except (best-effort)"

    def test_phase5_prints_convention_summary(self, panel):
        """run_phase5_tech_lead should print a summary line after appending rules."""
        source = inspect.getsource(panel.run_phase5_tech_lead)
        assert 'convention rule' in source.lower(), \
            "run_phase5_tech_lead must print convention rule count summary"
