"""
VCS Abstraction Layer for dokima.

Auto-detects GitHub vs GitLab from git remote URL and provides
semantic functions for PR/MR operations that dispatch to the
correct CLI (gh or glab).

Module-level state is set once at startup by detect_vcs_backend().
"""
import os
import sys
import re
import subprocess

# ── Module-level state ──────────────────────────────────────────────

VCS_BACKEND = "github"   # "github" | "gitlab"
VCS_TOKEN_ENV = "GH_TOKEN"  # "GH_TOKEN" | "GLAB_TOKEN" | "GITLAB_TOKEN"


# ── Detection ───────────────────────────────────────────────────────

def detect_vcs_backend(project_dir):
    """Detect VCS backend and repo slug from git remote origin.

    Returns "github" or "gitlab", or None for unknown/error.
    Sets module-level VCS_BACKEND, VCS_TOKEN_ENV, and REPO.
    """
    global VCS_BACKEND, VCS_TOKEN_ENV

    try:
        result = subprocess.run(
            ["git", "-C", project_dir, "remote", "get-url", "origin"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=10
        )
    except Exception:
        print("WARNING: Could not detect VCS from git remote. Some VCS commands may fail.")
        return None

    if result.returncode != 0:
        print("WARNING: Could not detect VCS from git remote. Some VCS commands may fail.")
        return None

    url = result.stdout.strip()

    # GitHub: github.com[:/]owner/repo(.git)?
    m = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$', url)
    if m:
        VCS_BACKEND = "github"
        VCS_TOKEN_ENV = "GH_TOKEN"
        return "github"

    # GitLab: gitlab.*[:/]namespace/project(.git)?
    # Supports subgroups: group/subgroup/project
    m = re.search(r'gitlab\.[^:/]+[:/](.+?)(?:\.git)?$', url)
    if m:
        VCS_BACKEND = "gitlab"
        # Use GITLAB_TOKEN first, fall back to GLAB_TOKEN
        if os.environ.get("GITLAB_TOKEN"):
            VCS_TOKEN_ENV = "GITLAB_TOKEN"
        else:
            VCS_TOKEN_ENV = "GLAB_TOKEN"
        return "gitlab"

    print("WARNING: Unsupported VCS — only GitHub and GitLab are supported. "
          "Some VCS commands may fail.")
    return None


def parse_vcs_flag():
    """Parse --vcs flag from sys.argv. Returns 'github', 'gitlab', or None."""
    args = sys.argv[1:]  # skip script name
    for i, arg in enumerate(args):
        if arg == "--vcs" and i + 1 < len(args):
            val = args[i + 1]
            if val in ("github", "gitlab"):
                return val
    return None


# ── Internal helper ─────────────────────────────────────────────────

def _run_vcs(cli, *args):
    """Run a VCS CLI command with the right token env.

    Returns (stdout, stderr, returncode).
    """
    cmd = [cli] + list(args)
    env = os.environ.copy()
    token = env.get(VCS_TOKEN_ENV, "")
    if token:
        env[VCS_TOKEN_ENV] = token
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=30, env=env
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", f"TIMEOUT: {' '.join(cmd)}", 124
    except FileNotFoundError:
        return "", f"{cli} not found. Please install {cli} CLI.", 1


# ── PR/MR Operations ────────────────────────────────────────────────

def vcs_pr_create(base, head, title, body):
    """Create a PR (GitHub) or MR (GitLab).

    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        return _run_vcs("glab", "mr", "create",
                        "--target-branch", base,
                        "--source-branch", head,
                        "--title", title,
                        "--description", body)
    else:
        return _run_vcs("gh", "pr", "create",
                        "--base", base,
                        "--head", head,
                        "--title", title,
                        "--body", body)


def vcs_pr_merge(pr_num, auto=False):
    """Merge a PR (GitHub) or MR (GitLab).

    If auto=True, uses --auto (gh) or --when-pipeline-succeeds (glab).
    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        args = ["glab", "mr", "merge", str(pr_num)]
        if auto:
            args.append("--when-pipeline-succeeds")
        return _run_vcs(*args)
    else:
        args = ["gh", "pr", "merge", str(pr_num), "--merge"]
        if auto:
            args.append("--auto")
        return _run_vcs(*args)


def vcs_pr_view(pr_num, fields="state,merged"):
    """View PR/MR details as JSON.

    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        return _run_vcs("glab", "mr", "view", str(pr_num))
    else:
        return _run_vcs("gh", "pr", "view", str(pr_num), "--json", fields)


def vcs_pr_list(state="open", head=None, json_fields="url,number"):
    """List PRs/MRs.

    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        args = ["glab", "mr", "list", "--state", state, "--output", "json"]
        if head:
            args.extend(["--source-branch", head])
        return _run_vcs(*args)
    else:
        args = ["gh", "pr", "list", "--state", state, "--json", json_fields]
        if head:
            args.extend(["--head", head])
        return _run_vcs(*args)


def vcs_pr_diff(pr_num, stat_only=False):
    """Get PR/MR diff.

    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        # glab does not have --stat; for stat_only we can post-process
        # or use mr diff and count lines
        return _run_vcs("glab", "mr", "diff", str(pr_num))
    else:
        args = ["gh", "pr", "diff", str(pr_num)]
        if stat_only:
            args.append("--stat")
        return _run_vcs(*args)


# ── Issue Operations ────────────────────────────────────────────────

def vcs_issue_create(title, body, labels=None):
    """Create an issue.

    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        args = ["glab", "issue", "create", "--title", title, "--description", body]
        if labels:
            args.extend(["--label", labels])
        return _run_vcs(*args)
    else:
        args = ["gh", "issue", "create", "--title", title, "--body", body]
        if labels:
            args.extend(["--label", labels])
        return _run_vcs(*args)


def vcs_issue_view(issue_num, fields="body,title"):
    """View issue details as JSON.

    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        return _run_vcs("glab", "issue", "view", str(issue_num))
    else:
        return _run_vcs("gh", "issue", "view", str(issue_num), "--json", fields)


# ── Release Operations ──────────────────────────────────────────────

def vcs_release_create(tag, title, target, generate_notes=True):
    """Create a release — GitHub only.

    On GitLab, returns error since release workflow is GitHub-only.
    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        return "", "Error: Release workflow is GitHub-only. GitLab releases are not yet supported.", 1
    else:
        args = ["gh", "release", "create", tag, "--title", title, "--target", target]
        if generate_notes:
            args.append("--generate-notes")
        return _run_vcs(*args)


def vcs_pr_update_body(pr_num, new_body, repo=""):
    """Update the body/description of a PR (GitHub) or MR (GitLab).

    Args:
        pr_num: PR/MR number as int or str.
        new_body: New body text (markdown).

    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        return _run_vcs("glab", "mr", "update", str(pr_num),
                        "--description", new_body)
    else:
        return _run_vcs("gh", "api",
                        f"repos/{repo}/pulls/{pr_num}",
                        "--method", "PATCH",
                        "-f", f"body={new_body}")


# ── Repo Operations ─────────────────────────────────────────────────

def vcs_repo_clone(repo_slug, target_dir):
    """Clone a repository using the VCS CLI.

    Returns (stdout, stderr, returncode).
    """
    if VCS_BACKEND == "gitlab":
        return _run_vcs("glab", "repo", "clone", repo_slug, target_dir)
    else:
        return _run_vcs("gh", "repo", "clone", repo_slug, target_dir)
