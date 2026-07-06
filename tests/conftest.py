"""Shared fixtures for dokima tests."""
import os
import sys
import json
import types
import tempfile
import subprocess
import pytest
from unittest.mock import patch

from context import PipelineContext

PANEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dokima"))


def _load_panel():
    """Load dokima as a Python module via exec.
    Registers in sys.modules so patch('dokima.X') works across all tests.

    No longer sets module globals or installs a setattr override —
    PipelineContext replaces all those globals.
    """
    module_name = "dokima"
    # Remove stale module if present
    if module_name in sys.modules:
        del sys.modules[module_name]
    # Also remove stale sub-modules so fresh imports pick up changes
    for sub in ('tasks', 'utils', 'agent', 'pipeline', 'roadmap'):
        if sub in sys.modules:
            del sys.modules[sub]

    module = types.ModuleType(module_name)
    module.__file__ = PANEL_PATH
    sys.modules[module_name] = module

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


@pytest.fixture(autouse=True)
def _isolate_panel_modules():
    """Save/restore sys.modules around every test to prevent stale
    references from _load()/_load_panel() calls leaking between tests
    (F022b: Modular Architecture — sys.modules state isolation).

    Tests that call _load() directly (not through the panel fixture)
    leave sys.modules pointing to their panel, breaking override
    detection in other tests that use module-level panel references."""
    _sub_module_names = ('tasks', 'utils', 'agent', 'pipeline', 'roadmap', 'dokima')
    _saved = {k: sys.modules.get(k) for k in _sub_module_names}
    _had = {k: k in sys.modules for k in _sub_module_names}

    yield

    for key in _sub_module_names:
        if _had[key] and _saved[key] is not None:
            sys.modules[key] = _saved[key]
        elif key in sys.modules:
            del sys.modules[key]


@pytest.fixture
def panel():
    """Loaded dokima module. Fresh per test.
    Saves/restores sys.modules so stale references from module-level
    imports in other test files don't leak into override detection
    (F022b: Modular Architecture — fix stale sys.modules references)."""
    _sub_module_names = ('tasks', 'utils', 'agent', 'pipeline', 'roadmap', 'dokima')
    _saved = {k: sys.modules.get(k) for k in _sub_module_names}
    _had = {k: k in sys.modules for k in _sub_module_names}

    p = _load_panel()
    yield p

    # Restore sys.modules to pre-test state so module-level imports
    # in other test files resolve correctly.
    for key in _sub_module_names:
        if _had[key] and _saved[key] is not None:
            sys.modules[key] = _saved[key]
        elif key in sys.modules:
            del sys.modules[key]


@pytest.fixture
def ctx():
    """Return a PipelineContext with test defaults.

    This is the new way to create test contexts — no more _load_panel()
    for simple tests that just need a PipelineContext. Tests opt in
    explicitly by requesting this fixture (autouse=False).
    """
    return PipelineContext(
        project_dir="",
        repo="test-owner/test-repo",
        api_key="test-key",
        default_branch="main",
        output_log="/dev/null",
        test_cmd="echo test",
        build_cmd="echo build",
        lint_cmd="echo lint",
    )


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


@pytest.fixture
def test_repo(panel, ctx, tmpdir_path):
    """Create a temporary git repository with AGENTS.md and specs/roadmap.md.
    Sets ctx.project_dir, ctx.repo, and ctx.default_branch.
    Yields the project directory path as a string."""
    project_dir = os.path.join(tmpdir_path, "test-project")
    os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)

    with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
        f.write("# Test Project\n\n## Commands\n- Test: `echo tests-pass`\n- Build: `echo build-ok`\n")

    with open(os.path.join(project_dir, "specs", "roadmap.md"), "w") as f:
        f.write("""# Roadmap\n\n## Phase 1\n\n### F001: Test Feature\n**Priority:** P0\n**Dependencies:** None\n**Status:** [ ] Pending\n**User Story:** Pipeline verification.\n""")

    subprocess.run(["git", "init", project_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "config", "user.email", "test@test.com"])
    subprocess.run(["git", "-C", project_dir, "config", "user.name", "Test"])
    subprocess.run(["git", "-C", project_dir, "add", "-A"])
    subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-C", project_dir, "remote", "add", "origin", "https://github.com/test-owner/test-repo.git"])

    ctx.project_dir = project_dir
    ctx.repo = "test-owner/test-repo"
    ctx.default_branch = "master"

    return project_dir


@pytest.fixture
def mock_orchestrator(panel):
    """Replace panel.spawn_agent with a mock and patch common panel functions
    (git, gh, _set_gh_token, load_key, load_github_token, detect_repo,
    acquire_lock, _cleanup_lock, time.sleep).
    Records spawn_agent calls in spawn_calls list.
    Yields dict with: panel, spawn_calls, mock_spawn
    Stops all patches on teardown."""
    spawn_calls = []

    def mock_spawn(profile, skills, prompt, timeout=600, cwd=None, **kwargs):
        spawn_calls.append(profile)
        return "Mock agent output"

    panel.spawn_agent = mock_spawn

    patches = [
        patch.object(panel, "_set_gh_token"),
        patch.object(panel, "git", return_value=("", "", 0)),
        patch.object(panel, "gh", return_value=("", "", 0)),
        patch.object(panel, "load_key", return_value="fk"),
        patch.object(panel, "load_github_token", return_value="ft"),
        patch.object(panel, "detect_repo", return_value="t/t"),
        patch.object(panel, "acquire_lock", return_value=(True, None)),
        patch.object(panel, "_cleanup_lock"),
        patch("time.sleep"),
    ]

    for p in patches:
        p.start()

    yield {
        "panel": panel,
        "spawn_calls": spawn_calls,
        "mock_spawn": mock_spawn,
    }

    for p in patches:
        p.stop()
