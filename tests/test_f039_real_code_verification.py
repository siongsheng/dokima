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


# ── Task 1: verify_source_function_exists tests ──

class TestVerifySourceFunctionExists:
    """Test cases for verify_source_function_exists()."""

    def test_existing_stdlib_symbol_returns_true(self, panel):
        """os.path exists → returns (True, None)."""
        from utils import verify_source_function_exists
        exists, error = verify_source_function_exists("os", "path")
        assert exists is True, f"os.path should exist, got error={error}"

    def test_nonexistent_module_returns_false(self, panel):
        """Non-existent module → returns (False, error string)."""
        from utils import verify_source_function_exists
        exists, error = verify_source_function_exists("nonexistent_module_xyz_12345", "foo")
        assert exists is False, f"Expected False for non-existent module, got {exists}"
        assert error is not None
        assert "ModuleNotFoundError" in error or "No module" in error or "modulenotfound" in error.lower()

    def test_existing_module_missing_attr_returns_false(self, panel):
        """json.loads exists, but json.nonexistent_attr does not → returns (False, error)."""
        from utils import verify_source_function_exists
        exists, error = verify_source_function_exists("json", "nonexistent_attr_xyz_12345")
        assert exists is False, f"Expected False for missing attr, got {exists}"
        assert error is not None
        assert "has no attribute" in error.lower() or "AttributeError" in error

    def test_existing_module_with_valid_attr_returns_true(self, panel):
        """json.loads exists → returns (True, None)."""
        from utils import verify_source_function_exists
        exists, error = verify_source_function_exists("json", "loads")
        assert exists is True, f"json.loads should exist, got error={error}"

    def test_module_with_import_error_returns_false_gracefully(self, panel):
        """Module that raises on import → returns (False, error) without crashing."""
        from utils import verify_source_function_exists
        exists, error = verify_source_function_exists("_this_module_definitely_does_not_exist_", "fake_func")
        assert exists is False, f"Expected False, got {exists}"
        assert error is not None


# ── Task 2: _parse_test_references tests ──

class TestParseTestReferences:
    """Test cases for _parse_test_references()."""

    def test_patch_decorator_with_string_target(self, panel, temp_project):
        """@patch('module.func') → one reference extracted."""
        from utils import _parse_test_references
        test_file = os.path.join(temp_project, "tests", "test_patch_deco.py")
        with open(test_file, "w") as f:
            f.write("from unittest.mock import patch\n")
            f.write("@patch('utils.slugify')\n")
            f.write("def test_foo(mock_slugify):\n")
            f.write("    pass\n")
        refs = _parse_test_references(test_file)
        assert len(refs) == 1, f"Expected 1 ref, got {refs}"
        assert refs[0]["attr_name"] == "slugify"
        assert refs[0]["module_target"] == "utils"

    def test_patch_object_with_create_flag(self, panel, temp_project):
        """patch.object(target, 'attr', create=True) → create_flag=True."""
        from utils import _parse_test_references
        test_file = os.path.join(temp_project, "tests", "test_patch_obj.py")
        with open(test_file, "w") as f:
            f.write("from unittest.mock import patch\n")
            f.write("def test_foo():\n")
            f.write("    with patch.object(utils, 'slugify', create=True):\n")
            f.write("        pass\n")
        refs = _parse_test_references(test_file)
        assert len(refs) >= 1, f"Expected >=1 ref, got {refs}"
        create_refs = [r for r in refs if r["create_flag"]]
        assert len(create_refs) >= 1, f"Expected >=1 create_flag=True ref, got {create_refs}"

    def test_direct_import_pattern(self, panel, temp_project):
        """from module import func → one reference extracted."""
        from utils import _parse_test_references
        test_file = os.path.join(temp_project, "tests", "test_import.py")
        with open(test_file, "w") as f:
            f.write("from utils import slugify\n")
            f.write("def test_foo():\n")
            f.write("    assert slugify('x')\n")
        refs = _parse_test_references(test_file)
        assert len(refs) >= 1, f"Expected >=1 ref, got {refs}"
        import_refs = [r for r in refs if r["attr_name"] == "slugify"]
        assert len(import_refs) >= 1, f"Expected slugify ref, got {refs}"

    def test_file_with_no_references_returns_empty(self, panel, temp_project):
        """Test file with no mocks or imports → returns empty list."""
        from utils import _parse_test_references
        test_file = os.path.join(temp_project, "tests", "test_empty.py")
        with open(test_file, "w") as f:
            f.write("def test_nothing():\n")
            f.write("    pass\n")
        refs = _parse_test_references(test_file)
        assert refs == [], f"Expected [], got {refs}"

    def test_file_with_syntax_error_returns_empty(self, panel, temp_project):
        """Syntax error in test file → returns empty list, no crash."""
        from utils import _parse_test_references
        test_file = os.path.join(temp_project, "tests", "test_broken.py")
        with open(test_file, "w") as f:
            f.write("this is not valid python @@@@\n")
        refs = _parse_test_references(test_file)
        assert isinstance(refs, list)
        assert refs == []


