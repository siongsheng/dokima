"""Dokima utilities — shared helpers, git/GitHub wrappers, security, spec extraction, checkpointing.

All functions extracted from dokima monolith (F022: Modular Architecture).
Module-level globals are set by main() in the dokima entry script before any function calls.
"""
import sys, json, subprocess, os, pwd, time, shlex, re, fcntl, signal, datetime

# shutil imported dynamically where needed (deploy_profile_skills)

# ── Module-level globals (set by main()) ──────────
# Set by conftest._load_panel() after importing this module.
# Used by override-detection to find the correct panel instance
# without relying on sys.modules (which can be stale from
# other _load_panel() calls in tests — F022b).
_IMPORTING_PANEL = None
PROJECT_DIR = ""
REPO = ""
DEFAULT_BRANCH = "master"
API_KEY = ""
OUTPUT_LOG = "/tmp/dokima-output.txt"
REAL_HOME = pwd.getpwuid(os.getuid()).pw_dir
HERMES = os.path.join(REAL_HOME, ".hermes")
HERMES_BIN = os.path.join(HERMES, "hermes-agent/venv/bin/hermes")
PROFILES = os.path.join(HERMES, "profiles")
PANEL_PORT = {"strategist": 8647, "tech-lead": 8644, "coder": 8645, "nm": 8648}
PANEL_FEATURE = ""
PANEL_DIR = ""
FALLBACK_MODELS = {}
SKIP_AUTOFIX = False
FORCE_FULL = False
SKIP_HUMAN_GATE = False
max_parallel_override = None
RESUME = None
TEST_CMD = "npm test"
BUILD_CMD = "npm run build"
LINT_CMD = "npm run lint"

# Version
_script_dir = os.path.dirname(os.path.abspath(__file__))
_version_path = os.path.join(_script_dir, "VERSION")
try:
    VERSION = open(_version_path).read().strip()
except OSError:
    VERSION = "unknown"

# ── Global state ─────────────────────────────────
_LOG_FILE_HANDLE = None
_LOCK_FD = None
_LOG_FILE = None
_STDOUT_ORIG = None
_GH_TOKEN_CACHE = None
MAX_CONTINUOUS = 20

HELP_TEXT = """Dokima — Multi-Agent Orchestration Engine

BUILD:
  dokima "Feature description" [dir]     Run full pipeline for a feature
  dokima init "description" [dir]        Project discovery & constitution
  dokima add "Feature" [-p P1] [dir]     Add feature to roadmap (auto-priority, auto-deps)

MANAGE:
  dokima next [dir]                      Build next feature from roadmap
  dokima next --continuous [dir]         Full sprint: build + auto-merge + loop
  dokima fix [dir]                       Fix BLOCKED PR: detect blockers, fix, verify
  dokima fix --issue N [dir]             Fix specific GitHub issue N by extracting What/Fix/Verify sections

CONTROL:
  dokima status [dir]                    Show pipeline state
  dokima stop [dir]                      Graceful stop after current feature
  dokima kill [dir]                      Emergency kill (SIGTERM then SIGKILL)
  dokima list-crons                      List all scheduled pipelines
  dokima version                         Print version and exit
  dokima upgrade                         Check for newer version and show upgrade instructions
  dokima release <patch|minor|major> [--dry-run] [dir]  Bump version, tag, changelog, and GitHub Release

MODIFIER FLAGS (apply across subcommands):
  --force-full         Run all 5 phases regardless of depth gating
  --skip-autofix       Disable auto-fix loopback (nm + TL phases)
  --skip-auto-archive  Don't auto-archive merged specs
  --skip-human-gate    Skip Human Gate prompt (for automation)
  --max-parallel=N     Max parallel coder agents (env: PANEL_MAX_PARALLEL, default: 5)
  --base-branch <b>    Override default branch for PR base (default: detected from origin/HEAD)
  --vcs <github|gitlab>  Override VCS backend (auto-detected from git remote by default)
  --interactive        Show human gate (with next)
  --answers <file>     Resume from saved interview state
  --fix-all            Include SHOULD FIX items (with fix)
  --create-blocker-issues  Create GitHub issues from detected blockers (with fix)
  --resume             Resume from last checkpoint (re-runs incomplete phases only)
  --no-resume          Ignore any existing checkpoint and start fresh

  All flags also accept their legacy PANEL_* env var equivalents
  (e.g., PANEL_FORCE_FULL=1). Flags take priority.

  LEGACY: --add, --next, --fix, --status, --stop, --kill, --list-crons,
  --version, --upgrade, --release flags have been replaced by subcommands.

EXAMPLES:
  dokima init "trading dashboard" ~/huat
  dokima add "Dark mode toggle" ~/huat
  dokima next ~/huat
  dokima next --continuous ~/huat
  dokima fix ~/huat
  dokima status ~/huat"""
