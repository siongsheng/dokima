"""Tests for run_add_to_roadmap() — auto-prioritize and insert feature blocks."""
import os
import re
import pytest

ROADMAP_EMPTY = ""
ROADMAP_MINIMAL = """# Roadmap

## Phase 1: Core

### F001: Security
**Priority:** P0
**Dependencies:** None
**Status:** [ ] Pending
**User Story:** As a user, I am secure.
"""

ROADMAP_MULTI_SECTION = """# Roadmap

## Phase 1: Core

### F001: Security Hardening
**Priority:** P0
**Dependencies:** None
**Status:** [x] Done
**User Story:** As a user, I am secure.

## Phase 2: Features

### F002: Dark Mode
**Priority:** P1
**Dependencies:** None
**Status:** [ ] Pending
**User Story:** As a user, I can toggle dark mode.

## Icebox

### F003: Someday Feature
**Priority:** P3
**Dependencies:** None
**Status:** [ ] Pending
**User Story:** As a user, someday.
"""

ROADMAP_WITH_SECURITY_DEPS = """# Roadmap

## Phase 1: Core

### F001: Authentication System
**Priority:** P0
**Dependencies:** None
**Status:** [ ] Pending
**User Story:** As a user, I can log in.

### F002: Password Security Audit
**Priority:** P0
**Dependencies:** F001
**Status:** [ ] Pending
**User Story:** As a user, my password security is audited.
"""


def _setup_roadmap(tmpdir, content):
    """Create specs/roadmap.md in tmpdir with given content."""
    specs_dir = os.path.join(tmpdir, "specs")
    os.makedirs(specs_dir, exist_ok=True)
    roadmap_path = os.path.join(specs_dir, "roadmap.md")
    with open(roadmap_path, "w") as f:
        f.write(content)
    return roadmap_path


def _read_roadmap(tmpdir):
    """Read specs/roadmap.md from tmpdir."""
    return open(os.path.join(tmpdir, "specs", "roadmap.md")).read()


