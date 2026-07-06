"""Control panel handlers extracted from utils.py (F041).

Contains handle_status(), handle_stop(), handle_kill(), handle_list_crons().
Uses lazy imports from utils for shared helpers.
"""

import os
import re
import sys
import time
import signal


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
    running, pid, info = _u._get_lock_state(project_dir)
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
    running, pid, _ = _u._get_lock_state(project_dir)
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
    running, pid, _ = _u._get_lock_state(project_dir)
    if not running:
        print(f"No pipeline running for {os.path.basename(os.path.abspath(project_dir))}.")
        sys.exit(0)
    # Verify PID still belongs to dokima before signaling
    if not _u._verify_pid_owner(int(pid)):
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
    if _u._check_pid(pid) and _u._verify_pid_owner(int(pid)):
        print(f"Process still alive — sending SIGKILL to PID {pid}")
        try:
            os.kill(int(pid), signal.SIGKILL)
            print(f"  SIGKILL sent successfully to PID {pid}")
        except OSError as e:
            print(f"  Failed to send SIGKILL: {e}")
        time.sleep(1)
    elif not _u._check_pid(pid):
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
            if pid_str and _u._check_pid(pid_str):
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