# KEEP IN SYNC with HELP_TEXT — add any new command/flag/env_var here too
CLI_METADATA = {
    "tool": "dokima",
    "version": VERSION,
    "commands": [
        {"name": "run", "syntax": "dokima \"Feature description\" [dir]", "description": "Run full pipeline for a feature"},
        {"name": "init", "syntax": "dokima init \"description\" [dir]", "description": "Project discovery & constitution"},
        {"name": "add", "syntax": "dokima add \"Feature\" [--priority=P1] [dir]", "description": "Add feature to roadmap (auto-priority, auto-deps)"},
        {"name": "next", "syntax": "dokima next [--continuous] [dir]", "description": "Build next feature from roadmap"},
        {"name": "fix", "syntax": "dokima fix [--issue N] [dir]", "description": "Fix BLOCKED PR or specific GitHub issue N: detect blockers, fix, verify"},
        {"name": "fix-issue", "syntax": "dokima fix --issue N [dir]", "description": "Fix specific GitHub issue N by extracting What/Fix/Verify from issue body"},
        {"name": "status", "syntax": "dokima status [dir]", "description": "Show pipeline state"},
        {"name": "stop", "syntax": "dokima stop [dir]", "description": "Graceful stop after current feature"},
        {"name": "kill", "syntax": "dokima kill [dir]", "description": "Emergency kill (SIGTERM then SIGKILL)"},
        {"name": "list-crons", "syntax": "dokima list-crons", "description": "List all scheduled pipelines"},
        {"name": "version", "syntax": "dokima version", "description": "Print version and exit"},
        {"name": "upgrade", "syntax": "dokima upgrade", "description": "Check for newer version and show upgrade instructions"},
        {"name": "release", "syntax": "dokima release <patch|minor|major> [--dry-run] [project_dir]", "description": "Bump version, generate changelog, tag, and publish GitHub Release"},
    ],
    "flags": [
        {"flag": "--interactive", "args": None, "env_var": None, "description": "Show human gate (with next/continuous)"},
        {"flag": "--answers", "args": "<file>", "env_var": None, "description": "Resume from saved interview state"},
        {"flag": "--fix-all", "args": None, "env_var": "PANEL_FIX_ALL", "description": "Include SHOULD FIX items (with --fix)"},
        {"flag": "--create-blocker-issues", "args": None, "env_var": None, "description": "Create GitHub issues from detected blockers (with fix)"},
        {"flag": "--issue", "args": "N", "env_var": None, "description": "Fix specific GitHub issue N instead of discovering BLOCKED PR (with fix)"},
        {"flag": "--skip-autofix", "args": None, "env_var": "PANEL_SKIP_AUTOFIX", "description": "Disable auto-fix loopback (nm + TL phases)"},
        {"flag": "--force-full", "args": None, "env_var": "PANEL_FORCE_FULL", "description": "Run all 5 phases regardless of depth gating"},
        {"flag": "--skip-auto-archive", "args": None, "env_var": "PANEL_SKIP_AUTO_ARCHIVE", "description": "Don't auto-archive merged specs"},
        {"flag": "--skip-human-gate", "args": None, "env_var": "PANEL_SKIP_HUMAN_GATE", "description": "Skip Human Gate prompt (for automation)"},
        {"flag": "--resume", "args": None, "env_var": "PANEL_RESUME", "description": "Resume from last checkpoint (re-runs incomplete phases only)"},
        {"flag": "--no-resume", "args": None, "env_var": "PANEL_NO_RESUME", "description": "Ignore any existing checkpoint and start fresh"},
        {"flag": "--max-parallel", "args": "N", "env_var": "PANEL_MAX_PARALLEL", "description": "Max parallel coder agents (default: 5)"},
        {"flag": "--base-branch", "args": "<b>", "env_var": "PANEL_BASE_BRANCH", "description": "Override default branch for PR base"},
        {"flag": "--vcs", "args": "<github|gitlab>", "env_var": "PANEL_VCS", "description": "Override VCS backend (auto-detected from git remote)"},
    ],
    "env_vars": [
        {"name": "PANEL_FIX_ALL", "description": "Include SHOULD FIX items", "related_flag": "--fix-all"},
        {"name": "PANEL_SKIP_AUTOFIX", "description": "Disable auto-fix loopback", "related_flag": "--skip-autofix"},
        {"name": "PANEL_FORCE_FULL", "description": "Run all 5 phases regardless of depth gating", "related_flag": "--force-full"},
        {"name": "PANEL_SKIP_AUTO_ARCHIVE", "description": "Don't auto-archive merged specs", "related_flag": "--skip-auto-archive"},
        {"name": "PANEL_SKIP_HUMAN_GATE", "description": "Skip Human Gate prompt", "related_flag": "--skip-human-gate"},
        {"name": "PANEL_RESUME", "description": "Resume from last checkpoint", "related_flag": "--resume"},
        {"name": "PANEL_NO_RESUME", "description": "Ignore existing checkpoint and start fresh", "related_flag": "--no-resume"},
        {"name": "PANEL_MAX_PARALLEL", "description": "Max parallel coder agents", "related_flag": "--max-parallel"},
        {"name": "PANEL_BASE_BRANCH", "description": "Override default branch for PR base", "related_flag": "--base-branch"},
        {"name": "PANEL_FALLBACK_STRATEGIST", "description": "Fallback model for strategist role", "related_flag": None},
        {"name": "PANEL_FALLBACK_CODER", "description": "Fallback model for coder role", "related_flag": None},
        {"name": "PANEL_FALLBACK_TECH_LEAD", "description": "Fallback model for tech-lead role", "related_flag": None},
    ],
}


def _sanitize_prompt(text):
    """Strip known injection patterns from user-supplied text before it enters agent prompts.
    Strips backtick-escaped shell commands, markdown code blocks with dangerous commands,
    and SYSTEM:/OVERRIDE: prefix injection attempts. Logs a warning on any strip."""
    if not text:
        return text
    original = text
    # Strip SYSTEM: / OVERRIDE: prefix injection (case-insensitive, word-boundary)
    text = re.sub(r'\b(?:SYSTEM|OVERRIDE)\s*:\s*', '', text, count=0, flags=re.IGNORECASE)
    # Strip backtick content that looks like a shell command (has spaces, pipes,
    # redirects, or starts with $ for expansion). Single-word inline code like
    # `--help-json` or `config.yaml` is legitimate Markdown — don't strip it.
    SHELL_PATTERN = r'[\s|&;<>$]'
    text = re.sub(r'`[^`]*' + SHELL_PATTERN + r'[^`]*`', '', text)
    # Strip markdown code blocks (```cmd``` or ```\ncmd\n```) containing dangerous patterns
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text).strip()
    if text != original:
        stripped = original[:80].strip()
        print(f"  WARNING: Sanitized prompt injection from feature text: {stripped!r}", file=sys.stderr, flush=True)
    return text


