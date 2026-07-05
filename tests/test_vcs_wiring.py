"""Tests for --vcs flag wiring into dokima main() entry point.

Verifies that when --vcs is passed on the command line,
it takes priority over auto-detection and PANEL_VCS env var.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock


# ── VCS flag wiring into VCS detection section ──────────────────────

class TestVcsFlagWiring:
    """--vcs flag is captured and passed to VCS detection with highest priority."""

    def test_vcs_flag_via_parse_vcs_flag_github(self):
        """vcs.parse_vcs_flag() finds --vcs github in sys.argv."""
        import vcs
        old = sys.argv
        try:
            sys.argv = ["dokima", "--vcs", "github", "run"]
            result = vcs.parse_vcs_flag()
            assert result == "github"
        finally:
            sys.argv = old

    def test_vcs_flag_via_parse_vcs_flag_gitlab(self):
        """vcs.parse_vcs_flag() finds --vcs gitlab in sys.argv."""
        import vcs
        old = sys.argv
        try:
            sys.argv = ["dokima", "--vcs", "gitlab"]
            result = vcs.parse_vcs_flag()
            assert result == "gitlab"
        finally:
            sys.argv = old

    def test_vcs_wiring_sets_backend_from_argparse_subcommand(self, tmpdir):
        """When 'dokima next --vcs gitlab' is run, vcs.VCS_BACKEND is set to 'gitlab'.

        This verifies the argparse --vcs value flows through to VCS_BACKEND.
        """
        import vcs
        from conftest import _load_panel

        panel = _load_panel()

        # Set up a minimal project
        project_dir = os.path.join(str(tmpdir), "vcs-test")
        os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
        with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

        import subprocess
        subprocess.run(["git", "init", project_dir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
        subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
        subprocess.run(["git", "-C", project_dir, "add", "-A"])
        subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                        "https://github.com/test-owner/test-repo.git"])

        old = sys.argv
        try:
            sys.argv = ["dokima", "next", "--vcs", "gitlab", project_dir]

            patches = [
                patch.object(panel._agent, "call_agent",
                             return_value={"content": "M", "tokens": 1}),
                patch.object(panel, "_set_gh_token"),
                patch.object(panel, "git", return_value=("", "", 0)),
                patch.object(panel, "gh", return_value=("", "", 0)),
                patch.object(panel, "load_key", return_value="fk"),
                patch.object(panel, "load_github_token", return_value="ft"),
                patch.object(panel, "detect_repo", return_value="t/t"),
                patch.object(panel, "acquire_lock", return_value=(True, None)),
                patch.object(panel, "_cleanup_lock"),
                patch("time.sleep"),
                patch.object(panel, "_safe_run",
                             return_value=subprocess.CompletedProcess(
                                 args=[], returncode=0)),
            ]

            from contextlib import ExitStack
            with ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)

                # Run main() — it should call vcs.parse_vcs_flag() and set VCS_BACKEND
                # We want to verify the argparse arg flows through
                try:
                    panel.main()
                except SystemExit:
                    pass

            # Verify: --vcs gitlab should set VCS_BACKEND to 'gitlab'
            assert vcs.VCS_BACKEND == "gitlab", (
                f"Expected VCS_BACKEND='gitlab', got '{vcs.VCS_BACKEND}'. "
                f"sys.argv was: {sys.argv}"
            )
        finally:
            sys.argv = old

    def test_vcs_wiring_auto_detects_github_when_no_flag(self, tmpdir):
        """When no --vcs flag, auto-detection from git remote sets VCS_BACKEND."""
        import vcs
        from conftest import _load_panel

        panel = _load_panel()

        project_dir = os.path.join(str(tmpdir), "vcs-auto-test")
        os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
        with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

        import subprocess
        subprocess.run(["git", "init", project_dir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
        subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
        subprocess.run(["git", "-C", project_dir, "add", "-A"])
        subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                        "https://gitlab.com/test-group/test-proj.git"])

        old = sys.argv
        try:
            sys.argv = ["dokima", "next", project_dir]

            patches = [
                patch.object(panel._agent, "call_agent",
                             return_value={"content": "M", "tokens": 1}),
                patch.object(panel, "_set_gh_token"),
                patch.object(panel, "git", return_value=("", "", 0)),
                patch.object(panel, "gh", return_value=("", "", 0)),
                patch.object(panel, "load_key", return_value="fk"),
                patch.object(panel, "load_github_token", return_value="ft"),
                patch.object(panel, "detect_repo", return_value="t/t"),
                patch.object(panel, "acquire_lock", return_value=(True, None)),
                patch.object(panel, "_cleanup_lock"),
                patch("time.sleep"),
                patch.object(panel, "_safe_run",
                             return_value=subprocess.CompletedProcess(
                                 args=[], returncode=0)),
            ]

            from contextlib import ExitStack
            with ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)
                try:
                    panel.main()
                except SystemExit:
                    pass

            assert vcs.VCS_BACKEND == "gitlab", (
                f"Expected auto-detected VCS_BACKEND='gitlab', got '{vcs.VCS_BACKEND}'"
            )
        finally:
            sys.argv = old

    def test_panel_vcs_env_var_sets_backend(self, monkeypatch, tmpdir):
        """PANEL_VCS env var sets VCS_BACKEND without --vcs flag."""
        import vcs
        from conftest import _load_panel

        monkeypatch.setenv("PANEL_VCS", "gitlab")

        panel = _load_panel()

        project_dir = os.path.join(str(tmpdir), "vcs-env-test")
        os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
        with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

        import subprocess
        subprocess.run(["git", "init", project_dir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
        subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
        subprocess.run(["git", "-C", project_dir, "add", "-A"])
        subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                        "https://github.com/test-owner/test-repo.git"])

        old = sys.argv
        try:
            sys.argv = ["dokima", "next", project_dir]

            patches = [
                patch.object(panel._agent, "call_agent",
                             return_value={"content": "M", "tokens": 1}),
                patch.object(panel, "_set_gh_token"),
                patch.object(panel, "git", return_value=("", "", 0)),
                patch.object(panel, "gh", return_value=("", "", 0)),
                patch.object(panel, "load_key", return_value="fk"),
                patch.object(panel, "load_github_token", return_value="ft"),
                patch.object(panel, "detect_repo", return_value="t/t"),
                patch.object(panel, "acquire_lock", return_value=(True, None)),
                patch.object(panel, "_cleanup_lock"),
                patch("time.sleep"),
                patch.object(panel, "_safe_run",
                             return_value=subprocess.CompletedProcess(
                                 args=[], returncode=0)),
            ]

            from contextlib import ExitStack
            with ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)
                try:
                    panel.main()
                except SystemExit:
                    pass

            # PANEL_VCS env should override auto-detect, setting GitLab
            assert vcs.VCS_BACKEND == "gitlab", (
                f"Expected PANEL_VCS env to set VCS_BACKEND='gitlab', got '{vcs.VCS_BACKEND}'"
            )
        finally:
            sys.argv = old

    def test_vcs_flag_priority_over_env_var(self, monkeypatch, tmpdir):
        """--vcs flag takes priority over PANEL_VCS env var."""
        import vcs
        from conftest import _load_panel

        monkeypatch.setenv("PANEL_VCS", "github")
        panel = _load_panel()

        project_dir = os.path.join(str(tmpdir), "vcs-priority-test")
        os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
        with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

        import subprocess
        subprocess.run(["git", "init", project_dir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
        subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
        subprocess.run(["git", "-C", project_dir, "add", "-A"])
        subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                        "https://github.com/test-owner/test-repo.git"])

        old = sys.argv
        try:
            sys.argv = ["dokima", "next", "--vcs", "gitlab", project_dir]

            patches = [
                patch.object(panel._agent, "call_agent",
                             return_value={"content": "M", "tokens": 1}),
                patch.object(panel, "_set_gh_token"),
                patch.object(panel, "git", return_value=("", "", 0)),
                patch.object(panel, "gh", return_value=("", "", 0)),
                patch.object(panel, "load_key", return_value="fk"),
                patch.object(panel, "load_github_token", return_value="ft"),
                patch.object(panel, "detect_repo", return_value="t/t"),
                patch.object(panel, "acquire_lock", return_value=(True, None)),
                patch.object(panel, "_cleanup_lock"),
                patch("time.sleep"),
                patch.object(panel, "_safe_run",
                             return_value=subprocess.CompletedProcess(
                                 args=[], returncode=0)),
            ]

            from contextlib import ExitStack
            with ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)
                try:
                    panel.main()
                except SystemExit:
                    pass

            # --vcs gitlab flag should win over PANEL_VCS=github env
            assert vcs.VCS_BACKEND == "gitlab", (
                f"Expected --vcs flag priority, got VCS_BACKEND='{vcs.VCS_BACKEND}'"
            )
        finally:
            sys.argv = old

    def test_fix_subcommand_vcs_flag(self, tmpdir):
        """'dokima fix --vcs gitlab' sets VCS_BACKEND to gitlab."""
        import vcs
        from conftest import _load_panel

        panel = _load_panel()

        project_dir = os.path.join(str(tmpdir), "vcs-fix-test")
        os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
        with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

        import subprocess
        subprocess.run(["git", "init", project_dir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
        subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
        subprocess.run(["git", "-C", project_dir, "add", "-A"])
        subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                        "https://github.com/test-owner/test-repo.git"])

        old = sys.argv
        try:
            sys.argv = ["dokima", "fix", "--vcs", "gitlab", project_dir]

            patches = [
                patch.object(panel._agent, "call_agent",
                             return_value={"content": "M", "tokens": 1}),
                patch.object(panel, "_set_gh_token"),
                patch.object(panel, "git", return_value=("", "", 0)),
                patch.object(panel, "gh", return_value=("", "", 0)),
                patch.object(panel, "load_key", return_value="fk"),
                patch.object(panel, "load_github_token", return_value="ft"),
                patch.object(panel, "detect_repo", return_value="t/t"),
                patch.object(panel, "acquire_lock", return_value=(True, None)),
                patch.object(panel, "_cleanup_lock"),
                patch("time.sleep"),
                patch.object(panel, "_safe_run",
                             return_value=subprocess.CompletedProcess(
                                 args=[], returncode=0)),
                # Mock run_fix_mode to prevent actual fix pipeline execution
                patch.object(panel._pipeline, "run_fix_mode"),
            ]

            from contextlib import ExitStack
            with ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)
                try:
                    panel.main()
                except SystemExit:
                    pass

            assert vcs.VCS_BACKEND == "gitlab", (
                f"Expected fix --vcs gitlab to set VCS_BACKEND='gitlab', got '{vcs.VCS_BACKEND}'"
            )
        finally:
            sys.argv = old

    def test_legacy_path_vcs_flag(self, tmpdir):
        """Legacy path: 'dokima --vcs gitlab feature dir' sets VCS_BACKEND to gitlab."""
        import vcs
        from conftest import _load_panel

        panel = _load_panel()

        project_dir = os.path.join(str(tmpdir), "vcs-legacy-test")
        os.makedirs(os.path.join(project_dir, "specs"), exist_ok=True)
        with open(os.path.join(project_dir, "AGENTS.md"), "w") as f:
            f.write("# Test\n\n## Commands\n- Test: `echo ok`\n- Build: `echo ok`\n")

        import subprocess
        subprocess.run(["git", "init", project_dir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "config", "user.email", "t@t.com"])
        subprocess.run(["git", "-C", project_dir, "config", "user.name", "T"])
        subprocess.run(["git", "-C", project_dir, "add", "-A"])
        subprocess.run(["git", "-C", project_dir, "commit", "-m", "init"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", project_dir, "remote", "add", "origin",
                        "https://github.com/test-owner/test-repo.git"])

        old = sys.argv
        try:
            sys.argv = ["dokima", "--vcs", "gitlab", "test feature", project_dir]

            patches = [
                patch.object(panel._agent, "call_agent",
                             return_value={"content": "M", "tokens": 1}),
                patch.object(panel, "_set_gh_token"),
                patch.object(panel, "git", return_value=("", "", 0)),
                patch.object(panel, "gh", return_value=("", "", 0)),
                patch.object(panel, "load_key", return_value="fk"),
                patch.object(panel, "load_github_token", return_value="ft"),
                patch.object(panel, "detect_repo", return_value="t/t"),
                patch.object(panel, "acquire_lock", return_value=(True, None)),
                patch.object(panel, "_cleanup_lock"),
                patch("time.sleep"),
                patch.object(panel, "_safe_run",
                             return_value=subprocess.CompletedProcess(
                                 args=[], returncode=0)),
            ]

            from contextlib import ExitStack
            with ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)
                try:
                    panel.main()
                except SystemExit:
                    pass

            assert vcs.VCS_BACKEND == "gitlab", (
                f"Expected legacy --vcs gitlab to set VCS_BACKEND='gitlab', got '{vcs.VCS_BACKEND}'"
            )
        finally:
            sys.argv = old
