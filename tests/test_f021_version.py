"""Tests for F021: Semantic Versioning + GitHub Releases — --version and --upgrade flags."""
import subprocess, os, sys, json

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dokima")

def _run(*args):
    """Run dokima with given args and return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, timeout=10
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def test_version_flag_prints_version_and_exits_0():
    """dokima --version prints 'dokima vX.Y.Z' and exits 0."""
    rc, out, err = _run("--version")
    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
    assert out.startswith("dokima v"), f"Expected 'dokima v...', got: {out}"
    # Should have a semver-like version after the 'v'
    parts = out.split("v", 1)
    assert len(parts) == 2, f"Expected 'dokima v<version>', got: {out}"
    version = parts[1]
    # Should be something like X.Y.Z
    assert "." in version, f"Expected semver, got version: {version}"


def test_help_includes_version_command():
    """--help output includes --version in CONTROL section."""
    rc, out, err = _run("--help")
    assert rc == 0, f"Expected exit 0, got {rc}"
    assert "dokima --version" in out, f"--version not in help output:\n{out}"


def test_help_json_includes_version():
    """--help-json includes version field and --version command."""
    rc, out, err = _run("--help-json")
    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {err}"
    data = json.loads(out)
    assert "version" in data, f"No 'version' field in help-json: {data}"
    assert data["version"], f"version field is empty"
    commands = data.get("commands", [])
    version_cmds = [c for c in commands if c.get("name") == "--version"]
    assert version_cmds, f"--version not in commands array: {commands}"
