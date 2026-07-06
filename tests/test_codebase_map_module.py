"""Tests for codebase_map.py module — verifying extraction from utils.py.

All map-generation functions that were previously in utils.py (Task 3 of F041)
should be importable from codebase_map module.
"""
import importlib
import pytest


# ── Module importability ────────────────────────────────────────

def test_codebase_map_module_importable():
    """codebase_map module must be importable."""
    module = importlib.import_module("codebase_map")
    assert module is not None
    assert hasattr(module, "__doc__")


# ── Public API surface ──────────────────────────────────────────

PUBLIC_FUNCTIONS = [
    "generate_codebase_map",
    "load_map_enrichments",
    "save_map_enrichments",
    "extract_map_enrichments",
]


@pytest.mark.parametrize("func_name", PUBLIC_FUNCTIONS)
def test_public_function_importable_from_codebase_map(func_name):
    """Each public map function must be importable from codebase_map."""
    module = importlib.import_module("codebase_map")
    assert hasattr(module, func_name), f"Missing {func_name} in codebase_map"
    fn = getattr(module, func_name)
    assert callable(fn), f"{func_name} must be callable"


# ── Private helpers ─────────────────────────────────────────────

PRIVATE_FUNCTIONS = [
    "_classify_domain",
    "_build_domain_map",
    "_build_impact_map",
    "_build_test_map",
    "_find_key_files",
    "_describe_file",
]


@pytest.mark.parametrize("func_name", PRIVATE_FUNCTIONS)
def test_private_helper_importable_from_codebase_map(func_name):
    """Each private helper must be importable from codebase_map."""
    module = importlib.import_module("codebase_map")
    assert hasattr(module, func_name), f"Missing {func_name} in codebase_map"
    fn = getattr(module, func_name)
    assert callable(fn), f"{func_name} must be callable"


# ── Integration parity ──────────────────────────────────────────

def test_generate_codebase_map_signature_matches():
    """generate_codebase_map must accept (project_dir, full=False)."""
    import codebase_map
    import inspect
    sig = inspect.signature(codebase_map.generate_codebase_map)
    params = list(sig.parameters.keys())
    assert "project_dir" in params
    assert "full" in params


def test_load_map_enrichments_signature_matches():
    """load_map_enrichments must accept (project_dir)."""
    import codebase_map
    import inspect
    sig = inspect.signature(codebase_map.load_map_enrichments)
    params = list(sig.parameters.keys())
    assert "project_dir" in params
