#!/usr/bin/env python3
"""Standalone real-code verification — check that functions referenced in tests exist in source.

Usage: python3 scripts/verify_imports.py <project-dir>

Scans test files for ``from <module> import <name>`` statements and
``@patch('module.name')`` / ``mock.patch('module.name')`` references.
Cross-references each name against the actual source module's ``dir()``.
Prints diagnostics for missing implementations.

Exit codes:
  0 = all references resolve
  1 = not enough info (no source modules or other issues)
  2 = missing implementations found (tests passed but real code missing)
  3 = script error (bad arguments)
"""

import ast
import glob
import importlib.util
import os
import sys


def discover_source_modules(project_dir):
    """Find all Python source modules in project_dir (exclude __init__, test_*)."""
    modules = []
    for pyfile in sorted(glob.glob(os.path.join(project_dir, "*.py"))):
        basename = os.path.basename(pyfile)
        mod_name = os.path.splitext(basename)[0]
        if basename == "__init__.py" or basename.startswith("test_"):
            continue
        modules.append(mod_name)
    return modules


def load_source_module(project_dir, mod_name):
    """Load a source module by name and return set(dir(mod)) or None on failure."""
    mod_path = os.path.join(project_dir, mod_name + ".py")
    if not os.path.isfile(mod_path):
        return None
    try:
        spec = importlib.util.spec_from_file_location(mod_name, mod_path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return set(dir(mod))
    except Exception:
        return None


def check_patch_arg(node, source_names, fname):
    """Check if an AST Call node is patch() / mock.patch() with a missing target.

    Returns list of violation strings (empty if no violation).
    """
    if not isinstance(node, ast.Call):
        return []

    # Determine function name: "patch" or "*.patch"
    func_name = None
    if isinstance(node.func, ast.Name):
        func_name = node.func.id
    elif isinstance(node.func, ast.Attribute):
        func_name = node.func.attr

    if func_name != "patch":
        return []

    if not node.args:
        return []
    first_arg = node.args[0]
    if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
        return []

    target = first_arg.value  # e.g. "utils.nonexistent_func"
    if "." not in target:
        return []

    module_name, attr_name = target.split(".", 1)
    if module_name not in source_names:
        return []

    if attr_name.startswith("_"):
        return []

    if attr_name not in source_names[module_name]:
        lineno = getattr(node, "lineno", 0)
        return ["{}.{}: {}:{}".format(module_name, attr_name, fname, lineno)]

    return []


def scan_test_file(fpath, source_names):
    """Scan a single test file via AST and return list of violation strings."""
    missing = []
    fname = os.path.basename(fpath)

    try:
        with open(fpath, "r") as f:
            source = f.read()
        tree = ast.parse(source, filename=fpath)
    except Exception:
        return []  # syntax error or unreadable — skip gracefully

    # Check from X import Y statements
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module is None:
            continue
        if node.module not in source_names:
            continue

        mod_names = source_names[node.module]
        for alias in node.names:
            name = alias.name
            if name.startswith("_"):
                continue  # skip private names
            if name not in mod_names:
                missing.append(
                    "{}.{}: {}:{}".format(node.module, name, fname, node.lineno)
                )

    # Check @patch decorators and mock.patch() calls
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                missing.extend(check_patch_arg(decorator, source_names, fname))
        if isinstance(node, ast.Call):
            missing.extend(check_patch_arg(node, source_names, fname))

    return missing


def verify_imports(project_dir):
    """Run real-code verification across all test files.

    Returns (violations, exit_code).
    """
    tests_dir = os.path.join(project_dir, "tests")
    if not os.path.isdir(tests_dir):
        print("No tests/ directory found — nothing to verify.")
        return [], 0

    # Discover and load source modules
    source_modules = discover_source_modules(project_dir)
    if not source_modules:
        print("No source modules found in {}".format(project_dir))
        return [], 1

    source_names = {}
    for mod_name in source_modules:
        names = load_source_module(project_dir, mod_name)
        if names is not None:
            source_names[mod_name] = names

    if not source_names:
        print("Could not load any source modules.")
        return [], 1

    # Scan test files
    missing = []
    test_files = sorted(
        f for f in os.listdir(tests_dir) if f.endswith(".py")
    )
    for test_file in test_files:
        fpath = os.path.join(tests_dir, test_file)
        missing.extend(scan_test_file(fpath, source_names))

    if not missing:
        print("All {} test file(s) reference only existing functions.".format(
            len(test_files)))
        return [], 0

    # Report violations
    print("MISSING IMPLEMENTATIONS — tests passed but real code is missing:")
    for m in sorted(set(missing)):
        print("  {}".format(m))
    print("\n{} function(s) referenced in tests but not found in source.".format(
        len(missing)))
    return missing, 2


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/verify_imports.py <project-dir>",
              file=sys.stderr)
        print("", file=sys.stderr)
        print("Verifies that functions referenced in test files exist in source modules.",
              file=sys.stderr)
        sys.exit(3)

    project_dir = sys.argv[1]
    if not os.path.isdir(project_dir):
        print("Error: '{}' is not a directory".format(project_dir),
              file=sys.stderr)
        sys.exit(3)

    violations, exit_code = verify_imports(project_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
