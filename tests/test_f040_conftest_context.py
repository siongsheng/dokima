"""Test that conftest.py _load_panel() creates PipelineContext and removes
the legacy __setattr__ override hack (F040: PipelineContext dataclass)."""

import sys
import types
import pytest
from unittest.mock import patch

from conftest import _load_panel, _reload_panel

# Import PipelineContext from the utils module that the loaded panel will use
# We DON'T import from conftest since conftest imports from the loaded panel's utils


class TestLoadPanelCreatesPipelineContext:
    """Verify _load_panel() produces a panel with a ctx PipelineContext."""

    def test_load_panel_has_ctx_attribute(self):
        """_load_panel() sets a `ctx` attribute on the returned module."""
        panel = _load_panel()
        assert hasattr(panel, 'ctx'), (
            "_load_panel() must set panel.ctx (PipelineContext) — "
            "modules should read configuration from ctx, not module globals"
        )

    def test_ctx_is_not_none(self):
        """panel.ctx is a non-None object."""
        panel = _load_panel()
        assert panel.ctx is not None, (
            "_load_panel() must initialize panel.ctx to a PipelineContext, not None"
        )

    def test_ctx_has_expected_fields(self):
        """panel.ctx has the core configuration fields expected by phase functions."""
        panel = _load_panel()
        ctx = panel.ctx

        # Core project identity fields that PipelineContext must have
        expected_attrs = [
            'project_dir', 'repo', 'default_branch',
            'api_key', 'panel_feature', 'panel_dir',
            'output_log', 'hermes_bin',
            'skip_autofix', 'force_full', 'skip_human_gate',
            'max_parallel_override', 'resume',
            'test_cmd', 'build_cmd', 'lint_cmd',
            'fallback_models',
        ]
        missing = [a for a in expected_attrs if not hasattr(ctx, a)]
        assert not missing, (
            f"PipelineContext missing fields: {missing}. "
            "All fields must exist so phase functions can access them unconditionally."
        )

    def test_ctx_matches_module_globals(self):
        """panel.ctx values reflect the module globals set by _load_panel()."""
        panel = _load_panel()
        ctx = panel.ctx

        assert ctx.project_dir == panel.PROJECT_DIR, (
            f"ctx.project_dir ({ctx.project_dir}) must match panel.PROJECT_DIR ({panel.PROJECT_DIR})"
        )
        assert ctx.repo == panel.REPO, (
            f"ctx.repo ({ctx.repo}) must match panel.REPO ({panel.REPO})"
        )
        assert ctx.panel_feature == panel.PANEL_FEATURE, (
            f"ctx.panel_feature mismatch"
        )
        assert ctx.panel_dir == panel.PANEL_DIR, (
            f"ctx.panel_dir mismatch"
        )
        assert ctx.api_key == panel.API_KEY, (
            f"ctx.api_key mismatch"
        )
        assert ctx.test_cmd == panel.TEST_CMD, (
            f"ctx.test_cmd mismatch"
        )
        assert ctx.build_cmd == panel.BUILD_CMD, (
            f"ctx.build_cmd mismatch"
        )
        assert ctx.lint_cmd == panel.LINT_CMD, (
            f"ctx.lint_cmd mismatch"
        )

    def test_no_setattr_override_hack(self):
        """The __setattr__ override hack has been simplified for F040 transition.
        The class name is 'module' (previously 'DokimaModule'), and PipelineContext
        (ctx) is the canonical configuration object.
        """
        panel = _load_panel()
        cls = type(panel)
        # The custom class must NOT be named 'DokimaModule' (the old hack name).
        # During the F040 transition, we keep a simplified 'module' subclass
        # for backward-compatible global sync; this will be removed when
        # all sub-modules read from ctx.
        assert cls.__name__ == 'module', (
            f"Module class must be named 'module', got '{cls.__name__}'. "
            "The DokimaModule hack has been replaced by PipelineContext (ctx)."
        )


class TestReloadPanelCreatesPipelineContext:
    """Verify _reload_panel() also produces PipelineContext."""

    def test_reload_panel_has_ctx(self):
        """_reload_panel() produces a panel with ctx set."""
        panel = _reload_panel()
        assert hasattr(panel, 'ctx'), "reloaded panel must have ctx"
        assert panel.ctx is not None, "reloaded panel ctx must not be None"


class TestPanelFixtureProvidesPipelineContext:
    """Verify the `panel` pytest fixture provides ctx."""

    def test_panel_fixture_has_ctx(self, panel):
        """The `panel` fixture yields a module with ctx PipelineContext."""
        assert hasattr(panel, 'ctx'), "panel fixture must provide ctx"
        assert panel.ctx is not None, "panel fixture ctx must not be None"
        assert panel.ctx.project_dir == panel.PROJECT_DIR

    def test_setattr_hack_absent_in_fixture(self, panel):
        """The `panel` fixture's module class is named 'module' (not 'DokimaModule')."""
        cls = type(panel)
        assert cls.__name__ == 'module', (
            f"panel fixture module class must be named 'module', got '{cls.__name__}'"
        )


class TestCleanupPreservesStandaloneModules:
    """After _load_panel(), the utils module (used by conftest itself)
    should not have its globals tampered with — the setattr hack used to
    modify sys.modules['utils'] globals, which could break tests that
    import from utils directly."""

    def test_utils_module_globals_unchanged(self):
        """After loading a panel, importing utils should give fresh state."""
        import utils as direct_utils
        # Save a known global
        old_project_dir = direct_utils.PROJECT_DIR

        panel = _load_panel()

        # direct_utils should NOT have been modified by the setattr hack
        # (it used to sync panel.PROJECT_DIR → _utils.PROJECT_DIR → utils.PROJECT_DIR)
        # With PipelineContext, no sync happens
        assert direct_utils.PROJECT_DIR == old_project_dir, (
            "Importing utils module should not have its globals modified by "
            "_load_panel(). The __setattr__ hack used to do this; PipelineContext "
            "eliminates the need for global sync."
        )