def _validate_project_dir(path):
    """Verify path is a real directory containing .git (a valid git repo).
    Returns True if valid, False otherwise."""
    if not path:
        return False
    if not os.path.isdir(path):
        return False
    git_dir = os.path.join(path, ".git")
    if not os.path.isdir(git_dir):
        return False
    return True

def _redact_secrets(text):
    """Strip GH_TOKEN, GITHUB_TOKEN, and API_SERVER_KEY values from text.
    Looks up current values from the environment at call time (not cached).
    Redacts with [REDACTED]. Returns the redacted text unmodified if no tokens found."""
    if not text:
        return text
    tokens = []
    for env_name in ("GH_TOKEN", "GITHUB_TOKEN", "API_SERVER_KEY", "GLAB_TOKEN", "GITLAB_TOKEN"):
        val = os.environ.get(env_name, "")
        if val:
            tokens.append(val)
    if not tokens:
        return text
    result = text
    for tok in tokens:
        result = result.replace(tok, "[REDACTED]")
    return result

def _write_log_line(text):
    """Append a redacted line to OUTPUT_LOG. Creates the file if it doesn't exist."""
    global _LOG_FILE_HANDLE
    try:
        if _LOG_FILE_HANDLE is None:
            _LOG_FILE_HANDLE = open(OUTPUT_LOG, "a")
            os.chmod(OUTPUT_LOG, 0o600)
        _LOG_FILE_HANDLE.write(text + "\n")
        _LOG_FILE_HANDLE.flush()
    except Exception:
        pass

# load_key moved to git_ops.py — imported below

# load_github_token moved to git_ops.py — imported below

# git and gh functions moved to git_ops.py — imported below

# _safe_run moved to git_ops.py — imported below

def slugify(text):
    import hashlib
    base = re.sub(r'[^a-z0-9-]', '', text.lower().replace(" ", "-"))[:40]
    if len(text) > 40:
        h = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"{base}-{h}"
    return base

# spec extraction functions moved to spec_extract.py — imported below
# extract_agent_messages moved to spec_extract.py — imported below

# detect_repo moved to git_ops.py — imported below

# detect_commands moved to git_ops.py — imported below

# _detect_referenced_repo moved to git_ops.py — imported below

def _lock_path(project_dir=None):
    """Project-scoped lock file path."""
    if project_dir:
        slug = os.path.basename(os.path.abspath(project_dir))
    else:
        try:
            slug = os.path.basename(os.path.abspath(PROJECT_DIR))
        except NameError:
            slug = "unknown"
    return f"/tmp/dokima-{slug or 'unknown'}.lock"

def _stop_path(project_dir=None):
    """Project-scoped stop signal file path."""
    if project_dir:
        slug = os.path.basename(os.path.abspath(project_dir))
    else:
        try:
            slug = os.path.basename(os.path.abspath(PROJECT_DIR))
        except NameError:
            slug = "unknown"
    return f"/tmp/dokima-{slug or 'unknown'}.stop"

def _checkpoint_path(slug):
    """Return the checkpoint file path for a given feature slug."""
    return f"/tmp/dokima-{slug}-checkpoint.json"

def save_checkpoint(slug, data):
    """Save checkpoint data to disk. If data is None, delete the checkpoint."""
    if data is None:
        delete_checkpoint(slug)
        return
    cpath = _checkpoint_path(slug)
    with open(cpath, "w") as f:
        json.dump(data, f)
    os.chmod(cpath, 0o600)

def load_checkpoint(slug):
    """Load checkpoint data from disk. Returns None if not found or invalid."""
    cpath = _checkpoint_path(slug)
    if not os.path.exists(cpath):
        return None
    try:
        with open(cpath) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, ValueError):
        return None

def delete_checkpoint(slug):
    """Delete checkpoint file if it exists. No error if missing."""
    cpath = _checkpoint_path(slug)
    if os.path.exists(cpath):
        os.remove(cpath)

def _phase_should_skip(phases_completed, phase_name, resume=None):
    """Check if a phase should be skipped during resume.
    Returns True if phase_name is in phases_completed AND resume is True.
    If resume is None (auto-detect) or False, never skip."""
    if not resume:
        return False
    return phase_name in phases_completed

def validate_checkpoint(slug):
    """Validate a stored checkpoint: branch exists, spec file exists.
    Returns True if valid, False otherwise."""
    data = load_checkpoint(slug)
    if not data:
        return False
    # Check spec file exists
    spec_path = data.get("spec_path", "")
    if not spec_path or not os.path.exists(spec_path):
        return False
    # Check branch exists via git
    branch = data.get("branch", "")
    if not branch:
        return False
    result = _safe_run("git rev-parse --verify " + shlex.quote(branch), cwd=PROJECT_DIR)
    if result.returncode != 0:
        return False
    return True

def acquire_lock():
    """Try to acquire an advisory lock. Returns (held, fd)."""
    max_attempts = 3
    for attempt in range(max_attempts):
        # Capture lock mtime before truncation (F023: lock-age auto-cleanup)
        lp = _lock_path()
        lock_mtime = None
        if os.path.exists(lp):
            try:
                lock_mtime = os.path.getmtime(lp)
            except OSError:
                pass

        fd = open(lp, "w")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fd.write(f"{os.getpid()}\n")
            fd.flush()
            os.chmod(lp, 0o600)
            return True, fd
        except (IOError, OSError):
            fd.close()
            try:
                with open(lp) as lf:
                    stale_pid = lf.read().strip()
            except Exception:
                stale_pid = ""
            if stale_pid and stale_pid.isdigit():
                if _check_pid(stale_pid) and _verify_pid_owner(int(stale_pid)):
                    # F023: Lock-age auto-cleanup — handle SIGKILL + PID recycled edge case
                    lock_max_age = int(os.environ.get("PANEL_LOCK_MAX_AGE_SECS", "43200"))
                    if lock_mtime is not None:
                        lock_age = time.time() - lock_mtime
                        if lock_age > lock_max_age:
                            print(f"  Stale lock (> {lock_max_age}s old, PID {stale_pid} recycled) — removing and retrying...")
                            try:
                                os.remove(lp)
                            except OSError:
                                pass
                            continue
                    print(f"ERROR: Panel already running (PID {stale_pid}). If stuck, remove {lp}.")
                    sys.exit(1)
                else:
                    print(f"  Stale lock (PID {stale_pid} is dead/wrong process) — removing and retrying...")
                    try:
                        os.remove(lp)
                    except OSError:
                        pass
                    continue
            sys.exit(1)
    sys.exit(1)

