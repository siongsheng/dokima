"""Codebase map generation functions extracted from utils.py (F041).

Contains generate_codebase_map(), _build_domain_map(), _build_impact_map().
Uses lazy imports from utils for shared helpers.
"""

import os
import re
import json
import datetime


def _classify_domain(rel_path):
    """Classify a file into a domain group based on its path."""
    parts = rel_path.split(os.sep)

    if parts[0] == 'tests':
        return 'Tests'
    if parts[0] == 'scripts':
        return 'Scripts'
    if parts[0] == 'skills':
        return 'Skills'
    if parts[0] == 'docs':
        return 'Documentation'
    if parts[0] == 'src' or parts[0] == 'lib':
        return 'Source Code'

    # Root-level classification by filename heuristics
    basename = os.path.basename(rel_path)
    name_lower = basename.lower()

    # Specific well-known filenames first (before substring matches)
    if basename == 'AGENTS.md' or basename == 'README.md' or basename == 'MAINTAINERS.md' or basename == 'CONTRIBUTING.md':
        return 'Documentation'
    if basename == 'dokima' or basename == 'main.py' or basename == 'index.js' or basename == 'index.ts':
        return 'Entry Point'
    if 'pipeline' in name_lower or 'workflow' in name_lower or 'orchestrat' in name_lower:
        return 'Pipeline Orchestration'
    if 'agent' in name_lower and 'test' not in name_lower:
        return 'Agent Management'
    if 'roadmap' in name_lower or 'status' in name_lower or 'tasks' in name_lower:
        return 'Pipeline Orchestration'
    if 'util' in name_lower or 'helper' in name_lower:
        return 'Utilities'
    if 'config' in name_lower or 'setting' in name_lower or basename.endswith('.toml') or basename.endswith('.yaml') or basename.endswith('.yml'):
        return 'Configuration'

    ext = os.path.splitext(basename)[1]
    if ext in ('.css', '.scss'):
        return 'Styles'
    if ext in ('.md', '.mdx'):
        return 'Documentation'
    if ext in ('.sh', '.bash'):
        return 'Scripts'
    if ext == '.json':
        return 'Configuration'

    return 'Other'



def _build_domain_map(all_files):
    """Build the Domain Map section: files grouped by domain."""
    groups = {}
    for rel_path, desc in all_files:
        domain = _classify_domain(rel_path)
        if domain not in groups:
            groups[domain] = []
        groups[domain].append((rel_path, desc))

    # Order domains deterministically
    domain_order = [
        'Entry Point', 'Pipeline Orchestration', 'Agent Management',
        'Source Code', 'Utilities', 'Configuration', 'Scripts', 'Skills',
        'Tests', 'Styles', 'Documentation', 'Other'
    ]

    lines = []
    for domain in domain_order:
        if domain not in groups:
            continue
        lines.append(f"### {domain}")
        for rel_path, desc in sorted(groups[domain]):
            if desc:
                lines.append(f"- {rel_path}  — {desc}")
            else:
                lines.append(f"- {rel_path}")
        lines.append("")

    if not lines:
        return "No source files detected."

    return '\n'.join(lines).rstrip()

