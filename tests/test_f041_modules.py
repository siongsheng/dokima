"""Tests for codebase_map.py and control_panel.py module extraction (F041)."""

import pytest

from conftest import _load_panel as _load


class TestCodebaseMapModule:
    """Verify codebase_map.py module structure."""

    def test_module_importable(self):
        import codebase_map

        assert codebase_map is not None

    def test_has_generate_codebase_map(self):
        import codebase_map

        assert hasattr(codebase_map, "generate_codebase_map")
        assert callable(codebase_map.generate_codebase_map)

    def test_has_build_domain_map(self):
        import codebase_map

        assert hasattr(codebase_map, "_build_domain_map")
        assert callable(codebase_map._build_domain_map)

    def test_has_build_impact_map(self):
        import codebase_map

        assert hasattr(codebase_map, "_build_impact_map")
        assert callable(codebase_map._build_impact_map)


class TestControlPanelModule:
    """Verify control_panel.py module structure."""

    def test_module_importable(self):
        import control_panel

        assert control_panel is not None

    def test_has_handle_status(self):
        import control_panel

        assert hasattr(control_panel, "handle_status")
        assert callable(control_panel.handle_status)

    def test_has_handle_stop(self):
        import control_panel

        assert hasattr(control_panel, "handle_stop")
        assert callable(control_panel.handle_stop)

    def test_has_handle_kill(self):
        import control_panel

        assert hasattr(control_panel, "handle_kill")
        assert callable(control_panel.handle_kill)

    def test_has_handle_list_crons(self):
        import control_panel

        assert hasattr(control_panel, "handle_list_crons")
        assert callable(control_panel.handle_list_crons)


class TestUtilsReExport:
    """Verify utils.py re-exports the moved functions."""

    def test_utils_has_generate_codebase_map(self):
        import utils

        assert hasattr(utils, "generate_codebase_map")
        assert callable(utils.generate_codebase_map)

    def test_utils_has_handle_status(self):
        import utils

        assert hasattr(utils, "handle_status")
        assert callable(utils.handle_status)

    def test_utils_has_handle_stop(self):
        import utils

        assert hasattr(utils, "handle_stop")
        assert callable(utils.handle_stop)

    def test_utils_has_handle_kill(self):
        import utils

        assert hasattr(utils, "handle_kill")
        assert callable(utils.handle_kill)

    def test_utils_has_handle_list_crons(self):
        import utils

        assert hasattr(utils, "handle_list_crons")
        assert callable(utils.handle_list_crons)
