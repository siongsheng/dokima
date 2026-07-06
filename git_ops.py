"""Git and GitHub wrapper functions extracted from utils.py (F041).

Contains git(), gh(), detect_repo(), load_key(), load_github_token(),
_safe_run(), detect_commands(), _detect_referenced_repo(),
_detect_default_branch(), _set_vcs_token(), _set_gh_token(),
_load_token_from_env_file(), try_auto_merge(), _supplement_pr_sections().
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
        _u._GH_TOKEN_CACHE = load_github_token()
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


def load_key():
    """Load API_SERVER_KEY from profiles/work/.env."""
    import utils as _u

    # Allow test patching via dokima.load_key override (F022b)
    dokima_mod = _u._IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'load_key', None)
        if override is not None and override is not load_key:
            return override()
    env_path = os.path.join(_u.PROFILES, "work", ".env")
    if not os.path.exists(env_path):
        return ""
    key_prefix = 'API_SERVER_KEY' + '='
    with open(env_path) as f:
        for line in f:
            if line.startswith(key_prefix):
                return line.strip().split("=", 1)[1]
    return ""


def load_github_token():
    """Load GH_TOKEN from profiles/work/.env."""
    import utils as _u

    # Allow test patching via dokima.load_github_token override (F022b)
    dokima_mod = _u._IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'load_github_token', None)
        if override is not None and override is not load_github_token:
            return override()
    env_path = os.path.join(_u.PROFILES, "work", ".env")
    if not os.path.exists(env_path):
        return ""
    prefix = 'GH_TOKEN' + '='
    with open(env_path) as f:
        for line in f:
            if line.startswith(prefix) and not line.startswith("#"):
                return line.strip().split("=", 1)[1]
    return ""


def _safe_run(cmd_str: str, cwd: str, timeout: int = 300):
    """Safely run a command string without shell injection.
    Uses shlex.split to parse into argument list.
    Returns a CompletedProcess-like object. On timeout, returns object
    with returncode=124 and timeout error message in stdout."""
    import shlex
    import utils as _u

    # Allow test patching via dokima._safe_run override (F022 modular refactor)
    dokima_mod = _u._IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, '_safe_run', None)
        if override is not None and override is not _safe_run:
            return override(cmd_str, cwd, timeout=timeout)

    import subprocess as _sp
    try:
        args = shlex.split(cmd_str)
        return _sp.run(args, stdout=_sp.PIPE, stderr=_sp.STDOUT,
                       universal_newlines=True, timeout=timeout, cwd=cwd)
    except _sp.TimeoutExpired as e:
        # Return a synthetic CompletedProcess so callers can check returncode
        result = _sp.CompletedProcess(args=shlex.split(cmd_str), returncode=124)
        result.stdout = f"TIMEOUT: {e}"
        result.stderr = ""
        return result
    except Exception as e:
        print(f"  _safe_run: failed for '{cmd_str[:100]}': {e}")
        raise


def detect_commands():
    """Read test/build/lint commands from AGENTS.md in PROJECT_DIR."""
    import utils as _u

    test_cmd = "npm test"
    build_cmd = "npm run build"
    lint_cmd = "npm run lint"
    agents_path = os.path.join(_u.PROJECT_DIR, "AGENTS.md")
    if os.path.exists(agents_path):
        with open(agents_path) as f:
            agent_content = f.read()
            # Primary: backtick-enclosed commands
            test_m = re.search(r'(?:[Uu]nit )?[Tt]est[s]?.*?:\s*`([^`]+)`', agent_content)
            build_m = re.search(r'(?:[Ff]ull )?[Bb]uild.*?:\s*`([^`]+)`', agent_content)
            lint_m = re.search(r'(?:[Ll]int).*?:\s*`([^`]+)`', agent_content)
            # Fallback: fenced code blocks after "Test:" / "Build:" / "Lint:" labels
            if not test_m:
                test_m = re.search(r'(?:[Uu]nit )?[Tt]est[s]?.*?:\s*```\s*(.+?)```', agent_content, re.DOTALL)
            if not build_m:
                build_m = re.search(r'(?:[Ff]ull )?[Bb]uild.*?:\s*```\s*(.+?)```', agent_content, re.DOTALL)
            if not lint_m:
                lint_m = re.search(r'(?:[Ll]int).*?:\s*```\s*(.+?)```', agent_content, re.DOTALL)
            if test_m:
                test_cmd = test_m.group(1).strip()
            if build_m:
                build_cmd = build_m.group(1).strip()
            if lint_m:
                lint_cmd = lint_m.group(1).strip()
    return test_cmd, build_cmd, lint_cmd


def _detect_referenced_repo(agents_path: str) -> str:
    """If this project documents an external system (e.g. dokima-docs documents dokima),
    parse AGENTS.md first line for a GitHub link, check if that repo exists locally,
    and return its AGENTS.md content + key architecture facts. Returns empty string
    if no referenced repo is found or accessible."""
    if not os.path.exists(agents_path):
        return ""
    with open(agents_path) as f:
        # Read first 10 lines — the reference is usually in the opening description
        header = "".join([f.readline() for _ in range(10)])
    # Match "Documentation site for [Name](https://github.com/owner/repo)"
    # or any markdown link with a github.com URL in the header
    gh_matches = list(re.finditer(
        r'https?://github\.com/([^/\s)]+)/([^/\s)]+?)(?:\.git)?(?:\)|[\s/#])',
        header[:3000]))
    if not gh_matches:
        return ""
    ref_context = ""
    for m in gh_matches:
        owner, repo_name = m.group(1), m.group(2)
        repo_name = repo_name.rstrip(')').rstrip('/')
        # Common local paths: ~/<repo>, ~/Projects/<repo>, /home/opc/<repo>
        candidates = [
            os.path.expanduser(f"~/{repo_name}"),
            os.path.expanduser(f"~/Projects/{repo_name}"),
        ]
        found = None
        for cand in candidates:
            if os.path.isdir(cand) and os.path.exists(os.path.join(cand, "AGENTS.md")):
                found = cand
                break
        if not found:
            continue
        try:
            with open(os.path.join(found, "AGENTS.md")) as ref_f:
                ref_agents = ref_f.read()[:4000]
            ref_context += ("\n\nEXTERNAL REFERENCE — This project documents {0}/{1}. "
                            "The REFERENCED SYSTEM lives at {2}. "
                            "Its AGENTS.md (below) is THE TRUTH — verify every claim against it. "
                            "If this reference contradicts what the project being documented says, "
                            "the reference wins.\n\n"
                            "REFERENCED AGENTS.md:\n{3}\n--- END EXTERNAL REFERENCE ---\n"
                            ).format(owner, repo_name, found, ref_agents)
        except Exception as e:
            ref_context += ("\n\nNOTE: Could not read AGENTS.md from {0}: {1}\n").format(found, e)
    return ref_context


def try_auto_merge(pr_url: str) -> str:
    """Try to merge a PR. Returns: 'merged', 'queued', 'failed'."""
    import utils as _u

    if not pr_url:
        return "failed"
    pr_num = pr_url.rstrip("/").split("/")[-1]
    if not pr_num.isdigit():
        print(f"  Cannot parse PR number from: {pr_url}")
        return "failed"
    if not _u.REPO:
        print("  REPO not configured, cannot merge")
        return "failed"
    try:
        merge_stdout, merge_stderr, merge_rc = gh("pr", "merge", pr_num, "--repo", _u.REPO,
                            "--merge", "--delete-branch")
    except Exception as e:
        print(f"  gh merge failed with exception: {e}")
        return "failed"
    if merge_rc == 0:
        print(f"  PR #{pr_num} merged")
        return "merged"
    merge_err_lower = (merge_stderr or "").lower()
    if any(kw in merge_err_lower for kw in
           ("required status", "required check", "status check", "required")):
        print(f"  PR #{pr_num} - branch protection requires CI. Queuing auto-merge...")
        try:
            _, queue_stderr, queue_rc = gh("pr", "merge", pr_num, "--repo", _u.REPO,
                              "--auto", "--delete-branch")
        except Exception:
            print(f"  Auto-merge queue exception")
            return "failed"
        if queue_rc == 0:
            print(f"  PR #{pr_num} auto-merge queued")
            return "queued"
        print(f"  Auto-merge queue failed: {queue_stderr[:200]}")
        return "failed"
    print(f"  PR #{pr_num} merge failed: {(merge_stderr or 'unknown')[:200]}")
    return "failed"


def _supplement_pr_sections(pr_sections, project_dir, branch, default_branch):
    """Supplement thin PR sections with git diff summary. Returns enriched pr_sections string."""
    result = pr_sections
    if "## Impact" not in pr_sections or "## What Changed" not in pr_sections:
        try:
            diff_stat = subprocess.run(
                ["git", "-C", project_dir, "diff", "--stat", f"{default_branch}...{branch}"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                universal_newlines=True, timeout=15)
            diff_summary = diff_stat.stdout.strip()
            if diff_summary:
                if "## Impact" not in pr_sections:
                    result += f"\n\n## Impact\n\nMinimal — see What Changed."
                if "## What Changed" not in pr_sections:
                    result += f"\n\n## What Changed\n\n```\n{diff_summary}\n```"
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"  ⚠ _supplement_pr_sections: git diff failed ({e}) — proceeding without supplement", flush=True)
    return result


def _set_vcs_token():
    """Load the appropriate VCS token based on VCS_BACKEND and export to environment.

    For GitHub: loads GH_TOKEN. For GitLab: loads GITLAB_TOKEN or GLAB_TOKEN.
    """
    # Auto-detect VCS from import if available
    try:
        import vcs
        backend = vcs.VCS_BACKEND
    except ImportError:
        backend = "github"

    if backend == "gitlab":
        # Try GITLAB_TOKEN first, then GLAB_TOKEN
        for env_var in ("GITLAB_TOKEN", "GLAB_TOKEN"):
            from_profiles = _load_token_from_env_file(env_var)
            if from_profiles:
                os.environ[env_var] = from_profiles
                return
        # If neither found in profiles, check if already in env
        if os.environ.get("GITLAB_TOKEN"):
            return
        if os.environ.get("GLAB_TOKEN"):
            return
    else:
        # GitHub (default)
        gh_token = load_github_token()
        if gh_token:
            os.environ["GH_TOKEN"] = gh_token


def _load_token_from_env_file(env_var_name):
    """Load a token from profiles/work/.env by env var name."""
    import utils as _u

    env_path = os.path.join(_u.PROFILES, "work", ".env")
    if not os.path.exists(env_path):
        return ""
    prefix = env_var_name + '='
    with open(env_path) as f:
        for line in f:
            if line.startswith(prefix) and not line.startswith("#"):
                return line.strip().split("=", 1)[1]
    return ""
