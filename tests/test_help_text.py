"""Tests for HELP_TEXT completeness."""


def test_help_text_is_non_empty(panel):
    """HELP_TEXT must be a non-empty string."""
    assert isinstance(panel.HELP_TEXT, str), "HELP_TEXT must be a string"
    assert len(panel.HELP_TEXT) > 0, "HELP_TEXT must not be empty"


def test_help_text_has_expected_sections(panel):
    """HELP_TEXT must contain the four expected sections."""
    assert "COMMANDS:" in panel.HELP_TEXT, (
        "HELP_TEXT must have a COMMANDS section"
    )
    assert "CONTROL:" in panel.HELP_TEXT, (
        "HELP_TEXT must have a CONTROL section"
    )
    assert "FLAGS:" in panel.HELP_TEXT, (
        "HELP_TEXT must have a FLAGS section"
    )
    assert "EXAMPLES:" in panel.HELP_TEXT, (
        "HELP_TEXT must have an EXAMPLES section"
    )


def test_help_text_documents_core_commands(panel):
    """Each core command must appear in HELP_TEXT."""
    ht = panel.HELP_TEXT
    core_commands = [
        ('dokima "Feature description"', "default pipeline"),
        ("dokima init", "project init"),
        ("dokima --add", "add to roadmap"),
        ("dokima --next", "build next feature"),
        ("dokima --continuous", "continuous sprint"),
        ("dokima --fix", "fix mode"),
    ]
    for cmd, desc in core_commands:
        assert cmd in ht, f"{desc} command '{cmd}' must appear in HELP_TEXT"


def test_help_text_documents_control_commands(panel):
    """Each control command must appear in HELP_TEXT."""
    ht = panel.HELP_TEXT
    control_commands = [
        ("dokima --status", "pipeline status"),
        ("dokima --stop", "graceful stop"),
        ("dokima --kill", "emergency kill"),
        ("dokima --list-crons", "list scheduled pipelines"),
        ("dokima --version", "print version"),
        ("dokima --upgrade", "check upgrade"),
        ("dokima --release", "bump version and release"),
    ]
    for cmd, desc in control_commands:
        assert cmd in ht, f"{desc} command '{cmd}' must appear in HELP_TEXT"


def test_help_text_documents_panel_max_parallel(panel):
    """PANEL_MAX_PARALLEL env var should be documented in HELP_TEXT
    alongside --max-parallel=N."""
    assert "PANEL_MAX_PARALLEL" in panel.HELP_TEXT, (
        "PANEL_MAX_PARALLEL should be documented in HELP_TEXT "
        "since --max-parallel=N already is"
    )


def test_help_text_documents_map_flag(panel):
    """--map flag (codebase map generation) must appear in HELP_TEXT."""
    assert "--map" in panel.HELP_TEXT, (
        "--map flag must be documented in HELP_TEXT "
        "(codebase map generation, handled in main)"
    )


def test_help_text_documents_map_full_flag(panel):
    """--map-full flag (full codebase map) must appear in HELP_TEXT."""
    assert "--map-full" in panel.HELP_TEXT, (
        "--map-full flag must be documented in HELP_TEXT "
        "(full codebase map generation, handled in main)"
    )


def test_help_text_documents_key_flags(panel):
    """Key flags with env var equivalents must appear in HELP_TEXT."""
    ht = panel.HELP_TEXT
    key_flags = [
        "--interactive",
        "--answers",
        "--fix-all",
        "--skip-autofix",
        "--force-full",
        "--skip-auto-archive",
        "--skip-human-gate",
        "--resume",
        "--no-resume",
        "--max-parallel",
        "--base-branch",
    ]
    for flag in key_flags:
        assert flag in ht, f"flag '{flag}' must appear in HELP_TEXT"


def test_help_text_mentions_env_var_fallback(panel):
    """HELP_TEXT must mention that flags accept PANEL_* env var equivalents."""
    ht = panel.HELP_TEXT
    assert "PANEL_" in ht, (
        "HELP_TEXT must mention PANEL_* env var equivalents for flags"
    )
    # Must mention that flags take priority over env vars
    assert "priority" in ht.lower() or "take" in ht.lower(), (
        "HELP_TEXT must indicate flag/env-var precedence"
    )


def test_help_text_documents_examples(panel):
    """HELP_TEXT must include usage examples for common operations."""
    ht = panel.HELP_TEXT
    example_commands = [
        "dokima init",
        "dokima --add",
        "dokima --next",
        "dokima --continuous",
        "dokima --fix",
        "dokima --status",
    ]
    for cmd in example_commands:
        # Check that the example section contains this command
        # Find the EXAMPLES section
        examples_start = ht.find("EXAMPLES:")
        if examples_start == -1:
            continue
        examples_section = ht[examples_start:]
        assert cmd in examples_section, (
            f"EXAMPLES section must include '{cmd}' usage example"
        )