# ── Task 2: vet --verify-code integration tests ──


class TestVetVerifyCode:
    """Integration tests for scripts/vet --verify-code flag (Task 2)."""

    def _make_verify_imports(self, tmpdir, exit_code=0, output=""):
        """Create a mock verify_imports.py that exits with given code and output."""
        scripts_dir = os.path.join(tmpdir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        script = os.path.join(scripts_dir, "verify_imports.py")
        content = (
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "print(" + repr(output) + ")\n"
            "sys.exit(" + str(exit_code) + ")\n"
        )
        with open(script, "w") as f:
            f.write(content)
        os.chmod(script, 0o755)
        return script

    def test_vet_verify_code_all_clear_exits_zero(self):
        """vet --verify-code with all real functions → exit 0."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            # AGENTS.md with passing test/build
            with open(os.path.join(tmp, "AGENTS.md"), "w") as f:
                f.write("- Test: `true`\n")
                f.write("- Build: `true`\n")
            # mock verify_imports.py that reports all clear
            self._make_verify_imports(tmp, exit_code=0, output="All imports verified.")
            result = subprocess.run(
                ["bash", os.path.join(os.path.dirname(__file__), "..", "scripts", "vet"),
                 "--verify-code", tmp],
                capture_output=True, text=True, timeout=30
            )
            assert result.returncode == 0, (
                f"Expected exit 0, got {result.returncode}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

    def test_vet_verify_code_missing_exits_two(self):
        """vet --verify-code with missing function → exit 2."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "AGENTS.md"), "w") as f:
                f.write("- Test: `true`\n")
                f.write("- Build: `true`\n")
            self._make_verify_imports(tmp, exit_code=2,
                                      output="utils.missing_func: test_bad.py:3")
            result = subprocess.run(
                ["bash", os.path.join(os.path.dirname(__file__), "..", "scripts", "vet"),
                 "--verify-code", tmp],
                capture_output=True, text=True, timeout=30
            )
            assert result.returncode == 2, (
                f"Expected exit 2 for missing func, got {result.returncode}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

    def test_vet_no_flag_unchanged_behavior(self):
        """vet without --verify-code → existing behavior (exit 0 on pass)."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "AGENTS.md"), "w") as f:
                f.write("- Test: `true`\n")
                f.write("- Build: `true`\n")
            result = subprocess.run(
                ["bash", os.path.join(os.path.dirname(__file__), "..", "scripts", "vet"),
                 tmp],
                capture_output=True, text=True, timeout=30
            )
            assert result.returncode == 0, (
                f"Expected exit 0, got {result.returncode}"
            )

    def test_vet_verify_code_env_var(self):
        """REAL_CODE_VERIFY=1 vet → equivalent to --verify-code."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "AGENTS.md"), "w") as f:
                f.write("- Test: `true`\n")
                f.write("- Build: `true`\n")
            self._make_verify_imports(tmp, exit_code=0, output="All clear.")
            env = os.environ.copy()
            env["REAL_CODE_VERIFY"] = "1"
            result = subprocess.run(
                ["bash", os.path.join(os.path.dirname(__file__), "..", "scripts", "vet"),
                 tmp],
                capture_output=True, text=True, timeout=30, env=env
            )
            assert result.returncode == 0, (
                f"Expected exit 0, got {result.returncode}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )


# ── Task 3: verify_imports.py standalone script tests ──


class TestVerifyImportsScript:
    """Tests for scripts/verify_imports.py standalone verification (Task 3)."""

    def _run_verify_imports(self, project_dir):
        """Run verify_imports.py as subprocess and return CompletedProcess."""
        import subprocess
        script = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "verify_imports.py"
        )
        return subprocess.run(
            ["python3", script, project_dir],
            capture_output=True, text=True, timeout=30
        )

    def test_all_real_imports_exits_zero(self):
        """All functions exist → exit 0, prints success message."""
        with tempfile.TemporaryDirectory() as tmp:
            # Create source modules
            with open(os.path.join(tmp, "utils.py"), "w") as f:
                f.write("def slugify(s): pass\n")
            # Create tests/
            os.makedirs(os.path.join(tmp, "tests"), exist_ok=True)
            with open(os.path.join(tmp, "tests", "test_real.py"), "w") as f:
                f.write("from utils import slugify\n")
                f.write("def test_slugify():\n")
                f.write("    assert slugify('x') is not None\n")

            result = self._run_verify_imports(tmp)
            assert result.returncode == 0, (
                f"Expected exit 0, got {result.returncode}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

    def test_missing_function_exits_two(self):
        """Missing function → exit 2, diagnostic in output."""
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "utils.py"), "w") as f:
                f.write("def slugify(s): pass\n")
            os.makedirs(os.path.join(tmp, "tests"), exist_ok=True)
            with open(os.path.join(tmp, "tests", "test_missing.py"), "w") as f:
                f.write("from utils import nonexistent_func\n")
                f.write("def test_foo():\n")
                f.write("    pass\n")

            result = self._run_verify_imports(tmp)
            assert result.returncode == 2, (
                f"Expected exit 2, got {result.returncode}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
            assert "nonexistent_func" in result.stdout, (
                f"Diagnostic should mention nonexistent_func:\n{result.stdout}"
            )

    def test_no_tests_dir_exits_zero(self):
        """No tests/ directory → exit 0 (nothing to verify)."""
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "utils.py"), "w") as f:
                f.write("def foo(): pass\n")
            # No tests/ dir

            result = self._run_verify_imports(tmp)
            assert result.returncode == 0, (
                f"Expected exit 0 for no tests dir, got {result.returncode}\n"
                f"stdout: {result.stdout}"
            )

    def test_no_args_exits_three(self):
        """No project dir argument → exit 3 (usage error)."""
        import subprocess
        script = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "verify_imports.py"
        )
        result = subprocess.run(
            ["python3", script],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 3, (
            f"Expected exit 3 for no args, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_mock_patch_missing_flagged(self):
        """@patch('module.missing_func') → exit 2, flagged."""
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "utils.py"), "w") as f:
                f.write("def slugify(s): pass\n")
            os.makedirs(os.path.join(tmp, "tests"), exist_ok=True)
            with open(os.path.join(tmp, "tests", "test_patch.py"), "w") as f:
                f.write("from unittest.mock import patch\n")
                f.write("@patch('utils.nonexistent_func')\n")
                f.write("def test_foo(mock_func):\n")
                f.write("    pass\n")

            result = self._run_verify_imports(tmp)
            assert result.returncode == 2, (
                f"Expected exit 2, got {result.returncode}\nstdout: {result.stdout}"
            )
            assert "nonexistent_func" in result.stdout
