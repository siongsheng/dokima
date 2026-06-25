"""Shared fixtures for dokima tests."""
import os
import sys
import json
import types
import tempfile
import pytest

PANEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dokima"))


def _load_panel():
    """Load dokima as a Python module via exec, setting required globals.
    Registers in sys.modules so patch('dokima.X') works across all tests."""
    module_name = "dokima"
    # Remove stale module if present
    if module_name in sys.modules:
        del sys.modules[module_name]

    module = types.ModuleType(module_name)
    module.__file__ = PANEL_PATH
    sys.modules[module_name] = module

    # Set required globals BEFORE execution so functions reference them
    module.PROJECT_DIR = "/tmp/test-project"
    module.REPO = "test-owner/test-repo"
    module.API_KEY = "test-key"
    module.PANEL_FEATURE = "Test Feature"
    module.PANEL_DIR = "/tmp/.dokima-test"
    module.DEFAULT_BRANCH = "main"
    module.TEST_CMD = "echo test"
    module.BUILD_CMD = "echo build"
    module.LINT_CMD = "echo lint"

    # Execute the script in the module's namespace
    with open(PANEL_PATH) as f:
        code = compile(f.read(), PANEL_PATH, "exec")
    exec(code, module.__dict__)

    return module


def _reload_panel():
    """Reload a fresh panel module, clearing any global state pollution.
    Use between tests that modify module-level globals."""
    module_name = "dokima"
    if module_name in sys.modules:
        del sys.modules[module_name]
    return _load_panel()


@pytest.fixture
def panel():
    """Loaded dokima module with globals set. Fresh per test."""
    return _load_panel()


@pytest.fixture
def tmpdir_path():
    """Temporary directory as a string path."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def fake_roadmap(tmpdir_path):
    """Create a temporary roadmap.md and return function to create with content."""
    p = os.path.join(tmpdir_path, "roadmap.md")
    def _create(content):
        with open(p, "w") as f:
            f.write(content)
        return p
    return _create


@pytest.fixture
def fake_agents_md(tmpdir_path):
    """Create a temporary AGENTS.md and return function to create with content."""
    p = os.path.join(tmpdir_path, "AGENTS.md")
    def _create(content):
        with open(p, "w") as f:
            f.write(content)
        return p
    return _create
