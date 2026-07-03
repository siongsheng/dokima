"""Tests that README.md usage examples reflect F030 subcommand CLI redesign.

Task 10: Update README.md usage examples. The F030 CLI redesign replaces
standalone --flags (--add, --next, --fix, --continuous, --status, --stop,
--kill, --list-crons, --version, --upgrade, --release) with subcommands
(dokima add, dokima next, etc.). README.md usage section must not reference
the old flag-style invocations for these commands.
"""

import os
import re


def _read_readme():
    path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    with open(path) as f:
        return f.read()


# ── Deprecated --flag commands replaced by subcommands in F030 ──
# These are the old standalone pattern: dokima --<flag> [args...]
# Flags that stay as flags (--help, --force-full, --answers, etc.)
# are NOT in this list.

DEPRECATED_FLAG_COMMANDS = [
    'dokima --add ',
    'dokima --next ',
    'dokima --next\n',
    'dokima --fix ',
    'dokima --fix\n',
    'dokima --continuous ',
    'dokima --continuous\n',
    'dokima --status ',
    'dokima --stop ',
    'dokima --kill ',
    'dokima --list-crons',
    'dokima --version',
    'dokima --upgrade',
    'dokima --release ',
]

# ── Section markers within README.md ──

USAGE_SECTION_HEADER = '### Usage'


def test_readme_exists():
    """README.md must exist at project root."""
    path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    assert os.path.exists(path), "README.md must exist at project root"


def test_usage_section_exists():
    """README.md must have a Usage section."""
    md = _read_readme()
    assert USAGE_SECTION_HEADER in md, \
        f"README.md must have '{USAGE_SECTION_HEADER}' section"


def test_no_deprecated_flag_commands_in_readme():
    """README.md must NOT contain old dokima --flag command references."""
    md = _read_readme()
    failures = []
    for pattern in DEPRECATED_FLAG_COMMANDS:
        if pattern in md:
            failures.append(pattern.strip())
    assert not failures, (
        f"README.md contains deprecated --flag commands: {failures}. "
        f"Replace with subcommand form (e.g. 'dokima --fix' → 'dokima fix')."
    )


def test_usage_section_has_subcommand_examples():
    """README.md Usage section should reference at least one new subcommand."""
    md = _read_readme()
    # Extract just the Usage section (from ### Usage to next ### or end)
    usage_start = md.find(USAGE_SECTION_HEADER)
    assert usage_start >= 0, "Usage section not found"
    usage_md = md[usage_start:]
    next_section = re.search(r'\n### ', usage_md[len(USAGE_SECTION_HEADER):])
    if next_section:
        usage_md = usage_md[:len(USAGE_SECTION_HEADER) + next_section.start()]

    # Should contain at least one subcommand reference: dokima add/next/fix
    subcommand_patterns = ['dokima fix', 'dokima next', 'dokima add']
    found = [p for p in subcommand_patterns if p in usage_md]
    assert found, (
        f"Usage section should reference subcommand form. "
        f"Expected at least one of: {subcommand_patterns}"
    )