def _cleanup_lock():
    """Release lock and restore stdout on interrupt or normal exit."""
    global _LOCK_FD, _LOG_FILE, _STDOUT_ORIG, _LOG_FILE_HANDLE
    # Also check dokima's _LOCK_FD (may be set by tests without syncing)
    dokima_mod = _IMPORTING_PANEL
    panel_fd = getattr(dokima_mod, '_LOCK_FD', None) if dokima_mod else None
    fd_to_close = _LOCK_FD or panel_fd
    if fd_to_close:
        try:
            fd_to_close.close()
        except Exception:
            pass
        _LOCK_FD = None
        # Sync to dokima module if loaded (F022 modular refactor)
        if dokima_mod is not None:
            dokima_mod._LOCK_FD = None
    try:
        os.remove(_lock_path())
    except OSError:
        pass
    if _STDOUT_ORIG:
        sys.stdout = _STDOUT_ORIG
    if _LOG_FILE:
        try:
            _LOG_FILE.close()
        except Exception:
            pass

def _signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM — clean up and exit."""
    print(f"\n  ⚠ Signal {signum} received — cleaning up...")
    _cleanup_lock()
    sys.exit(1)

# try_auto_merge moved to git_ops.py — imported below

# _supplement_pr_sections moved to git_ops.py — imported below

# _set_vcs_token moved to git_ops.py — imported below

# _load_token_from_env_file moved to git_ops.py — imported below

def show_help():
    print(HELP_TEXT)
    sys.exit(0)

def show_help_json():
    """Print CLI_METADATA as formatted JSON and exit."""
    print(json.dumps(CLI_METADATA, indent=2))
    sys.exit(0)

def check_upgrade():
    """--upgrade handler: check for newer version on GitHub."""
    import shutil
    install_dir = os.path.join(REAL_HOME, ".local", "share", "dokima")
    git_dir = os.path.join(install_dir, ".git")
    if not os.path.isdir(git_dir):
        print("Not installed via install.sh — cannot check for upgrades")
        sys.exit(0)

    # Check git is available
    git_path = shutil.which("git")
    if not git_path:
        print("git required for --upgrade")
        sys.exit(1)

    # Fetch tags from origin
    try:
        subprocess.run(
            [git_path, "-C", install_dir, "fetch", "--tags", "origin"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=30
        )
    except subprocess.TimeoutExpired:
        print("Could not check for updates: network timeout")
        sys.exit(1)
    except OSError:
        print("Could not check for updates: network error")
        sys.exit(1)

    # Read installed VERSION
    installed_version_path = os.path.join(install_dir, "VERSION")
    try:
        with open(installed_version_path) as f:
            installed_version = f.read().strip()
    except OSError:
        print("Could not determine installed version (VERSION file missing)")
        sys.exit(1)

    # Get latest semver tag
    try:
        tag_result = subprocess.run(
            [git_path, "-C", install_dir, "tag", "--sort=-v:refname"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            universal_newlines=True, timeout=10
        )
        tags = tag_result.stdout.strip().split("\n") if tag_result.stdout.strip() else []
        # Filter to vX.Y.Z patterns only
        semver_tags = [t for t in tags if re.match(r'^v\d+\.\d+\.\d+$', t)]
    except (subprocess.TimeoutExpired, OSError):
        print("Could not check for updates: failed to fetch tags")
        sys.exit(1)

    if not semver_tags:
        print("No releases found")
        sys.exit(0)

    latest_tag = semver_tags[0]
    latest_version = latest_tag.lstrip("v")

    # Compare versions
    if _version_newer(latest_version, installed_version):
        print(f"dokima v{latest_version} available (you have v{installed_version}) — "
              f"run: curl -sSL https://get.dokima.dev | bash")
    else:
        print(f"dokima v{installed_version} is up to date")
    sys.exit(0)

def _version_newer(a, b):
    """Return True if semver a > b. Both are 'X.Y.Z' strings."""
    try:
        parts_a = [int(x) for x in a.split(".")]
        parts_b = [int(x) for x in b.split(".")]
        return parts_a > parts_b
    except (ValueError, AttributeError):
        return False

def _parse_status_md(status_path: str) -> tuple:
    """Parse STATUS.md into (header, active_entries, archived_entries).
       Returns defaults if file doesn't exist."""
    if not os.path.exists(status_path):
        header = f"# Specs Status — initialized {time.strftime('%Y-%m-%d %H:%M')}\n\n"
        return header, [], []

    with open(status_path) as f:
        content = f.read()

    # Extract header (everything before ## Active or ## Archived)
    header_end = len(content)
    for marker in ["\n## Active", "\n## Archived"]:
        idx = content.find(marker)
        if idx != -1 and idx < header_end:
            header_end = idx
    header = content[:header_end].strip() + "\n"

    # Parse active entries
    active = []
    active_m = re.search(r'## Active\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if active_m:
        for line in active_m.group(1).strip().split("\n"):
            line = line.strip()
            if line:
                active.append(line)

    # Parse archived entries
    archived = []
    archive_m = re.search(r'## Archived\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if archive_m:
        for line in archive_m.group(1).strip().split("\n"):
            line = line.strip()
            if line:
                archived.append(line)

    return header, active, archived

def _make_status_entry(feature_id: str, title: str, status: str, timestamp: str = "",
                       branch: str = "", pr_url: str = "", source: str = "panel") -> str:
    """Build a structured STATUS.md entry line."""
    ts = timestamp or time.strftime('%Y-%m-%d %H:%M')

    if status == "in_progress":
        branch_part = f", branch `{branch}`" if branch else ""
        return f"- **{feature_id}: {title}** — in progress since {ts}{branch_part} [{source}]"
    elif status == "done":
        if pr_url:
            pr_match = re.search(r'/pull/(\d+)', pr_url)
            pr_num = pr_match.group(1) if pr_match else "?"
            pr_part = f", PR [#{pr_num}]({pr_url})"
        else:
            pr_part = ""
        return f"- **{feature_id}: {title}** — done {ts}{pr_part} [{source}]"
    else:
        # pending or other
        branch_part = f", branch `{branch}`" if branch else ""
        return f"- **{feature_id}: {title}** — {status} {ts}{branch_part} [{source}]"

def update_status_md(status_path: str, feature_id: str, title: str, status: str,
                     timestamp: str = "", branch: str = "", pr_url: str = "",
                     source: str = "panel"):
    """Update STATUS.md for a feature lifecycle event.
       status: 'in_progress' or 'done'. Dedupes, preserves manual entries."""

    header, active, archived = _parse_status_md(status_path)

    new_entry = _make_status_entry(feature_id, title, status, timestamp,
                                   branch, pr_url, source)

    # Pattern to match existing panel-managed entries for this feature
    entry_pattern = re.compile(rf'^- \*\*{feature_id}:')

    # Remove existing entry for this feature from both sections
    active = [e for e in active if not entry_pattern.match(e)]
    archived = [e for e in archived if not entry_pattern.match(e)]

    # Place in correct section
    if status == "in_progress":
        active.append(new_entry)
    else:
        archived.append(new_entry)

    # Update header timestamp
    ts = timestamp or time.strftime('%Y-%m-%d %H:%M')
    header = re.sub(r'(# Specs Status).*', rf'\1 — last updated {ts}', header)

    # Build output
    output = header + "\n"
    output += "## Active\n"
    if active:
        output += "\n".join(active) + "\n"
    output += "\n## Archived\n"
    if archived:
        output += "\n".join(archived) + "\n"

    os.makedirs(os.path.dirname(status_path), exist_ok=True)
    with open(status_path, "w") as f:
        f.write(output)

def _check_pid(pid_str):
    """Check if PID is alive. Returns True/False."""
    # Allow test patching via dokima._check_pid override (F022 modular refactor)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, '_check_pid', None)
        if override is not None and override is not _check_pid:
            return override(pid_str)

    try:
        os.kill(int(pid_str), 0)
        return True
    except (OSError, ValueError):
        return False

def _verify_pid_owner(pid: int) -> bool:
    """Verify /proc/{pid}/comm is dokima or python. Returns True/False."""
    # Allow test patching via dokima._verify_pid_owner override (F022 modular refactor)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, '_verify_pid_owner', None)
        if override is not None and override is not _verify_pid_owner:
            return override(pid)

    try:
        with open(f"/proc/{pid}/comm") as f:
            comm = f.read().strip()
        return comm in ("dokima", "python3", "python")
    except Exception:
        return False

def _get_lock_state(project_dir):
    """Read lock file for a project. Returns (running, pid, info_dict)."""
    lp = _lock_path(project_dir)
    if not os.path.exists(lp):
        return False, "", {}
    try:
        with open(lp) as f:
            pid = f.read().strip()
    except Exception:
        return False, "", {}
    if not pid or not _check_pid(pid):
        try:
            os.remove(lp)
        except OSError:
            pass
        return False, "", {}

    # F023: Lock-age auto-cleanup for --status — handle SIGKILL + PID recycled
    lock_max_age = int(os.environ.get("PANEL_LOCK_MAX_AGE_SECS", "43200"))
    try:
        lock_age = time.time() - os.path.getmtime(lp)
        if lock_age > lock_max_age:
            try:
                os.remove(lp)
            except OSError:
                pass
            return False, "", {}
    except OSError:
        pass  # Can't stat — proceed with existing logic

    # Read roadmap for current feature
    info = {}
    roadmap_path = os.path.join(project_dir, "specs", "roadmap.md")
    if os.path.exists(roadmap_path):
        try:
            # Lazy import from dokima monolith — parse_roadmap lives there until
            # it's extracted into a roadmap.py module (future refactor).
            import importlib
            dokima_mod = importlib.import_module('dokima')
            parse_roadmap = dokima_mod.parse_roadmap
            features = parse_roadmap(roadmap_path)
            current = [f for f in features if f.status == "in_progress"]
            if current:
                info["feature"] = f"{current[0].id}: {current[0].title}"
            info["done"] = sum(1 for f in features if f.status == "done")
            info["total"] = len(features)
        except ImportError:
            pass  # dokima not importable (fresh extraction context)
        except Exception:
            pass  # roadmap parsing errors are non-fatal for lock state
    # Read log tail for phase
    if os.path.exists(OUTPUT_LOG):
        try:
            with open(OUTPUT_LOG) as lf:
                for line in reversed(lf.readlines()):
                    for marker in ["── Phase", "── Next Feature", "── Continuous"]:
                        if marker in line:
                            info["activity"] = line.strip()
                            break
                    if "activity" in info:
                        break
        except Exception:
            pass
    return True, pid, info

# control panel handlers moved to control_panel.py — imported below
# extract_file_paths moved to spec_extract.py — imported below

def _hash_output(text):
    """Return MD5 hex digest of text for cycle detection (F023)."""
    import hashlib
    if text is None:
        text = ""
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()

def _detect_truncation(text):
    """Detect truncated coder output. Returns True if output appears truncated.

    A non-truncated output has a Report: line OR ends with terminal
    punctuation (., !, ?). None input returns False (safety); empty input
    returns True (coder crashed).
    """
    if text is None:
        return False
    if not text:
        return True
    # Check for Report: marker (case-insensitive, word boundary)
    if re.search(r'\bReport:', text, re.IGNORECASE):
        return False
    # Check if last non-whitespace character is terminal punctuation
    stripped = text.rstrip()
    if stripped and stripped[-1] in ('.', '!', '?'):
        return False
    return True

def _extract_code_context(spec_text, task_text, project_dir):
    """Extract relevant code snippets from line-range references in spec/task text.
    
    Parses patterns like:
    - "lines 4583–4594 in dokima"
    - "dokima:4583-4594"
    - "line 4584 of src/foo.py"
    
    Reads the target files and returns a code-context string for the coder prompt.
    Returns empty string if no line references found or files unreadable.
    """
    snippets = []
    # Pattern: "lines N–M" or "line N" with optional filename mention
    line_refs = re.findall(
        r'(?:lines?\s+|:)(\d{2,6})\s*(?:[–\-—]|\s*to\s*)\s*(\d{2,6})',
        spec_text + '\n' + task_text, re.IGNORECASE
    )
    if not line_refs:
        return ""
    
    # Build a set of (filename, start, end) to read — up to 5 snippets
    seen = set()
    for start, end in line_refs[:5]:
        start_i, end_i = int(start), int(end)
        if start_i > end_i:
            start_i, end_i = end_i, start_i
        # Expand context window: 3 lines before and after
        read_start = max(1, start_i - 3)
        read_end = end_i + 3
        
        # Try to find which file this refers to from task Files: fields
        files_m = re.findall(r'\*\*Files:\*\*\s*(.+)', task_text)
        target_files = []
        for fl in files_m:
            for f in re.split(r'[,;]\s*', fl):
                f = re.sub(r'\s*\(NEW\)', '', f).strip()
                if f and not f.startswith('http'):
                    target_files.append(f)
        
        for fname in target_files[:3]:
            key = (fname, read_start, read_end)
            if key in seen:
                continue
            seen.add(key)
            fpath = os.path.join(project_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath) as f:
                    lines = f.readlines()
                if read_start > len(lines):
                    continue
                actual_end = min(read_end, len(lines))
                chunk = ''.join(
                    f"{i}:{lines[i-1]}" 
                    for i in range(read_start, actual_end + 1)
                )
                if chunk.strip():
                    snippets.append(
                        f"```{fname}:{read_start}-{actual_end}\n{chunk}```"
                    )
            except Exception:
                pass
    
    if not snippets:
        return ""
    
    return (
        "\n### ⚡ Relevant Code (read ONLY these snippets — no full-file exploration)\n"
        + "\n".join(snippets)
        + "\n⚡ These are the EXACT lines to modify. Start here.\n"
    )

# ── F028: Map Enrichments ──────────────────────────
# load_map_enrichments moved to codebase_map.py — imported below
# save_map_enrichments moved to codebase_map.py — imported below
# extract_map_enrichments moved to codebase_map.py — imported below

# codebase map functions moved to codebase_map.py — imported below



# _build_test_map moved to codebase_map.py — imported below
# _find_key_files moved to codebase_map.py — imported below
# _describe_file moved to codebase_map.py — imported below

# _extract_tl_verdict moved to spec_extract.py — imported below
# _extract_tl_blockers moved to spec_extract.py — imported below
# format_blocker_cross_reference moved to spec_extract.py — imported below
# _extract_convention_rules moved to spec_extract.py — imported below
# _append_convention_rules moved to spec_extract.py — imported below

# ── Profile configuration defaults (F012) ──
_PROFILE_CONFIGS = {
    "strategist": {
        "model.default": "deepseek-v4-pro",
        "model.provider": "deepseek",
        "agent.max_turns": "150",
        "agent.reasoning_effort": "high",
        "terminal.env_passthrough": "[GH_TOKEN, GITHUB_TOKEN, GLAB_TOKEN, GITLAB_TOKEN, HERMES_HOME, HOME]",
    },
    "coder": {
        "model.default": "deepseek-v4-pro",
        "model.provider": "deepseek",
        "agent.max_turns": "150",
        "terminal.env_passthrough": "[GH_TOKEN, GITHUB_TOKEN, GLAB_TOKEN, GITLAB_TOKEN, HERMES_HOME, HOME]",
    },
    "tech-lead": {
        "model.default": "deepseek-v4-pro",
        "model.provider": "deepseek",
        "agent.max_turns": "150",
        "terminal.env_passthrough": "[GH_TOKEN, GITHUB_TOKEN, GLAB_TOKEN, GITLAB_TOKEN, HERMES_HOME, HOME]",
    },
    "nm": {
        "model.default": "deepseek-v4-pro",
        "model.provider": "deepseek",
        "agent.max_turns": "150",
        "terminal.env_passthrough": "[GH_TOKEN, GITHUB_TOKEN, GLAB_TOKEN, GITLAB_TOKEN, HERMES_HOME, HOME]",
    },
}
_PROFILE_ORDER = ["strategist", "coder", "tech-lead", "nm"]


def ensure_profiles():
    """Create agent profiles (strategist, coder, tech-lead, nm) if they don't exist.
    Configures sensible defaults: model, provider, max_turns, env_passthrough.
    Strategist also gets agent.reasoning_effort=high.
    Idempotent — skips profiles that already exist.
    Non-interactive safe — works without a TTY."""
    # Allow test patching via dokima module (F022 modular refactor)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'ensure_profiles', None)
        if override is not None and override is not _ENSURE_PROFILES_ORIGINAL:
            return override()

    for name in _PROFILE_ORDER:
        profile_dir = os.path.join(PROFILES, name)

        # Check if profile already exists
        if os.path.isdir(profile_dir):
            print(f"  Profile '{name}' already exists — skipping", flush=True)
            continue

        # Create the profile
        print(f"  Creating profile: {name}", flush=True)
        try:
            result = subprocess.run(
                [HERMES_BIN, "profile", "create", name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, timeout=30
            )
            if result.returncode != 0:
                print(f"  WARNING: Failed to create profile '{name}': {result.stderr.strip()[:200]}", flush=True)
                continue
        except Exception as e:
            print(f"  WARNING: Failed to create profile '{name}': {e}", flush=True)
            continue

        # Apply configuration
        config = _PROFILE_CONFIGS.get(name, {})
        for key, value in config.items():
            try:
                subprocess.run(
                    [HERMES_BIN, "--profile", name, "config", "set", key, value],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True, timeout=30
                )
            except Exception as e:
                print(f"  WARNING: Failed to set {key} for '{name}': {e}", flush=True)

        print(f"  Profile '{name}' configured", flush=True)

    # Verify profiles exist after creation (for idempotency check on re-run)
    missing_after = [n for n in _PROFILE_ORDER
                     if not os.path.isdir(os.path.join(PROFILES, n))]
    if missing_after:
        print(f"  WARNING: Profiles still missing after creation attempt: {', '.join(missing_after)}", flush=True)

def deploy_profile_skills():
    """Deploy panel skills from PANEL_DIR/skills/ to profile skill directories.
    Idempotent — skips existing skill directories.
    nm's 'no-mistakes' skill goes to the global skills dir (~/.hermes/skills/)."""
    # Allow test patching via dokima module (F022 modular refactor)
    dokima_mod = _IMPORTING_PANEL
    if dokima_mod is not None:
        override = getattr(dokima_mod, 'deploy_profile_skills', None)
        if override is not None and override is not _DEPLOY_PROFILE_SKILLS_ORIGINAL:
            return override()

    import shutil as _shutil

    # Source skills from PANEL_DIR first, fall back to dokima source directory
    skills_dir = os.path.join(PANEL_DIR, "skills")
    if not os.path.isdir(skills_dir):
        # We're running in a project — skills are in the dokima source
        skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
    software_dev = "software-development"

    # (profile, skill, is_global) — is_global=True deploys to HERMES/skills/
    _SKILL_MAPPINGS = [
        ("strategist", "spec-strategist-lite", False),
        ("strategist", "ponytail-guard", False),
        ("coder", "ai-coding-best-practices-lite", False),
        ("tech-lead", "adversarial-review-lite", False),
        ("tech-lead", "ponytail-guard", False),
        ("nm", "no-mistakes", True),
    ]

    for profile, skill, is_global in _SKILL_MAPPINGS:
        src = os.path.join(skills_dir, skill)

        if is_global:
            dest_parent = os.path.join(HERMES, "skills", software_dev)
        else:
            dest_parent = os.path.join(PROFILES, profile, "skills", software_dev)
        dest = os.path.join(dest_parent, skill)

        if not os.path.isdir(src):
            print(f"  WARNING: Source skill not found: {skill} — skipping", flush=True)
            continue

        if os.path.isdir(dest):
            print(f"  Skill '{skill}' already deployed for {profile} — skipping", flush=True)
            continue

        os.makedirs(dest_parent, exist_ok=True)
        _shutil.copytree(src, dest)
        print(f"  Deployed skill '{skill}' → {profile}", flush=True)


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


def archive_specs_for_feature(spec_path, branch, pr_url):
    """Move a feature's spec directory to archive/ if PR is merged.
    Returns True if archived, False otherwise."""
    if not pr_url:
        return False
    import shutil as _shutil
    pr_num = pr_url.rstrip("/").split("/")[-1]
    if not pr_num.isdigit():
        return False
    try:
        stdout, _, rc = gh("pr", "view", pr_num, "--json", "merged,state")
        if rc != 0 or not stdout.strip():
            return False
        import json as _json
        data = _json.loads(stdout)
        if data.get("merged") is True:
            parent_dir = os.path.dirname(spec_path)
            archive_dir = os.path.join(parent_dir, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            dirname = os.path.basename(spec_path)
            archive_target = os.path.join(archive_dir, dirname)
            if os.path.exists(archive_target):
                if os.path.isdir(archive_target):
                    _shutil.rmtree(archive_target)
                else:
                    os.remove(archive_target)
            _shutil.move(spec_path, archive_target)
            return True
    except Exception:
        pass
    return False

# ── F024: Auto-Release ───────────────────────────

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


# Module-level original references for delegation checks (F022 modular refactor)
_ENSURE_PROFILES_ORIGINAL = ensure_profiles
_DEPLOY_PROFILE_SKILLS_ORIGINAL = deploy_profile_skills

# ── F031: Init interview mode ──────────────────────

INTERVIEW_SAVE_PATH = "/tmp/dokima-init-interview.json"


def load_init_interview_state(path=None):
    """Load init interview state from JSON file.

    Reads the interview state from INTERVIEW_SAVE_PATH (or a custom path),
    validates the JSON structure, and returns the parsed dict.

    Returns None if the file is missing, empty, or contains invalid JSON.
    """
    if path is None:
        path = INTERVIEW_SAVE_PATH

    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return None

    # Validate it looks like an interview state dict (has expected keys)
    if not isinstance(data, dict):
        return None

    return data


def save_init_interview_state(feature, project_dir, round_num, confidence,
                              questions, original_prompt, answers=None, path=None):
    """Save init interview state to JSON file.

    Persists the interview state with all required fields. Answers defaults
    to an empty list if not provided. File is created with chmod 0o600.
    """
    if path is None:
        path = INTERVIEW_SAVE_PATH
    if answers is None:
        answers = []

    state = {
        "feature": feature,
        "project_dir": project_dir,
        "round": round_num,
        "max_rounds": 3,
        "confidence": confidence,
        "questions": questions,
        "answers": answers,
        "original_prompt": original_prompt,
        "timestamp": datetime.datetime.now().isoformat(),
    }

    with open(path, 'w') as f:
        json.dump(state, f)
    os.chmod(path, 0o600)


def has_init_interview_triggers(text):
    """Check if strategist output contains init interview triggers.

    Returns True if the text contains structured CLARIFICATION N: lines
    at line-start or a DECISION: INTERVIEW MODE marker. Returns False
    for prose that merely mentions 'CLARIFICATION' or 'INTERVIEW MODE'
    without the structured format.
    """
    if not text or not text.strip():
        return False

    # Structured CLARIFICATION N: at line start (init-specific format)
    if re.search(r'^\s*CLARIFICATION\s+\d+:', text, re.MULTILINE):
        return True

    # DECISION: INTERVIEW MODE marker
    if 'DECISION: INTERVIEW MODE' in text:
        return True

    return False


def collect_init_interview_answers(questions, interview_state, path=None):
    """Collect answers to interview questions interactively or via state save.

    In TTY mode: prompts user for each question with 60s timeout per question.
    Empty input (Enter with no text) breaks the loop — all subsequent questions
    get their assumptions accepted.

    In non-TTY mode: saves interview_state to JSON and returns exit code 2.
    The caller should propagate this exit code to the process.

    Args:
        questions: list of question dicts with 'id' and 'question' keys.
                   None or empty list returns immediately.
        interview_state: dict with current interview state for non-TTY save.
        path: path to save state JSON (default: INTERVIEW_SAVE_PATH).

    Returns:
        (answers: list[dict], exit_code: int)
        answers: list of {"question_id": int, "answer": str} dicts.
        exit_code: 0 = success (or assumptions accepted), 2 = non-TTY saved.
    """
    import select

    if path is None:
        path = INTERVIEW_SAVE_PATH

    # Empty/null questions -> nothing to collect
    if not questions:
        return ([], 0)

    # Non-TTY: save state and exit
    if not sys.stdin.isatty():
        save_init_interview_state(
            feature=interview_state.get("feature", ""),
            project_dir=interview_state.get("project_dir", ""),
            round_num=interview_state.get("round", 1),
            confidence=interview_state.get("confidence", "Low"),
            questions=questions,
            original_prompt=interview_state.get("original_prompt", ""),
            answers=interview_state.get("answers", []),
            path=path,
        )
        print(f"\n{'=' * 55}", flush=True)
        print("  STRATEGIST NEEDS CLARIFICATION (init)", flush=True)
        print(f"{'=' * 55}", flush=True)
        print(f"\n  State saved: {path}", flush=True)
        print(f"  Re-run with: dokima init --answers {path}", flush=True)
        return ([], 2)

    # TTY: interactively collect answers
    print(f"\n{'=' * 60}", flush=True)
    print("  INIT INTERVIEW — Clarifications Needed", flush=True)
    print(f"{'=' * 60}", flush=True)
    print("\nAnswer these questions to refine the project constitution.", flush=True)
    print("Blank line = accept assumptions and proceed.\n", flush=True)

    for i, q in enumerate(questions, 1):
        q_text = q.get("question", str(q))
        print(f"\n  Q{i}: {q_text}", flush=True)

    print(f"\n{'-' * 60}", flush=True)
    print("  Type your answers (one per line). Empty input = accept all assumptions.", flush=True)
    print(f"{'-' * 60}", flush=True)

    user_answers = []
    try:
        for i, q in enumerate(questions, 1):
            print(f"\n  A{i}: ", end="", flush=True)
            ready, _, _ = select.select([sys.stdin], [], [], 60.0)
            if not ready:
                print("(timed out — accepting assumptions)", flush=True)
                break
            answer = sys.stdin.readline().strip()
            if not answer:
                break
            user_answers.append({
                "question_id": q.get("id", i),
                "answer": answer,
            })
    except (EOFError, KeyboardInterrupt):
        print("\n  ⚠ No input available — proceeding with assumptions", flush=True)

    if user_answers:
        print(f"\n  ✓ Got {len(user_answers)} answer(s).", flush=True)
    else:
        print("\n  ✓ No answers provided — proceeding with assumptions as-is.", flush=True)

    return (user_answers, 0)

# ── Re-exports from domain modules (F041: Split utils.py) ──────────
from codebase_map import generate_codebase_map, _build_domain_map, _build_impact_map, _classify_domain, load_map_enrichments, save_map_enrichments, extract_map_enrichments, _build_test_map, _find_key_files, _describe_file  # noqa: E402,F401
from control_panel import handle_status, handle_stop, handle_kill, handle_list_crons  # noqa: E402,F401
from spec_extract import extract_pr_sections, clean_spec_content, verify_spec_quality, _check_pr_body_quality, extract_should_fix_from_text, _extract_nm_summary, extract_issue_sections, extract_agent_messages, extract_file_paths, _extract_tl_verdict, _extract_tl_blockers, format_blocker_cross_reference, _extract_convention_rules, _append_convention_rules  # noqa: E402,F401
from git_ops import git, gh, detect_repo, load_key, load_github_token, _safe_run, detect_commands, _detect_referenced_repo, _detect_default_branch, _set_vcs_token, _set_gh_token, _load_token_from_env_file, try_auto_merge, _supplement_pr_sections  # noqa: E402,F401

