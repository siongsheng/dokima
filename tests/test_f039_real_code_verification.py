"""Tests for F039: Real-code verification in vet phase.

_verify_test_imports_exist scans test files for import claims
and verifies referenced functions exist in source modules.
"""
import os
import sys
import tempfile
import pytest


# ── Helper: create temp project with tests/ dir ──

@pytest.fixture
def temp_project():
    """Create a temporary project directory with source and test files."""
    with tempfile.TemporaryDirectory() as tmp:
        # Create source modules
        open(os.path.join(tmp, "utils.py"), "w").write("def slugify(s): pass\n")
        open(os.path.join(tmp, "pipeline.py"), "w").write("def run_pipeline(): pass\ndef _internal(): pass\n")
        open(os.path.join(tmp, "agent.py"), "w").write("def call_agent(): pass\n")

        # Create tests/ dir
        os.makedirs(os.path.join(tmp, "tests"), exist_ok=True)

        yield tmp


# ── Task 4: F039 vet guard tests ──

class TestVerifyTestImportsExist:
    """Test cases for _verify_test_imports_exist()."""

    def test_happy_path_all_real_imports(self, panel, temp_project):
        """Test file imports real function -> empty list returned."""
        # Write a test file that imports a real function
        test_file = os.path.join(temp_project, "tests", "test_real.py")
        with open(test_file, "w") as f:
            f.write("from utils import slugify\n")
            f.write("\n")
            f.write("def test_slugify():\n")
            f.write("    assert slugify('hello') == 'hello'\n")

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        assert result == [], f"Expected empty list, got: {result}"

    def test_missing_function_flagged(self, panel, temp_project):
        """Test file imports nonexistent function -> flagged."""
        test_file = os.path.join(temp_project, "tests", "test_bad.py")
        with open(test_file, "w") as f:
            f.write("from utils import nonexistent_func\n")
            f.write("\n")
            f.write("def test_thing():\n")
            f.write("    pass\n")

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        assert len(result) == 1, f"Expected 1 missing, got: {result}"
        assert "utils.nonexistent_func" in result[0]
        assert "test_bad.py" in result[0]

    def test_private_names_skipped(self, panel, temp_project):
        """from X import _private_func -> not flagged (starts with _)."""
        test_file = os.path.join(temp_project, "tests", "test_private.py")
        with open(test_file, "w") as f:
            f.write("from utils import _secret\n")
            f.write("\n")
            f.write("def test_uses_secret():\n")
            f.write("    pass\n")

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        assert result == [], f"Private imports should be skipped, got: {result}"

    def test_no_tests_dir_returns_empty(self, panel, temp_project):
        """No tests/ directory -> returns empty list."""
        # Remove tests dir
        import shutil
        shutil.rmtree(os.path.join(temp_project, "tests"))

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        assert result == []

    def test_module_load_failure_skipped_gracefully(self, panel, temp_project):
        """Source module that raises on import -> skipped gracefully."""
        # Create a source module that raises on import
        bad_module = os.path.join(temp_project, "bad_mod.py")
        with open(bad_module, "w") as f:
            f.write("raise RuntimeError('cannot import')\n")

        test_file = os.path.join(temp_project, "tests", "test_bad_mod.py")
        with open(test_file, "w") as f:
            f.write("from bad_mod import something\n")

        # Should not crash — just skip the bad module
        result = panel._pipeline._verify_test_imports_exist(temp_project)
        # 'something' is not in bad_mod (module failed to load), so it's skipped
        # The function should not crash
        assert isinstance(result, list)

    def test_syntax_error_in_test_file_skipped(self, panel, temp_project):
        """Invalid syntax in test file -> skipped gracefully."""
        test_file = os.path.join(temp_project, "tests", "test_broken.py")
        with open(test_file, "w") as f:
            f.write("this is not valid python @@@@\n")

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        assert isinstance(result, list)  # should not crash

    def test_auto_discovers_source_modules(self, panel, temp_project):
        """Module not in hardcoded list is still discovered and checked."""
        # Create a source module NOT in the hardcoded list
        with open(os.path.join(temp_project, "custom_mod.py"), "w") as f:
            f.write("def custom_func(): pass\n")

        test_file = os.path.join(temp_project, "tests", "test_custom.py")
        with open(test_file, "w") as f:
            f.write("from custom_mod import nonexistent_in_custom\n")

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        # custom_mod must be discovered and checked — nonexistent_in_custom flagged
        assert len(result) == 1, f"Expected 1 missing from custom_mod, got: {result}"
        assert "custom_mod.nonexistent_in_custom" in result[0]

    # ── Task 6: Mock pattern detection ──

    def test_patch_decorator_missing_function_flagged(self, panel, temp_project):
        """@patch('module.nonexistent_func') decorator -> flagged."""
        test_file = os.path.join(temp_project, "tests", "test_patch_decorator.py")
        with open(test_file, "w") as f:
            f.write("from unittest.mock import patch\n")
            f.write("\n")
            f.write("@patch('utils.nonexistent_func')\n")
            f.write("def test_something(mock_func):\n")
            f.write("    pass\n")

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        assert len(result) >= 1, f"Expected missing func flagged, got: {result}"
        assert any("utils.nonexistent_func" in r for r in result), \
            f"nonexistent_func should be flagged in: {result}"

    def test_mock_patch_call_missing_function_flagged(self, panel, temp_project):
        """mock.patch('pipeline.missing_func') call -> flagged."""
        test_file = os.path.join(temp_project, "tests", "test_patch_call.py")
        with open(test_file, "w") as f:
            f.write("from unittest import mock\n")
            f.write("\n")
            f.write("def test_something():\n")
            f.write("    with mock.patch('pipeline.missing_func'):\n")
            f.write("        pass\n")

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        assert len(result) >= 1, f"Expected missing func flagged, got: {result}"
        assert any("pipeline.missing_func" in r for r in result), \
            f"missing_func should be flagged in: {result}"

    # ── Task 7: Extended mock pattern coverage ──

    def test_mixed_real_and_mock_only_missing_flagged(self, panel, temp_project):
        """Real import + mock to missing func -> only missing flagged."""
        test_file = os.path.join(temp_project, "tests", "test_mixed.py")
        with open(test_file, "w") as f:
            f.write("from unittest.mock import patch\n")
            f.write("from utils import slugify\n")
            f.write("\n")
            f.write("@patch('utils.nonexistent_func')\n")
            f.write("def test_mixed(mock_func):\n")
            f.write("    assert slugify('hello') is not None\n")

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        assert len(result) == 1, f"Expected only 1 missing, got: {result}"
        assert "utils.nonexistent_func" in result[0]
        # slugify is a real function, should NOT be flagged
        assert not any("slugify" in r for r in result), \
            f"slugify should NOT be flagged: {result}"

    def test_multiple_test_files_only_missing_flagged(self, panel, temp_project):
        """Two test files: real imports in one, missing in another — only missing flagged."""
        # File 1: all real imports
        test_file1 = os.path.join(temp_project, "tests", "test_clean.py")
        with open(test_file1, "w") as f:
            f.write("from utils import slugify\n")
            f.write("\n")
            f.write("def test_one():\n")
            f.write("    assert slugify('x') is not None\n")

        # File 2: imports a nonexistent function
        test_file2 = os.path.join(temp_project, "tests", "test_has_missing.py")
        with open(test_file2, "w") as f:
            f.write("from pipeline import nonexistent_pipeline_func\n")
            f.write("\n")
            f.write("def test_two():\n")
            f.write("    pass\n")

        result = panel._pipeline._verify_test_imports_exist(temp_project)
        # Only the missing function from file 2 should be flagged
        assert len(result) == 1, f"Expected 1 missing, got: {result}"
        assert "pipeline.nonexistent_pipeline_func" in result[0]
        assert "test_has_missing.py" in result[0]
