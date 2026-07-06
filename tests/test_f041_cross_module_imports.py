"""Tests for F041 Task 5: Inter-module cross-imports.

Verify that new domain modules correctly import from each other
where the call graph requires it.
"""
import pytest
import importlib
import sys


class TestCrossModuleImports:
    """Verify inter-module imports specified in Task 5."""

    def test_spec_extract_imports_git_from_git_ops(self):
        """_append_convention_rules() in spec_extract calls git().
        
        Spec: spec_extract.py must have 'from git_ops import git'.
        """
        # Import spec_extract — if git is not imported, accessing 
        # git via spec_extract should fail
        import spec_extract
        # Verify the git function is accessible and is the one from git_ops
        from git_ops import git as git_ops_git
        assert spec_extract.git is git_ops_git, \
            "spec_extract.git should be the same function object as git_ops.git"

    def test_control_panel_imports_do_release_from_git_ops(self):
        """check_upgrade() in control_panel calls do_release().
        
        Spec: control_panel.py must have 'from git_ops import do_release'.
        """
        import control_panel
        from git_ops import do_release as git_ops_do_release
        assert control_panel.do_release is git_ops_do_release, \
            "control_panel.do_release should be the same function object as git_ops.do_release"

    def test_git_ops_imports_cleanly(self):
        """git_ops.py should import without errors (no circular deps)."""
        import git_ops
        assert hasattr(git_ops, 'git')
        assert hasattr(git_ops, 'gh')
        assert hasattr(git_ops, 'do_release')

    def test_spec_extract_imports_cleanly(self):
        """spec_extract.py should import without errors."""
        import spec_extract
        assert hasattr(spec_extract, 'extract_pr_sections')
        assert hasattr(spec_extract, 'clean_spec_content')

    def test_codebase_map_imports_cleanly(self):
        """codebase_map.py should import without errors."""
        import codebase_map
        assert hasattr(codebase_map, 'generate_codebase_map')

    def test_control_panel_imports_cleanly(self):
        """control_panel.py should import without errors."""
        import control_panel
        assert hasattr(control_panel, 'show_help')
        assert hasattr(control_panel, 'handle_status')

    def test_no_circular_imports(self):
        """Verify importing each module in any order doesn't cause ImportError."""
        modules = ['git_ops', 'spec_extract', 'codebase_map', 'control_panel']
        for mod_name in modules:
            # Force reimport to catch circular import issues
            if mod_name in sys.modules:
                del sys.modules[mod_name]
            try:
                importlib.import_module(mod_name)
            except ImportError as e:
                pytest.fail(f"Circular import or missing dependency in {mod_name}: {e}")

    def test_spec_extract_git_is_callable(self):
        """git imported into spec_extract should be the real function."""
        import spec_extract
        assert callable(spec_extract.git), \
            "spec_extract.git should be a callable function"

    def test_control_panel_do_release_is_callable(self):
        """do_release imported into control_panel should be the real function."""
        import control_panel
        assert callable(control_panel.do_release), \
            "control_panel.do_release should be a callable function"

    def test_git_ops_has_no_spec_extract_dependency(self):
        """git_ops should NOT import from spec_extract (no reverse dep)."""
        import git_ops
        assert not hasattr(git_ops, 'extract_pr_sections'), \
            "git_ops should not import from spec_extract"

    def test_codebase_map_has_no_git_ops_dependency(self):
        """codebase_map should NOT import from git_ops."""
        import codebase_map
        assert not hasattr(codebase_map, 'git'), \
            "codebase_map should not import git from git_ops"
