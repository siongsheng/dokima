"""PipelineContext dataclass — single source of truth for all pipeline configuration.

Replaces 20+ module-level globals spread across utils.py, vcs.py, and pipeline.py
(F040). Constructed once at startup, passed explicitly to every phase function.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
import os
import pwd


@dataclass
class PipelineContext:
    """Single source of truth for all pipeline configuration and runtime state."""

    # ── Required (set at construction) ──
    project_dir: str
    repo: str = ""

    # ── Auto-detected (defaults from env, can be overridden) ──
    default_branch: str = "master"
    panel_feature: str = ""
    api_key: str = ""
    output_log: str = "/tmp/dokima-output.txt"

    # ── Derived from filesystem (computed in __post_init__) ──
    real_home: str = ""
    hermes_bin: str = ""
    profiles_dir: str = ""
    panel_dir: str = ""

    # ── Commands (detected from AGENTS.md) ──
    test_cmd: str = "npm test"
    build_cmd: str = "npm run build"
    lint_cmd: str = "npm run lint"

    # ── Feature flags ──
    skip_autofix: bool = False
    force_full: bool = False
    skip_human_gate: bool = False
    max_parallel_override: Optional[int] = None
    resume: Optional[bool] = None

    # ── Model configuration ──
    fallback_models: Dict[str, str] = field(default_factory=dict)
    panel_port: Dict[str, int] = field(default_factory=lambda: {
        "strategist": 8647, "tech-lead": 8644, "coder": 8645, "nm": 8648
    })

    # ── Transient (set during pipeline execution, NOT at construction) ──
    max_continuous: int = 20

    def __post_init__(self):
        """Compute derived paths from real_home."""
        # Compute real_home from pwd if not set
        if not self.real_home:
            try:
                self.real_home = pwd.getpwuid(os.getuid()).pw_dir
            except (KeyError, OSError):
                self.real_home = os.path.expanduser("~")

        hermes_root = os.path.join(self.real_home, ".hermes")
        if not self.hermes_bin:
            self.hermes_bin = os.path.join(hermes_root, "hermes-agent/venv/bin/hermes")
        if not self.profiles_dir:
            self.profiles_dir = os.path.join(hermes_root, "profiles")

    @classmethod
    def from_environ(cls, project_dir: str, **overrides) -> "PipelineContext":
        """Factory: construct from environment variables + overrides."""
        ctx = cls(
            project_dir=project_dir,
            skip_autofix=os.environ.get("PANEL_SKIP_AUTOFIX") == "1",
            force_full=os.environ.get("PANEL_FORCE_FULL") == "1",
            skip_human_gate=os.environ.get("PANEL_SKIP_HUMAN_GATE") == "1",
        )
        mp = os.environ.get("PANEL_MAX_PARALLEL")
        if mp and mp.isdigit():
            ctx.max_parallel_override = int(mp)
        for k, v in overrides.items():
            if hasattr(ctx, k):
                setattr(ctx, k, v)
        return ctx
