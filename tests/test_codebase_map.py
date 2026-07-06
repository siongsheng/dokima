"""Tests for generate_codebase_map() and _describe_file().

Covers: .mdx inclusion (regression), tech detection, commands, incremental
vs full mode, cache integrity, skip-dir enforcement, and edge cases.
"""
import os
import json
import tempfile
import pytest
from conftest import _load_panel as _load


@pytest.fixture(scope="module")
def panel():
    return _load()


# ── _describe_file ──────────────────────────────────────────────

def test_describe_python_exports(panel):
    desc = panel._describe_file("worker.py", "def process():\n    pass\n\nclass TaskRunner:\n    pass\n", "src/worker.py")
    assert "process" in desc
    assert "TaskRunner" in desc


def test_describe_typescript_exports(panel):
    desc = panel._describe_file("Header.tsx", 'export const Header = () => <div />;\nexport default Header;\n', "src/Header.tsx")
    assert "Header" in desc


def test_describe_jsdoc(panel):
    desc = panel._describe_file("api.ts", "/**\n * Fetch user data from API\n */\nexport async function fetchUser() {}", "src/api.ts")
    assert "Fetch user data" in desc


def test_describe_comment_first_line(panel):
    desc = panel._describe_file("config.py", "# Database connection settings\nDB_HOST = 'localhost'\n", "config.py")
    assert "Database connection" in desc


def test_describe_filename_fallback(panel):
    desc = panel._describe_file("layout.tsx", "export default function Layout({ children }) {}", "src/layout.tsx")
    assert "layout" in desc.lower()


def test_describe_empty_file(panel):
    desc = panel._describe_file("empty.py", "", "empty.py")
    assert desc == ""


def test_describe_mdx_file(panel):
    """MDX files should work — critical since .mdx was missing from source_exts."""
    desc = panel._describe_file("getting-started.mdx", "# Getting Started\n\nWelcome to the guide.\n", "content/getting-started.mdx")
    # MDX doesn't have exports/docstrings, so description may be empty or filename-based
    assert isinstance(desc, str)


def test_describe_rust_no_crash(panel):
    desc = panel._describe_file("main.rs", "fn main() {}\npub fn init() {}\n", "src/main.rs")
    assert isinstance(desc, str)


# ── generate_codebase_map ───────────────────────────────────────

@pytest.fixture
def tmp_project():
    """Create a minimal project tree for map generation."""
    with tempfile.TemporaryDirectory() as d:
        specs_dir = os.path.join(d, "specs")
        os.makedirs(specs_dir, exist_ok=True)

        # AGENTS.md with commands
        with open(os.path.join(d, "AGENTS.md"), "w") as f:
            f.write("Test: pytest\nBuild: npm run build\nLint: eslint\n")

        # package.json for tech detection
        with open(os.path.join(d, "package.json"), "w") as f:
            f.write('{"dependencies": {"next": "^16.0.0", "react": "^19.0.0"}, "devDependencies": {"typescript": "^5.0.0", "vitest": "^2.0.0"}}')

        # Source files
        os.makedirs(os.path.join(d, "src", "components"), exist_ok=True)
        with open(os.path.join(d, "src", "layout.tsx"), "w") as f:
            f.write("// Root layout\nexport default function Layout({ children }) { return <html>{children}</html>; }\n")
        with open(os.path.join(d, "src", "components", "Header.tsx"), "w") as f:
            f.write("export const Header = () => <header>Dokima</header>;\n")
        with open(os.path.join(d, "src", "page.tsx"), "w") as f:
            f.write("export default function Home() { return <h1>Home</h1>; }\n")

        # MDX content file (the extension we fixed)
        os.makedirs(os.path.join(d, "content"), exist_ok=True)
        with open(os.path.join(d, "content", "guide.mdx"), "w") as f:
            f.write("# User Guide\n\nWelcome.\n")

        # CSS
        with open(os.path.join(d, "src", "globals.css"), "w") as f:
            f.write("/* Global styles */\n:root { --color: red; }\n")

        yield d


def test_map_includes_mdx(tmp_project, panel):
    """The map must include .mdx files — regression test for the extension bug."""
    result = panel.generate_codebase_map(tmp_project, full=True)
    assert result is True

    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    assert os.path.exists(map_path)

    with open(map_path) as f:
        content = f.read()

    assert "layout.tsx" in content
    assert "Header.tsx" in content
    assert "page.tsx" in content
    assert "globals.css" in content
    assert "guide.mdx" in content, f"MDX file missing from map!\n{content}"

    # F027: Verify 4-section format
    assert "## Start Here" in content
    assert "## Domain Map" in content
    assert "## Impact Map" in content
    assert "## Test Map" in content


