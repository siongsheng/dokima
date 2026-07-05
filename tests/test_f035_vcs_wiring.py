"""Tests for F035: --vcs flag wiring in dokima entry point.

Verifies that the --vcs flag, when passed on the CLI, actually
sets vcs.VCS_BACKEND in the vcs module at startup.
"""

import os
import sys
import subprocess
import pytest
from unittest.mock import patch


class TestVcsFlagWiring:
    """--vcs flag in main() sets vcs.VCS_BACKEND."""

    def test_vcs_flag_gitlab_wired_in_main(self, panel, tmp_path):
        """--vcs gitlab in CLI args → vcs.VCS_BACKEND == 'gitlab' after main()."""
        import vcs

        project_dir = str(tmp_path / "proj")
        os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
        with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")
        subprocess.run(["git", "init", project_dir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
        subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
        subprocess.run(["git", "-C", project_dir, "add", "-A"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                        "https://github.com/t/t.git"])

        old_argv = sys.argv
        try:
            sys.argv = ['dokima', 'next', '--vcs', 'gitlab', project_dir]

            def mock_run_fix(**kwargs):
                pass

            with patch.object(panel, 'acquire_lock', return_value=(None, None)):
                with patch.object(panel, 'load_key', return_value="test-key"):
                    with patch.object(panel, 'detect_repo', return_value="t/t"):
                        with patch.object(panel, '_set_gh_token'):
                            with patch.object(panel, 'detect_commands',
                                              return_value=("echo test", "echo build", "echo lint")):
                                with patch.object(panel._pipeline, 'run_pipeline', side_effect=mock_run_fix):
                                    panel.main()

            # After main() processes --vcs gitlab flag, vcs.VCS_BACKEND should be "gitlab"
            assert vcs.VCS_BACKEND == "gitlab", (
                f"Expected vcs.VCS_BACKEND='gitlab' after --vcs gitlab flag, "
                f"got '{vcs.VCS_BACKEND}'"
            )
            assert vcs.VCS_TOKEN_ENV in ("GITLAB_TOKEN", "GLAB_TOKEN"), (
                f"Expected GITLAB_TOKEN/GLAB_TOKEN, got '{vcs.VCS_TOKEN_ENV}'"
            )
        finally:
            sys.argv = old_argv
            # Reset vcs module state
            vcs.VCS_BACKEND = "github"
            vcs.VCS_TOKEN_ENV = "GH_TOKEN"
            vcs.REPO = ""

    def test_vcs_flag_github_explicit_in_main(self, panel, tmp_path):
        """--vcs github in CLI args → vcs.VCS_BACKEND stays 'github'."""
        import vcs

        project_dir = str(tmp_path / "proj2")
        os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
        with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")
        subprocess.run(["git", "init", project_dir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
        subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
        subprocess.run(["git", "-C", project_dir, "add", "-A"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                        "https://github.com/t/t.git"])

        old_argv = sys.argv
        try:
            # Ensure vcs backend starts as something else to verify it gets set
            vcs.VCS_BACKEND = "gitlab"
            sys.argv = ['dokima', '--vcs', 'github', 'Test feature', project_dir]

            def mock_run_pipeline(*args, **kwargs):
                pass

            with patch.object(panel, 'acquire_lock', return_value=(None, None)):
                with patch.object(panel, 'load_key', return_value="test-key"):
                    with patch.object(panel, 'detect_repo', return_value="t/t"):
                        with patch.object(panel, '_set_gh_token'):
                            with patch.object(panel, 'detect_commands',
                                              return_value=("echo test", "echo build", "echo lint")):
                                with patch.object(panel, 'run_pipeline', side_effect=mock_run_pipeline):
                                    panel.main()

            assert vcs.VCS_BACKEND == "github", (
                f"Expected vcs.VCS_BACKEND='github' after --vcs github flag, "
                f"got '{vcs.VCS_BACKEND}'"
            )
        finally:
            sys.argv = old_argv
            vcs.VCS_BACKEND = "github"
            vcs.VCS_TOKEN_ENV = "GH_TOKEN"
            vcs.REPO = ""

    def test_auto_detect_without_vcs_flag(self, panel, tmp_path):
        """Without --vcs flag, auto-detection should run from git remote."""
        import vcs

        project_dir = str(tmp_path / "proj3")
        os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
        with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")
        subprocess.run(["git", "init", project_dir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
        subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
        subprocess.run(["git", "-C", project_dir, "add", "-A"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                        "https://github.com/t/t.git"])

        old_argv = sys.argv
        try:
            # Reset to unknown state that should be auto-detected
            vcs.VCS_BACKEND = "gitlab"
            sys.argv = ['dokima', 'next', project_dir]

            def mock_run_pipeline(*args, **kwargs):
                pass

            with patch.object(panel, 'acquire_lock', return_value=(None, None)):
                with patch.object(panel, 'load_key', return_value="test-key"):
                    with patch.object(panel, 'detect_repo', return_value="t/t"):
                        with patch.object(panel, '_set_gh_token'):
                            with patch.object(panel, 'detect_commands',
                                              return_value=("echo test", "echo build", "echo lint")):
                                with patch.object(panel._pipeline, 'run_pipeline', side_effect=mock_run_pipeline):
                                    panel.main()

            # Auto-detection should have detected github from the remote
            assert vcs.VCS_BACKEND == "github", (
                f"Expected auto-detection to set VCS_BACKEND='github', "
                f"got '{vcs.VCS_BACKEND}'"
            )
        finally:
            sys.argv = old_argv
            vcs.VCS_BACKEND = "github"
            vcs.VCS_TOKEN_ENV = "GH_TOKEN"
            vcs.REPO = ""


class TestDocsContentForGitlab:
    """Documentation files reference GitLab support."""

    def test_agents_md_mentions_glab(self):
        """AGENTS.md line ~10 should mention GitHub CLI (gh) or GitLab CLI (glab)."""
        agents_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "AGENTS.md"
        )
        with open(agents_path) as f:
            content = f.read()
        # After fix: should mention both gh and glab
        assert "glab" in content.lower(), (
            "AGENTS.md should mention GitLab CLI (glab) for PR/issue management"
        )

    def test_readme_md_mentions_gitlab(self):
        """README.md should have a GitLab usage section."""
        readme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "README.md"
        )
        with open(readme_path) as f:
            content = f.read()
        assert "GitLab" in content, (
            "README.md should document GitLab usage"
        )
        assert "glab" in content.lower(), (
            "README.md should mention glab CLI installation"
        )

    def test_setup_md_mentions_gitlab(self):
        """docs/setup.md should have GitLab setup instructions."""
        setup_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docs", "setup.md"
        )
        with open(setup_path) as f:
            content = f.read()
        assert "GitLab" in content, (
            "docs/setup.md should document GitLab setup"
        )
        assert "glab" in content.lower(), (
            "docs/setup.md should mention glab auth login"
        )
