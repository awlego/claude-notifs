import fcntl
import json
import os
import tempfile
import time

from .constants import (
    SESSION_PRUNE_TIMEOUT,
    STATUS_FILE,
    STATUS_PRIORITY,
    Status,
)


def read_status() -> dict:
    """Read the status file, returning empty sessions dict if missing/corrupt."""
    try:
        with open(STATUS_FILE) as f:
            data = json.load(f)
            if isinstance(data, dict) and "sessions" in data:
                return data
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return {"sessions": {}}


def is_pid_alive(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        # PermissionError means the process exists but we can't signal it
        return True


def write_session_status(
    session_id: str,
    status: str,
    project: str,
    cwd: str,
    last_message: str = "",
    pid: int = 0,
) -> None:
    """Update a single session's status with file locking and atomic write."""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Open or create the lock file
    lock_path = STATUS_FILE.with_suffix(".lock")
    with open(lock_path, "w") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            data = read_status()
            now = time.time()

            # Prune sessions older than 24 hours
            data["sessions"] = {
                sid: s
                for sid, s in data["sessions"].items()
                if now - s.get("last_update", 0) < SESSION_PRUNE_TIMEOUT
            }

            # Update this session
            data["sessions"][session_id] = {
                "status": status,
                "project": project,
                "cwd": cwd,
                "last_update": now,
                "last_message": last_message,
                "pid": pid,
            }

            # Atomic write: write to temp file then rename
            fd, tmp_path = tempfile.mkstemp(
                dir=STATUS_FILE.parent, suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w") as tmp_f:
                    json.dump(data, tmp_f, indent=2)
                    tmp_f.write("\n")
                os.rename(tmp_path, STATUS_FILE)
            except BaseException:
                os.unlink(tmp_path)
                raise
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)


def get_active_sessions(sessions: dict) -> dict:
    """Return sessions whose Claude Code process is still running."""
    return {
        sid: s
        for sid, s in sessions.items()
        if s.get("pid") and is_pid_alive(s["pid"])
    }


def get_aggregate_status(sessions: dict) -> Status:
    """Return the highest-priority status across all given sessions."""
    if not sessions:
        return Status.IDLE
    statuses = set()
    for s in sessions.values():
        try:
            statuses.add(Status(s.get("status", "idle")))
        except ValueError:
            statuses.add(Status.IDLE)
    # Return highest priority
    for status in reversed(STATUS_PRIORITY):
        if status in statuses:
            return status
    return Status.IDLE