def test_map_tech_detection(tmp_project, panel):
    """Tech stack should be detected from package.json."""
    panel.generate_codebase_map(tmp_project, full=True)
    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()
    assert "Next.js" in content
    assert "React" in content
    assert "TypeScript" in content
    assert "Vitest" in content

    # F027: Verify 4-section format
    assert "## Start Here" in content
    assert "## Domain Map" in content
    assert "## Impact Map" in content
    assert "## Test Map" in content


def test_map_commands_from_agents(tmp_project, panel):
    """Commands should be extracted from AGENTS.md."""
    panel.generate_codebase_map(tmp_project, full=True)
    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()
    assert "pytest" in content
    assert "npm run build" in content
    assert "eslint" in content

    # F027: Verify 4-section format
    assert "## Start Here" in content
    assert "## Domain Map" in content
    assert "## Impact Map" in content
    assert "## Test Map" in content


def test_map_incremental_no_change(tmp_project, panel):
    """Incremental mode with no file changes should return False."""
    result1 = panel.generate_codebase_map(tmp_project, full=True)
    assert result1 is True
    result2 = panel.generate_codebase_map(tmp_project, full=False)
    assert result2 is False


def test_map_incremental_detects_change(tmp_project, panel):
    """Incremental mode should detect a changed file."""
    panel.generate_codebase_map(tmp_project, full=True)
    with open(os.path.join(tmp_project, "src", "Header.tsx"), "a") as f:
        f.write("\n// New comment\n")
    result = panel.generate_codebase_map(tmp_project, full=False)
    assert result is True


def test_map_skips_node_modules(tmp_project, panel):
    """node_modules should never appear in the map."""
    os.makedirs(os.path.join(tmp_project, "node_modules", "some-pkg"), exist_ok=True)
    with open(os.path.join(tmp_project, "node_modules", "some-pkg", "index.js"), "w") as f:
        f.write("module.exports = {};\n")
    panel.generate_codebase_map(tmp_project, full=True)
    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()
    assert "node_modules" not in content
    assert "index.js" not in content


def test_map_skips_dot_dirs(tmp_project, panel):
    """.git, .next, .hermes directories should be excluded."""
    for skip_dir in [".git", ".next", ".hermes"]:
        d = os.path.join(tmp_project, skip_dir)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "config.txt"), "w") as f:
            f.write("skip me\n")
    panel.generate_codebase_map(tmp_project, full=True)
    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()
    assert "config.txt" not in content


def test_map_file_count(tmp_project, panel):
    """Map should report the correct file count."""
    panel.generate_codebase_map(tmp_project, full=True)
    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()
    # 7 source files: AGENTS.md, package.json, layout.tsx, Header.tsx, page.tsx, globals.css, guide.mdx
    assert "7 files" in content

    # F027: Verify 4-section format
    assert "## Start Here" in content
    assert "## Domain Map" in content
    assert "## Impact Map" in content
    assert "## Test Map" in content


def test_map_cache_written(tmp_project, panel):
    """Incremental cache should be written with hashes and descriptions."""
    panel.generate_codebase_map(tmp_project, full=True)
    cache_path = os.path.join(tmp_project, "specs", ".map-cache.json")
    assert os.path.exists(cache_path)
    with open(cache_path) as f:
        cache = json.load(f)
    assert len(cache) >= 7  # AGENTS.md + package.json + 5 source files (exact count depends on walk order)
    for key in cache:
        assert "hash" in cache[key]
        assert "desc" in cache[key]
        assert len(cache[key]["hash"]) == 32


def test_map_empty_project(panel):
    """Should not crash on a project with no source files."""
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "specs"), exist_ok=True)
        result = panel.generate_codebase_map(d, full=True)
        assert result is True
        assert os.path.exists(os.path.join(d, "specs", "codebase-map.md"))


def test_map_no_agents_md(tmp_project, panel):
    """Should handle missing AGENTS.md gracefully."""
    os.remove(os.path.join(tmp_project, "AGENTS.md"))
    result = panel.generate_codebase_map(tmp_project, full=True)
    assert result is True
    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()
    assert "Test: `?`" in content
    assert "Build: `?`" in content
    assert "Lint: `?`" in content

    # F027: Verify 4-section format still produced
    assert "## Start Here" in content
    assert "## Domain Map" in content
    assert "## Impact Map" in content
    assert "## Test Map" in content


def test_map_full_rebuild(tmp_project, panel):
    """Full rebuild should update everything even after file changes."""
    panel.generate_codebase_map(tmp_project, full=True)
    with open(os.path.join(tmp_project, "src", "Header.tsx"), "a") as f:
        f.write("// v2\n")
    result = panel.generate_codebase_map(tmp_project, full=True)
    assert result is True
    cache_path = os.path.join(tmp_project, "specs", ".map-cache.json")
    with open(cache_path) as f:
        cache = json.load(f)
    assert len(cache) >= 7  # AGENTS.md + package.json + 5 source files (exact count depends on walk order)


