"""Dokima VCS operations — git/GitHub wrappers, token management, release automation.

All functions extracted from dokima monolith utils.py (F041: Split utils.py into domain modules).
"""

import sys, json, subprocess, os, pwd, time, shlex, re, datetime, tempfile

# ── Module-level globals (moved from utils.py) ──────
# Set by main() in the dokima entry script and synced via conftest.
_IMPORTING_PANEL = None
PROFILES = ""
_GH_TOKEN_CACHE = None


def load_key():
    # Allow test patching via dokima.load_key override (F022b)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'load_key', None)
        if override is not None and override is not load_key:
            return override()
    env_path = os.path.join(PROFILES, "work", ".env")
    if not os.path.exists(env_path):
        return ""
    key_prefix = 'API_SERVER_KEY' + '='
    with open(env_path) as f:
        for line in f:
            if line.startswith(key_prefix):
                return line.strip().split("=", 1)[1]
    return ""



def load_github_token():
    # Allow test patching via dokima.load_github_token override (F022b)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'load_github_token', None)
        if override is not None and override is not load_github_token:
            return override()
    env_path = os.path.join(PROFILES, "work", ".env")
    if not os.path.exists(env_path):
        return ""
    prefix = 'GH_TOKEN' + '='
    with open(env_path) as f:
        for line in f:
            if line.startswith(prefix) and not line.startswith("#"):
                return line.strip().split("=", 1)[1]
    return ""



