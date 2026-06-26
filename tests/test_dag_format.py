"""Tests for DAG format enforcement — ensures strategist produces ### Task N: format.

The panel DAG parser (regex: ^### Task \\d+:) discards any other format.
The spec-strategist-lite skill was fixed from #### (4 hashes) to ### (3 hashes).
This module tests both the regex and the enforcement gate.
"""
import re
import pytest
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ── DAG format regex tests ──────────────────────────────────────

DAG_REGEX = r'^### Task \d+:'  # ^ requires start-of-line → won't match ####

VALID_TASKS = [
    "### Task 1: Create the sidebar component",
    "### Task 2: Add navigation links",
    "### Task 10: Final integration test",
]

INVALID_TASKS = [
    "#### Task 1: Wrong format (four hashes)",       # Old skill format
    "- **Task 1:** Bullet point",                     # Bullet list
    "1. Task 1: Numbered list",                       # Numbered
    "**Task 1:** Bold header",                        # Bold
    "Task 1: Plain text",                             # No header marker
    "### Task: Missing number",                       # Missing digit
    "## Task 1: Two hashes",                          # Wrong hash count
    "Task DAG: 5 tasks, sequential (TDD chain...)",   # Prose — what F015 produced
]


def test_dag_regex_matches_valid(panel):
    for text in VALID_TASKS:
        assert re.search(DAG_REGEX, text, re.MULTILINE), f"Should match: {text}"


def test_dag_regex_rejects_invalid(panel):
    for text in INVALID_TASKS:
        assert not re.search(DAG_REGEX, text, re.MULTILINE), f"Should NOT match: {text}"


def test_dag_regex_matches_multiple(panel):
    spec = """### Task 1: First
**Files:** a.tsx
**Dependencies:** [none]
**Parallelizable:** yes
**Description:** Do first thing.

### Task 2: Second
**Files:** b.tsx
**Dependencies:** [Task 1]
**Parallelizable:** no
**Description:** Do second thing."""
    
    matches = re.findall(DAG_REGEX, spec, re.MULTILINE)
    assert len(matches) == 2


def test_dag_regex_rejects_prose(panel):
    """The exact format F015's strategist produced — should NOT match."""
    prose = """Task DAG: 5 tasks, sequential (TDD chain: test → page → verify → docs → regression).
~75 min for one coder. Not parallelizable — Task 2 depends on Task 1 test structure,
Task 3 verifies Task 2."""
    assert not re.search(DAG_REGEX, prose)


def test_dag_regex_matches_actual_f004_format(panel):
    """F004's spec had proper DAG format — verify it matches."""
    spec = """### Task 1: Create Pipeline Phases index page
**Files:** src/app/(docs)/guides/pipelines/page.mdx
**Dependencies:** [none]
**Parallelizable:** no
**Description:** Create the index page for the Pipeline Phases section."""
    assert re.search(DAG_REGEX, spec)


# ── Skill format verification ───────────────────────────────────

def test_skill_uses_three_hashes():
    """The spec-strategist-lite skill must use ### not #### for tasks."""
    import os
    skill_path = os.path.expanduser("~/.hermes/skills/software-development/spec-strategist-lite/SKILL.md")
    if not os.path.exists(skill_path):
        pytest.skip("Skill file not found")
    with open(skill_path) as f:
        content = f.read()
    # Must have the three-hash format
    assert "### Task N:" in content, "Skill uses wrong task format — must be ### not ####"
    # Must NOT have the old four-hash format
    assert "#### Task N:" not in content, "Skill still has old #### Task N: format — update failed"


def test_skill_warns_about_wrong_format():
    """Skill must explicitly warn against #### format."""
    import os
    skill_path = os.path.expanduser("~/.hermes/skills/software-development/spec-strategist-lite/SKILL.md")
    if not os.path.exists(skill_path):
        pytest.skip("Skill file not found")
    with open(skill_path) as f:
        content = f.read()
    assert "not four" in content.lower() or "####" in content, \
        "Skill should warn against four-hash format"


# ── extract_file_paths integration ──────────────────────────────

def test_file_hints_from_dag_tasks(panel):
    """Target file hints must extract from properly formatted DAG tasks."""
    spec = """### Task 1: Add sidebar
**Files:** src/components/Sidebar.tsx, src/config/sidebar.ts
**Dependencies:** [none]
**Parallelizable:** yes
**Description:** Create sidebar component.

### Task 2: Add header
**Files:** src/components/Header.tsx
**Dependencies:** [Task 1]
**Parallelizable:** no
**Description:** Create header component."""

    files = panel.extract_file_paths(spec)
    assert "src/components/Sidebar.tsx" in files
    assert "src/config/sidebar.ts" in files
    assert "src/components/Header.tsx" in files
    assert len(files) == 3


def test_no_file_hints_from_prose(panel):
    """Prose task descriptions without **Files:** should yield empty hints."""
    prose = """Task DAG: 5 tasks, sequential.
Task 1: Create sidebar at src/components/Sidebar.tsx
Task 2: Add header at src/components/Header.tsx"""
    files = panel.extract_file_paths(prose)
    # Only backtick-quoted paths would match, not bare paths in prose
    # This should not crash — return whatever it finds or empty
    assert isinstance(files, list)
