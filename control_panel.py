"""Dokima control panel — CLI status, stop, kill, help, upgrade.

All functions extracted from dokima monolith utils.py (F041: Split utils.py into domain modules).
"""

import sys, json, os, re, subprocess, time


# Cross-module import: check_upgrade() calls do_release() from git_ops
from git_ops import do_release


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



def handle_status(project_dir):
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
        print(f"Log:         {OUTPUT_LOG}")
    else:
        print("State:       IDLE")
        if "done" in info:
            print(f"Roadmap:     {info['done']}/{info['total']} done")
    sys.exit(0)



def handle_stop(project_dir):
    """--stop handler."""
    running, pid, _ = _get_lock_state(project_dir)
    sp = _stop_path(project_dir)
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
    """--kill handler."""
    running, pid, _ = _get_lock_state(project_dir)
    if not running:
        print(f"No pipeline running for {os.path.basename(os.path.abspath(project_dir))}.")
        sys.exit(0)
    # Verify PID still belongs to dokima before signaling
    if not _verify_pid_owner(int(pid)):
        print(f"PID {pid} is not dokima (recycled?) — cleaning stale lock")
        try:
            os.remove(_lock_path(project_dir))
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
        os.remove(_lock_path(project_dir))
    except OSError:
        pass
    try:
        os.remove(_stop_path(project_dir))
    except OSError:
        pass
    print(f"Pipeline killed (was PID {pid})")
    sys.exit(0)



def handle_list_crons():
    """--list-crons handler."""
    # Parse crontab
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



