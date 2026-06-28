"""Tests for HELP_TEXT completeness."""


def test_help_text_documents_panel_max_parallel(panel):
    """PANEL_MAX_PARALLEL env var should be documented in HELP_TEXT
    alongside --max-parallel=N."""
    assert "PANEL_MAX_PARALLEL" in panel.HELP_TEXT, (
        "PANEL_MAX_PARALLEL should be documented in HELP_TEXT "
        "since --max-parallel=N already is"
    )
