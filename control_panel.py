"""Control panel handlers extracted from utils.py (F041).

Contains handle_status(), handle_stop(), handle_kill(), handle_list_crons(),
show_help(), show_help_json(), check_upgrade(), _version_newer(),
_check_pid(), _verify_pid_owner(), _get_lock_state().
Also holds HELP_TEXT and CLI_METADATA constants.
Uses lazy imports from utils for shared helpers.
"""

import os
import re
import sys
import time
import signal


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
    "version": "unknown",  # re-exported from utils.VERSION at import time
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


def handle_status(project_dir):
    import utils as _u
    """--status handler. Shows live dashboard if pipeline is running."""
    # Try live dashboard first (F025)
    try:
        from status import load_status, render
    except ImportError:
        load_status = None
    if load_status:
        s = load_status(project_dir)
        if s and s.current_phase != "init":
            print(render(s))
            # If --watch flag, poll every 2s
            if "--watch" in sys.argv:
                import time as _t
                try:
                    while True:
                        _t.sleep(2)
                        s = load_status(project_dir)
                        if s:
                            print("\033[2J\033[H" + render(s))  # clear screen
                except KeyboardInterrupt:
                    print("\n  (watch stopped)")
            return

    # Fallback: simple lock-based status
    running, pid, info = _get_lock_state(project_dir)
    print(f"── Panel Status: {os.path.basename(os.path.abspath(project_dir))} ──")
    if running:
        elapsed = ""
        try:
            import time as _t
            st = os.stat(f"/proc/{pid}").st_ctime
            mins = int((_t.time() - st) // 60)
            elapsed = f"{mins}min" if mins < 120 else f"{mins//60}h{mins%60}m"
        except Exception:
            elapsed = "?"
        print(f"State:       RUNNING (PID {pid}, {elapsed} elapsed)")
        if info.get("feature"):
            print(f"Feature:     {info['feature']}")
        if info.get("activity"):
            print(f"Activity:    {info['activity']}")
        if "done" in info:
            print(f"Roadmap:     {info['done']}/{info['total']} done")
        print(f"Log:         {_u.OUTPUT_LOG}")
    else:
        print("State:       IDLE")
        if "done" in info:
            print(f"Roadmap:     {info['done']}/{info['total']} done")
    sys.exit(0)

def handle_stop(project_dir):
    import utils as _u
    """--stop handler."""
    running, pid, _ = _get_lock_state(project_dir)
    sp = _u._stop_path(project_dir)
    if not running:
        print(f"No pipeline running for {os.path.basename(os.path.abspath(project_dir))}.")
        sys.exit(0)
    if os.path.exists(sp):
        print(f"Stop signal already sent to PID {pid}.")
    else:
        with open(sp, "w") as f:
            f.write(f"stop at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        os.chmod(sp, 0o600)
        print(f"Stop signal sent to PID {pid}. Pipeline will stop after current feature.")
    sys.exit(0)

def handle_kill(project_dir):
    import utils as _u
    """--kill handler."""
    running, pid, _ = _get_lock_state(project_dir)
    if not running:
        print(f"No pipeline running for {os.path.basename(os.path.abspath(project_dir))}.")
        sys.exit(0)
    # Verify PID still belongs to dokima before signaling
    if not _verify_pid_owner(int(pid)):
        print(f"PID {pid} is not dokima (recycled?) — cleaning stale lock")
        try:
            os.remove(_u._lock_path(project_dir))
        except OSError:
            pass
        sys.exit(0)
    print(f"Sending SIGTERM to PID {pid}...")
    try:
        os.kill(int(pid), signal.SIGTERM)
        print(f"  SIGTERM sent successfully to PID {pid}")
    except OSError as e:
        print(f"  Failed to send SIGTERM: {e}")
    time.sleep(2)
    if _check_pid(pid) and _verify_pid_owner(int(pid)):
        print(f"Process still alive — sending SIGKILL to PID {pid}")
        try:
            os.kill(int(pid), signal.SIGKILL)
            print(f"  SIGKILL sent successfully to PID {pid}")
        except OSError as e:
            print(f"  Failed to send SIGKILL: {e}")
        time.sleep(1)
    elif not _check_pid(pid):
        print(f"  Process already exited")
    # Clean up
    try:
        os.remove(_u._lock_path(project_dir))
    except OSError:
        pass
    try:
        os.remove(_u._stop_path(project_dir))
    except OSError:
        pass
    print(f"Pipeline killed (was PID {pid})")
    sys.exit(0)

def handle_list_crons():
    """--list-crons handler."""
    import subprocess as sp
    result = sp.run(["crontab", "-l"], stdout=sp.PIPE, stderr=sp.PIPE,
                    universal_newlines=True, timeout=10)
    cron_entries = []
    if result.returncode == 0:
        for line in result.stdout.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "dokima" in line:
                parts = line.split(None, 5)
                if len(parts) >= 6:
                    schedule = " ".join(parts[:5])
                    cmd = parts[5]
                    proj_match = re.search(r'(?:--continuous|--next)\s+(\S+)', cmd)
                    proj = os.path.expanduser(proj_match.group(1)) if proj_match else "cwd"
                    mode = "--continuous" if "--continuous" in cmd else "--next"
                    cron_entries.append((proj, schedule, mode))

    # Scan lock files for running state
    import glob as _glob
    lock_files = _glob.glob("/tmp/dokima-*.lock")
    running_projects = {}
    for lf in lock_files:
        try:
            slug = os.path.basename(lf).replace("dokima-", "").replace(".lock", "")
            with open(lf) as f:
                pid_str = f.read().strip()
            if pid_str and _check_pid(pid_str):
                running_projects[slug] = pid_str
            else:
                try:
                    os.remove(lf)
                except OSError:
                    pass
        except Exception:
            pass

    print("── Continuous Pipelines ──")
    if not cron_entries and not running_projects:
        print("No dokima pipelines found.")
        sys.exit(0)

    print(f"{'PROJECT':<30} {'SCHEDULE':<18} {'STATE'}")
    print("-" * 70)
    shown = set()
    for proj, schedule, mode in sorted(cron_entries):
        shown.add(os.path.basename(proj))
        slug = os.path.basename(os.path.abspath(proj))
        if slug in running_projects:
            state = f"RUNNING (PID {running_projects[slug]})"
        else:
            state = "IDLE"
        print(f"{proj:<30} {schedule:<18} {state}")
    # Show running projects not in crontab
    for slug, pid in running_projects.items():
        if slug not in shown:
            print(f"{slug:<30} {'manual':<18} RUNNING (PID {pid})")
    sys.exit(0)


def show_help():
    print(HELP_TEXT)
    sys.exit(0)


def show_help_json():
    """Print CLI_METADATA as formatted JSON and exit."""
    import json as _json
    print(_json.dumps(CLI_METADATA, indent=2))
    sys.exit(0)


def check_upgrade():
    """--upgrade handler: check for newer version on GitHub."""
    import utils as _u
    import shutil
    install_dir = os.path.join(_u.REAL_HOME, ".local", "share", "dokima")
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
    import subprocess as _sp
    try:
        _sp.run(
            [git_path, "-C", install_dir, "fetch", "--tags", "origin"],
            stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
            timeout=30
        )
    except _sp.TimeoutExpired:
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
        tag_result = _sp.run(
            [git_path, "-C", install_dir, "tag", "--sort=-v:refname"],
            stdout=_sp.PIPE, stderr=_sp.DEVNULL,
            universal_newlines=True, timeout=10
        )
        tags = tag_result.stdout.strip().split("\n") if tag_result.stdout.strip() else []
        # Filter to vX.Y.Z patterns only
        semver_tags = [t for t in tags if re.match(r'^v\d+\.\d+\.\d+$', t)]
    except (_sp.TimeoutExpired, OSError):
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


def _check_pid(pid_str):
    """Check if PID is alive. Returns True/False."""
    import utils as _u

    # Allow test patching via dokima._check_pid override (F022 modular refactor)
    dokima_mod = _u._IMPORTING_PANEL
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
    import utils as _u

    # Allow test patching via dokima._verify_pid_owner override (F022 modular refactor)
    dokima_mod = _u._IMPORTING_PANEL
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
    import utils as _u

    lp = _u._lock_path(project_dir)
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
    if os.path.exists(_u.OUTPUT_LOG):
        try:
            with open(_u.OUTPUT_LOG) as lf:
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