class TestRunAddToRoadmap:
    """Tests for run_add_to_roadmap() — auto-priority, dependencies, insertion."""

    def test_add_first_feature_gets_f001(self, panel, tmpdir_path):
        """Empty roadmap -> F001."""
        _setup_roadmap(tmpdir_path, ROADMAP_EMPTY)
        panel.run_add_to_roadmap("Dark mode toggle", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "### F001: Dark mode toggle" in content
        assert "**Priority:** P1" in content
        assert "**Dependencies:** None" in content

    def test_add_second_feature_gets_f002(self, panel, tmpdir_path):
        """Existing F001 -> F002."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Logging system", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "### F002: Logging system" in content

    def test_security_keyword_gets_p0(self, panel, tmpdir_path):
        """'security' keyword -> P0."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Fix security vulnerability in login", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P0" in content

    def test_crash_keyword_gets_p0(self, panel, tmpdir_path):
        """'crash' keyword -> P0."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Fix crash on empty input", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P0" in content

    def test_injection_keyword_gets_p0(self, panel, tmpdir_path):
        """'injection' keyword -> P0."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("SQL injection via user import", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P0" in content

    def test_silent_failure_keyword_gets_p0(self, panel, tmpdir_path):
        """'silent failure' keyword -> P0."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Fix silent failure when API key missing", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P0" in content

    def test_docs_keyword_gets_p2(self, panel, tmpdir_path):
        """'docs' keyword -> P2."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Update documentation for API", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P2" in content

    def test_portability_keyword_gets_p2(self, panel, tmpdir_path):
        """'portability' keyword -> P2."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Improve portability across platforms", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P2" in content

    def test_someday_keyword_gets_p3(self, panel, tmpdir_path):
        """'someday' -> P3."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Add AI chatbot someday", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P3" in content

    def test_icebox_keyword_gets_p3(self, panel, tmpdir_path):
        """'icebox' -> P3."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Icebox: full text search", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P3" in content

    def test_default_gets_p1(self, panel, tmpdir_path):
        """No keyword match -> P1."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Add user avatar upload", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P1" in content

    def test_explicit_priority_overrides_keyword(self, panel, tmpdir_path):
        """--priority=P2 overrides P0 keyword detection."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Fix critical security hole", tmpdir_path, priority_hint="P2")
        content = _read_roadmap(tmpdir_path)
        assert "**Priority:** P2" in content

    def test_placed_in_correct_section_p0(self, panel, tmpdir_path):
        """P0 -> Phase 1 section."""
        _setup_roadmap(tmpdir_path, ROADMAP_MULTI_SECTION)
        panel.run_add_to_roadmap("Security breach fix", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        phase1_end = content.index("## Phase 2")
        assert "### F004: Security breach fix" in content[:phase1_end]

    def test_placed_in_correct_section_p1(self, panel, tmpdir_path):
        """P1 -> Phase 2 section."""
        _setup_roadmap(tmpdir_path, ROADMAP_MULTI_SECTION)
        panel.run_add_to_roadmap("User notification system", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "### F004: User notification system" in content

    def test_placed_in_icebox_for_p3(self, panel, tmpdir_path):
        """P3 -> Icebox section."""
        _setup_roadmap(tmpdir_path, ROADMAP_MULTI_SECTION)
        panel.run_add_to_roadmap("Maybe add VR support someday", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        icebox_start = content.index("## Icebox")
        after_icebox = content[icebox_start:]
        assert "### F004: Maybe add VR support someday" in after_icebox

    def test_dependency_detection_keyword_overlap(self, panel, tmpdir_path):
        """Features with keyword overlap -> dependency on pending feature."""
        _setup_roadmap(tmpdir_path, ROADMAP_WITH_SECURITY_DEPS)
        # "password security" overlaps with "Password Security Audit" (F002)
        # Both share "password" (8 chars >= 4) and "security" (8 chars >= 4) => >=2 overlap
        panel.run_add_to_roadmap("Password security hardening", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "### F003: Password security hardening" in content
        f003_match = re.search(r'### F003: Password security hardening\n(.*?)(?=###|\Z)', content, re.DOTALL)
        assert f003_match
        f003_body = f003_match.group(1)
        assert "F002" in f003_body  # Depends on F002

    def test_no_dependency_on_done_features(self, panel, tmpdir_path):
        """Keyword overlap with [x] Done feature -> no dependency."""
        _setup_roadmap(tmpdir_path, ROADMAP_MULTI_SECTION)
        # F001 is [x] Done (Security Hardening)
        # "security" overlaps with F001 title but F001 is done -> no dep
        panel.run_add_to_roadmap("Security monitoring dashboard", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        f004_match = re.search(r'### F004: Security monitoring dashboard\n(.*?)(?=###|\Z)', content, re.DOTALL)
        assert f004_match
        f004_body = f004_match.group(1)
        assert "**Dependencies:** None" in f004_body

    def test_user_story_generated(self, panel, tmpdir_path):
        """User Story auto-generated from description."""
        _setup_roadmap(tmpdir_path, ROADMAP_MINIMAL)
        panel.run_add_to_roadmap("Export data to CSV", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "as a user, i can export data to csv." in content.lower()

    def test_missing_roadmap_exits_gracefully(self, panel, tmpdir_path):
        """No roadmap.md -> sys.exit(1)."""
        # No specs/ directory created
        with pytest.raises(SystemExit) as exc:
            panel.run_add_to_roadmap("Some feature", tmpdir_path)
        assert exc.value.code == 1

    def test_id_increments_past_existing_highest(self, panel, tmpdir_path):
        """Finds highest existing F-number, even with gaps."""
        content = """# Roadmap\n\n## Phase 1\n\n### F005: Some Feature\n**Priority:** P0\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** T.\n\n### F012: Another Feature\n**Priority:** P1\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** T.\n"""
        _setup_roadmap(tmpdir_path, content)
        panel.run_add_to_roadmap("New thing", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        assert "### F013: New thing" in content

    # ── Execution priority ordering tests ──

    def test_test_feature_inserted_before_security(self, panel, tmpdir_path):
        """P0 test (score 10) inserted before P0 security (score 40)."""
        content = """# Roadmap

## Phase 1: Core

### F001: Security Hardening
**Priority:** P0
**Dependencies:** None
**Status:** [ ] Pending
**User Story:** As a user, I am secure.
"""
        _setup_roadmap(tmpdir_path, content)
        panel.run_add_to_roadmap("Pipeline integration test for critical failures", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        # F002 (tests, score 10) should appear BEFORE F001 (security, score 40)
        f002_pos = content.index("### F002: Pipeline integration test for critical failures")
        f001_pos = content.index("### F001: Security Hardening")
        assert f002_pos < f001_pos, (
            f"Test feature (score 10) should be before security (score 40). "
            f"Got F002 at {f002_pos}, F001 at {f001_pos}"
        )

    def test_resilience_inserted_before_features(self, panel, tmpdir_path):
        """P1 resilience (score 130) inserted before P1 feature (score 150)."""
        content = """# Roadmap

## Phase 2: Features

### F001: User Dashboard
**Priority:** P1
**Dependencies:** None
**Status:** [ ] Pending
**User Story:** As a user, I see my dashboard.
"""
        _setup_roadmap(tmpdir_path, content)
        panel.run_add_to_roadmap("Model provider fallback and recovery", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        f002_pos = content.index("### F002: Model provider fallback and recovery")
        f001_pos = content.index("### F001: User Dashboard")
        assert f002_pos < f001_pos, (
            f"Resilience (score 130) should be before feature (score 150). "
            f"Got F002 at {f002_pos}, F001 at {f001_pos}"
        )

    def test_multiple_adds_maintain_order_within_section(self, panel, tmpdir_path):
        """Within same section+P-level, features maintain execution-priority order."""
        _setup_roadmap(tmpdir_path, ROADMAP_EMPTY)
        # All P0 → all go to Phase 1
        panel.run_add_to_roadmap("Add dark mode toggle for blockers", tmpdir_path)   # score 50 (feature)
        panel.run_add_to_roadmap("Fix crash on login", tmpdir_path)                   # score 20 (critical)
        panel.run_add_to_roadmap("Pipeline test harness for crash detection", tmpdir_path)  # score 10 (tests)
        panel.run_add_to_roadmap("Security audit", tmpdir_path)                      # score 40 (security)
        content = _read_roadmap(tmpdir_path)

        # Extract F-numbers in file order
        fids_in_order = re.findall(r'^### (F\d{3}):', content, re.MULTILINE)
        # F001 was "Add dark mode", F002 was "Fix crash"
        # F003 was "Pipeline test", F004 was "Security audit"
        # All P0: scores = 50, 20, 10, 40
        # Expected: F003 (10) < F002 (20) < F004 (40) < F001 (50)
        f003_idx = fids_in_order.index("F003") if "F003" in fids_in_order else -1
        f002_idx = fids_in_order.index("F002") if "F002" in fids_in_order else -1
        f004_idx = fids_in_order.index("F004") if "F004" in fids_in_order else -1
        f001_idx = fids_in_order.index("F001") if "F001" in fids_in_order else -1
        assert f003_idx < f002_idx < f004_idx < f001_idx, (
            f"Expected: F003 (tests,10) < F002 (critical,20) < F004 (security,40) < F001 (feature,50). "
            f"Got: {fids_in_order}"
        )

    def test_p0_security_comes_before_p0_features(self, panel, tmpdir_path):
        """P0 security (score 40) before P0 feature (score 50) within same section."""
        content = """# Roadmap

## Phase 1: Core

### F001: Dark mode support
**Priority:** P0
**Dependencies:** None
**Status:** [ ] Pending
**User Story:** As a user, I want dark mode.
"""
        _setup_roadmap(tmpdir_path, content)
        # "SQL injection fix" → P0 security, score 40
        panel.run_add_to_roadmap("SQL injection fix for login", tmpdir_path)
        content = _read_roadmap(tmpdir_path)
        f002_pos = content.index("### F002: SQL injection fix for login")
        f001_pos = content.index("### F001: Dark mode support")
        # Security (40) should be before feature (50)
        assert f002_pos < f001_pos, (
            f"Security (score 40) should execute before feature (score 50). "
            f"Got F002 at {f002_pos}, F001 at {f001_pos}"
        )
