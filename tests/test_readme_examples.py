"""Tests for README.md examples reflecting CLI redesign (F030: replace --add with --next)."""
import os


README_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))


def _read_readme():
    """Read README.md and return its content."""
    with open(README_PATH) as f:
        return f.read()


class TestReadmeExamples:
    """Task 11: README.md Usage section should reflect --next/--add workflow."""

    def test_readme_exists(self):
        """README.md exists at project root."""
        assert os.path.exists(README_PATH), "README.md must exist at project root"

    def test_readme_usage_has_next_flag(self):
        """Usage section mentions --next example."""
        content = _read_readme()
        # Find the Usage section: between "### Usage" and the next "##" or ">"
        assert "--next" in content, (
            "README.md must include --next usage example"
        )

    def test_readme_usage_has_add_flag(self):
        """Usage section mentions --add example for roadmap addition."""
        content = _read_readme()
        assert "--add" in content, (
            "README.md must include --add usage example for adding to roadmap"
        )

    def test_readme_usage_shows_roadmap_workflow(self):
        """Usage section shows the full roadmap workflow: --add then --next."""
        content = _read_readme()
        # The --add should appear before --next as it's the "add to roadmap" step
        add_pos = content.find("--add")
        next_pos = content.find("--next")
        assert add_pos != -1, "--add not found in README"
        assert next_pos != -1, "--next not found in README"
        # --add should appear before --next in the workflow flow
        assert add_pos < next_pos, (
            "README workflow should show --add (add to roadmap) before --next (build next). "
            f"Found --add at position {add_pos}, --next at position {next_pos}"
        )

    def test_readme_usage_has_continuous_flag(self):
        """Usage section mentions --continuous for full sprint mode."""
        content = _read_readme()
        assert "--continuous" in content, (
            "README.md must include --continuous usage example"
        )
