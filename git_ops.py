"""Git and GitHub wrapper functions extracted from utils.py (F041).

Contains git(), gh(), detect_repo(), _set_gh_token(), _detect_default_branch().
Uses lazy imports from utils to avoid circular dependencies.
"""

import os
import re
import subprocess


def git(*args, **kwargs):
    """Run git in PROJECT_DIR. Returns (stdout, stderr, returncode)."""
    import utils as _u

    # Allow test patching via dokima.git override (F022 modular refactor)
    dokima_mod = _u._IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'git', None)
        if override is not None and override is not git:
            return override(*args, **kwargs)

    result = subprocess.run(
        ["git", "-C", _u.PROJECT_DIR] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=30,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def gh(*args, **kwargs):
    """Run gh CLI with GH_TOKEN. Returns (stdout, stderr, returncode)."""
    import utils as _u

    # Allow test patching via dokima.gh override (F022 modular refactor)
    dokima_mod = _u._IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'gh', None)
        if override is not None and override is not gh:
            return override(*args, **kwargs)

    env = os.environ.copy()
    if _u._GH_TOKEN_CACHE is None:
        _u._GH_TOKEN_CACHE = _u.load_github_token()
    if _u._GH_TOKEN_CACHE:
        env["GH_TOKEN"] = _u._GH_TOKEN_CACHE
    result = subprocess.run(
        ["gh"] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=30,
        env=env,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def detect_repo():
    """Extract owner/repo from git remote origin. Supports GitHub and GitLab."""
    import utils as _u

    # Allow test patching via dokima.detect_repo override (F022b)
    dokima_mod = _u._IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'detect_repo', None)
        if override is not None and override is not detect_repo:
            return override()
    result = subprocess.run(
        ["git", "-C", _u.PROJECT_DIR, "remote", "get-url", "origin"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=10,
    )
    if result.returncode == 0:
        url = result.stdout.strip()
        # GitHub: github.com[:/]owner/repo(.git)?
        m = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$', url)
        if m:
            return m.group(1)
        # GitLab: gitlab.*[:/]namespace/project(.git)?
        # Supports subgroups: group/subgroup/project
        m = re.search(r'gitlab\.[^:/]+[:/](.+?)(?:\.git)?$', url)
        if m:
            return m.group(1)
    print("WARNING: Could not detect repo from git remote. Some VCS commands may fail.")
    return None


def _detect_default_branch(project_dir):
    """Detect default branch from origin/HEAD. Returns branch name string."""
    try:
        result = subprocess.run(
            ["git", "-C", project_dir, "symbolic-ref", "refs/remotes/origin/HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=10,
        )
        if result.returncode == 0:
            ref = result.stdout.strip()
            return ref.split("/")[-1] if "/" in ref else "master"
    except Exception:
        pass
    return "master"


def _set_gh_token():
    """Backward-compatible alias for _set_vcs_token()."""
    import utils as _u

    _u._set_vcs_token()
