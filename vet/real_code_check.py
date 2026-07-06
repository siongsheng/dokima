#!/usr/bin/env python3
"""real_code_check.py — Verify that functions referenced in test files
actually exist in source modules.

Greps test files for mock.patch / mocker.patch patterns, extracts
(module, func) pairs, and verifies importability via importlib.
Exits 0 if all targets are importable, 1 if any are missing.
"""
import argparse
import importlib
import os
import re
import sys


# ── Regex patterns for mock.patch / mocker.patch calls ──

# Matches: @patch('a.b'), @mock.patch('a.b'), mock.patch('a.b'),
#          mocker.patch('a.b'), with mock.patch('a.b'):
# Captures the full dotted target string (e.g., "pkg.sub.mod.func")
_PATCH_RE = re.compile(
    r"""(?:@|with\s+)?(?:mock\.)?(?:mocker\.)?patch\(\s*(["'])(.+?)\1""",
    re.DOTALL,
)


def extract_targets(test_file_path):
    """Parse a test file and extract (module_target, attr_name) pairs.

    Returns list of {module, func, line} dicts.
    """
    try:
        with open(test_file_path, "r") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    targets = []
    for match in _PATCH_RE.finditer(content):
        target = match.group(2)
        if not target or "." not in target:
            continue
        # Split on last dot: everything before is module, after is func
        parts = target.rsplit(".", 1)
        module_name = parts[0]
        func_name = parts[1]
        if not module_name or not func_name:
            continue
        # Calculate approximate line number
        line_no = content[: match.start()].count("\n") + 1
        targets.append({
            "module": module_name,
            "func": func_name,
            "line": line_no,
        })
    return targets


def verify_target(module_name, func_name, src_dir):
    """Verify that func_name exists on module_name (importable from src_dir).

    Returns (ok: bool, error: str or None).
    """
    # Add src_dir to sys.path so modules are importable
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        return False, "ModuleNotFoundError: {}".format(e)
    except SyntaxError as e:
        return False, "SyntaxError in {}: {}".format(module_name, e)
    except Exception as e:
        return False, "ImportError: {}: {}".format(module_name, e)

    if not hasattr(mod, func_name):
        return False, "AttributeError: module '{}' has no attribute '{}'".format(
            module_name, func_name
        )

    return True, None


def find_test_files(test_dir):
    """Recursively find all .py files in test_dir."""
    test_files = []
    if not os.path.isdir(test_dir):
        return test_files
    for root, _dirs, files in os.walk(test_dir):
        for f in files:
            if f.endswith(".py"):
                test_files.append(os.path.join(root, f))
    return sorted(test_files)


def main():
    parser = argparse.ArgumentParser(
        description="Verify mock.patch targets exist in source modules"
    )
    parser.add_argument(
        "--src-dir", default="src", help="Source directory (default: src)"
    )
    parser.add_argument(
        "--test-dir", default="tests", help="Test directory (default: tests)"
    )
    # Support positional arg as project dir (for compatibility)
    parser.add_argument(
        "project_dir", nargs="?", default=None,
        help="Project directory (sets --src-dir and --test-dir as subdirs)"
    )
    args = parser.parse_args()

    if args.project_dir:
        src_dir = os.path.join(args.project_dir, "src")
        test_dir = os.path.join(args.project_dir, "tests")
    else:
        src_dir = args.src_dir
        test_dir = args.test_dir

    # Resolve to absolute paths
    src_dir = os.path.abspath(src_dir)
    test_dir = os.path.abspath(test_dir)

    if not os.path.isdir(test_dir):
        print("OK: no tests directory ({}), nothing to verify".format(test_dir))
        sys.exit(0)

    test_files = find_test_files(test_dir)
    if not test_files:
        print("OK: no test files found in {}".format(test_dir))
        sys.exit(0)

    errors = []
    seen = set()  # deduplicate (module, func) pairs

    for test_file in test_files:
        targets = extract_targets(test_file)
        for t in targets:
            key = (t["module"], t["func"])
            if key in seen:
                continue
            seen.add(key)

            ok, error = verify_target(t["module"], t["func"], src_dir)
            if not ok:
                rel_path = os.path.relpath(test_file)
                errors.append(
                    "{}:{}: {} (referenced in {})".format(
                        t["module"], t["func"], error, rel_path
                    )
                )

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        print(
            "FAIL: {} unresolvable import(s) found".format(len(errors)),
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print("OK: all imports verified ({} test files checked)".format(len(test_files)))
        sys.exit(0)


if __name__ == "__main__":
    main()
