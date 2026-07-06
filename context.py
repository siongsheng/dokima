"""PipelineContext dataclass — single source of truth for pipeline configuration.

Replaces 17 module-level globals spread across 7 files with a single,
explicitly-passed dataclass. No behavior change — purely internal refactor.
"""
import os
from dataclasses import dataclass, field


@dataclass
class PipelineContext:
    """Mutable context object carrying all pipeline configuration.

    Constructed in main(), passed to every phase function.
    Fields match the module-level globals that this dataclass replaces:
    PROJECT_DIR, REPO, DEFAULT_BRANCH, API_KEY, PANEL_FEATURE, etc.

    Frozen? No — main() mutates fields during startup (e.g.,
    detect_vcs_backend sets ctx.repo, ctx.vcs_backend).
    Phase functions read-only. Tests mutate freely for setup.
    """
    # ── Paths ──
    project_dir: str = ""
    panel_dir: str = ""
    output_log: str = "/tmp/dokita-output.txt"
    hermes_bin: str = ""

    # ── VCS ──
    repo: str = ""
    default_branch: str = "master"
    vcs_backend: str = "github"
    vcs_token_env: str = "GH_TOKEN"

    # ── Auth ──
    api_key: str = ""

    # ── Feature ──
    panel_feature: str = ""

    # ── Commands (from AGENTS.md detection) ──
    test_cmd: str = "npm test"
    build_cmd: str = "npm run build"
    lint_cmd: str = "npm run lint"

    # ── Model fallback ──
    fallback_models: dict = field(default_factory=dict)

    # ── Feature flags ──
    skip_autofix: bool = False
    force_full: bool = False
    skip_human_gate: bool = False
    max_parallel_override: int | None = None
    resume: bool | None = None

    def __post_init__(self) -> None:
        """Validate project_dir exists if set."""
        if self.project_dir and not os.path.isdir(self.project_dir):
            raise ValueError(
                f"Project directory does not exist: {self.project_dir}"
            )