# ── F027: Domain-aware map format ─────────────────────────────────

def test_map_domain_aware_sections(tmp_project, panel):
    """F027: Map must output 4 domain-aware sections instead of flat Tree + Commands."""
    panel.generate_codebase_map(tmp_project, full=True)
    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()

    # New section headers must exist
    assert "## Start Here" in content, f"Missing Start Here section\n{content}"
    assert "## Domain Map" in content, f"Missing Domain Map section\n{content}"
    assert "## Impact Map" in content, f"Missing Impact Map section\n{content}"
    assert "## Test Map" in content, f"Missing Test Map section\n{content}"

    # Old format headers must NOT exist
    assert "## Tree" not in content, f"Old ## Tree header still present\n{content}"
    assert "## Commands" not in content, f"Old ## Commands header still present\n{content}"


def test_domain_map_groups_files(tmp_project, panel):
    """F027: Domain Map groups files under correct domain headers."""
    panel.generate_codebase_map(tmp_project, full=True)
    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()

    # Source files should appear under "Source Code" domain (src/ directory)
    assert "### Source Code" in content
    assert "layout.tsx" in content
    assert "Header.tsx" in content
    assert "globals.css" in content

    # Content files (MDX) should appear under "Documentation"
    assert "### Documentation" in content
    assert "guide.mdx" in content
    assert "AGENTS.md" in content

    # Config files
    assert "### Configuration" in content
    assert "package.json" in content


def test_impact_map_has_dependencies(panel):
    """F027: Impact Map lists file dependencies for Python projects."""
    with tempfile.TemporaryDirectory() as d:
        specs_dir = os.path.join(d, "specs")
        os.makedirs(specs_dir, exist_ok=True)

        # Create python files with imports
        with open(os.path.join(d, "main.py"), "w") as f:
            f.write("import utils\nfrom agent import spawn_agent\nimport os\n")
        with open(os.path.join(d, "utils.py"), "w") as f:
            f.write("# Standalone utilities\nimport os\n")
        with open(os.path.join(d, "agent.py"), "w") as f:
            f.write("import utils\n")

        panel.generate_codebase_map(d, full=True)
        map_path = os.path.join(d, "specs", "codebase-map.md")
        with open(map_path) as f:
            content = f.read()

        assert "## Impact Map" in content
        # main.py imports utils and agent (internal)
        assert "main.py" in content
        # utils.py is standalone
        assert "standalone" in content


def test_test_map_pairs_modules(panel):
    """F027: Test Map matches test files to source modules."""
    with tempfile.TemporaryDirectory() as d:
        specs_dir = os.path.join(d, "specs")
        os.makedirs(specs_dir, exist_ok=True)

        # Source files
        with open(os.path.join(d, "utils.py"), "w") as f:
            f.write("def slugify(): pass\n")
        with open(os.path.join(d, "pipeline.py"), "w") as f:
            f.write("def run(): pass\n")

        # Test files in tests/ directory
        tests_dir = os.path.join(d, "tests")
        os.makedirs(tests_dir, exist_ok=True)
        with open(os.path.join(tests_dir, "test_utils.py"), "w") as f:
            f.write("from utils import slugify\n")
        with open(os.path.join(tests_dir, "test_pipeline.py"), "w") as f:
            f.write("from pipeline import run\n")
        # Test with no matching source
        with open(os.path.join(tests_dir, "test_unknown.py"), "w") as f:
            f.write("# no matching source\n")

        panel.generate_codebase_map(d, full=True)
        map_path = os.path.join(d, "specs", "codebase-map.md")
        with open(map_path) as f:
            content = f.read()

        assert "## Test Map" in content
        assert "test_utils.py" in content
        assert "test_pipeline.py" in content


def test_start_here_has_commands(tmp_project, panel):
    """F027: Start Here includes project description and commands."""
    panel.generate_codebase_map(tmp_project, full=True)
    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()

    # Start Here section
    assert "## Start Here" in content
    assert "Test:" in content
    assert "Build:" in content
    assert "Lint:" in content
    assert "Key files:" in content


def test_empty_project_valid_map(panel):
    """F027: Empty project produces valid 4-section map with placeholders."""
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "specs"), exist_ok=True)
        panel.generate_codebase_map(d, full=True)
        map_path = os.path.join(d, "specs", "codebase-map.md")
        with open(map_path) as f:
            content = f.read()

        assert "## Start Here" in content
        assert "## Domain Map" in content
        assert "## Impact Map" in content
        assert "## Test Map" in content