def git(*args, **kwargs):
    """Run git in PROJECT_DIR. Returns (stdout, stderr, returncode)."""
    # Allow test patching via dokima.git override (F022 modular refactor)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'git', None)
        if override is not None and override is not git:
            return override(*args, **kwargs)

    result = subprocess.run(["git", "-C", PROJECT_DIR] + list(args),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
    return result.stdout.strip(), result.stderr.strip(), result.returncode



def gh(*args, **kwargs):
    """Run gh CLI with GH_TOKEN. Returns (stdout, stderr, returncode)."""
    # Allow test patching via dokima.gh override (F022 modular refactor)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'gh', None)
        if override is not None and override is not gh:
            return override(*args, **kwargs)

    global _GH_TOKEN_CACHE
    env = os.environ.copy()
    if _GH_TOKEN_CACHE is None:
        _GH_TOKEN_CACHE = load_github_token()
    if _GH_TOKEN_CACHE:
        env["GH_TOKEN"] = _GH_TOKEN_CACHE
    result = subprocess.run(["gh"] + list(args),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode



def _safe_run(cmd_str: str, cwd: str, timeout: int = 300):
    """Safely run a command string without shell injection.
    Uses shlex.split to parse into argument list.
    Returns a CompletedProcess-like object. On timeout, returns object
    with returncode=124 and timeout error message in stdout."""
    # Allow test patching via dokima._safe_run override (F022 modular refactor)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, '_safe_run', None)
        if override is not None and override is not _safe_run:
            # Patched in tests — call the mock with the same signature
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



def detect_repo():
    """Extract owner/repo from git remote origin. Supports GitHub and GitLab."""
    # Allow test patching via dokima.detect_repo override (F022b)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'detect_repo', None)
        if override is not None and override is not detect_repo:
            return override()
    result = subprocess.run(["git", "-C", PROJECT_DIR, "remote", "get-url", "origin"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
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



def detect_commands():
    """Read test/build/lint commands from AGENTS.md in PROJECT_DIR."""
    test_cmd = "npm test"
    build_cmd = "npm run build"
    lint_cmd = "npm run lint"
    agents_path = os.path.join(PROJECT_DIR, "AGENTS.md")
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
        owner, repo = m.group(1), m.group(2)
        repo_name = repo.rstrip(')').rstrip('/')
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
    if not pr_url:
        return "failed"
    pr_num = pr_url.rstrip("/").split("/")[-1]
    if not pr_num.isdigit():
        print(f"  Cannot parse PR number from: {pr_url}")
        return "failed"
    if not REPO:
        print("  REPO not configured, cannot merge")
        return "failed"
    try:
        merge_stdout, merge_stderr, merge_rc = gh("pr", "merge", pr_num, "--repo", REPO,
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
            _, queue_stderr, queue_rc = gh("pr", "merge", pr_num, "--repo", REPO,
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



def _detect_default_branch(project_dir):
    """Detect default branch from origin/HEAD. Returns branch name string."""
    try:
        result = subprocess.run(
            ["git", "-C", project_dir, "symbolic-ref", "refs/remotes/origin/HEAD"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            universal_newlines=True, timeout=10)
        if result.returncode == 0:
            ref = result.stdout.strip()
            return ref.split("/")[-1] if "/" in ref else "master"
    except Exception:
        pass
    return "master"



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
    env_path = os.path.join(PROFILES, "work", ".env")
    if not os.path.exists(env_path):
        return ""
    prefix = env_var_name + '='
    with open(env_path) as f:
        for line in f:
            if line.startswith(prefix) and not line.startswith("#"):
                return line.strip().split("=", 1)[1]
    return ""




def _set_gh_token():
    """Backward-compatible alias for _set_vcs_token()."""
    _set_vcs_token()



def halt_and_revert(reason, phase, branch, task_ids=None, worktrees=None):
    """Revert all changes and print failure summary for orchestrator.

    Args:
        reason: Why the pipeline halted.
        phase: Which phase failed (e.g., 'PHASE 2 (Parallel Coders)').
        branch: The main feature branch to delete.
        task_ids: Optional list of task IDs. When provided, deletes task
                  branches (feat/<slug>-tN) before the main branch.
        worktrees: Optional WorktreeManager reference. When provided,
                   calls cleanup_all() to remove worktree directories.
    """
    # Allow test patching via dokima.halt_and_revert override (F022 modular refactor)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'halt_and_revert', None)
        if override is not None and override is not halt_and_revert:
            return override(reason, phase, branch, task_ids=task_ids, worktrees=worktrees)

    print(f"\n{'═'*55}", flush=True)
    print(f"  PIPELINE HALTED — {phase} Failed", flush=True)
    print(f"{'═'*55}", flush=True)
    print(f"\nReason: {reason}", flush=True)
    print("\nReverting all changes...", flush=True)

    # Delete task branches first (feat/<slug>-tN)
    if task_ids:
        for tid in task_ids:
            task_branch = f"{branch}-t{tid}"
            try:
                git("branch", "-D", task_branch)
            except Exception:
                pass  # Branch might not exist if created before worktree

    git("checkout", DEFAULT_BRANCH)
    git("branch", "-D", branch)
    git("stash", "clear")
    print(f"  Branch '{branch}' deleted, back on master", flush=True)

    # Clean up worktree directories if manager provided
    if worktrees and task_ids:
        try:
            worktrees.cleanup_all(task_ids)
        except Exception:
            pass

    print("\n── Orchestrator Action Required ──", flush=True)
    print(f"  1. Review the failure context above", flush=True)
    print(f"  2. Diagnose root cause", flush=True)
    print(f"  3. Fix the issue (code, config, prompt, etc.)", flush=True)
    print(f"  4. Ask user for go-ahead before retrying", flush=True)
    print(f"\nFull log: {OUTPUT_LOG}", flush=True)




def _bump_version(current, bump):
    """Bump a semver string (X.Y.Z) by patch/minor/major.
    Returns the new version string. Raises ValueError on invalid input."""
    if bump not in ("patch", "minor", "major"):
        raise ValueError(f"Invalid bump type: {bump!r} (expected patch, minor, or major)")
    try:
        parts = [int(x) for x in current.split(".")]
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid version string: {current!r}")
    if len(parts) != 3:
        raise ValueError(f"Invalid version string: {current!r} (expected X.Y.Z)")

    x, y, z = parts
    if bump == "patch":
        z += 1
    elif bump == "minor":
        y += 1
        z = 0
    elif bump == "major":
        x += 1
        y = 0
        z = 0
    return f"{x}.{y}.{z}"




def _prune_old_tags(keep_count=10):
    """Prune old vX.Y.Z tags beyond keep_count from origin.
    Keeps the newest keep_count release tags, deletes the rest via
    git push origin --delete. Non-vX.Y.Z tags are ignored.
    Warns for each deleted tag. Silent no-op if ≤keep_count tags."""
    stdout, stderr, rc = git("tag", "--sort=-v:refname")
    if rc != 0 or not stdout.strip():
        return

    # Filter to vX.Y.Z tags only (already sorted newest-first)
    semver_pattern = re.compile(r'^v\d+\.\d+\.\d+$')
    version_tags = [t.strip() for t in stdout.split("\n") if semver_pattern.match(t.strip())]

    # Keep the first keep_count, delete the rest
    if len(version_tags) <= keep_count:
        return

    to_delete = version_tags[keep_count:]
    for tag in to_delete:
        print(f"  Pruning old tag: {tag}", flush=True)
        _, stderr, rc = git("push", "origin", "--delete", tag)
        if rc != 0:
            print(f"  ⚠ Failed to delete tag {tag}: {stderr}", flush=True)
            # Continue with remaining tags even if one fails




def _update_docs_cache(new_version):
    """Clone dokima-docs repo, regenerate cli-help.json, commit, and push.

    Non-blocking: warns on failure but never raises. Does nothing if
    gh CLI is not available or the docs repo cannot be reached.

    Args:
        new_version: The new version string (e.g. '1.2.5').
    """
    import tempfile, shutil, subprocess as _sp

    # Determine the dokima script path (same directory as utils.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dokima_path = os.path.join(script_dir, "dokima")

    clone_dir = None
    try:
        # a. Clone dokima-docs shallow
        print("  Updating docs cache...", flush=True)
        clone_dir = tempfile.mkdtemp(prefix="dokima-docs-")
        result = _sp.run(
            ["gh", "repo", "clone", "siongsheng/dokima-docs", clone_dir,
             "--", "--depth=1"],
            stdout=_sp.PIPE, stderr=_sp.PIPE, universal_newlines=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  WARNING: Could not clone dokima-docs: {result.stderr.strip()}", flush=True)
            return

        # b. Generate cli-help.json
        output_path = os.path.join(clone_dir, "scripts", "cli-help.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result = _sp.run(
            [sys.executable, dokima_path, "--help-json"],
            stdout=_sp.PIPE, stderr=_sp.PIPE, universal_newlines=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  WARNING: dokima --help-json failed: {result.stderr.strip()}", flush=True)
            return

        with open(output_path, "w") as f:
            f.write(result.stdout)

        # c. git add
        _sp.run(
            ["git", "-C", clone_dir, "add", "scripts/cli-help.json"],
            stdout=_sp.PIPE, stderr=_sp.PIPE, timeout=30
        )

        # d. git commit
        result = _sp.run(
            ["git", "-C", clone_dir, "commit", "-m",
             f"chore: update CLI reference for v{new_version}"],
            stdout=_sp.PIPE, stderr=_sp.PIPE, universal_newlines=True, timeout=30
        )
        if result.returncode != 0:
            if "nothing to commit" in (result.stdout + result.stderr):
                return  # No changes — OK
            print(f"  WARNING: Docs commit failed: {result.stderr.strip()}", flush=True)
            return

        # e. git push
        result = _sp.run(
            ["git", "-C", clone_dir, "push"],
            stdout=_sp.PIPE, stderr=_sp.PIPE, universal_newlines=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  WARNING: Docs push failed: {result.stderr.strip()}", flush=True)
            # Non-blocking: release still succeeds
        else:
            print("  \u2713 Updated CLI reference cache for dokima-docs", flush=True)

    except FileNotFoundError:
        # gh CLI not installed or not found
        print("  WARNING: gh CLI not found, skipping docs cache update", flush=True)
    except Exception as e:
        print(f"  WARNING: Docs cache update failed: {e}", flush=True)
    finally:
        if clone_dir is not None:
            shutil.rmtree(clone_dir, ignore_errors=True)




def do_release(bump, project_dir, dry_run=False):
    """Bump version, tag, generate changelog, and publish GitHub Release.

    Args:
        bump: 'patch', 'minor', or 'major'
        project_dir: Path to the git repository
        dry_run: If True, print the plan and exit without making changes

    Exits with code 1 on any precondition failure.
    """
    import shutil, tempfile

    # 1. Validate bump type
    if bump not in ("patch", "minor", "major"):
        print(f"ERROR: Invalid bump type: {bump!r} (expected patch, minor, or major)", flush=True)
        sys.exit(1)

    # 2. Validate project_dir is a git repo
    if not _validate_project_dir(project_dir):
        print(f"ERROR: {project_dir} is not a valid git repository", flush=True)
        sys.exit(1)

    # 3. Detect default branch
    default_branch = _detect_default_branch(project_dir)

    # 4. Check we're on the default branch
    stdout, _, rc = git("-C", project_dir, "rev-parse", "--abbrev-ref", "HEAD")
    current_branch = stdout.strip() if rc == 0 else ""
    if current_branch != default_branch:
        print(f"ERROR: Must be on {default_branch} branch to release (currently on {current_branch or 'detached HEAD'})", flush=True)
        sys.exit(1)

    # 5. Validate clean working tree
    _, _, rc = git("-C", project_dir, "diff-index", "--quiet", "HEAD", "--")
    if rc != 0:
        print("ERROR: Working tree is not clean. Commit or stash changes before releasing.", flush=True)
        # Show git status for context
        stdout, _, _ = git("-C", project_dir, "status", "--short")
        if stdout:
            print(stdout)
        sys.exit(1)

    # 6. Validate up to date with origin
    print("  Fetching origin...", flush=True)
    _, _, rc = git("-C", project_dir, "fetch", "origin")
    if rc != 0:
        print("ERROR: Could not reach origin", flush=True)
        sys.exit(1)

    behind, _, rc = git("-C", project_dir, "rev-list", f"HEAD..origin/{default_branch}", "--count")
    if rc == 0 and behind.strip() and behind.strip() != "0":
        count = behind.strip()
        print(f"ERROR: Behind origin/{default_branch} by {count} commit(s). Pull latest changes first.", flush=True)
        sys.exit(1)

    # 7. Read current VERSION and compute new version
    version_path = os.path.join(project_dir, "VERSION")
    if not os.path.exists(version_path):
        print(f"ERROR: VERSION file not found at {version_path}", flush=True)
        sys.exit(1)

    with open(version_path) as f:
        current_version = f.read().strip()
    if not current_version:
        print("ERROR: VERSION file is empty", flush=True)
        sys.exit(1)

    try:
        new_version = _bump_version(current_version, bump)
    except ValueError as e:
        print(f"ERROR: {e}", flush=True)
        sys.exit(1)

    tag_name = f"v{new_version}"

    # 8. Dry run: print plan and exit
    if dry_run:
        print(f"  [DRY RUN] Would bump: {current_version} → {new_version} ({bump})")
        print(f"  [DRY RUN] Would commit: chore: bump version to {tag_name}")
        print(f"  [DRY RUN] Would tag: {tag_name}")
        print(f"  [DRY RUN] Would push to origin/{default_branch}")
        print(f"  [DRY RUN] Would create GitHub Release: {tag_name}")
        print(f"  [DRY RUN] Command: gh release create {tag_name} --generate-notes --title \"{tag_name}\" --target {default_branch}")
        print(f"  [DRY RUN] Would update docs cache")
        return

    # 9. Write new VERSION atomically (temp + rename)
    print(f"  Bumping version: {current_version} → {new_version} ({bump})", flush=True)
    fd, tmp_path = tempfile.mkstemp(dir=project_dir, prefix=".VERSION.")
    try:
        os.write(fd, f"{new_version}\n".encode())
        os.close(fd)
        os.replace(tmp_path, version_path)
    except Exception:
        os.close(fd)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    # 10. git add VERSION
    git("-C", project_dir, "add", "VERSION")

    # 11. git commit
    commit_msg = f"chore: bump version to {tag_name}"
    stdout, stderr, rc = git("-C", project_dir, "commit", "-m", commit_msg)
    if rc != 0:
        print(f"ERROR: Commit failed: {stderr}", flush=True)
        sys.exit(1)

    # 12. git tag
    stdout, stderr, rc = git("-C", project_dir, "tag", "-a", tag_name, "-m", f"Release {tag_name}")
    if rc != 0:
        if "already exists" in (stdout + stderr):
            print(f"ERROR: Tag {tag_name} already exists", flush=True)
        else:
            print(f"ERROR: Tag creation failed: {stderr}", flush=True)
        sys.exit(1)

    # 13. Prune old tags
    _prune_old_tags()

    # 14. Push branch
    print(f"  Pushing to origin/{default_branch}...", flush=True)
    stdout, stderr, rc = git("-C", project_dir, "push", "origin", default_branch)
    if rc != 0:
        print(f"ERROR: Push failed: {stderr}", flush=True)
        sys.exit(1)

    # 15. Push tag
    print(f"  Pushing tag {tag_name}...", flush=True)
    stdout, stderr, rc = git("-C", project_dir, "push", "origin", tag_name)
    if rc != 0:
        print(f"ERROR: Tag push failed: {stderr}", flush=True)
        sys.exit(1)

    # 16. Create GitHub Release
    print(f"  Creating GitHub Release {tag_name}...", flush=True)
    stdout, stderr, rc = gh(
        "release", "create", tag_name,
        "--generate-notes",
        "--title", tag_name,
        "--target", default_branch
    )
    if rc != 0:
        print(f"ERROR: GitHub Release creation failed: {stderr}", flush=True)
        sys.exit(1)

    # 17. Update docs cache (non-blocking)
    _update_docs_cache(new_version)

    # 18. Print summary
    print(f"\n  ✓ Released dokima {tag_name}")
    if stdout:
        # gh release create outputs the release URL
        for line in stdout.split("\n"):
            if line.startswith("https://"):
                print(f"  Release: {line}")
                break