def _build_impact_map(py_files, project_dir):
    """Build the Impact Map section: which files import which modules."""
    import ast as _ast

    if not py_files:
        return "No Python source files detected."

    imports_by_file = {}
    for rel_path, fpath in py_files:
        try:
            with open(fpath, errors='replace') as f:
                source = f.read()
            tree = _ast.parse(source)
            imports = set()
            for node in _ast.walk(tree):
                if isinstance(node, _ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, _ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
            imports_by_file[rel_path] = imports
        except Exception:
            imports_by_file[rel_path] = set()

    # Build all known Python module names (files without .py extension)
    all_modules = set()
    for rel_path, _ in py_files:
        name = os.path.splitext(os.path.basename(rel_path))[0]
        all_modules.add(name)

    lines = []
    for rel_path in sorted(imports_by_file.keys()):
        imports = imports_by_file[rel_path]
        internal = imports & all_modules
        external = imports - all_modules - {'os', 'sys', 're', 'json', 'time', 'datetime',
                                             'subprocess', 'hashlib', 'ast', 'fcntl', 'signal',
                                             'shlex', 'pwd', 'tempfile', 'pathlib', 'typing',
                                             'collections', 'itertools', 'functools', 'math'}

        parts = []
        if internal:
            parts.append(f"imports from {', '.join(sorted(internal))}")
        if external:
            parts.append(f"external: {', '.join(sorted(external))}")

        if parts:
            lines.append(f"- {rel_path} → {'; '.join(parts)}")
        else:
            lines.append(f"- {rel_path} → standalone (stdlib only)")

    if not lines:
        return "No imports detected."

    return '\n'.join(lines)



def generate_codebase_map(project_dir, full=False):
    import utils as _u
    """Generate a deterministic domain-aware codebase map for agents to read at session start.
    Uses file hashes to skip unchanged files (incremental mode).
    Output: specs/codebase-map.md with 4 sections: Start Here, Domain Map, Impact Map, Test Map.
    Returns True if map was updated."""
    import ast as _ast

    specs_dir = os.path.join(project_dir, "specs")
    map_path = os.path.join(specs_dir, "codebase-map.md")
    cache_path = os.path.join(specs_dir, ".map-cache.json")
    os.makedirs(specs_dir, exist_ok=True)

    # Load cache
    cache = {}
    if not full and os.path.exists(cache_path):
        try:
            with open(cache_path) as f:
                cache = json.loads(f.read())
        except (json.JSONDecodeError, IOError):
            cache = {}

    # Tech stack detection (heuristic)
    tech = []
    if os.path.exists(os.path.join(project_dir, "package.json")):
        try:
            with open(os.path.join(project_dir, "package.json")) as f:
                pkg = json.loads(f.read())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps: tech.append(f"Next.js {deps['next'].lstrip('^~')}")
            if "react" in deps: tech.append(f"React {deps['react'].lstrip('^~')}")
            if "tailwindcss" in deps: tech.append("Tailwind CSS")
            if "typescript" in deps: tech.append("TypeScript")
            if "vitest" in deps: tech.append("Vitest")
        except Exception:
            pass
    if os.path.exists(os.path.join(project_dir, "Cargo.toml")):
        tech.append("Rust")
    if os.path.exists(os.path.join(project_dir, "pyproject.toml")):
        tech.append("Python")

    # Read AGENTS.md for commands
    agents_path = os.path.join(project_dir, "AGENTS.md")
    test_cmd = build_cmd = lint_cmd = "?"
    if os.path.exists(agents_path):
        try:
            with open(agents_path) as f:
                agents = f.read()
            for cmd_name, prefix in [("test", "Test:"), ("build", "Build:"), ("lint", "Lint:")]:
                m = re.search(rf'{prefix}\s+(.+)', agents)
                if m:
                    cmd = m.group(1).strip().rstrip('.')
                    if cmd_name == "test": test_cmd = cmd
                    elif cmd_name == "build": build_cmd = cmd
                    elif cmd_name == "lint": lint_cmd = cmd
        except Exception:
            pass

    # Walk the project tree
    source_exts = {'.py', '.ts', '.tsx', '.js', '.jsx', '.rs', '.go', '.css', '.scss',
                   '.md', '.mdx', '.json', '.yaml', '.yml', '.toml', '.sh', '.bash'}
    skip_dirs = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'target',
                 '.next', 'dist', 'build', '.turbo', '.hermes', 'specs', '.map-cache.json'}

    all_files = []       # (rel_path, description) for Domain Map
    py_files = []        # (rel_path, fpath) for Impact Map analysis
    changed = False
    new_cache = {}
    analyzed_files = 0

    for dirpath, dirnames, filenames in os.walk(project_dir):
        dirnames[:] = sorted([d for d in dirnames if d not in skip_dirs and not d.startswith('.')])
        rel_dir = os.path.relpath(dirpath, project_dir)
        if rel_dir == '.':
            rel_dir = ''

        source_files = sorted([f for f in filenames if any(f.endswith(ext) for ext in source_exts)])
        if not source_files:
            continue

        for fname in source_files:
            rel_path = os.path.join(rel_dir, fname) if rel_dir else fname
            fpath = os.path.join(dirpath, fname)

            # Compute hash
            try:
                with open(fpath, 'rb') as f:
                    import hashlib
                    fhash = hashlib.md5(f.read()).hexdigest()
            except Exception:
                continue

            entry = cache.get(rel_path, {})
            old_hash = entry.get("hash", "")
            description = ""
            if old_hash == fhash and not full:
                description = entry.get("desc", "")
            else:
                try:
                    with open(fpath, errors='replace') as f:
                        content = f.read()
                    description = _u._describe_file(fname, content, rel_path)
                    changed = True
                except Exception:
                    description = ""

            new_cache[rel_path] = {"hash": fhash, "desc": description}
            all_files.append((rel_path, description))

            # Track Python files for import analysis
            if fname.endswith('.py'):
                py_files.append((rel_path, fpath))

            analyzed_files += 1

    if not changed and os.path.exists(map_path) and not full:
        return False  # Nothing changed, no need to rewrite

    # ── Domain Map: group files by domain ──
    domain_map = _build_domain_map(all_files)

    # ── Impact Map: analyze Python imports ──
    impact_map = _build_impact_map(py_files, project_dir)

    # ── Test Map: match test files to source modules ──
    test_map = _u._build_test_map(all_files)

    # ── Write map ──
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = os.path.basename(os.path.abspath(project_dir))
    mode = "full" if full else "incremental"
    tech_str = ', '.join(tech) if tech else 'detected at runtime'

    # Start Here section
    key_files = _u._find_key_files(all_files)

    map_content = f"""## Project: {project_name}
## Tech: {tech_str}
## Generated: {now} ({mode} | {analyzed_files} files)

## Start Here
**{project_name}** is a software project in this directory.
- Test: `{test_cmd}`
- Build: `{build_cmd}`
- Lint: `{lint_cmd}`
Key files: {', '.join(key_files) if key_files else 'none detected'}
Read the Domain Map below to understand the file organization before exploring individual files.

## Domain Map
{domain_map}

## Impact Map
{impact_map}

## Test Map
{test_map}
"""

    # -- F028: Agent Guidance (accumulated enrichments) --
    enrichments = _u.load_map_enrichments(project_dir)
    if enrichments:
        guidance_lines = []
        guidance_lines.append("## Agent Guidance")
        guidance_lines.append("> Accumulated across features. Agents read this section as institutional knowledge.")
        guidance_lines.append("")
        for entry in enrichments:
            feat = entry.get("feature", "???")
            gtext = entry.get("guidance", "")
            guidance_lines.append(f"- ({feat}) {gtext}")
        map_content += "\n" + "\n".join(guidance_lines) + "\n"

    with open(map_path, 'w') as f:
        f.write(map_content)
    with open(cache_path, 'w') as f:
        json.dump(new_cache, f, indent=2)

    print(f"  \U0001f4c4 Codebase map: {map_path} ({analyzed_files} files, {mode})", flush=True)
    return True


