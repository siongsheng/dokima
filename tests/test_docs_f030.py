"""Test that docs/setup.md and docs/pipeline.md use new subcommand CLI syntax.

F030: CLI redesign — operation flags (--add, --next, --fix, --status,
--stop, --kill, --list-crons, --version, --upgrade, --release, --map,
--help, --continuous, --help-json) became subcommands. These docs must
reference the new `dokima <command>` form, not the old `dokima --<command>`.

Options (--answers, --force-full, --max-parallel, etc.) keep their -- prefix
and are allowed.
"""

import re
import os

# The operations that became subcommands in F030
_OPS_BECAME_SUBCOMMANDS = [
    'add', 'next', 'fix', 'status', 'stop', 'kill',
    'list-crons', 'version', 'upgrade', 'release',
    'map', 'help', 'continuous', 'help-json',
]

# Options that KEEP their -- prefix (allowed in docs)
_OPTIONS_STAY = {
    'answers', 'force-full', 'max-parallel', 'skip-autofix',
    'skip-human-gate', 'resume', 'no-resume', 'interactive',
    'fix-all', 'dry-run', 'base-branch', 'skip-auto-archive',
    'map-full',
}

# All known -- flags, both old ops and current options
_ALL_KNOWN_FLAGS = set(_OPS_BECAME_SUBCOMMANDS) | _OPTIONS_STAY


def _read_doc(path):
    """Read a doc file relative to the dokima root."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full = os.path.join(root, path)
    if not os.path.isfile(full):
        return None
    with open(full, 'r') as f:
        return f.read()


def _find_old_style_ops(text):
    """Find old-style `dokima --<op>` references in text.

    Returns a list of (line_number, matched_text) for any old-style
    operation references.  Only flags where the flag name is an operation
    that became a subcommand are flagged — option flags (--answers, etc.)
    are not.
    """
    results = []
    # Match `dokima --<word>` where <word> is an operation that became a subcommand
    pattern = r'dokima\s+--(' + '|'.join(_OPS_BECAME_SUBCOMMANDS) + r')\b'
    for i, line in enumerate(text.splitlines(), 1):
        m = re.search(pattern, line)
        if m:
            results.append((i, m.group(0)))
    return results


class TestDocsF030Subcommands:
    """Setup and pipeline docs must use new subcommand syntax."""

    def test_setup_md_no_old_style_ops(self):
        """docs/setup.md should not contain dokima --<op> for operations
        that became subcommands."""
        text = _read_doc('docs/setup.md')
        assert text is not None, 'docs/setup.md not found'
        hits = _find_old_style_ops(text)
        assert hits == [], (
            'docs/setup.md contains old-style operation flags:\n' +
            '\n'.join(f'  line {n}: {t}' for n, t in hits) +
            '\nThese should be subcommands (e.g. dokima help, not dokima --help).'
        )

    def test_pipeline_md_no_old_style_ops(self):
        """docs/pipeline.md should not contain dokima --<op> for operations
        that became subcommands."""
        text = _read_doc('docs/pipeline.md')
        assert text is not None, 'docs/pipeline.md not found'
        hits = _find_old_style_ops(text)
        assert hits == [], (
            'docs/pipeline.md contains old-style operation flags:\n' +
            '\n'.join(f'  line {n}: {t}' for n, t in hits) +
            '\nThese should be subcommands (e.g. dokima help, not dokima --help).'
        )

    def test_options_unchanged_in_setup_md(self):
        """Options like --answers, --force-full should still appear
        in docs/setup.md (they keep their -- prefix)."""
        text = _read_doc('docs/setup.md')
        assert text is not None
        # --answers must still be present (it's an option, not an operation)
        assert '--answers' in text, (
            'docs/setup.md should still reference --answers '
            '(it is an option, not a subcommand operation)'
        )

    def test_options_unchanged_in_pipeline_md(self):
        """Options like --answers, --force-full should still appear
        in docs/pipeline.md (they keep their -- prefix)."""
        text = _read_doc('docs/pipeline.md')
        assert text is not None
        # --answers must still be present (it's an option, not an operation)
        assert '--answers' in text, (
            'docs/pipeline.md should still reference --answers '
            '(it is an option, not a subcommand operation)'
        )