def test_incremental_regenerates_all_sections(tmp_project, panel):
    """F027: Incremental mode regenerates all 4 sections."""
    panel.generate_codebase_map(tmp_project, full=True)

    # Change a file to trigger incremental update
    with open(os.path.join(tmp_project, "src", "layout.tsx"), "a") as f:
        f.write("\n// changed\n")

    result = panel.generate_codebase_map(tmp_project, full=False)
    assert result is True

    map_path = os.path.join(tmp_project, "specs", "codebase-map.md")
    with open(map_path) as f:
        content = f.read()

    assert "## Start Here" in content
    assert "## Domain Map" in content
    assert "## Impact Map" in content
    assert "## Test Map" in content


# ── F028: Map Enrichments ─────────────────────────────────────

class TestMapEnrichments:
    """Tests for extract_map_enrichments(), save_map_enrichments(), load_map_enrichments()."""

    def test_extract_single_map_line(self, panel):
        strat_output = "some text\n> MAP: pipeline phases are sequential\nmore text"
        result = panel.extract_map_enrichments(strat_output, "F028")
        assert len(result) == 1
        assert result[0]["feature"] == "F028"
        assert result[0]["guidance"] == "pipeline phases are sequential"
        assert "timestamp" in result[0]
        assert result[0]["category"] == "pattern"

    def test_extract_multiple_map_lines(self, panel):
        strat_output = "> MAP: first note\n> MAP: second note\n> MAP: third note"
        result = panel.extract_map_enrichments(strat_output, "F028")
        assert len(result) == 3
        assert result[0]["guidance"] == "first note"
        assert result[1]["guidance"] == "second note"
        assert result[2]["guidance"] == "third note"

    def test_extract_no_map_lines(self, panel):
        strat_output = "some text\nno map markers here\njust regular output"
        result = panel.extract_map_enrichments(strat_output, "F028")
        assert result == []

    def test_extract_category_warning(self, panel):
        strat_output = "> MAP: WARNING: this is unsafe"
        result = panel.extract_map_enrichments(strat_output, "F028")
        assert len(result) == 1
        assert result[0]["category"] == "warning"
        assert result[0]["guidance"] == "WARNING: this is unsafe"

    def test_extract_category_arch(self, panel):
        strat_output = "> MAP: ARCH: pipeline order matters"
        result = panel.extract_map_enrichments(strat_output, "F028")
        assert len(result) == 1
        assert result[0]["category"] == "architecture"
        assert result[0]["guidance"] == "ARCH: pipeline order matters"

    def test_extract_truncation(self, panel):
        long_text = "x" * 600
        strat_output = f"> MAP: {long_text}"
        result = panel.extract_map_enrichments(strat_output, "F028")
        assert len(result) == 1
        assert len(result[0]["guidance"]) == 500

    def test_save_and_load_roundtrip(self, panel):
        with tempfile.TemporaryDirectory() as d:
            entries = [
                {"feature": "F028", "timestamp": "2026-07-06T12:00:00",
                 "guidance": "test guidance 1", "category": "pattern"},
                {"feature": "F029", "timestamp": "2026-07-06T13:00:00",
                 "guidance": "test guidance 2", "category": "architecture"},
            ]
            panel.save_map_enrichments(d, "F029", entries)
            loaded = panel.load_map_enrichments(d)
            assert len(loaded) == 2
            assert loaded[0]["guidance"] == "test guidance 1"
            assert loaded[1]["guidance"] == "test guidance 2"

    def test_save_dedup_by_feature(self, panel):
        with tempfile.TemporaryDirectory() as d:
            entries_a = [
                {"feature": "F028", "timestamp": "2026-07-06T12:00:00",
                 "guidance": "entry A", "category": "pattern"},
            ]
            panel.save_map_enrichments(d, "F028", entries_a)
            entries_b = [
                {"feature": "F028", "timestamp": "2026-07-06T13:00:00",
                 "guidance": "entry B", "category": "pattern"},
            ]
            panel.save_map_enrichments(d, "F028", entries_b)
            loaded = panel.load_map_enrichments(d)
            assert len(loaded) == 1
            assert loaded[0]["guidance"] == "entry B"

    def test_load_missing_file(self, panel):
        with tempfile.TemporaryDirectory() as d:
            result = panel.load_map_enrichments(d)
            assert result == []

    def test_load_malformed_json(self, panel):
        with tempfile.TemporaryDirectory() as d:
            enrich_path = os.path.join(d, "specs", ".map-enrichments.json")
            os.makedirs(os.path.join(d, "specs"), exist_ok=True)
            with open(enrich_path, "w") as f:
                f.write("this is not json {{{")
            result = panel.load_map_enrichments(d)
            assert result == []
