"""Tests verifying that conftest.py no longer uses the setattr hack.

Task 11 (F040): The _sync_globals_on_setattr override, _IMPORTING_PANEL
linkage, and initial sync loop are all removed. _load_panel() is simplified
to no longer install a custom __setattr__ or sync globals to sub-modules.
"""

import ast
import os
import pytest


CONFTEST_PATH = os.path.join(os.path.dirname(__file__), "conftest.py")


def _parse_conftest():
    """Parse conftest.py into an AST and return the module node."""
    with open(CONFTEST_PATH) as f:
        source = f.read()
    return ast.parse(source), source


def _find_load_panel_func(tree):
    """Return the AST FunctionDef node for _load_panel(), or None."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_load_panel":
            return node
    return None


class TestConftestNoSetattrHack:
    """Verify the three setattr-related hacks are gone from conftest.py."""

    def test_no_sync_globals_on_setattr_function(self):
        """_sync_globals_on_setattr is NOT defined anywhere in conftest.py."""
        tree, source = _parse_conftest()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                assert node.name != "_sync_globals_on_setattr", (
                    "_sync_globals_on_setattr must be removed from conftest.py"
                )

    def test_no_setattr_in_code(self):
        """The setattr override pattern (__setattr__ / object.__setattr__)
        does not appear in conftest.py code (docstrings excluded)."""
        with open(CONFTEST_PATH) as f:
            source = f.read()
        # Remove docstrings (triple-quoted strings)
        import re
        no_docs = re.sub(r'""".*?"""', '', source, flags=re.DOTALL)
        no_docs = re.sub(r"'''.*?'''", '', no_docs, flags=re.DOTALL)
        # Remove inline comments
        lines = []
        for line in no_docs.split('\n'):
            code = line.split('#')[0]
            lines.append(code)
        code_only = '\n'.join(lines)
        assert "__setattr__" not in code_only, (
            "__setattr__ override must be removed from conftest.py"
        )
        assert "object.__setattr__" not in code_only, (
            "object.__setattr__ calls must be removed from conftest.py"
        )

    def test_no_importing_panel_assignment_in_load_panel(self):
        """_load_panel() does NOT assign _IMPORTING_PANEL to sub-modules."""
        tree, source = _parse_conftest()
        func = _find_load_panel_func(tree)
        assert func is not None, "_load_panel() function must exist"

        # Walk all nodes inside _load_panel looking for _IMPORTING_PANEL
        found_importing = False
        for node in ast.walk(func):
            if isinstance(node, ast.Attribute) and node.attr == "_IMPORTING_PANEL":
                found_importing = True
                break
        assert not found_importing, (
            "_load_panel() must NOT set _IMPORTING_PANEL on sub-modules"
        )

    def test_no_importing_panel_in_source(self):
        """The string '_IMPORTING_PANEL' does not appear in conftest.py."""
        tree, source = _parse_conftest()
        assert "_IMPORTING_PANEL" not in source, (
            "No '_IMPORTING_PANEL' references should remain in conftest.py"
        )

    def test_no_initial_sync_loop(self):
        """_load_panel() does NOT contain the initial sync loop that iterates
        over globals and syncs them to sub-modules."""
        tree, source = _parse_conftest()
        func = _find_load_panel_func(tree)
        assert func is not None

        # The sync loop had a for-loop iterating over g_name in (...)
        # and inside it, iterating over mod_ref in (...).
        # Verify there's no nested for loop with those patterns.
        found_sync = False
        for node in ast.walk(func):
            if isinstance(node, ast.For):
                # Check if the for target is 'g_name'
                if isinstance(node.target, ast.Name) and node.target.id == "g_name":
                    found_sync = True
                    break
                # Also check if iterating over mod_ref
                if isinstance(node.target, ast.Name) and node.target.id == "mod_ref":
                    found_sync = True
                    break
        assert not found_sync, (
            "Initial sync loop (for g_name in ... / for mod_ref in ...) must be removed"
        )

    def test_no_module_class_modification(self):
        """_load_panel() does NOT modify module.__class__ to install setattr."""
        tree, source = _parse_conftest()
        func = _find_load_panel_func(tree)
        assert func is not None

        found_class_mod = False
        for node in ast.walk(func):
            if isinstance(node, ast.Attribute) and node.attr == "__class__":
                found_class_mod = True
                break
        assert not found_class_mod, (
            "module.__class__ override must be removed from _load_panel()"
        )
